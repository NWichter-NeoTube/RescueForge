"""Tests for symbol collision avoidance (_SymbolPlacer)."""

import pytest

from app.pipeline.plan_generator import _SymbolPlacer


class TestSymbolPlacerBasic:
    """Basic placement tests."""

    def test_first_placement_always_succeeds_at_original(self):
        """The very first placement should always use the original position."""
        placer = _SymbolPlacer()
        x, y = placer.place(10.0, 20.0, 3.0)
        assert x == 10.0
        assert y == 20.0

    def test_no_overlap_when_sufficient_spacing(self):
        """Symbols far apart should not be shifted."""
        placer = _SymbolPlacer()
        x1, y1 = placer.place(10.0, 10.0, 3.0)
        x2, y2 = placer.place(50.0, 50.0, 3.0)  # Far away

        assert x1 == 10.0 and y1 == 10.0
        assert x2 == 50.0 and y2 == 50.0

    def test_shifts_on_overlap(self):
        """Overlapping placement should be shifted to a new position."""
        placer = _SymbolPlacer()
        placer.place(10.0, 10.0, 5.0)  # Occupies 7.5-12.5 in both axes

        # Place another symbol at the same position
        x2, y2 = placer.place(10.0, 10.0, 5.0)

        # Should have been shifted
        assert (x2, y2) != (10.0, 10.0), "Overlapping symbol should be shifted"

        # Should be shifted by size*1.2 in one of the 4 directions
        shift = 5.0 * 1.2
        valid_positions = [
            (10.0 + shift, 10.0),  # right
            (10.0 - shift, 10.0),  # left
            (10.0, 10.0 + shift),  # down
            (10.0, 10.0 - shift),  # up
        ]
        assert (x2, y2) in valid_positions, f"Shifted to unexpected ({x2}, {y2})"


class TestSymbolPlacerRegister:
    """Tests for register() (blocking areas without shifting)."""

    def test_register_blocks_area(self):
        """A registered label should prevent symbol placement at that position."""
        placer = _SymbolPlacer()
        # Register a room label (e.g. 10x4 text block at (20, 20))
        placer.register(20.0, 20.0, 10.0, 4.0)

        # Try placing a symbol right on top
        x, y = placer.place(20.0, 20.0, 3.0)

        # Should be shifted away
        assert (x, y) != (20.0, 20.0), "Symbol should not overlap registered label"

    def test_register_does_not_shift(self):
        """register() should accept the position as-is (no shifting)."""
        placer = _SymbolPlacer()
        placer.place(10.0, 10.0, 5.0)

        # Registering at the same spot should NOT shift (it's register, not place)
        placer.register(10.0, 10.0, 5.0, 5.0)

        # Both should be recorded — placing a third element should now
        # avoid both registered areas
        x3, y3 = placer.place(10.0, 10.0, 5.0)
        assert (x3, y3) != (10.0, 10.0)


class TestSymbolPlacerEdgeCases:
    """Edge cases and max attempts."""

    def test_max_attempts_returns_original_when_all_blocked(self):
        """When all 4 shift directions are blocked, returns original position."""
        placer = _SymbolPlacer()
        size = 5.0
        shift = size * 1.2

        # Block all 4 shift directions and the center
        placer.register(10.0, 10.0, size, size)                   # center
        placer.register(10.0 + shift, 10.0, size, size)           # right
        placer.register(10.0 - shift, 10.0, size, size)           # left
        placer.register(10.0, 10.0 + shift, size, size)           # down
        placer.register(10.0, 10.0 - shift, size, size)           # up

        # Place should exhaust all attempts and return original
        x, y = placer.place(10.0, 10.0, size)
        assert x == 10.0 and y == 10.0, "Should fall back to original when all blocked"

    def test_overlaps_method_aabb(self):
        """Verify AABB (Axis-Aligned Bounding Box) overlap detection."""
        placer = _SymbolPlacer()
        placer.register(10.0, 10.0, 6.0, 4.0)  # stored as (7,8,6,4) → covers x=[7,13], y=[8,12]

        # Center clearly inside
        assert placer._overlaps(10.0, 10.0, 2.0, 2.0) is True
        # Partially overlapping (center at 12.0 → box [11,9]-[13,11] overlaps [7,8]-[13,12])
        assert placer._overlaps(12.0, 10.0, 2.0, 2.0) is True
        # Just touching edge (box [13,9]-[15,11] — not overlapping, edges touching)
        assert placer._overlaps(14.0, 10.0, 2.0, 2.0) is False
        # Clearly outside
        assert placer._overlaps(20.0, 20.0, 2.0, 2.0) is False

    def test_many_symbols_unique_positions(self):
        """Placing many symbols should produce mostly unique positions."""
        placer = _SymbolPlacer()
        positions = set()
        for i in range(10):
            # All start at the same position
            x, y = placer.place(10.0, 10.0, 3.0)
            positions.add((round(x, 2), round(y, 2)))

        # Not all should be identical (though max 5 unique due to 4 directions + original)
        assert len(positions) >= 2, "Should have at least 2 unique positions from 10 placements"
