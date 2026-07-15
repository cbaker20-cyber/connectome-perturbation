"""Composed, fail-closed validation for one staged targeted-validation summary.

The returned receipt records only repository-local validation gates. It is not an
experiment result and must not be interpreted as biological or neuroscience evidence.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path

from connectome_analysis.targeted_validation_csv import parse_targeted_validation_summary_csv
from connectome_analysis.targeted_validation_manifest import (
    CLAIM_STATUS,
    SCHEMA_VERSION,
    validate_targeted_validation_manifest,
    verify_targeted_validation_files,
)
from connectome_analysis.targeted_validation_summary import (
    validate_targeted_validation_summary_artifact,
)

RECEIPT_SCHEMA_VERSION = "atlas-targeted-validation-validation-receipt/v0"
_VALIDATED_GATES = (
    "manifest_contract",
    "declared_file_bytes",
    "strict_csv_schema",
    "summary_artifact_binding",
    "four_cell_semantics",
)


def validate_targeted_validation_run(
    manifest: object,
    run_directory: str | Path,
    *,
    summary_path: str = "sweep_summary.csv",
    numeric_fields: Sequence[str],
) -> dict[str, object]:
    """Validate one staged run and return a machine-readable validation receipt.

    The function composes the manifest contract, staged-file byte verification,
    strict CSV parsing, artifact-to-manifest binding, and four-cell semantic checks.
    It raises ``ValueError`` on the first failed gate and returns a receipt only after
    every gate succeeds.

    The receipt does not assert simulation correctness, FlyWire validity, biological
    meaning, causality, mechanism, generalization, or regeneration.
    """

    validate_targeted_validation_manifest(manifest)
    verify_targeted_validation_files(manifest, run_directory)
    assert isinstance(manifest, Mapping)

    if not isinstance(summary_path, str) or not summary_path.strip():
        raise ValueError("summary_path must be a non-empty string")

    root = Path(run_directory).resolve(strict=True)
    summary_file = root / summary_path
    try:
        resolved_summary = summary_file.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"summary_path does not exist: {summary_path!r}") from exc
    if not resolved_summary.is_relative_to(root):
        raise ValueError("summary_path escapes run_directory")
    if summary_file.is_symlink() or not resolved_summary.is_file():
        raise ValueError("summary_path must identify a regular non-symlink file")

    artifact_bytes = resolved_summary.read_bytes()
    rows = parse_targeted_validation_summary_csv(
        artifact_bytes,
        numeric_fields=numeric_fields,
    )
    validate_targeted_validation_summary_artifact(
        rows,
        manifest,
        artifact_path=summary_path,
        artifact_bytes=artifact_bytes,
        numeric_fields=numeric_fields,
    )

    parameters = manifest["parameters"]
    assert isinstance(parameters, Mapping)
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "claim_status": CLAIM_STATUS,
        "manifest_schema_version": SCHEMA_VERSION,
        "run_id": manifest["run_id"],
        "git_commit": manifest["git_commit"],
        "summary_path": summary_path,
        "summary_size_bytes": len(artifact_bytes),
        "summary_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
        "row_count": len(rows),
        "numeric_fields": list(numeric_fields),
        "parameters": {
            "n_run": parameters["n_run"],
            "t_run_ms": parameters["t_run_ms"],
        },
        "validated_gates": list(_VALIDATED_GATES),
        "limitations": [
            "Receipt covers repository-local validation gates only.",
            "Receipt does not establish parser-independent scientific correctness.",
            "Receipt does not support biological, behavioral, causal, mechanistic, generalization, or regeneration claims.",
        ],
    }
