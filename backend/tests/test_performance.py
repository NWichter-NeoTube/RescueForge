"""Performance regression tests to catch slowdowns early.

Each test asserts that a pipeline step completes under a generous time limit.
These limits are intentionally loose (2-5x expected) to avoid flaky tests,
while still catching catastrophic regressions.
"""

import time
from pathlib import Path

import pytest

from tests.conftest import SAMPLE_DXF


@pytest.fixture
def dxf_path():
    if not SAMPLE_DXF.exists():
        pytest.skip("Sample DXF not available")
    return SAMPLE_DXF


class TestParsingPerformance:
    def test_dxf_parsing_under_2s(self, dxf_path):
        """DXF parsing should complete in under 2 seconds."""
        from app.pipeline.dxf_parser import parse_dxf

        start = time.perf_counter()
        result = parse_dxf(dxf_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"DXF parsing took {elapsed:.2f}s (limit: 2.0s)"
        assert len(result.walls) > 0, "Parsing should find walls"

    def test_room_detection_under_2s(self, dxf_path):
        """Room detection should complete in under 2 seconds."""
        from app.pipeline.dxf_parser import parse_dxf
        from app.pipeline.room_detector import detect_rooms

        floor_plan = parse_dxf(dxf_path)

        start = time.perf_counter()
        rooms = detect_rooms(floor_plan)
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Room detection took {elapsed:.2f}s (limit: 2.0s)"
        assert len(rooms) > 0, "Should detect at least one room"


class TestGenerationPerformance:
    def test_svg_generation_under_2s(self, dxf_path, tmp_output):
        """SVG generation should complete in under 2 seconds."""
        from app.pipeline.dxf_parser import parse_dxf
        from app.pipeline.room_detector import detect_rooms
        from app.pipeline.plan_generator import generate_svg

        floor_plan = parse_dxf(dxf_path)
        rooms = detect_rooms(floor_plan)
        out = tmp_output / "test_orientierungsplan.svg"

        start = time.perf_counter()
        svg_path = generate_svg(floor_plan, rooms, out)
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"SVG generation took {elapsed:.2f}s (limit: 2.0s)"
        assert svg_path.exists()
        assert svg_path.stat().st_size > 0

    def test_pdf_export_under_10s(self, dxf_path, tmp_output):
        """PDF export should complete in under 10 seconds."""
        from app.pipeline.dxf_parser import parse_dxf
        from app.pipeline.room_detector import detect_rooms
        from app.pipeline.plan_generator import generate_svg

        try:
            from app.pipeline.pdf_exporter import export_pdf
        except (OSError, ImportError):
            pytest.skip("WeasyPrint not available (needs Cairo/GLib)")

        floor_plan = parse_dxf(dxf_path)
        rooms = detect_rooms(floor_plan)
        svg_path = generate_svg(floor_plan, rooms, tmp_output / "test.svg")
        pdf_path = tmp_output / "test.pdf"

        start = time.perf_counter()
        export_pdf(svg_path, pdf_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 10.0, f"PDF export took {elapsed:.2f}s (limit: 10.0s)"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 1000, "PDF should be > 1KB"

    def test_cover_sheet_under_2s(self, dxf_path, tmp_output):
        """Cover sheet generation should complete in under 2 seconds."""
        from app.pipeline.dxf_parser import parse_dxf
        from app.pipeline.room_detector import detect_rooms
        from app.pipeline.plan_generator import generate_cover_sheet

        floor_plan = parse_dxf(dxf_path)
        rooms = detect_rooms(floor_plan)
        out = tmp_output / "test_deckblatt.svg"

        start = time.perf_counter()
        generate_cover_sheet(rooms, out, building_name="Test", floors=["EG"])
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Cover sheet took {elapsed:.2f}s (limit: 2.0s)"
        assert out.exists()

    def test_situation_plan_under_2s(self, dxf_path, tmp_output):
        """Situation plan generation should complete in under 2 seconds."""
        from app.pipeline.dxf_parser import parse_dxf
        from app.pipeline.room_detector import detect_rooms
        from app.pipeline.plan_generator import generate_situation_plan

        floor_plan = parse_dxf(dxf_path)
        rooms = detect_rooms(floor_plan)
        out = tmp_output / "test_situationsplan.svg"

        start = time.perf_counter()
        generate_situation_plan(floor_plan, rooms, out, building_name="Test")
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Situation plan took {elapsed:.2f}s (limit: 2.0s)"
        assert out.exists()
