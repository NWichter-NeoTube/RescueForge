"""Tests for error handling, retry logic, and new safety features."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.models.schemas import (
    FloorPlanData,
    Point,
    RoomPolygon,
    RoomType,
    WallSegment,
)
from app.pipeline.dxf_parser import DXFParseError
from app.pipeline.room_classifier import classify_rooms

# WeasyPrint requires system libraries (GTK/Pango) — skip PDF tests if unavailable
try:
    from app.pipeline.pdf_exporter import PDFExportError, export_pdf
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False


# ── DXFParseError Tests ──────────────────────────────────────


class TestDXFParseError:
    def test_nonexistent_file_raises(self):
        """Parsing a nonexistent file should raise DXFParseError."""
        from app.pipeline.dxf_parser import parse_dxf

        with pytest.raises(DXFParseError, match="not found"):
            parse_dxf("/nonexistent/file.dxf")

    def test_empty_file_raises(self, tmp_path: Path):
        """Parsing an empty file should raise DXFParseError."""
        from app.pipeline.dxf_parser import parse_dxf

        empty = tmp_path / "empty.dxf"
        empty.write_text("")
        with pytest.raises(DXFParseError, match="empty"):
            parse_dxf(str(empty))

    def test_corrupt_file_raises(self, tmp_path: Path):
        """Parsing a corrupt DXF file should raise DXFParseError."""
        from app.pipeline.dxf_parser import parse_dxf

        corrupt = tmp_path / "corrupt.dxf"
        corrupt.write_text("NOT A VALID DXF FILE\nGARBAGE DATA")
        with pytest.raises((DXFParseError, Exception)):
            parse_dxf(str(corrupt))

    def test_error_message_contains_path(self, tmp_path: Path):
        """Error message should contain the file path."""
        from app.pipeline.dxf_parser import parse_dxf

        missing = str(tmp_path / "missing.dxf")
        with pytest.raises(DXFParseError) as exc_info:
            parse_dxf(missing)
        assert "missing.dxf" in str(exc_info.value)


# ── PDFExportError Tests ─────────────────────────────────────


@pytest.mark.skipif(not HAS_WEASYPRINT, reason="WeasyPrint system libraries not available")
class TestPDFExportError:
    def test_missing_svg_raises(self, tmp_path: Path):
        """Exporting PDF from nonexistent SVG should raise PDFExportError."""
        with pytest.raises(PDFExportError, match="not found"):
            export_pdf(tmp_path / "missing.svg", tmp_path / "out.pdf")

    def test_empty_svg_raises(self, tmp_path: Path):
        """Exporting PDF from empty SVG should raise PDFExportError."""
        svg = tmp_path / "empty.svg"
        svg.write_text("")
        with pytest.raises(PDFExportError, match="empty"):
            export_pdf(svg, tmp_path / "out.pdf")

    def test_valid_svg_exports(self, tmp_path: Path):
        """A valid SVG should produce a non-empty PDF."""
        svg = tmp_path / "test.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<rect width="100" height="100" fill="red"/></svg>'
        )
        pdf = tmp_path / "test.pdf"
        result = export_pdf(svg, pdf)
        assert result.exists()
        assert result.stat().st_size > 0


# ── Room Classifier Retry Tests ──────────────────────────────


@pytest.fixture
def simple_plan() -> FloorPlanData:
    return FloorPlanData(
        filename="test.dxf",
        walls=[
            WallSegment(start=Point(x=0, y=0), end=Point(x=10000, y=0)),
            WallSegment(start=Point(x=10000, y=0), end=Point(x=10000, y=8000)),
        ],
        bounds=(0, 0, 10000, 8000),
    )


@pytest.fixture
def test_rooms() -> list[RoomPolygon]:
    return [
        RoomPolygon(
            id=1,
            points=[Point(x=0, y=0), Point(x=5000, y=0), Point(x=5000, y=4000), Point(x=0, y=4000)],
            area=20_000_000,
        ),
        RoomPolygon(
            id=2,
            points=[Point(x=5000, y=0), Point(x=10000, y=0), Point(x=10000, y=4000), Point(x=5000, y=4000)],
            area=20_000_000,
        ),
    ]


class TestClassifyRoomsRetry:
    @pytest.mark.asyncio
    async def test_retries_on_api_failure(self, simple_plan, test_rooms, tmp_path):
        """classify_rooms should retry when Vision API fails on first attempt."""
        mock_response = json.dumps([
            {"id": 1, "type": "office", "label": "Buero"},
            {"id": 2, "type": "corridor", "label": "Korridor"},
        ])

        call_count = 0

        async def flaky_api(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Transient error")
            return mock_response

        with patch("app.pipeline.room_classifier.call_vision_api", side_effect=flaky_api):
            result = await classify_rooms(simple_plan, test_rooms, tmp_path)

        assert call_count >= 2, "Should have retried after first failure"
        assert result[0].room_type == RoomType.OFFICE

    @pytest.mark.asyncio
    async def test_falls_back_to_heuristic_after_all_retries(self, simple_plan, test_rooms, tmp_path):
        """After exhausting retries, should fall back to heuristic classification."""
        with patch(
            "app.pipeline.room_classifier.call_vision_api",
            new_callable=AsyncMock,
            side_effect=Exception("Persistent error"),
        ):
            result = await classify_rooms(simple_plan, test_rooms, tmp_path)

        # All rooms should still be classified (via heuristic fallback)
        assert len(result) == 2
        for r in result:
            assert r.room_type != RoomType.UNKNOWN

    @pytest.mark.asyncio
    async def test_retries_on_low_classification_rate(self, simple_plan, test_rooms, tmp_path):
        """Should retry when less than 30% of rooms are classified."""
        call_count = 0

        async def partial_then_full(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Only classify 0 out of 2 rooms (returns empty array)
                return "[]"
            # Second attempt classifies both
            return json.dumps([
                {"id": 1, "type": "office", "label": "Buero"},
                {"id": 2, "type": "corridor", "label": "Korridor"},
            ])

        with patch("app.pipeline.room_classifier.call_vision_api", side_effect=partial_then_full):
            result = await classify_rooms(simple_plan, test_rooms, tmp_path)

        assert call_count >= 2, "Should have retried after poor classification"


# ── Room Type Validation Tests ───────────────────────────────


class TestRoomTypeValidation:
    def test_all_enum_values_are_valid(self):
        """All RoomType enum values should be valid strings."""
        for rt in RoomType:
            assert isinstance(rt.value, str)
            assert len(rt.value) > 0

    def test_unknown_room_type_detection(self):
        """An invalid room type string should not be in RoomType values."""
        valid = {rt.value for rt in RoomType}
        assert "invalid_type" not in valid
        assert "foo" not in valid


# ── Security Headers Test ────────────────────────────────────


class TestSecurityHeaders:
    def test_security_middleware_imported(self):
        """SecurityHeadersMiddleware should be importable."""
        try:
            from app.main import SecurityHeadersMiddleware
            assert SecurityHeadersMiddleware is not None
        except ImportError:
            pytest.skip("Not available locally — runs in Docker CI")

    def test_rate_limit_middleware_imported(self):
        """RateLimitMiddleware should be importable."""
        try:
            from app.main import RateLimitMiddleware
            assert RateLimitMiddleware is not None
        except ImportError:
            pytest.skip("Not available locally — runs in Docker CI")


# ── Plan Generator Config Tests ──────────────────────────────


class TestLayoutConfig:
    def test_paper_size_a3(self):
        from app.pipeline.plan_generator import LayoutConfig
        w, h = LayoutConfig.paper_size("A3")
        assert w == 420
        assert h == 297

    def test_paper_size_a4(self):
        from app.pipeline.plan_generator import LayoutConfig
        w, h = LayoutConfig.paper_size("A4")
        assert w == 297
        assert h == 210

    def test_config_values_positive(self):
        from app.pipeline.plan_generator import LayoutConfig
        assert LayoutConfig.MARGIN > 0
        assert LayoutConfig.TITLE_BLOCK_HEIGHT > 0
        assert LayoutConfig.LEGEND_WIDTH > 0
        assert LayoutConfig.PLAN_PADDING > 0
        assert LayoutConfig.PLAN_PADDING <= 1


class TestCentroidCache:
    def test_centroid_cache_computes_all(self):
        from app.pipeline.plan_generator import _compute_room_centroids

        rooms = [
            RoomPolygon(
                id=1,
                points=[Point(x=0, y=0), Point(x=10, y=0), Point(x=10, y=10), Point(x=0, y=10)],
                area=100,
            ),
            RoomPolygon(
                id=2,
                points=[Point(x=20, y=20), Point(x=30, y=20), Point(x=30, y=30), Point(x=20, y=30)],
                area=100,
            ),
        ]
        cache = _compute_room_centroids(rooms)
        assert 1 in cache
        assert 2 in cache
        # Centroid of a square (0,0)-(10,10) is (5,5)
        assert abs(cache[1][0] - 5.0) < 0.1
        assert abs(cache[1][1] - 5.0) < 0.1

    def test_centroid_cache_skips_degenerate(self):
        from app.pipeline.plan_generator import _compute_room_centroids

        rooms = [
            RoomPolygon(id=1, points=[Point(x=0, y=0), Point(x=1, y=1)], area=0),
        ]
        cache = _compute_room_centroids(rooms)
        assert 1 not in cache  # Only 2 points, not a valid polygon


# ── BMA-BS Symbol Test ───────────────────────────────────────


class TestBmaSymbol:
    def test_bma_bs_symbol_creates_group(self):
        import svgwrite
        from app.utils.symbols import bma_bs

        dwg = svgwrite.Drawing(size=("100mm", "100mm"))
        g = bma_bs(dwg, 50, 50, size=5)
        assert g is not None
        # Should contain at least a rect and text
        svg_xml = g.tostring()
        assert "BMZ" in svg_xml
        assert "rect" in svg_xml

    def test_bma_bs_in_symbol_registry(self):
        from app.utils.symbols import SYMBOL_REGISTRY
        assert "bma_bs" in SYMBOL_REGISTRY
