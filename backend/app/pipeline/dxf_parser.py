"""DXF file parsing using ezdxf - extracts walls, doors, stairs, and other entities."""

import logging
import math
import re
from pathlib import Path
from statistics import median

import ezdxf
from ezdxf.entities import Arc, Circle, Insert, Line, LWPolyline
from shapely.geometry import LineString, box

from app.models.schemas import DoorInfo, FloorPlanData, Point, StairInfo, WallSegment

logger = logging.getLogger(__name__)

# Common layer name patterns for architectural elements (multilingual)
WALL_PATTERNS = [
    "wall", "wand", "mauer", "a-wall", "a_wall", "ar-wall",
    "s-wall", "struct", "bearing", "tragend", "partition",
    # Vietnamese (DWGShare.com)
    "tuong", "xay",
    # French
    "mur",
    # Spanish
    "pared", "muros",
]
DOOR_PATTERNS = [
    "door", "tuer", "tür", "a-door", "a_door", "ar-door",
    "opening", "oeffnung", "öffnung",
    # Vietnamese
    "cua",
    # French / Spanish
    "porte", "puerta",
]
STAIR_PATTERNS = [
    "stair", "treppe", "a-stair", "a_stair", "ar-stair",
    "step", "stufe",
    # Vietnamese
    "cau thang", "thang",
    # Spanish
    "escalera",
]
FURNITURE_PATTERNS = [
    "furn", "möbel", "moebel", "equip", "einricht",
    "appliance", "geraet", "gerät",
    # Vietnamese
    "thietbi", "noi that",
    # Spanish
    "mueble",
]
DIMENSION_PATTERNS = [
    "dim", "mass", "vermassung", "anno", "text", "note",
    "label", "beschrift",
    # Vietnamese
    "ghi chu", "kthuoc", "ten phong",
    # Spanish
    "texto", "acotado",
]
HATCH_PATTERNS = [
    "hatch", "schraffur", "fill", "pattern",
    "hatch_", "net hatch", "hacth",
    # Vietnamese
    "vua trat", "gar-trat",
]
FIRE_WALL_PATTERNS = [
    "brandwand", "fire_wall", "fw-", "brandschutzwand",
    "firewall", "fire-wall", "brand_wand",
]
FIRE_DOOR_PATTERNS = [
    "brandschutz", "fire_door", "t30", "t60", "t90",
    "ei30", "ei60", "ei90", "firedoor", "brand_tuer",
]
WINDOW_PATTERNS = [
    "window", "fenster", "glazing", "verglasung",
    "cua so", "ventana", "fenetre",
]
SPRINKLER_PATTERNS = [
    "sprinkler", "sprink", "spk", "suppression",
    "loeschanlage", "löschanlage",
]

# Layers to always skip
SKIP_PATTERNS = FURNITURE_PATTERNS + DIMENSION_PATTERNS + HATCH_PATTERNS + [
    "defpoints", "viewport", "title", "border", "frame",
    "lighting", "ceiling", "fixtures", "heating",
    # Spanish (non-structural)
    "electrica", "vidrio", "fachada", "cimiento",
]

# Block name patterns for doors (INSERT entities)
DOOR_BLOCK_PATTERNS = [
    "door", "tuer", "tür", "cua", "porte", "puerta",
    "dr_", "d_sing", "d_doub", "sgl_door", "dbl_door",
    "swing", "slide",
]

# Block name patterns for windows (skip)
WINDOW_BLOCK_PATTERNS = [
    "window", "fenster", "cua so", "ventana", "fenetre",
]


def _matches_patterns(layer_name: str, patterns: list[str]) -> bool:
    """Check if a layer name matches any of the given patterns (case-insensitive)."""
    name_lower = layer_name.lower()
    return any(p in name_lower for p in patterns)


def _is_anonymized_layer(layer_name: str) -> bool:
    """Check if the layer name is anonymized (e.g. DWGshare.com_X)."""
    lower = layer_name.lower()
    return "dwgshare" in lower or lower.startswith("layer") or lower.isdigit()


def _classify_layer(layer_name: str) -> str:
    """Classify a layer by name pattern. Returns: fire_wall, fire_door, window, wall, door, stair, skip, or unknown."""
    if _matches_patterns(layer_name, FIRE_WALL_PATTERNS):
        return "fire_wall"
    if _matches_patterns(layer_name, FIRE_DOOR_PATTERNS):
        return "fire_door"
    if _matches_patterns(layer_name, WINDOW_PATTERNS):
        return "window"
    if _matches_patterns(layer_name, SPRINKLER_PATTERNS):
        return "sprinkler"
    if _matches_patterns(layer_name, WALL_PATTERNS):
        return "wall"
    if _matches_patterns(layer_name, DOOR_PATTERNS):
        return "door"
    if _matches_patterns(layer_name, STAIR_PATTERNS):
        return "stair"
    if _matches_patterns(layer_name, SKIP_PATTERNS):
        return "skip"
    return "unknown"


def _extract_line_coords(entity) -> list[tuple[float, float]] | None:
    """Extract 2D coordinates from a DXF entity."""
    if isinstance(entity, Line):
        return [
            (entity.dxf.start.x, entity.dxf.start.y),
            (entity.dxf.end.x, entity.dxf.end.y),
        ]
    elif isinstance(entity, LWPolyline):
        points = [(p[0], p[1]) for p in entity.get_points(format="xy")]
        if len(points) >= 2:
            return points
    elif isinstance(entity, Arc):
        # Approximate arc with line segments
        arc_points = []
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)

        if end_angle < start_angle:
            end_angle += 2 * math.pi

        num_segments = max(8, int((end_angle - start_angle) / (math.pi / 16)))
        for i in range(num_segments + 1):
            angle = start_angle + (end_angle - start_angle) * i / num_segments
            arc_points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        return arc_points

    return None


def _is_door_arc(entity) -> DoorInfo | None:
    """Detect if an ARC entity represents a door swing.

    Door arcs are quarter-circles (80-100°) or wider swings (up to 150°).
    Only checks sweep angle; radius filtering happens later.
    """
    if not isinstance(entity, Arc):
        return None

    start_deg = entity.dxf.start_angle
    end_deg = entity.dxf.end_angle
    sweep = end_deg - start_deg
    if sweep < 0:
        sweep += 360

    # Accept 80-150° arcs (standard 90° doors + wider swing doors)
    if not (80 <= sweep <= 150):
        return None

    r = entity.dxf.radius
    cx, cy = entity.dxf.center.x, entity.dxf.center.y
    return DoorInfo(
        position=Point(x=cx, y=cy),
        width=r,
    )


def _filter_arc_doors(arc_doors: list[DoorInfo]) -> list[DoorInfo]:
    """Filter arc-detected doors using statistical clustering on radii.

    Instead of bounds-based thresholds (which fail with coordinate offsets),
    uses the distribution of arc radii to identify the most common door size
    and filters outliers.
    """
    if not arc_doors or len(arc_doors) < 2:
        return arc_doors

    radii = sorted(d.width for d in arc_doors)
    med_r = median(radii)

    if med_r <= 0:
        return arc_doors

    # Accept radii within 5x of median (generous range for mixed door sizes).
    # This handles any unit system: if most doors are ~0.9m, filter accepts 0.18m-4.5m.
    # If most doors are ~900mm, filter accepts 180mm-4500mm.
    min_r = med_r / 5
    max_r = med_r * 5

    filtered = [d for d in arc_doors if min_r <= d.width <= max_r]

    # Sanity cap: if still too many, likely false positives
    if len(filtered) > 200:
        logger.warning("Arc door filter: too many (%d) — likely false positives, skipping",
                        len(filtered))
        return []

    if len(filtered) < len(arc_doors):
        logger.info("Arc door filter: %d -> %d (median radius=%g, range %g-%g)",
                     len(arc_doors), len(filtered), med_r, min_r, max_r)
    return filtered


def _deduplicate_doors(doors: list[DoorInfo], tolerance: float = 5.0) -> list[DoorInfo]:
    """Remove duplicate doors that are very close together.

    When the same opening is detected by both arc detection and layer-based
    detection, we can get near-identical DoorInfo entries.  This merges
    doors whose positions are within *tolerance* plan units.
    """
    if len(doors) <= 1:
        return doors

    # Sort by x then y for deterministic order
    sorted_doors = sorted(doors, key=lambda d: (d.position.x, d.position.y))
    unique: list[DoorInfo] = [sorted_doors[0]]

    for door in sorted_doors[1:]:
        dx = door.position.x - unique[-1].position.x
        dy = door.position.y - unique[-1].position.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > tolerance:
            unique.append(door)
        else:
            # Keep the one with the more reasonable width
            if abs(door.width - 30) < abs(unique[-1].width - 30):
                unique[-1] = door

    if len(unique) < len(doors):
        logger.info("Door dedup: %d -> %d (tolerance=%g)", len(doors), len(unique), tolerance)
    return unique


def _detect_wall_gap_doors(walls: list[WallSegment], unit: str) -> list[DoorInfo]:
    """Detect doors by finding gaps in wall segments.

    When two wall segment endpoints are close together (within typical door
    width) and approximately collinear, the gap likely represents a door
    opening.  This method works even when the DXF has no explicit door
    symbols.
    """
    if len(walls) < 2:
        return []

    # Typical door widths in plan units
    unit_to_mm = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8}
    u2mm = unit_to_mm.get(unit, 1.0)

    # Door width range: 600mm–2500mm in real-world, converted to plan units
    min_gap = 600 / u2mm
    max_gap = 2500 / u2mm

    # Build a list of all wall endpoints
    endpoints: list[tuple[float, float, float, float]] = []  # (x, y, wall_dx, wall_dy)
    for w in walls:
        dx = w.end.x - w.start.x
        dy = w.end.y - w.start.y
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.01:
            continue
        ndx, ndy = dx / length, dy / length
        endpoints.append((w.start.x, w.start.y, ndx, ndy))
        endpoints.append((w.end.x, w.end.y, ndx, ndy))

    if len(endpoints) < 4:
        return []

    # Use spatial bucketing for efficient neighbor search
    bucket_size = max_gap * 1.5
    buckets: dict[tuple[int, int], list[int]] = {}
    for idx, (ex, ey, _, _) in enumerate(endpoints):
        bx, by = int(ex / bucket_size), int(ey / bucket_size)
        for dx_b in (-1, 0, 1):
            for dy_b in (-1, 0, 1):
                key = (bx + dx_b, by + dy_b)
                buckets.setdefault(key, []).append(idx)

    doors: list[DoorInfo] = []
    used: set[int] = set()

    for i, (x1, y1, dx1, dy1) in enumerate(endpoints):
        if i in used:
            continue
        bx, by = int(x1 / bucket_size), int(y1 / bucket_size)
        candidates = buckets.get((bx, by), [])

        for j in candidates:
            if j <= i or j in used:
                continue
            x2, y2, dx2, dy2 = endpoints[j]
            gap_dx = x2 - x1
            gap_dy = y2 - y1
            gap = math.sqrt(gap_dx * gap_dx + gap_dy * gap_dy)

            if not (min_gap <= gap <= max_gap):
                continue

            # Check collinearity: the two wall directions should be similar
            dot = abs(dx1 * dx2 + dy1 * dy2)
            if dot < 0.85:  # ~32° tolerance
                continue

            # Check that the gap direction is roughly perpendicular to wall direction
            if gap > 0:
                gap_ndx, gap_ndy = gap_dx / gap, gap_dy / gap
                perp = abs(dx1 * gap_ndx + dy1 * gap_ndy)
                if perp > 0.5:  # gap should be mostly perpendicular
                    continue

            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            doors.append(DoorInfo(
                position=Point(x=mid_x, y=mid_y),
                width=gap,
            ))
            used.add(i)
            used.add(j)

    if doors:
        logger.info("Wall-gap door detection found %d potential doors", len(doors))
    return doors


def _detect_insert_doors(msp, doc) -> list[DoorInfo]:
    """Detect doors from INSERT (block reference) entities.

    Uses two strategies:
    1. Block name matching (works for non-obfuscated files)
    2. Block geometry analysis (works for DWGshare.com obfuscated files)
       — looks for blocks containing a ~90° arc (door swing pattern)
    """
    doors = []
    # Cache block analysis results
    block_is_door: dict[str, bool] = {}

    for entity in msp:
        if not isinstance(entity, Insert):
            continue
        block_name = entity.dxf.name

        # Skip anonymous blocks (*U, *X, etc.)
        if block_name.startswith("*"):
            continue

        block_lower = block_name.lower()

        # Skip windows
        if _matches_patterns(block_lower, WINDOW_BLOCK_PATTERNS):
            continue

        is_door = False

        # Strategy 1: Name-based detection
        if _matches_patterns(block_lower, DOOR_BLOCK_PATTERNS):
            is_door = True

        # Strategy 2: Geometry-based detection for obfuscated blocks
        if not is_door and block_name not in block_is_door:
            block_is_door[block_name] = _analyze_block_for_door(doc, block_name)
        if not is_door:
            is_door = block_is_door.get(block_name, False)

        if is_door:
            pos = entity.dxf.insert
            sx = getattr(entity.dxf, "xscale", 1.0) or 1.0
            width = abs(sx) * 900  # Typical door ~900mm
            doors.append(DoorInfo(
                position=Point(x=pos.x, y=pos.y),
                width=width,
            ))

    return doors


def _analyze_block_for_door(doc, block_name: str) -> bool:
    """Analyze a block definition's geometry to detect door patterns.

    A door block typically contains:
    - One ~90° arc (the swing arc)
    - One or two lines (the door leaf)
    The combination is a universal CAD door symbol.
    """
    try:
        block = doc.blocks.get(block_name)
        if block is None:
            return False
    except Exception:
        return False

    has_door_arc = False
    line_count = 0
    entity_count = 0

    for entity in block:
        entity_count += 1
        if entity_count > 50:
            # Block too complex — not a simple door symbol
            return False

        if isinstance(entity, Arc):
            start_deg = entity.dxf.start_angle
            end_deg = entity.dxf.end_angle
            sweep = end_deg - start_deg
            if sweep < 0:
                sweep += 360
            # Door swing: 80-150° arc
            if 80 <= sweep <= 150:
                has_door_arc = True
        elif isinstance(entity, (Line, LWPolyline)):
            line_count += 1

    # A door block: has a swing arc and at least 1 line, and is simple (<20 entities)
    return has_door_arc and line_count >= 1 and entity_count <= 20


def _simplify_walls(walls: list[WallSegment], tolerance: float = 1.0) -> list[WallSegment]:
    """Merge nearly-collinear wall segments to reduce count.

    Groups wall segments by angle and merges overlapping/adjacent ones.
    """
    if len(walls) <= 5000:
        return walls  # No need to simplify small sets

    # Remove very short segments (noise)
    min_length = tolerance * 2
    filtered = []
    for w in walls:
        dx = w.end.x - w.start.x
        dy = w.end.y - w.start.y
        if math.sqrt(dx * dx + dy * dy) >= min_length:
            filtered.append(w)

    if len(filtered) < len(walls):
        logger.info("Wall simplification: removed %d short segments (%d -> %d)",
                     len(walls) - len(filtered), len(walls), len(filtered))

    return filtered


# German floor label patterns (used for layout detection and filename parsing)
_FLOOR_PATTERN = re.compile(
    r"^(UG|KG|EG|DG|"            # Simple labels: Untergeschoss, Keller, Erdgeschoss, Dach
    r"\d+\.?\s*OG|"              # e.g. 1.OG, 2OG, 3. OG
    r"\d+\.?\s*UG|"              # e.g. 1.UG, 2UG
    r"GF|B\d+|L\d+)$",          # Ground Floor, Basement 1, Level 1
    re.IGNORECASE,
)

# Standard floor ordering for consistent display
_FLOOR_ORDER = {
    "2.UG": 0, "1.UG": 1, "UG": 2, "KG": 2,
    "EG": 3, "GF": 3,
    "1.OG": 4, "2.OG": 5, "3.OG": 6, "4.OG": 7, "5.OG": 8,
    "DG": 9,
}


def _detect_floors(doc, filepath: Path) -> tuple[list[str], str]:
    """Detect floor names from DXF layouts and filename.

    Returns:
        Tuple of (floor_list, current_floor_label).
        floor_list: Sorted list of detected floor labels.
        current_floor_label: Best guess for the current floor (from filename or "EG").
    """
    floors: set[str] = set()
    current_floor = ""

    # Strategy 1: Check DXF layout tab names
    try:
        for layout in doc.layouts:
            name = layout.name.strip()
            if name.lower() in ("model", "model_space", "*model_space"):
                continue
            # Check if layout name matches a floor pattern
            if _FLOOR_PATTERN.match(name):
                floors.add(name.upper().replace(" ", ""))
    except Exception:
        pass  # Some DXF files have broken layout definitions

    # Strategy 2: Extract floor from filename
    stem = filepath.stem.upper().replace(" ", "").replace("_", ".")
    # Try common filename patterns: "Building_1OG", "Plan_EG", etc.
    for part in re.split(r"[_\-\s.]+", filepath.stem):
        if _FLOOR_PATTERN.match(part.strip()):
            current_floor = part.strip().upper().replace(" ", "")
            floors.add(current_floor)
            break

    # Sort floors by building order
    sorted_floors = sorted(
        floors,
        key=lambda f: _FLOOR_ORDER.get(f, 3 + int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 3),
    )

    if not current_floor:
        current_floor = sorted_floors[0] if sorted_floors else ""

    return sorted_floors, current_floor


class DXFParseError(Exception):
    """Raised when a DXF file cannot be parsed."""


def parse_dxf(filepath: str | Path) -> FloorPlanData:
    """Parse a DXF file and extract architectural elements.

    Uses layer-name classification with fallback to geometric heuristics
    for anonymized layers (e.g. DWGShare.com files).

    Args:
        filepath: Path to the DXF file.

    Returns:
        FloorPlanData with extracted walls, doors, stairs.

    Raises:
        DXFParseError: If the file is missing, corrupt, or unreadable.
    """
    filepath = Path(filepath)
    logger.info("Parsing DXF: %s", filepath)

    if not filepath.exists():
        raise DXFParseError(f"DXF file not found: {filepath}")

    if filepath.stat().st_size == 0:
        raise DXFParseError(f"DXF file is empty: {filepath}")

    try:
        doc = ezdxf.readfile(str(filepath))
    except ezdxf.DXFError as exc:
        raise DXFParseError(f"Invalid or corrupt DXF file: {exc}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise DXFParseError(f"Cannot read DXF file: {exc}") from exc

    msp = doc.modelspace()

    # Detect unit early so arc door detection can use radius thresholds
    unit_code = doc.header.get("$INSUNITS", 0)
    unit_map = {1: "in", 2: "ft", 4: "mm", 5: "cm", 6: "m"}
    unit = unit_map.get(unit_code, "mm")

    walls: list[WallSegment] = []
    doors: list[DoorInfo] = []
    stairs: list[StairInfo] = []
    fire_walls: list[WallSegment] = []
    fire_doors: list[DoorInfo] = []
    windows: list[WallSegment] = []
    has_sprinkler = False
    unknown_lines: list[WallSegment] = []
    arc_doors: list[DoorInfo] = []  # Doors detected from arc geometry

    # Collect all line geometries for bounds calculation
    all_coords: list[tuple[float, float]] = []

    # Track layer statistics
    layer_stats: dict[str, int] = {}
    has_anonymized_layers = False

    entity_errors = 0
    for entity in msp:
        try:
            layer_name = entity.dxf.layer if hasattr(entity.dxf, "layer") else "0"
            layer_class = _classify_layer(layer_name)
            layer_stats[layer_name] = layer_stats.get(layer_name, 0) + 1

            if _is_anonymized_layer(layer_name):
                has_anonymized_layers = True

            if layer_class == "skip":
                continue

            # Sprinkler detection: flag based on layer name alone (no geometry needed)
            if layer_class == "sprinkler":
                has_sprinkler = True
                # Still extract coords for bounds calculation below

            # Detect door swing arcs regardless of layer classification
            if isinstance(entity, Arc):
                door_info = _is_door_arc(entity)
                if door_info:
                    arc_doors.append(door_info)
                    all_coords.append((door_info.position.x, door_info.position.y))
                    # Don't add to walls — this arc is a door swing
                    continue

            coords = _extract_line_coords(entity)
            if coords is None:
                continue

            all_coords.extend(coords)

            if layer_class == "wall":
                # Create wall segments from consecutive point pairs
                for i in range(len(coords) - 1):
                    walls.append(WallSegment(
                        start=Point(x=coords[i][0], y=coords[i][1]),
                        end=Point(x=coords[i + 1][0], y=coords[i + 1][1]),
                    ))
            elif layer_class == "door":
                if len(coords) >= 2:
                    mid_x = sum(c[0] for c in coords) / len(coords)
                    mid_y = sum(c[1] for c in coords) / len(coords)
                    line = LineString(coords)
                    doors.append(DoorInfo(
                        position=Point(x=mid_x, y=mid_y),
                        width=line.length,
                    ))
            elif layer_class == "stair":
                stairs.append(StairInfo(
                    polygon=[Point(x=c[0], y=c[1]) for c in coords]
                ))
            elif layer_class == "fire_wall":
                for i in range(len(coords) - 1):
                    fire_walls.append(WallSegment(
                        start=Point(x=coords[i][0], y=coords[i][1]),
                        end=Point(x=coords[i + 1][0], y=coords[i + 1][1]),
                        thickness=0.4,
                    ))
            elif layer_class == "fire_door":
                if len(coords) >= 2:
                    mid_x = sum(c[0] for c in coords) / len(coords)
                    mid_y = sum(c[1] for c in coords) / len(coords)
                    line = LineString(coords)
                    fire_doors.append(DoorInfo(
                        position=Point(x=mid_x, y=mid_y),
                        width=line.length,
                        fire_rating="T30",  # default, can be refined
                    ))
            elif layer_class == "window":
                for i in range(len(coords) - 1):
                    windows.append(WallSegment(
                        start=Point(x=coords[i][0], y=coords[i][1]),
                        end=Point(x=coords[i + 1][0], y=coords[i + 1][1]),
                        thickness=0.1,
                    ))
            elif layer_class == "sprinkler":
                has_sprinkler = True
            elif layer_class == "unknown":
                # Treat unknown layers as potential walls based on lineweight
                lineweight = getattr(entity.dxf, "lineweight", 0)
                if lineweight and lineweight >= 30:  # ~0.3mm, typical wall thickness
                    for i in range(len(coords) - 1):
                        walls.append(WallSegment(
                            start=Point(x=coords[i][0], y=coords[i][1]),
                            end=Point(x=coords[i + 1][0], y=coords[i + 1][1]),
                        ))
                else:
                    for i in range(len(coords) - 1):
                        unknown_lines.append(WallSegment(
                            start=Point(x=coords[i][0], y=coords[i][1]),
                            end=Point(x=coords[i + 1][0], y=coords[i + 1][1]),
                        ))
        except Exception as exc:
            entity_errors += 1
            if entity_errors <= 5:
                logger.debug("Skipping malformed entity: %s", exc)
            continue

    if entity_errors:
        logger.warning("Skipped %d malformed entities during parsing", entity_errors)

    # Detect doors from INSERT (block reference) entities
    try:
        insert_doors = _detect_insert_doors(msp, doc)
    except Exception as exc:
        logger.warning("INSERT door detection failed (continuing without): %s", exc)
        insert_doors = []
    if insert_doors:
        logger.info("Found %d doors from INSERT block references", len(insert_doors))
        doors.extend(insert_doors)

    # If no walls found by layer name, use all unknown lines as walls
    # (many DXF files don't use standard layer names)
    if not walls and unknown_lines:
        logger.warning(
            "No wall layers found by name. Using %d unknown-layer lines as walls.",
            len(unknown_lines),
        )
        walls = unknown_lines

    # Simplify walls if there are too many segments
    walls = _simplify_walls(walls)

    # Calculate bounds (with degenerate check)
    if all_coords:
        xs = [c[0] for c in all_coords]
        ys = [c[1] for c in all_coords]
        minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
        # Prevent degenerate zero-size bounds
        if maxx <= minx:
            maxx = minx + 1.0
        if maxy <= miny:
            maxy = miny + 1.0
        bounds = (minx, miny, maxx, maxy)
    else:
        bounds = (0, 0, 1, 1)

    # Filter and add arc-detected doors (uses statistical clustering)
    if arc_doors:
        arc_doors = _filter_arc_doors(arc_doors)
        if arc_doors:
            logger.info("Found %d doors from arc swing detection", len(arc_doors))
            doors.extend(arc_doors)

    # Wall-gap door detection (finds openings as gaps between wall endpoints)
    if walls and not doors:
        gap_doors = _detect_wall_gap_doors(walls, unit)
        if gap_doors:
            doors.extend(gap_doors)

    # Deduplicate doors (arc + layer + insert can produce near-identical entries)
    if len(doors) > 1:
        doors = _deduplicate_doors(doors, tolerance=5.0)

    logger.info(
        "Parsed DXF: %d walls, %d doors, %d stairs, %d fire_walls, %d fire_doors, %d windows (sprinkler=%s, anonymized=%s). Layers: %s",
        len(walls), len(doors), len(stairs), len(fire_walls), len(fire_doors), len(windows),
        has_sprinkler, has_anonymized_layers,
        {k: v for k, v in sorted(layer_stats.items(), key=lambda x: -x[1])[:10]},
    )

    # Detect floor information from layouts and filename
    detected_floors, detected_floor_label = _detect_floors(doc, filepath)

    return FloorPlanData(
        filename=filepath.name,
        floor_label=detected_floor_label,
        floors=detected_floors,
        walls=walls,
        doors=doors,
        stairs=stairs,
        fire_walls=fire_walls,
        fire_doors=fire_doors,
        windows=windows,
        has_sprinkler=has_sprinkler,
        bounds=bounds,
        unit=unit,
    )
