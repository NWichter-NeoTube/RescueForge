"""API routes for file upload, processing, and download."""

import json
import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.api.tasks import process_floor_plan_task
from app.config import settings
from app.models.schemas import JobStatus, ProcessingStatus, RoomType, UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter()

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Cache duration for completed plan outputs (1 hour)
_CACHE_MAX_AGE = 3600


def _validate_job_id(job_id: str) -> None:
    """Validate job_id is a proper UUID to prevent path traversal."""
    if not _UUID_RE.match(job_id):
        raise HTTPException(400, "Invalid job ID format")


def _cached_file_response(
    path: Path, media_type: str, *, cache: bool = True
) -> FileResponse:
    """Return a FileResponse with proper cache headers."""
    headers = {}
    if cache:
        headers["Cache-Control"] = f"public, max-age={_CACHE_MAX_AGE}"
    return FileResponse(path, media_type=media_type, filename=path.name, headers=headers)


# ── Upload ──────────────────────────────────────────────────


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile, language: str = "en"):
    """Upload a DWG or DXF file for processing."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".dwg", ".dxf"):
        raise HTTPException(400, f"Unsupported file format: {suffix}. Use .dwg or .dxf")

    # Check file size
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"File too large. Maximum: {settings.max_upload_size_mb}MB")

    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    # Sanitise filename to prevent path traversal via crafted names
    safe_name = Path(file.filename).name

    # Save uploaded file
    job_id = str(uuid.uuid4())
    job_dir = Path(settings.upload_dir) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    filepath = job_dir / safe_name
    filepath.write_bytes(content)

    # Queue processing task (use job_id as Celery task_id for easy lookup)
    process_floor_plan_task.apply_async(
        args=[job_id, str(filepath)],
        kwargs={"language": language},
        task_id=job_id,
    )

    logger.info("Upload accepted: %s (job: %s, size: %d bytes)", safe_name, job_id, len(content))

    return UploadResponse(
        job_id=job_id,
        filename=safe_name,
        status=ProcessingStatus.PENDING,
    )


@router.post("/upload/batch")
async def upload_batch(files: list[UploadFile], language: str = "en"):
    """Upload multiple DWG/DXF files (e.g., multiple floors) for batch processing."""
    if not files:
        raise HTTPException(400, "No files provided")
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 files per batch")

    batch_id = str(uuid.uuid4())
    results = []
    skipped = []

    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    for file in files:
        if not file.filename:
            continue
        suffix = Path(file.filename).suffix.lower()
        if suffix not in (".dwg", ".dxf"):
            skipped.append(file.filename)
            continue

        content = await file.read()
        if len(content) == 0:
            skipped.append(file.filename)
            continue
        if len(content) > max_bytes:
            skipped.append(f"{file.filename} (>{settings.max_upload_size_mb}MB)")
            continue

        safe_name = Path(file.filename).name
        job_id = str(uuid.uuid4())
        job_dir = Path(settings.upload_dir) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        filepath = job_dir / safe_name
        filepath.write_bytes(content)

        process_floor_plan_task.apply_async(
            args=[job_id, str(filepath)],
            kwargs={"language": language},
            task_id=job_id,
        )
        results.append({"job_id": job_id, "filename": safe_name})

    if not results:
        raise HTTPException(400, "No valid DWG/DXF files in batch")

    return {
        "batch_id": batch_id,
        "jobs": results,
        "count": len(results),
        "skipped": skipped,
    }


# ── Job Status ──────────────────────────────────────────────


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the processing status of a job."""
    _validate_job_id(job_id)

    # Use Celery result backend (Redis) as single source of truth
    result = process_floor_plan_task.AsyncResult(job_id)
    state = result.state

    if state == "PENDING":
        # Check if job directory exists to distinguish unknown from queued
        job_dir = Path(settings.upload_dir) / job_id
        if not job_dir.exists():
            raise HTTPException(404, "Job not found")
        return JobStatus(
            job_id=job_id,
            status=ProcessingStatus.PENDING,
            progress=0.0,
            message="Waiting for processing to start",
        )
    elif state == "PROGRESS":
        meta = result.info or {}
        step = meta.get("step", "processing")
        progress = meta.get("progress", 0.0)
        try:
            status = ProcessingStatus(step)
        except ValueError:
            status = ProcessingStatus.PARSING
        return JobStatus(
            job_id=job_id,
            status=status,
            progress=progress,
            message=f"Processing: {step}",
        )
    elif state == "SUCCESS":
        task_result = result.get()
        return JobStatus(
            job_id=job_id,
            status=ProcessingStatus.COMPLETED,
            progress=1.0,
            message="Processing complete",
            result_svg=task_result.get("svg_url"),
            result_pdf=task_result.get("pdf_url"),
        )
    elif state == "FAILURE":
        return JobStatus(
            job_id=job_id,
            status=ProcessingStatus.FAILED,
            progress=0.0,
            message=str(result.result),
        )

    return JobStatus(
        job_id=job_id,
        status=ProcessingStatus.PENDING,
        progress=0.0,
        message=f"State: {state}",
    )


# ── Downloads ───────────────────────────────────────────────


@router.get("/jobs/{job_id}/svg")
async def download_svg(job_id: str):
    """Download the generated orientation plan SVG file."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    svg_files = (
        list(output_dir.glob("*_orientation_plan_*.svg"))
        or list(output_dir.glob("*_orientierungsplan_*.svg"))
        or list(output_dir.glob("*_orientierungsplan.svg"))
        or list(output_dir.glob("*.svg"))
    )
    if not svg_files:
        raise HTTPException(404, "SVG output not found. Is the job complete?")
    return _cached_file_response(svg_files[0], "image/svg+xml")


@router.get("/jobs/{job_id}/pdf")
async def download_pdf(job_id: str):
    """Download the generated PDF file."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    pdf_files = list(output_dir.glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(404, "PDF output not found. Is the job complete?")
    return _cached_file_response(pdf_files[0], "application/pdf")


@router.get("/jobs/{job_id}/cover-sheet")
async def download_cover_sheet(job_id: str):
    """Download the cover sheet (Deckblatt) SVG."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    cover_files = (
        list(output_dir.glob("*_cover_sheet_*.svg"))
        or list(output_dir.glob("*_deckblatt_*.svg"))
        or list(output_dir.glob("*_deckblatt.svg"))
    )
    if not cover_files:
        raise HTTPException(404, "Cover sheet not found. Is the job complete?")
    return _cached_file_response(cover_files[0], "image/svg+xml")


@router.get("/jobs/{job_id}/situation-plan")
async def download_situation_plan(job_id: str):
    """Download the situation plan (Situationsplan) SVG."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    sit_files = (
        list(output_dir.glob("*_situation_plan_*.svg"))
        or list(output_dir.glob("*_situationsplan_*.svg"))
        or list(output_dir.glob("*_situationsplan.svg"))
    )
    if not sit_files:
        raise HTTPException(404, "Situation plan not found. Is the job complete?")
    return _cached_file_response(sit_files[0], "image/svg+xml")


@router.get("/jobs/{job_id}/compliance")
async def download_compliance_doc(job_id: str):
    """Download the DIN 14095 compliance report (.docx)."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    docx_files = list(output_dir.glob("*_compliance_report_*.docx")) or list(output_dir.glob("*_konformitaetsbericht_*.docx"))
    if not docx_files:
        raise HTTPException(404, "Compliance report not found. Is the job complete?")
    return _cached_file_response(docx_files[0], "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.get("/jobs/{job_id}/original-svg")
async def get_original_svg(job_id: str):
    """Get a raw SVG preview of the original DXF file (no FKS processing)."""
    _validate_job_id(job_id)
    upload_dir = Path(settings.upload_dir) / job_id
    if not upload_dir.exists():
        raise HTTPException(404, "Upload not found")

    dxf_files = list(upload_dir.glob("*.dxf"))
    if not dxf_files:
        raise HTTPException(404, "No DXF file found for this job")

    try:
        from app.pipeline.dxf_parser import parse_dxf
        floor_plan = parse_dxf(dxf_files[0])
    except Exception as e:
        logger.error("Failed to parse DXF for preview: %s", e)
        raise HTTPException(422, "Failed to parse DXF file for preview") from e

    # Generate a simple SVG preview of the raw geometry
    minx, miny, maxx, maxy = floor_plan.bounds
    plan_w = maxx - minx
    plan_h = maxy - miny
    if plan_w <= 0 or plan_h <= 0:
        raise HTTPException(422, "Floor plan has zero dimensions")

    vw, vh = 800, 600
    scale = min(vw / plan_w, vh / plan_h) * 0.9
    ox = (vw - plan_w * scale) / 2
    oy = (vh - plan_h * scale) / 2

    def tx(x: float) -> float:
        return ox + (x - minx) * scale

    def ty(y: float) -> float:
        return oy + (maxy - y) * scale

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}">']
    lines.append(f'<rect width="{vw}" height="{vh}" fill="white"/>')

    # Walls
    for w in floor_plan.walls:
        lines.append(f'<line x1="{tx(w.start.x):.1f}" y1="{ty(w.start.y):.1f}" x2="{tx(w.end.x):.1f}" y2="{ty(w.end.y):.1f}" stroke="#333" stroke-width="1.5" stroke-linecap="round"/>')

    # Doors
    for d in floor_plan.doors:
        lines.append(f'<circle cx="{tx(d.position.x):.1f}" cy="{ty(d.position.y):.1f}" r="3" fill="#8B4513" opacity="0.7"/>')

    # Stairs
    for s in floor_plan.stairs:
        if len(s.polygon) >= 3:
            pts = " ".join(f"{tx(p.x):.1f},{ty(p.y):.1f}" for p in s.polygon)
            lines.append(f'<polygon points="{pts}" fill="#006400" fill-opacity="0.3" stroke="#006400" stroke-width="0.5"/>')

    lines.append("</svg>")
    svg_str = "\n".join(lines)
    return Response(
        content=svg_str,
        media_type="image/svg+xml",
        headers={"Cache-Control": f"public, max-age={_CACHE_MAX_AGE}"},
    )


# ── Data & Metrics ──────────────────────────────────────────


@router.get("/jobs/{job_id}/data")
async def get_floor_plan_data(job_id: str):
    """Get the parsed floor plan data (rooms, walls, etc.) as JSON."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    data_file = output_dir / "floor_plan_data.json"
    if not data_file.exists():
        raise HTTPException(404, "Floor plan data not found. Is the job complete?")

    return json.loads(data_file.read_text())


@router.get("/jobs/{job_id}/metrics")
async def get_job_metrics(job_id: str):
    """Get pipeline performance metrics for a completed job."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    metrics_file = output_dir / "metrics.json"
    if not metrics_file.exists():
        raise HTTPException(404, "Metrics not found. Is the job complete?")

    return json.loads(metrics_file.read_text())


# ── Room Editor ─────────────────────────────────────────────


@router.put("/jobs/{job_id}/rooms")
async def update_rooms(job_id: str, rooms: list[dict], language: str = "en"):
    """Update room classifications and regenerate the plan."""
    _validate_job_id(job_id)

    if not rooms:
        raise HTTPException(400, "No room updates provided")
    if len(rooms) > 1000:
        raise HTTPException(400, "Too many room updates (max 1000)")

    # Validate each room update has at least an id and valid room_type
    _valid_room_types = {rt.value for rt in RoomType}
    for room in rooms:
        if "id" not in room:
            raise HTTPException(400, "Each room update must have an 'id' field")
        if "room_type" in room and room["room_type"] not in _valid_room_types:
            raise HTTPException(
                400,
                f"Invalid room_type '{room['room_type']}'. "
                f"Valid types: {', '.join(sorted(_valid_room_types))}",
            )

    output_dir = Path(settings.output_dir) / job_id
    data_file = output_dir / "floor_plan_data.json"
    if not data_file.exists():
        raise HTTPException(404, "Floor plan data not found")

    # Load existing data
    floor_plan_dict = json.loads(data_file.read_text())

    # Update room classifications
    room_updates = {r["id"]: r for r in rooms}
    for room in floor_plan_dict.get("rooms", []):
        if room["id"] in room_updates:
            update = room_updates[room["id"]]
            if "room_type" in update:
                room["room_type"] = update["room_type"]
            if "label" in update:
                room["label"] = update["label"]

    # Save updated data
    data_file.write_text(json.dumps(floor_plan_dict, indent=2))

    # Regenerate SVG and PDF with updated classifications
    try:
        from app.models.schemas import FloorPlanData
        from app.pipeline.plan_generator import generate_cover_sheet, generate_situation_plan, generate_svg
        from app.pipeline.pdf_exporter import export_pdf
        from app.utils.translations import t as tr

        floor_plan = FloorPlanData(**floor_plan_dict)

        stem = floor_plan.filename.rsplit(".", 1)[0]
        floor_label = floor_plan.floor_label or "EG"
        lang_suffix = tr("filename.orientation_plan", language)

        # Remove old outputs (keep data files)
        for f in output_dir.glob("*.svg"):
            f.unlink()
        for f in output_dir.glob("*.pdf"):
            f.unlink()

        svg_path = generate_svg(
            floor_plan,
            floor_plan.rooms,
            output_dir / f"{stem}_{lang_suffix}_{language}.svg",
            building_name=stem,
            floor_label=floor_label,
            language=language,
        )
        export_pdf(svg_path, output_dir / f"{stem}_{lang_suffix}_{language}.pdf")

        cover_suffix = tr("filename.cover_sheet", language)
        generate_cover_sheet(
            floor_plan.rooms,
            output_dir / f"{stem}_{cover_suffix}_{language}.svg",
            building_name=stem,
            floors=[floor_label],
            language=language,
            floor_plan=floor_plan,
        )

        sit_suffix = tr("filename.situation_plan", language)
        generate_situation_plan(
            floor_plan,
            floor_plan.rooms,
            output_dir / f"{stem}_{sit_suffix}_{language}.svg",
            building_name=stem,
            language=language,
        )
    except Exception as e:
        logger.error("Plan regeneration failed: %s", e)
        raise HTTPException(500, f"Plan regeneration failed: {e}") from e

    return {"status": "regenerated", "rooms_updated": len(room_updates)}


# ── Error Details ────────────────────────────────────────────


@router.get("/jobs/{job_id}/error")
async def get_job_error(job_id: str):
    """Get detailed error information for a failed job."""
    _validate_job_id(job_id)
    output_dir = Path(settings.output_dir) / job_id
    error_file = output_dir / "error.json"
    if not error_file.exists():
        raise HTTPException(404, "No error details found for this job")
    return json.loads(error_file.read_text())
