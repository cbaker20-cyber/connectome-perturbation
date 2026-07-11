from __future__ import annotations

import pytest

from connectome_analysis.graph_metrics import (
    degree_maps,
    expected_graph_metrics,
    reachable_from,
    weak_component_count,
)


NODES = ["sensory_a", "interneuron_b", "motor_c", "isolated_d"]
EDGES = [
    {"source": "sensory_a", "target": "interneuron_b"},
    {"source": "interneuron_b", "target": "motor_c"},
    {"source": "sensory_a", "target": "motor_c"},
]


def test_expected_graph_metrics_for_toy_fixture():
    assert expected_graph_metrics(NODES, EDGES, reachability_start="sensory_a") == {
        "node_count": 4,
        "edge_count": 3,
        "in_degree": {
            "sensory_a": 0,
            "interneuron_b": 1,
            "motor_c": 2,
            "isolated_d": 0,
        },
        "out_degree": {
            "sensory_a": 2,
            "interneuron_b": 1,
            "motor_c": 0,
            "isolated_d": 0,
        },
        "reachable_from_sensory_a": ["interneuron_b", "motor_c", "sensory_a"],
        "weak_component_count": 2,
    }


def test_degree_maps_reject_unknown_source():
    with pytest.raises(ValueError, match="edge source is not in nodes"):
        degree_maps(["a"], [{"source": "missing", "target": "a"}])


def test_degree_maps_reject_unknown_target():
    with pytest.raises(ValueError, match="edge target is not in nodes"):
        degree_maps(["a"], [{"source": "a", "target": "missing"}])


def test_reachable_from_rejects_unknown_start():
    with pytest.raises(ValueError, match="start node is not in nodes"):
        reachable_from("missing", ["a"], [])


def test_reachable_from_rejects_unknown_edge_endpoint():
    with pytest.raises(ValueError, match="edge target is not in nodes"):
        reachable_from("a", ["a"], [{"source": "a", "target": "missing"}])


def test_weak_component_count_rejects_unknown_edge_endpoint():
    with pytest.raises(ValueError, match="edge source is not in nodes"):
        weak_component_count(["a"], [{"source": "missing", "target": "a"}])
