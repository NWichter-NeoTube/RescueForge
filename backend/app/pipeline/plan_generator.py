"""SVG plan generator - creates DIN 14095 / FKS-compliant fire department orientation plans."""

import logging
import math
from datetime import date
from pathlib import Path

import svgwrite

from app.models.schemas import FloorPlanData, RoomPolygon, RoomType
from app.utils.symbols import (
    assembly_point_symbol,
    bma_bs,
    electricity_shutoff,
    elevator_symbol,
    erstinfo_symbol,
    fire_access_arrow,
    fire_door_symbol,
    floor_section_indicator,
    gas_shutoff,
    key_depot,
    manual_call_point,
    north_arrow,
    rwa_symbol,
    smoke_detector,
    stair_direction_arrow,
    wall_hydrant_symbol,
    water_shutoff,
)
from app.utils.translations import Locale, room_label, t

logger = logging.getLogger(__name__)

# ── Unit conversion ──────────────────────────────────────────
UNIT_TO_MM: dict[str, float] = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "ft": 304.8,
}

# Standard DIN architectural scales
DIN_SCALES = [50, 100, 200, 250, 500, 1000]


def _detect_unit_to_mm(plan_w: float, plan_h: float, declared_unit: str) -> float:
    """Detect the most likely mm-conversion factor for the plan coordinates.

    Many DXF files declare $INSUNITS incorrectly (e.g. report mm but coordinates
    are actually in inches).  This heuristic checks whether the declared unit
    produces a reasonable building size (5 m – 500 m on the longest side) and,
    if not, tries alternatives.
    """
    u2mm = UNIT_TO_MM.get(declared_unit, 1.0)
    max_dim = max(plan_w, plan_h)
    real_m = max_dim * u2mm / 1000

    if 5 <= real_m <= 500:
        return u2mm  # declared unit is reasonable

    # Try alternatives — prefer the one closest to a "typical" building (20–80 m)
    best_u2mm = u2mm
    best_score = float("inf")
    for try_unit, try_u2mm in UNIT_TO_MM.items():
        try_m = max_dim * try_u2mm / 1000
        if 5 <= try_m <= 500:
            score = abs(math.log10(try_m / 25))  # 25 m = typical building
            if score < best_score:
                best_score = score
                best_u2mm = try_u2mm
    if best_u2mm != u2mm:
        logger.info(
            "Unit auto-detect: declared=%s (%.1fm), using factor=%.1f (%.1fm)",
            declared_unit, max_dim * u2mm / 1000, best_u2mm, max_dim * best_u2mm / 1000,
        )
    return best_u2mm


def _compute_din_scale(rendering_scale: float, unit_to_mm: float) -> int:
    """Return the closest standard DIN scale ratio (e.g. 100 for 1:100).

    rendering_scale converts plan-units to SVG mm.
    unit_to_mm converts plan-units to real-world mm.
    The architectural ratio = unit_to_mm / rendering_scale.
    """
    if rendering_scale <= 0:
        return 100
    ratio = unit_to_mm / rendering_scale
    return min(DIN_SCALES, key=lambda s: abs(ratio - s))


def _area_to_m2(area_plan_units_sq: float, unit_to_mm: float) -> float:
    """Convert an area in plan-unit² to m²."""
    # plan_unit² → mm² → m²
    return area_plan_units_sq * (unit_to_mm ** 2) / 1_000_000


# ── DIN 14095 / RAL Color Scheme ─────────────────────────────
COLORS = {
    "wall": "#282828",              # RAL 9004 Signalschwarz
    "wall_stroke_width": 2.5,
    "fire_wall": "#AF2B1E",         # RAL 3000 Feuerrot
    "fire_wall_stroke_width": 5.0,
    "door": "#8B4513",
    "fire_door": "#AF2B1E",         # RAL 3000
    "window": "#87CEEB",            # Light blue for windows
    "stair": "#006400",             # Dark green for vertical escape routes
    "corridor": "#BDECB6",          # RAL 6019 Weissgrün (horizontal escape)
    "room_stroke": "#333333",
    "room_fill_default": "#F5F5F5",
    "text": "#000000",
    "danger_text": "#FF0000",
    "danger_zone": "#FFBF00",       # Signal yellow for non-passable / hazmat
    "title_bg": "#FFFFFF",
    "legend_bg": "#FFFFFF",
    "grid": "#CCCCCC",
}

# Room type to fill color mapping (DIN 14095 / FKS standard)
ROOM_COLORS: dict[RoomType, str] = {
    RoomType.STAIRWELL: "#006400",  # Dark green - vertical escape
    RoomType.CORRIDOR: "#BDECB6",   # RAL 6019 - horizontal escape
    RoomType.ELEVATOR: "#B0C4DE",
    RoomType.BATHROOM: "#ADD8E6",
    RoomType.KITCHEN: "#FFDAB9",
    RoomType.STORAGE: "#D2B48C",
    RoomType.TECHNICAL: "#FFB6C1",
    RoomType.SERVER_ROOM: "#FFB6C1",
    RoomType.GARAGE: "#C0C0C0",
    RoomType.LOBBY: "#FFFACD",
    RoomType.CONFERENCE: "#E6E6FA",
    RoomType.OFFICE: "#F0F8FF",
    RoomType.RESIDENTIAL: "#FFF8DC",
    RoomType.BEDROOM: "#E8E8E8",
    RoomType.LIVING_ROOM: "#FAFAD2",
    RoomType.BALCONY: "#98FB98",
    RoomType.UNKNOWN: "#F5F5F5",
}

# FKS: Dangerous rooms require red highlighting
DANGEROUS_ROOM_TYPES = {RoomType.TECHNICAL, RoomType.SERVER_ROOM, RoomType.GARAGE}


# ── Layout Configuration ──────────────────────────────────────
class LayoutConfig:
    """Centralised layout constants — eliminates scattered magic numbers."""

    # Paper sizes (mm, landscape)
    A3_WIDTH = 420
    A3_HEIGHT = 297
    A4_WIDTH = 297
    A4_HEIGHT = 210

    # Margins (mm)
    MARGIN = 15
    TITLE_BLOCK_HEIGHT = 38     # Extended for DIN 14095
    LEGEND_WIDTH = 60

    # SVG generation
    PLAN_PADDING = 0.95        # 5 % padding inside drawing area
    ROOM_FILL_OPACITY = 0.6
    DANGER_BORDER_WIDTH = 0.8
    LABEL_FONT_SIZE = 2.5
    AREA_FONT_SIZE = 2.0
    LARGE_ROOM_THRESHOLD = 2.0  # × median area

    # DIN 14095 minimum sizes
    MIN_SYMBOL_SIZE_MM = 7.0    # DIN 14034-6: min 7mm edge length
    MIN_FONT_SIZE_MM = 2.0      # DIN 14095: min 2mm text height (~5.7pt)

    # Wall rendering
    WALL_THICKNESS_MM = 0.8     # Filled wall polygon thickness

    # Escape route drawing
    ESCAPE_BUFFER = 1.0        # buffer for adjacency detection
    ESCAPE_AREA_THRESHOLD = 0.5
    ARROW_SIZE = 2.5

    @classmethod
    def paper_size(cls, fmt: str = "A3") -> tuple[float, float]:
        """Return (width, height) for a paper format."""
        if fmt == "A3":
            return cls.A3_WIDTH, cls.A3_HEIGHT
        return cls.A4_WIDTH, cls.A4_HEIGHT


# Keep backwards-compatible module-level aliases
A3_WIDTH = LayoutConfig.A3_WIDTH
A3_HEIGHT = LayoutConfig.A3_HEIGHT
A4_WIDTH = LayoutConfig.A4_WIDTH
A4_HEIGHT = LayoutConfig.A4_HEIGHT
MARGIN = LayoutConfig.MARGIN
TITLE_BLOCK_HEIGHT = LayoutConfig.TITLE_BLOCK_HEIGHT
LEGEND_WIDTH = LayoutConfig.LEGEND_WIDTH


# ── Centroid Cache ──────────────────────────────────────────
def _compute_room_centroids(
    rooms: list[RoomPolygon],
) -> dict[int, tuple[float, float]]:
    """Pre-compute Shapely centroids for all rooms once, avoiding duplicate work."""
    from shapely.geometry import Polygon as ShapelyPoly

    centroids: dict[int, tuple[float, float]] = {}
    for room in rooms:
        if len(room.points) < 3:
            continue
        poly = ShapelyPoly([(p.x, p.y) for p in room.points])
        c = poly.centroid
        centroids[room.id] = (c.x, c.y)
    return centroids


def _ensure_min_size(size: float) -> float:
    """Enforce DIN 14034-6 minimum symbol size (7mm)."""
    return max(size, LayoutConfig.MIN_SYMBOL_SIZE_MM)


def _ensure_min_font(size: float) -> float:
    """Enforce DIN 14095 minimum font size (2mm)."""
    return max(size, LayoutConfig.MIN_FONT_SIZE_MM)


def generate_svg(
    floor_plan: FloorPlanData,
    rooms: list[RoomPolygon],
    output_path: Path,
    paper_format: str = "A3",
    building_name: str = "Building",
    address: str = "",
    floor_label: str = "",
    language: str = "en",
    creation_date: str = "",
    plan_creator: str = "RescueForge",
    registration_number: str = "",
    page_number: str = "1",
) -> Path:
    """Generate a DIN 14095-compliant SVG orientation plan.

    Args:
        floor_plan: Parsed floor plan data.
        rooms: Classified room polygons.
        output_path: Where to save the SVG.
        paper_format: "A3" or "A4".
        building_name: Building name for title block.
        address: Building address.
        floor_label: Floor designation (e.g., "EG", "1.OG").
        language: "en" or "de" for output language.
        creation_date: ISO date string; defaults to today.
        plan_creator: Creator name for title block.
        registration_number: Registration number for title block.
        page_number: Page number string.

    Returns:
        Path to the generated SVG file.
    """
    lang: Locale = "de" if language == "de" else "en"

    # Paper dimensions
    if paper_format == "A3":
        paper_w, paper_h = A3_WIDTH, A3_HEIGHT
    else:
        paper_w, paper_h = A4_WIDTH, A4_HEIGHT

    # Drawing area (inside margins, minus title block and legend)
    draw_x = MARGIN
    draw_y = MARGIN
    draw_w = paper_w - 2 * MARGIN - LEGEND_WIDTH
    draw_h = paper_h - 2 * MARGIN - TITLE_BLOCK_HEIGHT

    # Calculate scale to fit floor plan in drawing area
    minx, miny, maxx, maxy = floor_plan.bounds
    plan_w = maxx - minx
    plan_h = maxy - miny

    if plan_w <= 0 or plan_h <= 0:
        logger.error("Floor plan has zero dimensions")
        raise ValueError("Floor plan has zero dimensions")

    # Detect real-world unit conversion factor
    unit_to_mm = _detect_unit_to_mm(plan_w, plan_h, floor_plan.unit)

    # Scale factor (drawing units to mm)
    scale_x = draw_w / plan_w
    scale_y = draw_h / plan_h
    scale = min(scale_x, scale_y) * 0.95  # 5% padding

    # Compute DIN display scale (e.g. 100 for "1:100")
    din_scale = _compute_din_scale(scale, unit_to_mm)

    # Offset to center the plan in drawing area
    offset_x = draw_x + (draw_w - plan_w * scale) / 2
    offset_y = draw_y + (draw_h - plan_h * scale) / 2

    def tx(x: float) -> float:
        """Transform X coordinate from plan to SVG."""
        return offset_x + (x - minx) * scale

    def ty(y: float) -> float:
        """Transform Y coordinate from plan to SVG (Y axis flipped)."""
        return offset_y + (maxy - y) * scale

    # Create SVG
    dwg = svgwrite.Drawing(
        str(output_path),
        size=(f"{paper_w}mm", f"{paper_h}mm"),
        viewBox=f"0 0 {paper_w} {paper_h}",
    )

    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=(paper_w, paper_h), fill="white"))

    # Border
    dwg.add(dwg.rect(
        insert=(MARGIN - 1, MARGIN - 1),
        size=(paper_w - 2 * MARGIN + 2, paper_h - 2 * MARGIN + 2),
        fill="none", stroke="black", stroke_width=0.5,
    ))

    # === 10m REFERENCE GRID (DIN 14095 §5.3) ===
    _draw_reference_grid(dwg, floor_plan, tx, ty, minx, miny, maxx, maxy, scale, draw_x, draw_y, draw_w, draw_h, unit_to_mm)

    # === ROOMS ===
    rooms_group = dwg.g(id="rooms")

    # Pre-compute centroids once (used by rooms, safety symbols, escape routes)
    centroid_cache = _compute_room_centroids(rooms)

    # Calculate median area for large-room threshold
    room_areas = sorted(r.area for r in rooms if r.area > 0)
    median_area = room_areas[len(room_areas) // 2] if room_areas else 0

    cfg = LayoutConfig  # shorthand

    # Room numbering counters
    room_counters: dict[str, int] = {}
    floor_prefix = floor_label.replace(".", "").replace("OG", "").replace("UG", "-1").replace("EG", "0") if floor_label else "0"

    # Symbol placer for collision avoidance (shared between labels and symbols)
    symbol_placer = _SymbolPlacer()

    for room in rooms:
        if len(room.points) < 3:
            continue
        points = [(tx(p.x), ty(p.y)) for p in room.points]
        fill = ROOM_COLORS.get(room.room_type, ROOM_COLORS[RoomType.UNKNOWN])

        # Non-passable / hazmat areas get signal yellow (DIN 14095)
        if room.room_type in DANGEROUS_ROOM_TYPES:
            fill = COLORS.get("danger_zone", fill)

        rooms_group.add(dwg.polygon(
            points=points,
            fill=fill,
            fill_opacity=cfg.ROOM_FILL_OPACITY,
            stroke=COLORS["room_stroke"],
            stroke_width=0.3,
        ))

        # FKS: Red dashed border for dangerous rooms
        if room.room_type in DANGEROUS_ROOM_TYPES:
            rooms_group.add(dwg.polygon(
                points=points,
                fill="none",
                stroke="#FF0000",
                stroke_width=cfg.DANGER_BORDER_WIDTH,
                stroke_dasharray="2,1",
            ))

        # Room label at centroid (from cache)
        if room.id not in centroid_cache:
            continue
        cx, cy = centroid_cache[room.id]

        # Room numbering: "Type floor.counter" (DIN 14095 §6.2)
        rt_val = room.room_type.value
        room_counters[rt_val] = room_counters.get(rt_val, 0) + 1
        room_number = f"{floor_prefix}.{room_counters[rt_val]:02d}"
        display_label = room.label or room_label(rt_val, lang)
        numbered_label = f"{display_label} {room_number}"

        label_color = COLORS["danger_text"] if room.room_type in DANGEROUS_ROOM_TYPES else COLORS["text"]
        label_font_size = _ensure_min_font(cfg.LABEL_FONT_SIZE)
        rooms_group.add(dwg.text(
            numbered_label,
            insert=(tx(cx), ty(cy)),
            text_anchor="middle",
            dominant_baseline="middle",
            font_size=str(label_font_size),
            font_family="Arial, sans-serif",
            fill=label_color,
        ))

        # Register room label with symbol placer for collision avoidance
        text_w = len(numbered_label) * label_font_size * 0.55
        text_h = label_font_size * 1.2
        symbol_placer.register(tx(cx), ty(cy), text_w, text_h)

        # FKS: Show area for large rooms
        if room.area > median_area * cfg.LARGE_ROOM_THRESHOLD and room.area > 0:
            area_m2 = _area_to_m2(room.area, unit_to_mm)
            area_text = f"A = {area_m2:.1f} m\u00b2"
            area_font_size = _ensure_min_font(cfg.AREA_FONT_SIZE)
            rooms_group.add(dwg.text(
                area_text,
                insert=(tx(cx), ty(cy) + 3.5),
                text_anchor="middle",
                dominant_baseline="middle",
                font_size=str(area_font_size),
                font_family="Arial, sans-serif",
                fill=COLORS["danger_text"] if room.room_type in DANGEROUS_ROOM_TYPES else "#666666",
            ))
            # Register area text too
            area_text_w = len(area_text) * area_font_size * 0.55
            symbol_placer.register(tx(cx), ty(cy) + 3.5, area_text_w, area_font_size * 1.2)
    dwg.add(rooms_group)

    # === WALLS (filled polygons per DIN 14095) ===
    walls_group = dwg.g(id="walls")
    wall_thickness = cfg.WALL_THICKNESS_MM
    for wall in floor_plan.walls:
        _draw_filled_wall(dwg, walls_group, wall, tx, ty, scale, wall_thickness, COLORS["wall"])
    dwg.add(walls_group)

    # === FIRE WALLS (DIN 14095 — red, double thickness) ===
    if floor_plan.fire_walls:
        fw_group = dwg.g(id="fire-walls")
        fw_thickness = wall_thickness * 2.0
        for fw in floor_plan.fire_walls:
            _draw_filled_wall(dwg, fw_group, fw, tx, ty, scale, fw_thickness, COLORS["fire_wall"])
        dwg.add(fw_group)

    # === WINDOWS ===
    if floor_plan.windows:
        win_group = dwg.g(id="windows")
        for win in floor_plan.windows:
            win_group.add(dwg.line(
                start=(tx(win.start.x), ty(win.start.y)),
                end=(tx(win.end.x), ty(win.end.y)),
                stroke=COLORS["window"],
                stroke_width=0.3,
                stroke_linecap="round",
            ))
        dwg.add(win_group)

    # === DOORS (with swing arcs) ===
    doors_group = dwg.g(id="doors")
    for door in floor_plan.doors:
        dx = tx(door.position.x)
        dy = ty(door.position.y)
        door_w = door.width * scale if door.width > 0 else 3.0
        r = door_w * 0.5

        # Door opening (gap in wall)
        doors_group.add(dwg.line(
            start=(dx - r, dy),
            end=(dx + r, dy),
            stroke="white",
            stroke_width=COLORS["wall_stroke_width"] * scale * 0.6,
        ))

        # Door leaf (line from hinge to edge)
        angle_rad = math.radians(door.angle)
        leaf_x = dx + r * math.cos(angle_rad)
        leaf_y = dy - r * math.sin(angle_rad)
        doors_group.add(dwg.line(
            start=(dx - r, dy),
            end=(leaf_x, leaf_y),
            stroke=COLORS["door"],
            stroke_width=0.4,
        ))

        # Swing arc (90-degree quarter circle)
        sweep = 1 if door.angle >= 0 else 0
        arc_path = f"M {dx + r},{dy} A {r},{r} 0 0,{sweep} {leaf_x},{leaf_y}"
        doors_group.add(dwg.path(
            d=arc_path,
            fill="none",
            stroke=COLORS["door"],
            stroke_width=0.3,
            stroke_dasharray="1,0.5",
        ))
    dwg.add(doors_group)

    # === FIRE DOORS (DIN 14095 — red with rating label) ===
    if floor_plan.fire_doors:
        fd_group = dwg.g(id="fire-doors")
        for fd in floor_plan.fire_doors:
            fdx = tx(fd.position.x)
            fdy = ty(fd.position.y)
            fd_w = fd.width * scale if fd.width > 0 else 3.0
            fd_r = fd_w * 0.5

            # Fire door rendered in red
            fd_group.add(dwg.line(
                start=(fdx - fd_r, fdy),
                end=(fdx + fd_r, fdy),
                stroke=COLORS["fire_door"],
                stroke_width=0.6,
            ))
            # Rating label
            rating = fd.fire_rating or "T30"
            fd_group.add(dwg.text(
                rating,
                insert=(fdx, fdy - 1.5),
                text_anchor="middle",
                font_size=str(_ensure_min_font(1.8)),
                font_family="Arial, sans-serif",
                fill=COLORS["fire_door"],
                font_weight="bold",
            ))
        dwg.add(fd_group)

    # === STAIRS ===
    stairs_group = dwg.g(id="stairs")
    for stair in floor_plan.stairs:
        if len(stair.polygon) < 3:
            continue
        points = [(tx(p.x), ty(p.y)) for p in stair.polygon]
        stairs_group.add(dwg.polygon(
            points=points,
            fill=COLORS["stair"],
            fill_opacity=0.4,
            stroke=COLORS["stair"],
            stroke_width=0.5,
        ))
    dwg.add(stairs_group)

    # === LEGEND ===
    _draw_legend(dwg, paper_w, rooms, floor_plan, lang)

    # === TITLE BLOCK (Extended per DIN 14095) ===
    _draw_title_block(
        dwg, paper_w, paper_h, building_name, address, floor_label,
        din_scale, plan_w, lang,
        creation_date=creation_date or date.today().isoformat(),
        plan_creator=plan_creator,
        registration_number=registration_number,
        page_number=page_number,
    )

    # === FKS SYMBOLS ===
    # North arrow (top-right of drawing area)
    na = north_arrow(dwg, paper_w - MARGIN - LEGEND_WIDTH - 10, MARGIN + 15, size=8)
    dwg.add(na)

    # Floor section indicator (below legend)
    floors = ["UG", "EG", "1.OG", "2.OG"]
    current = floor_label or "EG"
    if current not in floors:
        floors.append(current)
    fsi = floor_section_indicator(
        dwg,
        paper_w - MARGIN - LEGEND_WIDTH + 15,
        MARGIN + 160,
        floors=floors,
        current_floor=current,
    )
    dwg.add(fsi)

    # Scale bar (unit-aware)
    _draw_scale_bar(dwg, offset_x, paper_h - MARGIN - TITLE_BLOCK_HEIGHT - 8, scale, unit_to_mm)

    # === FKS SAFETY SYMBOLS ===
    _draw_safety_symbols(dwg, rooms, tx, ty, centroid_cache, floor_plan, symbol_placer)

    # === ESCAPE ROUTE LINES ===
    _draw_escape_routes(dwg, rooms, tx, ty, centroid_cache)

    # Fire access arrow (bottom-left of drawing area)
    fa = fire_access_arrow(dwg, MARGIN + 8, paper_h - MARGIN - TITLE_BLOCK_HEIGHT - 12, angle=0, size=6)
    dwg.add(fa)

    # Key depot near entrance (bottom-left)
    kd = key_depot(dwg, MARGIN + 20, paper_h - MARGIN - TITLE_BLOCK_HEIGHT - 12, size=4)
    dwg.add(kd)

    # FKS: Brandmeldezentrale (BMA-BS / fire alarm control panel)
    bmz = bma_bs(dwg, MARGIN + 32, paper_h - MARGIN - TITLE_BLOCK_HEIGHT - 12, size=5)
    dwg.add(bmz)

    # === UTILITY SHUTOFF SYMBOLS (DIN 14095 §7) ===
    shutoff_y = paper_h - MARGIN - TITLE_BLOCK_HEIGHT - 12
    dwg.add(gas_shutoff(dwg, MARGIN + 44, shutoff_y, size=_ensure_min_size(4)))
    dwg.add(water_shutoff(dwg, MARGIN + 54, shutoff_y, size=_ensure_min_size(4)))
    dwg.add(electricity_shutoff(dwg, MARGIN + 64, shutoff_y, size=_ensure_min_size(4)))

    dwg.save()
    logger.info("SVG generated: %s", output_path)
    return output_path


def _draw_filled_wall(
    dwg: svgwrite.Drawing,
    group: svgwrite.container.Group,
    wall,
    tx, ty, scale: float,
    thickness: float,
    color: str,
) -> None:
    """Draw a wall as a filled polygon (DIN 14095: vollflächig schwarz)."""
    x1, y1 = tx(wall.start.x), ty(wall.start.y)
    x2, y2 = tx(wall.end.x), ty(wall.end.y)

    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.01:
        return

    # Perpendicular offset for wall thickness
    half_t = thickness * 0.5
    nx = -dy / length * half_t
    ny = dx / length * half_t

    points = [
        (x1 + nx, y1 + ny),
        (x2 + nx, y2 + ny),
        (x2 - nx, y2 - ny),
        (x1 - nx, y1 - ny),
    ]
    group.add(dwg.polygon(
        points=points,
        fill=color,
        stroke=color,
        stroke_width=0.1,
    ))


def _draw_reference_grid(
    dwg: svgwrite.Drawing,
    floor_plan: FloorPlanData,
    tx, ty,
    minx: float, miny: float, maxx: float, maxy: float,
    scale: float,
    draw_x: float, draw_y: float, draw_w: float, draw_h: float,
    unit_to_mm: float = 1.0,
) -> None:
    """Draw 10m reference grid (DIN 14095 §5.3)."""
    grid_group = dwg.g(id="reference-grid")

    # Grid spacing = 10m expressed in plan units
    grid_spacing = 10_000.0 / unit_to_mm  # 10m = 10000mm / (mm per plan unit)

    # Prevent too-dense or too-sparse grids on paper
    grid_svg_mm = grid_spacing * scale
    if grid_svg_mm < 15:
        grid_spacing *= 2  # double to 20m
        grid_svg_mm *= 2
    if grid_svg_mm < 10:
        dwg.add(grid_group)
        return  # grid too dense, skip

    fnt = "Arial, sans-serif"

    # Draw vertical grid lines
    x_start = minx - (minx % grid_spacing) if grid_spacing > 0 else minx
    x = x_start
    max_lines = 50
    count = 0
    while x <= maxx and count < max_lines:
        if x >= minx:
            sx = tx(x)
            if draw_x <= sx <= draw_x + draw_w:
                grid_group.add(dwg.line(
                    start=(sx, draw_y), end=(sx, draw_y + draw_h),
                    stroke=COLORS["grid"], stroke_width=0.15, stroke_dasharray="2,2",
                ))
                meters = (x - minx) * unit_to_mm / 1000
                grid_group.add(dwg.text(
                    f"{int(meters)}m",
                    insert=(sx, draw_y + draw_h + 3), text_anchor="middle",
                    font_size="1.5", font_family=fnt, fill=COLORS["grid"],
                ))
        x += grid_spacing
        count += 1

    # Draw horizontal grid lines
    y_start = miny - (miny % grid_spacing) if grid_spacing > 0 else miny
    y = y_start
    count = 0
    while y <= maxy and count < max_lines:
        if y >= miny:
            sy = ty(y)
            if draw_y <= sy <= draw_y + draw_h:
                grid_group.add(dwg.line(
                    start=(draw_x, sy), end=(draw_x + draw_w, sy),
                    stroke=COLORS["grid"], stroke_width=0.15, stroke_dasharray="2,2",
                ))
                meters = (y - miny) * unit_to_mm / 1000
                grid_group.add(dwg.text(
                    f"{int(meters)}m",
                    insert=(draw_x - 2, sy + 0.5), text_anchor="end",
                    font_size="1.5", font_family=fnt, fill=COLORS["grid"],
                ))
        y += grid_spacing
        count += 1

    dwg.add(grid_group)


def _draw_legend(
    dwg: svgwrite.Drawing, paper_w: float, rooms: list[RoomPolygon],
    floor_plan: FloorPlanData, lang: Locale,
) -> None:
    """Draw the legend panel on the right side."""
    legend_x = paper_w - MARGIN - LEGEND_WIDTH + 5
    legend_y = MARGIN + 5

    dwg.add(dwg.rect(
        insert=(paper_w - MARGIN - LEGEND_WIDTH, MARGIN),
        size=(LEGEND_WIDTH, 200),
        fill=COLORS["legend_bg"],
        stroke="black",
        stroke_width=0.3,
    ))

    dwg.add(dwg.text(
        t("legend.title", lang),
        insert=(legend_x, legend_y + 5),
        font_size="4",
        font_weight="bold",
        font_family="Arial, sans-serif",
    ))

    # Escape route legend
    y = legend_y + 12
    entries = [
        (t("legend.vertical_escape", lang), COLORS["stair"]),
        (t("legend.horizontal_escape", lang), COLORS["corridor"]),
        (t("legend.danger_zone", lang), "#FF0000"),
    ]

    # Fire wall legend entry if present
    if floor_plan.fire_walls:
        entries.append((t("legend.fire_wall", lang), COLORS["fire_wall"]))

    # Fire door legend entry if present
    if floor_plan.fire_doors:
        entries.append((t("legend.fire_door", lang), COLORS["fire_door"]))

    # Non-passable area legend
    entries.append((t("legend.non_passable", lang), COLORS["danger_zone"]))

    # Add unique room types from the plan
    seen_types: set[RoomType] = set()
    for room in rooms:
        if room.room_type not in seen_types and room.room_type not in (RoomType.STAIRWELL, RoomType.CORRIDOR):
            seen_types.add(room.room_type)
            entries.append((
                room_label(room.room_type.value, lang),
                ROOM_COLORS.get(room.room_type, "#F5F5F5"),
            ))

    for label, color in entries:
        dwg.add(dwg.rect(
            insert=(legend_x, y),
            size=(4, 4),
            fill=color,
            fill_opacity=0.6,
            stroke="black",
            stroke_width=0.2,
        ))
        dwg.add(dwg.text(
            label,
            insert=(legend_x + 6, y + 3),
            font_size=str(_ensure_min_font(2.5)),
            font_family="Arial, sans-serif",
        ))
        y += 7

    # FKS symbol legend entries
    y += 3
    dwg.add(dwg.text(
        t("legend.symbols", lang),
        insert=(legend_x, y + 3),
        font_size="3",
        font_weight="bold",
        font_family="Arial, sans-serif",
    ))
    y += 8

    symbol_entries = [
        ("S", "red", t("symbol.smoke_detector", lang)),
        ("\u25B2", "red", t("symbol.manual_call_point", lang)),
        ("BMZ", "red", t("symbol.bma", lang)),
        ("\u2192", "#006400", t("symbol.escape_route", lang)),
        ("\u25B6", "#FF0000", t("symbol.fire_access", lang)),
        ("\U0001f511", "#FF0000", t("symbol.key_depot", lang)),
        ("G", "#FFD700", t("symbol.gas_shutoff", lang)),
        ("W", "#4169E1", t("symbol.water_shutoff", lang)),
        ("E", "#DC143C", t("symbol.electricity_shutoff", lang)),
    ]

    # Conditional legend entries based on detected features
    if floor_plan.has_sprinkler:
        symbol_entries.append(("SP", "#0000FF", t("symbol.sprinkler", lang)))

    for symbol, color, label in symbol_entries:
        dwg.add(dwg.text(
            symbol,
            insert=(legend_x + 2, y + 3),
            text_anchor="middle",
            font_size="3",
            font_family="Arial, sans-serif",
            fill=color,
            font_weight="bold",
        ))
        dwg.add(dwg.text(
            label,
            insert=(legend_x + 6, y + 3),
            font_size=str(_ensure_min_font(2.5)),
            font_family="Arial, sans-serif",
        ))
        y += 6


def _draw_title_block(
    dwg: svgwrite.Drawing,
    paper_w: float,
    paper_h: float,
    building_name: str,
    address: str,
    floor_label: str,
    din_scale: int,
    plan_width: float,
    lang: Locale,
    creation_date: str = "",
    plan_creator: str = "RescueForge",
    registration_number: str = "",
    page_number: str = "1",
) -> None:
    """Draw a DIN 6771 / ISO 7200-inspired title block (Schriftfeld).

    Layout (from left to right, top to bottom):
    ┌──────────────────────────────────┬──────────────┬──────────┐
    │  Title: Orientation Plan         │  Scale 1:N   │ Reg.Nr.  │
    ├──────────────────────────────────┤              │ Page     │
    │  Object: …     │ Floor: …      ├──────────────┤          │
    ├──────────────────────────────────┤ Creator      └──────────┤
    │  Address: …                      │ Created:     │ DIN 14095│
    │  Created: …  │  Revised: …      │ Revised:     │          │
    └──────────────────────────────────┴──────────────┴──────────┘
    """
    tb_y = paper_h - MARGIN - TITLE_BLOCK_HEIGHT
    tb_w = paper_w - 2 * MARGIN
    tb_h = TITLE_BLOCK_HEIGHT

    # === Outer frame ===
    dwg.add(dwg.rect(
        insert=(MARGIN, tb_y), size=(tb_w, tb_h),
        fill=COLORS["title_bg"], stroke="black", stroke_width=0.5,
    ))

    # Column widths
    col1_w = tb_w * 0.55   # left: building info
    col2_w = tb_w * 0.25   # middle: scale/creator
    col3_w = tb_w * 0.20   # right: registration/standard

    col2_x = MARGIN + col1_w
    col3_x = col2_x + col2_w

    # Vertical dividers
    dwg.add(dwg.line(start=(col2_x, tb_y), end=(col2_x, tb_y + tb_h),
                     stroke="black", stroke_width=0.3))
    dwg.add(dwg.line(start=(col3_x, tb_y), end=(col3_x, tb_y + tb_h),
                     stroke="black", stroke_width=0.3))

    # Horizontal divider at 50% height
    mid_y = tb_y + tb_h * 0.5
    dwg.add(dwg.line(start=(MARGIN, mid_y), end=(MARGIN + col1_w, mid_y),
                     stroke="black", stroke_width=0.2))

    fnt = "Arial, sans-serif"

    # === Column 1 — Building Info (top half) ===
    dwg.add(dwg.text(
        t("title.orientation_plan", lang),
        insert=(MARGIN + 4, tb_y + 6),
        font_size="5", font_weight="bold", font_family=fnt,
    ))
    dwg.add(dwg.text(
        f"{t('title.object', lang)}: {building_name}",
        insert=(MARGIN + 4, tb_y + 12),
        font_size="3.5", font_family=fnt,
    ))
    if floor_label:
        dwg.add(dwg.text(
            f"{t('title.floor', lang)}: {floor_label}",
            insert=(MARGIN + col1_w * 0.55, tb_y + 12),
            font_size="3.5", font_family=fnt,
        ))
    if address:
        dwg.add(dwg.text(
            f"{t('title.address', lang)}: {address}",
            insert=(MARGIN + 4, tb_y + 17),
            font_size="3", font_family=fnt,
        ))

    # === Column 1 — Dates (bottom half) ===
    if creation_date:
        dwg.add(dwg.text(
            f"{t('title.creation_date', lang)}: {creation_date}",
            insert=(MARGIN + 4, mid_y + 6),
            font_size=str(_ensure_min_font(2.0)), font_family=fnt,
        ))
    dwg.add(dwg.text(
        f"{t('title.revision_date', lang)}: {date.today().isoformat()}",
        insert=(MARGIN + 4, mid_y + 12),
        font_size=str(_ensure_min_font(2.0)), font_family=fnt,
    ))

    # === Column 2 — Scale & Creator ===
    scale_text = f"{t('title.scale', lang)}: 1:{din_scale}" if din_scale > 0 else ""
    dwg.add(dwg.text(
        scale_text,
        insert=(col2_x + col2_w / 2, tb_y + 8),
        text_anchor="middle",
        font_size="4", font_weight="bold", font_family=fnt,
    ))
    dwg.add(dwg.text(
        f"{t('title.creator', lang)}: {plan_creator}",
        insert=(col2_x + col2_w / 2, tb_y + 16),
        text_anchor="middle",
        font_size="3", font_family=fnt,
    ))
    # Credit
    dwg.add(dwg.text(
        t("title.created_with", lang),
        insert=(col2_x + col2_w / 2, mid_y + 10),
        text_anchor="middle",
        font_size="2", font_family=fnt, fill="#888888",
    ))

    # === Column 3 — Registration & Standard ===
    if registration_number:
        dwg.add(dwg.text(
            f"{t('title.registration', lang)}",
            insert=(col3_x + col3_w / 2, tb_y + 5),
            text_anchor="middle",
            font_size=str(_ensure_min_font(2.0)), font_family=fnt, fill="#666666",
        ))
        dwg.add(dwg.text(
            registration_number,
            insert=(col3_x + col3_w / 2, tb_y + 10),
            text_anchor="middle",
            font_size=str(_ensure_min_font(2.5)), font_weight="bold", font_family=fnt,
        ))
    dwg.add(dwg.text(
        f"{t('title.page', lang)} {page_number}",
        insert=(col3_x + col3_w / 2, tb_y + 17),
        text_anchor="middle",
        font_size=str(_ensure_min_font(2.0)), font_family=fnt,
    ))
    # Standard reference
    dwg.add(dwg.text(
        "DIN 14095",
        insert=(col3_x + col3_w / 2, mid_y + 6),
        text_anchor="middle",
        font_size="3", font_weight="bold", font_family=fnt, fill="#333333",
    ))
    dwg.add(dwg.text(
        "DIN 14034-6",
        insert=(col3_x + col3_w / 2, mid_y + 11),
        text_anchor="middle",
        font_size="2.5", font_family=fnt, fill="#666666",
    ))


def _draw_scale_bar(
    dwg: svgwrite.Drawing, x: float, y: float,
    scale: float, unit_to_mm: float = 1.0,
) -> None:
    """Draw a graphical scale bar with real-world metre labels."""
    if scale <= 0:
        return

    # How many real-world mm does 1 SVG mm represent?
    real_mm_per_svg_mm = unit_to_mm / scale  # unit_to_mm / rendering_scale
    # Target ~50mm bar on paper → real-world mm
    target_real_mm = real_mm_per_svg_mm * 50
    target_real_m = target_real_mm / 1000

    # Pick a nice round number of metres (1, 2, 5, 10, 20, 50 …)
    if target_real_m < 1:
        nice_m = 1.0
    else:
        magnitude = 10 ** int(math.log10(target_real_m))
        nice_m = float(magnitude)
        for candidate in [1, 2, 5, 10]:
            if candidate * magnitude <= target_real_m * 1.3:
                nice_m = float(candidate * magnitude)

    # Back-convert to plan units and then to SVG mm
    nice_plan_units = nice_m * 1000 / unit_to_mm
    bar_svg_length = nice_plan_units * scale
    # Clamp bar to reasonable paper size (20–80mm)
    if bar_svg_length < 20:
        bar_svg_length = 20
    elif bar_svg_length > 80:
        bar_svg_length = 80

    segments = 4
    g = dwg.g(id="scale-bar")
    seg_len = bar_svg_length / segments
    for i in range(segments):
        g.add(dwg.rect(
            insert=(x + i * seg_len, y),
            size=(seg_len, 1.5),
            fill="black" if i % 2 == 0 else "white",
            stroke="black", stroke_width=0.2,
        ))

    fnt = "Arial, sans-serif"
    g.add(dwg.text(
        "0", insert=(x, y + 3.5),
        font_size=str(_ensure_min_font(2.0)), font_family=fnt, text_anchor="middle",
    ))
    label = f"{int(nice_m)} m" if nice_m >= 1 else f"{int(nice_m * 100)} cm"
    g.add(dwg.text(
        label, insert=(x + bar_svg_length, y + 3.5),
        font_size=str(_ensure_min_font(2.0)), font_family=fnt, text_anchor="middle",
    ))

    dwg.add(g)


class _SymbolPlacer:
    """Collision-aware symbol placement for DIN 14034-6 safety symbols.

    Tracks bounding boxes of placed symbols and room labels.  When a new
    symbol would overlap an existing one, shifts it in 4 directions
    (right, left, down, up) until a free slot is found or max attempts
    are exhausted.
    """

    def __init__(self) -> None:
        self._boxes: list[tuple[float, float, float, float]] = []  # (x, y, w, h)

    def register(self, x: float, y: float, w: float, h: float) -> None:
        """Register an existing element (e.g. room label) without shifting."""
        self._boxes.append((x - w / 2, y - h / 2, w, h))

    def place(self, x: float, y: float, size: float) -> tuple[float, float]:
        """Find a non-overlapping position for a symbol of given size.

        Tries the original position first, then shifts right, left, down, up
        by size*1.2.  After 4 failed attempts, accepts the original position.
        Returns the adjusted (x, y).
        """
        if not self._overlaps(x, y, size, size):
            self._boxes.append((x - size / 2, y - size / 2, size, size))
            return x, y

        shift = size * 1.2
        for dx, dy in [(shift, 0), (-shift, 0), (0, shift), (0, -shift)]:
            nx, ny = x + dx, y + dy
            if not self._overlaps(nx, ny, size, size):
                self._boxes.append((nx - size / 2, ny - size / 2, size, size))
                return nx, ny

        # All attempts failed — accept original and register it
        self._boxes.append((x - size / 2, y - size / 2, size, size))
        return x, y

    def _overlaps(self, cx: float, cy: float, w: float, h: float) -> bool:
        """Check if a centered box (cx, cy, w, h) overlaps any registered box."""
        ax1 = cx - w / 2
        ay1 = cy - h / 2
        ax2 = cx + w / 2
        ay2 = cy + h / 2
        for bx, by, bw, bh in self._boxes:
            bx2 = bx + bw
            by2 = by + bh
            if ax1 < bx2 and ax2 > bx and ay1 < by2 and ay2 > by:
                return True
        return False


def _room_edge_point(
    room: RoomPolygon, centroid: tuple[float, float], direction: str,
) -> tuple[float, float]:
    """Return a point between the room centroid and an edge.

    *direction* is one of "top", "bottom", "left", "right", "top-left", etc.
    Falls back to centroid if the room has fewer than 3 points.
    """
    cx, cy = centroid
    if len(room.points) < 3:
        return cx, cy

    xs = [p.x for p in room.points]
    ys = [p.y for p in room.points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    # Move ⅔ of the way from centroid toward the indicated edge
    blend = 0.55
    targets = {
        "top":       (cx, maxy),
        "bottom":    (cx, miny),
        "left":      (minx, cy),
        "right":     (maxx, cy),
        "top-left":  (minx, maxy),
        "top-right": (maxx, maxy),
        "bottom-left":  (minx, miny),
        "bottom-right": (maxx, miny),
    }
    tx_val, ty_val = targets.get(direction, (cx, cy))
    return cx + (tx_val - cx) * blend, cy + (ty_val - cy) * blend


def _draw_safety_symbols(
    dwg: svgwrite.Drawing,
    rooms: list[RoomPolygon],
    tx,
    ty,
    centroid_cache: dict[int, tuple[float, float]] | None = None,
    floor_plan: FloorPlanData | None = None,
    placer: _SymbolPlacer | None = None,
) -> None:
    """Place DIN 14034-6 safety symbols in rooms.

    Symbols are placed near room edges (not just at centroids) to avoid
    overlapping with room labels.  Uses _SymbolPlacer for collision detection
    when provided.
    """
    symbols_group = dwg.g(id="safety-symbols")

    if centroid_cache is None:
        centroid_cache = _compute_room_centroids(rooms)
    if placer is None:
        placer = _SymbolPlacer()

    sym_size = _ensure_min_size(2.5)

    for room in rooms:
        if room.id not in centroid_cache:
            continue
        centroid = centroid_cache[room.id]

        # Smoke detector: top-right of room (FKS standard — every room)
        sx, sy = _room_edge_point(room, centroid, "top-right")
        sx, sy = placer.place(tx(sx), ty(sy), sym_size)
        symbols_group.add(smoke_detector(dwg, sx, sy, size=sym_size))

        # Manual call point: bottom-left of escape rooms
        if room.room_type in (RoomType.STAIRWELL, RoomType.CORRIDOR, RoomType.LOBBY):
            mx, my = _room_edge_point(room, centroid, "bottom-left")
            mx, my = placer.place(tx(mx), ty(my), sym_size)
            symbols_group.add(manual_call_point(dwg, mx, my, size=sym_size))

        # Stair direction arrow: center of stairwells (DIN 14034-6)
        if room.room_type == RoomType.STAIRWELL:
            arrow_size = _ensure_min_size(4)
            arr_x, arr_y = placer.place(tx(centroid[0]), ty(centroid[1]) + 3, arrow_size)
            symbols_group.add(stair_direction_arrow(dwg, arr_x, arr_y, size=arrow_size))

        # Elevator symbol: center of elevator rooms (DIN 14034-6)
        if room.room_type == RoomType.ELEVATOR:
            elev_size = _ensure_min_size(4)
            ex, ey = placer.place(tx(centroid[0]), ty(centroid[1]), elev_size)
            symbols_group.add(elevator_symbol(dwg, ex, ey, size=elev_size))

    # Wall hydrant: near first corridor edge (if sprinkler detected)
    if floor_plan and floor_plan.has_sprinkler:
        for room in rooms:
            if room.room_type == RoomType.CORRIDOR and room.id in centroid_cache:
                wx, wy = _room_edge_point(room, centroid_cache[room.id], "left")
                hyd_size = _ensure_min_size(4)
                wx, wy = placer.place(tx(wx), ty(wy), hyd_size)
                symbols_group.add(wall_hydrant_symbol(dwg, wx, wy, size=hyd_size))
                break

    # RWA: near first stairwell top edge
    for room in rooms:
        if room.room_type == RoomType.STAIRWELL and room.id in centroid_cache:
            rx, ry = _room_edge_point(room, centroid_cache[room.id], "top")
            rwa_size = _ensure_min_size(4)
            rx, ry = placer.place(tx(rx), ty(ry), rwa_size)
            symbols_group.add(rwa_symbol(dwg, rx, ry, size=rwa_size))
            break

    dwg.add(symbols_group)


def _draw_escape_routes(
    dwg: svgwrite.Drawing,
    rooms: list[RoomPolygon],
    tx,
    ty,
    centroid_cache: dict[int, tuple[float, float]] | None = None,
) -> None:
    """Draw escape route lines using room adjacency graph for realistic paths.

    Builds a graph of adjacent rooms (rooms sharing walls) and finds shortest
    paths from each room to the nearest stairwell using BFS.  For corridor rooms,
    uses Voronoi medial-axis centerlines so routes follow corridor geometry
    instead of straight centroid-to-centroid lines (DIN 14095 compliance).
    """
    from collections import deque
    from shapely.geometry import Polygon as ShapelyPoly

    if centroid_cache is None:
        centroid_cache = _compute_room_centroids(rooms)

    escape_group = dwg.g(id="escape-routes")

    # Build room data: centroids and polygons (reuse cached centroids)
    room_data = []
    stairwell_indices = []
    corridor_indices = []
    for i, room in enumerate(rooms):
        if len(room.points) < 3 or room.id not in centroid_cache:
            room_data.append(None)
            continue
        poly = ShapelyPoly([(p.x, p.y) for p in room.points])
        cx, cy = centroid_cache[room.id]
        room_data.append({"poly": poly, "cx": cx, "cy": cy, "type": room.room_type})
        if room.room_type == RoomType.STAIRWELL:
            stairwell_indices.append(i)
        elif room.room_type == RoomType.CORRIDOR:
            corridor_indices.append(i)

    n = len(rooms)

    # If no stairwells, fall back to building exits (rooms touching the perimeter)
    exit_indices = list(stairwell_indices)
    if not exit_indices:
        # Use corridor endpoints or lobby as exit targets
        lobby_indices = [
            i for i in range(n) if room_data[i] is not None
            and room_data[i]["type"] == RoomType.LOBBY
        ]
        if lobby_indices:
            exit_indices = lobby_indices
        elif corridor_indices:
            exit_indices = [corridor_indices[0]]
        else:
            dwg.add(escape_group)
            return

    # Build adjacency graph using spatial indexing (STRtree) for performance.
    # Two rooms are adjacent if their buffered polygons share significant area.
    from shapely import STRtree
    adjacency: dict[int, list[int]] = {i: [] for i in range(n) if room_data[i] is not None}

    # Pre-buffer all polygons once (avoids repeated .buffer() calls)
    valid_indices = [i for i in range(n) if room_data[i] is not None]
    buffered_polys = []
    index_map = []  # maps STRtree position -> room index
    for i in valid_indices:
        buffered_polys.append(room_data[i]["poly"].buffer(1))
        index_map.append(i)

    if buffered_polys:
        tree = STRtree(buffered_polys)
        # For each buffered polygon, query the tree for candidates
        for pos_a, buf_a in enumerate(buffered_polys):
            room_i = index_map[pos_a]
            candidate_positions = tree.query(buf_a)
            for pos_b in candidate_positions:
                room_j = index_map[pos_b]
                if room_j <= room_i:
                    continue  # avoid duplicates and self-match
                buf_b = buffered_polys[pos_b]
                # Fast boolean check before expensive intersection geometry
                if not buf_a.intersects(buf_b):
                    continue
                shared = buf_a.intersection(buf_b)
                if shared.area > 0.5:
                    adjacency[room_i].append(room_j)
                    adjacency[room_j].append(room_i)

    # ── Corridor centerline graph (enhanced routing) ─────────────
    # Build a NetworkX graph with medial-axis edges for corridor rooms.
    # Falls back to centroid-to-centroid if import or graph build fails.
    corridor_graph = None
    try:
        from app.utils.corridor_routing import build_corridor_graph, route_escape_path
        corridor_graph = build_corridor_graph(rooms, room_data, adjacency)
    except Exception:
        logger.debug("Corridor routing unavailable, using centroid fallback")

    # BFS from each corridor/lobby to nearest exit through room adjacency
    exit_set = set(exit_indices)
    escape_sources = corridor_indices + [
        i for i in range(n) if room_data[i] is not None
        and room_data[i]["type"] == RoomType.LOBBY
    ]
    # Don't route from an exit to itself
    escape_sources = [s for s in escape_sources if s not in exit_set]

    def _draw_escape_arrow_at(group, end_x, end_y, prev_x, prev_y):
        """Draw an arrowhead pointing from (prev_x,prev_y) to (end_x,end_y) in SVG coords."""
        ddx = end_x - prev_x
        ddy = end_y - prev_y
        length = math.sqrt(ddx * ddx + ddy * ddy)
        if length <= 0:
            return
        udx, udy = ddx / length, ddy / length
        arrow_size = 2.5
        ax1 = end_x - udx * arrow_size - udy * arrow_size * 0.4
        ay1 = end_y - udy * arrow_size + udx * arrow_size * 0.4
        ax2 = end_x - udx * arrow_size + udy * arrow_size * 0.4
        ay2 = end_y - udy * arrow_size - udx * arrow_size * 0.4
        group.add(dwg.polygon(
            points=[(end_x, end_y), (ax1, ay1), (ax2, ay2)],
            fill="#006400",
        ))

    for src_idx in escape_sources:
        if room_data[src_idx] is None:
            continue

        # BFS to find nearest exit (room-level path)
        visited = {src_idx}
        queue = deque([(src_idx, [src_idx])])
        path = None

        while queue:
            current, current_path = queue.popleft()
            if current in exit_set:
                path = current_path
                break
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, current_path + [neighbor]))

        if path and len(path) >= 2:
            # Try enhanced corridor routing (polyline through centerlines)
            waypoints = []
            if corridor_graph is not None:
                try:
                    waypoints = route_escape_path(
                        corridor_graph, src_idx, [path[-1]],
                    )
                except Exception:
                    waypoints = []

            if len(waypoints) >= 2:
                # Draw polyline through corridor centerline waypoints
                svg_points = [(tx(wx), ty(wy)) for wx, wy in waypoints]
                escape_group.add(dwg.polyline(
                    points=svg_points,
                    fill="none",
                    stroke="#006400", stroke_width=0.8, stroke_dasharray="2,1",
                ))
                # Arrow at the end
                if len(svg_points) >= 2:
                    _draw_escape_arrow_at(
                        escape_group,
                        svg_points[-1][0], svg_points[-1][1],
                        svg_points[-2][0], svg_points[-2][1],
                    )
            else:
                # Fallback: centroid-to-centroid lines (original behavior)
                for k in range(len(path) - 1):
                    ri, rj = path[k], path[k + 1]
                    x1, y1 = room_data[ri]["cx"], room_data[ri]["cy"]
                    x2, y2 = room_data[rj]["cx"], room_data[rj]["cy"]
                    escape_group.add(dwg.line(
                        start=(tx(x1), ty(y1)), end=(tx(x2), ty(y2)),
                        stroke="#006400", stroke_width=0.8, stroke_dasharray="2,1",
                    ))
                _draw_escape_arrow_at(
                    escape_group,
                    tx(room_data[path[-1]]["cx"]), ty(room_data[path[-1]]["cy"]),
                    tx(room_data[path[-2]]["cx"]), ty(room_data[path[-2]]["cy"]),
                )
        elif not path and exit_indices:
            # Fallback: direct line to nearest exit
            cx_s, cy_s = room_data[src_idx]["cx"], room_data[src_idx]["cy"]
            nearest = min(exit_indices, key=lambda s: (
                (room_data[s]["cx"] - cx_s) ** 2 + (room_data[s]["cy"] - cy_s) ** 2
            ) if room_data[s] is not None else float("inf"))
            if room_data[nearest] is not None:
                nx_val, ny_val = room_data[nearest]["cx"], room_data[nearest]["cy"]
                escape_group.add(dwg.line(
                    start=(tx(cx_s), ty(cy_s)), end=(tx(nx_val), ty(ny_val)),
                    stroke="#006400", stroke_width=0.8, stroke_dasharray="2,1",
                ))
                _draw_escape_arrow_at(
                    escape_group,
                    tx(nx_val), ty(ny_val), tx(cx_s), ty(cy_s),
                )

    dwg.add(escape_group)


def generate_cover_sheet(
    rooms: list[RoomPolygon],
    output_path: Path,
    building_name: str = "Building",
    address: str = "",
    floors: list[str] | None = None,
    paper_format: str = "A3",
    language: str = "en",
    floor_plan: FloorPlanData | None = None,
) -> Path:
    """Generate a DIN 14095-compliant cover sheet (Deckblatt).

    The cover sheet contains:
    - Building identification (name, address, usage)
    - Complete legend with all symbols
    - Floor overview
    - Title block

    Args:
        rooms: All rooms across all floors (for complete legend).
        output_path: Where to save the SVG.
        building_name: Building name.
        address: Building address.
        floors: List of floor labels (e.g., ["UG", "EG", "1.OG"]).
        paper_format: "A3" or "A4".
        language: "en" or "de".
        floor_plan: Optional floor plan data for feature detection.

    Returns:
        Path to the generated cover sheet SVG.
    """
    lang: Locale = "de" if language == "de" else "en"

    if paper_format == "A3":
        paper_w, paper_h = A3_WIDTH, A3_HEIGHT
    else:
        paper_w, paper_h = A4_WIDTH, A4_HEIGHT

    if floors is None:
        floors = ["EG"]

    dwg = svgwrite.Drawing(
        str(output_path),
        size=(f"{paper_w}mm", f"{paper_h}mm"),
        viewBox=f"0 0 {paper_w} {paper_h}",
    )

    # Background + border
    dwg.add(dwg.rect(insert=(0, 0), size=(paper_w, paper_h), fill="white"))
    dwg.add(dwg.rect(
        insert=(MARGIN - 1, MARGIN - 1),
        size=(paper_w - 2 * MARGIN + 2, paper_h - 2 * MARGIN + 2),
        fill="none", stroke="black", stroke_width=0.5,
    ))

    # === HEADER ===
    dwg.add(dwg.text(
        t("cover.header", lang),
        insert=(paper_w / 2, MARGIN + 15),
        text_anchor="middle",
        font_size="10",
        font_weight="bold",
        font_family="Arial, sans-serif",
    ))

    # === BUILDING INFO ===
    info_y = MARGIN + 30
    dwg.add(dwg.rect(
        insert=(MARGIN + 5, info_y),
        size=(paper_w - 2 * MARGIN - 10, 40),
        fill="#F8F8F8", stroke="black", stroke_width=0.3,
    ))
    dwg.add(dwg.text(
        t("cover.object_definition", lang),
        insert=(MARGIN + 10, info_y + 8),
        font_size="5", font_weight="bold", font_family="Arial, sans-serif",
    ))
    dwg.add(dwg.text(
        f"{t('title.object', lang)}: {building_name}",
        insert=(MARGIN + 10, info_y + 18),
        font_size="4", font_family="Arial, sans-serif",
    ))
    if address:
        dwg.add(dwg.text(
            f"{t('title.address', lang)}: {address}",
            insert=(MARGIN + 10, info_y + 25),
            font_size="4", font_family="Arial, sans-serif",
        ))

    # Detect building usage from room types
    room_types_present = {r.room_type for r in rooms}
    if RoomType.RESIDENTIAL in room_types_present or RoomType.BEDROOM in room_types_present:
        usage = t("cover.usage_residential", lang)
    elif RoomType.GARAGE in room_types_present:
        usage = t("cover.usage_commercial", lang)
    else:
        usage = t("cover.usage_office", lang)
    dwg.add(dwg.text(
        f"{t('cover.usage', lang)}: {usage}",
        insert=(MARGIN + 10, info_y + 32),
        font_size="4", font_family="Arial, sans-serif",
    ))

    # Floor count
    dwg.add(dwg.text(
        f"{t('title.floors_label', lang)}: {', '.join(floors)} ({len(floors)} {t('cover.plans', lang)})",
        insert=(paper_w / 2, info_y + 18),
        font_size="4", font_family="Arial, sans-serif",
    ))

    # PV system indication (if detected from DXF)
    if floor_plan and hasattr(floor_plan, 'has_sprinkler') and floor_plan.has_sprinkler:
        dwg.add(dwg.text(
            t("cover.pv_present", lang),
            insert=(paper_w / 2, info_y + 32),
            font_size="3", font_family="Arial, sans-serif",
            fill="#FF6600",
        ))

    # === COMPLETE LEGEND ===
    legend_y = info_y + 50
    dwg.add(dwg.text(
        t("cover.room_types", lang),
        insert=(MARGIN + 10, legend_y),
        font_size="5", font_weight="bold", font_family="Arial, sans-serif",
    ))

    col_w = (paper_w - 2 * MARGIN - 20) / 3
    y = legend_y + 8
    col = 0
    for rt in RoomType:
        color = ROOM_COLORS.get(rt, "#F5F5F5")
        label = room_label(rt.value, lang)
        x = MARGIN + 10 + col * col_w
        dwg.add(dwg.rect(
            insert=(x, y), size=(5, 5),
            fill=color, fill_opacity=0.6,
            stroke="#FF0000" if rt in DANGEROUS_ROOM_TYPES else "black",
            stroke_width=0.5 if rt in DANGEROUS_ROOM_TYPES else 0.2,
        ))
        dwg.add(dwg.text(
            label, insert=(x + 7, y + 4),
            font_size="3", font_family="Arial, sans-serif",
            fill="#FF0000" if rt in DANGEROUS_ROOM_TYPES else "black",
        ))
        y += 8
        if y > legend_y + 8 + 8 * 6:  # Max 6 per column
            y = legend_y + 8
            col += 1

    # === SYMBOL LEGEND ===
    sym_y = legend_y + 65
    dwg.add(dwg.text(
        t("cover.symbols", lang),
        insert=(MARGIN + 10, sym_y),
        font_size="5", font_weight="bold", font_family="Arial, sans-serif",
    ))

    symbol_items = [
        ("S", "red", t("symbol.smoke_detector", lang)),
        ("\u25b2", "red", t("symbol.manual_call_point", lang)),
        ("BMZ", "red", t("symbol.bma", lang)),
        ("\u2192", "#006400", t("cover.escape_direction", lang)),
        ("\u25b6", "#FF0000", t("symbol.fire_access", lang)),
        ("\U0001f511", "#FF0000", t("symbol.key_depot", lang)),
        ("N", "black", t("symbol.north_arrow", lang)),
        ("\u2501\u2501", "black", t("symbol.scale_bar", lang)),
        ("G", "#FFD700", t("symbol.gas_shutoff", lang)),
        ("W", "#4169E1", t("symbol.water_shutoff", lang)),
        ("E", "#DC143C", t("symbol.electricity_shutoff", lang)),
        ("WH", "#4169E1", t("symbol.wall_hydrant", lang)),
        ("SP", "#0000FF", t("symbol.sprinkler", lang)),
        ("\u2191", "#228B22", t("symbol.stair_direction", lang)),
        ("A", "black", t("symbol.elevator", lang)),
        ("RWA", "black", t("symbol.rwa", lang)),
        ("S\u25a0", "#228B22", t("symbol.assembly_point", lang)),
        ("EI", "red", t("symbol.erstinfo", lang)),
    ]

    # Render symbol items in two columns
    y = sym_y + 8
    col_start_y = y
    half = len(symbol_items) // 2 + len(symbol_items) % 2
    for idx, (sym, color, label) in enumerate(symbol_items):
        col_offset = 0 if idx < half else (paper_w - 2 * MARGIN) / 2
        row_y = col_start_y + (idx % half) * 7
        dwg.add(dwg.text(
            sym, insert=(MARGIN + 15 + col_offset, row_y + 3),
            text_anchor="middle", font_size="4",
            font_family="Arial, sans-serif", fill=color, font_weight="bold",
        ))
        dwg.add(dwg.text(
            label, insert=(MARGIN + 22 + col_offset, row_y + 3),
            font_size="3", font_family="Arial, sans-serif",
        ))

    # === COLOR LEGEND ===
    color_y = sym_y + 75
    dwg.add(dwg.text(
        t("cover.colors", lang),
        insert=(MARGIN + 10, color_y),
        font_size="5", font_weight="bold", font_family="Arial, sans-serif",
    ))
    color_items = [
        (t("color.vertical_escape", lang), "#006400"),
        (t("color.horizontal_escape", lang), COLORS["corridor"]),
        (t("legend.danger_zone", lang), "#FF0000"),
        (t("color.walls", lang), COLORS["wall"]),
        (t("color.doors", lang), COLORS["door"]),
        (t("color.fire_walls", lang), COLORS["fire_wall"]),
    ]
    y = color_y + 8
    for label, color in color_items:
        dwg.add(dwg.rect(
            insert=(MARGIN + 10, y), size=(15, 4),
            fill=color, fill_opacity=0.7, stroke="black", stroke_width=0.2,
        ))
        dwg.add(dwg.text(
            label, insert=(MARGIN + 28, y + 3),
            font_size="3", font_family="Arial, sans-serif",
        ))
        y += 7

    # === TITLE BLOCK ===
    _draw_title_block(
        dwg, paper_w, paper_h, building_name, address,
        t("title.cover_sheet", lang), 0, 0, lang,  # no scale for cover sheet
    )

    dwg.save()
    logger.info("Cover sheet generated: %s", output_path)
    return output_path


def generate_situation_plan(
    floor_plan: FloorPlanData,
    rooms: list[RoomPolygon],
    output_path: Path,
    building_name: str = "Building",
    address: str = "",
    paper_format: str = "A3",
    language: str = "en",
) -> Path:
    """Generate a DIN 14095-compliant situation plan (Situationsplan).

    Shows the building outline with labeled sides, north arrow,
    fire department access points, and key depot location.

    Args:
        floor_plan: Parsed floor plan data.
        rooms: Classified room polygons.
        output_path: Where to save the SVG.
        building_name: Building name.
        address: Building address.
        paper_format: "A3" or "A4".
        language: "en" or "de".

    Returns:
        Path to the generated situation plan SVG.
    """
    lang: Locale = "de" if language == "de" else "en"

    if paper_format == "A3":
        paper_w, paper_h = A3_WIDTH, A3_HEIGHT
    else:
        paper_w, paper_h = A4_WIDTH, A4_HEIGHT

    dwg = svgwrite.Drawing(
        str(output_path),
        size=(f"{paper_w}mm", f"{paper_h}mm"),
        viewBox=f"0 0 {paper_w} {paper_h}",
    )

    # Background + border
    dwg.add(dwg.rect(insert=(0, 0), size=(paper_w, paper_h), fill="white"))
    dwg.add(dwg.rect(
        insert=(MARGIN - 1, MARGIN - 1),
        size=(paper_w - 2 * MARGIN + 2, paper_h - 2 * MARGIN + 2),
        fill="none", stroke="black", stroke_width=0.5,
    ))

    # Header
    dwg.add(dwg.text(
        t("situation.header", lang),
        insert=(paper_w / 2, MARGIN + 15),
        text_anchor="middle",
        font_size="10", font_weight="bold", font_family="Arial, sans-serif",
    ))

    # Drawing area for the building outline
    draw_x = MARGIN + 20
    draw_y = MARGIN + 30
    draw_w = paper_w - 2 * MARGIN - 40
    draw_h = paper_h - 2 * MARGIN - TITLE_BLOCK_HEIGHT - 50

    minx, miny, maxx, maxy = floor_plan.bounds
    plan_w = maxx - minx
    plan_h = maxy - miny

    if plan_w <= 0 or plan_h <= 0:
        dwg.add(dwg.text(
            t("situation.header", lang),
            insert=(paper_w / 2, paper_h / 2),
            text_anchor="middle", font_size="6", font_family="Arial, sans-serif",
        ))
        _draw_title_block(dwg, paper_w, paper_h, building_name, address,
                          t("situation.header", lang), 1.0, 1.0, lang)
        dwg.save()
        return output_path

    scale = min(draw_w / plan_w, draw_h / plan_h) * 0.6  # 60% fill for context space
    offset_x = draw_x + (draw_w - plan_w * scale) / 2
    offset_y = draw_y + (draw_h - plan_h * scale) / 2

    def tx(x: float) -> float:
        return offset_x + (x - minx) * scale

    def ty(y: float) -> float:
        return offset_y + (maxy - y) * scale

    # === SURROUNDINGS (simplified context) ===
    ctx_margin = 30
    dwg.add(dwg.rect(
        insert=(tx(minx) - ctx_margin, ty(maxy) - ctx_margin),
        size=(plan_w * scale + 2 * ctx_margin, plan_h * scale + 2 * ctx_margin),
        fill="#E8E8E8", stroke="none",
    ))

    # Simplified street placeholder
    street_y_top = ty(maxy) - ctx_margin - 5
    street_w = plan_w * scale + 2 * ctx_margin + 20
    dwg.add(dwg.rect(
        insert=(tx(minx) - ctx_margin - 10, street_y_top),
        size=(street_w, 8),
        fill="#D3D3D3", stroke="#AAAAAA", stroke_width=0.3,
    ))
    dwg.add(dwg.text(
        t("situation.street", lang),
        insert=(tx(minx + plan_w / 2), street_y_top + 5),
        text_anchor="middle", font_size="3",
        font_family="Arial, sans-serif", fill="#666666", font_style="italic",
    ))

    # === BUILDING OUTLINE ===
    for wall in floor_plan.walls:
        dwg.add(dwg.line(
            start=(tx(wall.start.x), ty(wall.start.y)),
            end=(tx(wall.end.x), ty(wall.end.y)),
            stroke="black", stroke_width=1.0, stroke_linecap="round",
        ))

    # Fill rooms with light colors
    for room in rooms:
        if len(room.points) < 3:
            continue
        points = [(tx(p.x), ty(p.y)) for p in room.points]
        fill = ROOM_COLORS.get(room.room_type, ROOM_COLORS[RoomType.UNKNOWN])
        dwg.add(dwg.polygon(
            points=points, fill=fill, fill_opacity=0.3, stroke="none",
        ))

    # === BUILDING SIDE LABELS ===
    center_x = tx(minx + plan_w / 2)
    center_y = ty(miny + plan_h / 2)
    sides = [
        (t("situation.side_a", lang), center_x, ty(maxy) - ctx_margin + 3, "middle"),
        (t("situation.side_b", lang), tx(maxx) + ctx_margin + 3, center_y, "start"),
        (t("situation.side_c", lang), center_x, ty(miny) + ctx_margin + 8, "middle"),
        (t("situation.side_d", lang), tx(minx) - ctx_margin - 3, center_y, "end"),
    ]
    for label, sx, sy, anchor in sides:
        dwg.add(dwg.text(
            label, insert=(sx, sy),
            text_anchor=anchor, font_size="3.5",
            font_weight="bold", font_family="Arial, sans-serif", fill="#333333",
        ))

    # === FKS ACCESS SYMBOLS ===
    fa = fire_access_arrow(dwg, center_x - 3, ty(miny) + ctx_margin - 3, angle=90, size=8)
    dwg.add(fa)
    dwg.add(dwg.text(
        t("situation.fire_access", lang),
        insert=(center_x + 8, ty(miny) + ctx_margin),
        font_size="3", font_family="Arial, sans-serif", fill="red", font_weight="bold",
    ))

    # Key depot
    kd = key_depot(dwg, tx(minx) - 5, ty(miny + plan_h / 2), size=5)
    dwg.add(kd)
    dwg.add(dwg.text(
        t("situation.key_depot", lang),
        insert=(tx(minx) - 12, ty(miny + plan_h / 2) + 8),
        text_anchor="middle", font_size="2.5",
        font_family="Arial, sans-serif", fill="red",
    ))

    # Assembly point symbol (DIN 14095)
    ap = assembly_point_symbol(dwg, tx(maxx) + ctx_margin - 10, ty(miny) + ctx_margin - 10, size=_ensure_min_size(6))
    dwg.add(ap)
    dwg.add(dwg.text(
        t("symbol.assembly_point", lang),
        insert=(tx(maxx) + ctx_margin - 10, ty(miny) + ctx_margin + 2),
        text_anchor="middle", font_size="2.5",
        font_family="Arial, sans-serif", fill="#228B22", font_weight="bold",
    ))

    # Erstinformationsstelle (DIN 14034-6 2024)
    ei = erstinfo_symbol(dwg, tx(minx) - ctx_margin + 5, ty(maxy) - ctx_margin + 15, size=_ensure_min_size(5))
    dwg.add(ei)
    dwg.add(dwg.text(
        t("symbol.erstinfo", lang),
        insert=(tx(minx) - ctx_margin + 5, ty(maxy) - ctx_margin + 23),
        text_anchor="middle", font_size="2",
        font_family="Arial, sans-serif", fill="red",
    ))

    # North arrow (top-right)
    na = north_arrow(dwg, paper_w - MARGIN - 15, MARGIN + 30, size=10)
    dwg.add(na)

    # Building name label
    dwg.add(dwg.text(
        building_name,
        insert=(center_x, center_y),
        text_anchor="middle", dominant_baseline="middle",
        font_size="5", font_weight="bold", font_family="Arial, sans-serif",
    ))

    # === TITLE BLOCK ===
    sit_unit_to_mm = _detect_unit_to_mm(plan_w, plan_h, floor_plan.unit)
    sit_din_scale = _compute_din_scale(scale, sit_unit_to_mm)
    _draw_title_block(dwg, paper_w, paper_h, building_name, address,
                      t("situation.header", lang), sit_din_scale, plan_w, lang)

    dwg.save()
    logger.info("Situation plan generated: %s", output_path)
    return output_path
