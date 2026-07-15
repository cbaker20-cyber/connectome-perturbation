import hashlib

import pytest

from connectome_analysis.targeted_validation_receipt import (
    RECEIPT_SCHEMA_VERSION,
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


def test_returns_receipt_only_after_all_gates_pass(tmp_path):
    manifest = _staged_run(tmp_path)

    receipt = validate_targeted_validation_run(
        manifest,
        tmp_path,
        numeric_fields=NUMERIC_FIELDS,
    )

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

    with pytest.raises(ValueError, match="exactly one manifest output record"):
        validate_targeted_validation_run(
            manifest,
            tmp_path,
            summary_path="sweep_run_info.csv",
            numeric_fields=NUMERIC_FIELDS,
        )
