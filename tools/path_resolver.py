#!/usr/bin/env python3
"""Resolve repository paths without hard-coded data directories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "README.md").exists():
            return candidate
    return current


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_repo_path(root: Path, candidate: Path, label: str) -> Path:
    """Return a resolved path only when it stays inside ``root``."""
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"{label} must stay within the repository: {candidate}"
        ) from exc
    return resolved_candidate


def resolve_input(identifier: str, manifest_path: str | Path = "data/input_manifest.json", repo_root: Path | None = None) -> Path:
    """Resolve an input by exact path, filename, role, or materialization.

    The resolver refuses ambiguous matches and paths outside the repository so
    scripts cannot silently pick the wrong materialization or external file.
    """
    root = repo_root_from(repo_root)
    manifest_file = require_repo_path(root, root / manifest_path, "manifest path")
    manifest = load_manifest(manifest_file)
    matches = []
    for record in manifest.get("inputs", []):
        values = {
            record.get("path"),
            record.get("filename"),
            record.get("guessed_role"),
            record.get("guessed_materialization"),
        }
        if identifier in values:
            matches.append(record)
    if not matches:
        candidate = require_repo_path(root, root / identifier, "input path")
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"No manifest entry or file found for {identifier!r}")
    if len(matches) > 1:
        choices = ", ".join(record["path"] for record in matches)
        raise ValueError(f"Ambiguous input identifier {identifier!r}; matches: {choices}")
    return require_repo_path(root, root / matches[0]["path"], "manifest input path")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identifier", help="Manifest path, filename, role, or materialization")
    parser.add_argument("--manifest", default="data/input_manifest.json")
    args = parser.parse_args()
    print(resolve_input(args.identifier, args.manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
