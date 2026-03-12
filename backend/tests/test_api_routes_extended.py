"""Extended tests for API routes — covers download, original-svg, error, and room editor endpoints."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def job_id():
    return "12345678-1234-1234-1234-123456789abc"


# ── Download Endpoint Tests (with actual files) ─────────────


class TestDownloadWithFiles:
    def test_svg_download_success(self, client, job_id, tmp_path):
        """Should download SVG when file exists."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        svg = output_dir / "test_orientierungsplan.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')

        res = client.get(f"/api/jobs/{job_id}/svg")
        assert res.status_code == 200
        assert "svg" in res.headers["content-type"]

        # Cleanup
        svg.unlink()
        output_dir.rmdir()

    def test_pdf_download_success(self, client, job_id, tmp_path):
        """Should download PDF when file exists."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf = output_dir / "test_orientierungsplan.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake content")

        res = client.get(f"/api/jobs/{job_id}/pdf")
        assert res.status_code == 200

        pdf.unlink()
        output_dir.rmdir()

    def test_cover_sheet_download_success(self, client, job_id):
        """Should download cover sheet when file exists."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        cover = output_dir / "test_deckblatt.svg"
        cover.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')

        res = client.get(f"/api/jobs/{job_id}/cover-sheet")
        assert res.status_code == 200

        cover.unlink()
        output_dir.rmdir()

    def test_situation_plan_download_success(self, client, job_id):
        """Should download situation plan when file exists."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        sit = output_dir / "test_situationsplan.svg"
        sit.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')

        res = client.get(f"/api/jobs/{job_id}/situation-plan")
        assert res.status_code == 200

        sit.unlink()
        output_dir.rmdir()


# ── Error Endpoint Tests ─────────────────────────────────────


class TestErrorEndpoint:
    def test_error_not_found(self, client, job_id):
        """Should return 404 when no error.json exists."""
        res = client.get(f"/api/jobs/{job_id}/error")
        assert res.status_code == 404

    def test_error_found(self, client, job_id):
        """Should return error details when error.json exists."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        error_data = {
            "job_id": job_id,
            "error": "DXF parsing failed",
            "error_type": "DXFParseError",
            "step": "parsing",
            "elapsed_ms": 150.5,
        }
        error_file = output_dir / "error.json"
        error_file.write_text(json.dumps(error_data))

        res = client.get(f"/api/jobs/{job_id}/error")
        assert res.status_code == 200
        data = res.json()
        assert data["error_type"] == "DXFParseError"
        assert data["step"] == "parsing"

        error_file.unlink()
        output_dir.rmdir()

    def test_error_invalid_uuid(self, client):
        """Non-UUID job_id should be rejected."""
        res = client.get("/api/jobs/not-a-uuid/error")
        assert res.status_code == 400


# ── Metrics Endpoint with Data ───────────────────────────────


class TestMetricsWithData:
    def test_metrics_found(self, client, job_id):
        """Should return metrics when metrics.json exists."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        metrics = {
            "dxf_parsing_ms": 450.2,
            "room_detection_ms": 300.0,
            "total_pipeline_ms": 12000.0,
        }
        metrics_file = output_dir / "metrics.json"
        metrics_file.write_text(json.dumps(metrics))

        res = client.get(f"/api/jobs/{job_id}/metrics")
        assert res.status_code == 200
        data = res.json()
        assert data["dxf_parsing_ms"] == 450.2

        metrics_file.unlink()
        output_dir.rmdir()


# ── Floor Plan Data Endpoint ─────────────────────────────────


class TestFloorPlanData:
    def test_data_found(self, client, job_id):
        """Should return floor plan data when file exists."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "filename": "test.dxf",
            "walls": [],
            "rooms": [],
            "bounds": [0, 0, 100, 100],
        }
        data_file = output_dir / "floor_plan_data.json"
        data_file.write_text(json.dumps(data))

        res = client.get(f"/api/jobs/{job_id}/data")
        assert res.status_code == 200
        result = res.json()
        assert result["filename"] == "test.dxf"

        data_file.unlink()
        output_dir.rmdir()


# ── Room Editor Extended Tests ───────────────────────────────


class TestRoomEditorValidation:
    def test_invalid_room_type_rejected(self, client, job_id):
        """Invalid room_type should return 400 with list of valid types."""
        from app.config import settings

        output_dir = Path(settings.output_dir) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        data_file = output_dir / "floor_plan_data.json"
        data_file.write_text(json.dumps({
            "filename": "test.dxf",
            "walls": [],
            "rooms": [{"id": 1, "room_type": "office", "label": "Buero", "points": [], "area": 100}],
            "bounds": [0, 0, 100, 100],
        }))

        res = client.put(
            f"/api/jobs/{job_id}/rooms",
            json=[{"id": 1, "room_type": "invalid_type"}],
        )
        assert res.status_code == 400
        assert "Invalid room_type" in res.json()["detail"]
        assert "Valid types" in res.json()["detail"]

        data_file.unlink()
        output_dir.rmdir()

    def test_too_many_room_updates(self, client, job_id):
        """More than 1000 room updates should be rejected."""
        rooms = [{"id": i, "room_type": "office"} for i in range(1001)]
        res = client.put(f"/api/jobs/{job_id}/rooms", json=rooms)
        assert res.status_code == 400
        assert "Too many" in res.json()["detail"]


# ── Original SVG Endpoint Tests ──────────────────────────────


class TestOriginalSvg:
    def test_original_svg_no_upload(self, client, job_id):
        """Should return 404 when upload directory doesn't exist."""
        res = client.get(f"/api/jobs/{job_id}/original-svg")
        assert res.status_code == 404

    def test_original_svg_no_dxf_file(self, client, job_id):
        """Should return 404 when no DXF file found in upload dir."""
        from app.config import settings

        upload_dir = Path(settings.upload_dir) / job_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        res = client.get(f"/api/jobs/{job_id}/original-svg")
        assert res.status_code == 404

        upload_dir.rmdir()

    def test_original_svg_with_sample_dxf(self, client, job_id):
        """Should generate SVG preview from sample DXF."""
        from app.config import settings
        from tests.conftest import SAMPLE_DXF

        if not SAMPLE_DXF.exists():
            pytest.skip("Sample DXF not found")

        upload_dir = Path(settings.upload_dir) / job_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Copy sample DXF to upload dir
        import shutil
        dxf_copy = upload_dir / "test.dxf"
        shutil.copy2(SAMPLE_DXF, dxf_copy)

        res = client.get(f"/api/jobs/{job_id}/original-svg")
        assert res.status_code == 200
        assert "svg" in res.headers["content-type"]
        assert "<svg" in res.text

        # Cleanup
        dxf_copy.unlink()
        upload_dir.rmdir()


# ── Job Status State Tests ───────────────────────────────────


class TestJobStatusStates:
    def test_pending_state_with_directory(self, client, job_id):
        """PENDING state with existing directory should return queued status."""
        from app.config import settings
        from app.worker import job_store

        upload_dir = Path(settings.upload_dir) / job_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        job_store.create(job_id)

        res = client.get(f"/api/jobs/{job_id}")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "pending"

        upload_dir.rmdir()
        job_store.remove(job_id)

    def test_success_state(self, client, job_id):
        """SUCCESS state should return completed status with URLs."""
        from app.worker import job_store

        job_store.create(job_id)
        job_store.set_success(job_id, {
            "svg_url": f"/api/jobs/{job_id}/svg",
            "pdf_url": f"/api/jobs/{job_id}/pdf",
        })

        res = client.get(f"/api/jobs/{job_id}")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["progress"] == 1.0
        assert "svg" in data.get("result_svg", "")

        job_store.remove(job_id)

    def test_failure_state(self, client, job_id):
        """FAILURE state should return failed status with error message."""
        from app.worker import job_store

        job_store.create(job_id)
        job_store.set_failure(job_id, "DXF parse error")

        res = client.get(f"/api/jobs/{job_id}")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "failed"
        assert "DXF parse error" in data["message"]

        job_store.remove(job_id)

    def test_progress_state(self, client, job_id):
        """PROGRESS state should return current step and progress."""
        from app.worker import job_store

        job_store.create(job_id)
        job_store.update_progress(job_id, "classifying", 0.6)

        res = client.get(f"/api/jobs/{job_id}")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "classifying"
        assert data["progress"] == 0.6

        job_store.remove(job_id)

    def test_progress_state_unknown_step(self, client, job_id):
        """Unknown step in PROGRESS state should default to parsing."""
        from app.worker import job_store

        job_store.create(job_id)
        job_store.update_progress(job_id, "nonexistent_step", 0.5)

        res = client.get(f"/api/jobs/{job_id}")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "parsing"  # fallback

        job_store.remove(job_id)
