#!/usr/bin/env python3
"""Write quantitative benchmark comparison reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from benchmark_comparison import (
    DEFAULT_BENCHMARK_REGISTRY,
    DEFAULT_EVALUATION_CONFIG,
    build_benchmark_comparison_report,
    validate_comparison_report,
)


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "README.md").exists():
            return candidate
    return current


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=DEFAULT_BENCHMARK_REGISTRY)
    parser.add_argument("--evaluation-config", default=DEFAULT_EVALUATION_CONFIG)
    parser.add_argument(
        "--output",
        default="benchmark_comparison_report.json",
        help="Repo-relative JSON report path.",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit non-zero when any benchmark metric comparison fails.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

    try:
        report = build_benchmark_comparison_report(
            repo_root,
            registry_path=(repo_root / args.registry).resolve(),
            evaluation_config_path=(repo_root / args.evaluation_config).resolve(),
        )
    except ValueError as exc:
        print(f"Benchmark comparison failed: {exc}", file=sys.stderr)
        return 1

    output_path = (repo_root / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    print(json.dumps(report["summary"], sort_keys=True))

    if args.fail_on_regression:
        errors = validate_comparison_report(report)
        if errors:
            print("Benchmark comparison validation failed:")
            for error in errors:
                print(f"- {error}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
