#!/usr/bin/env python3
"""Validate neuron identifiers without numeric coercion.

This module checks representation integrity only. Passing validation does not
establish dataset provenance, biological identity, or any neuroscience claim.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
VALIDATOR_VERSION = "0.2.0"
CLAIM_STATUS = "not_interpretable_as_neuroscience"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_MISSING = object()


def validate_neuron_id(value: Any) -> str | None:
    """Return a machine-readable reason code, or ``None`` when valid.

    IDs are intentionally treated as opaque decimal strings. Numeric coercion
    is forbidden even when a value could be converted losslessly.
    """
    if value is None or value == "":
        return "missing_value"
    if not isinstance(value, str):
        return "non_string"
    if value != value.strip():
        return "surrounding_whitespace"
    if value[0] in "+-":
        return "signed"
    if not value.isascii() or not value.isdecimal():
        return "non_decimal"
    return None


def classify_neuron_id(
    candidate: Any,
    *,
    original_text: Any = _MISSING,
    provenance_original_text_available: Any = _MISSING,
) -> str:
    """Classify representation and optional original-text provenance.

    Comparison is deliberately byte-for-byte at the Python string level. The
    function never converts an identifier with ``int`` or ``float``.

    Absent provenance metadata is distinct from an explicit statement that
    original text was unavailable. Explicitly unavailable original text yields
    ``unverified_precision``; malformed or contradictory provenance yields
    ``invalid_provenance``.
    """
    reason = validate_neuron_id(candidate)
    if reason == "non_string":
        return "invalid_type"
    if reason == "missing_value":
        return "missing_value"
    if reason is not None:
        return "invalid_format"

    availability_supplied = provenance_original_text_available is not _MISSING
    original_supplied = original_text is not _MISSING

    if availability_supplied and not isinstance(
        provenance_original_text_available, bool
    ):
        return "invalid_provenance"

    if original_supplied:
        if provenance_original_text_available is False:
            return "invalid_provenance"
        if validate_neuron_id(original_text) is not None:
            return "invalid_provenance"
        if candidate != original_text:
            return "suspected_precision_loss"
        return "valid_exact_string"

    if provenance_original_text_available is True:
        return "invalid_provenance"
    if provenance_original_text_available is False:
        return "unverified_precision"
    return "valid_exact_string"


def validate_records(records: Iterable[dict[str, Any]], column: str) -> dict[str, Any]:
    """Validate one named column and return a deterministic summary."""
    total = 0
    valid = 0
    reasons: Counter[str] = Counter()
    for record in records:
        total += 1
        if column not in record:
            reasons["missing_column"] += 1
            continue
        reason = validate_neuron_id(record[column])
        if reason is None:
            valid += 1
        else:
            reasons[reason] += 1

    invalid = total - valid
    return {
        "schema_version": SCHEMA_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "claim_status": CLAIM_STATUS,
        "column": column,
        "record_count": total,
        "valid_count": valid,
        "invalid_count": invalid,
        "reason_counts": dict(sorted(reasons.items())),
        "status": "valid" if invalid == 0 else "invalid",
    }


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load CSV rows or JSON records without modifying the source file."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            value = value.get("records")
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise ValueError("JSON input must be a list of objects or an object with a records list")
        return value
    raise ValueError("input must use .csv or .json")


def deterministic_json(value: dict[str, Any]) -> str:
    """Serialize reports with stable key ordering and a final newline."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def resolve_repository_path(
    path: Path,
    repository_root: Path = REPOSITORY_ROOT,
    *,
    must_exist: bool,
) -> Path:
    """Resolve ``path`` and reject traversal or symlink escape from the repo."""
    root = repository_root.resolve(strict=True)
    candidate = path.resolve(strict=must_exist)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {path}") from exc
    return candidate


def resolve_io_paths(
    input_path: Path,
    report_path: Path | None,
    repository_root: Path = REPOSITORY_ROOT,
) -> tuple[Path, Path | None]:
    """Resolve safe input/output paths and prevent source-file overwrite."""
    resolved_input = resolve_repository_path(
        input_path, repository_root, must_exist=True
    )
    if report_path is None:
        return resolved_input, None

    resolved_report = resolve_repository_path(
        report_path, repository_root, must_exist=False
    )
    if resolved_report == resolved_input:
        raise ValueError("report path must not resolve to the input path")
    return resolved_input, resolved_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--column", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        input_path, report_path = resolve_io_paths(args.input, args.report)
        records = load_records(input_path)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    report = validate_records(records, args.column)
    rendered = deterministic_json(report)
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
