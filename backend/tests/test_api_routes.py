"""Tests for API route endpoints."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from tests.conftest import SAMPLE_DXF

# A valid UUID that doesn't correspond to any real job
FAKE_JOB_ID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(autouse=True)
def _ensure_dirs():
    """Ensure upload/output directories exist for tests."""
    for d in [os.environ.get("UPLOAD_DIR", "/tmp/rescueforge_test/uploads"),
              os.environ.get("OUTPUT_DIR", "/tmp/rescueforge_test/outputs")]:
        Path(d).mkdir(parents=True, exist_ok=True)


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    from app.main import app
    return app


@pytest.fixture
async def client(app):
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client):
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["service"] == "rescueforge"
        assert "version" in data


class TestUploadEndpoint:
    @pytest.mark.asyncio
    async def test_upload_dxf(self, client):
        """Test uploading a DXF file."""
        if not SAMPLE_DXF.exists():
            pytest.skip("Sample DXF not available")

        content = SAMPLE_DXF.read_bytes()
        with patch("app.api.routes.process_floor_plan_task") as mock_task:
            mock_task.apply_async = MagicMock()
            res = await client.post(
                "/api/upload",
                files={"file": ("test.dxf", content, "application/octet-stream")},
            )
        assert res.status_code == 200
        data = res.json()
        assert "job_id" in data
        assert data["filename"] == "test.dxf"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_upload_invalid_format(self, client):
        """Test uploading a non-DXF/DWG file."""
        res = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert res.status_code == 400
        assert "Unsupported" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_no_filename(self, client):
        """Test uploading without a filename."""
        res = await client.post(
            "/api/upload",
            files={"file": ("", b"", "application/octet-stream")},
        )
        # FastAPI may return 400 or 422 depending on validation order
        assert res.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client):
        """Test uploading an empty DXF file."""
        res = await client.post(
            "/api/upload",
            files={"file": ("empty.dxf", b"", "application/octet-stream")},
        )
        assert res.status_code == 400
        assert "Empty" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_filename_sanitized(self, client):
        """Test that path traversal in filename is sanitized."""
        if not SAMPLE_DXF.exists():
            pytest.skip("Sample DXF not available")

        content = SAMPLE_DXF.read_bytes()
        with patch("app.api.routes.process_floor_plan_task") as mock_task:
            mock_task.apply_async = MagicMock()
            res = await client.post(
                "/api/upload",
                files={"file": ("../../etc/evil.dxf", content, "application/octet-stream")},
            )
        assert res.status_code == 200
        data = res.json()
        # Filename should be sanitized — no path components
        assert "/" not in data["filename"]
        assert "\\" not in data["filename"]


class TestBatchUploadEndpoint:
    @pytest.mark.asyncio
    async def test_batch_upload(self, client):
        """Test batch uploading multiple DXF files."""
        if not SAMPLE_DXF.exists():
            pytest.skip("Sample DXF not available")

        content = SAMPLE_DXF.read_bytes()
        with patch("app.api.routes.process_floor_plan_task") as mock_task:
            mock_task.apply_async = MagicMock()
            res = await client.post(
                "/api/upload/batch",
                files=[
                    ("files", ("floor1.dxf", content, "application/octet-stream")),
                    ("files", ("floor2.dxf", content, "application/octet-stream")),
                ],
            )
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 2
        assert len(data["jobs"]) == 2
        assert "batch_id" in data

    @pytest.mark.asyncio
    async def test_batch_upload_empty(self, client):
        """Test batch upload with no valid files."""
        res = await client.post(
            "/api/upload/batch",
            files=[
                ("files", ("test.txt", b"hello", "text/plain")),
            ],
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_batch_upload_skips_invalid(self, client):
        """Test that batch upload skips invalid files and reports them."""
        if not SAMPLE_DXF.exists():
            pytest.skip("Sample DXF not available")

        content = SAMPLE_DXF.read_bytes()
        with patch("app.api.routes.process_floor_plan_task") as mock_task:
            mock_task.apply_async = MagicMock()
            res = await client.post(
                "/api/upload/batch",
                files=[
                    ("files", ("valid.dxf", content, "application/octet-stream")),
                    ("files", ("readme.txt", b"hello", "text/plain")),
                    ("files", ("empty.dxf", b"", "application/octet-stream")),
                ],
            )
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 1
        assert len(data["skipped"]) == 2


class TestJobStatusEndpoint:
    @pytest.mark.asyncio
    async def test_job_status_unknown(self, client):
        """Test getting status of an unknown job (valid UUID, no directory)."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_job_status_invalid_uuid(self, client):
        """Test that non-UUID job IDs are rejected."""
        res = await client.get("/api/jobs/nonexistent-id")
        assert res.status_code == 400
        assert "Invalid job ID" in res.json()["detail"]


class TestMetricsEndpoint:
    @pytest.mark.asyncio
    async def test_metrics_not_found(self, client):
        """Test getting metrics for a non-existent job."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}/metrics")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_metrics_invalid_uuid(self, client):
        """Test that non-UUID job IDs are rejected."""
        res = await client.get("/api/jobs/not-a-valid-uuid/metrics")
        assert res.status_code == 400


class TestDownloadEndpoints:
    @pytest.mark.asyncio
    async def test_svg_not_found(self, client):
        """Test downloading SVG for a non-existent job."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}/svg")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_pdf_not_found(self, client):
        """Test downloading PDF for a non-existent job."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}/pdf")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_cover_sheet_not_found(self, client):
        """Test downloading cover sheet for a non-existent job."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}/cover-sheet")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_situation_plan_not_found(self, client):
        """Test downloading situation plan for a non-existent job."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}/situation-plan")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_original_svg_not_found(self, client):
        """Test downloading original SVG for a non-existent job."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}/original-svg")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_download_invalid_uuid(self, client):
        """Test that all download endpoints reject non-UUID IDs."""
        for path in ["/svg", "/pdf", "/cover-sheet", "/situation-plan", "/data"]:
            res = await client.get(f"/api/jobs/bad-id{path}")
            assert res.status_code == 400, f"Expected 400 for {path}"


class TestRoomEditorEndpoint:
    @pytest.mark.asyncio
    async def test_rooms_not_found(self, client):
        """Test updating rooms for a non-existent job."""
        res = await client.put(
            f"/api/jobs/{FAKE_JOB_ID}/rooms",
            json=[{"id": 1, "room_type": "office"}],
        )
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_rooms_empty_update(self, client):
        """Test sending an empty rooms update."""
        res = await client.put(
            f"/api/jobs/{FAKE_JOB_ID}/rooms",
            json=[],
        )
        assert res.status_code == 400
        assert "No room" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_rooms_missing_id(self, client):
        """Test sending a room update without an id field."""
        res = await client.put(
            f"/api/jobs/{FAKE_JOB_ID}/rooms",
            json=[{"room_type": "office"}],
        )
        assert res.status_code == 400
        assert "id" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_rooms_invalid_uuid(self, client):
        """Test that rooms endpoint rejects non-UUID IDs."""
        res = await client.put(
            "/api/jobs/not-valid/rooms",
            json=[{"id": 1}],
        )
        assert res.status_code == 400


class TestFloorPlanDataEndpoint:
    @pytest.mark.asyncio
    async def test_data_not_found(self, client):
        """Test getting floor plan data for a non-existent job."""
        res = await client.get(f"/api/jobs/{FAKE_JOB_ID}/data")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_data_invalid_uuid(self, client):
        """Test that data endpoint rejects non-UUID IDs."""
        res = await client.get("/api/jobs/traversal-attempt/data")
        assert res.status_code == 400
