import copy

import pytest

from connectome_analysis.structural_baseline import build_structural_baseline_table
from tools.validate_atlas import validate_record


NODES = ["9007199254740993", "b", "c"]
EDGES = [
    {"source": "9007199254740993", "target": "b", "weight": 2},
    {"source": "9007199254740993", "target": "b", "weight": 3.5},
    {"source": "b", "target": "b", "weight": 4},
    {"source": "c", "target": "9007199254740993", "weight": 1},
]


def valid_table():
    return build_structural_baseline_table(NODES, EDGES)


def test_accepts_structural_baseline_table_and_preserves_string_ids():
    table = valid_table()

    validate_record(table)

    assert table["schema_version"] == "atlas-structural-baseline-table/v0"
    assert table["node_ids"] == NODES
    assert table["rows"][0]["node_id"] == "9007199254740993"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda table: table.pop("claim_status"), "missing required fields"),
        (lambda table: table.__setitem__("extra", True), "unknown fields"),
        (lambda table: table.__setitem__("node_ids", [9007199254740993, "b", "c"]), "non-empty strings"),
        (lambda table: table["node_ids"].append("b"), "must not contain duplicates"),
        (lambda table: table["metrics"].reverse(), "exactly match the structural baseline metric order"),
        (lambda table: table["rows"].pop(), "exactly one entry per node_id"),
        (lambda table: table["rows"][0].__setitem__("node_id", "wrong"), "must match node_ids order"),
        (lambda table: table["rows"][0].__setitem__("in_degree", True), "non-negative integer"),
        (lambda table: table["rows"][0].__setitem__("out_degree", -1), "non-negative integer"),
        (lambda table: table["rows"][0].__setitem__("weighted_in_degree", float("inf")), "non-negative finite"),
        (lambda table: table["rows"][0].__setitem__("weighted_out_degree", -1.0), "non-negative finite"),
        (lambda table: table["rows"][0].__setitem__("weighted_degree", 999.0), "must equal weighted_in_degree plus weighted_out_degree"),
        (lambda table: table.__setitem__("limitations", []), "limitations must be"),
        (lambda table: table.__setitem__("schema_version", "external/v1"), "unsupported schema_version"),
    ],
)
def test_rejects_corrupted_structural_baseline_tables(mutate, message):
    table = copy.deepcopy(valid_table())
    mutate(table)

    with pytest.raises(ValueError, match=message):
        validate_record(table)
