#!/usr/bin/env python3
"""Detect unsafe parsing of large FlyWire/root IDs.

FlyWire root IDs can be 18 digits long. Parsing them through float can silently
change the final digits before integer conversion. That is not a cosmetic bug; it
can change which neurons a context actually stimulates or lesions.

This checker is intentionally small and dependency-free so it can run in GitHub
Actions before any expensive simulation work starts.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
    "results",
}
SCAN_SUFFIXES = {".py", ".ps1", ".md", ".yml", ".yaml"}

# Directly dangerous patterns. Keep these specific to avoid blocking ordinary
# numeric work that is not operating on IDs.
BANNED_PATTERNS = [
    (re.compile(r"int\s*\(\s*float\s*\("), "int(float(...)) can corrupt 18-digit IDs"),
    (
        re.compile(r"astype\s*\(\s*['\"]?float[^)]*\)\s*\.\s*astype\s*\(\s*['\"]?int", re.IGNORECASE),
        "astype(float).astype(int) can corrupt 18-digit IDs",
    ),
]

ID_CONTEXT_RE = re.compile(r"(flywire|root_id|source_id|source_ids|neuron_id|neuron_ids|id_file|parse_id)", re.IGNORECASE)
SOFT_FLOAT_RE = re.compile(r"(float\s*\(|astype\s*\(\s*['\"]?float)", re.IGNORECASE)


def changed_files(base_ref: str | None) -> list[Path]:
    if not base_ref:
        return []
    try:
        subprocess.run(["git", "fetch", "origin", base_ref, "--depth=1"], cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception:
        return []
    return [ROOT / line.strip() for line in proc.stdout.splitlines() if line.strip()]


def iter_files(changed_only: bool, base_ref: str | None) -> list[Path]:
    if changed_only:
        files = changed_files(base_ref)
    else:
        files = [p for p in ROOT.rglob("*") if p.is_file()]

    kept: list[Path] = []
    for path in files:
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            continue
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() in SCAN_SUFFIXES:
            kept.append(path)
    return sorted(kept)


def scan_file(path: Path) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    soft: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return [f"{path.relative_to(ROOT)}: could not read file: {exc}"], []

    rel = path.relative_to(ROOT)
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        for pattern, message in BANNED_PATTERNS:
            if pattern.search(stripped):
                hard.append(f"{rel}:{line_no}: {message}: {stripped}")
        if ID_CONTEXT_RE.search(stripped) and SOFT_FLOAT_RE.search(stripped):
            soft.append(f"{rel}:{line_no}: review float use near ID context: {stripped}")
    return hard, soft


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for unsafe large-ID parsing patterns.")
    parser.add_argument("--changed-only", action="store_true", help="Only scan files changed against the base ref.")
    parser.add_argument("--base-ref", default=None, help="Base branch/ref for --changed-only. Defaults to GITHUB_BASE_REF.")
    parser.add_argument("--warnings-are-errors", action="store_true", help="Fail on soft float-in-ID-context warnings too.")
    args = parser.parse_args()

    base_ref = args.base_ref or (None if not args.changed_only else __import__("os").environ.get("GITHUB_BASE_REF"))
    hard_findings: list[str] = []
    soft_findings: list[str] = []

    for path in iter_files(args.changed_only, base_ref):
        hard, soft = scan_file(path)
        hard_findings.extend(hard)
        soft_findings.extend(soft)

    if soft_findings:
        print("Large-ID parsing warnings:")
        for item in soft_findings:
            print(f" - {item}")

    if hard_findings:
        print("Unsafe large-ID parsing patterns found:")
        for item in hard_findings:
            print(f" - {item}")
        raise SystemExit(1)

    if args.warnings_are_errors and soft_findings:
        raise SystemExit(1)

    print("Large-ID parsing safety check passed.")


if __name__ == "__main__":
    main()
