"""Small deterministic graph-metric helpers for fixture validation.

These helpers intentionally avoid scientific interpretation. They are pure graph
plumbing that can be tested on toy fixtures before baseline/perturbation code is
trusted on real connectome inputs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

Edge = Mapping[str, str]


def degree_maps(nodes: Iterable[str], edges: Iterable[Edge]) -> dict[str, dict[str, int]]:
    """Return in/out degree maps for a directed edge list."""
    node_list = list(nodes)
    in_degree = {node: 0 for node in node_list}
    out_degree = {node: 0 for node in node_list}

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source not in out_degree:
            raise ValueError(f"edge source is not in nodes: {source}")
        if target not in in_degree:
            raise ValueError(f"edge target is not in nodes: {target}")
        out_degree[source] += 1
        in_degree[target] += 1

    return {"in_degree": in_degree, "out_degree": out_degree}


def reachable_from(start: str, nodes: Iterable[str], edges: Iterable[Edge]) -> list[str]:
    """Return sorted nodes reachable from start, including start."""
    node_list = list(nodes)
    if start not in node_list:
        raise ValueError(f"start node is not in nodes: {start}")

    adjacency: dict[str, list[str]] = {node: [] for node in node_list}
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source not in adjacency:
            raise ValueError(f"edge source is not in nodes: {source}")
        if target not in adjacency:
            raise ValueError(f"edge target is not in nodes: {target}")
        adjacency[source].append(target)

    seen = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        for target in adjacency[node]:
            if target not in seen:
                seen.add(target)
                stack.append(target)

    return sorted(seen)


def weak_component_count(nodes: Iterable[str], edges: Iterable[Edge]) -> int:
    """Return the number of weakly connected components in a directed graph."""
    node_list = list(nodes)
    adjacency: dict[str, set[str]] = {node: set() for node in node_list}
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source not in adjacency:
            raise ValueError(f"edge source is not in nodes: {source}")
        if target not in adjacency:
            raise ValueError(f"edge target is not in nodes: {target}")
        adjacency[source].add(target)
        adjacency[target].add(source)

    seen: set[str] = set()
    components = 0
    for node in node_list:
        if node in seen:
            continue
        components += 1
        stack = [node]
        seen.add(node)
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)

    return components


def expected_graph_metrics(nodes: Iterable[str], edges: Iterable[Edge], *, reachability_start: str) -> dict[str, object]:
    """Compute the deterministic metric bundle used by toy artifacts/tests."""
    node_list = list(nodes)
    edge_list = list(edges)
    degrees = degree_maps(node_list, edge_list)
    return {
        "edge_count": len(edge_list),
        "in_degree": degrees["in_degree"],
        "node_count": len(node_list),
        "out_degree": degrees["out_degree"],
        f"reachable_from_{reachability_start}": reachable_from(reachability_start, node_list, edge_list),
        "weak_component_count": weak_component_count(node_list, edge_list),
    }
