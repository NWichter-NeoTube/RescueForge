"""Visual regression tests for SVG plan output.

Generates SVG plans from deterministic test data and compares structural
fingerprints against stored baselines.  This catches unintended layout,
color, or content changes without requiring pixel-based screenshot tools.

The optional TestPixelRegression class uses CairoSVG to render SVGs to
PNG images and compares pixel-by-pixel against stored baseline PNGs.
This catches subtle rendering differences missed by structural fingerprints.

Usage:
    # Normal run — compare against baselines
    uv run pytest tests/test_visual_regression.py -v

    # Update baselines after intentional changes
    uv run pytest tests/test_visual_regression.py -v --update-baselines

Baselines are stored in testdata/baselines/*.json (structural) and
testdata/baselines/*.png (pixel-based).
"""

import json
import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

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
    """Build a rich, deterministic floor plan for regression testing.

    Includes: walls, fire walls, fire doors, doors, windows, multiple room
    types (office, corridor, stairwell, technical, bathroom), ensuring the
    generator exercises most code paths.
    """
    walls = [
        # Outer walls
        WallSegment(start=Point(x=0, y=0), end=Point(x=400, y=0)),
        WallSegment(start=Point(x=400, y=0), end=Point(x=400, y=200)),
        WallSegment(start=Point(x=400, y=200), end=Point(x=0, y=200)),
        WallSegment(start=Point(x=0, y=200), end=Point(x=0, y=0)),
        # Inner walls
        WallSegment(start=Point(x=100, y=0), end=Point(x=100, y=200)),
        WallSegment(start=Point(x=200, y=0), end=Point(x=200, y=200)),
        WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=200)),
        WallSegment(start=Point(x=200, y=100), end=Point(x=300, y=100)),
    ]

    fire_walls = [
        WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=200)),
    ]

    doors = [
        DoorInfo(position=Point(x=100, y=50), width=30),
        DoorInfo(position=Point(x=200, y=50), width=30),
        DoorInfo(position=Point(x=300, y=50), width=30),
    ]

    fire_doors = [
        DoorInfo(position=Point(x=300, y=50), width=30, fire_rating="T30"),
    ]

    windows = [
        WallSegment(start=Point(x=30, y=0), end=Point(x=70, y=0)),
        WallSegment(start=Point(x=130, y=0), end=Point(x=170, y=0)),
    ]

    fp = FloorPlanData(
        filename="regression_test.dxf",
        walls=walls,
        fire_walls=fire_walls,
        doors=doors,
        fire_doors=fire_doors,
        windows=windows,
        bounds=(0, 0, 400, 200),
        unit="mm",
    )

    rooms = [
        RoomPolygon(
            id=1,
            points=[Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=200), Point(x=0, y=200)],
            room_type=RoomType.CORRIDOR,
            label="Corridor",
            area=20000,
        ),
        RoomPolygon(
            id=2,
            points=[Point(x=100, y=0), Point(x=200, y=0), Point(x=200, y=200), Point(x=100, y=200)],
            room_type=RoomType.OFFICE,
            label="Office 1",
            area=20000,
        ),
        RoomPolygon(
            id=3,
            points=[Point(x=200, y=0), Point(x=300, y=0), Point(x=300, y=100), Point(x=200, y=100)],
            room_type=RoomType.BATHROOM,
            label="WC",
            area=10000,
        ),
        RoomPolygon(
            id=4,
            points=[Point(x=200, y=100), Point(x=300, y=100), Point(x=300, y=200), Point(x=200, y=200)],
            room_type=RoomType.TECHNICAL,
            label="Technical",
            area=10000,
        ),
        RoomPolygon(
            id=5,
            points=[Point(x=300, y=0), Point(x=400, y=0), Point(x=400, y=200), Point(x=300, y=200)],
            room_type=RoomType.STAIRWELL,
            label="Stairwell",
            area=20000,
        ),
    ]

    return fp, rooms


# ── SVG fingerprinting ───────────────────────────────────────

def _fingerprint_svg(svg_text: str) -> dict:
    """Extract a structural fingerprint from an SVG string.

    The fingerprint captures:
    - element counts (<rect>, <polygon>, <text>, <line>, <path>, <circle>, <g>)
    - group ids present
    - all text content (sorted)
    - all unique fill/stroke colors
    - viewBox / width / height attributes
    - total character count (rough size proxy)
    """
    fp: dict = {}

    # Element counts
    for tag in ("rect", "polygon", "text", "line", "path", "circle", "g", "polyline"):
        fp[f"count_{tag}"] = len(re.findall(rf"<{tag}[\s/>]", svg_text))

    # Group IDs
    group_ids = sorted(set(re.findall(r'id="([^"]+)"', svg_text)))
    fp["group_ids"] = group_ids

    # Text content
    texts = sorted(re.findall(r">([^<]+)<", svg_text))
    # Filter out whitespace-only entries
    texts = [t.strip() for t in texts if t.strip()]
    fp["text_content"] = texts

    # Colors (fill and stroke)
    colors = sorted(set(re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,8})"', svg_text)))
    fp["colors"] = colors

    # SVG root attributes
    vb = re.search(r'viewBox="([^"]+)"', svg_text)
    fp["viewBox"] = vb.group(1) if vb else ""

    width = re.search(r'width="([^"]+)"', svg_text)
    fp["width"] = width.group(1) if width else ""

    height = re.search(r'height="([^"]+)"', svg_text)
    fp["height"] = height.group(1) if height else ""

    # Size proxy
    fp["total_chars"] = len(svg_text)

    return fp


def _compare_fingerprints(
    baseline: dict, current: dict, name: str, tolerance_chars: float = 0.15,
) -> list[str]:
    """Compare two fingerprints and return a list of differences.

    Args:
        baseline: The stored baseline fingerprint.
        current: The newly generated fingerprint.
        name: Human-readable name for error messages.
        tolerance_chars: Allowed relative difference in total_chars (default 15%).

    Returns:
        List of difference descriptions (empty = match).
    """
    diffs: list[str] = []

    # Element counts — exact match
    for key in baseline:
        if key.startswith("count_"):
            b_val = baseline[key]
            c_val = current.get(key, 0)
            if b_val != c_val:
                diffs.append(f"{name}: {key} changed {b_val} → {c_val}")

    # Group IDs — exact match
    if baseline.get("group_ids") != current.get("group_ids"):
        b_ids = set(baseline.get("group_ids", []))
        c_ids = set(current.get("group_ids", []))
        added = c_ids - b_ids
        removed = b_ids - c_ids
        if added:
            diffs.append(f"{name}: new group IDs {added}")
        if removed:
            diffs.append(f"{name}: removed group IDs {removed}")

    # Colors — exact match
    if baseline.get("colors") != current.get("colors"):
        b_colors = set(baseline.get("colors", []))
        c_colors = set(current.get("colors", []))
        added = c_colors - b_colors
        removed = b_colors - c_colors
        if added:
            diffs.append(f"{name}: new colors {added}")
        if removed:
            diffs.append(f"{name}: removed colors {removed}")

    # Text content — check for missing/added entries
    b_texts = set(baseline.get("text_content", []))
    c_texts = set(current.get("text_content", []))
    missing = b_texts - c_texts
    added = c_texts - b_texts
    if missing:
        # Only flag significant missing text (>2 chars, not purely numeric)
        sig_missing = {t for t in missing if len(t) > 2 and not t.replace(".", "").isdigit()}
        if sig_missing:
            diffs.append(f"{name}: missing text entries (sample): {list(sig_missing)[:5]}")
    if added:
        sig_added = {t for t in added if len(t) > 2 and not t.replace(".", "").isdigit()}
        if sig_added:
            diffs.append(f"{name}: new text entries (sample): {list(sig_added)[:5]}")

    # Paper dimensions — exact
    for dim in ("viewBox", "width", "height"):
        if baseline.get(dim) != current.get(dim):
            diffs.append(f"{name}: {dim} changed '{baseline.get(dim)}' → '{current.get(dim)}'")

    # Total size — within tolerance
    b_size = baseline.get("total_chars", 0)
    c_size = current.get("total_chars", 0)
    if b_size > 0:
        rel_diff = abs(c_size - b_size) / b_size
        if rel_diff > tolerance_chars:
            diffs.append(
                f"{name}: size changed by {rel_diff:.0%} "
                f"({b_size} → {c_size} chars, tolerance {tolerance_chars:.0%})"
            )

    return diffs


# ── Test scenarios ───────────────────────────────────────────

SCENARIOS = {
    "floor_plan_en_a3": {
        "generator": "svg",
        "kwargs": {"paper_format": "A3", "language": "en", "building_name": "Regression Test", "floor_label": "GF"},
    },
    "floor_plan_de_a3": {
        "generator": "svg",
        "kwargs": {"paper_format": "A3", "language": "de", "building_name": "Regressionstest", "floor_label": "EG"},
    },
    "floor_plan_en_a4": {
        "generator": "svg",
        "kwargs": {"paper_format": "A4", "language": "en", "building_name": "Regression A4"},
    },
    "cover_sheet_en": {
        "generator": "cover_sheet",
        "kwargs": {"language": "en", "building_name": "Regression Cover", "floors": ["GF", "1F", "2F"]},
    },
    "cover_sheet_de": {
        "generator": "cover_sheet",
        "kwargs": {"language": "de", "building_name": "Regressions-Deckblatt", "floors": ["EG", "1.OG", "2.OG"]},
    },
    "situation_plan_en": {
        "generator": "situation",
        "kwargs": {"language": "en", "building_name": "Regression Situation"},
    },
    "situation_plan_de": {
        "generator": "situation",
        "kwargs": {"language": "de", "building_name": "Regressions-Situation"},
    },
}


def _generate_scenario(scenario: dict, fp: FloorPlanData, rooms: list[RoomPolygon], out_dir: Path) -> str:
    """Generate SVG for a scenario and return the SVG text."""
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


# ── Tests ────────────────────────────────────────────────────

class TestVisualRegression:
    """Compare generated SVGs against stored structural baselines."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_output: Path, request):
        self.tmp = tmp_output
        self.update = request.config.getoption("--update-baselines", default=False)
        self.fp, self.rooms = _make_regression_floor_plan()

    @pytest.mark.parametrize("name", list(SCENARIOS.keys()))
    def test_scenario_matches_baseline(self, name: str):
        """Generated SVG fingerprint should match stored baseline."""
        scenario = SCENARIOS[name]
        svg_text = _generate_scenario(scenario, self.fp, self.rooms, self.tmp)
        current = _fingerprint_svg(svg_text)

        baseline_path = BASELINES_DIR / f"{name}.json"

        if self.update or not baseline_path.exists():
            # Create or update baseline
            BASELINES_DIR.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(
                json.dumps(current, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            pytest.skip(f"Baseline {'updated' if self.update else 'created'}: {baseline_path.name}")

        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        diffs = _compare_fingerprints(baseline, current, name)

        if diffs:
            # Also dump current fingerprint for debugging
            debug_path = self.tmp / f"{name}_current.json"
            debug_path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
            pytest.fail(
                f"Visual regression detected in '{name}':\n"
                + "\n".join(f"  - {d}" for d in diffs)
                + f"\n\nCurrent fingerprint saved to: {debug_path}"
                + "\nRun with --update-baselines to accept changes."
            )

    def test_all_scenarios_have_baselines(self):
        """Every scenario should have a baseline file."""
        missing = []
        for name in SCENARIOS:
            if not (BASELINES_DIR / f"{name}.json").exists():
                missing.append(name)
        if missing:
            pytest.skip(
                f"Missing baselines: {missing}. Run with --update-baselines to create them."
            )

    def test_floor_plan_svg_is_substantial(self):
        """Regression floor plan SVG should be larger than 5KB (sanity check)."""
        svg_text = _generate_scenario(
            SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp,
        )
        assert len(svg_text) > 5000, f"SVG too small: {len(svg_text)} chars"

    def test_cover_sheet_contains_all_room_types(self):
        """Cover sheet legend should reference all room types present in test data."""
        svg_text = _generate_scenario(
            SCENARIOS["cover_sheet_en"], self.fp, self.rooms, self.tmp,
        )
        for rt in {r.room_type for r in self.rooms}:
            # At least the room type value or its label should appear
            assert rt.value.lower().replace("_", " ") in svg_text.lower() or \
                   rt.value in svg_text, \
                   f"Room type {rt.value} not found in cover sheet"

    def test_situation_plan_has_building_outline(self):
        """Situation plan should contain the building outline polygon."""
        svg_text = _generate_scenario(
            SCENARIOS["situation_plan_en"], self.fp, self.rooms, self.tmp,
        )
        assert "<polygon" in svg_text or "<rect" in svg_text, \
            "Situation plan should contain building outline shape"

    def test_fire_features_present_in_floor_plan(self):
        """Floor plan should render fire walls and fire doors from test data."""
        svg_text = _generate_scenario(
            SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp,
        )
        assert "#AF2B1E" in svg_text, "Fire wall color (RAL 3000) should be present"
        assert "T30" in svg_text, "Fire door rating should be rendered"

    def test_escape_routes_rendered(self):
        """Floor plan with stairwell should have escape routes."""
        svg_text = _generate_scenario(
            SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp,
        )
        assert 'id="escape-routes"' in svg_text, "Escape routes group should exist"

    def test_language_consistency_en(self):
        """English plan should not contain German-only strings."""
        svg_text = _generate_scenario(
            SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp,
        )
        # These German terms should NOT appear in English version
        # Use regex word boundaries to avoid substring false positives
        german_only = [r"\bLegende\b", r"\bOrientierungsplan\b", r"\bGefahrenbereich\b", r"\bFluchtweg\b"]
        for pattern in german_only:
            assert not re.search(pattern, svg_text), \
                f"German term '{pattern}' found in English SVG"

    def test_language_consistency_de(self):
        """German plan should not contain English-only strings."""
        svg_text = _generate_scenario(
            SCENARIOS["floor_plan_de_a3"], self.fp, self.rooms, self.tmp,
        )
        # These English multi-word terms should NOT appear in German version
        # "Legend" alone would match "Legende", so use exact phrase matching
        english_only = ["Orientation Plan", "Danger Zone", "Escape Route"]
        for term in english_only:
            assert term not in svg_text, f"English term '{term}' found in German SVG"
        # Check "Legend" as standalone word (not substring of "Legende")
        # Find all occurrences and filter out "Legende"
        legend_matches = [m for m in re.finditer(r"Legend", svg_text)
                          if not svg_text[m.start():m.start()+7] == "Legende"]
        assert len(legend_matches) == 0, "Standalone 'Legend' (not 'Legende') found in German SVG"


# ── Pixel-based visual regression ─────────────────────────────

def _render_svg_to_png(svg_text: str, output_path: Path, width: int = 800) -> Image.Image:
    """Render SVG text to a PNG file using CairoSVG.

    Returns a PIL Image object for comparison.
    """
    import cairosvg

    cairosvg.svg2png(
        bytestring=svg_text.encode("utf-8"),
        write_to=str(output_path),
        output_width=width,
    )
    return Image.open(output_path)


def _pixel_diff(img_a: Image.Image, img_b: Image.Image) -> float:
    """Compute mean pixel difference between two images.

    Resizes both to the same dimensions, converts to grayscale,
    and returns a value between 0.0 (identical) and 1.0 (completely different).
    """
    # Normalize to same size
    target_size = (800, 600)
    a = img_a.resize(target_size).convert("L")
    b = img_b.resize(target_size).convert("L")

    arr_a = np.array(a, dtype=np.float64)
    arr_b = np.array(b, dtype=np.float64)

    return float(np.mean(np.abs(arr_a - arr_b)) / 255.0)


class TestPixelRegression:
    """Pixel-based visual regression using CairoSVG rendering.

    Renders each SVG scenario to PNG and compares against stored baseline
    images.  Catches subtle layout shifts and rendering differences that
    structural fingerprints would miss.

    Requires cairosvg (optional dev dependency) — skips gracefully if missing.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_output: Path, request):
        # CairoSVG needs both the Python package AND the native cairo library.
        # On Windows without GTK/Cairo runtime, the import raises OSError.
        try:
            import cairosvg  # noqa: F401
        except (ImportError, OSError) as exc:
            pytest.skip(f"cairosvg not available — pixel regression skipped: {exc}")
        self.tmp = tmp_output
        self.update = request.config.getoption("--update-baselines", default=False)
        self.fp, self.rooms = _make_regression_floor_plan()

    @pytest.mark.parametrize("name", list(SCENARIOS.keys()))
    def test_pixel_baseline(self, name: str):
        """Rendered PNG should match stored pixel baseline within threshold."""
        scenario = SCENARIOS[name]
        svg_text = _generate_scenario(scenario, self.fp, self.rooms, self.tmp)

        # Render SVG to PNG
        current_png = self.tmp / f"{name}_current.png"
        current_img = _render_svg_to_png(svg_text, current_png)

        baseline_png = BASELINES_DIR / f"{name}.png"

        if self.update or not baseline_png.exists():
            # Create or update baseline PNG
            BASELINES_DIR.mkdir(parents=True, exist_ok=True)
            _render_svg_to_png(svg_text, baseline_png)
            pytest.skip(f"Pixel baseline {'updated' if self.update else 'created'}: {baseline_png.name}")

        baseline_img = Image.open(baseline_png)
        diff = _pixel_diff(baseline_img, current_img)

        # 3% threshold — allows for minor antialiasing/rounding differences
        max_diff = 0.03
        if diff > max_diff:
            # Save diff image for debugging
            debug_path = self.tmp / f"{name}_diff.png"
            _save_diff_image(baseline_img, current_img, debug_path)
            pytest.fail(
                f"Pixel regression in '{name}': {diff:.1%} mean difference "
                f"(threshold {max_diff:.0%}).\n"
                f"Current: {current_png}\n"
                f"Diff: {debug_path}\n"
                f"Run with --update-baselines to accept changes."
            )

    def test_render_produces_non_empty_png(self):
        """Basic sanity: rendering an SVG should produce a non-empty PNG."""
        svg_text = _generate_scenario(
            SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp,
        )
        png_path = self.tmp / "sanity.png"
        img = _render_svg_to_png(svg_text, png_path)
        assert img.size[0] > 0 and img.size[1] > 0
        assert png_path.stat().st_size > 1000, "PNG should be larger than 1KB"

    def test_pixel_diff_identical_images(self):
        """Two identical images should have 0% difference."""
        svg_text = _generate_scenario(
            SCENARIOS["floor_plan_en_a3"], self.fp, self.rooms, self.tmp,
        )
        png_a = self.tmp / "identical_a.png"
        png_b = self.tmp / "identical_b.png"
        img_a = _render_svg_to_png(svg_text, png_a)
        img_b = _render_svg_to_png(svg_text, png_b)
        diff = _pixel_diff(img_a, img_b)
        assert diff == 0.0, f"Identical renders should have 0% diff, got {diff:.4%}"


def _save_diff_image(img_a: Image.Image, img_b: Image.Image, output_path: Path) -> None:
    """Generate and save a visual diff image (absolute difference, enhanced)."""
    target_size = (800, 600)
    a = np.array(img_a.resize(target_size).convert("RGB"), dtype=np.float64)
    b = np.array(img_b.resize(target_size).convert("RGB"), dtype=np.float64)
    diff = np.abs(a - b)
    # Enhance differences for visibility (scale to 0-255)
    max_val = diff.max()
    if max_val > 0:
        diff = (diff / max_val * 255).astype(np.uint8)
    else:
        diff = diff.astype(np.uint8)
    Image.fromarray(diff).save(output_path)
