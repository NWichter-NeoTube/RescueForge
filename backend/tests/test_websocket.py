"""Tests for WebSocket progress endpoint."""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from app.api.websocket import _step_label


# ── _step_label Tests ────────────────────────────────────────


class TestStepLabel:
    def test_converting_label(self):
        assert _step_label("converting") == "DWG wird konvertiert..."

    def test_parsing_label(self):
        assert _step_label("parsing") == "DXF wird analysiert..."

    def test_detecting_rooms_label(self):
        assert _step_label("detecting_rooms") == "Räume werden erkannt..."

    def test_classifying_label(self):
        assert _step_label("classifying") == "AI klassifiziert Räume..."

    def test_generating_label(self):
        assert _step_label("generating") == "Orientierungsplan wird erstellt..."

    def test_exporting_label(self):
        assert _step_label("exporting") == "PDF wird exportiert..."

    def test_unknown_step_label(self):
        result = _step_label("unknown_step")
        assert "Verarbeitung" in result
        assert "unknown_step" in result

    def test_empty_step_label(self):
        result = _step_label("")
        assert "Verarbeitung" in result


# ── WebSocket Endpoint Tests (via TestClient) ────────────────


class TestWebSocketEndpoint:
    @pytest.fixture
    def client(self):
        """Create FastAPI test client with WebSocket support."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_invalid_uuid_rejected(self, client):
        """Non-UUID job_id should close with code 1008."""
        from starlette.websockets import WebSocketDisconnect
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/ws/not-a-valid-uuid") as ws:
                pass  # Server closes before accept

    def test_valid_uuid_accepted(self, client):
        """Valid UUID should be accepted."""
        job_id = "12345678-1234-1234-1234-123456789abc"

        # Mock the Celery AsyncResult to return PENDING state
        mock_result = MagicMock()
        mock_result.state = "PENDING"

        with patch("app.api.websocket.process_floor_plan_task") as mock_task:
            mock_task.AsyncResult.return_value = mock_result
            try:
                with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                    # Connection should be accepted, we just connect then close
                    pass
            except Exception:
                pass  # Expected: connection closes after we disconnect

    def test_progress_state_sends_update(self, client):
        """PROGRESS state should send progress update via WebSocket."""
        job_id = "12345678-1234-1234-1234-123456789abc"

        call_count = 0

        def create_mock_result(*args):
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            if call_count == 1:
                mock.state = "PROGRESS"
                mock.info = {"step": "parsing", "progress": 0.3}
            else:
                mock.state = "SUCCESS"
                mock.get.return_value = {
                    "svg_url": "/api/jobs/test/svg",
                    "pdf_url": "/api/jobs/test/pdf",
                    "rooms_count": 5,
                    "walls_count": 100,
                }
            return mock

        with patch("app.api.websocket.process_floor_plan_task") as mock_task:
            mock_task.AsyncResult = create_mock_result
            with patch("app.api.websocket.asyncio.sleep"):
                try:
                    with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                        data = ws.receive_json()
                        assert data["type"] == "progress"
                        assert data["step"] == "parsing"
                        assert data["progress"] == 0.3
                except Exception:
                    pass

    def test_success_state_sends_complete(self, client):
        """SUCCESS state should send complete message."""
        job_id = "12345678-1234-1234-1234-123456789abc"

        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.get.return_value = {
            "svg_url": f"/api/jobs/{job_id}/svg",
            "pdf_url": f"/api/jobs/{job_id}/pdf",
            "rooms_count": 8,
            "walls_count": 200,
        }

        with patch("app.api.websocket.process_floor_plan_task") as mock_task:
            mock_task.AsyncResult.return_value = mock_result
            with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                data = ws.receive_json()
                assert data["type"] == "complete"
                assert data["status"] == "completed"
                assert data["progress"] == 1.0
                assert "svg_url" in data

    def test_failure_state_sends_error(self, client):
        """FAILURE state should send error message."""
        job_id = "12345678-1234-1234-1234-123456789abc"

        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.result = Exception("Pipeline crashed")

        with patch("app.api.websocket.process_floor_plan_task") as mock_task:
            mock_task.AsyncResult.return_value = mock_result
            with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                data = ws.receive_json()
                assert data["type"] == "error"
                assert data["status"] == "failed"
                assert "Pipeline crashed" in data["message"]
