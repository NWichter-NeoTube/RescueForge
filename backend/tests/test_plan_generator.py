"""Tests for SVG plan generation and PDF export."""

from pathlib import Path

import pytest

from app.models.schemas import DoorInfo, FloorPlanData, Point, RoomPolygon, RoomType, WallSegment
from app.pipeline.plan_generator import (
    DANGEROUS_ROOM_TYPES,
    generate_cover_sheet,
    generate_situation_plan,
    generate_svg,
)


def _make_test_floor_plan() -> tuple[FloorPlanData, list[RoomPolygon]]:
    """Create test floor plan with rooms for SVG generation."""
    walls = [
        WallSegment(start=Point(x=0, y=0), end=Point(x=200, y=0)),
        WallSegment(start=Point(x=200, y=0), end=Point(x=200, y=100)),
        WallSegment(start=Point(x=200, y=100), end=Point(x=0, y=100)),
        WallSegment(start=Point(x=0, y=100), end=Point(x=0, y=0)),
        WallSegment(start=Point(x=100, y=0), end=Point(x=100, y=100)),
    ]
    fp = FloorPlanData(
        filename="test.dxf",
        walls=walls,
        bounds=(0, 0, 200, 100),
    )
    rooms = [
        RoomPolygon(
            id=1,
            points=[Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=100), Point(x=0, y=100)],
            room_type=RoomType.OFFICE,
            label="Büro 1",
            area=10000,
        ),
        RoomPolygon(
            id=2,
            points=[Point(x=100, y=0), Point(x=200, y=0), Point(x=200, y=100), Point(x=100, y=100)],
            room_type=RoomType.CORRIDOR,
            label="Korridor",
            area=10000,
        ),
    ]
    return fp, rooms


class TestSvgGeneration:
    """Test FKS-compliant SVG generation."""

    def test_generate_svg_creates_file(self, tmp_output: Path):
        """SVG generation should create a valid file."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "test.svg")
        assert svg_path.exists()
        assert svg_path.stat().st_size > 0

    def test_svg_contains_rooms(self, tmp_output: Path):
        """Generated SVG should contain room labels."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "test.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert "Büro 1" in content
        assert "Korridor" in content

    def test_svg_contains_structural_elements(self, tmp_output: Path):
        """SVG should contain walls and legend."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "test.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert 'id="walls"' in content
        assert 'id="rooms"' in content
        assert "Legend" in content
        assert "Orientation Plan" in content

    def test_svg_paper_format_a3(self, tmp_output: Path):
        """A3 format should produce correct dimensions."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "test.svg", paper_format="A3")
        content = svg_path.read_text(encoding="utf-8")
        assert "420mm" in content
        assert "297mm" in content

    def test_svg_paper_format_a4(self, tmp_output: Path):
        """A4 format should produce correct dimensions."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "test.svg", paper_format="A4")
        content = svg_path.read_text(encoding="utf-8")
        assert "297mm" in content
        assert "210mm" in content

    def test_svg_building_name(self, tmp_output: Path):
        """Building name should appear in title block."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(
            fp, rooms, tmp_output / "test.svg",
            building_name="Testgebäude",
            floor_label="1.OG",
        )
        content = svg_path.read_text(encoding="utf-8")
        assert "Testgebäude" in content
        assert "1.OG" in content

    def test_svg_color_coding(self, tmp_output: Path):
        """FKS color coding should be applied to escape routes."""
        fp, rooms = _make_test_floor_plan()
        # Add stairwell room
        rooms.append(RoomPolygon(
            id=3,
            points=[Point(x=50, y=50), Point(x=60, y=50), Point(x=60, y=60), Point(x=50, y=60)],
            room_type=RoomType.STAIRWELL,
            label="Treppenhaus",
            area=100,
        ))
        svg_path = generate_svg(fp, rooms, tmp_output / "test.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Dark green for stairwells
        assert "#006400" in content

    def test_full_pipeline_dxf_to_svg(self, sample_dxf_path: Path, tmp_output: Path):
        """Integration: Parse DXF -> detect rooms -> generate SVG."""
        from app.pipeline.dxf_parser import parse_dxf
        from app.pipeline.room_detector import detect_rooms

        floor_plan = parse_dxf(sample_dxf_path)
        rooms = detect_rooms(floor_plan)

        svg_path = generate_svg(
            floor_plan, rooms, tmp_output / "integration_test.svg",
            building_name="Integration Test",
            floor_label="EG",
        )

        assert svg_path.exists()
        content = svg_path.read_text(encoding="utf-8")
        assert "Integration Test" in content
        assert svg_path.stat().st_size > 1000, "SVG should be substantial"


class TestDangerousRooms:
    """Test FKS dangerous room highlighting."""

    def test_dangerous_room_red_border(self, tmp_output: Path):
        """Dangerous rooms (TECHNICAL, SERVER_ROOM, GARAGE) should have red dashed borders."""
        fp, rooms = _make_test_floor_plan()
        rooms.append(RoomPolygon(
            id=3,
            points=[Point(x=50, y=50), Point(x=80, y=50), Point(x=80, y=80), Point(x=50, y=80)],
            room_type=RoomType.TECHNICAL,
            label="Technik",
            area=900,
        ))
        svg_path = generate_svg(fp, rooms, tmp_output / "danger.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Red dashed border for danger zone
        assert "#FF0000" in content
        assert "Technik" in content

    def test_dangerous_room_types_defined(self):
        """DANGEROUS_ROOM_TYPES should contain expected types."""
        assert RoomType.TECHNICAL in DANGEROUS_ROOM_TYPES
        assert RoomType.SERVER_ROOM in DANGEROUS_ROOM_TYPES
        assert RoomType.GARAGE in DANGEROUS_ROOM_TYPES
        assert RoomType.OFFICE not in DANGEROUS_ROOM_TYPES

    def test_danger_legend_entry(self, tmp_output: Path):
        """Legend should contain danger zone entry."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "legend.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert "Danger Zone" in content


class TestLargeRoomArea:
    """Test area labels for large rooms."""

    def test_large_room_shows_area(self, tmp_output: Path):
        """Rooms larger than 2x median should show area label."""
        fp = FloorPlanData(
            filename="test.dxf",
            walls=[
                WallSegment(start=Point(x=0, y=0), end=Point(x=300, y=0)),
                WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=200)),
                WallSegment(start=Point(x=300, y=200), end=Point(x=0, y=200)),
                WallSegment(start=Point(x=0, y=200), end=Point(x=0, y=0)),
            ],
            bounds=(0, 0, 300, 200),
        )
        # 3 rooms: small (2500), medium (5000), large (50000)
        # sorted = [2500, 5000, 50000], median = 5000, threshold = 10000
        # 50000 > 10000 -> area label shown
        rooms = [
            RoomPolygon(id=1, points=[
                Point(x=0, y=0), Point(x=50, y=0), Point(x=50, y=50), Point(x=0, y=50),
            ], room_type=RoomType.BATHROOM, label="WC", area=2500),
            RoomPolygon(id=2, points=[
                Point(x=50, y=0), Point(x=100, y=0), Point(x=100, y=50), Point(x=50, y=50),
            ], room_type=RoomType.OFFICE, label="Büro", area=5000),
            RoomPolygon(id=3, points=[
                Point(x=100, y=0), Point(x=300, y=0), Point(x=300, y=200), Point(x=100, y=200),
            ], room_type=RoomType.LOBBY, label="Halle", area=50000),
        ]
        svg_path = generate_svg(fp, rooms, tmp_output / "area.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Large room should have "A =" area label
        assert "A =" in content


class TestEscapeRoutes:
    """Test graph-based escape route calculation."""

    def test_escape_routes_with_adjacent_rooms(self, tmp_output: Path):
        """Escape routes should connect corridors to stairwells through adjacent rooms."""
        fp = FloorPlanData(
            filename="test.dxf",
            walls=[
                WallSegment(start=Point(x=0, y=0), end=Point(x=300, y=0)),
                WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=100)),
                WallSegment(start=Point(x=300, y=100), end=Point(x=0, y=100)),
                WallSegment(start=Point(x=0, y=100), end=Point(x=0, y=0)),
            ],
            bounds=(0, 0, 300, 100),
        )
        rooms = [
            RoomPolygon(id=1, points=[
                Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=100), Point(x=0, y=100),
            ], room_type=RoomType.CORRIDOR, label="Korridor", area=10000),
            RoomPolygon(id=2, points=[
                Point(x=100, y=0), Point(x=200, y=0), Point(x=200, y=100), Point(x=100, y=100),
            ], room_type=RoomType.OFFICE, label="Büro", area=10000),
            RoomPolygon(id=3, points=[
                Point(x=200, y=0), Point(x=300, y=0), Point(x=300, y=100), Point(x=200, y=100),
            ], room_type=RoomType.STAIRWELL, label="Treppenhaus", area=10000),
        ]
        svg_path = generate_svg(fp, rooms, tmp_output / "escape.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Escape route group should exist
        assert 'id="escape-routes"' in content
        # Green escape lines
        assert "#006400" in content

    def test_no_stairwell_no_crash(self, tmp_output: Path):
        """Escape route generation should not crash without stairwells."""
        fp, rooms = _make_test_floor_plan()
        # Only corridor, no stairwell
        rooms = [r for r in rooms if r.room_type == RoomType.CORRIDOR]
        svg_path = generate_svg(fp, rooms, tmp_output / "no_stairs.svg")
        assert svg_path.exists()


class TestCoverSheet:
    """Test FKS cover sheet generation."""

    def test_cover_sheet_creates_file(self, tmp_output: Path):
        """Cover sheet generation should create a valid SVG."""
        fp, rooms = _make_test_floor_plan()
        path = generate_cover_sheet(rooms, tmp_output / "cover.svg", building_name="Testgebäude")
        assert path.exists()
        assert path.stat().st_size > 0

    def test_cover_sheet_contains_building_info(self, tmp_output: Path):
        """Cover sheet should contain building name and legend sections."""
        fp, rooms = _make_test_floor_plan()
        path = generate_cover_sheet(
            rooms, tmp_output / "cover.svg",
            building_name="Musterhaus",
            floors=["UG", "EG", "1.OG"],
        )
        content = path.read_text(encoding="utf-8")
        assert "Cover Sheet" in content
        assert "Musterhaus" in content
        assert "Building Definition" in content
        assert "Legend" in content

    def test_cover_sheet_contains_symbols(self, tmp_output: Path):
        """Cover sheet legend should include FKS symbol descriptions."""
        fp, rooms = _make_test_floor_plan()
        path = generate_cover_sheet(rooms, tmp_output / "cover.svg")
        content = path.read_text(encoding="utf-8")
        assert "Smoke Detector" in content
        assert "Manual Call Point" in content
        assert "Escape Route" in content
        assert "Fire Access" in content

    def test_cover_sheet_danger_zones(self, tmp_output: Path):
        """Cover sheet should highlight danger zone room types."""
        rooms = [
            RoomPolygon(id=1, points=[Point(x=0, y=0), Point(x=10, y=0), Point(x=10, y=10), Point(x=0, y=10)],
                        room_type=RoomType.TECHNICAL, label="Technik", area=100),
        ]
        path = generate_cover_sheet(rooms, tmp_output / "cover_danger.svg")
        content = path.read_text(encoding="utf-8")
        assert "Technical" in content


class TestSituationPlan:
    """Test FKS situation plan generation."""

    def test_situation_plan_creates_file(self, tmp_output: Path):
        """Situation plan generation should create a valid SVG."""
        fp, rooms = _make_test_floor_plan()
        path = generate_situation_plan(fp, rooms, tmp_output / "situation.svg", building_name="Testgebäude")
        assert path.exists()
        assert path.stat().st_size > 0

    def test_situation_plan_contains_sides(self, tmp_output: Path):
        """Situation plan should label building sides (A-D)."""
        fp, rooms = _make_test_floor_plan()
        path = generate_situation_plan(fp, rooms, tmp_output / "situation.svg")
        content = path.read_text(encoding="utf-8")
        assert "Side A" in content
        assert "Side B" in content
        assert "Side C" in content
        assert "Side D" in content

    def test_situation_plan_contains_access(self, tmp_output: Path):
        """Situation plan should show fire department access and key depot."""
        fp, rooms = _make_test_floor_plan()
        path = generate_situation_plan(fp, rooms, tmp_output / "situation.svg")
        content = path.read_text(encoding="utf-8")
        assert "Fire Dept. Access" in content
        assert "Situation Plan" in content

    def test_situation_plan_zero_dims(self, tmp_output: Path):
        """Situation plan should handle zero-dimension floor plans gracefully."""
        fp = FloorPlanData(filename="empty.dxf", bounds=(0, 0, 0, 0))
        path = generate_situation_plan(fp, [], tmp_output / "empty_sit.svg")
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Situation Plan" in content


class TestGeometryUtils:
    """Test geometry utility functions."""

    def test_line_angle(self):
        from app.utils.geometry import line_angle
        assert line_angle(0, 0, 1, 0) == pytest.approx(0, abs=0.1)
        assert line_angle(0, 0, 0, 1) == pytest.approx(90, abs=0.1)
        assert line_angle(0, 0, -1, 0) == pytest.approx(180, abs=0.1)

    def test_is_horizontal(self):
        from app.utils.geometry import is_horizontal
        assert is_horizontal(0, 0, 10, 0)
        assert not is_horizontal(0, 0, 0, 10)

    def test_is_vertical(self):
        from app.utils.geometry import is_vertical
        assert is_vertical(0, 0, 0, 10)
        assert not is_vertical(0, 0, 10, 0)

    def test_polygon_aspect_ratio(self):
        from shapely.geometry import Polygon
        from app.utils.geometry import polygon_aspect_ratio
        square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        assert polygon_aspect_ratio(square) == pytest.approx(1.0)

        rectangle = Polygon([(0, 0), (40, 0), (40, 10), (0, 10)])
        assert polygon_aspect_ratio(rectangle) == pytest.approx(4.0)


class TestLanguageSupport:
    """Test multi-language support for SVG, cover sheet, and situation plan."""

    def test_svg_german_labels(self, tmp_output: Path):
        """SVG with language='de' should contain German text."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "de.svg", language="de")
        content = svg_path.read_text(encoding="utf-8")
        assert "Legende" in content
        assert "Orientierungsplan" in content
        assert "Gefahrenbereich" in content

    def test_svg_english_labels(self, tmp_output: Path):
        """SVG with language='en' (default) should contain English text."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "en.svg", language="en")
        content = svg_path.read_text(encoding="utf-8")
        assert "Legend" in content
        assert "Orientation Plan" in content
        assert "Danger Zone" in content

    def test_cover_sheet_german(self, tmp_output: Path):
        """Cover sheet with language='de' should contain German text."""
        fp, rooms = _make_test_floor_plan()
        path = generate_cover_sheet(rooms, tmp_output / "cover_de.svg", language="de")
        content = path.read_text(encoding="utf-8")
        assert "Deckblatt" in content
        assert "Objektdefinition" in content
        assert "Rauchmelder" in content

    def test_cover_sheet_english(self, tmp_output: Path):
        """Cover sheet with language='en' should contain English text."""
        fp, rooms = _make_test_floor_plan()
        path = generate_cover_sheet(rooms, tmp_output / "cover_en.svg", language="en")
        content = path.read_text(encoding="utf-8")
        assert "Cover Sheet" in content
        assert "Building Definition" in content
        assert "Smoke Detector" in content

    def test_situation_plan_german(self, tmp_output: Path):
        """Situation plan with language='de' should contain German text."""
        fp, rooms = _make_test_floor_plan()
        path = generate_situation_plan(fp, rooms, tmp_output / "sit_de.svg", language="de")
        content = path.read_text(encoding="utf-8")
        assert "Situationsplan" in content
        assert "Seite A" in content
        assert "Feuerwehrzufahrt" in content

    def test_situation_plan_english(self, tmp_output: Path):
        """Situation plan with language='en' should contain English text."""
        fp, rooms = _make_test_floor_plan()
        path = generate_situation_plan(fp, rooms, tmp_output / "sit_en.svg", language="en")
        content = path.read_text(encoding="utf-8")
        assert "Situation Plan" in content
        assert "Side A" in content
        assert "Fire Dept. Access" in content


class TestFilledWalls:
    """Test that walls are rendered as filled polygons per DIN 14095."""

    def test_walls_rendered_as_polygons(self, tmp_output: Path):
        """Walls should be rendered as <polygon> elements, not just lines."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "walls.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Walls group should contain polygon elements (filled walls)
        walls_idx = content.find('id="walls"')
        assert walls_idx != -1, "Walls group must exist"
        walls_section = content[walls_idx:]
        assert "<polygon" in walls_section


class TestFireFeatures:
    """Test fire wall and fire door rendering."""

    def test_fire_wall_red_color(self, tmp_output: Path):
        """Fire walls should be rendered in RAL 3000 red (#AF2B1E)."""
        fp, rooms = _make_test_floor_plan()
        fp.fire_walls = [
            WallSegment(start=Point(x=100, y=0), end=Point(x=100, y=100)),
        ]
        svg_path = generate_svg(fp, rooms, tmp_output / "fire_wall.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert "#AF2B1E" in content

    def test_fire_door_rendering(self, tmp_output: Path):
        """Fire doors should appear in the generated SVG."""
        fp, rooms = _make_test_floor_plan()
        fp.fire_doors = [
            DoorInfo(position=Point(x=100, y=50), width=10, fire_rating="T30"),
        ]
        svg_path = generate_svg(fp, rooms, tmp_output / "fire_door.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert 'id="fire-doors"' in content
        assert "T30" in content


class TestReferenceGrid:
    """Test DIN 14095 reference grid generation."""

    def test_grid_exists(self, tmp_output: Path):
        """SVG should contain a reference-grid group."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "grid.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert 'id="reference-grid"' in content


class TestExtendedTitleBlock:
    """Test extended title block fields per DIN 14095."""

    def test_title_block_creation_date(self, tmp_output: Path):
        """Creation date should appear in the title block."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(
            fp, rooms, tmp_output / "date.svg", creation_date="2025-06-15",
        )
        content = svg_path.read_text(encoding="utf-8")
        assert "2025-06-15" in content

    def test_title_block_registration(self, tmp_output: Path):
        """Registration number should appear in the title block."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(
            fp, rooms, tmp_output / "reg.svg", registration_number="FW-2025-042",
        )
        content = svg_path.read_text(encoding="utf-8")
        assert "FW-2025-042" in content

    def test_title_block_page_number(self, tmp_output: Path):
        """Page number should appear in the title block."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(
            fp, rooms, tmp_output / "page.svg", page_number="3",
        )
        content = svg_path.read_text(encoding="utf-8")
        assert "Page" in content
        assert "3" in content


class TestRoomNumbering:
    """Test DIN 14095 room numbering."""

    def test_rooms_get_numbered(self, tmp_output: Path):
        """Rooms should receive DIN 14095 numbering like 'Label 0.01'."""
        fp, rooms = _make_test_floor_plan()
        # Add a second office so the counter increments to 0.02
        rooms.append(RoomPolygon(
            id=3,
            points=[Point(x=50, y=50), Point(x=80, y=50), Point(x=80, y=80), Point(x=50, y=80)],
            room_type=RoomType.OFFICE,
            label="Büro 2",
            area=900,
        ))
        svg_path = generate_svg(fp, rooms, tmp_output / "numbered.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Room numbering follows "label floor.counter" pattern, per type
        assert "0.01" in content
        assert "0.02" in content


class TestUtilitySymbols:
    """Test utility shutoff symbol rendering."""

    def test_shutoff_symbols_in_svg(self, tmp_output: Path):
        """SVG should contain G, W, E texts for gas/water/electricity shutoffs."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "shutoffs.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Gas, Water, Electricity shutoff letter symbols
        assert ">G<" in content
        assert ">W<" in content
        assert ">E<" in content


class TestUnitDetection:
    """Test automatic unit detection and scale computation."""

    def test_mm_building_keeps_mm(self):
        from app.pipeline.plan_generator import _detect_unit_to_mm
        # 20000mm x 15000mm building — declared mm is correct
        assert _detect_unit_to_mm(20000, 15000, "mm") == 1.0

    def test_meters_building_keeps_m(self):
        from app.pipeline.plan_generator import _detect_unit_to_mm
        # 12m x 10m in meters — declared m is correct
        assert _detect_unit_to_mm(12, 10, "m") == 1000.0

    def test_wrong_unit_autodetects(self):
        from app.pipeline.plan_generator import _detect_unit_to_mm
        # 866 x 572 declared as mm but actually inches (building = 22m x 14.5m)
        u2mm = _detect_unit_to_mm(866, 572, "mm")
        assert u2mm == 25.4  # inches

    def test_din_scale_for_small_house(self):
        from app.pipeline.plan_generator import _compute_din_scale
        # rendering_scale ≈ 0.4, unit_to_mm = 25.4 → ratio ≈ 63 → nearest DIN = 50
        assert _compute_din_scale(0.4, 25.4) == 50

    def test_din_scale_for_large_building(self):
        from app.pipeline.plan_generator import _compute_din_scale
        # ratio ≈ 200 → DIN 200
        assert _compute_din_scale(0.05, 10.0) == 200

    def test_area_to_m2_mm(self):
        from app.pipeline.plan_generator import _area_to_m2
        # 1,000,000 mm² = 1 m²
        assert _area_to_m2(1_000_000, 1.0) == pytest.approx(1.0)

    def test_area_to_m2_inches(self):
        from app.pipeline.plan_generator import _area_to_m2
        # 1550 in² ≈ 1 m² (25.4² / 1e6 * 1550 ≈ 1.0)
        result = _area_to_m2(1550, 25.4)
        assert 0.9 < result < 1.1

    def test_svg_shows_din_scale(self, tmp_output: Path):
        """Generated SVG title block should show DIN scale like '1:50', not 'ca. 1:2'."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "scale.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Should contain a standard DIN scale, not "ca."
        assert "ca." not in content
        assert "1:" in content

    def test_title_block_din_layout(self, tmp_output: Path):
        """Title block should contain DIN 14095 reference."""
        fp, rooms = _make_test_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "tb.svg")
        content = svg_path.read_text(encoding="utf-8")
        assert "DIN 14095" in content
        assert "DIN 14034-6" in content


def _skip_if_no_weasyprint():
    """Skip test if WeasyPrint native libraries are not available."""
    try:
        from app.pipeline.pdf_exporter import export_pdf  # noqa: F401
    except (ImportError, OSError):
        pytest.skip("WeasyPrint native libraries not available (needs GTK/Pango)")


class TestPdfValidity:
    """Verify PDF export produces valid files after SVG structural changes.

    Skipped on systems without WeasyPrint native libraries (Windows without GTK).
    Runs in Docker where all dependencies are installed.
    """

    def test_pdf_valid_header(self, tmp_output: Path):
        """Generated PDF should start with %PDF- magic bytes."""
        _skip_if_no_weasyprint()
        from app.pipeline.pdf_exporter import export_pdf

        fp, rooms = _make_rich_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "pdf_test.svg")
        pdf_path = export_pdf(svg_path, tmp_output / "pdf_test.pdf")

        assert pdf_path.exists()
        content = pdf_path.read_bytes()
        assert content[:5] == b"%PDF-", "PDF should start with %PDF- header"

    def test_pdf_minimum_size(self, tmp_output: Path):
        """Generated PDF should be larger than 1KB (not empty/corrupted)."""
        _skip_if_no_weasyprint()
        from app.pipeline.pdf_exporter import export_pdf

        fp, rooms = _make_rich_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "pdf_size.svg")
        pdf_path = export_pdf(svg_path, tmp_output / "pdf_size.pdf")

        file_size = pdf_path.stat().st_size
        assert file_size > 1000, f"PDF too small: {file_size} bytes"

    def test_pdf_from_cover_sheet(self, tmp_output: Path):
        """PDF export should work for cover sheets too."""
        _skip_if_no_weasyprint()
        from app.pipeline.pdf_exporter import export_pdf

        fp, rooms = _make_rich_floor_plan()
        svg_path = generate_cover_sheet(rooms, tmp_output / "cover.svg", floor_plan=fp)
        pdf_path = export_pdf(svg_path, tmp_output / "cover.pdf")

        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 500

    def test_pdf_from_situation_plan(self, tmp_output: Path):
        """PDF export should work for situation plans."""
        _skip_if_no_weasyprint()
        from app.pipeline.pdf_exporter import export_pdf

        fp, rooms = _make_rich_floor_plan()
        svg_path = generate_situation_plan(fp, rooms, tmp_output / "situation.svg")
        pdf_path = export_pdf(svg_path, tmp_output / "situation.pdf")

        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 500


class TestEscapeRoutePolylines:
    """Verify escape routes use polyline routing through corridor centerlines."""

    def test_escape_route_has_polyline(self, tmp_output: Path):
        """SVG with corridor→stairwell should contain <polyline> elements."""
        fp, rooms = _make_rich_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "polyline.svg")
        content = svg_path.read_text(encoding="utf-8")
        # The corridor routing should produce polyline elements
        assert "<polyline" in content, "Escape routes should use <polyline> elements"

    def test_escape_route_polyline_is_dashed(self, tmp_output: Path):
        """Escape polylines should have dash pattern per DIN 14095."""
        fp, rooms = _make_rich_floor_plan()
        svg_path = generate_svg(fp, rooms, tmp_output / "dash.svg")
        content = svg_path.read_text(encoding="utf-8")
        # Check for dashed stroke style in the escape routes section
        assert 'stroke-dasharray="2,1"' in content


def _make_rich_floor_plan() -> tuple[FloorPlanData, list[RoomPolygon]]:
    """Create a rich test floor plan with corridor, offices, stairwell for PDF/polyline tests."""
    walls = [
        WallSegment(start=Point(x=0, y=0), end=Point(x=400, y=0)),
        WallSegment(start=Point(x=400, y=0), end=Point(x=400, y=200)),
        WallSegment(start=Point(x=400, y=200), end=Point(x=0, y=200)),
        WallSegment(start=Point(x=0, y=200), end=Point(x=0, y=0)),
        WallSegment(start=Point(x=100, y=0), end=Point(x=100, y=200)),
        WallSegment(start=Point(x=200, y=0), end=Point(x=200, y=200)),
        WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=200)),
    ]
    fire_walls = [
        WallSegment(start=Point(x=300, y=0), end=Point(x=300, y=200)),
    ]
    doors = [
        DoorInfo(position=Point(x=100, y=50), width=30),
        DoorInfo(position=Point(x=200, y=50), width=30),
        DoorInfo(position=Point(x=300, y=50), width=30),
    ]
    fp = FloorPlanData(
        filename="rich_test.dxf",
        walls=walls,
        fire_walls=fire_walls,
        doors=doors,
        fire_doors=[DoorInfo(position=Point(x=300, y=50), width=30, fire_rating="T30")],
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
            label="Office",
            area=20000,
        ),
        RoomPolygon(
            id=3,
            points=[Point(x=200, y=0), Point(x=300, y=0), Point(x=300, y=200), Point(x=200, y=200)],
            room_type=RoomType.OFFICE,
            label="Office 2",
            area=20000,
        ),
        RoomPolygon(
            id=4,
            points=[Point(x=300, y=0), Point(x=400, y=0), Point(x=400, y=200), Point(x=300, y=200)],
            room_type=RoomType.STAIRWELL,
            label="Stairwell",
            area=20000,
        ),
    ]
    return fp, rooms
