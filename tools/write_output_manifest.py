#!/usr/bin/env python3
"""Write a metadata-first output manifest for smoke/reproduction runs."""

from __future__ import annotations

import argparse
import hashlib
import json
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


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        return None
    return value


def input_manifest_checksums(input_manifest: dict | None) -> list[dict]:
    """Return conservative input checksum records from a manifest-like object.

    The writer should not crash on partially edited or stale manifests. Full
    schema errors are the validator's job; this function only copies checksum
    facts when the shape is safe enough to inspect.
    """
    if input_manifest is None:
        return []
    inputs = input_manifest.get("inputs")
    if not isinstance(inputs, list):
        return []

    checksums = []
    for item in inputs:
        if not isinstance(item, dict):
            continue
        checksums.append({"path": item.get("path"), "sha256": item.get("sha256"), "size_bytes": item.get("size_bytes")})
    return checksums


def input_manifest_count(input_manifest: dict | None) -> int | None:
    if input_manifest is None:
        return None
    count = input_manifest.get("input_count")
    return count if isinstance(count, int) else None


def load_run_config_snapshot(config_path: Path) -> dict:
    """Return reproducibility metadata copied from a YAML run config."""
    try:
        import yaml
    except ImportError:
        return {}
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}
    snapshot: dict = {}
    if "random_seed" in loaded:
        snapshot["random_seed"] = loaded["random_seed"]
    if "selected_materialization" in loaded:
        snapshot["selected_materialization"] = loaded["selected_materialization"]
    if isinstance(loaded.get("selected_inputs"), dict):
        snapshot["selected_inputs"] = loaded["selected_inputs"]
    return snapshot


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str | None:
    """Return a file checksum, or None when an optional metadata file is absent."""
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def output_artifact_records(repo_root: Path, artifact_paths: list[str]) -> list[dict]:
    """Return manifest records for declared output artifacts.

    A writer-created output declaration should be stronger than a hand-authored
    placeholder: every declared artifact must already exist, be a regular file,
    stay inside the repository, and get fresh checksum/size metadata from disk.
    """
    records = []
    for artifact_path in artifact_paths:
        resolved = repo_relative_path(repo_root, artifact_path, "--artifact")
        if not resolved.exists():
            raise ValueError(f"--artifact must exist before it can be recorded: {artifact_path}")
        if not resolved.is_file():
            raise ValueError(f"--artifact must be a regular file: {artifact_path}")
        records.append(
            {
                "path": artifact_path,
                "sha256": sha256_file(resolved),
                "size_bytes": resolved.stat().st_size,
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/smoke_run.yaml")
    parser.add_argument("--input-manifest", default="data/input_manifest.json")
    parser.add_argument("--output", default="output_manifest.json")
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Repo-relative output artifact to record with sha256 and size metadata. May be supplied more than once.",
    )
    parser.add_argument("--status", default="metadata_only_smoke")
    parser.add_argument("--note", action="append", default=[])
    args = parser.parse_args()

    repo_root = repo_root_from()
    try:
        config_path = repo_relative_path(repo_root, args.config, "--config")
        input_manifest_path = repo_relative_path(repo_root, args.input_manifest, "--input-manifest")
        output_path = repo_relative_path(repo_root, args.output, "--output")
        outputs = output_artifact_records(repo_root, args.artifact)
    except ValueError as exc:
        print(f"Output manifest write failed: {exc}", file=sys.stderr)
        return 1

    input_manifest = read_json(input_manifest_path)
    run_config = load_run_config_snapshot(config_path)

    manifest = {
        "schema_version": "0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "command": " ".join(sys.argv),
        "repo_commit": git_commit(repo_root),
        "config_path": args.config,
        "config_sha256": sha256_file(config_path),
        "input_manifest_path": args.input_manifest,
        "input_manifest_present": input_manifest is not None,
        "input_count": input_manifest_count(input_manifest),
        "input_checksums": input_manifest_checksums(input_manifest),
        "run_config": run_config,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "outputs": outputs,
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
