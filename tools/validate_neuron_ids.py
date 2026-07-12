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

SCHEMA_VERSION = "1.1"
VALIDATOR_VERSION = "0.3.1"
CLAIM_STATUS = "not_interpretable_as_neuroscience"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_MISSING = object()


def validate_neuron_id(value: Any) -> str | None:
    """Return a machine-readable reason code, or ``None`` when valid."""
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
    """Classify representation and optional original-text provenance."""
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


def parse_availability(value: Any) -> Any:
    """Decode provenance availability without touching identifier values.

    JSON booleans are accepted directly. CSV text must be exactly ``true`` or
    ``false`` (case-insensitive); blanks and all other values are malformed.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return _MISSING


def validate_records(
    records: Iterable[dict[str, Any]],
    column: str,
    *,
    original_text_column: str | None = None,
    availability_column: str | None = None,
) -> dict[str, Any]:
    """Validate records and return a deterministic aggregate report."""
    total = 0
    statuses: Counter[str] = Counter()

    for record in records:
        total += 1
        if column not in record:
            statuses["missing_column"] += 1
            continue

        kwargs: dict[str, Any] = {}
        original_text_missing = (
            original_text_column is not None and original_text_column not in record
        )
        if original_text_column is not None and not original_text_missing:
            kwargs["original_text"] = record[original_text_column]

        parsed_availability: Any = _MISSING
        if availability_column is not None:
            if availability_column not in record:
                statuses["invalid_provenance"] += 1
                continue
            parsed_availability = parse_availability(record[availability_column])
            if parsed_availability is _MISSING:
                statuses["invalid_provenance"] += 1
                continue
            kwargs["provenance_original_text_available"] = parsed_availability

        if original_text_missing and parsed_availability is not False:
            statuses["invalid_provenance"] += 1
            continue

        status = classify_neuron_id(record[column], **kwargs)
        statuses[status] += 1

    valid = statuses.get("valid_exact_string", 0)
    invalid = total - valid
    return {
        "schema_version": SCHEMA_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "claim_status": CLAIM_STATUS,
        "column": column,
        "original_text_column": original_text_column,
        "availability_column": availability_column,
        "record_count": total,
        "valid_count": valid,
        "invalid_count": invalid,
        "status_counts": dict(sorted(statuses.items())),
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
    """Resolve safe I/O paths and confine reports to the validation output tree."""
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

    validation_root = (
        repository_root.resolve(strict=True) / "results" / "validation"
    ).resolve(strict=False)
    try:
        resolved_report.relative_to(validation_root)
    except ValueError as exc:
        raise ValueError(
            "report path must resolve under results/validation"
        ) from exc
    return resolved_input, resolved_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--column", required=True)
    parser.add_argument("--original-text-column")
    parser.add_argument("--availability-column")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        input_path, report_path = resolve_io_paths(args.input, args.report)
        records = load_records(input_path)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    report = validate_records(
        records,
        args.column,
        original_text_column=args.original_text_column,
        availability_column=args.availability_column,
    )
    rendered = deterministic_json(report)
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
