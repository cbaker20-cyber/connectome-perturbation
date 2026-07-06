#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ipynb_checkpoints', 'results'}
SCAN_SUFFIXES = {'.py', '.ps1'}

BAD_DIRECT = re.compile('int' + r'\s*\(\s*' + 'float' + r'\s*\(')
BAD_CAST = re.compile('astype' + r'\s*\(\s*[\'\"]?float[^)]*\)\s*\.\s*astype\s*\(\s*[\'\"]?int', re.IGNORECASE)


def changed_files(base_ref: str | None) -> list[Path]:
    if not base_ref:
        return []
    try:
        subprocess.run(['git', 'fetch', 'origin', base_ref, '--depth=1'], cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc = subprocess.run(['git', 'diff', '--name-only', f'origin/{base_ref}...HEAD'], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        return []
    return [ROOT / line.strip() for line in proc.stdout.splitlines() if line.strip()]


def iter_files(changed_only: bool, base_ref: str | None) -> list[Path]:
    files = changed_files(base_ref) if changed_only else [p for p in ROOT.rglob('*') if p.is_file()]
    out: list[Path] = []
    for path in files:
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            continue
        if any(part in IGNORE for part in rel.parts):
            continue
        if path.suffix.lower() in SCAN_SUFFIXES:
            out.append(path)
    return sorted(out)


def scan(path: Path) -> list[str]:
    rel = path.relative_to(ROOT)
    findings: list[str] = []
    try:
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    except Exception as exc:
        return [f'{rel}: could not read file: {exc}']
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if BAD_DIRECT.search(stripped) or BAD_CAST.search(stripped):
            findings.append(f'{rel}:{line_no}: unsafe large-ID parser pattern: {stripped}')
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--changed-only', action='store_true')
    parser.add_argument('--base-ref', default=None)
    args = parser.parse_args()
    base_ref = args.base_ref or (os.environ.get('GITHUB_BASE_REF') if args.changed_only else None)
    findings: list[str] = []
    for path in iter_files(args.changed_only, base_ref):
        findings.extend(scan(path))
    if findings:
        print('Unsafe large-ID parsing patterns found:')
        for item in findings:
            print(f' - {item}')
        raise SystemExit(1)
    print('Large-ID parsing safety check passed.')


if __name__ == '__main__':
    main()
