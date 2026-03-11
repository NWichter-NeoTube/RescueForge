"""AI-powered room classification using OpenRouter Vision API."""

import json
import logging
import re
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import Polygon

from app.models.schemas import FloorPlanData, RoomPolygon, RoomType
from app.services.openrouter import call_vision_api
from app.utils.translations import room_label as tr_room_label

matplotlib.use("Agg")  # Non-interactive backend

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT_EN = """You are analyzing a building floor plan image. Each room is numbered and outlined.

Classify each numbered room into one of these types:
- office: Work spaces, desks
- corridor: Hallways, passages between rooms
- stairwell: Staircases, stairwells (vertical escape routes)
- elevator: Elevator shafts
- bathroom: WC, toilets, showers
- kitchen: Kitchen, break room with kitchen
- storage: Storage rooms, archives, closets
- technical: Server rooms, electrical rooms, HVAC, mechanical
- garage: Parking, vehicle areas
- lobby: Entrance halls, reception areas
- conference: Meeting rooms, conference rooms
- residential: General living spaces
- bedroom: Sleeping rooms
- living_room: Living/family rooms
- balcony: Balconies, terraces, outdoor areas
- unknown: Cannot determine

Consider the room's shape, size, position, and context:
- Long narrow rooms are likely corridors
- Small rooms near entrances may be bathrooms or storage
- Large open areas may be lobbies or open-plan offices
- Rooms with stair symbols are stairwells

Respond ONLY with a JSON array like:
[{"id": 1, "type": "office", "label": "Office 101"}, {"id": 2, "type": "corridor", "label": "Corridor"}]

Use English labels (Office, Corridor, Stairwell, Storage, Technical, Bathroom, Kitchen).
"""

CLASSIFICATION_PROMPT_DE = """You are analyzing a building floor plan image. Each room is numbered and outlined.

Classify each numbered room into one of these types:
- office: Work spaces, desks
- corridor: Hallways, passages between rooms
- stairwell: Staircases, stairwells (vertical escape routes)
- elevator: Elevator shafts
- bathroom: WC, toilets, showers
- kitchen: Kitchen, break room with kitchen
- storage: Storage rooms, archives, closets
- technical: Server rooms, electrical rooms, HVAC, mechanical
- garage: Parking, vehicle areas
- lobby: Entrance halls, reception areas
- conference: Meeting rooms, conference rooms
- residential: General living spaces
- bedroom: Sleeping rooms
- living_room: Living/family rooms
- balcony: Balconies, terraces, outdoor areas
- unknown: Cannot determine

Consider the room's shape, size, position, and context:
- Long narrow rooms are likely corridors
- Small rooms near entrances may be bathrooms or storage
- Large open areas may be lobbies or open-plan offices
- Rooms with stair symbols are stairwells

Respond ONLY with a JSON array like:
[{"id": 1, "type": "office", "label": "Büro 101"}, {"id": 2, "type": "corridor", "label": "Korridor"}]

Use German labels where appropriate (Büro, Korridor, Treppenhaus, Lager, Technik, WC, Küche).
"""


def _render_floor_plan_image(
    floor_plan: FloorPlanData,
    rooms: list[RoomPolygon],
    output_path: Path,
    dpi: int = 150,
) -> None:
    """Render floor plan with numbered rooms to a PNG image for AI classification."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_aspect("equal")

    # Draw walls
    for wall in floor_plan.walls:
        ax.plot(
            [wall.start.x, wall.end.x],
            [wall.start.y, wall.end.y],
            color="black",
            linewidth=1.5,
        )

    # Draw rooms with numbers
    colors = plt.cm.Set3(np.linspace(0, 1, max(len(rooms), 1)))
    for i, room in enumerate(rooms):
        coords = [(p.x, p.y) for p in room.points]
        poly = MplPolygon(coords, alpha=0.3, facecolor=colors[i % len(colors)], edgecolor="blue", linewidth=1)
        ax.add_patch(poly)

        # Add room number at centroid
        shapely_poly = Polygon(coords)
        centroid = shapely_poly.centroid
        ax.text(
            centroid.x, centroid.y, str(room.id),
            ha="center", va="center",
            fontsize=14, fontweight="bold",
            color="red",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8},
        )

    # Draw doors
    for door in floor_plan.doors:
        ax.plot(door.position.x, door.position.y, "s", color="brown", markersize=6)

    ax.set_title("Floor Plan - Room Classification")
    ax.autoscale()
    ax.invert_yaxis()  # CAD coordinate system
    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


async def classify_rooms(
    floor_plan: FloorPlanData,
    rooms: list[RoomPolygon],
    work_dir: Path,
    language: str = "en",
) -> list[RoomPolygon]:
    """Classify rooms using OpenRouter Vision API.

    Renders the floor plan to an image, sends it to the vision model,
    and updates room types based on the response.

    Args:
        floor_plan: The parsed floor plan data.
        rooms: Detected room polygons to classify.
        work_dir: Working directory for temporary files.

    Returns:
        Updated room polygons with classifications.
    """
    if not rooms:
        return rooms

    prompt = CLASSIFICATION_PROMPT_DE if language == "de" else CLASSIFICATION_PROMPT_EN

    # For very large room counts, use heuristic directly (Vision API can't
    # handle 100+ rooms in a single image reliably)
    MAX_ROOMS_FOR_VISION = 80
    if len(rooms) > MAX_ROOMS_FOR_VISION:
        logger.info("Too many rooms (%d) for Vision API, using heuristic classification",
                     len(rooms))
        return _heuristic_classify(rooms, floor_plan, language)

    # Render floor plan with numbered rooms
    image_path = work_dir / "classification_input.png"
    _render_floor_plan_image(floor_plan, rooms, image_path)

    logger.info("Sending floor plan image to Vision API for classification...")

    MAX_VISION_RETRIES = 2
    for attempt in range(MAX_VISION_RETRIES + 1):
        try:
            response_text = await call_vision_api(image_path, prompt)

            classifications = _parse_classification_response(response_text)

            # Apply classifications - normalize IDs to int for matching
            class_map = {}
            for c in classifications:
                try:
                    class_map[int(c["id"])] = c
                except (ValueError, TypeError):
                    class_map[c["id"]] = c

            for room in rooms:
                if room.id in class_map:
                    info = class_map[room.id]
                    try:
                        room.room_type = RoomType(info["type"])
                    except ValueError:
                        room.room_type = RoomType.UNKNOWN
                    room.label = info.get("label", "")

            classified = sum(1 for r in rooms if r.room_type != RoomType.UNKNOWN)
            logger.info("Classified %d/%d rooms via Vision API (attempt %d)",
                        classified, len(rooms), attempt + 1)

            # If Vision API classified too few and we have retries left, try again
            if classified < len(rooms) * 0.3 and attempt < MAX_VISION_RETRIES:
                logger.warning(
                    "Only %d/%d classified — retrying Vision API (attempt %d/%d)",
                    classified, len(rooms), attempt + 1, MAX_VISION_RETRIES + 1,
                )
                # Reset unclassified rooms for retry
                for room in rooms:
                    if room.room_type == RoomType.UNKNOWN:
                        room.label = ""
                continue

            # Supplement remaining unknowns with heuristic
            if classified < len(rooms):
                logger.info("Supplementing %d unclassified rooms with heuristic",
                            len(rooms) - classified)
                rooms = _heuristic_classify_unclassified(rooms, floor_plan, language)

            break  # Success — exit retry loop

        except Exception as e:
            if attempt < MAX_VISION_RETRIES:
                logger.warning("Vision API attempt %d failed: %s — retrying",
                               attempt + 1, e)
                continue
            logger.error("Vision API classification failed after %d attempts: %s",
                         MAX_VISION_RETRIES + 1, e)
            logger.info("Falling back to heuristic classification")
            rooms = _heuristic_classify(rooms, floor_plan, language)

    return rooms


def _parse_classification_response(response_text: str) -> list[dict]:
    """Parse JSON from Vision API response with robust error handling.

    Handles common LLM output quirks: markdown code blocks, trailing commas,
    single quotes, comments, and other non-standard JSON.
    """
    json_text = response_text.strip()

    # Remove markdown code blocks
    if "```" in json_text:
        # Extract content between first ``` and last ```
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", json_text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()

    # Extract JSON array if surrounded by other text
    if not json_text.startswith("["):
        start = json_text.find("[")
        end = json_text.rfind("]")
        if start != -1 and end != -1:
            json_text = json_text[start:end + 1]

    # Fix common JSON issues from LLMs
    # Remove trailing commas before ] or }
    json_text = re.sub(r",\s*([}\]])", r"\1", json_text)
    # Remove single-line comments
    json_text = re.sub(r"//[^\n]*", "", json_text)

    logger.info("Parsing classification response (%d chars)", len(json_text))

    return json.loads(json_text)


def _heuristic_classify_unclassified(rooms: list[RoomPolygon], floor_plan: FloorPlanData, language: str = "en") -> list[RoomPolygon]:
    """Apply heuristic classification only to rooms still marked as UNKNOWN."""
    if not rooms:
        return rooms

    areas = [r.area for r in rooms]
    median_area = sorted(areas)[len(areas) // 2]

    for room in rooms:
        if room.room_type != RoomType.UNKNOWN:
            continue  # Already classified by Vision API

        coords = [(p.x, p.y) for p in room.points]
        poly = Polygon(coords)
        bounds = poly.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        aspect_ratio = max(width, height) / max(min(width, height), 0.01)

        if aspect_ratio > 4 and room.area > median_area * 0.3:
            room.room_type = RoomType.CORRIDOR
            room.label = tr_room_label("corridor", language)
        elif room.area < median_area * 0.2:
            room.room_type = RoomType.BATHROOM
            room.label = tr_room_label("bathroom", language)
        elif room.area < median_area * 0.4:
            room.room_type = RoomType.STORAGE
            room.label = tr_room_label("storage", language)
        elif room.area < median_area * 2:
            room.room_type = RoomType.OFFICE
            room.label = tr_room_label("office", language)
        else:
            room.room_type = RoomType.LOBBY
            room.label = tr_room_label("lobby", language)

    return rooms


def _heuristic_classify(rooms: list[RoomPolygon], floor_plan: FloorPlanData, language: str = "en") -> list[RoomPolygon]:
    """Fallback heuristic classification based on geometry."""
    if not rooms:
        return rooms

    areas = [r.area for r in rooms]
    median_area = sorted(areas)[len(areas) // 2]

    for room in rooms:
        coords = [(p.x, p.y) for p in room.points]
        poly = Polygon(coords)
        bounds = poly.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        aspect_ratio = max(width, height) / max(min(width, height), 0.01)

        # Long narrow rooms -> corridor
        if aspect_ratio > 4 and room.area > median_area * 0.3:
            room.room_type = RoomType.CORRIDOR
            room.label = tr_room_label("corridor", language)
        # Very small rooms -> bathroom or storage
        elif room.area < median_area * 0.2:
            room.room_type = RoomType.BATHROOM
            room.label = tr_room_label("bathroom", language)
        # Small rooms -> storage
        elif room.area < median_area * 0.4:
            room.room_type = RoomType.STORAGE
            room.label = tr_room_label("storage", language)
        # Medium rooms -> office
        elif room.area < median_area * 2:
            room.room_type = RoomType.OFFICE
            room.label = tr_room_label("office", language)
        # Large rooms -> lobby or conference
        else:
            room.room_type = RoomType.LOBBY
            room.label = tr_room_label("lobby", language)

    return rooms
