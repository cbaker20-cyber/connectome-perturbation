#!/usr/bin/env python3
"""Write a standardized benchmark evaluation report."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output",
        default="benchmark_evaluation_report.json",
        help="Repo-relative JSON report path.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    command = [
        sys.executable,
        str(repo_root / "tools/validate_benchmarks.py"),
        "--repo-root",
        str(repo_root),
        "--report",
        args.output,
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
