"""Deterministic connection-removal scoring for synthetic graph fixtures only.

The values produced here are numerical bookkeeping for known-answer tests. They
must not be interpreted as neural activity, synaptic effects, or behavior.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from connectome_analysis.node_lesion import compare_output_vectors
from connectome_analysis.toy_signal import propagate_toy_signal

Edge = Mapping[str, object]
TargetEdge = Sequence[str]


def _edge_pair(edge: Edge, *, index: int) -> tuple[str, str]:
    source = edge.get("source")
    target = edge.get("target")
    if not isinstance(source, str) or not source:
        raise ValueError(f"edges[{index}].source must be a non-empty string")
    if not isinstance(target, str) or not target:
        raise ValueError(f"edges[{index}].target must be a non-empty string")
    return source, target


def _target_pair(value: TargetEdge, *, index: int) -> tuple[str, str]:
    if isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError(f"target_edges[{index}] must contain exactly source and target")
    source, target = value
    if not isinstance(source, str) or not source:
        raise ValueError(f"target_edges[{index}].source must be a non-empty string")
    if not isinstance(target, str) or not target:
        raise ValueError(f"target_edges[{index}].target must be a non-empty string")
    return source, target


def score_connection_lesions(
    nodes: Iterable[str],
    edges: Iterable[Edge],
    input_values: Mapping[str, float],
    output_ids: Sequence[str],
    target_edges: Sequence[TargetEdge],
    *,
    steps: int,
    decay: float = 1.0,
    seed: int = 0,
    graph_id: str = "synthetic_fixture",
) -> dict[str, object]:
    """Score one-at-a-time directed-edge removals without mutating inputs."""
    node_list = list(nodes)
    edge_list = [dict(edge) for edge in edges]
    inputs = dict(input_values)
    outputs = list(output_ids)
    targets = [_target_pair(value, index=index) for index, value in enumerate(target_edges)]

    if len(set(targets)) != len(targets):
        raise ValueError("target_edges must be unique")

    edge_pairs = [_edge_pair(edge, index=index) for index, edge in enumerate(edge_list)]
    if len(set(edge_pairs)) != len(edge_pairs):
        raise ValueError("parallel edges with the same source and target are ambiguous")

    edge_pair_set = set(edge_pairs)
    for source, target in targets:
        if (source, target) not in edge_pair_set:
            raise ValueError(f"target edge is not in edges: {source} -> {target}")

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
    for source, target in targets:
        perturbed_edges = [
            edge
            for edge in edge_list
            if (edge.get("source"), edge.get("target")) != (source, target)
        ]
        perturbed = propagate_toy_signal(
            node_list,
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
                "source_id": source,
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
            str(row["source_id"]),
            str(row["target_id"]),
        )
    )
    return {
        "schema_version": "atlas-connection-lesion-table/v0",
        "artifact_type": "synthetic_connection_lesion_scores",
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
            "Connection removal scores do not establish synaptic effects, biological vulnerability, or causality.",
        ],
    }
