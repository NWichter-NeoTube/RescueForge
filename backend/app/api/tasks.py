"""Celery tasks for background floor plan processing."""

import json
import logging
import time
from pathlib import Path

from app.config import settings
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="process_floor_plan",
    time_limit=600,           # Hard kill after 10 minutes
    soft_time_limit=550,      # Raise SoftTimeLimitExceeded after ~9 min
    acks_late=True,           # Re-queue if worker crashes
    reject_on_worker_lost=True,
)
def process_floor_plan_task(self, job_id: str, filepath: str, language: str = "en"):
    """Process a floor plan file through the full pipeline.

    Steps:
    1. Convert DWG to DXF (if needed)
    2. Parse DXF entities
    3. Detect room polygons
    4. Classify rooms via AI
    5. Generate SVG orientation plan
    6. Export to PDF
    """
    import asyncio

    from app.pipeline.dwg_converter import convert_dwg_to_dxf, is_dwg_file
    from app.pipeline.dxf_parser import parse_dxf
    from app.pipeline.pdf_exporter import export_pdf
    from app.pipeline.plan_generator import generate_cover_sheet, generate_situation_plan, generate_svg
    from app.pipeline.room_classifier import classify_rooms
    from app.pipeline.room_detector import detect_rooms
    from app.utils.translations import t as tr

    output_dir = Path(settings.output_dir) / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics: dict[str, float] = {}
    pipeline_start = time.time()

    try:
        # Step 1: DWG conversion
        metrics["_last_step"] = "converting"
        self.update_state(state="PROGRESS", meta={"step": "converting", "progress": 0.1})
        t0 = time.time()
        if is_dwg_file(filepath):
            logger.info("[%s] Converting DWG to DXF...", job_id)
            filepath = str(convert_dwg_to_dxf(filepath, output_dir))
        metrics["dwg_conversion_ms"] = round((time.time() - t0) * 1000, 1)

        # Step 2: Parse DXF
        metrics["_last_step"] = "parsing"
        self.update_state(state="PROGRESS", meta={"step": "parsing", "progress": 0.2})
        logger.info("[%s] Parsing DXF...", job_id)
        t0 = time.time()
        floor_plan = parse_dxf(filepath)
        metrics["dxf_parsing_ms"] = round((time.time() - t0) * 1000, 1)
        metrics["entities_walls"] = len(floor_plan.walls)
        metrics["entities_doors"] = len(floor_plan.doors)
        metrics["entities_stairs"] = len(floor_plan.stairs)

        # Step 3: Detect rooms
        metrics["_last_step"] = "detecting_rooms"
        self.update_state(state="PROGRESS", meta={"step": "detecting_rooms", "progress": 0.4})
        logger.info("[%s] Detecting rooms...", job_id)
        t0 = time.time()
        rooms = detect_rooms(floor_plan)
        metrics["room_detection_ms"] = round((time.time() - t0) * 1000, 1)
        metrics["rooms_detected"] = len(rooms)

        # Step 4: Classify rooms
        metrics["_last_step"] = "classifying"
        self.update_state(state="PROGRESS", meta={"step": "classifying", "progress": 0.6})
        logger.info("[%s] Classifying %d rooms...", job_id, len(rooms))

        t0 = time.time()
        loop = asyncio.new_event_loop()
        try:
            rooms = loop.run_until_complete(classify_rooms(floor_plan, rooms, output_dir))
        finally:
            loop.close()
        metrics["room_classification_ms"] = round((time.time() - t0) * 1000, 1)
        metrics["rooms_classified"] = sum(1 for r in rooms if r.room_type.value != "unknown")

        floor_plan.rooms = rooms

        # Step 5: Generate SVG
        metrics["_last_step"] = "generating"
        self.update_state(state="PROGRESS", meta={"step": "generating", "progress": 0.8})
        logger.info("[%s] Generating SVG...", job_id)
        t0 = time.time()
        suffix = tr("filename.orientation_plan", language)
        svg_name = f"{Path(filepath).stem}_{suffix}_{language}.svg"
        svg_path = generate_svg(
            floor_plan,
            rooms,
            output_dir / svg_name,
            building_name=Path(filepath).stem,
            floor_label=floor_plan.floor_label or "EG",
            language=language,
        )
        metrics["svg_generation_ms"] = round((time.time() - t0) * 1000, 1)
        metrics["svg_size_bytes"] = svg_path.stat().st_size

        # Step 6: Export PDF
        metrics["_last_step"] = "exporting"
        self.update_state(state="PROGRESS", meta={"step": "exporting", "progress": 0.9})
        logger.info("[%s] Exporting PDF...", job_id)
        t0 = time.time()
        pdf_name = f"{Path(filepath).stem}_{suffix}_{language}.pdf"
        pdf_path = export_pdf(svg_path, output_dir / pdf_name)
        metrics["pdf_export_ms"] = round((time.time() - t0) * 1000, 1)
        metrics["pdf_size_bytes"] = pdf_path.stat().st_size

        # Step 7: Generate cover sheet + situation plan (FKS requirement)
        t0 = time.time()
        stem = Path(filepath).stem
        floor_label = floor_plan.floor_label or "EG"
        cover_suffix = tr("filename.cover_sheet", language)
        sit_suffix = tr("filename.situation_plan", language)
        try:
            generate_cover_sheet(
                rooms,
                output_dir / f"{stem}_{cover_suffix}_{language}.svg",
                building_name=stem,
                address="",
                floors=[floor_label],
                language=language,
                floor_plan=floor_plan,
            )
            generate_situation_plan(
                floor_plan,
                rooms,
                output_dir / f"{stem}_{sit_suffix}_{language}.svg",
                building_name=stem,
                language=language,
            )
            logger.info("[%s] Cover sheet + situation plan generated", job_id)
        except Exception as e:
            logger.warning("[%s] Optional plan generation failed: %s", job_id, e)
        metrics["supplementary_plans_ms"] = round((time.time() - t0) * 1000, 1)

        # Step 8: Generate compliance document
        try:
            from app.pipeline.compliance_doc import generate_compliance_doc
            comp_suffix = tr("filename.compliance_report", language)
            generate_compliance_doc(
                floor_plan,
                rooms,
                output_dir / f"{stem}_{comp_suffix}_{language}.docx",
                language=language,
            )
            logger.info("[%s] Compliance document generated", job_id)
        except Exception as e:
            logger.warning("[%s] Compliance document generation failed: %s", job_id, e)

        metrics["total_pipeline_ms"] = round((time.time() - pipeline_start) * 1000, 1)
        metrics.pop("_last_step", None)  # Remove internal tracking key

        # Save floor plan data as JSON
        json_path = output_dir / "floor_plan_data.json"
        json_path.write_text(floor_plan.model_dump_json(indent=2))

        # Save metrics
        metrics_path = output_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2))

        logger.info("[%s] Processing complete! Metrics: %s", job_id, metrics)

        return {
            "job_id": job_id,
            "svg_url": f"/api/jobs/{job_id}/svg",
            "pdf_url": f"/api/jobs/{job_id}/pdf",
            "rooms_count": len(rooms),
            "walls_count": len(floor_plan.walls),
            "metrics": metrics,
        }

    except Exception as e:
        logger.error("[%s] Processing failed: %s", job_id, e, exc_info=True)
        # Persist error details so the /error endpoint can serve them
        try:
            error_data = {
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "step": metrics.get("_last_step", "unknown"),
                "elapsed_ms": round((time.time() - pipeline_start) * 1000, 1),
            }
            error_path = output_dir / "error.json"
            error_path.write_text(json.dumps(error_data, indent=2))
        except Exception:
            pass  # Don't mask the original error
        raise
