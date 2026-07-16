"""Composed, fail-closed validation for one staged targeted-validation summary.

The returned receipt records only repository-local validation gates. It is not an
experiment result and must not be interpreted as biological or neuroscience evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

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
_RECEIPT_KEYS = {
    "schema_version",
    "claim_status",
    "manifest_schema_version",
    "run_id",
    "git_commit",
    "summary_path",
    "summary_size_bytes",
    "summary_sha256",
    "row_count",
    "numeric_fields",
    "parameters",
    "validated_gates",
    "limitations",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _validate_receipt_summary_path(value: object) -> None:
    """Require one canonical repository-relative POSIX artifact path."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError("receipt summary_path must be a non-empty string")
    if "\\" in value:
        raise ValueError("receipt summary_path must use POSIX separators")

    path = PurePosixPath(value)
    if path.is_absolute():
        raise ValueError("receipt summary_path must be relative")
    if value != path.as_posix() or any(part in {".", ".."} for part in path.parts):
        raise ValueError("receipt summary_path must be normalized and non-escaping")


def validate_targeted_validation_receipt(receipt: object) -> None:
    """Validate a stored receipt's schema and provenance completeness.

    This validates only the receipt record itself. It does not re-run the underlying
    staged-file or semantic checks and therefore cannot establish scientific validity.
    """

    if not isinstance(receipt, Mapping):
        raise ValueError("receipt must be a mapping")
    if set(receipt) != _RECEIPT_KEYS:
        missing = sorted(_RECEIPT_KEYS - set(receipt))
        unexpected = sorted(set(receipt) - _RECEIPT_KEYS)
        raise ValueError(f"receipt keys mismatch: missing={missing}, unexpected={unexpected}")
    if receipt["schema_version"] != RECEIPT_SCHEMA_VERSION:
        raise ValueError("unsupported receipt schema_version")
    if receipt["claim_status"] != CLAIM_STATUS:
        raise ValueError("receipt claim_status mismatch")
    if receipt["manifest_schema_version"] != SCHEMA_VERSION:
        raise ValueError("receipt manifest_schema_version mismatch")

    if not isinstance(receipt["run_id"], str) or not receipt["run_id"].strip():
        raise ValueError("receipt run_id must be a non-empty string")
    _validate_receipt_summary_path(receipt["summary_path"])
    if not isinstance(receipt["git_commit"], str) or not _GIT_COMMIT_RE.fullmatch(receipt["git_commit"]):
        raise ValueError("receipt git_commit must be a lowercase 40-character hex SHA")
    if not isinstance(receipt["summary_sha256"], str) or not _SHA256_RE.fullmatch(receipt["summary_sha256"]):
        raise ValueError("receipt summary_sha256 must be a lowercase 64-character hex digest")

    summary_size_bytes = receipt["summary_size_bytes"]
    if isinstance(summary_size_bytes, bool) or not isinstance(summary_size_bytes, int) or summary_size_bytes <= 0:
        raise ValueError("receipt summary_size_bytes must be a positive integer")

    row_count = receipt["row_count"]
    if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count != 4:
        raise ValueError("receipt row_count must equal 4 for four_cell_semantics")

    numeric_fields = receipt["numeric_fields"]
    if not isinstance(numeric_fields, list) or not numeric_fields:
        raise ValueError("receipt numeric_fields must be a non-empty list")
    if any(not isinstance(field, str) or not field.strip() for field in numeric_fields):
        raise ValueError("receipt numeric_fields entries must be non-empty strings")
    if len(numeric_fields) != len(set(numeric_fields)):
        raise ValueError("receipt numeric_fields must not contain duplicates")

    parameters = receipt["parameters"]
    if not isinstance(parameters, Mapping) or set(parameters) != {"n_run", "t_run_ms"}:
        raise ValueError("receipt parameters must contain exactly n_run and t_run_ms")
    for field in ("n_run", "t_run_ms"):
        value = parameters[field]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"receipt parameters.{field} must be a positive integer")

    if receipt["validated_gates"] != list(_VALIDATED_GATES):
        raise ValueError("receipt validated_gates mismatch")
    limitations = receipt["limitations"]
    if not isinstance(limitations, list) or not limitations:
        raise ValueError("receipt limitations must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in limitations):
        raise ValueError("receipt limitations entries must be non-empty strings")


def serialize_targeted_validation_receipt(receipt: object) -> bytes:
    """Return canonical UTF-8 JSON bytes after validating the receipt contract."""

    validate_targeted_validation_receipt(receipt)
    return (json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode(
        "utf-8"
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
    receipt = {
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
    validate_targeted_validation_receipt(receipt)
    return receipt
