"""Tests for FKS symbol functions in app/utils/symbols.py.

Focuses on: registry completeness, symbol content (text labels), key behaviour.
Avoids redundant per-symbol returns_group/has_children/custom_size tests.
"""

import pytest
import svgwrite

from app.utils.symbols import (
    SYMBOL_REGISTRY,
    assembly_point_symbol,
    bma_bs,
    electricity_shutoff,
    elevator_symbol,
    erstinfo_symbol,
    fire_access_arrow,
    fire_door_symbol,
    floor_section_indicator,
    gas_shutoff,
    north_arrow,
    rwa_symbol,
    smoke_detector,
    stair_direction_arrow,
    wall_hydrant_symbol,
    water_shutoff,
)


@pytest.fixture
def dwg() -> svgwrite.Drawing:
    return svgwrite.Drawing(size=("200mm", "200mm"))


# ── Registry ──────────────────────────────────────────────────────

class TestSymbolRegistry:
    EXPECTED_KEYS = {
        "north_arrow", "fire_access", "sprinkler_access",
        "smoke_detector", "manual_call_point", "key_depot", "bma_bs",
        "floor_section", "gas_shutoff", "water_shutoff", "electricity_shutoff",
        "stair_direction", "elevator", "wall_hydrant", "rwa",
        "assembly_point", "erstinfo", "fire_door",
    }

    def test_has_18_entries(self):
        assert len(SYMBOL_REGISTRY) == 18

    def test_expected_keys(self):
        assert set(SYMBOL_REGISTRY.keys()) == self.EXPECTED_KEYS

    def test_all_callable(self):
        for key, func in SYMBOL_REGISTRY.items():
            assert callable(func), f"{key} not callable"

    def test_invoke_all_returns_groups(self, dwg):
        """Every registry entry must produce an svgwrite Group."""
        for key, func in SYMBOL_REGISTRY.items():
            if key == "floor_section":
                result = func(dwg, 10, 10, ["EG", "OG1"], "EG")
            elif key in ("fire_access", "sprinkler_access"):
                result = func(dwg, 50, 50, angle=0, size=10)
            else:
                result = func(dwg, 50, 50)
            assert isinstance(result, svgwrite.container.Group), f"{key} failed"


# ── Content tests (parametrized) ──────────────────────────────────

class TestSymbolContent:
    """Verify each text-bearing symbol contains its expected label."""

    @pytest.mark.parametrize(
        "func, text",
        [
            (gas_shutoff, ">G<"),
            (water_shutoff, ">W<"),
            (electricity_shutoff, ">E<"),
            (bma_bs, ">BMZ<"),
            (wall_hydrant_symbol, ">WH<"),
            (rwa_symbol, ">RWA<"),
            (assembly_point_symbol, ">S<"),
            (erstinfo_symbol, ">EI<"),
            (fire_door_symbol, ">T<"),
            (elevator_symbol, ">A<"),
            (north_arrow, ">N<"),
            (smoke_detector, ">S<"),
        ],
        ids=lambda x: x.__name__ if callable(x) else x,
    )
    def test_contains_label(self, dwg, func, text):
        svg = func(dwg, 50, 50).tostring()
        assert text in svg

    def test_fire_access_arrow_red(self, dwg):
        svg = fire_access_arrow(dwg, 50, 50).tostring()
        assert "#FF0000" in svg

    def test_stair_direction_green(self, dwg):
        svg = stair_direction_arrow(dwg, 50, 50).tostring()
        assert "#228B22" in svg


# ── Floor section indicator ──────────────────────────────────────

class TestFloorSection:
    def test_highlights_current_floor(self, dwg):
        svg = floor_section_indicator(dwg, 0, 0, ["EG", "OG1", "OG2"], "OG1").tostring()
        assert "#FF6B6B" in svg  # highlight color

    def test_all_floors_labelled(self, dwg):
        floors = ["UG", "EG", "OG1"]
        svg = floor_section_indicator(dwg, 0, 0, floors, "EG").tostring()
        for f in floors:
            assert f in svg

    def test_element_count(self, dwg):
        result = floor_section_indicator(dwg, 0, 0, ["EG", "OG1"], "EG")
        assert len(result.elements) == 4  # 2 floors × (rect + text)


# ── Edge cases ────────────────────────────────────────────────────

class TestEdgeCases:
    def test_all_symbols_at_origin(self, dwg):
        """Symbols should not crash at (0, 0)."""
        for key, func in SYMBOL_REGISTRY.items():
            if key == "floor_section":
                func(dwg, 0, 0, ["EG"], "EG")
            elif key in ("fire_access", "sprinkler_access"):
                func(dwg, 0, 0, angle=0, size=5)
            else:
                func(dwg, 0, 0)
