#!/usr/bin/env python3
"""Write a deterministic toy graph artifact with known expected outcomes.

This artifact is intentionally synthetic. It exercises graph-analysis,
known-answer lesion scoring, and provenance plumbing without making any claim
about fly connectome data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from connectome_analysis.graph_metrics import expected_graph_metrics

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

LESION_SOURCE = "9007199254740993"
LESION_TARGET = "toy_output"
EXPECTED_CRITICAL_NODE = "critical_relay"
EXPECTED_CRITICAL_EDGE = ("critical_relay", LESION_TARGET)
EXPECTED_MISLEADING_HUB = "structural_hub"
LESION_NODES = [
    LESION_SOURCE,
    EXPECTED_CRITICAL_NODE,
    LESION_TARGET,
    EXPECTED_MISLEADING_HUB,
    "dead_end_a",
    "dead_end_b",
    "dead_end_c",
]
LESION_EDGES = [
    {"source": LESION_SOURCE, "target": EXPECTED_CRITICAL_NODE},
    {"source": EXPECTED_CRITICAL_NODE, "target": LESION_TARGET},
    {"source": LESION_SOURCE, "target": EXPECTED_MISLEADING_HUB},
    {"source": EXPECTED_MISLEADING_HUB, "target": "dead_end_a"},
    {"source": EXPECTED_MISLEADING_HUB, "target": "dead_end_b"},
    {"source": EXPECTED_MISLEADING_HUB, "target": "dead_end_c"},
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


def target_is_reachable(
    nodes: list[str],
    edges: list[dict[str, str]],
    source: str,
    target: str,
    *,
    removed_node: str | None = None,
    removed_edge: tuple[str, str] | None = None,
) -> bool:
    """Return whether target is reachable after one synthetic lesion."""
    if removed_node in {source, target}:
        return False

    adjacency = {node: [] for node in nodes if node != removed_node}
    for edge in edges:
        edge_key = (edge["source"], edge["target"])
        if removed_edge == edge_key:
            continue
        if removed_node in edge_key:
            continue
        adjacency[edge["source"]].append(edge["target"])

    seen = {source}
    stack = [source]
    while stack:
        current = stack.pop()
        if current == target:
            return True
        for neighbor in sorted(adjacency.get(current, []), reverse=True):
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return False


def toy_lesion_scores() -> dict[str, object]:
    """Compute deterministic binary target-reachability loss scores."""
    baseline_reachable = target_is_reachable(
        LESION_NODES,
        LESION_EDGES,
        LESION_SOURCE,
        LESION_TARGET,
    )
    if not baseline_reachable:
        raise ValueError("toy lesion fixture baseline target must be reachable")

    node_scores = {
        node: int(
            not target_is_reachable(
                LESION_NODES,
                LESION_EDGES,
                LESION_SOURCE,
                LESION_TARGET,
                removed_node=node,
            )
        )
        for node in LESION_NODES
        if node not in {LESION_SOURCE, LESION_TARGET}
    }
    edge_scores = {
        f"{edge['source']}->{edge['target']}": int(
            not target_is_reachable(
                LESION_NODES,
                LESION_EDGES,
                LESION_SOURCE,
                LESION_TARGET,
                removed_edge=(edge["source"], edge["target"]),
            )
        )
        for edge in LESION_EDGES
    }
    out_degree = {
        node: sum(edge["source"] == node for edge in LESION_EDGES)
        for node in LESION_NODES
    }

    return {
        "baseline_target_reachable": baseline_reachable,
        "edge_scores": edge_scores,
        "node_scores": node_scores,
        "out_degree": out_degree,
        "score_definition": "1 when a single lesion removes source-to-target reachability; otherwise 0",
    }


def toy_graph_payload() -> dict[str, object]:
    return {
        "artifact_type": "toy_graph_expected_outcomes",
        "claim_status": "not_interpretable_as_neuroscience",
        "graph": {
            "directed": True,
            "nodes": TOY_NODES,
            "edges": TOY_EDGES,
        },
        "lesion_fixture": {
            "directed": True,
            "nodes": LESION_NODES,
            "edges": LESION_EDGES,
            "source": LESION_SOURCE,
            "target": LESION_TARGET,
            "expected_critical_node": EXPECTED_CRITICAL_NODE,
            "expected_critical_edge": list(EXPECTED_CRITICAL_EDGE),
            "expected_misleading_hub": EXPECTED_MISLEADING_HUB,
            "expected_scores": toy_lesion_scores(),
        },
        "non_claims": [
            "This is not FlyWire data.",
            "This is not a biological connectome result.",
            "This artifact only validates deterministic graph/provenance plumbing and toy scoring logic.",
        ],
        "purpose": "Exercise deterministic graph-analysis artifact generation before real connectome experiments.",
        "schema_version": "0.2",
        "expected_metrics": expected_graph_metrics(
            TOY_NODES,
            TOY_EDGES,
            reachability_start="sensory_a",
        ),
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
