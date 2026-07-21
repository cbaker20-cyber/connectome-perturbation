#!/usr/bin/env python3
"""Write a deterministic metadata-only smoke artifact.

This artifact exists to test the reproducibility plumbing around produced files:
artifact creation, output-manifest declaration, checksum recording, and
validation. It is intentionally not a neuroscience result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "README.md").exists():
            return candidate
    return current


def repo_relative_path(repo_root: Path, path_value: str, label: str) -> Path:
    """Resolve a CLI path only if it is relative and stays inside repo_root."""
    if not isinstance(path_value, str) or not path_value.strip():
        raise ValueError(f"{label} must be a non-empty string")

    candidate = Path(path_value)
    if candidate.is_absolute():
        raise ValueError(f"{label} must be repo-relative, not absolute: {path_value}")

    resolved_root = repo_root.resolve()
    resolved_candidate = (resolved_root / candidate).resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay within the repository: {path_value}") from exc
    return resolved_candidate


def smoke_artifact_payload() -> dict:
    """Return stable metadata for a reproducibility smoke artifact."""
    return {
        "schema_version": "0.1",
        "artifact_type": "metadata_only_reproducibility_smoke",
        "claim_status": "not_interpretable_as_neuroscience",
        "purpose": "Exercise output artifact creation, declaration, checksum recording, and validation.",
        "expected_next_command": "python tools/write_output_manifest.py --config configs/smoke_run.yaml --output output_manifest.json --artifact results/reproducibility_smoke_artifact.json",
        "non_claims": [
            "This artifact is not a simulation result.",
            "This artifact is not evidence for a biological conclusion.",
            "This artifact contains no connectome-derived measurement.",
        ],
    }


def write_smoke_artifact(repo_root: Path, output_path: str) -> Path:
    resolved_output = repo_relative_path(repo_root, output_path, "--output")
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(json.dumps(smoke_artifact_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved_output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/reproducibility_smoke_artifact.json")
    args = parser.parse_args()

    repo_root = repo_root_from()
    try:
        output_path = write_smoke_artifact(repo_root, args.output)
    except ValueError as exc:
        print(f"Smoke artifact write failed: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
