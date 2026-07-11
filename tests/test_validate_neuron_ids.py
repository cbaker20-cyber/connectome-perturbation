import json

import pytest

from tools.validate_neuron_ids import deterministic_json, validate_neuron_id, validate_records


@pytest.mark.parametrize(
    "value",
    ["9007199254740993", "72057594062115730", "000123"],
)
def test_exact_decimal_strings_are_accepted(value):
    assert validate_neuron_id(value) is None


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (9007199254740993, "non_string"),
        (9007199254740992.0, "non_string"),
        ("", "empty"),
        (" 123", "surrounding_whitespace"),
        ("123 ", "surrounding_whitespace"),
        ("+123", "signed"),
        ("-123", "signed"),
        ("1e20", "non_decimal"),
        ("123.0", "non_decimal"),
        ("12a3", "non_decimal"),
    ],
)
def test_unsafe_representations_are_rejected(value, reason):
    assert validate_neuron_id(value) == reason


def test_report_is_deterministic_and_machine_readable():
    records = [
        {"root_id": "9007199254740993"},
        {"root_id": 9007199254740993},
        {"other": "123"},
    ]
    report = validate_records(records, "root_id")

    assert report["status"] == "invalid"
    assert report["valid_count"] == 1
    assert report["invalid_count"] == 2
    assert report["reason_counts"] == {"missing_column": 1, "non_string": 1}
    assert report["claim_status"] == "not_interpretable_as_neuroscience"

    first = deterministic_json(report)
    second = deterministic_json(report)
    assert first == second
    assert first.endswith("\n")
    assert json.loads(first) == report
