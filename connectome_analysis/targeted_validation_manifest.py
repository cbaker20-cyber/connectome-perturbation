"""Fail-closed validation for the planned four-cell targeted validation run.

This module validates an already-parsed manifest mapping. It deliberately does not
parse YAML so the validation contract remains dependency-free and testable without
claiming that an experiment has run.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

SCHEMA_VERSION = "atlas-targeted-validation-run-manifest/v0"
CLAIM_STATUS = "not_interpretable_as_neuroscience"
EXPECTED_CELLS = (
    ("sugar", "AN"),
    ("sugar", "brain_motor_neuron"),
    ("gustatory", "AN"),
    ("gustatory", "brain_motor_neuron"),
)
REQUIRED_OUTPUTS = (
    "sweep_summary.csv",
    "sweep_run_info.csv",
    "ranked_targeted_validation.csv",
    "targeted_validation_readable_summary.txt",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _require_exact_fields(value: Mapping, expected: set[str], context: str) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        raise ValueError(f"{context} missing required fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"{context} contains unknown fields: {sorted(unknown)}")


def _require_nonempty_string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} must be a non-empty string")
    return value


def _validate_file_record(record: object, context: str) -> None:
    if not isinstance(record, Mapping):
        raise ValueError(f"{context} must be an object")
    _require_exact_fields(record, {"path", "size_bytes", "sha256"}, context)
    _require_nonempty_string(record["path"], f"{context}.path")
    if isinstance(record["size_bytes"], bool) or not isinstance(record["size_bytes"], int) or record["size_bytes"] <= 0:
        raise ValueError(f"{context}.size_bytes must be a positive integer")
    if not isinstance(record["sha256"], str) or not _SHA256_RE.fullmatch(record["sha256"]):
        raise ValueError(f"{context}.sha256 must be 64 lowercase hexadecimal characters")


def validate_targeted_validation_manifest(manifest: object) -> None:
    """Validate a parsed targeted-validation manifest or raise ``ValueError``.

    The function checks provenance fields and exact four-cell coverage only. It does
    not verify files on disk, execute simulations, or support biological inference.
    """

    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")

    _require_exact_fields(
        manifest,
        {
            "schema_version",
            "claim_status",
            "run_id",
            "git_commit",
            "command",
            "backend",
            "parameters",
            "sources",
            "targets",
            "cells",
            "inputs",
            "outputs",
            "limitations",
        },
        "manifest",
    )

    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {manifest['schema_version']!r}")
    if manifest["claim_status"] != CLAIM_STATUS:
        raise ValueError(f"claim_status must be {CLAIM_STATUS!r}")
    _require_nonempty_string(manifest["run_id"], "run_id")
    _require_nonempty_string(manifest["command"], "command")
    if not isinstance(manifest["git_commit"], str) or not _GIT_SHA_RE.fullmatch(manifest["git_commit"]):
        raise ValueError("git_commit must be a full 40-character lowercase hexadecimal SHA")

    backend = manifest["backend"]
    if not isinstance(backend, Mapping):
        raise ValueError("backend must be an object")
    _require_exact_fields(backend, {"name", "version"}, "backend")
    _require_nonempty_string(backend["name"], "backend.name")
    _require_nonempty_string(backend["version"], "backend.version")

    parameters = manifest["parameters"]
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be an object")
    _require_exact_fields(parameters, {"n_run", "t_run_ms", "seed_policy"}, "parameters")
    for field in ("n_run", "t_run_ms"):
        value = parameters[field]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"parameters.{field} must be a positive integer")
    _require_nonempty_string(parameters["seed_policy"], "parameters.seed_policy")

    sources = manifest["sources"]
    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)):
        raise ValueError("sources must be an array")
    source_counts: dict[str, int] = {}
    for index, source in enumerate(sources):
        context = f"sources[{index}]"
        if not isinstance(source, Mapping):
            raise ValueError(f"{context} must be an object")
        _require_exact_fields(source, {"label", "id_count"}, context)
        label = _require_nonempty_string(source["label"], f"{context}.label")
        count = source["id_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError(f"{context}.id_count must be a positive integer")
        if label in source_counts:
            raise ValueError(f"duplicate source label: {label!r}")
        source_counts[label] = count
    if set(source_counts) != {"sugar", "gustatory"}:
        raise ValueError("sources must contain exactly sugar and gustatory")
    if source_counts["sugar"] != 21:
        raise ValueError("sugar source id_count must equal 21")

    targets = manifest["targets"]
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        raise ValueError("targets must be an array")
    target_labels = [_require_nonempty_string(value, "target label") for value in targets]
    if len(target_labels) != len(set(target_labels)):
        raise ValueError("targets must not contain duplicates")
    if set(target_labels) != {"AN", "brain_motor_neuron"}:
        raise ValueError("targets must contain exactly AN and brain_motor_neuron")

    cells = manifest["cells"]
    if not isinstance(cells, Sequence) or isinstance(cells, (str, bytes)):
        raise ValueError("cells must be an array")
    observed_cells: list[tuple[str, str]] = []
    for index, cell in enumerate(cells):
        context = f"cells[{index}]"
        if not isinstance(cell, Mapping):
            raise ValueError(f"{context} must be an object")
        _require_exact_fields(cell, {"source", "target"}, context)
        observed_cells.append(
            (
                _require_nonempty_string(cell["source"], f"{context}.source"),
                _require_nonempty_string(cell["target"], f"{context}.target"),
            )
        )
    if len(observed_cells) != len(set(observed_cells)):
        raise ValueError("cells must not contain duplicates")
    if set(observed_cells) != set(EXPECTED_CELLS):
        raise ValueError("cells must cover exactly the four declared source-target combinations")

    for field in ("inputs", "outputs"):
        records = manifest[field]
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)) or not records:
            raise ValueError(f"{field} must be a non-empty array")
        paths: list[str] = []
        for index, record in enumerate(records):
            _validate_file_record(record, f"{field}[{index}]")
            paths.append(record["path"])
        if len(paths) != len(set(paths)):
            raise ValueError(f"{field} paths must not contain duplicates")

    output_paths = {record["path"] for record in manifest["outputs"]}
    missing_outputs = [path for path in REQUIRED_OUTPUTS if path not in output_paths]
    if missing_outputs:
        raise ValueError(f"outputs missing required paths: {missing_outputs}")
    if not any(path.startswith("logs/") and len(path) > len("logs/") for path in output_paths):
        raise ValueError("outputs must include a non-empty path under logs/")

    limitations = manifest["limitations"]
    if not isinstance(limitations, Sequence) or isinstance(limitations, (str, bytes)) or not limitations:
        raise ValueError("limitations must be a non-empty array")
    for index, limitation in enumerate(limitations):
        _require_nonempty_string(limitation, f"limitations[{index}]")
