import copy
import math

import pytest

from connectome_analysis.node_lesion import (
    compare_output_vectors,
    score_node_lesions,
)


NODES = [
    "9007199254740993",
    "critical_relay",
    "structural_hub",
    "backup",
    "dead_end_a",
    "dead_end_b",
    "toy_output_a",
    "toy_output_b",
]
EDGES = [
    {"source": "9007199254740993", "target": "critical_relay", "weight": 4.0},
    {"source": "critical_relay", "target": "toy_output_a", "weight": 1.0},
    {"source": "9007199254740993", "target": "backup", "weight": 1.0},
    {"source": "backup", "target": "toy_output_a", "weight": 1.0},
    {"source": "9007199254740993", "target": "toy_output_b", "weight": 1.0},
    {"source": "9007199254740993", "target": "structural_hub", "weight": 1.0},
    {"source": "structural_hub", "target": "dead_end_a", "weight": 1.0},
    {"source": "structural_hub", "target": "dead_end_b", "weight": 1.0},
]


def score_fixture():
    return score_node_lesions(
        NODES,
        EDGES,
        {"9007199254740993": 1.0},
        ["toy_output_a", "toy_output_b"],
        ["structural_hub", "critical_relay"],
        steps=2,
        decay=1.0,
        seed=7,
        graph_id="node-lesion-known-answer-v0",
    )


def test_known_critical_relay_ranks_above_misleading_hub_and_ids_stay_strings():
    result = score_fixture()

    assert result["input_ids"] == ["9007199254740993"]
    assert result["rows"][0]["target_id"] == "critical_relay"
    assert result["rows"][1]["target_id"] == "structural_hub"
    assert result["rows"][0]["percent_output_change"] > result["rows"][1]["percent_output_change"]
    assert result["claim_status"] == "not_interpretable_as_neuroscience"


def test_scoring_is_deterministic_and_does_not_mutate_inputs():
    nodes = list(NODES)
    edges = copy.deepcopy(EDGES)
    inputs = {"9007199254740993": 1.0}
    outputs = ["toy_output_a", "toy_output_b"]
    targets = ["structural_hub", "critical_relay"]
    before = copy.deepcopy((nodes, edges, inputs, outputs, targets))

    first = score_node_lesions(
        nodes, edges, inputs, outputs, targets, steps=2, seed=7
    )
    second = score_node_lesions(
        nodes, edges, inputs, outputs, targets, steps=2, seed=7
    )

    assert first == second
    assert (nodes, edges, inputs, outputs, targets) == before


@pytest.mark.parametrize(
    ("targets", "message"),
    [
        (["missing"], "target node is not in nodes"),
        (["critical_relay", "critical_relay"], "target_ids must be unique"),
        (["9007199254740993"], "cannot remove fixed input"),
        (["toy_output_a"], "cannot remove requested output"),
    ],
)
def test_rejects_invalid_targets(targets, message):
    with pytest.raises(ValueError, match=message):
        score_node_lesions(
            NODES,
            EDGES,
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            targets,
            steps=2,
        )


@pytest.mark.parametrize(
    ("baseline", "perturbed", "message"),
    [
        ([0.0, 0.0], [1.0, 1.0], "L1 magnitude"),
        ([1.0, 1.0], [0.0, 0.0], "non-zero vector norms"),
        ([1.0], [1.0, 2.0], "equal length"),
        ([1.0, math.inf], [1.0, 1.0], "finite number"),
    ],
)
def test_comparison_metrics_fail_closed(baseline, perturbed, message):
    with pytest.raises(ValueError, match=message):
        compare_output_vectors(baseline, perturbed)


def test_dangling_edges_and_nonfinite_weights_are_rejected_by_propagation():
    with pytest.raises(ValueError, match="target is not in nodes"):
        score_node_lesions(
            NODES,
            EDGES + [{"source": "backup", "target": "missing", "weight": 1.0}],
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            ["critical_relay"],
            steps=2,
        )

    broken = copy.deepcopy(EDGES)
    broken[0]["weight"] = math.nan
    with pytest.raises(ValueError, match="finite number"):
        score_node_lesions(
            NODES,
            broken,
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            ["critical_relay"],
            steps=2,
        )
