"""Geometry utility functions for floor plan processing."""

import math

from shapely.geometry import LineString, Point, Polygon


def line_angle(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate the angle of a line segment in degrees (0-360)."""
    return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 360


def is_horizontal(x1: float, y1: float, x2: float, y2: float, tolerance: float = 5.0) -> bool:
    """Check if a line segment is approximately horizontal."""
    angle = line_angle(x1, y1, x2, y2)
    return angle < tolerance or abs(angle - 180) < tolerance or abs(angle - 360) < tolerance


def is_vertical(x1: float, y1: float, x2: float, y2: float, tolerance: float = 5.0) -> bool:
    """Check if a line segment is approximately vertical."""
    angle = line_angle(x1, y1, x2, y2)
    return abs(angle - 90) < tolerance or abs(angle - 270) < tolerance


def point_to_line_distance(px: float, py: float, line: LineString) -> float:
    """Calculate the distance from a point to a line."""
    return Point(px, py).distance(line)


def polygon_aspect_ratio(polygon: Polygon) -> float:
    """Calculate the aspect ratio of a polygon's bounding box."""
    minx, miny, maxx, maxy = polygon.bounds
    width = maxx - minx
    height = maxy - miny
    if min(width, height) == 0:
        return float("inf")
    return max(width, height) / min(width, height)


def simplify_polygon(polygon: Polygon, tolerance: float = 0.1) -> Polygon:
    """Simplify a polygon by removing unnecessary vertices."""
    simplified = polygon.simplify(tolerance, preserve_topology=True)
    if isinstance(simplified, Polygon) and simplified.is_valid:
        return simplified
    return polygon
