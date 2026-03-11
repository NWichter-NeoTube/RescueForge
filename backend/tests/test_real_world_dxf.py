"""Real-world DXF/DWG file processing tests.

Tests the full pipeline (parse → detect rooms → generate SVG) against
real architectural floor plans downloaded from various sources.

Files are expected in testdata/ — tests skip gracefully if files are missing.
DWG files require LibreDWG (odafileconverter or libredwg) for conversion;
they are skipped if conversion tools are not available.
"""

import logging
from pathlib import Path

import pytest

from app.models.schemas import FloorPlanData, RoomPolygon
from app.pipeline.plan_generator import generate_svg

logger = logging.getLogger(__name__)


# ── Test data paths ───────────────────────────────────────────

_local_testdata = Path(__file__).parent.parent.parent / "testdata"
_docker_testdata = Path("/app/testdata")
TESTDATA_DIR = _docker_testdata if _docker_testdata.exists() else _local_testdata


# Real DXF files (can be parsed directly)
REAL_DXF_FILES = {
    "floorplan_sample": TESTDATA_DIR / "floorplan_sample.dxf",
    "basement_plan": TESTDATA_DIR / "basement_plan.dxf",
}

# Real DWG files (need conversion to DXF first — skip if converter not available)
REAL_DWG_FILES = {
    "apartment_highrise": TESTDATA_DIR / "apartment_highrise_61.dwg",
    "apartment_typical": TESTDATA_DIR / "apartment_typical_119.dwg",
    "dormitory": TESTDATA_DIR / "dormitory_104.dwg",
    "family_home": TESTDATA_DIR / "family_home_360m2_433.dwg",
    "hospital": TESTDATA_DIR / "hospital_65000m2_55.dwg",
    "kindergarten": TESTDATA_DIR / "kindergarten_31.dwg",
    "office_12story": TESTDATA_DIR / "office_12story_64.dwg",
    "office_3story": TESTDATA_DIR / "office_3story_900m2_84.dwg",
}


# ── Helpers ──────────────────────────────────────────────────

def _parse_dxf(dxf_path: Path) -> tuple[FloorPlanData, list[RoomPolygon]]:
    """Parse a DXF file through the full pipeline (parser → room detector)."""
    from app.pipeline.dxf_parser import parse_dxf
    from app.pipeline.room_detector import detect_rooms

    floor_plan = parse_dxf(str(dxf_path))
    rooms = detect_rooms(floor_plan)
    return floor_plan, rooms


def _has_libredwg() -> bool:
    """Check if DWG→DXF conversion is available."""
    import shutil
    return shutil.which("dwg2dxf") is not None or shutil.which("ODAFileConverter") is not None


def _convert_dwg_to_dxf(dwg_path: Path, output_dir: Path) -> Path | None:
    """Convert a DWG file to DXF using available tools."""
    import shutil
    import subprocess

    dxf_path = output_dir / dwg_path.with_suffix(".dxf").name

    if shutil.which("dwg2dxf"):
        try:
            subprocess.run(
                ["dwg2dxf", "-o", str(dxf_path), str(dwg_path)],
                capture_output=True, timeout=60, check=True,
            )
            return dxf_path
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

    return None


# ── DXF tests ────────────────────────────────────────────────

class TestRealDxfParsing:
    """Test parsing of real DXF floor plans."""

    @pytest.fixture(params=list(REAL_DXF_FILES.keys()))
    def dxf_path(self, request) -> Path:
        path = REAL_DXF_FILES[request.param]
        if not path.exists():
            pytest.skip(f"Real DXF file not found: {path.name}")
        return path

    def test_parse_no_crash(self, dxf_path: Path):
        """Real DXF file should parse without raising exceptions."""
        fp, rooms = _parse_dxf(dxf_path)
        assert fp is not None
        assert isinstance(rooms, list)

    def test_walls_detected(self, dxf_path: Path):
        """Real DXF file should have at least some walls."""
        fp, rooms = _parse_dxf(dxf_path)
        assert len(fp.walls) > 0, f"No walls detected in {dxf_path.name}"

    def test_bounds_valid(self, dxf_path: Path):
        """Parsed bounds should be finite and non-degenerate."""
        fp, rooms = _parse_dxf(dxf_path)
        minx, miny, maxx, maxy = fp.bounds
        assert maxx > minx, f"Degenerate X bounds in {dxf_path.name}"
        assert maxy > miny, f"Degenerate Y bounds in {dxf_path.name}"


class TestRealDxfSvgGeneration:
    """Test SVG generation from real DXF floor plans."""

    @pytest.fixture(params=list(REAL_DXF_FILES.keys()))
    def dxf_data(self, request, tmp_path: Path) -> tuple[str, FloorPlanData, list[RoomPolygon], Path]:
        path = REAL_DXF_FILES[request.param]
        if not path.exists():
            pytest.skip(f"Real DXF file not found: {path.name}")
        fp, rooms = _parse_dxf(path)
        return request.param, fp, rooms, tmp_path

    def test_svg_generation_no_crash(self, dxf_data):
        """SVG generation should not crash for real DXF data."""
        name, fp, rooms, tmp = dxf_data
        out = tmp / f"{name}.svg"
        result = generate_svg(fp, rooms, out)
        assert result.exists()

    def test_svg_has_content(self, dxf_data):
        """Generated SVG should have substantial content."""
        name, fp, rooms, tmp = dxf_data
        out = tmp / f"{name}.svg"
        generate_svg(fp, rooms, out)
        content = out.read_text(encoding="utf-8")
        assert len(content) > 1000, f"SVG too small for {name}: {len(content)} chars"


class TestRealDxfDiagnostics:
    """Diagnostic tests — log findings about real DXF files for future improvements."""

    @pytest.fixture(params=list(REAL_DXF_FILES.keys()))
    def dxf_path(self, request) -> Path:
        path = REAL_DXF_FILES[request.param]
        if not path.exists():
            pytest.skip(f"Real DXF file not found: {path.name}")
        return path

    def test_log_statistics(self, dxf_path: Path, caplog):
        """Log parsing statistics for real-world DXF files."""
        with caplog.at_level(logging.INFO):
            fp, rooms = _parse_dxf(dxf_path)

        # Log diagnostics (visible with -v flag)
        stats = {
            "file": dxf_path.name,
            "walls": len(fp.walls),
            "doors": len(fp.doors),
            "rooms_detected": len(rooms),
            "rooms_classified": sum(1 for r in rooms if r.room_type.value != "unknown"),
            "unit": fp.unit,
            "scale": fp.scale if hasattr(fp, "scale") else "N/A",
            "fire_walls": len(fp.fire_walls) if fp.fire_walls else 0,
            "fire_doors": len(fp.fire_doors) if fp.fire_doors else 0,
            "windows": len(fp.windows) if fp.windows else 0,
        }
        logger.info("Real-world DXF stats: %s", stats)

        # Minimal assertions — this is diagnostic
        assert fp.walls is not None
        assert rooms is not None
