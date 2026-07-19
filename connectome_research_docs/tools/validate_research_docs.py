#!/usr/bin/env python3
"""Delegate to the canonical research documentation validator at the repository root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    command = [sys.executable, str(repo_root / "tools/validate_research_docs.py"), *sys.argv[1:]]
    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
