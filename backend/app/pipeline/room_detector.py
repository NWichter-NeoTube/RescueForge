"""Room detection using Shapely - finds closed polygons from wall segments."""

import logging

from shapely.geometry import LineString, MultiLineString, Polygon
from shapely.ops import polygonize, unary_union

from app.models.schemas import FloorPlanData, Point, RoomPolygon

logger = logging.getLogger(__name__)

# Room area thresholds (in square drawing units)
MIN_ROOM_AREA_FACTOR = 0.0002  # Min room = 0.02% of total floor area
MAX_ROOM_AREA_FACTOR = 0.8  # Max room = 80% of total floor area


def _walls_to_lines(floor_plan: FloorPlanData) -> list[LineString]:
    """Convert wall segments to Shapely LineStrings."""
    lines = []
    for wall in floor_plan.walls:
        line = LineString([
            (wall.start.x, wall.start.y),
            (wall.end.x, wall.end.y),
        ])
        if line.length > 0:
            lines.append(line)
    return lines


def _close_gaps(lines: list[LineString], tolerance: float) -> list[LineString]:
    """Close small gaps between wall endpoints by extending/snapping.

    Uses buffer-unbuffer technique: buffer all lines slightly, union them,
    then extract the boundary lines. This effectively closes small gaps.
    """
    if not lines:
        return lines

    multi = MultiLineString(lines)

    # Buffer by tolerance, then take the boundary
    buffered = multi.buffer(tolerance, cap_style="flat", join_style="mitre")
    union = unary_union(buffered) if buffered.geom_type == "MultiPolygon" else buffered

    # The boundary of the buffered area gives us closed outlines
    boundary = union.boundary

    if boundary.is_empty:
        return lines

    # Extract individual linestrings from the boundary
    if boundary.geom_type == "MultiLineString":
        return list(boundary.geoms)
    elif boundary.geom_type == "LineString":
        return [boundary]
    else:
        return lines


def detect_rooms(floor_plan: FloorPlanData, gap_tolerance: float | None = None) -> list[RoomPolygon]:
    """Detect rooms by finding closed polygons formed by wall segments.

    Args:
        floor_plan: Parsed floor plan with wall segments.
        gap_tolerance: Maximum gap size to close (in drawing units).
                       Auto-calculated if None.

    Returns:
        List of detected room polygons.
    """
    lines = _walls_to_lines(floor_plan)
    if not lines:
        logger.warning("No wall lines found - cannot detect rooms")
        return []

    # Calculate total floor area for filtering
    minx, miny, maxx, maxy = floor_plan.bounds
    total_area = (maxx - minx) * (maxy - miny)

    if total_area <= 0:
        logger.warning("Floor plan has zero area")
        return []

    # Auto-calculate gap tolerance based on plan size
    if gap_tolerance is None:
        plan_diagonal = ((maxx - minx) ** 2 + (maxy - miny) ** 2) ** 0.5
        gap_tolerance = plan_diagonal * 0.005  # 0.5% of diagonal

    logger.info(
        "Detecting rooms from %d wall segments (gap tolerance: %.2f)",
        len(lines), gap_tolerance,
    )

    # Step 1: Try direct polygonization
    merged = unary_union(lines)
    polygons = list(polygonize(merged))

    # Step 2: If too few rooms, try closing gaps
    if len(polygons) < 2:
        logger.info("Direct polygonization found %d rooms, trying gap closing...", len(polygons))
        closed_lines = _close_gaps(lines, gap_tolerance)
        merged_closed = unary_union(closed_lines)
        polygons = list(polygonize(merged_closed))

    # Step 3: If still too few, try with larger tolerance
    if len(polygons) < 2:
        logger.info("Gap closing found %d rooms, trying larger tolerance...", len(polygons))
        closed_lines = _close_gaps(lines, gap_tolerance * 3)
        merged_closed = unary_union(closed_lines)
        polygons = list(polygonize(merged_closed))

    logger.info("Found %d candidate polygons before filtering", len(polygons))

    # Filter by area
    min_area = total_area * MIN_ROOM_AREA_FACTOR
    max_area = total_area * MAX_ROOM_AREA_FACTOR

    rooms: list[RoomPolygon] = []
    for i, poly in enumerate(polygons):
        if not poly.is_valid:
            poly = poly.buffer(0)  # Fix invalid geometry
        if not isinstance(poly, Polygon):
            continue

        area = poly.area
        if area < min_area or area > max_area:
            continue

        # Extract exterior coordinates
        coords = list(poly.exterior.coords)
        points = [Point(x=c[0], y=c[1]) for c in coords]

        rooms.append(RoomPolygon(
            id=len(rooms) + 1,
            points=points,
            area=area,
        ))

    logger.info("Detected %d rooms after filtering (area range: %.1f - %.1f)", len(rooms), min_area, max_area)
    return rooms
