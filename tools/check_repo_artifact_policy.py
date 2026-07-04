#!/usr/bin/env python3
"""Repository policy gate for generated artifacts, caches, and unapproved data.

This does not prove the science. It prevents the easiest reproducibility mistake:
letting generated outputs, virtual environments, private files, or new large data
slip into Git before anyone has written down provenance and permissions.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWLIST = {
    "Connectivity_783.parquet",
    "2023_03_23_connectivity_630_final.parquet",
    "flywire_annotations.tsv",
    "Completeness_783.csv",
    "2023_03_23_completeness_630_final.csv",
    "results/perturbation_summary.csv",
}

BANNED_DIR_PARTS = {
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
    "Drosophila_brain_model",
}

BANNED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".envrc",
    "secrets.json",
    "credentials.json",
    "token.json",
}

BANNED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".dll",
    ".so",
    ".dylib",
    ".exe",
    ".pkl",
    ".pickle",
    ".npy",
    ".npz",
    ".h5",
    ".hdf5",
    ".feather",
    ".parquet",
}

SECRET_TEXT_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

TEXT_SUFFIXES = {".py", ".ps1", ".md", ".txt", ".csv", ".yml", ".yaml", ".json", ".toml", ".ini", ".sh"}


def relpath(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def should_skip(path: Path) -> bool:
    rel = relpath(path)
    return rel.startswith(".git/")


def scan_secret_text(path: Path) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    findings: list[str] = []
    for pattern in SECRET_TEXT_PATTERNS:
        if pattern.search(text):
            findings.append(f"{relpath(path)}: possible secret/token pattern")
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Check repository artifact/data hygiene.")
    parser.add_argument("--max-bytes", type=int, default=10_000_000, help="Fail on unapproved files larger than this many bytes.")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        rel = relpath(path)
        parts = set(path.relative_to(ROOT).parts)
        suffix = path.suffix.lower()
        name = path.name
        size = path.stat().st_size

        if rel in ALLOWLIST:
            if size > args.max_bytes or suffix in BANNED_SUFFIXES or rel.startswith("results/"):
                warnings.append(f"allowlisted legacy artifact retained: {rel} ({size:,} bytes)")
            continue

        if parts & BANNED_DIR_PARTS:
            errors.append(f"banned generated/local directory content: {rel}")
        if rel.startswith("results/"):
            errors.append(f"generated result file is not approved for Git: {rel}")
        if name in BANNED_FILE_NAMES:
            errors.append(f"possible secret/config file should not be committed: {rel}")
        if suffix in BANNED_SUFFIXES:
            errors.append(f"unapproved binary/data artifact: {rel}")
        if size > args.max_bytes:
            errors.append(f"unapproved large file over {args.max_bytes:,} bytes: {rel} ({size:,} bytes)")
        errors.extend(scan_secret_text(path))

    if warnings:
        print("Repository policy warnings:")
        for item in warnings:
            print(f" - {item}")

    if errors:
        print("Repository policy errors:")
        for item in errors:
            print(f" - {item}")
        raise SystemExit(1)

    print("Repository artifact policy check passed.")


if __name__ == "__main__":
    main()
