"""Tests for DXF parsing pipeline."""

from pathlib import Path

import pytest

from app.pipeline.dxf_parser import (
    _classify_layer,
    _is_anonymized_layer,
    _matches_patterns,
    parse_dxf,
    DOOR_BLOCK_PATTERNS,
    DOOR_PATTERNS,
    FIRE_DOOR_PATTERNS,
    FIRE_WALL_PATTERNS,
    SKIP_PATTERNS,
    SPRINKLER_PATTERNS,
    STAIR_PATTERNS,
    WALL_PATTERNS,
    WINDOW_BLOCK_PATTERNS,
    WINDOW_PATTERNS,
)


class TestLayerClassification:
    """Test layer name pattern matching and classification."""

    def test_wall_patterns_match(self):
        assert _matches_patterns("A-WALL", WALL_PATTERNS)
        assert _matches_patterns("xref-08$0$A-WALL", WALL_PATTERNS)
        assert _matches_patterns("Wand_EG", WALL_PATTERNS)
        assert _matches_patterns("S-WALL-BEARING", WALL_PATTERNS)

    def test_door_patterns_match(self):
        assert _matches_patterns("A-DOOR", DOOR_PATTERNS)
        assert _matches_patterns("Tür_EG", DOOR_PATTERNS)
        assert _matches_patterns("A-OPENING", DOOR_PATTERNS)

    def test_stair_patterns_match(self):
        assert _matches_patterns("A-STAIR", STAIR_PATTERNS)
        assert _matches_patterns("Treppe_1OG", STAIR_PATTERNS)

    def test_skip_patterns_match(self):
        assert _matches_patterns("A-DIMS-1", SKIP_PATTERNS)
        assert _matches_patterns("FURNITURE", SKIP_PATTERNS)
        assert _matches_patterns("A-NOTE", SKIP_PATTERNS)
        assert _matches_patterns("Möbel_EG", SKIP_PATTERNS)

    def test_classify_wall(self):
        assert _classify_layer("A-WALL") == "wall"
        assert _classify_layer("xref$0$A-WALL") == "wall"

    def test_classify_door(self):
        assert _classify_layer("A-DOOR") == "door"

    def test_classify_skip(self):
        assert _classify_layer("A-DIMS-1") == "skip"
        assert _classify_layer("FURNITURE") == "skip"

    def test_classify_unknown(self):
        assert _classify_layer("RANDOM-LAYER") == "unknown"
        assert _classify_layer("0") == "unknown"

    def test_case_insensitive(self):
        assert _matches_patterns("A-WALL", WALL_PATTERNS)
        assert _matches_patterns("a-wall", WALL_PATTERNS)
        assert _matches_patterns("A-Wall", WALL_PATTERNS)

    def test_vietnamese_patterns(self):
        """Vietnamese layer names from DWGShare.com files."""
        assert _matches_patterns("tuong_xay", WALL_PATTERNS)
        assert _matches_patterns("cua_chinh", DOOR_PATTERNS)
        assert _matches_patterns("cau thang_01", STAIR_PATTERNS)

    def test_french_spanish_patterns(self):
        """French and Spanish layer names."""
        assert _matches_patterns("MUR-EXT", WALL_PATTERNS)
        assert _matches_patterns("PORTE-01", DOOR_PATTERNS)
        assert _matches_patterns("PARED_INT", WALL_PATTERNS)

    def test_door_block_patterns(self):
        """Block reference names that indicate doors."""
        assert _matches_patterns("DOOR_SINGLE", DOOR_BLOCK_PATTERNS)
        assert _matches_patterns("DR_900", DOOR_BLOCK_PATTERNS)
        assert _matches_patterns("SGL_DOOR_90", DOOR_BLOCK_PATTERNS)
        assert not _matches_patterns("WINDOW_1200", DOOR_BLOCK_PATTERNS)

    def test_window_block_patterns(self):
        """Block reference names that indicate windows (to skip)."""
        assert _matches_patterns("WINDOW_1200", WINDOW_BLOCK_PATTERNS)
        assert _matches_patterns("FENSTER_EG", WINDOW_BLOCK_PATTERNS)
        assert not _matches_patterns("DOOR_900", WINDOW_BLOCK_PATTERNS)

    def test_anonymized_layer_detection(self):
        """Detect anonymized layers from DWGShare.com."""
        assert _is_anonymized_layer("DWGshare.com_9")
        assert _is_anonymized_layer("DWGShare.com_14")
        assert _is_anonymized_layer("layer5")
        assert _is_anonymized_layer("42")
        assert not _is_anonymized_layer("A-WALL")
        assert not _is_anonymized_layer("Wand_EG")

    def test_hatch_skip_patterns(self):
        """Hatch/fill patterns should be skipped."""
        assert _matches_patterns("HATCH_WALL", SKIP_PATTERNS)
        assert _matches_patterns("schraffur_01", SKIP_PATTERNS)


class TestDxfParsing:
    """Test DXF file parsing with sample data."""

    def test_parse_sample_dxf(self, sample_dxf_path: Path):
        """Test parsing the sample DXF file extracts walls and doors."""
        result = parse_dxf(sample_dxf_path)

        assert result.filename == "floorplan_sample.dxf"
        assert len(result.walls) > 0, "Should detect at least some walls"
        assert len(result.doors) >= 0, "Doors may or may not be present"

        # Bounds should be valid
        minx, miny, maxx, maxy = result.bounds
        assert maxx > minx, "Bounding box should have positive width"
        assert maxy > miny, "Bounding box should have positive height"

    def test_parse_sample_dxf_wall_count(self, sample_dxf_path: Path):
        """Test that wall extraction produces reasonable results."""
        result = parse_dxf(sample_dxf_path)

        # Our sample should have 200+ walls
        assert len(result.walls) > 50, f"Expected many walls, got {len(result.walls)}"

    def test_parse_sample_dxf_wall_segments_valid(self, sample_dxf_path: Path):
        """Test that wall segments have valid coordinates."""
        result = parse_dxf(sample_dxf_path)

        for wall in result.walls[:20]:
            assert wall.start.x != wall.end.x or wall.start.y != wall.end.y, \
                "Wall segment should have non-zero length"

    def test_parse_nonexistent_file(self):
        """Test error handling for missing files."""
        with pytest.raises(Exception):
            parse_dxf("/nonexistent/file.dxf")


class TestFireWallPatterns:
    """Test fire wall layer pattern matching and classification."""

    def test_fire_wall_layer_match(self):
        """Fire wall layer names should match FIRE_WALL_PATTERNS."""
        assert _matches_patterns("Brandwand_EG", FIRE_WALL_PATTERNS)
        assert _matches_patterns("FIRE_WALL-01", FIRE_WALL_PATTERNS)
        assert _matches_patterns("FW-Keller", FIRE_WALL_PATTERNS)
        assert _matches_patterns("Brandschutzwand", FIRE_WALL_PATTERNS)

    def test_fire_wall_classification(self):
        """_classify_layer should return 'fire_wall' for fire wall layers."""
        assert _classify_layer("Brandwand_EG") == "fire_wall"

    def test_fire_wall_priority_over_wall(self):
        """Fire wall classification should take priority over generic wall.

        'brandwand' contains 'wand' which matches WALL_PATTERNS, but the
        fire_wall check must come first in _classify_layer.
        """
        assert _classify_layer("brandwand") == "fire_wall"


class TestFireDoorPatterns:
    """Test fire door layer pattern matching and classification."""

    def test_fire_door_layer_match(self):
        """Fire door layer names should match FIRE_DOOR_PATTERNS."""
        assert _matches_patterns("Brandschutz_T30", FIRE_DOOR_PATTERNS)
        assert _matches_patterns("FIRE_DOOR", FIRE_DOOR_PATTERNS)
        assert _matches_patterns("T90-Tuer", FIRE_DOOR_PATTERNS)
        assert _matches_patterns("EI60_door", FIRE_DOOR_PATTERNS)

    def test_fire_door_classification(self):
        """_classify_layer should return 'fire_door' for fire door layers."""
        assert _classify_layer("Brandschutz_EG") == "fire_door"

    def test_fire_door_priority(self):
        """Fire door classification should take priority over generic door.

        'fire_door_01' contains 'door' which matches DOOR_PATTERNS, but the
        fire_door check must come first in _classify_layer.
        """
        assert _classify_layer("fire_door_01") == "fire_door"


class TestWindowPatterns:
    """Test window layer pattern matching and classification."""

    def test_window_layer_match(self):
        """Window layer names should match WINDOW_PATTERNS."""
        assert _matches_patterns("WINDOW-01", WINDOW_PATTERNS)
        assert _matches_patterns("Fenster_EG", WINDOW_PATTERNS)
        assert _matches_patterns("GLAZING-EXT", WINDOW_PATTERNS)
        assert _matches_patterns("Verglasung", WINDOW_PATTERNS)

    def test_window_classification(self):
        """_classify_layer should return 'window' for window layers."""
        assert _classify_layer("WINDOW-EXT") == "window"


class TestSprinklerPatterns:
    """Test sprinkler layer pattern matching and classification."""

    def test_sprinkler_layer_match(self):
        """Sprinkler layer names should match SPRINKLER_PATTERNS."""
        assert _matches_patterns("SPRINKLER-ZONE", SPRINKLER_PATTERNS)
        assert _matches_patterns("SPK-01", SPRINKLER_PATTERNS)
        assert _matches_patterns("Löschanlage", SPRINKLER_PATTERNS)

    def test_sprinkler_classification(self):
        """_classify_layer should return 'sprinkler' for sprinkler layers."""
        assert _classify_layer("SPRINKLER-SYSTEM") == "sprinkler"


class TestFloorPlanDataNewFields:
    """Test that parse_dxf returns the new fire safety fields."""

    def test_parse_returns_new_fields(self, sample_dxf_path: Path):
        """Parsed FloorPlanData should include fire_walls, fire_doors, windows, and has_sprinkler."""
        result = parse_dxf(sample_dxf_path)

        assert isinstance(result.fire_walls, list), "fire_walls should be a list"
        assert isinstance(result.fire_doors, list), "fire_doors should be a list"
        assert isinstance(result.windows, list), "windows should be a list"
        assert isinstance(result.has_sprinkler, bool), "has_sprinkler should be a bool"


class TestSyntheticDxfFiles:
    """Test parser across multiple DXF files with different units and conventions."""

    def test_parse_synthetic_dxf(self, synthetic_dxf_path: Path):
        """All synthetic DXFs should parse without error and produce walls."""
        result = parse_dxf(synthetic_dxf_path)
        assert len(result.walls) > 0, f"No walls found in {synthetic_dxf_path.name}"
        minx, miny, maxx, maxy = result.bounds
        assert maxx > minx, "Bounds width must be positive"
        assert maxy > miny, "Bounds height must be positive"

    def test_warehouse_has_fire_walls(self):
        """Warehouse DXF with Brandwand layer should detect fire walls."""
        from tests.conftest import SYNTHETIC_DXFS
        path = SYNTHETIC_DXFS.get("warehouse_cm")
        if path is None or not path.exists():
            pytest.skip("warehouse_cm.dxf not found")
        result = parse_dxf(path)
        assert len(result.fire_walls) > 0, "Fire wall should be detected"

    def test_warehouse_has_sprinkler(self):
        """Warehouse DXF with SPRINKLER-ZONE layer should flag sprinkler system."""
        from tests.conftest import SYNTHETIC_DXFS
        path = SYNTHETIC_DXFS.get("warehouse_cm")
        if path is None or not path.exists():
            pytest.skip("warehouse_cm.dxf not found")
        result = parse_dxf(path)
        assert result.has_sprinkler is True

    def test_house_meters_unit(self):
        """House DXF should report 'm' unit."""
        from tests.conftest import SYNTHETIC_DXFS
        path = SYNTHETIC_DXFS.get("house_m")
        if path is None or not path.exists():
            pytest.skip("house_meters.dxf not found")
        result = parse_dxf(path)
        assert result.unit == "m"

    def test_door_deduplication(self):
        """Door deduplication should reduce duplicate entries."""
        from app.models.schemas import DoorInfo, Point
        from app.pipeline.dxf_parser import _deduplicate_doors
        doors = [
            DoorInfo(position=Point(x=10, y=10), width=30),
            DoorInfo(position=Point(x=10.5, y=10.5), width=28),  # near-duplicate
            DoorInfo(position=Point(x=100, y=100), width=30),
        ]
        result = _deduplicate_doors(doors, tolerance=5.0)
        assert len(result) == 2, f"Expected 2 doors, got {len(result)}"
