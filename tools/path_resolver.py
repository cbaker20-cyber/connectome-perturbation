#!/usr/bin/env python3
"""Resolve repository paths without hard-coded data directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEGACY_DATA_DIR = "Drosophila_brain_model"
DEFAULT_MANIFEST_PATH = "data/input_manifest.json"
SMOKE_MATERIALIZATION = "630"
ANNOTATIONS_INPUT = "flywire_annotations.tsv"
MATERIALIZATION_FILENAMES: dict[str, dict[str, str]] = {
    "630": {
        "completeness": "2023_03_23_completeness_630_final.csv",
        "connectivity": "2023_03_23_connectivity_630_final.parquet",
    },
    "783": {
        "completeness": "Completeness_783.csv",
        "connectivity": "Connectivity_783.parquet",
    },
}


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "README.md").exists():
            return candidate
    return current


def ensure_repo_on_path(start: Path | None = None) -> Path:
    """Insert the repository root on ``sys.path`` for legacy script imports."""
    root = repo_root_from(start)
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


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


def normalize_input_identifier(identifier: str) -> str:
    """Strip a legacy ``Drosophila_brain_model/`` prefix for manifest lookup."""
    prefix = f"{LEGACY_DATA_DIR}/"
    if identifier.startswith(prefix):
        return identifier[len(prefix) :]
    return identifier


def _manifest_matches(identifier: str, record: dict) -> bool:
    values = {
        record.get("path"),
        record.get("filename"),
        record.get("guessed_role"),
        record.get("guessed_materialization"),
    }
    return identifier in values


def _resolve_from_manifest(
    root: Path,
    identifier: str,
    manifest_path: str | Path,
) -> Path:
    manifest_file = require_repo_path(root, root / manifest_path, "manifest path")
    manifest = load_manifest(manifest_file)
    matches = []
    for record in manifest.get("inputs", []):
        if _manifest_matches(identifier, record):
            matches.append(record)
    if not matches:
        raise FileNotFoundError(f"No manifest entry found for {identifier!r}")
    if len(matches) > 1:
        choices = ", ".join(record["path"] for record in matches)
        raise ValueError(f"Ambiguous input identifier {identifier!r}; matches: {choices}")
    return require_repo_path(root, root / matches[0]["path"], "manifest input path")


def _legacy_fallback_candidates(root: Path, identifier: str) -> list[Path]:
    normalized = normalize_input_identifier(identifier)
    basename = Path(normalized).name
    return [
        root / normalized,
        root / identifier,
        root / LEGACY_DATA_DIR / basename,
        root / LEGACY_DATA_DIR / normalized,
    ]


def resolve_input(
    identifier: str,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    repo_root: Path | None = None,
) -> Path:
    """Resolve an input by manifest entry, repo-relative path, or legacy layout.

    Lookup order:
    1. Exact manifest match for the identifier, its normalized form, or basename.
    2. Existing repo-relative file at the identifier or normalized path.
    3. Legacy ``Drosophila_brain_model/<basename>`` checkout layout.

    The resolver refuses ambiguous manifest matches and paths outside the
    repository so scripts cannot silently pick the wrong materialization.
    """
    root = repo_root_from(repo_root)
    normalized = normalize_input_identifier(identifier)
    basename = Path(normalized).name
    manifest_identifiers = []
    for candidate in (identifier, normalized, basename):
        if candidate not in manifest_identifiers:
            manifest_identifiers.append(candidate)

    manifest_file = root / manifest_path
    if manifest_file.exists():
        for manifest_identifier in manifest_identifiers:
            try:
                return _resolve_from_manifest(root, manifest_identifier, manifest_path)
            except FileNotFoundError:
                continue
            except ValueError:
                raise

    for candidate in _legacy_fallback_candidates(root, identifier):
        if candidate.exists():
            return require_repo_path(root, candidate, "input path")

    raise FileNotFoundError(
        f"No manifest entry or file found for {identifier!r} "
        f"(normalized: {normalized!r})"
    )


def resolve_existing_path(
    path: str | Path,
    description: str = "file",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    repo_root: Path | None = None,
) -> Path:
    """Backwards-compatible wrapper around :func:`resolve_input`."""
    try:
        return resolve_input(str(path), manifest_path=manifest_path, repo_root=repo_root)
    except (FileNotFoundError, ValueError) as exc:
        raise FileNotFoundError(f"Could not find {description}: {path}") from exc


def materialization_filenames(materialization: str) -> dict[str, str]:
    """Return the tracked completeness/connectivity filenames for a materialization."""
    try:
        filenames = MATERIALIZATION_FILENAMES[materialization]
    except KeyError as exc:
        known = ", ".join(sorted(MATERIALIZATION_FILENAMES))
        raise ValueError(
            f"Unknown materialization {materialization!r}; expected one of: {known}"
        ) from exc
    return dict(filenames)


def resolve_materialization_inputs(
    materialization: str = SMOKE_MATERIALIZATION,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    repo_root: Path | None = None,
    include_annotations: bool = True,
) -> dict[str, Path]:
    """Resolve the standard input bundle for one connectome materialization.

    Scripts should pass exact filenames or call this helper instead of querying
  by bare materialization ID through :func:`resolve_input`, because multiple
    manifest rows can share the same ``guessed_materialization`` value.
    """
    filenames = materialization_filenames(materialization)
    resolved = {
        "completeness": resolve_input(
            filenames["completeness"],
            manifest_path=manifest_path,
            repo_root=repo_root,
        ),
        "connectivity": resolve_input(
            filenames["connectivity"],
            manifest_path=manifest_path,
            repo_root=repo_root,
        ),
    }
    if include_annotations:
        resolved["annotations"] = resolve_input(
            ANNOTATIONS_INPUT,
            manifest_path=manifest_path,
            repo_root=repo_root,
        )
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identifier", help="Manifest path, filename, role, or materialization")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()
    print(resolve_input(args.identifier, args.manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
