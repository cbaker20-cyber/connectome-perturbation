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


def toy_graph_payload() -> dict[str, object]:
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
