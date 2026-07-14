import copy

import pytest

from connectome_analysis.connection_lesion import score_connection_lesions
from connectome_analysis.toy_signal import build_toy_signal_run_record
from connectome_analysis.vulnerability_matrix import build_vulnerability_signature_matrix
from tools.validate_atlas import validate_record


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
        {"9007199254740993": 1.0},
        ["toy_output_a", "toy_output_b"],
        [
            ("structural_hub", "dead_end_a"),
            ("critical_relay", "toy_output_a"),
        ],
        steps=2,
        decay=1.0,
        seed=7,
        graph_id="validator-known-answer-v0",
    )


def valid_node_source(artifact_id, first, second):
    return {
        "artifact_id": artifact_id,
        "record": {
            "schema_version": "atlas-node-lesion-table/v0",
            "artifact_type": "synthetic_node_lesion_scores",
            "claim_status": "not_interpretable_as_neuroscience",
            "rows": [
                {"target_id": "critical_relay", "percent_output_change": first, "cosine_distance": 0.5},
                {"target_id": "9007199254740993", "percent_output_change": second, "cosine_distance": 0.1},
            ],
        },
    }


def valid_vulnerability_matrix():
    return build_vulnerability_signature_matrix(
        [
            valid_node_source("toy-a", 100.0, 10.0),
            valid_node_source("toy-b", 5.0, 25.0),
        ],
        context_ids=["toy_context_a", "toy_context_b"],
        target_ids=["critical_relay", "9007199254740993"],
        score_name="percent_output_change",
        matrix_id="validator-vulnerability-matrix-v0",
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


def test_accepts_vulnerability_matrix_and_preserves_axes():
    matrix = valid_vulnerability_matrix()

    validate_record(matrix)

    assert matrix["context_ids"] == ["toy_context_a", "toy_context_b"]
    assert matrix["target_ids"] == ["critical_relay", "9007199254740993"]
    assert matrix["values"] == [[100.0, 10.0], [5.0, 25.0]]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda matrix: matrix.pop("claim_status"), "missing required fields"),
        (lambda matrix: matrix.__setitem__("score_name", "signed_effect"), "supported non-negative"),
        (lambda matrix: matrix.__setitem__("context_ids", [9007199254740993, "toy_context_b"]), "non-empty strings"),
        (lambda matrix: matrix["values"].pop(), "one row per context_id"),
        (lambda matrix: matrix["values"][0].pop(), "one value per target_id"),
        (lambda matrix: matrix["values"][0].__setitem__(0, float("nan")), "non-negative finite"),
        (lambda matrix: matrix["values"][0].__setitem__(0, -1.0), "non-negative finite"),
        (lambda matrix: matrix["source_artifacts"].pop(), "one entry per context_id"),
        (lambda matrix: matrix["source_artifacts"][0].__setitem__("context_id", "wrong"), "must match context_ids order"),
        (lambda matrix: matrix["source_artifacts"][0].__setitem__("schema_version", "external/v1"), "is unsupported"),
        (lambda matrix: matrix["source_artifacts"][0].__setitem__("artifact_sha256", "ABC"), "lowercase SHA-256 hex"),
        (lambda matrix: matrix["source_artifacts"][0]["target_axis"].reverse(), "exactly match target_ids order"),
        (lambda matrix: matrix["source_artifacts"][1].__setitem__("artifact_id", "toy-a"), "duplicate artifact_id"),
        (lambda matrix: matrix.__setitem__("limitations", []), "limitations must be"),
    ],
)
def test_rejects_invalid_vulnerability_matrices(mutate, message):
    matrix = copy.deepcopy(valid_vulnerability_matrix())
    mutate(matrix)

    with pytest.raises(ValueError, match=message):
        validate_record(matrix)
