import copy

import pytest

from connectome_analysis.connection_lesion import score_connection_lesions
from connectome_analysis.toy_signal import build_toy_signal_run_record
from tools.validate_atlas import validate_record


NODES = ["input", "relay", "output"]
EDGES = [
    {"source": "input", "target": "relay", "weight": 2.0},
    {"source": "relay", "target": "output", "weight": 1.0},
]


def valid_record():
    return build_toy_signal_run_record(
        input_ids=["9007199254740993"],
        output_ids=["toy_output"],
        output_vector=[1.0],
        steps=2,
        decay=1.0,
        seed=7,
    )


def valid_connection_table():
    return score_connection_lesions(
        NODES,
        EDGES,
        {"input": 1.0},
        ["output"],
        [("relay", "output"), ("input", "relay")],
        steps=2,
        decay=1.0,
        seed=7,
        graph_id="validator-known-answer-v0",
    )


def test_accepts_repository_local_v0_record_and_preserves_string_id():
    record = valid_record()

    validate_record(record)

    assert record["schema_version"] == "atlas-run-record/v0"
    assert record["input_ids"] == ["9007199254740993"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda record: record.pop("claim_status"), "missing required fields"),
        (lambda record: record.__setitem__("extra", True), "unknown fields"),
        (lambda record: record["parameters"].__setitem__("steps", True), "steps must be"),
        (lambda record: record["parameters"].__setitem__("decay", float("inf")), "decay must be"),
        (lambda record: record["input_ids"].append("9007199254740993"), "must not contain duplicates"),
        (lambda record: record.__setitem__("input_ids", [9007199254740993]), "non-empty strings"),
        (lambda record: record["output_vector"].append(2.0), "length must equal"),
        (lambda record: record.__setitem__("limitations", []), "limitations must be"),
    ],
)
def test_rejects_invalid_records(mutate, message):
    record = copy.deepcopy(valid_record())
    mutate(record)

    with pytest.raises(ValueError, match=message):
        validate_record(record)


def test_accepts_connection_lesion_table():
    table = valid_connection_table()

    validate_record(table)

    assert table["schema_version"] == "atlas-connection-lesion-table/v0"
    assert table["claim_status"] == "not_interpretable_as_neuroscience"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda table: table["rows"][0].__setitem__("source_id", 9007199254740993), "source_id must be"),
        (lambda table: table["rows"][0]["perturbed_output_vector"].append(0.0), "length must equal"),
        (lambda table: table["rows"][0].__setitem__("percent_output_change", float("inf")), "non-negative finite"),
        (lambda table: table["rows"][0].__setitem__("cosine_distance", 3.0), "between 0 and 2"),
        (lambda table: table["rows"][0]["baseline_output_vector"].__setitem__(0, -1.0), "must equal table"),
        (lambda table: table["rows"].append(copy.deepcopy(table["rows"][0])), "duplicate directed edges"),
        (lambda table: table["rows"].reverse(), "deterministic descending metric order"),
        (lambda table: table.__setitem__("schema_version", "external-atlas/v1"), "unsupported schema_version"),
    ],
)
def test_rejects_invalid_connection_lesion_tables(mutate, message):
    table = copy.deepcopy(valid_connection_table())
    mutate(table)

    with pytest.raises(ValueError, match=message):
        validate_record(table)
