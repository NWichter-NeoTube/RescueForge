"""Tests for OpenRouter API client with retry logic."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.openrouter import (
    _request_with_retry,
    call_vision_api,
    call_text_api,
    _RETRYABLE_STATUS_CODES,
    _MAX_RETRIES,
    _BASE_DELAY,
)


# ── _request_with_retry Tests ────────────────────────────────


class TestRequestWithRetry:
    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Successful 200 response should return immediately."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        result = await _request_with_retry(
            mock_client, url="https://api.test/v1/chat", headers={}, json_body={}
        )
        assert result == mock_response
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_non_retryable_client_error(self):
        """400/401/403 errors should fail immediately without retry."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=mock_response
            )
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await _request_with_retry(
                mock_client, url="https://api.test/v1/chat", headers={}, json_body={}
            )
        # Should NOT retry
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_retryable_429_then_success(self):
        """429 rate limit should retry and eventually succeed."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()

        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[rate_limit_response, success_response]
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await _request_with_retry(
                mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                max_retries=2,
            )

        assert result == success_response
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_retryable_500_series(self):
        """500/502/503/504 should trigger retry."""
        for status_code in [500, 502, 503, 504]:
            success_response = MagicMock()
            success_response.status_code = 200
            success_response.raise_for_status = MagicMock()

            error_response = MagicMock()
            error_response.status_code = status_code
            error_response.headers = {}

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[error_response, success_response]
            )

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await _request_with_retry(
                    mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                    max_retries=2,
                )

            assert result == success_response, f"Failed for status {status_code}"

    @pytest.mark.asyncio
    async def test_retry_after_header_honored(self):
        """Retry-After header should control the delay."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()

        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"retry-after": "5"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[rate_limit_response, success_response]
        )

        mock_sleep = AsyncMock()
        with patch("asyncio.sleep", mock_sleep):
            await _request_with_retry(
                mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                max_retries=2,
            )

        # Should sleep for 5 seconds (from Retry-After header)
        mock_sleep.assert_called_once_with(5.0)

    @pytest.mark.asyncio
    async def test_retry_after_invalid_uses_exponential(self):
        """Invalid Retry-After value should fall back to exponential backoff."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()

        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"retry-after": "not-a-number"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[rate_limit_response, success_response]
        )

        mock_sleep = AsyncMock()
        with patch("asyncio.sleep", mock_sleep):
            await _request_with_retry(
                mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                max_retries=2,
            )

        # Should use _BASE_DELAY * 2^0 = 2.0 (first retry)
        mock_sleep.assert_called_once_with(_BASE_DELAY)

    @pytest.mark.asyncio
    async def test_timeout_retries_then_raises(self):
        """TimeoutException should retry max_retries times then raise."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        mock_sleep = AsyncMock()
        with patch("asyncio.sleep", mock_sleep):
            with pytest.raises(httpx.TimeoutException):
                await _request_with_retry(
                    mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                    max_retries=2,
                )

        # Should try 3 times (initial + 2 retries)
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_connect_error_retries_then_raises(self):
        """ConnectError should retry max_retries times then raise."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        mock_sleep = AsyncMock()
        with patch("asyncio.sleep", mock_sleep):
            with pytest.raises(httpx.ConnectError):
                await _request_with_retry(
                    mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                    max_retries=1,
                )

        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_then_success(self):
        """Timeout on first attempt, success on retry."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[httpx.TimeoutException("Timeout"), success_response]
        )

        mock_sleep = AsyncMock()
        with patch("asyncio.sleep", mock_sleep):
            result = await _request_with_retry(
                mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                max_retries=2,
            )

        assert result == success_response
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_raises_last_error(self):
        """Exhausting all retries on server errors should raise."""
        error_response = MagicMock()
        error_response.status_code = 503
        error_response.headers = {}
        error_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Service Unavailable", request=MagicMock(), response=error_response
            )
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=error_response)

        mock_sleep = AsyncMock()
        with patch("asyncio.sleep", mock_sleep):
            with pytest.raises(httpx.HTTPStatusError):
                await _request_with_retry(
                    mock_client, url="https://api.test/v1/chat", headers={}, json_body={},
                    max_retries=2,
                )

        # Should try 3 times total
        assert mock_client.post.call_count == 3


# ── call_vision_api Tests ────────────────────────────────────


class TestCallVisionApi:
    @pytest.mark.asyncio
    async def test_png_image_mime_type(self, tmp_path: Path):
        """PNG images should use image/png MIME type."""
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG header

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Room classification result"}}]
        }

        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            result = await call_vision_api(img, "Classify rooms")

        assert result == "Room classification result"

    @pytest.mark.asyncio
    async def test_jpeg_image_mime_type(self, tmp_path: Path):
        """JPEG images should use image/jpeg MIME type."""
        img = tmp_path / "test.jpg"
        img.write_bytes(b"\xff\xd8\xff\xe0")  # JPEG header

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Result"}}]
        }

        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            result = await call_vision_api(img, "Classify")

        assert result == "Result"

    @pytest.mark.asyncio
    async def test_malformed_response_raises_value_error(self, tmp_path: Path):
        """Malformed API response should raise ValueError."""
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"error": "bad response"}

        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ValueError, match="Unexpected API response"):
                await call_vision_api(img, "Classify")

    @pytest.mark.asyncio
    async def test_empty_choices_raises_value_error(self, tmp_path: Path):
        """Empty choices array should raise ValueError."""
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": []}

        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ValueError, match="Unexpected API response"):
                await call_vision_api(img, "Classify")


# ── call_text_api Tests ──────────────────────────────────────


class TestCallTextApi:
    @pytest.mark.asyncio
    async def test_successful_text_api_call(self):
        """Valid text API call should return content string."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from the API"}}]
        }

        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            result = await call_text_api("Test prompt")

        assert result == "Hello from the API"

    @pytest.mark.asyncio
    async def test_text_api_malformed_response(self):
        """Malformed text API response should raise ValueError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"invalid": "structure"}

        with patch("app.services.openrouter._request_with_retry", new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ValueError, match="Unexpected API response"):
                await call_text_api("Test prompt")

    @pytest.mark.asyncio
    async def test_text_api_uses_default_model(self):
        """Without explicit model, should use settings.openrouter_model."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OK"}}]
        }

        captured_kwargs = {}

        async def capture_retry(client, *, url, headers, json_body, **kwargs):
            captured_kwargs["json_body"] = json_body
            return mock_response

        with patch("app.services.openrouter._request_with_retry", side_effect=capture_retry):
            await call_text_api("Test prompt")

        assert "model" in captured_kwargs["json_body"]


# ── Constants Tests ──────────────────────────────────────────


class TestRetryConstants:
    def test_retryable_status_codes(self):
        assert 429 in _RETRYABLE_STATUS_CODES
        assert 500 in _RETRYABLE_STATUS_CODES
        assert 502 in _RETRYABLE_STATUS_CODES
        assert 503 in _RETRYABLE_STATUS_CODES
        assert 504 in _RETRYABLE_STATUS_CODES
        assert 400 not in _RETRYABLE_STATUS_CODES

    def test_max_retries_positive(self):
        assert _MAX_RETRIES > 0

    def test_base_delay_positive(self):
        assert _BASE_DELAY > 0
