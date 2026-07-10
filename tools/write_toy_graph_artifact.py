#!/usr/bin/env python3
"""Write a deterministic toy graph artifact with known expected outcomes.

This artifact is intentionally synthetic. It exercises graph-analysis and
provenance plumbing without making any claim about fly connectome data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOY_NODES = ["sensory_a", "interneuron_b", "motor_c", "isolated_d"]
TOY_EDGES = [
    {
        "source": "sensory_a",
        "target": "interneuron_b",
        "kind": "fixture_edge",
    },
    {
        "source": "interneuron_b",
        "target": "motor_c",
        "kind": "fixture_edge",
    },
    {
        "source": "sensory_a",
        "target": "motor_c",
        "kind": "shortcut_fixture_edge",
    },
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_repo_relative_path(root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        raise ValueError(f"output path must be repo-relative: {raw_path}")

    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"output path escapes repository: {raw_path}") from exc

    return resolved


def degree_maps(nodes: list[str], edges: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    in_degree = {node: 0 for node in nodes}
    out_degree = {node: 0 for node in nodes}

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        out_degree[source] += 1
        in_degree[target] += 1

    return {"in_degree": in_degree, "out_degree": out_degree}


def reachable_from(start: str, edges: list[dict[str, str]]) -> list[str]:
    adjacency: dict[str, list[str]] = {node: [] for node in TOY_NODES}
    for edge in edges:
        adjacency[edge["source"]].append(edge["target"])

    seen = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        for target in adjacency[node]:
            if target not in seen:
                seen.add(target)
                stack.append(target)

    return sorted(seen)


def weak_component_count(nodes: list[str], edges: list[dict[str, str]]) -> int:
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        adjacency[source].add(target)
        adjacency[target].add(source)

    seen: set[str] = set()
    components = 0
    for node in nodes:
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


def toy_graph_payload() -> dict[str, object]:
    degrees = degree_maps(TOY_NODES, TOY_EDGES)
    return {
        "artifact_type": "toy_graph_expected_outcomes",
        "claim_status": "not_interpretable_as_neuroscience",
        "graph": {
            "directed": True,
            "nodes": TOY_NODES,
            "edges": TOY_EDGES,
        },
        "non_claims": [
            "This is not FlyWire data.",
            "This is not a biological connectome result.",
            "This artifact only validates deterministic graph/provenance plumbing.",
        ],
        "purpose": "Exercise deterministic graph-analysis artifact generation before real connectome experiments.",
        "schema_version": "0.1",
        "expected_metrics": {
            "edge_count": len(TOY_EDGES),
            "in_degree": degrees["in_degree"],
            "node_count": len(TOY_NODES),
            "out_degree": degrees["out_degree"],
            "reachable_from_sensory_a": reachable_from("sensory_a", TOY_EDGES),
            "weak_component_count": weak_component_count(TOY_NODES, TOY_EDGES),
        },
    }


def write_toy_graph_artifact(output: str) -> Path:
    root = repo_root()
    output_path = resolve_repo_relative_path(root, output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(toy_graph_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a deterministic toy graph expected-outcomes artifact."
    )
    parser.add_argument(
        "--output",
        default="results/toy_graph_artifact.json",
        help="Repo-relative JSON output path.",
    )
    args = parser.parse_args(argv)

    try:
        output_path = write_toy_graph_artifact(args.output)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(output_path.relative_to(repo_root()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
