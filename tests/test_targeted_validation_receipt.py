import hashlib
import json

import pytest

from connectome_analysis.targeted_validation_receipt import (
    RECEIPT_SCHEMA_VERSION,
    serialize_targeted_validation_receipt,
    validate_targeted_validation_receipt,
    validate_targeted_validation_run,
)


NUMERIC_FIELDS = ("mean_score",)
SUMMARY = (
    b"source,target,n_run,t_run_ms,mean_score\n"
    b"sugar,AN,50,1000,1.0\n"
    b"sugar,brain_motor_neuron,50,1000,2.0\n"
    b"gustatory,AN,50,1000,3.0\n"
    b"gustatory,brain_motor_neuron,50,1000,4.0\n"
)


def _record(path, data):
    return {
        "path": path,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _staged_run(tmp_path):
    files = {
        "inputs/source_ids.txt": b"synthetic input fixture\n",
        "sweep_summary.csv": SUMMARY,
        "sweep_run_info.csv": b"key,value\nfixture,true\n",
        "ranked_targeted_validation.csv": b"rank,fixture\n1,true\n",
        "targeted_validation_readable_summary.txt": b"synthetic validation fixture\n",
        "logs/run.log": b"synthetic test log\n",
    }
    for relative_path, data in files.items():
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)

    manifest = {
        "schema_version": "atlas-targeted-validation-run-manifest/v0",
        "claim_status": "not_interpretable_as_neuroscience",
        "run_id": "synthetic-receipt-test",
        "git_commit": "a" * 40,
        "command": "synthetic test fixture only",
        "backend": {"name": "fixture", "version": "0"},
        "parameters": {"n_run": 50, "t_run_ms": 1000, "seed_policy": "fixture"},
        "sources": [
            {"label": "sugar", "id_count": 21},
            {"label": "gustatory", "id_count": 1},
        ],
        "targets": ["AN", "brain_motor_neuron"],
        "cells": [
            {"source": "sugar", "target": "AN"},
            {"source": "sugar", "target": "brain_motor_neuron"},
            {"source": "gustatory", "target": "AN"},
            {"source": "gustatory", "target": "brain_motor_neuron"},
        ],
        "inputs": [_record("inputs/source_ids.txt", files["inputs/source_ids.txt"])],
        "outputs": [
            _record(path, data)
            for path, data in files.items()
            if path != "inputs/source_ids.txt"
        ],
        "limitations": ["Synthetic fixture; no scientific interpretation."],
    }
    return manifest


def _receipt(tmp_path):
    return validate_targeted_validation_run(
        _staged_run(tmp_path),
        tmp_path,
        numeric_fields=NUMERIC_FIELDS,
    )


def test_returns_receipt_only_after_all_gates_pass(tmp_path):
    receipt = _receipt(tmp_path)

    assert receipt["schema_version"] == RECEIPT_SCHEMA_VERSION
    assert receipt["claim_status"] == "not_interpretable_as_neuroscience"
    assert receipt["run_id"] == "synthetic-receipt-test"
    assert receipt["summary_sha256"] == hashlib.sha256(SUMMARY).hexdigest()
    assert receipt["summary_size_bytes"] == len(SUMMARY)
    assert receipt["row_count"] == 4
    assert receipt["numeric_fields"] == ["mean_score"]
    assert receipt["validated_gates"] == [
        "manifest_contract",
        "declared_file_bytes",
        "strict_csv_schema",
        "summary_artifact_binding",
        "four_cell_semantics",
    ]


def test_serialization_is_canonical_and_round_trips(tmp_path):
    receipt = _receipt(tmp_path)

    serialized = serialize_targeted_validation_receipt(receipt)

    assert serialized.endswith(b"\n")
    assert serialized == serialize_targeted_validation_receipt(json.loads(serialized))
    assert serialized == (
        json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode("utf-8")


def test_stored_receipt_rejects_missing_provenance(tmp_path):
    receipt = _receipt(tmp_path)
    del receipt["git_commit"]

    with pytest.raises(ValueError, match="receipt keys mismatch"):
        validate_targeted_validation_receipt(receipt)


def test_stored_receipt_rejects_unknown_schema(tmp_path):
    receipt = _receipt(tmp_path)
    receipt["schema_version"] = "future-or-unknown"

    with pytest.raises(ValueError, match="unsupported receipt schema_version"):
        serialize_targeted_validation_receipt(receipt)


def test_stored_receipt_rejects_changed_gate_claim(tmp_path):
    receipt = _receipt(tmp_path)
    receipt["validated_gates"] = ["manifest_contract"]

    with pytest.raises(ValueError, match="validated_gates mismatch"):
        validate_targeted_validation_receipt(receipt)


def test_stored_receipt_rejects_non_four_cell_row_count(tmp_path):
    receipt = _receipt(tmp_path)
    receipt["row_count"] = 3

    with pytest.raises(ValueError, match="row_count must equal 4"):
        validate_targeted_validation_receipt(receipt)


def test_stored_receipt_rejects_empty_summary_artifact(tmp_path):
    receipt = _receipt(tmp_path)
    receipt["summary_size_bytes"] = 0

    with pytest.raises(ValueError, match="summary_size_bytes must be a positive integer"):
        validate_targeted_validation_receipt(receipt)


@pytest.mark.parametrize(
    "summary_path",
    [
        "/tmp/sweep_summary.csv",
        "../sweep_summary.csv",
        "results/../sweep_summary.csv",
        "results\\sweep_summary.csv",
    ],
)
def test_stored_receipt_rejects_unsafe_or_ambiguous_summary_path(tmp_path, summary_path):
    receipt = _receipt(tmp_path)
    receipt["summary_path"] = summary_path

    with pytest.raises(ValueError, match="summary_path"):
        validate_targeted_validation_receipt(receipt)


def test_fails_before_receipt_when_declared_bytes_change(tmp_path):
    manifest = _staged_run(tmp_path)
    (tmp_path / "sweep_summary.csv").write_bytes(SUMMARY + b"\n")

    with pytest.raises(ValueError, match="size_bytes mismatch"):
        validate_targeted_validation_run(
            manifest,
            tmp_path,
            numeric_fields=NUMERIC_FIELDS,
        )


def test_rejects_summary_path_not_declared_as_the_parsed_artifact(tmp_path):
    manifest = _staged_run(tmp_path)

    # sweep_run_info.csv is a declared output but not a valid summary schema.
    # Fail-closed validation must reject it before issuing a receipt.
    with pytest.raises(
        ValueError,
        match="summary CSV header must equal|exactly one manifest output record",
    ):
        validate_targeted_validation_run(
            manifest,
            tmp_path,
            summary_path="sweep_run_info.csv",
            numeric_fields=NUMERIC_FIELDS,
        )
