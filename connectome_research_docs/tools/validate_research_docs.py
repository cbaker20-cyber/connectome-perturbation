#!/usr/bin/env python3
"""Delegate to the repository-level research documentation validator."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    docs_root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        str(repo_root / "tools/validate_research_docs.py"),
        "--repo-root",
        str(repo_root),
        "--research-docs-root",
        str(docs_root),
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
