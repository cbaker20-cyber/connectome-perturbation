#!/usr/bin/env python3
"""Validate repository-local synthetic Atlas JSON artifacts.

This validator checks representation and declared limitations only. It does not
validate neuron identity, biological connectivity, neural dynamics, behavior,
or any neuroscience conclusion.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import NoReturn

RUN_RECORD_FIELDS = {
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

CONNECTION_TABLE_FIELDS = {
    "schema_version",
    "artifact_type",
    "claim_status",
    "graph_id",
    "input_ids",
    "output_ids",
    "parameters",
    "baseline_output_vector",
    "rows",
    "limitations",
}

CONNECTION_ROW_FIELDS = {
    "source_id",
    "target_id",
    "baseline_output_vector",
    "perturbed_output_vector",
    "percent_output_change",
    "cosine_distance",
}

VULNERABILITY_MATRIX_FIELDS = {
    "schema_version",
    "artifact_type",
    "claim_status",
    "matrix_id",
    "score_name",
    "context_ids",
    "target_ids",
    "values",
    "source_artifacts",
    "limitations",
}

VULNERABILITY_SOURCE_FIELDS = {
    "context_id",
    "schema_version",
    "artifact_id",
    "artifact_sha256",
    "target_axis",
}

SUPPORTED_VULNERABILITY_SCORES = {"percent_output_change", "cosine_distance"}
SUPPORTED_VULNERABILITY_SOURCE_SCHEMAS = {"atlas-node-lesion-table/v0"}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


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


def _validate_exact_fields(record: dict[str, object], expected: set[str], *, field: str) -> None:
    fields = set(record)
    missing = sorted(expected - fields)
    unknown = sorted(fields - expected)
    if missing:
        _fail(f"{field} missing required fields: {', '.join(missing)}")
    if unknown:
        _fail(f"{field} unknown fields: {', '.join(unknown)}")


def _validate_id_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list):
        _fail(f"{field} must be an array")
    if any(not isinstance(item, str) or not item for item in value):
        _fail(f"{field} must contain only non-empty strings")
    if len(set(value)) != len(value):
        _fail(f"{field} must not contain duplicates")
    return value


def _validate_vector(value: object, *, field: str, expected_length: int) -> list[object]:
    if not isinstance(value, list):
        _fail(f"{field} must be an array")
    if any(not _is_finite_number(item) for item in value):
        _fail(f"{field} must contain only finite numbers")
    if len(value) != expected_length:
        _fail(f"{field} length must equal output_ids length")
    return value


def _validate_parameters(value: object) -> None:
    if not isinstance(value, dict):
        _fail("parameters must be an object")
    if set(value) != {"steps", "decay", "seed"}:
        _fail("parameters must contain exactly steps, decay, and seed")
    if not _is_integer(value["steps"]) or value["steps"] < 0:
        _fail("parameters.steps must be a non-negative integer")
    if not _is_finite_number(value["decay"]):
        _fail("parameters.decay must be a finite number")
    if not _is_integer(value["seed"]):
        _fail("parameters.seed must be an integer")


def _validate_limitations(value: object) -> None:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        _fail("limitations must be a non-empty array of non-empty strings")


def validate_run_record(record: dict[str, object]) -> None:
    """Raise ValueError when a record violates atlas-run-record/v0."""
    _validate_exact_fields(record, RUN_RECORD_FIELDS, field="record")

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

    _validate_parameters(record["parameters"])
    _validate_id_list(record["input_ids"], field="input_ids")
    output_ids = _validate_id_list(record["output_ids"], field="output_ids")
    _validate_vector(record["output_vector"], field="output_vector", expected_length=len(output_ids))
    _validate_limitations(record["limitations"])


def validate_connection_lesion_table(record: dict[str, object]) -> None:
    """Raise ValueError when a record violates atlas-connection-lesion-table/v0."""
    _validate_exact_fields(record, CONNECTION_TABLE_FIELDS, field="record")

    fixed_values = {
        "schema_version": "atlas-connection-lesion-table/v0",
        "artifact_type": "synthetic_connection_lesion_scores",
        "claim_status": "not_interpretable_as_neuroscience",
    }
    for field, expected in fixed_values.items():
        if record[field] != expected:
            _fail(f"{field} must equal {expected!r}")

    if not isinstance(record["graph_id"], str) or not record["graph_id"]:
        _fail("graph_id must be a non-empty string")

    _validate_parameters(record["parameters"])
    _validate_id_list(record["input_ids"], field="input_ids")
    output_ids = _validate_id_list(record["output_ids"], field="output_ids")
    baseline = _validate_vector(
        record["baseline_output_vector"],
        field="baseline_output_vector",
        expected_length=len(output_ids),
    )

    rows = record["rows"]
    if not isinstance(rows, list):
        _fail("rows must be an array")

    seen_edges: set[tuple[str, str]] = set()
    previous_rank_key: tuple[float, float, str, str] | None = None
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            _fail(f"rows[{index}] must be an object")
        _validate_exact_fields(row, CONNECTION_ROW_FIELDS, field=f"rows[{index}]")

        source_id = row["source_id"]
        target_id = row["target_id"]
        if not isinstance(source_id, str) or not source_id:
            _fail(f"rows[{index}].source_id must be a non-empty string")
        if not isinstance(target_id, str) or not target_id:
            _fail(f"rows[{index}].target_id must be a non-empty string")
        edge = (source_id, target_id)
        if edge in seen_edges:
            _fail("rows must not contain duplicate directed edges")
        seen_edges.add(edge)

        row_baseline = _validate_vector(
            row["baseline_output_vector"],
            field=f"rows[{index}].baseline_output_vector",
            expected_length=len(output_ids),
        )
        if row_baseline != baseline:
            _fail(f"rows[{index}].baseline_output_vector must equal table baseline_output_vector")
        _validate_vector(
            row["perturbed_output_vector"],
            field=f"rows[{index}].perturbed_output_vector",
            expected_length=len(output_ids),
        )

        percent_change = row["percent_output_change"]
        cosine_distance = row["cosine_distance"]
        if not _is_finite_number(percent_change) or float(percent_change) < 0:
            _fail(f"rows[{index}].percent_output_change must be a non-negative finite number")
        if not _is_finite_number(cosine_distance) or not 0 <= float(cosine_distance) <= 2:
            _fail(f"rows[{index}].cosine_distance must be a finite number between 0 and 2")

        rank_key = (-float(percent_change), -float(cosine_distance), source_id, target_id)
        if previous_rank_key is not None and rank_key < previous_rank_key:
            _fail("rows must use deterministic descending metric order with string-ID tie-breaking")
        previous_rank_key = rank_key

    _validate_limitations(record["limitations"])


def validate_vulnerability_signature_matrix(record: dict[str, object]) -> None:
    """Raise ValueError when a record violates the repository-local matrix v0 schema."""
    _validate_exact_fields(record, VULNERABILITY_MATRIX_FIELDS, field="record")

    fixed_values = {
        "schema_version": "atlas-vulnerability-signature-matrix/v0",
        "artifact_type": "synthetic_vulnerability_signature_matrix",
        "claim_status": "not_interpretable_as_neuroscience",
    }
    for field, expected in fixed_values.items():
        if record[field] != expected:
            _fail(f"{field} must equal {expected!r}")

    if not isinstance(record["matrix_id"], str) or not record["matrix_id"]:
        _fail("matrix_id must be a non-empty string")
    if record["score_name"] not in SUPPORTED_VULNERABILITY_SCORES:
        _fail("score_name must be a supported non-negative lesion metric")

    context_ids = _validate_id_list(record["context_ids"], field="context_ids")
    target_ids = _validate_id_list(record["target_ids"], field="target_ids")
    if not context_ids or not target_ids:
        _fail("context_ids and target_ids must be non-empty")

    values = record["values"]
    if not isinstance(values, list) or len(values) != len(context_ids):
        _fail("values must contain exactly one row per context_id")
    for row_index, row in enumerate(values):
        if not isinstance(row, list) or len(row) != len(target_ids):
            _fail(f"values[{row_index}] must contain exactly one value per target_id")
        if any(not _is_finite_number(value) or float(value) < 0 for value in row):
            _fail(f"values[{row_index}] must contain only non-negative finite numbers")

    sources = record["source_artifacts"]
    if not isinstance(sources, list) or len(sources) != len(context_ids):
        _fail("source_artifacts must contain exactly one entry per context_id")
    seen_artifacts: set[str] = set()
    for index, (context_id, source) in enumerate(zip(context_ids, sources, strict=True)):
        if not isinstance(source, dict):
            _fail(f"source_artifacts[{index}] must be an object")
        _validate_exact_fields(source, VULNERABILITY_SOURCE_FIELDS, field=f"source_artifacts[{index}]")
        if source["context_id"] != context_id:
            _fail(f"source_artifacts[{index}].context_id must match context_ids order")
        if source["schema_version"] not in SUPPORTED_VULNERABILITY_SOURCE_SCHEMAS:
            _fail(f"source_artifacts[{index}].schema_version is unsupported")
        artifact_id = source["artifact_id"]
        if not isinstance(artifact_id, str) or not artifact_id:
            _fail(f"source_artifacts[{index}].artifact_id must be a non-empty string")
        if artifact_id in seen_artifacts:
            _fail("source_artifacts must not contain duplicate artifact_id values")
        seen_artifacts.add(artifact_id)
        digest = source["artifact_sha256"]
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            _fail(f"source_artifacts[{index}].artifact_sha256 must be lowercase SHA-256 hex")
        source_axis = _validate_id_list(source["target_axis"], field=f"source_artifacts[{index}].target_axis")
        if source_axis != target_ids:
            _fail(f"source_artifacts[{index}].target_axis must exactly match target_ids order")

    _validate_limitations(record["limitations"])


def validate_record(record: object) -> None:
    """Dispatch validation by repository-local schema_version."""
    if not isinstance(record, dict):
        _fail("record must be a JSON object")
    schema_version = record.get("schema_version")
    if schema_version == "atlas-run-record/v0":
        validate_run_record(record)
    elif schema_version == "atlas-connection-lesion-table/v0":
        validate_connection_lesion_table(record)
    elif schema_version == "atlas-vulnerability-signature-matrix/v0":
        validate_vulnerability_signature_matrix(record)
    else:
        _fail("unsupported schema_version")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Path to a UTF-8 JSON artifact")
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
