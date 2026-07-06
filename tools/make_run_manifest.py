#!/usr/bin/env python3
"""Create a reproducibility manifest before a connectome validation run.

The manifest is plain YAML-like text written without external dependencies. It
records the command, input file sizes/checksums, Git state, and planned run
configuration before simulation output is interpreted.
"""
from __future__ import annotations

import argparse
import hashlib
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "MISSING"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def size_bytes(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "MISSING"
    return str(path.stat().st_size)


def git_value(args: list[str]) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
        return proc.stdout.strip()
    except Exception:
        return "UNKNOWN"


def q(text: object) -> str:
    return '"' + str(text).replace('"', '\\"') + '"'


def file_block(label: str, path_text: str) -> list[str]:
    path = ROOT / path_text
    return [
        f"  {label}:",
        f"    path: {q(path_text)}",
        f"    exists: {str(path.exists()).lower()}",
        f"    byte_size: {q(size_bytes(path))}",
        f"    sha256: {q(sha256(path))}",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a run manifest for a connectome validation run.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--completeness", default="Drosophila_brain_model/2023_03_23_completeness_630_final.csv")
    parser.add_argument("--connectivity", default="Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet")
    parser.add_argument("--contexts", default="metadata/source_contexts/source_context_manifest.csv")
    parser.add_argument("--context-names", default="sugar,gustatory")
    parser.add_argument("--target-names", default="AN,brain_motor_neuron")
    parser.add_argument("--group-by", default="cell_class")
    parser.add_argument("--n-run", type=int, default=30)
    parser.add_argument("--t-run-ms", type=float, default=1000.0)
    parser.add_argument("--backend", default="numpy")
    args = parser.parse_args()

    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "run_manifest.yml"

    lines: list[str] = [
        "run_manifest_version: 1",
        f"created_utc: {q(datetime.now(timezone.utc).isoformat())}",
        "project: connectome-perturbation",
        "scientific_status: preliminary_until_reproduced",
        "repo:",
        f"  branch: {q(git_value(['rev-parse', '--abbrev-ref', 'HEAD']))}",
        f"  commit: {q(git_value(['rev-parse', 'HEAD']))}",
        f"  dirty_status: {q(git_value(['status', '--short']))}",
        "environment:",
        f"  platform: {q(platform.platform())}",
        f"  python: {q(platform.python_version())}",
        f"  backend: {q(args.backend)}",
        "configuration:",
        f"  command: {q(args.command)}",
        f"  context_names: {q(args.context_names)}",
        f"  target_names: {q(args.target_names)}",
        f"  group_by: {q(args.group_by)}",
        f"  n_run: {args.n_run}",
        f"  t_run_ms: {args.t_run_ms}",
        "inputs:",
    ]
    lines.extend(file_block("annotations", args.annotations))
    lines.extend(file_block("completeness", args.completeness))
    lines.extend(file_block("connectivity", args.connectivity))
    lines.extend(file_block("source_context_manifest", args.contexts))
    lines.extend([
        "outputs:",
        f"  output_dir: {q(args.output_dir)}",
        "  expected_summary: sweep_summary.csv",
        "  expected_run_info: sweep_run_info.csv",
        "interpretation_policy:",
        "  no_new_biological_claim_without_reproduction: true",
        "  compare_against_pilot_matrix: true",
        "  record_failed_or_null_results: true",
        "  preserve_context_specific_language: true",
    ])

    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {manifest}")


if __name__ == "__main__":
    main()
