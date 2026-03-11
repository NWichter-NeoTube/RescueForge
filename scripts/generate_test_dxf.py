"""Generate synthetic DXF test files for different building types.

Creates realistic floor plans with proper layer names so the parser
can classify walls, doors, and stairs correctly.
"""

import ezdxf
from pathlib import Path
import math

TESTDATA_DIR = Path(__file__).parent.parent / "testdata"


def add_wall_rect(msp, x, y, w, h, layer="WALL"):
    """Add a rectangular room outline as wall segments."""
    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    msp.add_lwpolyline(points, dxfattribs={"layer": layer})


def add_door(msp, x, y, width=900, angle=90, layer="DOOR"):
    """Add a door arc at position."""
    msp.add_arc(
        center=(x, y),
        radius=width,
        start_angle=0,
        end_angle=angle,
        dxfattribs={"layer": layer},
    )


def add_door_line(msp, x1, y1, x2, y2, layer="DOOR"):
    """Add a door as a line segment."""
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})


def add_stair(msp, x, y, w, h, num_steps=10, layer="STAIR"):
    """Add a staircase with step lines."""
    # Outline
    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    msp.add_lwpolyline(points, dxfattribs={"layer": layer})
    # Steps
    step_h = h / num_steps
    for i in range(1, num_steps):
        sy = y + i * step_h
        msp.add_line((x, sy), (x + w, sy), dxfattribs={"layer": layer})


def generate_office_building():
    """Generate an office building floor plan with corridors, offices, meeting rooms."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("WALL", color=7)
    doc.layers.add("DOOR", color=3)
    doc.layers.add("STAIR", color=1)

    # Building outline: 30m x 20m
    W, H = 30000, 20000
    add_wall_rect(msp, 0, 0, W, H)

    # Central corridor (2m wide, running horizontally)
    corr_y = 9000
    corr_h = 2000
    msp.add_line((0, corr_y), (W, corr_y), dxfattribs={"layer": "WALL"})
    msp.add_line((0, corr_y + corr_h), (W, corr_y + corr_h), dxfattribs={"layer": "WALL"})

    # North side: 6 offices (each 5m x 9m)
    for i in range(6):
        ox = i * 5000
        if i > 0:
            msp.add_line((ox, corr_y + corr_h), (ox, H), dxfattribs={"layer": "WALL"})
        # Door to corridor
        add_door_line(msp, ox + 1500, corr_y + corr_h, ox + 2500, corr_y + corr_h, "DOOR")
        add_door(msp, ox + 1500, corr_y + corr_h, 1000, 90, "DOOR")

    # South side: offices + meeting room + WC
    # WC block (5m x 4m) at left
    msp.add_line((5000, 0), (5000, corr_y), dxfattribs={"layer": "WALL"})
    msp.add_line((0, 4000), (5000, 4000), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 2000, corr_y, 3000, corr_y, "DOOR")

    # Meeting room (10m x 9m)
    msp.add_line((15000, 0), (15000, corr_y), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 8000, corr_y, 9000, corr_y, "DOOR")

    # 3 offices on the right (each 5m x 9m)
    for i in range(3):
        ox = 15000 + i * 5000
        if i > 0:
            msp.add_line((ox, 0), (ox, corr_y), dxfattribs={"layer": "WALL"})
        add_door_line(msp, ox + 1500, corr_y, ox + 2500, corr_y, "DOOR")
        add_door(msp, ox + 1500, corr_y, 1000, -90, "DOOR")

    # Stairwell at the right end
    add_stair(msp, W - 4000, corr_y + corr_h, 3000, 4000, 12, "STAIR")

    # Elevator next to stairwell
    add_wall_rect(msp, W - 4000, corr_y + corr_h + 4500, 2000, 2000)

    filepath = TESTDATA_DIR / "office_building.dxf"
    doc.saveas(str(filepath))
    print(f"Created: {filepath}")


def generate_residential_apartment():
    """Generate a residential apartment floor plan."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()

    doc.layers.add("WALL", color=7)
    doc.layers.add("DOOR", color=3)
    doc.layers.add("STAIR", color=1)

    # Apartment: 12m x 10m
    W, H = 12000, 10000
    add_wall_rect(msp, 0, 0, W, H)

    # Entry/corridor (1.2m wide, L-shaped)
    msp.add_line((0, 4000), (5000, 4000), dxfattribs={"layer": "WALL"})
    msp.add_line((3500, 0), (3500, 4000), dxfattribs={"layer": "WALL"})

    # Living room (8.5m x 6m) - top right
    msp.add_line((3500, 4000), (3500, H), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 3500, 5000, 3500, 6000, "DOOR")
    add_door(msp, 3500, 5000, 1000, 90, "DOOR")

    # Kitchen (3.5m x 3.5m) - bottom left
    msp.add_line((0, 3500), (3500, 3500), dxfattribs={"layer": "WALL"})
    # Kitchen is below corridor wall
    add_door_line(msp, 1500, 4000, 2500, 4000, "DOOR")

    # Bedroom 1 (4m x 4m) - top left area
    msp.add_line((0, 6000), (3500, 6000), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 1000, 4000, 2000, 4000, "DOOR")

    # Bathroom (3m x 2.5m)
    msp.add_line((7000, 0), (7000, 4000), dxfattribs={"layer": "WALL"})
    msp.add_line((7000, 2500), (W, 2500), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 5000, 4000, 6000, 4000, "DOOR")

    # Bedroom 2 (5m x 4m) - bottom right
    msp.add_line((7000, 4000), (7000, H), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 7000, 5500, 7000, 6500, "DOOR")
    add_door(msp, 7000, 5500, 1000, 90, "DOOR")

    # Storage closet
    msp.add_line((W - 2000, 0), (W - 2000, 2500), dxfattribs={"layer": "WALL"})

    # Balcony indicator
    msp.add_line((3500, H), (W, H), dxfattribs={"layer": "WALL"})
    msp.add_line((3500, H + 1500), (W, H + 1500), dxfattribs={"layer": "WALL"})
    msp.add_line((3500, H), (3500, H + 1500), dxfattribs={"layer": "WALL"})
    msp.add_line((W, H), (W, H + 1500), dxfattribs={"layer": "WALL"})

    # Entry door
    add_door_line(msp, 1000, 0, 2000, 0, "DOOR")
    add_door(msp, 1000, 0, 1000, 90, "DOOR")

    filepath = TESTDATA_DIR / "residential_apartment.dxf"
    doc.saveas(str(filepath))
    print(f"Created: {filepath}")


def generate_industrial_warehouse():
    """Generate an industrial warehouse/production hall floor plan."""
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()

    doc.layers.add("WALL", color=7)
    doc.layers.add("DOOR", color=3)
    doc.layers.add("STAIR", color=1)

    # Large warehouse: 50m x 30m
    W, H = 50000, 30000
    add_wall_rect(msp, 0, 0, W, H)

    # Main production hall: open 40m x 25m space
    # Office wing on the left side (10m x 30m)
    msp.add_line((10000, 0), (10000, H), dxfattribs={"layer": "WALL"})

    # Office wing internal walls
    # Ground floor offices
    for i in range(5):
        oy = i * 5000
        if i > 0:
            msp.add_line((0, oy), (10000, oy), dxfattribs={"layer": "WALL"})

    # Corridor in office wing (2m wide)
    msp.add_line((4000, 0), (4000, H), dxfattribs={"layer": "WALL"})

    # Doors for each office
    for i in range(6):
        oy = i * 5000 + 1500
        add_door_line(msp, 4000, oy, 4000, oy + 1000, "DOOR")
        add_door(msp, 4000, oy, 1000, 90, "DOOR")
        # Right side offices
        if i < 5:
            add_door_line(msp, 4000, oy + 500, 4000, oy + 1500, "DOOR")

    # WC block in office wing
    msp.add_line((0, 25000), (4000, 25000), dxfattribs={"layer": "WALL"})
    msp.add_line((2000, 25000), (2000, H), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 1000, 25000, 1500, 25000, "DOOR")
    add_door_line(msp, 2500, 25000, 3000, 25000, "DOOR")

    # Stairwell in office wing
    add_stair(msp, 6000, 25000, 3500, 5000, 15, "STAIR")

    # Production hall doors (large roller doors)
    add_door_line(msp, 10000, 5000, 10000, 9000, "DOOR")  # Internal door to hall
    add_door_line(msp, 20000, 0, 25000, 0, "DOOR")  # Loading dock 1
    add_door_line(msp, 35000, 0, 40000, 0, "DOOR")  # Loading dock 2
    add_door_line(msp, W, 10000, W, 15000, "DOOR")  # Side entrance

    # Technical room in production hall
    msp.add_line((40000, H - 6000), (W, H - 6000), dxfattribs={"layer": "WALL"})
    msp.add_line((40000, H - 6000), (40000, H), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 43000, H - 6000, 44000, H - 6000, "DOOR")

    # Storage room in production hall
    msp.add_line((40000, 0), (40000, 8000), dxfattribs={"layer": "WALL"})
    msp.add_line((40000, 8000), (W, 8000), dxfattribs={"layer": "WALL"})
    add_door_line(msp, 40000, 3000, 40000, 5000, "DOOR")

    # Fire escape on the right side
    add_door_line(msp, W, 20000, W, 22000, "DOOR")

    # Columns in production hall (structural grid 5m x 5m)
    for cx in range(15000, W, 5000):
        for cy in range(5000, H, 5000):
            # Small column markers (not on walls)
            if cx > 10000 and cx < W and cy > 0 and cy < H:
                col_size = 300
                points = [
                    (cx - col_size, cy - col_size),
                    (cx + col_size, cy - col_size),
                    (cx + col_size, cy + col_size),
                    (cx - col_size, cy + col_size),
                    (cx - col_size, cy - col_size),
                ]
                msp.add_lwpolyline(points, dxfattribs={"layer": "WALL"})

    filepath = TESTDATA_DIR / "industrial_warehouse.dxf"
    doc.saveas(str(filepath))
    print(f"Created: {filepath}")


if __name__ == "__main__":
    TESTDATA_DIR.mkdir(exist_ok=True)
    generate_office_building()
    generate_residential_apartment()
    generate_industrial_warehouse()
    print("\nAll test DXF files generated!")
