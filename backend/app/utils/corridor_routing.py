"""Corridor centerline routing for DIN 14095 escape paths.

Uses scipy Voronoi diagrams to extract medial axes (centerlines) of corridor
polygons, then builds a NetworkX graph for shortest-path escape routing.
Voronoi ridges from densified boundary points naturally trace the geometric
center of elongated polygons like corridors and hallways.
"""

import logging
import math

import networkx as nx
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import linemerge

logger = logging.getLogger(__name__)

# Minimum area for medial axis extraction (skip degenerate polygons)
_MIN_POLYGON_AREA = 0.5
# Maximum spacing between boundary sample points (in plan units)
_BOUNDARY_SAMPLE_SPACING = 1.0
# Minimum number of boundary samples for Voronoi
_MIN_BOUNDARY_SAMPLES = 10


def extract_medial_axis(polygon: Polygon, sample_spacing: float = _BOUNDARY_SAMPLE_SPACING) -> LineString | MultiLineString:
    """Extract the medial axis (centerline) of a polygon using Voronoi ridges.

    Densifies the polygon boundary, feeds points into scipy.spatial.Voronoi,
    and keeps only ridges whose BOTH endpoints lie inside the polygon.
    These interior ridges form the medial axis / skeleton of the polygon.

    Args:
        polygon: A Shapely polygon (typically a corridor or hallway).
        sample_spacing: Distance between boundary sample points.

    Returns:
        LineString or MultiLineString representing the centerline.
        Falls back to a LineString through the centroid if extraction fails.
    """
    if not polygon.is_valid or polygon.is_empty or polygon.area < _MIN_POLYGON_AREA:
        if polygon.is_empty:
            return LineString([(0, 0), (0, 0)])
        centroid = polygon.centroid
        if centroid.is_empty:
            return LineString([(0, 0), (0, 0)])
        return LineString([(centroid.x, centroid.y), (centroid.x, centroid.y)])

    # Densify boundary: sample points along the polygon perimeter
    boundary = polygon.boundary
    perimeter = boundary.length
    if perimeter <= 0:
        centroid = polygon.centroid
        return LineString([(centroid.x, centroid.y), (centroid.x, centroid.y)])

    n_samples = max(_MIN_BOUNDARY_SAMPLES, int(perimeter / sample_spacing))
    boundary_points = []
    for i in range(n_samples):
        pt = boundary.interpolate(i / n_samples, normalized=True)
        boundary_points.append((pt.x, pt.y))

    boundary_arr = np.array(boundary_points)

    # Compute Voronoi diagram from boundary points
    try:
        vor = Voronoi(boundary_arr)
    except Exception:
        logger.warning("Voronoi computation failed for polygon, using centroid fallback")
        centroid = polygon.centroid
        return LineString([(centroid.x, centroid.y), (centroid.x, centroid.y)])

    # Filter ridges: keep only those with BOTH vertices inside the polygon
    interior_segments = []
    vertices = vor.vertices

    for ridge_vertices in vor.ridge_vertices:
        # Skip ridges extending to infinity (indicated by -1)
        if -1 in ridge_vertices:
            continue
        v0_idx, v1_idx = ridge_vertices
        v0 = vertices[v0_idx]
        v1 = vertices[v1_idx]
        p0 = Point(v0[0], v0[1])
        p1 = Point(v1[0], v1[1])

        # Both endpoints must be inside the polygon
        if polygon.contains(p0) and polygon.contains(p1):
            interior_segments.append(LineString([v0, v1]))

    if not interior_segments:
        # No interior ridges found — use centroid
        logger.debug("No interior Voronoi ridges for polygon, using centroid")
        centroid = polygon.centroid
        return LineString([(centroid.x, centroid.y), (centroid.x, centroid.y)])

    # Merge segments into connected lines
    merged = linemerge(MultiLineString(interior_segments))
    return merged


def _nearest_boundary_point(poly_a: Polygon, poly_b: Polygon) -> tuple[float, float]:
    """Find the midpoint of the closest approach between two polygon boundaries.

    Returns the midpoint between the nearest points on the two boundaries,
    which serves as the connection point between adjacent rooms.
    """
    # Use Shapely's nearest_points for efficiency
    from shapely.ops import nearest_points

    p1, p2 = nearest_points(poly_a.boundary, poly_b.boundary)
    return ((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)


def build_corridor_graph(
    rooms: list,
    room_data: list[dict | None],
    adjacency: dict[int, list[int]],
    corridor_types: set[str] | None = None,
) -> nx.Graph:
    """Build a weighted graph for escape route pathfinding.

    - Corridor/lobby rooms get medial axis edges (centerline waypoints).
    - Non-corridor rooms get a single node at their centroid.
    - Adjacent rooms are connected at their shared boundary midpoint.

    Args:
        rooms: List of RoomPolygon objects.
        room_data: Parallel list of dicts with 'poly', 'cx', 'cy', 'type' keys (or None).
        adjacency: Dict mapping room index -> list of adjacent room indices.
        corridor_types: Set of room type strings considered corridors.
                        Defaults to {"corridor", "lobby"}.

    Returns:
        A NetworkX weighted undirected graph.
    """
    if corridor_types is None:
        corridor_types = {"corridor", "lobby"}

    G = nx.Graph()

    # Add nodes and medial axis edges for each room
    for i, rd in enumerate(room_data):
        if rd is None:
            continue

        centroid_node = f"room_{i}_centroid"
        G.add_node(centroid_node, x=rd["cx"], y=rd["cy"], room_idx=i)

        room_type_str = rd["type"].value if hasattr(rd["type"], "value") else str(rd["type"])

        if room_type_str in corridor_types:
            # Extract medial axis for corridor rooms
            try:
                axis = extract_medial_axis(rd["poly"])
                _add_medial_axis_edges(G, i, axis, rd["cx"], rd["cy"])
            except Exception:
                logger.debug(f"Medial axis extraction failed for room {i}, using centroid only")
        # Non-corridor rooms just have the centroid node (already added)

    # Connect adjacent rooms at boundary midpoints
    connected_pairs = set()
    for i, neighbors in adjacency.items():
        if room_data[i] is None:
            continue
        for j in neighbors:
            if room_data[j] is None:
                continue
            pair = (min(i, j), max(i, j))
            if pair in connected_pairs:
                continue
            connected_pairs.add(pair)

            # Find connection point between rooms
            try:
                mid_x, mid_y = _nearest_boundary_point(room_data[i]["poly"], room_data[j]["poly"])
            except Exception:
                # Fallback: midpoint of centroids
                mid_x = (room_data[i]["cx"] + room_data[j]["cx"]) / 2
                mid_y = (room_data[i]["cy"] + room_data[j]["cy"]) / 2

            conn_node = f"conn_{pair[0]}_{pair[1]}"
            G.add_node(conn_node, x=mid_x, y=mid_y)

            # Connect to nearest node in each room's subgraph
            _connect_to_nearest(G, i, conn_node, mid_x, mid_y)
            _connect_to_nearest(G, j, conn_node, mid_x, mid_y)

    return G


def _add_medial_axis_edges(
    G: nx.Graph, room_idx: int, axis: LineString | MultiLineString,
    cx: float, cy: float,
) -> None:
    """Add medial axis line segments as graph edges for a corridor room.

    After adding all segments, merges nodes that are very close together
    (same Voronoi vertex appearing in different line segments).
    """
    lines = []
    if isinstance(axis, MultiLineString):
        lines = list(axis.geoms)
    elif isinstance(axis, LineString):
        lines = [axis]
    else:
        return

    centroid_node = f"room_{room_idx}_centroid"
    node_counter = 0
    # Track all axis nodes for post-processing
    all_axis_nodes = []

    for line in lines:
        coords = list(line.coords)
        if len(coords) < 2:
            continue

        prev_node = None
        for k, (x, y) in enumerate(coords):
            # Check if an existing node is at (nearly) the same position
            existing = _find_nearby_node(G, all_axis_nodes, x, y, threshold=0.01)
            if existing is not None:
                node_name = existing
            else:
                node_name = f"room_{room_idx}_axis_{node_counter}"
                node_counter += 1
                G.add_node(node_name, x=x, y=y, room_idx=room_idx)
                all_axis_nodes.append(node_name)

            if prev_node is not None and prev_node != node_name:
                px, py = G.nodes[prev_node]["x"], G.nodes[prev_node]["y"]
                dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
                if not G.has_edge(prev_node, node_name):
                    G.add_edge(prev_node, node_name, weight=dist)

            prev_node = node_name

    # Connect centroid to the nearest axis node
    if all_axis_nodes:
        nearest = min(all_axis_nodes, key=lambda n: math.sqrt(
            (G.nodes[n]["x"] - cx) ** 2 + (G.nodes[n]["y"] - cy) ** 2
        ))
        dist = math.sqrt(
            (G.nodes[nearest]["x"] - cx) ** 2 + (G.nodes[nearest]["y"] - cy) ** 2
        )
        G.add_edge(centroid_node, nearest, weight=dist)


def _find_nearby_node(
    G: nx.Graph, nodes: list[str], x: float, y: float, threshold: float = 0.01,
) -> str | None:
    """Find an existing node within threshold distance of (x, y)."""
    for n in nodes:
        nx_val = G.nodes[n]["x"]
        ny_val = G.nodes[n]["y"]
        if math.sqrt((nx_val - x) ** 2 + (ny_val - y) ** 2) < threshold:
            return n
    return None


def _connect_to_nearest(G: nx.Graph, room_idx: int, conn_node: str, cx: float, cy: float) -> None:
    """Connect a boundary connection node to the nearest node in a room's subgraph."""
    room_nodes = [
        n for n in G.nodes
        if G.nodes[n].get("room_idx") == room_idx
    ]
    if not room_nodes:
        # Fallback: connect to centroid
        centroid_node = f"room_{room_idx}_centroid"
        if centroid_node in G.nodes:
            room_nodes = [centroid_node]
        else:
            return

    nearest = min(room_nodes, key=lambda n: math.sqrt(
        (G.nodes[n]["x"] - cx) ** 2 + (G.nodes[n]["y"] - cy) ** 2
    ))
    dist = math.sqrt(
        (G.nodes[nearest]["x"] - cx) ** 2 + (G.nodes[nearest]["y"] - cy) ** 2
    )
    G.add_edge(conn_node, nearest, weight=dist)


def route_escape_path(
    G: nx.Graph,
    source_room_idx: int,
    exit_room_indices: list[int],
) -> list[tuple[float, float]]:
    """Find the shortest escape path from a source room to the nearest exit.

    Uses Dijkstra shortest path (weighted by distance) through the corridor
    graph. Returns waypoint coordinates that follow corridor centerlines.

    Args:
        G: The corridor graph from build_corridor_graph().
        source_room_idx: Index of the room to route FROM.
        exit_room_indices: Indices of rooms considered exits (stairwells, lobbies).

    Returns:
        List of (x, y) waypoint coordinates along the path.
        Empty list if no path exists (disconnected graph).
    """
    source_node = f"room_{source_room_idx}_centroid"
    if source_node not in G:
        return []

    # Find shortest path to any exit
    best_path = None
    best_length = float("inf")

    for exit_idx in exit_room_indices:
        exit_node = f"room_{exit_idx}_centroid"
        if exit_node not in G:
            continue
        try:
            path = nx.shortest_path(G, source_node, exit_node, weight="weight")
            length = nx.shortest_path_length(G, source_node, exit_node, weight="weight")
            if length < best_length:
                best_path = path
                best_length = length
        except nx.NetworkXNoPath:
            continue

    if best_path is None:
        return []

    # Extract (x, y) coordinates from path nodes
    waypoints = []
    for node in best_path:
        x = G.nodes[node]["x"]
        y = G.nodes[node]["y"]
        waypoints.append((x, y))

    # Simplify: remove consecutive duplicate or near-duplicate points
    if len(waypoints) > 2:
        simplified = [waypoints[0]]
        for wp in waypoints[1:]:
            prev = simplified[-1]
            dist = math.sqrt((wp[0] - prev[0]) ** 2 + (wp[1] - prev[1]) ** 2)
            if dist > 0.1:  # Skip near-duplicates
                simplified.append(wp)
        if simplified[-1] != waypoints[-1]:
            simplified.append(waypoints[-1])
        waypoints = simplified

    return waypoints
