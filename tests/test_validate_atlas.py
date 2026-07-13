import copy

import pytest

from connectome_analysis.toy_signal import build_toy_signal_run_record
from tools.validate_atlas import validate_record


def valid_record():
    return build_toy_signal_run_record(
        input_ids=["9007199254740993"],
        output_ids=["toy_output"],
        output_vector=[1.0],
        steps=2,
        decay=1.0,
        seed=7,
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
