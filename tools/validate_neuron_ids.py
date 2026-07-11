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
VALIDATOR_VERSION = "0.1.0"
CLAIM_STATUS = "not_interpretable_as_neuroscience"


def validate_neuron_id(value: Any) -> str | None:
    """Return a machine-readable reason code, or ``None`` when valid.

    IDs are intentionally treated as opaque decimal strings. Numeric coercion
    is forbidden even when a value could be converted losslessly.
    """
    if not isinstance(value, str):
        return "non_string"
    if value == "":
        return "empty"
    if value != value.strip():
        return "surrounding_whitespace"
    if value[0] in "+-":
        return "signed"
    if not value.isascii() or not value.isdecimal():
        return "non_decimal"
    return None


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--column", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    records = load_records(args.input)
    report = validate_records(records, args.column)
    rendered = deterministic_json(report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
