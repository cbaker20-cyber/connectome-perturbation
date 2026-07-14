"""Deterministic node-removal scoring for synthetic graph fixtures only.

The values produced here are numerical bookkeeping for known-answer tests. They
must not be interpreted as neural activity, biological lesions, or behavior.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence

from connectome_analysis.toy_signal import propagate_toy_signal

Edge = Mapping[str, object]


def _finite_vector(values: Sequence[float], *, name: str) -> list[float]:
    if not values:
        raise ValueError(f"{name} must be non-empty")
    result: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name}[{index}] must be a finite number")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{name}[{index}] must be a finite number")
        result.append(number)
    return result


def compare_output_vectors(
    baseline: Sequence[float], perturbed: Sequence[float]
) -> dict[str, float]:
    """Return contract-defined percent change and cosine distance.

    Zero L1 baseline magnitude or a zero vector norm is rejected rather than
    assigned an undocumented sentinel value. Cosine similarity is clamped to
    its mathematical range to absorb floating-point roundoff at the boundaries.
    """
    baseline_values = _finite_vector(baseline, name="baseline")
    perturbed_values = _finite_vector(perturbed, name="perturbed")
    if len(baseline_values) != len(perturbed_values):
        raise ValueError("baseline and perturbed vectors must have equal length")

    baseline_l1 = sum(abs(value) for value in baseline_values)
    if baseline_l1 == 0.0:
        raise ValueError("baseline vector L1 magnitude must be non-zero")

    baseline_norm = math.sqrt(sum(value * value for value in baseline_values))
    perturbed_norm = math.sqrt(sum(value * value for value in perturbed_values))
    if baseline_norm == 0.0 or perturbed_norm == 0.0:
        raise ValueError("cosine distance requires non-zero vector norms")

    percent_change = 100.0 * sum(
        abs(perturbed - base)
        for base, perturbed in zip(baseline_values, perturbed_values, strict=True)
    ) / baseline_l1
    cosine_similarity = sum(
        base * perturbed
        for base, perturbed in zip(baseline_values, perturbed_values, strict=True)
    ) / (baseline_norm * perturbed_norm)
    cosine_distance = 1.0 - max(-1.0, min(1.0, cosine_similarity))

    if not math.isfinite(percent_change) or not math.isfinite(cosine_distance):
        raise ValueError("comparison metrics must be finite")
    return {
        "percent_output_change": percent_change,
        "cosine_distance": cosine_distance,
    }


def score_node_lesions(
    nodes: Iterable[str],
    edges: Iterable[Edge],
    input_values: Mapping[str, float],
    output_ids: Sequence[str],
    target_ids: Sequence[str],
    *,
    steps: int,
    decay: float = 1.0,
    seed: int = 0,
    graph_id: str = "synthetic_fixture",
) -> dict[str, object]:
    """Score one-at-a-time node removals without mutating caller inputs."""
    node_list = list(nodes)
    edge_list = [dict(edge) for edge in edges]
    inputs = dict(input_values)
    outputs = list(output_ids)
    targets = list(target_ids)

    if len(set(targets)) != len(targets):
        raise ValueError("target_ids must be unique")
    node_set = set(node_list)
    for target in targets:
        if not isinstance(target, str) or target not in node_set:
            raise ValueError(f"target node is not in nodes: {target}")
        if target in inputs:
            raise ValueError(f"cannot remove fixed input node: {target}")
        if target in outputs:
            raise ValueError(f"cannot remove requested output node: {target}")

    baseline = propagate_toy_signal(
        node_list,
        edge_list,
        inputs,
        outputs,
        steps=steps,
        decay=decay,
        seed=seed,
    )

    rows: list[dict[str, object]] = []
    for target in targets:
        perturbed_nodes = [node for node in node_list if node != target]
        perturbed_edges = [
            edge
            for edge in edge_list
            if edge.get("source") != target and edge.get("target") != target
        ]
        perturbed = propagate_toy_signal(
            perturbed_nodes,
            perturbed_edges,
            inputs,
            outputs,
            steps=steps,
            decay=decay,
            seed=seed,
        )
        metrics = compare_output_vectors(baseline, perturbed)
        rows.append(
            {
                "target_id": target,
                "baseline_output_vector": list(baseline),
                "perturbed_output_vector": perturbed,
                **metrics,
            }
        )

    rows.sort(
        key=lambda row: (
            -float(row["percent_output_change"]),
            -float(row["cosine_distance"]),
            str(row["target_id"]),
        )
    )
    return {
        "schema_version": "atlas-node-lesion-table/v0",
        "artifact_type": "synthetic_node_lesion_scores",
        "claim_status": "not_interpretable_as_neuroscience",
        "graph_id": graph_id,
        "input_ids": list(inputs),
        "output_ids": outputs,
        "parameters": {"decay": float(decay), "seed": seed, "steps": steps},
        "baseline_output_vector": list(baseline),
        "rows": rows,
        "limitations": [
            "Synthetic graph fixture only.",
            "Propagation values are not neural activity or behavior.",
            "Node removal scores do not establish biological vulnerability or causality.",
        ],
    }
