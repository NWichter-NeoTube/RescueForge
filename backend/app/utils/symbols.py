"""FKS standard symbols for fire department orientation plans.

Symbols follow SES-Richtlinie "Brandmeldeanlagen" and the FKS guideline.
Each symbol is returned as SVG snippet (group element) that can be inserted
into the plan at the specified position.
"""

import svgwrite


def north_arrow(dwg: svgwrite.Drawing, x: float, y: float, size: float = 15) -> svgwrite.container.Group:
    """Create a north arrow symbol."""
    g = dwg.g(id="north-arrow")
    # Arrow body
    g.add(dwg.polygon(
        points=[(x, y - size), (x - size * 0.3, y), (x + size * 0.3, y)],
        fill="black",
    ))
    # "N" label
    g.add(dwg.text(
        "N",
        insert=(x, y - size - 2),
        text_anchor="middle",
        font_size=str(size * 0.4),
        font_weight="bold",
        font_family="Arial, sans-serif",
    ))
    return g


def fire_access_arrow(
    dwg: svgwrite.Drawing, x: float, y: float, angle: float = 0, size: float = 10
) -> svgwrite.container.Group:
    """Create a red fire department access arrow."""
    g = dwg.g(id="fire-access")
    g.add(dwg.polygon(
        points=[
            (x, y - size * 0.5),
            (x + size, y),
            (x, y + size * 0.5),
        ],
        fill="#FF0000",
        stroke="#CC0000",
        stroke_width=0.3,
        transform=f"rotate({angle},{x},{y})",
    ))
    return g


def sprinkler_access_arrow(
    dwg: svgwrite.Drawing, x: float, y: float, angle: float = 0, size: float = 10
) -> svgwrite.container.Group:
    """Create a blue sprinkler access arrow."""
    g = dwg.g(id="sprinkler-access")
    g.add(dwg.polygon(
        points=[
            (x, y - size * 0.5),
            (x + size, y),
            (x, y + size * 0.5),
        ],
        fill="#0000FF",
        stroke="#0000CC",
        stroke_width=0.3,
        transform=f"rotate({angle},{x},{y})",
    ))
    return g


def smoke_detector(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 3
) -> svgwrite.container.Group:
    """Rauchmelder: "S" in a square (SES standard)."""
    g = dwg.g(class_="detector smoke-detector")
    g.add(dwg.rect(
        insert=(x - size / 2, y - size / 2),
        size=(size, size),
        fill="white",
        stroke="red",
        stroke_width=0.3,
    ))
    g.add(dwg.text(
        "S",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.7),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="red",
    ))
    return g


def manual_call_point(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 3
) -> svgwrite.container.Group:
    """Handfeuermelder: Red triangle (SES standard)."""
    g = dwg.g(class_="detector manual-call-point")
    g.add(dwg.polygon(
        points=[
            (x, y - size * 0.6),
            (x + size * 0.5, y + size * 0.4),
            (x - size * 0.5, y + size * 0.4),
        ],
        fill="red",
        stroke="darkred",
        stroke_width=0.2,
    ))
    return g


def key_depot(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 4
) -> svgwrite.container.Group:
    """Schlüsseldepot: Red box with key symbol."""
    g = dwg.g(class_="key-depot")
    g.add(dwg.rect(
        insert=(x - size / 2, y - size / 2),
        size=(size, size),
        fill="white",
        stroke="red",
        stroke_width=0.4,
    ))
    # Simple key icon (circle + line)
    g.add(dwg.circle(
        center=(x - size * 0.15, y - size * 0.1),
        r=size * 0.15,
        fill="none",
        stroke="red",
        stroke_width=0.3,
    ))
    g.add(dwg.line(
        start=(x, y - size * 0.1),
        end=(x + size * 0.3, y - size * 0.1),
        stroke="red",
        stroke_width=0.3,
    ))
    return g


def floor_section_indicator(
    dwg: svgwrite.Drawing,
    x: float,
    y: float,
    floors: list[str],
    current_floor: str,
    width: float = 15,
    floor_height: float = 5,
) -> svgwrite.container.Group:
    """Geschosslage-Querschnitt (floor section indicator).

    Shows a simple vertical stack of floors with the current floor highlighted.
    """
    g = dwg.g(id="floor-section")
    total_height = len(floors) * floor_height

    for i, floor in enumerate(reversed(floors)):
        fy = y + i * floor_height
        is_current = floor == current_floor

        g.add(dwg.rect(
            insert=(x, fy),
            size=(width, floor_height),
            fill="#FF6B6B" if is_current else "white",
            fill_opacity=0.5 if is_current else 0.1,
            stroke="black",
            stroke_width=0.3,
        ))
        g.add(dwg.text(
            floor,
            insert=(x + width / 2, fy + floor_height * 0.65),
            text_anchor="middle",
            font_size="2.5",
            font_weight="bold" if is_current else "normal",
            font_family="Arial, sans-serif",
        ))

    return g


def bma_bs(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Brandmeldezentrale (BMA-BS): Red outlined box with "BMZ" text.

    FKS standard symbol for the fire alarm control panel location.
    """
    g = dwg.g(class_="bma-bs")
    g.add(dwg.rect(
        insert=(x - size / 2, y - size / 2),
        size=(size, size),
        fill="white",
        stroke="red",
        stroke_width=0.5,
    ))
    g.add(dwg.text(
        "BMZ",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.4),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="red",
    ))
    return g


def gas_shutoff(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Gasabsperrung: Yellow circle with "G" (DIN 14034-6)."""
    g = dwg.g(class_="gas-shutoff")
    g.add(dwg.circle(
        center=(x, y),
        r=size / 2,
        fill="#FFD700",
        stroke="#B8960C",
        stroke_width=0.4,
    ))
    g.add(dwg.text(
        "G",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.55),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="black",
    ))
    return g


def water_shutoff(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Wasserabsperrung: Blue circle with "W" (DIN 14034-6)."""
    g = dwg.g(class_="water-shutoff")
    g.add(dwg.circle(
        center=(x, y),
        r=size / 2,
        fill="#4169E1",
        stroke="#2A4A9E",
        stroke_width=0.4,
    ))
    g.add(dwg.text(
        "W",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.55),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="white",
    ))
    return g


def electricity_shutoff(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Stromabsperrung: Red circle with "E" lightning bolt (DIN 14034-6)."""
    g = dwg.g(class_="electricity-shutoff")
    g.add(dwg.circle(
        center=(x, y),
        r=size / 2,
        fill="#DC143C",
        stroke="#A00E2B",
        stroke_width=0.4,
    ))
    g.add(dwg.text(
        "E",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.55),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="white",
    ))
    # Lightning bolt accent lines
    bolt_offset = size * 0.15
    g.add(dwg.line(
        start=(x + bolt_offset, y - size * 0.1),
        end=(x + bolt_offset + size * 0.08, y + size * 0.15),
        stroke="white",
        stroke_width=0.3,
    ))
    return g


def stair_direction_arrow(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Treppenlaufrichtung: Green upward arrow indicating stair direction."""
    g = dwg.g(class_="stair-direction")
    # Arrow shaft
    shaft_width = size * 0.25
    g.add(dwg.rect(
        insert=(x - shaft_width / 2, y - size * 0.1),
        size=(shaft_width, size * 0.6),
        fill="#228B22",
    ))
    # Arrow head
    g.add(dwg.polygon(
        points=[
            (x, y - size * 0.5),
            (x - size * 0.35, y - size * 0.1),
            (x + size * 0.35, y - size * 0.1),
        ],
        fill="#228B22",
    ))
    return g


def elevator_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Aufzug: Box with "A" and bidirectional arrow (DIN 14034-6)."""
    g = dwg.g(class_="elevator")
    g.add(dwg.rect(
        insert=(x - size / 2, y - size / 2),
        size=(size, size),
        fill="white",
        stroke="black",
        stroke_width=0.4,
    ))
    # "A" label
    g.add(dwg.text(
        "A",
        insert=(x - size * 0.15, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.45),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="black",
    ))
    # Bidirectional vertical arrow
    arrow_x = x + size * 0.25
    arrow_top = y - size * 0.3
    arrow_bottom = y + size * 0.3
    g.add(dwg.line(
        start=(arrow_x, arrow_top),
        end=(arrow_x, arrow_bottom),
        stroke="black",
        stroke_width=0.3,
    ))
    # Top arrowhead
    g.add(dwg.polygon(
        points=[
            (arrow_x, arrow_top - size * 0.05),
            (arrow_x - size * 0.06, arrow_top + size * 0.08),
            (arrow_x + size * 0.06, arrow_top + size * 0.08),
        ],
        fill="black",
    ))
    # Bottom arrowhead
    g.add(dwg.polygon(
        points=[
            (arrow_x, arrow_bottom + size * 0.05),
            (arrow_x - size * 0.06, arrow_bottom - size * 0.08),
            (arrow_x + size * 0.06, arrow_bottom - size * 0.08),
        ],
        fill="black",
    ))
    return g


def wall_hydrant_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Wandhydrant: Blue box with "WH" text (DIN 14034-6)."""
    g = dwg.g(class_="wall-hydrant")
    g.add(dwg.rect(
        insert=(x - size * 0.6, y - size / 2),
        size=(size * 1.2, size),
        fill="#4169E1",
        stroke="#2A4A9E",
        stroke_width=0.4,
        rx=0.5,
        ry=0.5,
    ))
    g.add(dwg.text(
        "WH",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.45),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="white",
    ))
    return g


def rwa_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Rauch- und Waermeabzug (RWA): Box with "RWA" text (DIN 14034-6)."""
    g = dwg.g(class_="rwa")
    g.add(dwg.rect(
        insert=(x - size * 0.7, y - size / 2),
        size=(size * 1.4, size),
        fill="white",
        stroke="black",
        stroke_width=0.4,
    ))
    g.add(dwg.text(
        "RWA",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.4),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="black",
    ))
    return g


def assembly_point_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 6
) -> svgwrite.container.Group:
    """Sammelplatz: Green square with "S" (DIN 14034-6)."""
    g = dwg.g(class_="assembly-point")
    g.add(dwg.rect(
        insert=(x - size / 2, y - size / 2),
        size=(size, size),
        fill="#228B22",
        stroke="#1B6B1B",
        stroke_width=0.4,
    ))
    g.add(dwg.text(
        "S",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.55),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="white",
    ))
    return g


def erstinfo_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 5
) -> svgwrite.container.Group:
    """Erstinformationsstelle: Red-framed box with "EI" (DIN 14034-6 2024)."""
    g = dwg.g(class_="erstinfo")
    g.add(dwg.rect(
        insert=(x - size * 0.6, y - size / 2),
        size=(size * 1.2, size),
        fill="white",
        stroke="red",
        stroke_width=0.6,
    ))
    g.add(dwg.text(
        "EI",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.5),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="red",
    ))
    return g


def fire_door_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 4
) -> svgwrite.container.Group:
    """Brandschutztuer: Red rectangle with "T" text (DIN 14034-6)."""
    g = dwg.g(class_="fire-door")
    g.add(dwg.rect(
        insert=(x - size * 0.6, y - size / 2),
        size=(size * 1.2, size),
        fill="#DC143C",
        stroke="#A00E2B",
        stroke_width=0.4,
        rx=0.3,
        ry=0.3,
    ))
    g.add(dwg.text(
        "T",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.6),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="white",
    ))
    return g


def emergency_exit_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 4
) -> svgwrite.container.Group:
    """Emergency exit sign: green rectangle with running figure (DIN 14034-6 / ISO 7010 E001)."""
    g = dwg.g(class_="emergency-exit")
    g.add(dwg.rect(
        insert=(x - size * 0.6, y - size / 2),
        size=(size * 1.2, size),
        fill="#228B22",
        stroke="#006400",
        stroke_width=0.3,
        rx=0.3,
        ry=0.3,
    ))
    # Simplified running figure arrow
    g.add(dwg.text(
        "\u2192",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.65),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="white",
    ))
    return g


def fire_extinguisher_symbol(
    dwg: svgwrite.Drawing, x: float, y: float, size: float = 3
) -> svgwrite.container.Group:
    """Fire extinguisher symbol (DIN 14034-6 / ISO 7010 F001)."""
    g = dwg.g(class_="fire-extinguisher")
    g.add(dwg.rect(
        insert=(x - size * 0.4, y - size / 2),
        size=(size * 0.8, size),
        fill="#DC143C",
        stroke="#A00E2B",
        stroke_width=0.3,
        rx=0.3,
        ry=0.3,
    ))
    g.add(dwg.text(
        "F",
        insert=(x, y),
        text_anchor="middle",
        dominant_baseline="central",
        font_size=str(size * 0.55),
        font_weight="bold",
        font_family="Arial, sans-serif",
        fill="white",
    ))
    return g


# Map of all available symbols for use in plan generation
SYMBOL_REGISTRY = {
    "north_arrow": north_arrow,
    "fire_access": fire_access_arrow,
    "sprinkler_access": sprinkler_access_arrow,
    "smoke_detector": smoke_detector,
    "manual_call_point": manual_call_point,
    "key_depot": key_depot,
    "bma_bs": bma_bs,
    "floor_section": floor_section_indicator,
    "gas_shutoff": gas_shutoff,
    "water_shutoff": water_shutoff,
    "electricity_shutoff": electricity_shutoff,
    "stair_direction": stair_direction_arrow,
    "elevator": elevator_symbol,
    "wall_hydrant": wall_hydrant_symbol,
    "rwa": rwa_symbol,
    "assembly_point": assembly_point_symbol,
    "erstinfo": erstinfo_symbol,
    "fire_door": fire_door_symbol,
    "emergency_exit": emergency_exit_symbol,
    "fire_extinguisher": fire_extinguisher_symbol,
}
