"""Tests for error handling and retry logic."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

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

try:
    from app.pipeline.pdf_exporter import PDFExportError, export_pdf
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False


class TestDXFParseError:
    def test_nonexistent_file_raises(self):
        from app.pipeline.dxf_parser import parse_dxf
        with pytest.raises(DXFParseError, match="not found"):
            parse_dxf("/nonexistent/file.dxf")

    def test_empty_file_raises(self, tmp_path: Path):
        from app.pipeline.dxf_parser import parse_dxf
        empty = tmp_path / "empty.dxf"
        empty.write_text("")
        with pytest.raises(DXFParseError, match="empty"):
            parse_dxf(str(empty))

    def test_corrupt_file_raises(self, tmp_path: Path):
        from app.pipeline.dxf_parser import parse_dxf
        corrupt = tmp_path / "corrupt.dxf"
        corrupt.write_text("NOT A VALID DXF FILE\nGARBAGE DATA")
        with pytest.raises((DXFParseError, Exception)):
            parse_dxf(str(corrupt))


@pytest.mark.skipif(not HAS_WEASYPRINT, reason="WeasyPrint not available")
class TestPDFExportError:
    def test_missing_svg_raises(self, tmp_path: Path):
        with pytest.raises(PDFExportError, match="not found"):
            export_pdf(tmp_path / "missing.svg", tmp_path / "out.pdf")

    def test_valid_svg_exports(self, tmp_path: Path):
        svg = tmp_path / "test.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<rect width="100" height="100" fill="red"/></svg>'
        )
        pdf = tmp_path / "test.pdf"
        result = export_pdf(svg, pdf)
        assert result.exists() and result.stat().st_size > 0


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
        RoomPolygon(id=1, points=[Point(x=0, y=0), Point(x=5000, y=0), Point(x=5000, y=4000), Point(x=0, y=4000)], area=20_000_000),
        RoomPolygon(id=2, points=[Point(x=5000, y=0), Point(x=10000, y=0), Point(x=10000, y=4000), Point(x=5000, y=4000)], area=20_000_000),
    ]


class TestClassifyRoomsRetry:
    @pytest.mark.asyncio
    async def test_retries_on_api_failure(self, simple_plan, test_rooms, tmp_path):
        call_count = 0

        async def flaky_api(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Transient error")
            return json.dumps([
                {"id": 1, "type": "office", "label": "Buero"},
                {"id": 2, "type": "corridor", "label": "Korridor"},
            ])

        with patch("app.pipeline.room_classifier.call_vision_api", side_effect=flaky_api):
            result = await classify_rooms(simple_plan, test_rooms, tmp_path)

        assert call_count >= 2
        assert result[0].room_type == RoomType.OFFICE

    @pytest.mark.asyncio
    async def test_falls_back_to_heuristic_after_all_retries(self, simple_plan, test_rooms, tmp_path):
        with patch(
            "app.pipeline.room_classifier.call_vision_api",
            new_callable=AsyncMock,
            side_effect=Exception("Persistent error"),
        ):
            result = await classify_rooms(simple_plan, test_rooms, tmp_path)
        assert len(result) == 2
        for r in result:
            assert r.room_type != RoomType.UNKNOWN
