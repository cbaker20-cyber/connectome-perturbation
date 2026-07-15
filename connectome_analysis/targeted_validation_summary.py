"""Semantic checks for staged targeted-validation summary rows.

The validator is intentionally format-agnostic: callers parse CSV or another tabular
format, then pass row mappings here. It checks only repository-local completeness and
consistency. It does not assess biological validity or execute simulations.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence

from connectome_analysis.targeted_validation_manifest import EXPECTED_CELLS

_REQUIRED_FIELDS = {"source", "target", "n_run", "t_run_ms"}


def _positive_int(value: object, context: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{context} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} must be a positive integer") from exc
    if parsed <= 0 or str(value).strip() not in {str(parsed), f"{parsed}.0"}:
        raise ValueError(f"{context} must be a positive integer")
    return parsed


def validate_targeted_validation_summary_rows(
    rows: object,
    manifest: object,
    *,
    numeric_fields: Sequence[str],
) -> None:
    """Validate complete four-cell summary coverage against a run manifest.

    ``numeric_fields`` must be explicitly declared by the caller. Every declared field
    must exist in every row and parse to a finite float. The function raises
    ``ValueError`` on the first failed gate.
    """

    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ValueError("manifest.parameters must be an object")
    expected_n_run = _positive_int(parameters.get("n_run"), "manifest.parameters.n_run")
    expected_t_run_ms = _positive_int(parameters.get("t_run_ms"), "manifest.parameters.t_run_ms")

    if not isinstance(numeric_fields, Sequence) or isinstance(numeric_fields, (str, bytes)):
        raise ValueError("numeric_fields must be an array")
    declared_numeric_fields = list(numeric_fields)
    if not declared_numeric_fields or any(not isinstance(field, str) or not field for field in declared_numeric_fields):
        raise ValueError("numeric_fields must contain non-empty strings")
    if len(declared_numeric_fields) != len(set(declared_numeric_fields)):
        raise ValueError("numeric_fields must not contain duplicates")
    if _REQUIRED_FIELDS.intersection(declared_numeric_fields):
        raise ValueError("numeric_fields must not repeat required identity or parameter fields")

    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("rows must be a non-empty array")

    observed_cells: list[tuple[str, str]] = []
    for index, row in enumerate(rows):
        context = f"rows[{index}]"
        if not isinstance(row, Mapping):
            raise ValueError(f"{context} must be an object")
        missing = (_REQUIRED_FIELDS | set(declared_numeric_fields)) - set(row)
        if missing:
            raise ValueError(f"{context} missing required fields: {sorted(missing)}")

        source = row["source"]
        target = row["target"]
        if not isinstance(source, str) or not source:
            raise ValueError(f"{context}.source must be a non-empty string")
        if not isinstance(target, str) or not target:
            raise ValueError(f"{context}.target must be a non-empty string")
        observed_cells.append((source, target))

        if _positive_int(row["n_run"], f"{context}.n_run") != expected_n_run:
            raise ValueError(f"{context}.n_run disagrees with manifest")
        if _positive_int(row["t_run_ms"], f"{context}.t_run_ms") != expected_t_run_ms:
            raise ValueError(f"{context}.t_run_ms disagrees with manifest")

        for field in declared_numeric_fields:
            try:
                value = float(row[field])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{context}.{field} must be numeric") from exc
            if not math.isfinite(value):
                raise ValueError(f"{context}.{field} must be finite")

    if len(observed_cells) != len(set(observed_cells)):
        raise ValueError("summary rows must not contain duplicate cells")
    if set(observed_cells) != set(EXPECTED_CELLS):
        raise ValueError("summary rows must cover exactly the four declared source-target cells")


def validate_targeted_validation_summary_artifact(
    rows: object,
    manifest: object,
    *,
    artifact_path: str,
    artifact_bytes: bytes,
    numeric_fields: Sequence[str],
) -> None:
    """Tie parsed summary rows to one manifest-declared output artifact.

    The caller must pass the exact bytes that were parsed into ``rows``. This function
    fails closed unless the manifest has exactly one matching output record and its
    declared byte size and SHA-256 digest match those bytes. It then applies the row
    semantic gates above. It does not prove that parsing was correct, execute a run, or
    support neuroscience interpretation.
    """

    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    if not isinstance(artifact_path, str) or not artifact_path.strip():
        raise ValueError("artifact_path must be a non-empty string")
    if not isinstance(artifact_bytes, bytes):
        raise ValueError("artifact_bytes must be bytes")

    outputs = manifest.get("outputs")
    if not isinstance(outputs, Sequence) or isinstance(outputs, (str, bytes)):
        raise ValueError("manifest.outputs must be an array")
    matches = [record for record in outputs if isinstance(record, Mapping) and record.get("path") == artifact_path]
    if len(matches) != 1:
        raise ValueError("artifact_path must match exactly one manifest output record")

    record = matches[0]
    declared_size = record.get("size_bytes")
    if isinstance(declared_size, bool) or not isinstance(declared_size, int) or declared_size <= 0:
        raise ValueError("manifest output size_bytes must be a positive integer")
    if len(artifact_bytes) != declared_size:
        raise ValueError(
            f"artifact byte size disagrees with manifest: manifest={declared_size} actual={len(artifact_bytes)}"
        )

    declared_digest = record.get("sha256")
    actual_digest = hashlib.sha256(artifact_bytes).hexdigest()
    if declared_digest != actual_digest:
        raise ValueError(
            f"artifact SHA-256 disagrees with manifest: manifest={declared_digest!r} actual={actual_digest!r}"
        )

    validate_targeted_validation_summary_rows(rows, manifest, numeric_fields=numeric_fields)
