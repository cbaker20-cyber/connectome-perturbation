#!/usr/bin/env python3
"""Write a metadata-first output manifest for smoke/reproduction runs."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "README.md").exists():
            return candidate
    return current


def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/smoke_run.yaml")
    parser.add_argument("--input-manifest", default="data/input_manifest.json")
    parser.add_argument("--output", default="output_manifest.json")
    parser.add_argument("--status", default="metadata_only_smoke")
    parser.add_argument("--note", action="append", default=[])
    args = parser.parse_args()

    repo_root = repo_root_from()
    input_manifest_path = repo_root / args.input_manifest
    input_manifest = read_json(input_manifest_path)
    output_path = repo_root / args.output

    manifest = {
        "schema_version": "0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "command": " ".join(sys.argv),
        "repo_commit": git_commit(repo_root),
        "config_path": args.config,
        "input_manifest_path": args.input_manifest,
        "input_manifest_present": input_manifest is not None,
        "input_count": None if input_manifest is None else input_manifest.get("input_count"),
        "input_checksums": [] if input_manifest is None else [
            {"path": item.get("path"), "sha256": item.get("sha256"), "size_bytes": item.get("size_bytes")}
            for item in input_manifest.get("inputs", [])
        ],
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "outputs": [],
        "notes": args.note or [
            "This manifest records metadata plumbing only unless paired with a real simulation log and validated outputs."
        ],
        "claim_status": "not_interpretable_as_neuroscience",
    }

    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
