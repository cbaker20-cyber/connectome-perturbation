#!/usr/bin/env python3
"""Validate basic reproducibility artifacts.

This script intentionally checks metadata plumbing, not neuroscience results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

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


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_input_manifest(repo_root: Path, manifest_path: Path, errors: list[str]) -> None:
    require(manifest_path.exists(), f"missing input manifest: {manifest_path}", errors)
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inputs = manifest.get("inputs", [])
    require(isinstance(inputs, list), "input manifest `inputs` must be a list", errors)
    require(manifest.get("input_count") == len(inputs), "input_count does not match inputs length", errors)
    for idx, record in enumerate(inputs):
        missing = REQUIRED_INPUT_FIELDS - set(record)
        require(not missing, f"input {idx} missing fields: {sorted(missing)}", errors)
        path = repo_root / record.get("path", "")
        require(path.exists(), f"input path missing on disk: {record.get('path')}", errors)
        if path.exists():
            require(path.stat().st_size == record.get("size_bytes"), f"size mismatch: {record.get('path')}", errors)
            require(sha256_file(path) == record.get("sha256"), f"sha256 mismatch: {record.get('path')}", errors)
        provenance = record.get("provenance", {})
        require("canonical_url_or_doi" in provenance, f"input {idx} missing provenance canonical_url_or_doi", errors)
        require("license_or_terms" in provenance, f"input {idx} missing provenance license_or_terms", errors)


def validate_output_manifest(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing output manifest: {path}", errors)
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED_OUTPUT_FIELDS - set(manifest)
    require(not missing, f"output manifest missing fields: {sorted(missing)}", errors)
    require(manifest.get("claim_status") == "not_interpretable_as_neuroscience", "output manifest must preserve conservative claim status for smoke metadata", errors)
    require(isinstance(manifest.get("input_checksums", []), list), "output input_checksums must be a list", errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--input-manifest", default="data/input_manifest.json")
    parser.add_argument("--output-manifest", default="output_manifest.json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    validate_input_manifest(repo_root, repo_root / args.input_manifest, errors)
    validate_output_manifest(repo_root / args.output_manifest, errors)

    if errors:
        print("Reproducibility validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Reproducibility metadata validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
