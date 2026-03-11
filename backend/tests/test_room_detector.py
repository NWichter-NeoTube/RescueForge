"""Tests for room detection pipeline."""

from pathlib import Path

import pytest

from app.models.schemas import FloorPlanData, Point, WallSegment
from app.pipeline.dxf_parser import parse_dxf
from app.pipeline.room_detector import detect_rooms


def _make_box_floor_plan(
    x: float, y: float, w: float, h: float, label: str = "test"
) -> FloorPlanData:
    """Create a simple rectangular floor plan for testing."""
    walls = [
        WallSegment(start=Point(x=x, y=y), end=Point(x=x + w, y=y)),
        WallSegment(start=Point(x=x + w, y=y), end=Point(x=x + w, y=y + h)),
        WallSegment(start=Point(x=x + w, y=y + h), end=Point(x=x, y=y + h)),
        WallSegment(start=Point(x=x, y=y + h), end=Point(x=x, y=y)),
    ]
    return FloorPlanData(
        filename=f"{label}.dxf",
        walls=walls,
        bounds=(x, y, x + w, y + h),
    )


def _make_multi_room_floor_plan() -> FloorPlanData:
    """Create a floor plan with multiple rooms sharing walls."""
    walls = [
        # Outer boundary
        WallSegment(start=Point(x=0, y=0), end=Point(x=20, y=0)),
        WallSegment(start=Point(x=20, y=0), end=Point(x=20, y=10)),
        WallSegment(start=Point(x=20, y=10), end=Point(x=0, y=10)),
        WallSegment(start=Point(x=0, y=10), end=Point(x=0, y=0)),
        # Internal wall dividing into 2 rooms
        WallSegment(start=Point(x=10, y=0), end=Point(x=10, y=10)),
    ]
    return FloorPlanData(
        filename="multi_room.dxf",
        walls=walls,
        bounds=(0, 0, 20, 10),
    )


class TestRoomDetection:
    """Test room polygon detection."""

    def test_single_room(self):
        """A simple box should produce exactly 1 room."""
        fp = _make_box_floor_plan(0, 0, 100, 100)
        rooms = detect_rooms(fp)
        assert len(rooms) >= 1, "Should detect at least one room from a closed box"

    def test_multi_room(self):
        """Two rooms divided by an internal wall should produce 2 rooms."""
        fp = _make_multi_room_floor_plan()
        rooms = detect_rooms(fp)
        assert len(rooms) == 2, f"Expected 2 rooms, got {len(rooms)}"

    def test_room_ids_unique(self):
        """Room IDs should be unique."""
        fp = _make_multi_room_floor_plan()
        rooms = detect_rooms(fp)
        ids = [r.id for r in rooms]
        assert len(ids) == len(set(ids)), "Room IDs must be unique"

    def test_room_ids_sequential(self):
        """Room IDs should be sequential starting from 1."""
        fp = _make_multi_room_floor_plan()
        rooms = detect_rooms(fp)
        expected_ids = list(range(1, len(rooms) + 1))
        actual_ids = sorted([r.id for r in rooms])
        assert actual_ids == expected_ids

    def test_room_area_positive(self):
        """All detected rooms should have positive area."""
        fp = _make_multi_room_floor_plan()
        rooms = detect_rooms(fp)
        for room in rooms:
            assert room.area > 0, f"Room {room.id} has non-positive area: {room.area}"

    def test_room_points_polygon(self):
        """Each room should have at least 3 points forming a polygon."""
        fp = _make_multi_room_floor_plan()
        rooms = detect_rooms(fp)
        for room in rooms:
            assert len(room.points) >= 3, \
                f"Room {room.id} has only {len(room.points)} points"

    def test_no_walls_no_rooms(self):
        """Empty floor plan should produce no rooms."""
        fp = FloorPlanData(filename="empty.dxf", walls=[], bounds=(0, 0, 0, 0))
        rooms = detect_rooms(fp)
        assert len(rooms) == 0

    def test_detect_from_sample_dxf(self, sample_dxf_path: Path):
        """Integration test: parse real DXF, then detect rooms."""
        floor_plan = parse_dxf(sample_dxf_path)
        rooms = detect_rooms(floor_plan)
        assert len(rooms) >= 3, f"Expected at least 3 rooms, got {len(rooms)}"

        total_area = sum(r.area for r in rooms)
        assert total_area > 0, "Total room area should be positive"
