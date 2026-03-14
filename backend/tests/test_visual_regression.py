"""Visual regression tests for SVG plan output.

Generates SVG plans from deterministic test data and compares structural
fingerprints against stored baselines.

Usage:
    uv run pytest tests/test_visual_regression.py -v
    uv run pytest tests/test_visual_regression.py -v --update-baselines
"""

import json
import re
from pathlib import Path

import pytest

from app.models.schemas import (
    DoorInfo,
    FloorPlanData,
    Point,
    RoomPolygon,
    RoomType,
    WallSegment,
)
from app.pipeline.plan_generator import (
    generate_cover_sheet,
    generate_situation_plan,
    generate_svg,
)


# ── Paths ────────────────────────────────────────────────────
_local_baselines = Path(__file__).parent.parent.parent / "testdata" / "baselines"
_docker_baselines = Path("/app/testdata/baselines")
BASELINES_DIR = _docker_baselines if _docker_baselines.exists() else _local_baselines


# ── Deterministic test data ──────────────────────────────────

def _make_regression_floor_plan() -> tuple[FloorPlanData, list[RoomPolygon]]:
    """Build a rich, deterministic floor plan for regression testing."""
    walls = [
        WallSegment(start=Point(x=0, y=0), end=Point(x=400, y=0)),
        WallSegment(start=Point(x=400, y=0), end=Point(x=400, y=200)),
        WallSegment(start=Point(x=400, y=200), end=Point(x=0, y=200)),
        WallSegment(start=Point(x=0, y=200), end=Point(x=0, y=0)),
        WallSegment(start=Point(x=100, y=0), end=Point(x=100, y=200)),
        WallSegment(start=Point(x=200, y=0), end=Point(x=200, y=200)),
        WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=200)),
        WallSegment(start=Point(x=200, y=100), end=Point(x=300, y=100)),
    ]

    fire_walls = [WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=200))]
    doors = [
        DoorInfo(position=Point(x=100, y=50), width=30),
        DoorInfo(position=Point(x=200, y=50), width=30),
        DoorInfo(position=Point(x=300, y=50), width=30),
    ]
    fire_doors = [DoorInfo(position=Point(x=300, y=50), width=30, fire_rating="T30")]
    windows = [
        WallSegment(start=Point(x=30, y=0), end=Point(x=70, y=0)),
        WallSegment(start=Point(x=130, y=0), end=Point(x=170, y=0)),
    ]

    fp = FloorPlanData(
        filename="regression_test.dxf",
        walls=walls, fire_walls=fire_walls, doors=doors,
        fire_doors=fire_doors, windows=windows,
        bounds=(0, 0, 400, 200), unit="mm",
    )

    rooms = [
        RoomPolygon(id=1, points=[Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=200), Point(x=0, y=200)], room_type=RoomType.CORRIDOR, label="Corridor", area=20000),
        RoomPolygon(id=2, points=[Point(x=100, y=0), Point(x=200, y=0), Point(x=200, y=200), Point(x=100, y=200)], room_type=RoomType.OFFICE, label="Office 1", area=20000),
        RoomPolygon(id=3, points=[Point(x=200, y=0), Point(x=300, y=0), Point(x=300, y=100), Point(x=200, y=100)], room_type=RoomType.BATHROOM, label="WC", area=10000),
        RoomPolygon(id=4, points=[Point(x=200, y=100), Point(x=300, y=100), Point(x=300, y=200), Point(x=200, y=200)], room_type=RoomType.TECHNICAL, label="Technical", area=10000),
        RoomPolygon(id=5, points=[Point(x=300, y=0), Point(x=400, y=0), Point(x=400, y=200), Point(x=300, y=200)], room_type=RoomType.STAIRWELL, label="Stairwell", area=20000),
    ]

    return fp, rooms


# ── SVG fingerprinting ───────────────────────────────────────

def _fingerprint_svg(svg_text: str) -> dict:
    """Extract a structural fingerprint from an SVG string."""
    fp: dict = {}
    for tag in ("rect", "polygon", "text", "line", "path", "circle", "g", "polyline"):
        fp[f"count_{tag}"] = len(re.findall(rf"<{tag}[\s/>]", svg_text))
    fp["group_ids"] = sorted(set(re.findall(r'id="([^"]+)"', svg_text)))
    texts = sorted(t.strip() for t in re.findall(r">([^<]+)<", svg_text) if t.strip())
    fp["text_content"] = texts
    fp["colors"] = sorted(set(re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,8})"', svg_text)))
    vb = re.search(r'viewBox="([^"]+)"', svg_text)
    fp["viewBox"] = vb.group(1) if vb else ""
    width = re.search(r'width="([^"]+)"', svg_text)
    fp["width"] = width.group(1) if width else ""
    height = re.search(r'height="([^"]+)"', svg_text)
    fp["height"] = height.group(1) if height else ""
    fp["total_chars"] = len(svg_text)
    return fp


def _compare_fingerprints(baseline: dict, current: dict, name: str, tolerance_chars: float = 0.15) -> list[str]:
    """Compare two fingerprints and return a list of differences."""
    diffs: list[str] = []
    for key in baseline:
        if key.startswith("count_"):
            if baseline[key] != current.get(key, 0):
                diffs.append(f"{name}: {key} changed {baseline[key]} → {current.get(key, 0)}")
    if baseline.get("group_ids") != current.get("group_ids"):
        added = set(current.get("group_ids", [])) - set(baseline.get("group_ids", []))
        removed = set(baseline.get("group_ids", [])) - set(current.get("group_ids", []))
        if added: diffs.append(f"{name}: new group IDs {added}")
        if removed: diffs.append(f"{name}: removed group IDs {removed}")
    if baseline.get("colors") != current.get("colors"):
        added = set(current.get("colors", [])) - set(baseline.get("colors", []))
        removed = set(baseline.get("colors", [])) - set(current.get("colors", []))
        if added: diffs.append(f"{name}: new colors {added}")
        if removed: diffs.append(f"{name}: removed colors {removed}")
    b_texts = set(baseline.get("text_content", []))
    c_texts = set(current.get("text_content", []))
    missing = {t for t in b_texts - c_texts if len(t) > 2 and not t.replace(".", "").isdigit()}
    added = {t for t in c_texts - b_texts if len(t) > 2 and not t.replace(".", "").isdigit()}
    if missing: diffs.append(f"{name}: missing text entries (sample): {list(missing)[:5]}")
    if added: diffs.append(f"{name}: new text entries (sample): {list(added)[:5]}")
    for dim in ("viewBox", "width", "height"):
        if baseline.get(dim) != current.get(dim):
            diffs.append(f"{name}: {dim} changed '{baseline.get(dim)}' → '{current.get(dim)}'")
    b_size = baseline.get("total_chars", 0)
    c_size = current.get("total_chars", 0)
    if b_size > 0:
        rel_diff = abs(c_size - b_size) / b_size
        if rel_diff > tolerance_chars:
            diffs.append(f"{name}: size changed by {rel_diff:.0%} ({b_size} → {c_size} chars)")
    return diffs


# ── Reduced scenario set (EN floor plan + DE cover sheet) ────

SCENARIOS = {
    "floor_plan_en_a3": {
        "generator": "svg",
        "kwargs": {"paper_format": "A3", "language": "en", "building_name": "Regression Test", "floor_label": "GF"},
    },
    "cover_sheet_de": {
        "generator": "cover_sheet",
        "kwargs": {"language": "de", "building_name": "Regressions-Deckblatt", "floors": ["EG", "1.OG", "2.OG"]},
    },
    "situation_plan_en": {
        "generator": "situation",
        "kwargs": {"language": "en", "building_name": "Regression Situation"},
    },
}


def _generate_scenario(scenario: dict, fp: FloorPlanData, rooms: list[RoomPolygon], out_dir: Path) -> str:
    gen = scenario["generator"]
    kw = scenario["kwargs"]
    out_file = out_dir / f"{gen}.svg"
    if gen == "svg":
        generate_svg(fp, rooms, out_file, **kw)
    elif gen == "cover_sheet":
        generate_cover_sheet(rooms, out_file, floor_plan=fp, **kw)
    elif gen == "situation":
        generate_situation_plan(fp, rooms, out_file, **kw)
    return out_file.read_text(encoding="utf-8")


class TestVisualRegression:
    """Compare generated SVGs against stored structural baselines."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_output: Path, request):
        self.tmp = tmp_output
        self.update = request.config.getoption("--update-baselines", default=False)
        self.fp, self.rooms = _make_regression_floor_plan()

    @pytest.mark.parametrize("name", list(SCENARIOS.keys()))
    def test_scenario_matches_baseline(self, name: str):
        scenario = SCENARIOS[name]
        svg_text = _generate_scenario(scenario, self.fp, self.rooms, self.tmp)
        current = _fingerprint_svg(svg_text)
        baseline_path = BASELINES_DIR / f"{name}.json"
        if self.update or not baseline_path.exists():
            BASELINES_DIR.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
            pytest.skip(f"Baseline {'updated' if self.update else 'created'}: {baseline_path.name}")
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        diffs = _compare_fingerprints(baseline, current, name)
        if diffs:
            debug_path = self.tmp / f"{name}_current.json"
            debug_path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
            pytest.fail(
                f"Visual regression in '{name}':\n" + "\n".join(f"  - {d}" for d in diffs)
                + f"\n\nRun with --update-baselines to accept changes."
            )

    def test_floor_plan_svg_is_substantial(self):
        svg_text = _generate_scenario(SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp)
        assert len(svg_text) > 5000, f"SVG too small: {len(svg_text)} chars"

    def test_fire_features_present_in_floor_plan(self):
        svg_text = _generate_scenario(SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp)
        assert "#AF2B1E" in svg_text, "Fire wall color (RAL 3000) should be present"
        assert "T30" in svg_text, "Fire door rating should be rendered"

    def test_escape_routes_rendered(self):
        svg_text = _generate_scenario(SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp)
        assert 'id="escape-routes"' in svg_text, "Escape routes group should exist"
