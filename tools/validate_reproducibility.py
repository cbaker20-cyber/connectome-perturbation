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

REQUIRED_INPUT_FIELDS = {"path", "filename", "extension", "size_bytes", "sha256", "guessed_role", "provenance"}
REQUIRED_OUTPUT_FIELDS = {
    "schema_version",
    "created_at_utc",
    "status",
    "command",
    "repo_commit",
    "config_path",
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


def load_json(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
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
    inputs = manifest.get("inputs", [])
    require(isinstance(inputs, list), "input manifest `inputs` must be a list", errors)
    require(manifest.get("input_count") == len(inputs), "input_count does not match inputs length", errors)
    for idx, record in enumerate(inputs):
        require(isinstance(record, dict), f"input {idx} must be an object", errors)
        if not isinstance(record, dict):
            continue
        missing = REQUIRED_INPUT_FIELDS - set(record)
        require(not missing, f"input {idx} missing fields: {sorted(missing)}", errors)
        path = repo_root / record.get("path", "")
        require(path.exists(), f"input path missing on disk: {record.get('path')}", errors)
        if path.exists():
            require(path.stat().st_size == record.get("size_bytes"), f"size mismatch: {record.get('path')}", errors)
            require(sha256_file(path) == record.get("sha256"), f"sha256 mismatch: {record.get('path')}", errors)
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


def validate_output_manifest(path: Path, errors: list[str], input_manifest: dict[str, Any] | None = None) -> None:
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
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    input_manifest = validate_input_manifest(repo_root, repo_root / args.input_manifest, errors, require_provenance=args.require_provenance)
    validate_output_manifest(repo_root / args.output_manifest, errors, input_manifest=input_manifest)

    if errors:
        print("Reproducibility validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Reproducibility metadata validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
