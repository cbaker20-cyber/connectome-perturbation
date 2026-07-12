import json
from pathlib import Path

import pytest

from tools.validate_neuron_ids import (
    classify_neuron_id,
    deterministic_json,
    parse_availability,
    resolve_io_paths,
    resolve_repository_path,
    validate_neuron_id,
    validate_records,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "neuron_id_validation_cases.json"


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
        (None, "missing_value"),
        ("", "missing_value"),
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


def test_merged_conformance_fixture_matches_validator_scope():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for case in fixture["cases"]:
        kwargs = {}
        if "original_text" in case:
            kwargs["original_text"] = case["original_text"]
        if "provenance_original_text_available" in case:
            kwargs["provenance_original_text_available"] = case[
                "provenance_original_text_available"
            ]

        actual = classify_neuron_id(case["candidate"], **kwargs)
        assert actual == case["expected_status"], case["name"]
        if "expected_preserved_value" in case:
            assert case["candidate"] == case["expected_preserved_value"], case["name"]


@pytest.mark.parametrize(
    "original_text",
    [None, "", 9007199254740993, " 123", "+123", "12A3"],
)
def test_malformed_original_text_is_invalid_provenance(original_text):
    assert (
        classify_neuron_id("9007199254740993", original_text=original_text)
        == "invalid_provenance"
    )


def test_absent_provenance_is_not_reported_as_unverified():
    assert classify_neuron_id("9007199254740993") == "valid_exact_string"


def test_explicit_unavailable_original_is_unverified():
    assert (
        classify_neuron_id(
            "9007199254740993", provenance_original_text_available=False
        )
        == "unverified_precision"
    )


def test_available_flag_without_original_is_invalid_provenance():
    assert (
        classify_neuron_id(
            "9007199254740993", provenance_original_text_available=True
        )
        == "invalid_provenance"
    )


def test_unavailable_flag_with_original_is_invalid_provenance():
    assert (
        classify_neuron_id(
            "9007199254740993",
            original_text="9007199254740993",
            provenance_original_text_available=False,
        )
        == "invalid_provenance"
    )


def test_non_boolean_availability_is_invalid_provenance():
    assert (
        classify_neuron_id(
            "9007199254740993", provenance_original_text_available="false"
        )
        == "invalid_provenance"
    )


def test_original_text_comparison_preserves_leading_zeroes():
    assert (
        classify_neuron_id("00123", original_text="000123")
        == "suspected_precision_loss"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, True), (False, False), ("true", True), ("FALSE", False)],
)
def test_availability_adapter_accepts_explicit_booleans(value, expected):
    assert parse_availability(value) is expected


@pytest.mark.parametrize("value", [None, "", "yes", 0, 1])
def test_availability_adapter_rejects_ambiguous_values(value):
    from tools.validate_neuron_ids import _MISSING

    assert parse_availability(value) is _MISSING


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
    assert report["status_counts"] == {
        "invalid_type": 1,
        "missing_column": 1,
        "valid_exact_string": 1,
    }
    assert report["claim_status"] == "not_interpretable_as_neuroscience"

    first = deterministic_json(report)
    second = deterministic_json(report)
    assert first == second
    assert first.endswith("\n")
    assert json.loads(first) == report


def test_provenance_columns_are_aggregated_without_id_coercion():
    records = [
        {
            "root_id": "9007199254740993",
            "source_id": "9007199254740993",
            "source_available": True,
        },
        {
            "root_id": "9007199254740992",
            "source_id": "9007199254740993",
            "source_available": "true",
        },
        {
            "root_id": "72057594062115730",
            "source_available": "false",
        },
    ]

    report = validate_records(
        records,
        "root_id",
        original_text_column="source_id",
        availability_column="source_available",
    )

    assert report["valid_count"] == 1
    assert report["invalid_count"] == 2
    assert report["status_counts"] == {
        "suspected_precision_loss": 1,
        "unverified_precision": 1,
        "valid_exact_string": 1,
    }
    assert report["original_text_column"] == "source_id"
    assert report["availability_column"] == "source_available"


def test_missing_or_malformed_availability_is_invalid_provenance():
    records = [
        {"root_id": "123"},
        {"root_id": "456", "available": "unknown"},
    ]
    report = validate_records(records, "root_id", availability_column="available")

    assert report["status_counts"] == {"invalid_provenance": 2}
    assert report["valid_count"] == 0


def test_repository_path_accepts_file_inside_root(tmp_path):
    source = tmp_path / "input.json"
    source.write_text("[]", encoding="utf-8")

    assert resolve_repository_path(source, tmp_path, must_exist=True) == source.resolve()


def test_repository_path_rejects_outside_root(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes repository root"):
        resolve_repository_path(outside, root, must_exist=True)


def test_report_path_outside_root_is_rejected(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "input.json"
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="under results/validation"):
        resolve_io_paths(source, tmp_path / "report.json", root)


def test_nested_report_path_under_validation_tree_is_accepted(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "input.json"
    source.write_text("[]", encoding="utf-8")
    report = root / "results" / "validation" / "nested" / "report.json"

    resolved_source, resolved_report = resolve_io_paths(source, report, root)

    assert resolved_source == source.resolve()
    assert resolved_report == report.resolve()


def test_repo_relative_report_outside_validation_tree_is_rejected(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "input.json"
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="under results/validation"):
        resolve_io_paths(source, root / "docs" / "report.json", root)


def test_validation_tree_symlink_escape_is_rejected_when_supported(tmp_path):
    root = tmp_path / "repo"
    validation_root = root / "results" / "validation"
    validation_root.mkdir(parents=True)
    source = root / "input.json"
    source.write_text("[]", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    link = validation_root / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported in this environment")

    with pytest.raises(ValueError, match="under results/validation"):
        resolve_io_paths(source, link / "report.json", root)


def test_report_must_not_alias_input(tmp_path):
    root = tmp_path / "repo"
    source = root / "results" / "validation" / "input.json"
    source.parent.mkdir(parents=True)
    source.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must not resolve to the input path"):
        resolve_io_paths(source, Path(source.parent / "." / source.name), root)


def test_symlink_escape_is_rejected_when_supported(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("[]", encoding="utf-8")
    link = root / "linked.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not supported in this environment")

    with pytest.raises(ValueError, match="escapes repository root"):
        resolve_repository_path(link, root, must_exist=True)
