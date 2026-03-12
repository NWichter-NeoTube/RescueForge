"""WebSocket endpoint for real-time processing progress updates."""

import asyncio
import logging
import re
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.schemas import ProcessingStatus
from app.worker import job_store

logger = logging.getLogger(__name__)

ws_router = APIRouter()

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)

# Maximum time to keep a WebSocket open (5 minutes)
_MAX_WS_DURATION_S = 300


@ws_router.websocket("/ws/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """Stream processing progress for a job via WebSocket.

    Clients connect after uploading a file and receive real-time updates
    until processing completes or fails.
    """
    # Validate job_id before accepting
    if not _UUID_RE.match(job_id):
        await websocket.close(code=1008, reason="Invalid job ID format")
        return

    await websocket.accept()
    logger.info("WebSocket connected for job %s", job_id)

    start = time.monotonic()

    try:
        prev_step = None
        prev_progress = -1.0

        while True:
            # Guard against zombie connections
            if time.monotonic() - start > _MAX_WS_DURATION_S:
                await websocket.send_json({
                    "type": "error",
                    "message": "Connection timeout – please reconnect",
                })
                break

            job = job_store.get(job_id)

            if job is None:
                await asyncio.sleep(0.5)
                continue

            if job.status == "PROGRESS":
                step = job.step
                progress = job.progress

                # Only send if changed
                if step != prev_step or progress != prev_progress:
                    try:
                        status_enum = ProcessingStatus(step)
                    except ValueError:
                        status_enum = ProcessingStatus.PARSING

                    await websocket.send_json({
                        "type": "progress",
                        "step": step,
                        "status": status_enum.value,
                        "progress": progress,
                        "message": _step_label(step),
                    })
                    prev_step = step
                    prev_progress = progress

            elif job.status == "SUCCESS":
                result = job.result or {}
                await websocket.send_json({
                    "type": "complete",
                    "status": "completed",
                    "progress": 1.0,
                    "svg_url": result.get("svg_url"),
                    "pdf_url": result.get("pdf_url"),
                    "rooms_count": result.get("rooms_count", 0),
                    "walls_count": result.get("walls_count", 0),
                })
                break

            elif job.status == "FAILURE":
                await websocket.send_json({
                    "type": "error",
                    "status": "failed",
                    "progress": 0.0,
                    "message": job.error or "Processing failed",
                })
                break

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for job %s", job_id)
    except Exception as e:
        logger.error("WebSocket error for job %s: %s", job_id, e)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass


def _step_label(step: str, lang: str = "de") -> str:
    """Human-readable label for a pipeline step (supports EN/DE)."""
    _LABELS = {
        "de": {
            "converting": "DWG wird konvertiert...",
            "parsing": "DXF wird analysiert...",
            "detecting_rooms": "Räume werden erkannt...",
            "classifying": "AI klassifiziert Räume...",
            "generating": "Orientierungsplan wird erstellt...",
            "exporting": "PDF wird exportiert...",
            "generating_cover": "Deckblatt wird erstellt...",
            "generating_situation": "Situationsplan wird erstellt...",
            "generating_compliance": "Konformitätsbericht wird erstellt...",
        },
        "en": {
            "converting": "Converting DWG file...",
            "parsing": "Analyzing DXF file...",
            "detecting_rooms": "Detecting rooms...",
            "classifying": "AI classifying rooms...",
            "generating": "Generating orientation plan...",
            "exporting": "Exporting PDF...",
            "generating_cover": "Generating cover sheet...",
            "generating_situation": "Generating situation plan...",
            "generating_compliance": "Generating compliance report...",
        },
    }
    labels = _LABELS.get(lang, _LABELS["en"])
    fallback = f"Verarbeitung: {step}" if lang == "de" else f"Processing: {step}"
    return labels.get(step, fallback)
