"""Tests for DXF parsing pipeline — critical logic only."""

from pathlib import Path

import pytest

from app.pipeline.dxf_parser import (
    _classify_layer,
    _matches_patterns,
    parse_dxf,
    FIRE_DOOR_PATTERNS,
    FIRE_WALL_PATTERNS,
    WALL_PATTERNS,
)


class TestLayerClassification:
    """Test priority logic in layer classification (not pattern lists)."""

    def test_fire_wall_priority_over_wall(self):
        """'brandwand' contains 'wand' but must classify as fire_wall."""
        assert _classify_layer("brandwand") == "fire_wall"

    def test_fire_door_priority_over_door(self):
        """'fire_door_01' contains 'door' but must classify as fire_door."""
        assert _classify_layer("fire_door_01") == "fire_door"

    def test_classify_wall(self):
        assert _classify_layer("A-WALL") == "wall"

    def test_classify_door(self):
        assert _classify_layer("A-DOOR") == "door"

    def test_classify_skip(self):
        assert _classify_layer("FURNITURE") == "skip"

    def test_classify_unknown(self):
        assert _classify_layer("RANDOM-LAYER") == "unknown"


class TestDxfParsing:
    """Integration tests with real DXF files."""

    def test_parse_sample_dxf(self, sample_dxf_path: Path):
        result = parse_dxf(sample_dxf_path)
        assert result.filename == "floorplan_sample.dxf"
        assert len(result.walls) > 50
        minx, miny, maxx, maxy = result.bounds
        assert maxx > minx
        assert maxy > miny

    def test_parse_nonexistent_file(self):
        with pytest.raises(Exception):
            parse_dxf("/nonexistent/file.dxf")

    def test_parse_returns_fire_safety_fields(self, sample_dxf_path: Path):
        result = parse_dxf(sample_dxf_path)
        assert isinstance(result.fire_walls, list)
        assert isinstance(result.fire_doors, list)
        assert isinstance(result.windows, list)
        assert isinstance(result.has_sprinkler, bool)


class TestSyntheticDxfFiles:
    """Test parser across synthetic DXFs with different units and conventions."""

    def test_parse_synthetic_dxf(self, synthetic_dxf_path: Path):
        result = parse_dxf(synthetic_dxf_path)
        assert len(result.walls) > 0
        minx, miny, maxx, maxy = result.bounds
        assert maxx > minx and maxy > miny

    def test_warehouse_has_fire_walls(self):
        from tests.conftest import SYNTHETIC_DXFS
        path = SYNTHETIC_DXFS.get("warehouse_cm")
        if path is None or not path.exists():
            pytest.skip("warehouse_cm.dxf not found")
        result = parse_dxf(path)
        assert len(result.fire_walls) > 0

    def test_warehouse_has_sprinkler(self):
        from tests.conftest import SYNTHETIC_DXFS
        path = SYNTHETIC_DXFS.get("warehouse_cm")
        if path is None or not path.exists():
            pytest.skip("warehouse_cm.dxf not found")
        result = parse_dxf(path)
        assert result.has_sprinkler is True

    def test_door_deduplication(self):
        from app.models.schemas import DoorInfo, Point
        from app.pipeline.dxf_parser import _deduplicate_doors
        doors = [
            DoorInfo(position=Point(x=10, y=10), width=30),
            DoorInfo(position=Point(x=10.5, y=10.5), width=28),
            DoorInfo(position=Point(x=100, y=100), width=30),
        ]
        result = _deduplicate_doors(doors, tolerance=5.0)
        assert len(result) == 2
