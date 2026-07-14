from copy import deepcopy

import pytest

from connectome_analysis.structural_baseline import build_structural_baseline_table


def test_known_answer_counts_parallel_edges_and_self_loops():
    nodes = ["9007199254740993", "b", "c"]
    edges = [
        {"source": "9007199254740993", "target": "b", "weight": 2},
        {"source": "9007199254740993", "target": "b", "weight": 3.5},
        {"source": "b", "target": "b", "weight": 4},
        {"source": "c", "target": "9007199254740993", "weight": 1},
    ]
    original_nodes = deepcopy(nodes)
    original_edges = deepcopy(edges)

    artifact = build_structural_baseline_table(nodes, edges)

    assert artifact["node_ids"] == nodes
    assert artifact["rows"] == [
        {
            "node_id": "9007199254740993",
            "in_degree": 1,
            "out_degree": 2,
            "weighted_in_degree": 1.0,
            "weighted_out_degree": 5.5,
            "weighted_degree": 6.5,
        },
        {
            "node_id": "b",
            "in_degree": 3,
            "out_degree": 1,
            "weighted_in_degree": 9.5,
            "weighted_out_degree": 4.0,
            "weighted_degree": 13.5,
        },
        {
            "node_id": "c",
            "in_degree": 0,
            "out_degree": 1,
            "weighted_in_degree": 0.0,
            "weighted_out_degree": 1.0,
            "weighted_degree": 1.0,
        },
    ]
    assert nodes == original_nodes
    assert edges == original_edges
    assert build_structural_baseline_table(nodes, edges) == artifact


@pytest.mark.parametrize(
    "nodes,edges",
    [
        ([], []),
        (["a", "a"], []),
        (["a", 1], []),
        (["a"], [{"source": "a", "target": "missing", "weight": 1}]),
        (["a"], [{"source": "a", "target": "a"}]),
        (["a"], [{"source": "a", "target": "a", "weight": True}]),
        (["a"], [{"source": "a", "target": "a", "weight": -1}]),
        (["a"], [{"source": "a", "target": "a", "weight": float("inf")}]),
    ],
)
def test_malformed_inputs_fail_closed(nodes, edges):
    with pytest.raises(ValueError):
        build_structural_baseline_table(nodes, edges)
