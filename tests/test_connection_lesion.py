import copy
import json

import pytest

from connectome_analysis.connection_lesion import score_connection_lesions


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
    return score_connection_lesions(
        NODES,
        EDGES,
        {"9007199254740993": 1.0},
        ["toy_output_a", "toy_output_b"],
        [
            ("structural_hub", "dead_end_a"),
            ("critical_relay", "toy_output_a"),
        ],
        steps=2,
        decay=1.0,
        seed=7,
        graph_id="connection-lesion-known-answer-v0",
    )


def test_known_critical_connection_ranks_above_noncritical_connection():
    result = score_fixture()

    assert result["input_ids"] == ["9007199254740993"]
    assert result["rows"][0]["source_id"] == "critical_relay"
    assert result["rows"][0]["target_id"] == "toy_output_a"
    assert result["rows"][1]["source_id"] == "structural_hub"
    assert result["rows"][0]["percent_output_change"] > result["rows"][1]["percent_output_change"]
    assert result["claim_status"] == "not_interpretable_as_neuroscience"


def test_scoring_is_deterministic_serializable_and_does_not_mutate_inputs():
    nodes = list(NODES)
    edges = copy.deepcopy(EDGES)
    inputs = {"9007199254740993": 1.0}
    outputs = ["toy_output_a", "toy_output_b"]
    targets = [
        ("structural_hub", "dead_end_a"),
        ("critical_relay", "toy_output_a"),
    ]
    before = copy.deepcopy((nodes, edges, inputs, outputs, targets))

    first = score_connection_lesions(nodes, edges, inputs, outputs, targets, steps=2, seed=7)
    second = score_connection_lesions(nodes, edges, inputs, outputs, targets, steps=2, seed=7)

    assert first == second
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )
    assert (nodes, edges, inputs, outputs, targets) == before


def test_edge_identity_is_direction_sensitive():
    with pytest.raises(ValueError, match="target edge is not in edges"):
        score_connection_lesions(
            NODES,
            EDGES,
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            [("toy_output_a", "critical_relay")],
            steps=2,
        )


@pytest.mark.parametrize(
    ("targets", "message"),
    [
        ([('missing', 'toy_output_a')], "target edge is not in edges"),
        ([('critical_relay', 'toy_output_a'), ('critical_relay', 'toy_output_a')], "target_edges must be unique"),
        ([('critical_relay',)], "exactly source and target"),
        ([('critical_relay', 3)], "target.*target must be a non-empty string"),
    ],
)
def test_rejects_invalid_targets(targets, message):
    with pytest.raises(ValueError, match=message):
        score_connection_lesions(
            NODES,
            EDGES,
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            targets,
            steps=2,
        )


def test_rejects_ambiguous_parallel_edges():
    edges = copy.deepcopy(EDGES)
    edges.append(copy.deepcopy(EDGES[1]))
    with pytest.raises(ValueError, match="parallel edges"):
        score_connection_lesions(
            NODES,
            edges,
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            [("critical_relay", "toy_output_a")],
            steps=2,
        )


def test_dangling_and_malformed_edges_fail_closed():
    dangling = copy.deepcopy(EDGES)
    dangling.append({"source": "backup", "target": "missing", "weight": 1.0})
    with pytest.raises(ValueError, match="target is not in nodes"):
        score_connection_lesions(
            NODES,
            dangling,
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            [("critical_relay", "toy_output_a")],
            steps=2,
        )

    malformed = copy.deepcopy(EDGES)
    malformed[0]["source"] = 9007199254740993
    with pytest.raises(ValueError, match="source must be a non-empty string"):
        score_connection_lesions(
            NODES,
            malformed,
            {"9007199254740993": 1.0},
            ["toy_output_a", "toy_output_b"],
            [("critical_relay", "toy_output_a")],
            steps=2,
        )
