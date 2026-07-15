from __future__ import annotations

import hashlib

import pytest

from connectome_analysis.targeted_validation_summary import (
    validate_targeted_validation_summary_artifact,
)


ARTIFACT_PATH = "sweep_summary.csv"
ARTIFACT_BYTES = b"source,target,n_run,t_run_ms,score\nsynthetic fixture only\n"


def _rows() -> list[dict[str, object]]:
    return [
        {"source": "sugar", "target": "AN", "n_run": 30, "t_run_ms": 1000, "score": 1.0},
        {
            "source": "sugar",
            "target": "brain_motor_neuron",
            "n_run": 30,
            "t_run_ms": 1000,
            "score": 2.0,
        },
        {"source": "gustatory", "target": "AN", "n_run": 30, "t_run_ms": 1000, "score": 3.0},
        {
            "source": "gustatory",
            "target": "brain_motor_neuron",
            "n_run": 30,
            "t_run_ms": 1000,
            "score": 4.0,
        },
    ]


def _manifest() -> dict[str, object]:
    return {
        "parameters": {"n_run": 30, "t_run_ms": 1000},
        "outputs": [
            {
                "path": ARTIFACT_PATH,
                "size_bytes": len(ARTIFACT_BYTES),
                "sha256": hashlib.sha256(ARTIFACT_BYTES).hexdigest(),
            }
        ],
    }


def test_accepts_rows_tied_to_exact_declared_artifact_bytes() -> None:
    validate_targeted_validation_summary_artifact(
        _rows(),
        _manifest(),
        artifact_path=ARTIFACT_PATH,
        artifact_bytes=ARTIFACT_BYTES,
        numeric_fields=["score"],
    )


def test_rejects_undeclared_artifact_path() -> None:
    with pytest.raises(ValueError, match="exactly one manifest output"):
        validate_targeted_validation_summary_artifact(
            _rows(),
            _manifest(),
            artifact_path="ranked_targeted_validation.csv",
            artifact_bytes=ARTIFACT_BYTES,
            numeric_fields=["score"],
        )


def test_rejects_duplicate_manifest_records_for_artifact() -> None:
    manifest = _manifest()
    manifest["outputs"] = [manifest["outputs"][0], dict(manifest["outputs"][0])]
    with pytest.raises(ValueError, match="exactly one manifest output"):
        validate_targeted_validation_summary_artifact(
            _rows(),
            manifest,
            artifact_path=ARTIFACT_PATH,
            artifact_bytes=ARTIFACT_BYTES,
            numeric_fields=["score"],
        )


def test_rejects_artifact_size_mismatch() -> None:
    manifest = _manifest()
    manifest["outputs"][0]["size_bytes"] += 1
    with pytest.raises(ValueError, match="byte size disagrees"):
        validate_targeted_validation_summary_artifact(
            _rows(),
            manifest,
            artifact_path=ARTIFACT_PATH,
            artifact_bytes=ARTIFACT_BYTES,
            numeric_fields=["score"],
        )


def test_rejects_artifact_digest_mismatch() -> None:
    manifest = _manifest()
    manifest["outputs"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256 disagrees"):
        validate_targeted_validation_summary_artifact(
            _rows(),
            manifest,
            artifact_path=ARTIFACT_PATH,
            artifact_bytes=ARTIFACT_BYTES,
            numeric_fields=["score"],
        )


def test_still_rejects_semantically_incomplete_rows() -> None:
    with pytest.raises(ValueError, match="exactly the four declared"):
        validate_targeted_validation_summary_artifact(
            _rows()[:-1],
            _manifest(),
            artifact_path=ARTIFACT_PATH,
            artifact_bytes=ARTIFACT_BYTES,
            numeric_fields=["score"],
        )
