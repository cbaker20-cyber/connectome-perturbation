"""Deterministic signal propagation for synthetic graph fixtures only.

This module is intentionally dependency-free and is not a neural simulator. Its
outputs are bookkeeping values for known-answer tests, not neural activity or
behavior.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence

Edge = Mapping[str, object]


def _finite_number(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def propagate_toy_signal(
    nodes: Iterable[str],
    edges: Iterable[Edge],
    input_values: Mapping[str, float],
    output_ids: Sequence[str],
    *,
    steps: int,
    decay: float = 1.0,
    seed: int = 0,
) -> list[float]:
    """Return output values after synchronous deterministic propagation.

    At each step, the fixed input drive is re-applied and incoming weighted
    values from the previous state are multiplied by ``decay``. ``seed`` is
    accepted and validated for run-record compatibility; this deterministic
    baseline does not consume randomness.
    """
    node_list = list(nodes)
    if not node_list or any(not isinstance(node, str) or not node for node in node_list):
        raise ValueError("nodes must be non-empty strings")
    if len(set(node_list)) != len(node_list):
        raise ValueError("nodes must be unique")
    node_set = set(node_list)

    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("steps must be a non-negative integer")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    decay_value = _finite_number(decay, name="decay")

    fixed_inputs = {node: 0.0 for node in node_list}
    for node, value in input_values.items():
        if node not in node_set:
            raise ValueError(f"input node is not in nodes: {node}")
        fixed_inputs[node] = _finite_number(value, name=f"input value for {node}")

    for output_id in output_ids:
        if output_id not in node_set:
            raise ValueError(f"output node is not in nodes: {output_id}")

    edge_list: list[tuple[str, str, float]] = []
    for index, edge in enumerate(edges):
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_set:
            raise ValueError(f"edge {index} source is not in nodes: {source}")
        if target not in node_set:
            raise ValueError(f"edge {index} target is not in nodes: {target}")
        weight = _finite_number(edge.get("weight", 1.0), name=f"edge {index} weight")
        edge_list.append((str(source), str(target), weight))

    state = dict(fixed_inputs)
    for _ in range(steps):
        next_state = dict(fixed_inputs)
        for source, target, weight in edge_list:
            next_state[target] += decay_value * state[source] * weight
        state = next_state

    return [state[output_id] for output_id in output_ids]


def build_toy_signal_run_record(
    *,
    input_ids: Sequence[str],
    output_ids: Sequence[str],
    output_vector: Sequence[float],
    steps: int,
    decay: float,
    seed: int,
) -> dict[str, object]:
    """Build a deterministic provenance record without claiming Atlas validity."""
    if len(output_ids) != len(output_vector):
        raise ValueError("output_ids and output_vector must have the same length")
    return {
        "artifact_type": "toy_signal_run_record",
        "claim_status": "not_interpretable_as_neuroscience",
        "model": "deterministic_synchronous_weighted_propagation",
        "parameters": {"decay": float(decay), "seed": seed, "steps": steps},
        "input_ids": list(input_ids),
        "output_ids": list(output_ids),
        "output_vector": [float(value) for value in output_vector],
        "limitations": [
            "Synthetic graph fixture only.",
            "Output values are not neural activity or behavior.",
            "Atlas schema compatibility is not asserted until a repository schema validator exists.",
        ],
    }
