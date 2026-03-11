"""Tests for corridor centerline routing (DIN 14095 escape paths)."""

import math
from unittest.mock import MagicMock

import networkx as nx
import pytest
from shapely.geometry import LineString, MultiLineString, Polygon

from app.utils.corridor_routing import (
    build_corridor_graph,
    extract_medial_axis,
    route_escape_path,
)


# ── extract_medial_axis tests ─────────────────────────────────


class TestMedialAxisRectangle:
    """Test medial axis extraction on a simple 10x2 rectangular corridor."""

    def test_centerline_is_roughly_horizontal(self):
        """A wide rectangle's medial axis should run along its long dimension."""
        corridor = Polygon([(0, 0), (10, 0), (10, 2), (0, 2)])
        axis = extract_medial_axis(corridor, sample_spacing=0.5)

        # Get all coordinates from the result
        coords = _extract_coords(axis)
        assert len(coords) >= 2, "Medial axis should have at least 2 points"

        # Most Y values should be near the center (y=1.0).
        # Some Voronoi ridges near corners can deviate, so we check that
        # the majority (>= 60%) of points are close to center.
        near_center = [c for c in coords if abs(c[1] - 1.0) < 0.6]
        assert len(near_center) / len(coords) >= 0.6, (
            f"Only {len(near_center)}/{len(coords)} points near centerline"
        )

    def test_centerline_spans_corridor_length(self):
        """Medial axis should extend along most of the corridor length."""
        corridor = Polygon([(0, 0), (10, 0), (10, 2), (0, 2)])
        axis = extract_medial_axis(corridor, sample_spacing=0.5)

        coords = _extract_coords(axis)
        xs = [c[0] for c in coords]
        span = max(xs) - min(xs)
        # Should cover at least 60% of the corridor length
        assert span > 6.0, f"Medial axis span {span} too short for 10-unit corridor"


class TestMedialAxisLShape:
    """Test medial axis extraction on an L-shaped corridor."""

    def test_l_shape_produces_bent_centerline(self):
        """An L-shaped corridor should produce a centerline with a bend."""
        # L-shape: horizontal segment (0,0)-(8,2) + vertical segment (6,0)-(8,6)
        l_shape = Polygon([
            (0, 0), (8, 0), (8, 6), (6, 6), (6, 2), (0, 2),
        ])
        axis = extract_medial_axis(l_shape, sample_spacing=0.5)

        coords = _extract_coords(axis)
        assert len(coords) >= 3, "L-shape should have >= 3 centerline points"

        # Verify we have points in both the horizontal and vertical segments
        horiz_pts = [c for c in coords if c[1] < 2.5]
        vert_pts = [c for c in coords if c[1] > 2.0]
        assert len(horiz_pts) > 0, "No points in horizontal corridor segment"
        assert len(vert_pts) > 0, "No points in vertical corridor segment"


class TestCenterlineInsidePolygon:
    """All centerline points must lie inside the original polygon."""

    def test_all_points_inside_rectangle(self):
        corridor = Polygon([(0, 0), (10, 0), (10, 3), (0, 3)])
        axis = extract_medial_axis(corridor, sample_spacing=0.5)
        coords = _extract_coords(axis)

        for x, y in coords:
            assert corridor.contains(
                __import__("shapely.geometry", fromlist=["Point"]).Point(x, y)
            ) or corridor.boundary.distance(
                __import__("shapely.geometry", fromlist=["Point"]).Point(x, y)
            ) < 0.01, f"Point ({x}, {y}) outside corridor polygon"

    def test_all_points_inside_l_shape(self):
        l_shape = Polygon([
            (0, 0), (8, 0), (8, 6), (6, 6), (6, 2), (0, 2),
        ])
        axis = extract_medial_axis(l_shape, sample_spacing=0.5)
        coords = _extract_coords(axis)

        from shapely.geometry import Point
        for x, y in coords:
            dist_to_boundary = l_shape.boundary.distance(Point(x, y))
            assert l_shape.contains(Point(x, y)) or dist_to_boundary < 0.01, (
                f"Point ({x}, {y}) outside L-shape polygon"
            )


class TestFallbackDegenerate:
    """Degenerate or tiny polygons should fall back to centroid."""

    def test_tiny_polygon_returns_centroid(self):
        """A polygon with area < _MIN_POLYGON_AREA should return a centroid line."""
        tiny = Polygon([(0, 0), (0.1, 0), (0.1, 0.1), (0, 0.1)])
        axis = extract_medial_axis(tiny)
        coords = _extract_coords(axis)
        # Should return something (not crash)
        assert len(coords) >= 1

    def test_empty_polygon_returns_centroid(self):
        """An empty polygon should not crash."""
        empty = Polygon()
        axis = extract_medial_axis(empty)
        coords = _extract_coords(axis)
        assert len(coords) >= 1


# ── build_corridor_graph tests ────────────────────────────────


class TestBuildGraph:
    """Tests for the corridor graph construction."""

    def _make_room_data(self, rooms_config):
        """Helper to create room_data list from simple config."""
        room_data = []
        for cfg in rooms_config:
            poly = Polygon(cfg["points"])
            centroid = poly.centroid
            room_data.append({
                "poly": poly,
                "cx": centroid.x,
                "cy": centroid.y,
                "type": MagicMock(value=cfg["type"]),
            })
        return room_data

    def test_graph_connects_adjacent_rooms(self):
        """Adjacent rooms should have a path in the graph."""
        rooms_config = [
            {"points": [(0, 0), (5, 0), (5, 2), (0, 2)], "type": "corridor"},
            {"points": [(5, 0), (10, 0), (10, 2), (5, 2)], "type": "office"},
        ]
        room_data = self._make_room_data(rooms_config)
        adjacency = {0: [1], 1: [0]}

        G = build_corridor_graph([], room_data, adjacency)

        # Both rooms should have centroid nodes
        assert "room_0_centroid" in G.nodes
        assert "room_1_centroid" in G.nodes

        # There should be a path between them
        assert nx.has_path(G, "room_0_centroid", "room_1_centroid")

    def test_corridor_has_axis_nodes(self):
        """Corridor rooms should have medial axis nodes in addition to centroid."""
        rooms_config = [
            {"points": [(0, 0), (10, 0), (10, 2), (0, 2)], "type": "corridor"},
        ]
        room_data = self._make_room_data(rooms_config)
        adjacency = {0: []}

        G = build_corridor_graph([], room_data, adjacency)

        axis_nodes = [n for n in G.nodes if "axis" in n]
        assert len(axis_nodes) > 0, "Corridor should have medial axis nodes"

    def test_non_corridor_has_only_centroid(self):
        """Non-corridor rooms should have only a centroid node."""
        rooms_config = [
            {"points": [(0, 0), (5, 0), (5, 5), (0, 5)], "type": "office"},
        ]
        room_data = self._make_room_data(rooms_config)
        adjacency = {0: []}

        G = build_corridor_graph([], room_data, adjacency)

        room_0_nodes = [n for n in G.nodes if n.startswith("room_0")]
        assert len(room_0_nodes) == 1, "Office should have only centroid node"
        assert room_0_nodes[0] == "room_0_centroid"


# ── route_escape_path tests ──────────────────────────────────


class TestRouteEscapePath:
    """Tests for escape path routing through the graph."""

    def _make_simple_graph(self):
        """Create a simple 3-room graph: office -> corridor -> stairwell."""
        rooms_config = [
            {"points": [(0, 0), (5, 0), (5, 5), (0, 5)], "type": "office"},
            {"points": [(5, 0), (15, 0), (15, 2), (5, 2)], "type": "corridor"},
            {"points": [(15, 0), (20, 0), (20, 5), (15, 5)], "type": "stairwell"},
        ]
        room_data = []
        for cfg in rooms_config:
            poly = Polygon(cfg["points"])
            centroid = poly.centroid
            room_data.append({
                "poly": poly,
                "cx": centroid.x,
                "cy": centroid.y,
                "type": MagicMock(value=cfg["type"]),
            })
        adjacency = {0: [1], 1: [0, 2], 2: [1]}
        G = build_corridor_graph([], room_data, adjacency)
        return G

    def test_route_finds_path_to_exit(self):
        """Should find a path from office to stairwell."""
        G = self._make_simple_graph()
        waypoints = route_escape_path(G, source_room_idx=0, exit_room_indices=[2])

        assert len(waypoints) >= 2, "Path should have at least start and end"

        # First point near office centroid (2.5, 2.5)
        assert abs(waypoints[0][0] - 2.5) < 1.0
        assert abs(waypoints[0][1] - 2.5) < 1.0

        # Last point near stairwell centroid (17.5, 2.5)
        assert abs(waypoints[-1][0] - 17.5) < 1.0
        assert abs(waypoints[-1][1] - 2.5) < 1.0

    def test_route_waypoints_inside_corridor(self):
        """Intermediate waypoints should be inside corridor geometry."""
        G = self._make_simple_graph()
        waypoints = route_escape_path(G, source_room_idx=0, exit_room_indices=[2])

        # The corridor extends from x=5 to x=15, y=0 to y=2
        # Intermediate waypoints (not first/last) should pass through this area
        corridor_poly = Polygon([(5, 0), (15, 0), (15, 2), (5, 2)])
        from shapely.geometry import Point

        # At least some intermediate waypoints should be near/in the corridor
        if len(waypoints) > 2:
            corridor_adjacent = [
                wp for wp in waypoints[1:-1]
                if corridor_poly.buffer(2.0).contains(Point(wp[0], wp[1]))
            ]
            assert len(corridor_adjacent) > 0, "No waypoints near corridor"

    def test_disconnected_graph_returns_empty(self):
        """Disconnected source and exit should return empty waypoints."""
        G = nx.Graph()
        G.add_node("room_0_centroid", x=0, y=0, room_idx=0)
        G.add_node("room_1_centroid", x=100, y=100, room_idx=1)
        # No edges — disconnected

        waypoints = route_escape_path(G, source_room_idx=0, exit_room_indices=[1])
        assert waypoints == [], "Disconnected graph should return empty path"

    def test_missing_source_returns_empty(self):
        """Non-existent source room should return empty."""
        G = nx.Graph()
        G.add_node("room_0_centroid", x=0, y=0, room_idx=0)

        waypoints = route_escape_path(G, source_room_idx=99, exit_room_indices=[0])
        assert waypoints == []


# ── Helpers ──────────────────────────────────────────────────


def _extract_coords(geom) -> list[tuple[float, float]]:
    """Extract all coordinate pairs from a LineString or MultiLineString."""
    coords = []
    if isinstance(geom, MultiLineString):
        for line in geom.geoms:
            coords.extend(list(line.coords))
    elif isinstance(geom, LineString):
        coords.extend(list(geom.coords))
    return coords
