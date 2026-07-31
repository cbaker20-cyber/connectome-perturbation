#!/usr/bin/env python3
"""Validate basic reproducibility artifacts.

This script intentionally checks metadata plumbing, not neuroscience results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

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


# Text inputs are hashed after CRLF→LF normalization so Windows checkouts match
# manifests produced on LF-only systems (git autocrlf).
_TEXT_HASH_SUFFIXES = frozenset({".csv", ".tsv", ".txt", ".json", ".yaml", ".yml", ".md"})


def canonical_file_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() in _TEXT_HASH_SUFFIXES:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return data


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    data = canonical_file_bytes(path)
    digest = hashlib.sha256()
    view = memoryview(data)
    for start in range(0, len(data), chunk_size):
        digest.update(view[start : start + chunk_size])
    return digest.hexdigest()


def canonical_file_size(path: Path) -> int:
    return len(canonical_file_bytes(path))


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
                    declared_size = record.get("size_bytes")
                    require(
                        declared_size
                        in (path.stat().st_size, canonical_file_size(path)),
                        f"size mismatch: {path_value}",
                        errors,
                    )
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


def validate_output_manifest(
    repo_root: Path,
    path: Path,
    errors: list[str],
    input_manifest: dict[str, Any] | None = None,
    input_manifest_path: Path | None = None,
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
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    input_manifest_path = repo_relative_path(repo_root, args.input_manifest, "--input-manifest", errors)
    output_manifest_path = repo_relative_path(repo_root, args.output_manifest, "--output-manifest", errors)

    input_manifest = None
    if input_manifest_path is not None:
        input_manifest = validate_input_manifest(repo_root, input_manifest_path, errors, require_provenance=args.require_provenance)
    if output_manifest_path is not None and not args.skip_output_manifest:
        validate_output_manifest(
            repo_root,
            output_manifest_path,
            errors,
            input_manifest=input_manifest,
            input_manifest_path=input_manifest_path,
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
