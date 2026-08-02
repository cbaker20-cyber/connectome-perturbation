#!/usr/bin/env python3
"""Build a conservative manifest for tracked input-like files.

The script records facts available from the local checkout and leaves provenance
fields empty for human/source-backed completion. It does not certify that any
file is authoritative, licensed for redistribution, or scientifically valid.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATTERNS = (
    "*.parquet",
    "*.csv",
    "*.tsv",
    "metadata/*.txt",
    "metadata/*.csv",
    "metadata/*.tsv",
)

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "results",
}

# Project-maintained ledgers/registries are not connectome inputs.
EXCLUDED_FILENAMES = frozenset(
    {
        "03_EXPERIMENT_REGISTRY.csv",
        "04_RESULTS_LEDGER.csv",
        "11_CLAIMS_REGISTER.csv",
    }
)


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


def guess_materialization(path: Path) -> str | None:
    name = path.name.lower()
    if "630" in name:
        return "630"
    if "783" in name:
        return "783"
    return None


def guess_role(path: Path) -> str:
    name = path.name.lower()
    if "connectivity" in name:
        return "connectivity_table"
    if "completeness" in name:
        return "completeness_table"
    if "annotation" in name:
        return "annotation_table"
    if "motor" in name:
        return "curated_motor_targets"
    return "unknown_input_like_file"


def should_include(path: Path) -> bool:
    if path.name in EXCLUDED_FILENAMES:
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if not path.is_file():
        return False
    return True


def iter_input_like_files(repo_root: Path, patterns: tuple[str, ...]) -> list[Path]:
    files: set[Path] = set()
    for pattern in patterns:
        for path in repo_root.glob(pattern):
            if should_include(path):
                files.add(path)
    return sorted(files, key=lambda p: p.as_posix())


def build_record(path: Path, repo_root: Path) -> dict[str, Any]:
    rel = path.relative_to(repo_root).as_posix()
    payload = canonical_file_bytes(path)
    return {
        "path": rel,
        "filename": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": len(payload),
        "sha256": sha256_file(path),
        "guessed_role": guess_role(path),
        "guessed_materialization": guess_materialization(path),
        "provenance": {
            "dataset_name": None,
            "release_or_materialization": guess_materialization(path),
            "canonical_url_or_doi": None,
            "citation": None,
            "license_or_terms": None,
            "access_date": None,
            "redistribution_status": "unknown",
            "schema_notes": None,
            "row_count": None,
            "preprocessing_notes": None,
        },
        "validation_status": "checksum_recorded_provenance_missing",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--output", default="data/input_manifest.json", help="Manifest path to write")
    parser.add_argument("--pattern", action="append", help="Additional glob pattern to include")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    patterns = DEFAULT_PATTERNS + tuple(args.pattern or ())
    output = (repo_root / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    records = [build_record(path, repo_root) for path in iter_input_like_files(repo_root, patterns)]
    manifest = {
        "schema_version": "0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": ".",
        "purpose": "Record local input-like file facts; provenance fields require source-backed completion.",
        "input_count": len(records),
        "inputs": records,
    }

    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output} with {len(records)} input-like records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
