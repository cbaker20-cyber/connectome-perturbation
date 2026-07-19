#!/usr/bin/env python3
"""Validate basic reproducibility artifacts.

This script intentionally checks metadata plumbing, not neuroscience results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_EXPERIMENT_REGISTRY = "03_EXPERIMENT_REGISTRY.csv"

REQUIRED_INPUT_MANIFEST_FIELDS = {"schema_version", "generated_at_utc", "input_count", "inputs"}
REQUIRED_INPUT_FIELDS = {"path", "filename", "extension", "size_bytes", "sha256", "guessed_role", "provenance"}
REQUIRED_OUTPUT_FIELDS = {
    "schema_version",
    "created_at_utc",
    "status",
    "command",
    "repo_commit",
    "config_path",
    "config_sha256",
    "input_manifest_path",
    "input_manifest_present",
    "input_checksums",
    "claim_status",
}
REQUIRED_PROVENANCE_FIELDS = {
    "dataset_name",
    "release_or_materialization",
    "canonical_url_or_doi",
    "citation",
    "license_or_terms",
    "access_date",
    "redistribution_status",
    "schema_notes",
    "row_count",
    "preprocessing_notes",
}
UNKNOWN_PROVENANCE_VALUES = {None, "", "unknown", "UNKNOWN", "Unknown"}
PROVENANCE_COMPLETE_STATUS = "provenance_complete"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def has_claim_ready_value(value: Any) -> bool:
    """Return whether a provenance field is filled enough for strict validation.

    This is intentionally conservative. Free-text fields may later need stronger
    schema-specific validation, but strict mode should at least block null,
    blank, and explicitly unknown provenance before any biological claim.
    """
    if isinstance(value, str):
        return value.strip() not in UNKNOWN_PROVENANCE_VALUES
    if value in UNKNOWN_PROVENANCE_VALUES:
        return False
    return True


def is_iso_datetime_with_timezone(value: Any) -> bool:
    """Return whether a value is an ISO-8601 datetime with timezone info."""
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def is_sha256_hex(value: Any) -> bool:
    """Return whether a value is a canonical lowercase SHA-256 digest."""
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def is_iso_date(value: Any) -> bool:
    """Return whether a value is an ISO-8601 calendar date (YYYY-MM-DD)."""
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.strip())
    except ValueError:
        return False
    return len(value.strip()) == 10 and value[4] == "-" and value[7] == "-"


def is_valid_url_or_doi(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    lowered = value.strip().lower()
    return lowered.startswith("http://") or lowered.startswith("https://") or lowered.startswith("doi:")


def repo_relative_path(repo_root: Path, path_value: Any, label: str, errors: list[str]) -> Path | None:
    """Resolve a manifest path only if it is relative and stays inside repo_root."""
    if not isinstance(path_value, str) or not path_value.strip():
        errors.append(f"{label} must be a non-empty string")
        return None

    candidate = Path(path_value)
    if candidate.is_absolute():
        errors.append(f"{label} must be repo-relative, not absolute: {path_value}")
        return None

    resolved_root = repo_root.resolve()
    resolved_candidate = (resolved_root / candidate).resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError:
        errors.append(f"{label} must stay within the repository: {path_value}")
        return None

    return resolved_candidate


def load_json(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return None
    require(isinstance(value, dict), f"{label} must be a JSON object", errors)
    return value if isinstance(value, dict) else None


def validate_input_manifest(repo_root: Path, manifest_path: Path, errors: list[str], require_provenance: bool = False) -> dict[str, Any] | None:
    require(manifest_path.exists(), f"missing input manifest: {manifest_path}", errors)
    if not manifest_path.exists():
        return None
    manifest = load_json(manifest_path, errors, "input manifest")
    if manifest is None:
        return None
    missing_manifest_fields = REQUIRED_INPUT_MANIFEST_FIELDS - set(manifest)
    require(not missing_manifest_fields, f"input manifest missing fields: {sorted(missing_manifest_fields)}", errors)
    require(
        is_iso_datetime_with_timezone(manifest.get("generated_at_utc")),
        "input generated_at_utc must be an ISO-8601 datetime with timezone",
        errors,
    )
    inputs = manifest.get("inputs", [])
    require(isinstance(inputs, list), "input manifest `inputs` must be a list", errors)
    if not isinstance(inputs, list):
        return manifest
    require(manifest.get("input_count") == len(inputs), "input_count does not match inputs length", errors)

    seen_literals: dict[str, int] = {}
    seen_resolved: dict[Path, int] = {}
    for idx, record in enumerate(inputs):
        require(isinstance(record, dict), f"input {idx} must be an object", errors)
        if not isinstance(record, dict):
            continue
        missing = REQUIRED_INPUT_FIELDS - set(record)
        require(not missing, f"input {idx} missing fields: {sorted(missing)}", errors)

        path_value = record.get("path")
        if isinstance(path_value, str):
            normalized_literal = Path(path_value).as_posix()
            if normalized_literal in seen_literals:
                errors.append(
                    f"input {idx} duplicates manifest path from input {seen_literals[normalized_literal]}: {path_value}"
                )
            else:
                seen_literals[normalized_literal] = idx

        path = repo_relative_path(repo_root, path_value, f"input {idx} path", errors)
        if path is None:
            continue

        if path in seen_resolved:
            errors.append(
                f"input {idx} resolves to the same file as input {seen_resolved[path]}: {path_value}"
            )
        else:
            seen_resolved[path] = idx

        expected_filename = Path(path_value).name if isinstance(path_value, str) else None
        expected_extension = Path(path_value).suffix if isinstance(path_value, str) else None
        require(
            isinstance(record.get("filename"), str) and record.get("filename") == expected_filename,
            f"input {idx} filename does not match path: {path_value}",
            errors,
        )
        require(
            isinstance(record.get("extension"), str) and record.get("extension") == expected_extension,
            f"input {idx} extension does not match path: {path_value}",
            errors,
        )
        valid_size = isinstance(record.get("size_bytes"), int) and record.get("size_bytes") >= 0
        require(valid_size, f"input {idx} size_bytes must be a non-negative integer: {path_value}", errors)
        valid_sha = is_sha256_hex(record.get("sha256"))
        require(valid_sha, f"input {idx} sha256 must be a 64-character lowercase hex digest: {path_value}", errors)

        require(path.exists(), f"input path missing on disk: {path_value}", errors)
        if path.exists():
            require(path.is_file(), f"input path must be a file: {path_value}", errors)
            if path.is_file():
                if valid_size:
                    require(path.stat().st_size == record.get("size_bytes"), f"size mismatch: {path_value}", errors)
                if valid_sha:
                    require(sha256_file(path) == record.get("sha256"), f"sha256 mismatch: {path_value}", errors)

        provenance = record.get("provenance", {})
        require(isinstance(provenance, dict), f"input {idx} provenance must be an object", errors)
        if not isinstance(provenance, dict):
            continue
        provenance_missing = REQUIRED_PROVENANCE_FIELDS - set(provenance)
        require(not provenance_missing, f"input {idx} missing provenance fields: {sorted(provenance_missing)}", errors)
        if require_provenance:
            for field in sorted(REQUIRED_PROVENANCE_FIELDS):
                require(
                    has_claim_ready_value(provenance.get(field)),
                    f"input {idx} provenance field `{field}` is required for claim-ready validation",
                    errors,
                )
            access_date = provenance.get("access_date")
            require(
                is_iso_date(access_date),
                f"input {idx} provenance access_date must be ISO-8601 YYYY-MM-DD: {path_value}",
                errors,
            )
            url_or_doi = provenance.get("canonical_url_or_doi")
            require(
                is_valid_url_or_doi(url_or_doi),
                f"input {idx} provenance canonical_url_or_doi must be an http(s) URL or doi: URI: {path_value}",
                errors,
            )
            row_count = provenance.get("row_count")
            require(
                isinstance(row_count, int) and row_count >= 0,
                f"input {idx} provenance row_count must be a non-negative integer: {path_value}",
                errors,
            )
            require(
                record.get("validation_status") == PROVENANCE_COMPLETE_STATUS,
                f"input {idx} validation_status must be {PROVENANCE_COMPLETE_STATUS!r} when --require-provenance is set: {path_value}",
                errors,
            )
    return manifest


def expected_input_checksums(input_manifest: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if input_manifest is None:
        return None
    inputs = input_manifest.get("inputs")
    if not isinstance(inputs, list):
        return None
    expected = []
    for item in inputs:
        if not isinstance(item, dict):
            return None
        expected.append({"path": item.get("path"), "sha256": item.get("sha256"), "size_bytes": item.get("size_bytes")})
    return expected


def validate_config_checksum(repo_root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    config_path = repo_relative_path(repo_root, manifest.get("config_path"), "output config_path", errors)
    if config_path is None:
        return
    config_path_value = manifest.get("config_path")
    require(config_path.exists(), f"output config_path missing on disk: {config_path_value}", errors)
    if config_path.exists():
        require(
            manifest.get("config_sha256") == sha256_file(config_path),
            "output config_sha256 does not match config_path contents",
            errors,
        )


def validate_declared_outputs(repo_root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    """Validate optional output artifact records in an output manifest.

    Smoke manifests may legitimately have no produced artifacts yet. Once an
    output record is declared, however, its path must be repo-relative and any
    declared checksum/size facts must be canonical and match the file on disk.
    Duplicate aliases and directories are rejected so each record identifies
    exactly one produced file.
    """
    outputs = manifest.get("outputs", [])
    require(isinstance(outputs, list), "output outputs must be a list", errors)
    if not isinstance(outputs, list):
        return

    seen_literals: dict[str, int] = {}
    seen_resolved: dict[Path, int] = {}
    for idx, record in enumerate(outputs):
        require(isinstance(record, dict), f"output {idx} must be an object", errors)
        if not isinstance(record, dict):
            continue

        path_value = record.get("path")
        if isinstance(path_value, str):
            normalized_literal = Path(path_value).as_posix()
            if normalized_literal in seen_literals:
                errors.append(
                    f"output {idx} duplicates manifest path from output {seen_literals[normalized_literal]}: {path_value}"
                )
            else:
                seen_literals[normalized_literal] = idx

        output_path = repo_relative_path(repo_root, path_value, f"output {idx} path", errors)
        if output_path is None:
            continue

        if output_path in seen_resolved:
            errors.append(
                f"output {idx} resolves to the same file as output {seen_resolved[output_path]}: {path_value}"
            )
        else:
            seen_resolved[output_path] = idx

        if "size_bytes" in record:
            require(
                isinstance(record.get("size_bytes"), int) and record.get("size_bytes") >= 0,
                f"output size_bytes must be a non-negative integer: {path_value}",
                errors,
            )
        if "sha256" in record:
            require(
                is_sha256_hex(record.get("sha256")),
                f"output sha256 must be a 64-character lowercase hex digest: {path_value}",
                errors,
            )
        require(output_path.exists(), f"output path missing on disk: {path_value}", errors)
        if not output_path.exists():
            continue
        require(output_path.is_file(), f"output path must be a file: {path_value}", errors)
        if not output_path.is_file():
            continue
        if "size_bytes" in record:
            require(output_path.stat().st_size == record.get("size_bytes"), f"output size mismatch: {path_value}", errors)
        if "sha256" in record:
            require(sha256_file(output_path) == record.get("sha256"), f"output sha256 mismatch: {path_value}", errors)


def validate_input_manifest_reference(repo_root: Path, manifest: dict[str, Any], errors: list[str], input_manifest_path: Path | None = None) -> None:
    """Validate the output manifest's pointer back to the input manifest.

    An output manifest should not only copy input checksums; it should also name
    the repo-relative input manifest it came from. This catches stale manifests
    that were generated from one input manifest but validated against another.
    """
    recorded_path = repo_relative_path(repo_root, manifest.get("input_manifest_path"), "output input_manifest_path", errors)
    if recorded_path is None or input_manifest_path is None:
        return
    require(
        recorded_path == input_manifest_path.resolve(),
        "output input_manifest_path does not match validated input manifest path",
        errors,
    )


def validate_environment_record(manifest: dict[str, Any], errors: list[str], *, require_for_outputs: bool = False) -> None:
    outputs = manifest.get("outputs", [])
    if require_for_outputs and not outputs:
        return
    environment = manifest.get("environment")
    require(isinstance(environment, dict), "output manifest environment must be an object", errors)
    if not isinstance(environment, dict):
        return
    for key in ("python", "platform", "executable"):
        require(isinstance(environment.get(key), str) and environment.get(key).strip(), f"output environment.{key} must be a non-empty string", errors)


def validate_run_config_binding(repo_root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    """Ensure output manifest run_config matches the referenced config file."""
    outputs = manifest.get("outputs", [])
    if not isinstance(outputs, list) or not outputs:
        return

    run_config = manifest.get("run_config")
    require(isinstance(run_config, dict), "output manifest run_config must be an object when outputs are declared", errors)
    if not isinstance(run_config, dict):
        return

    config_path = repo_relative_path(repo_root, manifest.get("config_path"), "output config_path", errors)
    if config_path is None or not config_path.exists():
        return

    expected = load_smoke_config(config_path)
    if expected is None:
        errors.append("output config must be a YAML mapping to validate run_config binding")
        return

    for key in ("random_seed", "selected_materialization", "selected_inputs"):
        if key not in expected:
            continue
        require(
            run_config.get(key) == expected.get(key),
            f"output run_config.{key} does not match config file contents",
            errors,
        )

    require(
        isinstance(manifest.get("repo_commit"), str) and manifest.get("repo_commit").strip(),
        "output manifest repo_commit must be recorded when outputs are declared",
        errors,
    )


def validate_output_manifest(
    repo_root: Path,
    path: Path,
    errors: list[str],
    input_manifest: dict[str, Any] | None = None,
    input_manifest_path: Path | None = None,
    *,
    require_experiment_binding: bool = False,
) -> None:
    require(path.exists(), f"missing output manifest: {path}", errors)
    if not path.exists():
        return
    manifest = load_json(path, errors, "output manifest")
    if manifest is None:
        return
    missing = REQUIRED_OUTPUT_FIELDS - set(manifest)
    require(not missing, f"output manifest missing fields: {sorted(missing)}", errors)
    require(
        is_iso_datetime_with_timezone(manifest.get("created_at_utc")),
        "output created_at_utc must be an ISO-8601 datetime with timezone",
        errors,
    )
    require(manifest.get("claim_status") == "not_interpretable_as_neuroscience", "output manifest must preserve conservative claim status for smoke metadata", errors)
    require(isinstance(manifest.get("input_checksums", []), list), "output input_checksums must be a list", errors)
    validate_config_checksum(repo_root, manifest, errors)
    validate_declared_outputs(repo_root, manifest, errors)
    validate_input_manifest_reference(repo_root, manifest, errors, input_manifest_path=input_manifest_path)
    validate_environment_record(manifest, errors, require_for_outputs=True)
    validate_run_config_binding(repo_root, manifest, errors)
    validate_experiment_registry_binding(
        repo_root,
        manifest,
        errors,
        require_binding=require_experiment_binding,
    )

    expected_checksums = expected_input_checksums(input_manifest)
    if expected_checksums is not None:
        require(
            manifest.get("input_manifest_present") is True,
            "output manifest must record input_manifest_present=true when an input manifest was validated",
            errors,
        )
        require(
            manifest.get("input_count") == len(expected_checksums),
            "output input_count does not match validated input manifest",
            errors,
        )
        require(
            manifest.get("input_checksums") == expected_checksums,
            "output input_checksums do not match validated input manifest",
            errors,
        )


def read_experiment_registry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_primary_output_paths(primary_output: Any) -> list[str]:
    if not isinstance(primary_output, str) or not primary_output.strip():
        return []
    return [part.strip() for part in primary_output.split(";") if part.strip()]


def resolvable_primary_output_paths(primary_output: Any) -> list[str]:
    return [path for path in parse_primary_output_paths(primary_output) if "*" not in path]


def load_experiment_registry(repo_root: Path, registry_path: Path, errors: list[str]) -> dict[str, dict[str, str]]:
    require(registry_path.exists(), f"missing experiment registry: {registry_path}", errors)
    if not registry_path.exists():
        return {}
    rows = read_experiment_registry(registry_path)
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        experiment_id = (row.get("experiment_id") or "").strip()
        if not experiment_id:
            continue
        if experiment_id in by_id:
            errors.append(f"duplicate experiment_id in registry: {experiment_id}")
        by_id[experiment_id] = row
    return by_id


def validate_experiment_registry_binding(
    repo_root: Path,
    manifest: dict[str, Any],
    errors: list[str],
    *,
    require_binding: bool = False,
) -> None:
    """Ensure output manifest experiment_id matches the experiment registry and declared outputs."""
    outputs = manifest.get("outputs", [])
    if not isinstance(outputs, list) or not outputs:
        return

    experiment_id = manifest.get("experiment_id")
    if require_binding:
        require(
            isinstance(experiment_id, str) and experiment_id.strip(),
            "output manifest experiment_id must be recorded when outputs are declared and experiment binding is required",
            errors,
        )
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        return

    registry_literal = manifest.get("experiment_registry_path") or DEFAULT_EXPERIMENT_REGISTRY
    registry_path = repo_relative_path(
        repo_root,
        registry_literal,
        "output experiment_registry_path",
        errors,
    )
    if registry_path is None:
        return

    experiments = load_experiment_registry(repo_root, registry_path, errors)
    experiment = experiments.get(experiment_id)
    require(experiment is not None, f"output manifest experiment_id not found in registry: {experiment_id}", errors)
    if experiment is None:
        return

    declared_paths = {
        record.get("path")
        for record in outputs
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    }
    expected_paths = set(resolvable_primary_output_paths(experiment.get("primary_output")))
    if not expected_paths:
        return

    for path in sorted(declared_paths):
        require(
            path in expected_paths,
            f"output manifest declares artifact not listed in experiment {experiment_id} primary_output: {path}",
            errors,
        )
    for path in sorted(expected_paths):
        require(
            path in declared_paths,
            f"output manifest missing experiment {experiment_id} primary_output artifact: {path}",
            errors,
        )


def load_smoke_config(path: Path) -> dict[str, Any] | None:
    try:
        import yaml
    except ImportError:
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def validate_smoke_config(
    repo_root: Path,
    config_path: Path,
    errors: list[str],
    input_manifest: dict[str, Any] | None = None,
) -> None:
    """Validate smoke config materialization and selected input filenames.

    Ensures ``configs/smoke_run.yaml`` stays aligned with
    ``tools/path_resolver.MATERIALIZATION_FILENAMES`` and the committed input
    manifest. This is metadata plumbing only; it does not validate biology.
    """
    require(config_path.exists(), f"missing smoke config: {config_path}", errors)
    if not config_path.exists():
        return

    config = load_smoke_config(config_path)
    if config is None:
        require(False, "smoke config must be a YAML mapping; install PyYAML to validate", errors)
        return

    materialization = config.get("selected_materialization")
    selected_inputs = config.get("selected_inputs")
    require(
        isinstance(materialization, str) and materialization.strip(),
        "smoke config selected_materialization must be a non-empty string",
        errors,
    )
    require(isinstance(selected_inputs, dict), "smoke config selected_inputs must be a mapping", errors)
    if not isinstance(selected_inputs, dict):
        return

    from importlib.util import module_from_spec, spec_from_file_location

    resolver_path = Path(__file__).resolve().parent / "path_resolver.py"
    spec = spec_from_file_location("path_resolver", resolver_path)
    if spec is None or spec.loader is None:
        errors.append("could not load path_resolver for smoke config validation")
        return
    path_resolver = module_from_spec(spec)
    spec.loader.exec_module(path_resolver)
    ANNOTATIONS_INPUT = path_resolver.ANNOTATIONS_INPUT
    materialization_filenames = path_resolver.materialization_filenames

    try:
        expected_tables = materialization_filenames(materialization)
    except ValueError as exc:
        errors.append(str(exc))
        return

    expected_inputs = {
        "completeness": expected_tables["completeness"],
        "connectivity": expected_tables["connectivity"],
        "annotations": ANNOTATIONS_INPUT,
    }
    for key, expected_path in expected_inputs.items():
        actual = selected_inputs.get(key)
        require(
            actual == expected_path,
            f"smoke config selected_inputs[{key!r}] must be {expected_path!r}, got {actual!r}",
            errors,
        )

    if input_manifest is None:
        return
    manifest_paths = {
        record.get("path")
        for record in input_manifest.get("inputs", [])
        if isinstance(record, dict)
    }
    for path in expected_inputs.values():
        require(path in manifest_paths, f"smoke config input missing from input manifest: {path}", errors)

    experiment_id = config.get("experiment_id")
    if isinstance(experiment_id, str) and experiment_id.strip():
        registry_literal = config.get("experiment_registry_path") or DEFAULT_EXPERIMENT_REGISTRY
        registry_path = repo_relative_path(repo_root, registry_literal, "smoke config experiment_registry_path", errors)
        if registry_path is not None:
            experiments = load_experiment_registry(repo_root, registry_path, errors)
            require(
                experiment_id in experiments,
                f"smoke config experiment_id not found in registry: {experiment_id}",
                errors,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input-manifest", default="data/input_manifest.json")
    parser.add_argument("--output-manifest", default="output_manifest.json")
    parser.add_argument(
        "--require-provenance",
        action="store_true",
        help="Fail unless every input has non-empty source, release, citation, license/terms, schema, row-count, and preprocessing provenance.",
    )
    parser.add_argument(
        "--skip-output-manifest",
        action="store_true",
        help="Validate only the input manifest; do not require an output manifest.",
    )
    parser.add_argument(
        "--smoke-config",
        default="configs/smoke_run.yaml",
        help="Validate smoke config materialization and selected_inputs against the resolver and input manifest.",
    )
    parser.add_argument(
        "--require-experiment-binding",
        action="store_true",
        help="Require output manifests with declared artifacts to record experiment_id and match the experiment registry.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    input_manifest_path = repo_relative_path(repo_root, args.input_manifest, "--input-manifest", errors)
    output_manifest_path = repo_relative_path(repo_root, args.output_manifest, "--output-manifest", errors)
    smoke_config_path = repo_relative_path(repo_root, args.smoke_config, "--smoke-config", errors)

    input_manifest = None
    if input_manifest_path is not None:
        input_manifest = validate_input_manifest(repo_root, input_manifest_path, errors, require_provenance=args.require_provenance)
    if smoke_config_path is not None:
        validate_smoke_config(repo_root, smoke_config_path, errors, input_manifest=input_manifest)
    if output_manifest_path is not None and not args.skip_output_manifest:
        validate_output_manifest(
            repo_root,
            output_manifest_path,
            errors,
            input_manifest=input_manifest,
            input_manifest_path=input_manifest_path,
            require_experiment_binding=args.require_experiment_binding,
        )

    if errors:
        print("Reproducibility validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Reproducibility metadata validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
