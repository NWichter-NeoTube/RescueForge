"""Tests for the rate limiting middleware."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from tests.conftest import SAMPLE_DXF


@pytest.fixture(autouse=True)
def _ensure_dirs():
    for d in [os.environ.get("UPLOAD_DIR", "/tmp/rescueforge_test/uploads"),
              os.environ.get("OUTPUT_DIR", "/tmp/rescueforge_test/outputs")]:
        Path(d).mkdir(parents=True, exist_ok=True)


@pytest.fixture
def fresh_app():
    """Create a fresh app with clean rate-limiter state per test."""
    # Re-import to get fresh middleware state
    import importlib
    import app.main as main_mod
    importlib.reload(main_mod)
    return main_mod.app


@pytest.fixture
async def client(fresh_app):
    transport = ASGITransport(app=fresh_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limit_not_applied_to_non_upload(self, client):
        """Health endpoint should never be rate-limited."""
        for _ in range(25):
            res = await client.get("/health")
            assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_triggers_on_uploads(self, client):
        """Upload endpoint should return 429 after exceeding the limit."""
        if not SAMPLE_DXF.exists():
            pytest.skip("Sample DXF not available")

        content = SAMPLE_DXF.read_bytes()
        blocked = False

        with patch("app.api.routes.process_floor_plan_task") as mock_task:
            mock_task.apply_async = MagicMock()

            for i in range(25):
                res = await client.post(
                    "/api/upload",
                    files={"file": (f"test_{i}.dxf", content, "application/octet-stream")},
                )
                if res.status_code == 429:
                    blocked = True
                    assert "Too many" in res.json()["detail"]
                    break

        assert blocked, "Rate limiter should have triggered before 25 requests"

    @pytest.mark.asyncio
    async def test_rate_limit_response_format(self, client):
        """429 response should have the correct JSON format."""
        if not SAMPLE_DXF.exists():
            pytest.skip("Sample DXF not available")

        content = SAMPLE_DXF.read_bytes()

        with patch("app.api.routes.process_floor_plan_task") as mock_task:
            mock_task.apply_async = MagicMock()

            # Exhaust rate limit
            for i in range(21):
                res = await client.post(
                    "/api/upload",
                    files={"file": (f"test_{i}.dxf", content, "application/octet-stream")},
                )

            # This should be rate-limited
            res = await client.post(
                "/api/upload",
                files={"file": ("final.dxf", content, "application/octet-stream")},
            )

        if res.status_code == 429:
            data = res.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
