"""Tests for room classifier with mocked Vision API."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import FloorPlanData, Point, RoomPolygon, RoomType, WallSegment
from app.pipeline.room_classifier import classify_rooms, _heuristic_classify


@pytest.fixture
def simple_floor_plan() -> FloorPlanData:
    """Create a simple floor plan with walls."""
    return FloorPlanData(
        filename="test.dxf",
        walls=[
            WallSegment(start=Point(x=0, y=0), end=Point(x=10000, y=0)),
            WallSegment(start=Point(x=10000, y=0), end=Point(x=10000, y=8000)),
            WallSegment(start=Point(x=10000, y=8000), end=Point(x=0, y=8000)),
            WallSegment(start=Point(x=0, y=8000), end=Point(x=0, y=0)),
        ],
        doors=[],
        stairs=[],
        rooms=[],
        bounds=(0, 0, 10000, 8000),
    )


@pytest.fixture
def sample_rooms() -> list[RoomPolygon]:
    """Create sample rooms for classification."""
    return [
        RoomPolygon(
            id=1,
            points=[Point(x=0, y=0), Point(x=5000, y=0), Point(x=5000, y=4000), Point(x=0, y=4000)],
            area=20_000_000,
            room_type=RoomType.UNKNOWN,
        ),
        RoomPolygon(
            id=2,
            points=[Point(x=5000, y=0), Point(x=10000, y=0), Point(x=10000, y=1000), Point(x=5000, y=1000)],
            area=5_000_000,
            room_type=RoomType.UNKNOWN,
        ),
        RoomPolygon(
            id=3,
            points=[Point(x=0, y=4000), Point(x=1500, y=4000), Point(x=1500, y=8000), Point(x=0, y=8000)],
            area=6_000_000,
            room_type=RoomType.UNKNOWN,
        ),
    ]


class TestHeuristicClassification:
    def test_corridor_detection(self, simple_floor_plan):
        """Long narrow rooms should be classified as corridors."""
        rooms = [
            RoomPolygon(
                id=1,
                points=[Point(x=0, y=0), Point(x=20000, y=0), Point(x=20000, y=2000), Point(x=0, y=2000)],
                area=40_000_000,
                room_type=RoomType.UNKNOWN,
            ),
            RoomPolygon(
                id=2,
                points=[Point(x=0, y=3000), Point(x=5000, y=3000), Point(x=5000, y=7000), Point(x=0, y=7000)],
                area=20_000_000,
                room_type=RoomType.UNKNOWN,
            ),
        ]
        result = _heuristic_classify(rooms, simple_floor_plan)
        assert result[0].room_type == RoomType.CORRIDOR

    def test_small_room_bathroom(self, simple_floor_plan):
        """Very small rooms should be classified as bathrooms."""
        rooms = [
            RoomPolygon(
                id=1,
                points=[Point(x=0, y=0), Point(x=1000, y=0), Point(x=1000, y=1000), Point(x=0, y=1000)],
                area=1_000_000,
                room_type=RoomType.UNKNOWN,
            ),
            RoomPolygon(
                id=2,
                points=[Point(x=0, y=2000), Point(x=5000, y=2000), Point(x=5000, y=6000), Point(x=0, y=6000)],
                area=20_000_000,
                room_type=RoomType.UNKNOWN,
            ),
        ]
        result = _heuristic_classify(rooms, simple_floor_plan)
        assert result[0].room_type == RoomType.BATHROOM

    def test_large_room_lobby(self, simple_floor_plan):
        """Very large rooms (>2x median) should be classified as lobbies."""
        # 3 rooms: areas 5M, 10M, 200M. Median=10M, 200M > 2*10M => LOBBY
        rooms = [
            RoomPolygon(
                id=1,
                points=[Point(x=0, y=0), Point(x=1000, y=0), Point(x=1000, y=5000), Point(x=0, y=5000)],
                area=5_000_000,
                room_type=RoomType.UNKNOWN,
            ),
            RoomPolygon(
                id=2,
                points=[Point(x=2000, y=0), Point(x=4000, y=0), Point(x=4000, y=5000), Point(x=2000, y=5000)],
                area=10_000_000,
                room_type=RoomType.UNKNOWN,
            ),
            RoomPolygon(
                id=3,
                points=[Point(x=0, y=6000), Point(x=20000, y=6000), Point(x=20000, y=16000), Point(x=0, y=16000)],
                area=200_000_000,
                room_type=RoomType.UNKNOWN,
            ),
        ]
        result = _heuristic_classify(rooms, simple_floor_plan)
        assert result[2].room_type == RoomType.LOBBY

    def test_empty_rooms(self, simple_floor_plan):
        """Empty room list should be handled gracefully."""
        result = _heuristic_classify([], simple_floor_plan)
        assert result == []

    def test_labels_in_default_language(self, simple_floor_plan):
        """Heuristic labels should be in default language (English)."""
        rooms = [
            RoomPolygon(
                id=1,
                points=[Point(x=0, y=0), Point(x=5000, y=0), Point(x=5000, y=4000), Point(x=0, y=4000)],
                area=20_000_000,
                room_type=RoomType.UNKNOWN,
            ),
        ]
        result = _heuristic_classify(rooms, simple_floor_plan)
        assert result[0].label in ("Office", "Corridor", "Lobby/Reception", "Bathroom", "Storage")

    def test_labels_in_german(self, simple_floor_plan):
        """Heuristic labels should be in German when language='de'."""
        rooms = [
            RoomPolygon(
                id=1,
                points=[Point(x=0, y=0), Point(x=5000, y=0), Point(x=5000, y=4000), Point(x=0, y=4000)],
                area=20_000_000,
                room_type=RoomType.UNKNOWN,
            ),
        ]
        result = _heuristic_classify(rooms, simple_floor_plan, language="de")
        assert result[0].label in ("Büro", "Korridor", "Halle/Empfang", "WC/Nassraum", "Lager")


class TestVisionAPIClassification:
    @pytest.mark.asyncio
    async def test_classify_with_mock_api(self, simple_floor_plan, sample_rooms, tmp_path):
        """Test classification with mocked Vision API response."""
        mock_response = json.dumps([
            {"id": 1, "type": "office", "label": "Büro 101"},
            {"id": 2, "type": "corridor", "label": "Korridor"},
            {"id": 3, "type": "stairwell", "label": "Treppenhaus"},
        ])

        with patch("app.pipeline.room_classifier.call_vision_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response
            result = await classify_rooms(simple_floor_plan, sample_rooms, tmp_path)

        assert len(result) == 3
        assert result[0].room_type == RoomType.OFFICE
        assert result[0].label == "Büro 101"
        assert result[1].room_type == RoomType.CORRIDOR
        assert result[2].room_type == RoomType.STAIRWELL

    @pytest.mark.asyncio
    async def test_classify_with_markdown_response(self, simple_floor_plan, sample_rooms, tmp_path):
        """Test parsing Vision API response wrapped in markdown code blocks."""
        mock_response = '```json\n[{"id": 1, "type": "office", "label": "Büro"}]\n```'

        with patch("app.pipeline.room_classifier.call_vision_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response
            result = await classify_rooms(simple_floor_plan, sample_rooms, tmp_path)

        assert result[0].room_type == RoomType.OFFICE

    @pytest.mark.asyncio
    async def test_classify_fallback_on_api_error(self, simple_floor_plan, sample_rooms, tmp_path):
        """Test fallback to heuristics when Vision API fails."""
        with patch("app.pipeline.room_classifier.call_vision_api", new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API Error")
            result = await classify_rooms(simple_floor_plan, sample_rooms, tmp_path)

        # Should still classify all rooms via heuristics
        assert len(result) == 3
        for r in result:
            assert r.room_type != RoomType.UNKNOWN or r.label != ""

    @pytest.mark.asyncio
    async def test_classify_empty_rooms(self, simple_floor_plan, tmp_path):
        """Test with empty room list."""
        result = await classify_rooms(simple_floor_plan, [], tmp_path)
        assert result == []
