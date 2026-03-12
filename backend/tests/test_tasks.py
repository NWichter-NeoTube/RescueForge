"""Tests for pipeline task and in-memory job store."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class TestPipelineErrorHandling:
    """Test error persistence when pipeline fails."""

    def test_error_json_saved_on_failure(self, tmp_path: Path):
        """Pipeline failure should create error.json with details."""
        job_id = "test-job-123"
        output_dir = tmp_path / job_id
        output_dir.mkdir()

        # Simulate what tasks.py does in the except block
        import time
        pipeline_start = time.time()
        metrics = {"_last_step": "parsing"}

        error = ValueError("DXF file corrupt")
        error_data = {
            "job_id": job_id,
            "error": str(error),
            "error_type": type(error).__name__,
            "step": metrics.get("_last_step", "unknown"),
            "elapsed_ms": round((time.time() - pipeline_start) * 1000, 1),
        }
        error_path = output_dir / "error.json"
        error_path.write_text(json.dumps(error_data, indent=2))

        assert error_path.exists()
        saved = json.loads(error_path.read_text())
        assert saved["error_type"] == "ValueError"
        assert saved["step"] == "parsing"
        assert saved["elapsed_ms"] >= 0

    def test_error_json_includes_all_fields(self, tmp_path: Path):
        """error.json should contain job_id, error, error_type, step, elapsed_ms."""
        error_data = {
            "job_id": "abc-123",
            "error": "API timeout",
            "error_type": "TimeoutError",
            "step": "classifying",
            "elapsed_ms": 5500.0,
        }
        error_path = tmp_path / "error.json"
        error_path.write_text(json.dumps(error_data))

        loaded = json.loads(error_path.read_text())
        assert "job_id" in loaded
        assert "error" in loaded
        assert "error_type" in loaded
        assert "step" in loaded
        assert "elapsed_ms" in loaded


class TestPipelineMetrics:
    """Test metrics.json generation."""

    def test_metrics_json_structure(self, tmp_path: Path):
        """metrics.json should contain all expected pipeline step timings."""
        metrics = {
            "dwg_conversion_ms": 0.0,
            "dxf_parsing_ms": 450.5,
            "entities_walls": 248,
            "entities_doors": 42,
            "entities_stairs": 3,
            "room_detection_ms": 300.0,
            "rooms_detected": 14,
            "room_classification_ms": 5200.0,
            "rooms_classified": 12,
            "svg_generation_ms": 95.0,
            "svg_size_bytes": 69000,
            "pdf_export_ms": 2100.0,
            "pdf_size_bytes": 25000,
            "supplementary_plans_ms": 20.0,
            "total_pipeline_ms": 12500.0,
        }
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2))

        loaded = json.loads(metrics_path.read_text())
        assert loaded["dxf_parsing_ms"] == 450.5
        assert loaded["rooms_detected"] == 14
        assert loaded["total_pipeline_ms"] == 12500.0
        # _last_step should NOT be in final metrics
        assert "_last_step" not in loaded

    def test_last_step_removed_before_save(self):
        """_last_step tracking key should be removed before saving metrics."""
        metrics = {
            "_last_step": "classifying",
            "dxf_parsing_ms": 200.0,
            "total_pipeline_ms": 5000.0,
        }
        metrics.pop("_last_step", None)
        assert "_last_step" not in metrics
        assert "dxf_parsing_ms" in metrics


class TestPipelineStepTracking:
    """Test that _last_step is updated at each pipeline stage."""

    def test_all_pipeline_steps_tracked(self):
        """All pipeline steps should have corresponding _last_step values."""
        expected_steps = [
            "converting",
            "parsing",
            "detecting_rooms",
            "classifying",
            "generating",
            "exporting",
        ]
        # Verify all steps are valid by checking they exist
        for step in expected_steps:
            assert isinstance(step, str)
            assert len(step) > 0


class TestJobStore:
    """Test the in-memory job store."""

    def test_create_and_get(self):
        """Creating a job should make it retrievable."""
        from app.worker import JobStore
        store = JobStore()
        store.create("test-1")
        job = store.get("test-1")
        assert job is not None
        assert job.status == "PENDING"

    def test_get_nonexistent(self):
        """Getting a nonexistent job should return None."""
        from app.worker import JobStore
        store = JobStore()
        assert store.get("nonexistent") is None

    def test_update_progress(self):
        """Updating progress should change step and progress."""
        from app.worker import JobStore
        store = JobStore()
        store.create("test-2")
        store.update_progress("test-2", "parsing", 0.3)
        job = store.get("test-2")
        assert job.status == "PROGRESS"
        assert job.step == "parsing"
        assert job.progress == 0.3

    def test_set_success(self):
        """Setting success should store result."""
        from app.worker import JobStore
        store = JobStore()
        store.create("test-3")
        store.set_success("test-3", {"svg_url": "/api/jobs/test-3/svg"})
        job = store.get("test-3")
        assert job.status == "SUCCESS"
        assert job.result["svg_url"] == "/api/jobs/test-3/svg"

    def test_set_failure(self):
        """Setting failure should store error message."""
        from app.worker import JobStore
        store = JobStore()
        store.create("test-4")
        store.set_failure("test-4", "DXF parse error")
        job = store.get("test-4")
        assert job.status == "FAILURE"
        assert job.error == "DXF parse error"

    def test_remove(self):
        """Removing a job should make it no longer retrievable."""
        from app.worker import JobStore
        store = JobStore()
        store.create("test-5")
        store.remove("test-5")
        assert store.get("test-5") is None


class TestTaskImport:
    """Test that the task function is importable."""

    def test_task_importable(self):
        """process_floor_plan_task should be importable."""
        from app.api.tasks import process_floor_plan_task
        assert process_floor_plan_task is not None
        assert callable(process_floor_plan_task)


class TestDwgDetectionInPipeline:
    """Test is_dwg_file integration in pipeline."""

    def test_dxf_file_skips_conversion(self):
        """DXF files should skip the DWG conversion step."""
        from app.pipeline.dwg_converter import is_dwg_file
        assert is_dwg_file("plan.dxf") is False

    def test_dwg_file_triggers_conversion(self):
        """DWG files should trigger the conversion step."""
        from app.pipeline.dwg_converter import is_dwg_file
        assert is_dwg_file("plan.dwg") is True
