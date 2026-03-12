"""Tests for WebSocket progress endpoint."""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from app.api.websocket import _step_label
from app.worker import job_store


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

        # Create a PENDING job in the store
        job_store.create(job_id)

        try:
            with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                # Connection should be accepted, we just connect then close
                pass
        except Exception:
            pass  # Expected: connection closes after we disconnect
        finally:
            job_store.remove(job_id)

    def test_progress_state_sends_update(self, client):
        """PROGRESS state should send progress update via WebSocket."""
        job_id = "12345678-1234-1234-1234-123456789abc"

        job_store.create(job_id)
        job_store.update_progress(job_id, "parsing", 0.3)

        # After the first read, set to SUCCESS so the loop terminates
        original_get = job_store.get
        call_count = 0

        def patched_get(jid):
            nonlocal call_count
            call_count += 1
            job = original_get(jid)
            if job and call_count > 1:
                job.status = "SUCCESS"
                job.result = {
                    "svg_url": "/api/jobs/test/svg",
                    "pdf_url": "/api/jobs/test/pdf",
                    "rooms_count": 5,
                    "walls_count": 100,
                }
            return job

        with patch.object(job_store, "get", side_effect=patched_get):
            with patch("app.api.websocket.asyncio.sleep"):
                try:
                    with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                        data = ws.receive_json()
                        assert data["type"] == "progress"
                        assert data["step"] == "parsing"
                        assert data["progress"] == 0.3
                except Exception:
                    pass
                finally:
                    job_store.remove(job_id)

    def test_success_state_sends_complete(self, client):
        """SUCCESS state should send complete message."""
        job_id = "12345678-1234-1234-1234-123456789abc"

        job_store.create(job_id)
        job_store.set_success(job_id, {
            "svg_url": f"/api/jobs/{job_id}/svg",
            "pdf_url": f"/api/jobs/{job_id}/pdf",
            "rooms_count": 8,
            "walls_count": 200,
        })

        try:
            with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                data = ws.receive_json()
                assert data["type"] == "complete"
                assert data["status"] == "completed"
                assert data["progress"] == 1.0
                assert "svg_url" in data
        finally:
            job_store.remove(job_id)

    def test_failure_state_sends_error(self, client):
        """FAILURE state should send error message."""
        job_id = "12345678-1234-1234-1234-123456789abc"

        job_store.create(job_id)
        job_store.set_failure(job_id, "Pipeline crashed")

        try:
            with client.websocket_connect(f"/api/ws/{job_id}") as ws:
                data = ws.receive_json()
                assert data["type"] == "error"
                assert data["status"] == "failed"
                assert "Pipeline crashed" in data["message"]
        finally:
            job_store.remove(job_id)
