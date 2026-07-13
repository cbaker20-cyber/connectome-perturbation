#!/usr/bin/env python3
"""Validate repository-local synthetic atlas-run-record/v0 JSON artifacts.

This validator checks representation and declared limitations only. It does not
validate neuron identity, biological connectivity, neural dynamics, behavior,
or any neuroscience conclusion.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import NoReturn

REQUIRED_FIELDS = {
    "schema_version",
    "artifact_type",
    "claim_status",
    "model",
    "parameters",
    "input_ids",
    "output_ids",
    "output_vector",
    "limitations",
}


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validate_id_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list):
        _fail(f"{field} must be an array")
    if any(not isinstance(item, str) or not item for item in value):
        _fail(f"{field} must contain only non-empty strings")
    if len(set(value)) != len(value):
        _fail(f"{field} must not contain duplicates")
    return value


def validate_record(record: object) -> None:
    """Raise ValueError when a record violates atlas-run-record/v0."""
    if not isinstance(record, dict):
        _fail("record must be a JSON object")

    fields = set(record)
    missing = sorted(REQUIRED_FIELDS - fields)
    unknown = sorted(fields - REQUIRED_FIELDS)
    if missing:
        _fail(f"missing required fields: {', '.join(missing)}")
    if unknown:
        _fail(f"unknown fields: {', '.join(unknown)}")

    fixed_values = {
        "schema_version": "atlas-run-record/v0",
        "artifact_type": "toy_signal_run_record",
        "claim_status": "not_interpretable_as_neuroscience",
    }
    for field, expected in fixed_values.items():
        if record[field] != expected:
            _fail(f"{field} must equal {expected!r}")

    if not isinstance(record["model"], str) or not record["model"]:
        _fail("model must be a non-empty string")

    parameters = record["parameters"]
    if not isinstance(parameters, dict):
        _fail("parameters must be an object")
    if set(parameters) != {"steps", "decay", "seed"}:
        _fail("parameters must contain exactly steps, decay, and seed")
    if not _is_integer(parameters["steps"]) or parameters["steps"] < 0:
        _fail("parameters.steps must be a non-negative integer")
    if not _is_finite_number(parameters["decay"]):
        _fail("parameters.decay must be a finite number")
    if not _is_integer(parameters["seed"]):
        _fail("parameters.seed must be an integer")

    _validate_id_list(record["input_ids"], field="input_ids")
    output_ids = _validate_id_list(record["output_ids"], field="output_ids")

    output_vector = record["output_vector"]
    if not isinstance(output_vector, list):
        _fail("output_vector must be an array")
    if any(not _is_finite_number(value) for value in output_vector):
        _fail("output_vector must contain only finite numbers")
    if len(output_vector) != len(output_ids):
        _fail("output_vector length must equal output_ids length")

    limitations = record["limitations"]
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not isinstance(item, str) or not item for item in limitations)
    ):
        _fail("limitations must be a non-empty array of non-empty strings")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Path to a UTF-8 JSON run record")
    args = parser.parse_args()

    try:
        with args.record.open("r", encoding="utf-8") as handle:
            record = json.load(handle, parse_constant=lambda value: _fail(f"invalid numeric constant: {value}"))
        validate_record(record)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))

    print(f"valid: {args.record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
