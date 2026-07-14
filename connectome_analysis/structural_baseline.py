"""Compute dependency-free structural metrics for synthetic directed graphs.

These statistics describe only repository-local fixtures. They are not evidence
of neural function, biological importance, vulnerability, behavior, or causality.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

METRICS = [
    "in_degree",
    "out_degree",
    "weighted_in_degree",
    "weighted_out_degree",
    "weighted_degree",
]


def _validated_nodes(nodes: Sequence[str]) -> list[str]:
    result = list(nodes)
    if not result:
        raise ValueError("nodes must be non-empty")
    if any(not isinstance(node, str) or not node for node in result):
        raise ValueError("nodes must contain only non-empty strings")
    if len(set(result)) != len(result):
        raise ValueError("nodes must not contain duplicates")
    return result


def build_structural_baseline_table(
    nodes: Sequence[str], edges: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    """Return deterministic degree statistics without mutating caller inputs."""
    node_ids = _validated_nodes(nodes)
    known = set(node_ids)
    totals = {
        node_id: {
            "in_degree": 0,
            "out_degree": 0,
            "weighted_in_degree": 0.0,
            "weighted_out_degree": 0.0,
        }
        for node_id in node_ids
    }

    for index, edge in enumerate(edges):
        if not isinstance(edge, Mapping):
            raise ValueError(f"edges[{index}] must be an object")
        if set(edge) != {"source", "target", "weight"}:
            raise ValueError(f"edges[{index}] must contain exactly source, target, and weight")
        source = edge["source"]
        target = edge["target"]
        weight = edge["weight"]
        if not isinstance(source, str) or not source or source not in known:
            raise ValueError(f"edges[{index}].source must be a known non-empty string")
        if not isinstance(target, str) or not target or target not in known:
            raise ValueError(f"edges[{index}].target must be a known non-empty string")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise ValueError(f"edges[{index}].weight must be a finite non-negative number")
        number = float(weight)
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"edges[{index}].weight must be a finite non-negative number")

        totals[source]["out_degree"] += 1
        totals[target]["in_degree"] += 1
        totals[source]["weighted_out_degree"] += number
        totals[target]["weighted_in_degree"] += number

    rows = []
    for node_id in node_ids:
        values = totals[node_id]
        rows.append(
            {
                "node_id": node_id,
                "in_degree": values["in_degree"],
                "out_degree": values["out_degree"],
                "weighted_in_degree": values["weighted_in_degree"],
                "weighted_out_degree": values["weighted_out_degree"],
                "weighted_degree": values["weighted_in_degree"] + values["weighted_out_degree"],
            }
        )

    return {
        "schema_version": "atlas-structural-baseline-table/v0",
        "artifact_type": "synthetic_structural_baseline_table",
        "claim_status": "not_interpretable_as_neuroscience",
        "node_ids": node_ids,
        "metrics": list(METRICS),
        "rows": rows,
        "limitations": [
            "Degree statistics describe only the supplied synthetic edge table.",
            "High degree is not equivalent to functional importance or biological vulnerability.",
            "This artifact does not establish neural dynamics, behavior, mechanism, or causality.",
        ],
    }
