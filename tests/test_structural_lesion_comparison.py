"""Known-answer comparison of synthetic structural and lesion rankings.

This test describes only a repository-local toy fixture. It is not evidence of
neural function, biological importance, vulnerability, behavior, or causality.
"""

from connectome_analysis.node_lesion import score_node_lesions
from connectome_analysis.structural_baseline import build_structural_baseline_table


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


def test_declared_out_degree_ranking_disagrees_with_synthetic_lesion_ranking():
    """The deliberately misleading hub wins out-degree but loses lesion impact."""
    structural = build_structural_baseline_table(NODES, EDGES)
    structural_rows = {row["node_id"]: row for row in structural["rows"]}

    lesions = score_node_lesions(
        NODES,
        EDGES,
        {"9007199254740993": 1.0},
        ["toy_output_a", "toy_output_b"],
        ["structural_hub", "critical_relay"],
        steps=2,
        decay=1.0,
        seed=7,
        graph_id="structural-lesion-comparison-v0",
    )
    lesion_rows = {row["target_id"]: row for row in lesions["rows"]}

    assert structural_rows["structural_hub"]["out_degree"] == 2
    assert structural_rows["critical_relay"]["out_degree"] == 1
    assert (
        lesion_rows["critical_relay"]["percent_output_change"]
        > lesion_rows["structural_hub"]["percent_output_change"]
    )
    assert structural["claim_status"] == "not_interpretable_as_neuroscience"
    assert lesions["claim_status"] == "not_interpretable_as_neuroscience"
