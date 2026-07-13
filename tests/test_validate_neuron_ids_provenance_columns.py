"""Focused tests for configured original-text provenance enforcement."""

from tools.validate_neuron_ids import validate_records


def test_missing_configured_original_text_without_availability_is_invalid():
    report = validate_records(
        [{"root_id": "9007199254740993"}],
        "root_id",
        original_text_column="source_id",
    )

    assert report["status"] == "invalid"
    assert report["status_counts"] == {"invalid_provenance": 1}
    assert report["valid_count"] == 0


def test_missing_configured_original_text_when_declared_available_is_invalid():
    report = validate_records(
        [{"root_id": "9007199254740993", "source_available": True}],
        "root_id",
        original_text_column="source_id",
        availability_column="source_available",
    )

    assert report["status"] == "invalid"
    assert report["status_counts"] == {"invalid_provenance": 1}


def test_missing_configured_original_text_when_declared_unavailable_is_unverified():
    report = validate_records(
        [{"root_id": "9007199254740993", "source_available": False}],
        "root_id",
        original_text_column="source_id",
        availability_column="source_available",
    )

    assert report["status"] == "invalid"
    assert report["status_counts"] == {"unverified_precision": 1}
