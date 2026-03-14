"""Tests for OpenRouter API client — core retry logic and API calls."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.openrouter import (
    _request_with_retry,
    call_vision_api,
    call_text_api,
    _RETRYABLE_STATUS_CODES,
)


class TestRequestWithRetry:
    @pytest.mark.asyncio
    async def test_successful_request(self):
        mock_response = MagicMock(status_code=200)
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        result = await _request_with_retry(mock_client, url="https://api.test/v1/chat", headers={}, json_body={})
        assert result == mock_response
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_non_retryable_client_error(self):
        """401 should fail immediately without retry."""
        mock_response = MagicMock(status_code=401)
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
        )
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        with pytest.raises(httpx.HTTPStatusError):
            await _request_with_retry(mock_client, url="https://api.test/v1/chat", headers={}, json_body={})
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_retryable_429_then_success(self):
        success = MagicMock(status_code=200)
        success.raise_for_status = MagicMock()
        rate_limit = MagicMock(status_code=429, headers={})
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[rate_limit, success])
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await _request_with_retry(mock_client, url="https://api.test/v1/chat", headers={}, json_body={}, max_retries=2)
        assert result == success
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_then_success(self):
        success = MagicMock(status_code=200)
        success.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[httpx.TimeoutException("Timeout"), success])
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await _request_with_retry(mock_client, url="https://api.test/v1/chat", headers={}, json_body={}, max_retries=2)
        assert result == success

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_raises(self):
        error_response = MagicMock(status_code=503, headers={})
        error_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Unavailable", request=MagicMock(), response=error_response)
        )
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=error_response)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.HTTPStatusError):
                await _request_with_retry(mock_client, url="https://api.test/v1/chat", headers={}, json_body={}, max_retries=2)
        assert mock_client.post.call_count == 3


class TestCallVisionApi:
    @pytest.mark.asyncio
    async def test_successful_vision_call(self, tmp_path: Path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")
        mock_response = MagicMock(status_code=200)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Result"}}]}
        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            result = await call_vision_api(img, "Classify rooms")
        assert result == "Result"

    @pytest.mark.asyncio
    async def test_malformed_response_raises(self, tmp_path: Path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")
        mock_response = MagicMock(status_code=200)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"error": "bad"}
        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ValueError, match="Unexpected API response"):
                await call_vision_api(img, "Classify")


class TestCallTextApi:
    @pytest.mark.asyncio
    async def test_successful_text_call(self):
        mock_response = MagicMock(status_code=200)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Hello"}}]}
        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            result = await call_text_api("Test")
        assert result == "Hello"


class TestRetryConstants:
    def test_retryable_status_codes(self):
        for code in [429, 500, 502, 503, 504]:
            assert code in _RETRYABLE_STATUS_CODES
        assert 400 not in _RETRYABLE_STATUS_CODES
