"""Generate synthetic test DXF files covering different scenarios.

Creates DXF files with known geometry for testing the parser and plan generator
under various conditions: different units, layer naming conventions, and
architectural elements.

Usage:
    python testdata/generate_test_dxfs.py
"""

import math
import ezdxf


def _add_room_rect(msp, x, y, w, h, layer):
    """Add a rectangular room to modelspace."""
    msp.add_line((x, y), (x + w, y), dxfattribs={"layer": layer})
    msp.add_line((x + w, y), (x + w, y + h), dxfattribs={"layer": layer})
    msp.add_line((x + w, y + h), (x, y + h), dxfattribs={"layer": layer})
    msp.add_line((x, y + h), (x, y), dxfattribs={"layer": layer})


def _add_door_arc(msp, x, y, radius, start_angle=0, end_angle=90, layer="0"):
    """Add a door swing arc at position (x, y)."""
    msp.add_arc(
        center=(x, y), radius=radius,
        start_angle=start_angle, end_angle=end_angle,
        dxfattribs={"layer": layer},
    )


def create_simple_office_mm():
    """Simple office building in millimeters with German layer names."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()

    # Outer walls (20m x 15m = 20000mm x 15000mm)
    wall_layer = "Wand_EG"
    _add_room_rect(msp, 0, 0, 20000, 15000, wall_layer)

    # Internal walls
    msp.add_line((10000, 0), (10000, 15000), dxfattribs={"layer": wall_layer})
    msp.add_line((0, 7500), (10000, 7500), dxfattribs={"layer": wall_layer})
    msp.add_line((10000, 5000), (20000, 5000), dxfattribs={"layer": wall_layer})

    # Doors (900mm wide)
    door_layer = "Tür_EG"
    _add_door_arc(msp, 5000, 7500, 900, 0, 90, layer=door_layer)
    _add_door_arc(msp, 10000, 3000, 900, 90, 180, layer=door_layer)
    _add_door_arc(msp, 15000, 5000, 900, 0, 90, layer=door_layer)

    # Stairwell
    stair_layer = "Treppe_EG"
    _add_room_rect(msp, 17000, 12000, 3000, 3000, stair_layer)
    # Stair steps (lines)
    for i in range(6):
        y = 12000 + i * 500
        msp.add_line((17000, y), (20000, y), dxfattribs={"layer": stair_layer})

    # Fire door
    fd_layer = "Brandschutz_T30"
    _add_door_arc(msp, 17000, 12000, 900, 180, 270, layer=fd_layer)

    doc.saveas("testdata/office_simple_mm.dxf")
    print("Created: office_simple_mm.dxf (20m x 15m, mm units, German layers)")


def create_house_meters():
    """Residential house in meters with English layer names."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6  # meters
    msp = doc.modelspace()

    wall_layer = "A-WALL"
    # Outer walls (12m x 10m)
    _add_room_rect(msp, 0, 0, 12, 10, wall_layer)

    # Internal
    msp.add_line((6, 0), (6, 10), dxfattribs={"layer": wall_layer})
    msp.add_line((0, 5), (6, 5), dxfattribs={"layer": wall_layer})
    msp.add_line((6, 4), (12, 4), dxfattribs={"layer": wall_layer})
    msp.add_line((9, 4), (9, 10), dxfattribs={"layer": wall_layer})

    # Doors
    door_layer = "A-DOOR"
    _add_door_arc(msp, 3, 5, 0.9, 0, 90, layer=door_layer)
    _add_door_arc(msp, 6, 2, 0.8, 90, 180, layer=door_layer)
    _add_door_arc(msp, 9, 7, 0.9, 0, 90, layer=door_layer)

    # Windows
    win_layer = "A-WINDOW"
    msp.add_line((2, 0), (4, 0), dxfattribs={"layer": win_layer})
    msp.add_line((8, 0), (10, 0), dxfattribs={"layer": win_layer})
    msp.add_line((0, 2), (0, 4), dxfattribs={"layer": win_layer})

    # Stairwell
    stair_layer = "A-STAIR"
    _add_room_rect(msp, 9, 4, 3, 3, stair_layer)

    doc.saveas("testdata/house_meters.dxf")
    print("Created: house_meters.dxf (12m x 10m, meter units, English layers)")


def create_warehouse_cm():
    """Large warehouse in centimeters with mixed layer names."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 5  # cm
    msp = doc.modelspace()

    wall_layer = "MAUER_AUSSEN"
    # 50m x 30m = 5000cm x 3000cm
    _add_room_rect(msp, 0, 0, 5000, 3000, wall_layer)

    # Fire walls dividing the warehouse
    fw_layer = "Brandwand_EG"
    msp.add_line((2500, 0), (2500, 3000), dxfattribs={"layer": fw_layer})

    # Sprinkler system markers
    spk_layer = "SPRINKLER-ZONE"
    for x in range(500, 5000, 500):
        for y in range(500, 3000, 500):
            msp.add_circle((x, y), 10, dxfattribs={"layer": spk_layer})

    # Large rolling doors
    door_layer = "A-OPENING"
    _add_door_arc(msp, 1250, 0, 300, 0, 90, layer=door_layer)
    _add_door_arc(msp, 3750, 0, 300, 0, 90, layer=door_layer)

    doc.saveas("testdata/warehouse_cm.dxf")
    print("Created: warehouse_cm.dxf (50m x 30m, cm units, mixed layers, fire walls, sprinklers)")


def create_anonymized():
    """Anonymized DXF (simulating DWGShare.com obfuscated layer names)."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 0  # unitless
    msp = doc.modelspace()

    # Use numeric/anonymized layer names
    wall_layer = "DWGShare.com_3"
    door_layer = "DWGShare.com_7"
    stair_layer = "layer5"

    # Small apartment (8m x 6m, coordinates in ~inches = 315 x 236)
    _add_room_rect(msp, 0, 0, 315, 236, wall_layer)
    msp.add_line((157, 0), (157, 236), dxfattribs={"layer": wall_layer})
    msp.add_line((0, 118), (157, 118), dxfattribs={"layer": wall_layer})

    # Door arcs
    _add_door_arc(msp, 80, 118, 36, 0, 90, layer=door_layer)
    _add_door_arc(msp, 157, 60, 36, 90, 180, layer=door_layer)

    doc.saveas("testdata/anonymized_layers.dxf")
    print("Created: anonymized_layers.dxf (DWGShare-style anonymous layers, no units)")


def create_multilingual():
    """DXF with Vietnamese/French/Spanish layer names."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()

    # Vietnamese walls (15m x 10m)
    wall_layer = "tuong_xay_01"
    _add_room_rect(msp, 0, 0, 15000, 10000, wall_layer)
    msp.add_line((7500, 0), (7500, 10000), dxfattribs={"layer": wall_layer})

    # French doors
    door_layer = "PORTE-01"
    _add_door_arc(msp, 3000, 0, 900, 0, 90, layer=door_layer)

    # Spanish stairs
    stair_layer = "escalera_01"
    _add_room_rect(msp, 12000, 7000, 3000, 3000, stair_layer)

    doc.saveas("testdata/multilingual_layers.dxf")
    print("Created: multilingual_layers.dxf (Vietnamese/French/Spanish layers)")


if __name__ == "__main__":
    create_simple_office_mm()
    create_house_meters()
    create_warehouse_cm()
    create_anonymized()
    create_multilingual()
    print("\nAll test DXFs generated successfully!")
