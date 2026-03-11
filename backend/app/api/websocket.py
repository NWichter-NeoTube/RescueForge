"""WebSocket endpoint for real-time processing progress updates."""

import asyncio
import logging
import re
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.tasks import process_floor_plan_task
from app.models.schemas import ProcessingStatus

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
        prev_state = None
        prev_progress = -1.0

        while True:
            # Guard against zombie connections
            if time.monotonic() - start > _MAX_WS_DURATION_S:
                await websocket.send_json({
                    "type": "error",
                    "message": "Connection timeout – please reconnect",
                })
                break

            result = process_floor_plan_task.AsyncResult(job_id)
            state = result.state

            if state == "PROGRESS":
                meta = result.info or {}
                step = meta.get("step", "processing")
                progress = meta.get("progress", 0.0)

                # Only send if changed
                if state != prev_state or progress != prev_progress:
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
                    prev_state = state
                    prev_progress = progress

            elif state == "SUCCESS":
                task_result = result.get()
                await websocket.send_json({
                    "type": "complete",
                    "status": "completed",
                    "progress": 1.0,
                    "svg_url": task_result.get("svg_url"),
                    "pdf_url": task_result.get("pdf_url"),
                    "rooms_count": task_result.get("rooms_count", 0),
                    "walls_count": task_result.get("walls_count", 0),
                })
                break

            elif state == "FAILURE":
                await websocket.send_json({
                    "type": "error",
                    "status": "failed",
                    "progress": 0.0,
                    "message": str(result.result),
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
