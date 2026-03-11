"""OpenRouter API client for vision-based room classification.

Includes exponential backoff retry for transient errors (429, 500, 502, 503, 504).
"""

import base64
import logging
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Transient HTTP status codes worth retrying
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Retry configuration
_MAX_RETRIES = 3
_BASE_DELAY = 2.0  # seconds — doubled each retry: 2s, 4s, 8s


async def _request_with_retry(
    client: httpx.AsyncClient,
    *,
    url: str,
    headers: dict,
    json_body: dict,
    max_retries: int = _MAX_RETRIES,
) -> httpx.Response:
    """POST with exponential backoff retry for transient errors.

    Retries on 429 (rate limit), 500, 502, 503, 504 and on network errors.
    Non-retryable errors (400, 401, 403, 422) are raised immediately.
    """
    import asyncio

    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = await client.post(url, headers=headers, json=json_body)

            # Non-retryable client errors — fail fast
            if response.status_code < 500 and response.status_code != 429:
                response.raise_for_status()
                return response

            # Retryable error
            if response.status_code in _RETRYABLE_STATUS_CODES:
                if attempt < max_retries:
                    # Check for Retry-After header (rate limiting)
                    retry_after = response.headers.get("retry-after")
                    if retry_after:
                        try:
                            delay = min(float(retry_after), 30.0)
                        except ValueError:
                            delay = _BASE_DELAY * (2 ** attempt)
                    else:
                        delay = _BASE_DELAY * (2 ** attempt)

                    logger.warning(
                        "OpenRouter API returned %d (attempt %d/%d), retrying in %.1fs",
                        response.status_code, attempt + 1, max_retries + 1, delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                # Last attempt — raise the error
                response.raise_for_status()

            return response

        except httpx.TimeoutException as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = _BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "OpenRouter API timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1, max_retries + 1, delay,
                )
                await asyncio.sleep(delay)
                continue
            raise

        except httpx.ConnectError as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = _BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "OpenRouter API connection error (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, max_retries + 1, delay, exc,
                )
                await asyncio.sleep(delay)
                continue
            raise

    # Should not reach here, but just in case
    if last_exc:
        raise last_exc
    raise httpx.HTTPError("Max retries exhausted")


async def call_vision_api(
    image_path: str | Path,
    prompt: str,
    model: str | None = None,
) -> str:
    """Send an image to OpenRouter vision API and get a text response.

    Includes retry with exponential backoff for transient errors.

    Args:
        image_path: Path to the image file (PNG/JPG).
        prompt: Text prompt describing what to analyze.
        model: Model to use. Defaults to settings.openrouter_vision_model.

    Returns:
        Text response from the model.

    Raises:
        httpx.HTTPStatusError: For non-retryable API errors (401, 403, etc.)
        httpx.TimeoutException: If all retries are exhausted on timeout.
        ValueError: If the API response is malformed.
    """
    model = model or settings.openrouter_vision_model
    image_path = Path(image_path)

    # Read and base64 encode image
    image_bytes = image_path.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    suffix = image_path.suffix.lower()
    mime_type = "image/png" if suffix == ".png" else "image/jpeg"

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rescueforge.app",
        "X-Title": "RescueForge",
    }
    json_body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await _request_with_retry(
            client,
            url=f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json_body=json_body,
        )
        data = response.json()

    # Validate response structure
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.error("Malformed API response: %s", data)
        raise ValueError(f"Unexpected API response structure: {exc}") from exc


async def call_text_api(prompt: str, model: str | None = None) -> str:
    """Send a text prompt to OpenRouter API.

    Includes retry with exponential backoff for transient errors.

    Args:
        prompt: Text prompt.
        model: Model to use. Defaults to settings.openrouter_model.

    Returns:
        Text response from the model.

    Raises:
        httpx.HTTPStatusError: For non-retryable API errors.
        httpx.TimeoutException: If all retries are exhausted on timeout.
        ValueError: If the API response is malformed.
    """
    model = model or settings.openrouter_model

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rescueforge.app",
        "X-Title": "RescueForge",
    }
    json_body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await _request_with_retry(
            client,
            url=f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json_body=json_body,
        )
        data = response.json()

    # Validate response structure
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.error("Malformed API response: %s", data)
        raise ValueError(f"Unexpected API response structure: {exc}") from exc
