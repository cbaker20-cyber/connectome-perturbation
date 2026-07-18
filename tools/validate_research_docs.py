#!/usr/bin/env python3
"""Validate the living research documentation system against the canonical pack."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "README.md",
    "00_PROJECT_STATE.md",
    "01_LIVING_RESEARCH_LOG.md",
    "02_METHODS_MASTER.md",
    "03_EXPERIMENT_REGISTRY.csv",
    "04_RESULTS_LEDGER.csv",
    "05_CODE_CHANGELOG.md",
    "06_DECISION_LOG.md",
    "07_ISSUES_AND_CAVEATS.md",
    "08_DATA_PROVENANCE.md",
    "09_REPRODUCIBILITY_CHECKLIST.md",
    "10_PUBLICATION_NARRATIVE_TRACKER.md",
    "11_CLAIMS_REGISTER.csv",
    "12_LITERATURE_AND_SOURCE_NOTES.md",
    "docs_config.yaml",
]

SKIP_EVIDENCE_PATTERNS = (
    re.compile(r"\*"),
    re.compile(r"^Pasted text\.txt$", re.I),
    re.compile(r"perturb_descending output", re.I),
    re.compile(r"hq_.*output", re.I),
    re.compile(r"^notebook/", re.I),
)

SCRIPT_SEARCH_DIRS = ("perturbation", "connectome_analysis", "")


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "README.md").exists():
            return candidate
    return current


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_docs_config(docs_root: Path) -> dict[str, Any]:
    path = docs_root / "docs_config.yaml"
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def status_uses_allowed_label(status: str, allowed: list[str]) -> bool:
    if not status.strip():
        return False
    normalized = status.strip().lower()
    for label in allowed:
        token = label.strip().lower()
        if not token:
            continue
        if normalized == token:
            return True
        if normalized.startswith(f"{token}/") or normalized.startswith(f"{token} ") or normalized.startswith(f"{token}-"):
            return True
        if f"/{token}" in normalized or f" {token}" in normalized:
            return True
    return False


def should_skip_evidence_token(token: str) -> bool:
    cleaned = token.strip()
    if not cleaned:
        return True
    return any(pattern.search(cleaned) for pattern in SKIP_EVIDENCE_PATTERNS)


def resolve_repo_path(repo_root: Path, relative_path: str) -> Path | None:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        return None
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def resolve_script_path(repo_root: Path, script_name: str) -> Path | None:
    for directory in SCRIPT_SEARCH_DIRS:
        candidate = repo_root / directory / script_name if directory else repo_root / script_name
        if candidate.is_file():
            return candidate
    return None


def resolve_evidence_path(repo_root: Path, token: str) -> Path | None:
    cleaned = token.strip()
    if should_skip_evidence_token(cleaned):
        return None
    if cleaned.endswith(".py"):
        return resolve_script_path(repo_root, cleaned)
    if cleaned.startswith("results/"):
        return resolve_repo_path(repo_root, cleaned)
    resolved = resolve_repo_path(repo_root, cleaned)
    if resolved is not None and resolved.is_file():
        return resolved
    return None


def parse_claim_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[;,]", value) if part.strip()]


def validate_required_files(docs_root: Path, errors: list[str]) -> None:
    for name in REQUIRED_FILES:
        if not (docs_root / name).exists():
            errors.append(f"missing required research document: {name}")


def validate_experiments(
    docs_root: Path,
    experiments: list[dict[str, str]],
    claim_ids: set[str],
    allowed_statuses: list[str],
    errors: list[str],
) -> dict[str, dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for row in experiments:
        experiment_id = (row.get("experiment_id") or "").strip()
        status = (row.get("status") or "").strip()
        if not experiment_id or not status:
            errors.append(f"experiment row missing id/status: {row}")
            continue
        if experiment_id in by_id:
            errors.append(f"duplicate experiment_id: {experiment_id}")
        by_id[experiment_id] = row
        if allowed_statuses and not status_uses_allowed_label(status, allowed_statuses):
            errors.append(f"experiment {experiment_id} uses unrecognized status label: {status}")
        if status == "validated" and not (row.get("primary_output") or "").strip():
            errors.append(f"validated experiment lacks primary output: {experiment_id}")
        for claim_id in parse_claim_ids(row.get("claim_ids")):
            if claim_id not in claim_ids:
                errors.append(f"experiment {experiment_id} references unknown claim_id: {claim_id}")
    return by_id


def validate_claims(
    claims: list[dict[str, str]],
    allowed_statuses: list[str],
    errors: list[str],
) -> dict[str, dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for row in claims:
        claim_id = (row.get("claim_id") or "").strip()
        claim = (row.get("claim") or "").strip()
        status = (row.get("status") or "").strip()
        if not claim_id or not claim:
            errors.append(f"claim row missing id/claim: {row}")
            continue
        if claim_id in by_id:
            errors.append(f"duplicate claim_id: {claim_id}")
        by_id[claim_id] = row
        if allowed_statuses and status and not status_uses_allowed_label(status, allowed_statuses):
            errors.append(f"claim {claim_id} uses unrecognized status label: {status}")
        if status.startswith("validated") and not (row.get("evidence_files") or "").strip():
            errors.append(f"validated claim lacks evidence files: {claim_id}")
    return by_id


def validate_results(
    results: list[dict[str, str]],
    experiment_ids: set[str],
    allowed_statuses: list[str],
    errors: list[str],
) -> None:
    seen_result_ids: set[str] = set()
    for row in results:
        result_id = (row.get("result_id") or "").strip()
        experiment_id = (row.get("experiment_id") or "").strip()
        status = (row.get("status") or "").strip()
        if not result_id:
            errors.append(f"result row missing result_id: {row}")
            continue
        if result_id in seen_result_ids:
            errors.append(f"duplicate result_id: {result_id}")
        seen_result_ids.add(result_id)
        if experiment_id not in experiment_ids:
            errors.append(
                f"result {result_id} references unknown experiment {experiment_id or '<missing>'}"
            )
        if allowed_statuses and status and not status_uses_allowed_label(status, allowed_statuses):
            errors.append(f"result {result_id} uses unrecognized status label: {status}")


def validate_evidence_files(repo_root: Path, claims: list[dict[str, str]], errors: list[str]) -> None:
    for row in claims:
        claim_id = (row.get("claim_id") or "").strip()
        evidence = row.get("evidence_files") or ""
        for token in re.split(r"[;]", evidence):
            cleaned = token.strip()
            if should_skip_evidence_token(cleaned):
                continue
            resolved = resolve_evidence_path(repo_root, cleaned)
            if resolved is None:
                errors.append(f"claim {claim_id} evidence file not found on disk: {cleaned}")
            elif not resolved.is_file():
                errors.append(f"claim {claim_id} evidence path is not a file: {cleaned}")


def validate_primary_outputs(repo_root: Path, experiments: list[dict[str, str]], errors: list[str]) -> None:
    for row in experiments:
        experiment_id = (row.get("experiment_id") or "").strip()
        status = (row.get("status") or "").strip()
        primary_output = (row.get("primary_output") or "").strip()
        if "validated" not in status or not primary_output or "*" in primary_output:
            continue
        for token in re.split(r"[;]", primary_output):
            cleaned = token.strip()
            if not cleaned or "*" in cleaned:
                continue
            resolved = resolve_repo_path(repo_root, cleaned)
            if resolved is None or not resolved.is_file():
                errors.append(
                    f"experiment {experiment_id} validated primary_output missing on disk: {cleaned}"
                )


def validate_research_docs(
    repo_root: Path,
    docs_root: Path | None = None,
    *,
    check_evidence_files: bool = True,
    check_validated_outputs: bool = True,
) -> list[str]:
    """Return validation errors for the canonical research documentation pack."""
    docs_root = (docs_root or repo_root).resolve()
    errors: list[str] = []
    config = load_docs_config(docs_root)
    allowed_statuses = list(config.get("status_labels") or [])
    for extra in (
        "completed",
        "implemented",
        "documented",
        "active",
        "not significant",
        "candidate",
        "partially",
    ):
        if extra not in allowed_statuses:
            allowed_statuses.append(extra)

    validate_required_files(docs_root, errors)

    exp_path = docs_root / "03_EXPERIMENT_REGISTRY.csv"
    claim_path = docs_root / "11_CLAIMS_REGISTER.csv"
    result_path = docs_root / "04_RESULTS_LEDGER.csv"

    claims = read_csv(claim_path) if claim_path.exists() else []
    claim_by_id = validate_claims(claims, allowed_statuses, errors)

    experiments = read_csv(exp_path) if exp_path.exists() else []
    experiment_by_id = validate_experiments(
        docs_root,
        experiments,
        set(claim_by_id),
        allowed_statuses,
        errors,
    )

    if result_path.exists():
        validate_results(read_csv(result_path), set(experiment_by_id), allowed_statuses, errors)

    if check_evidence_files:
        validate_evidence_files(repo_root, claims, errors)
    if check_validated_outputs:
        validate_primary_outputs(repo_root, experiments, errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve scripts and tracked outputs.",
    )
    parser.add_argument(
        "--research-docs-root",
        default=None,
        help="Directory containing the canonical research documentation pack (defaults to repo root).",
    )
    parser.add_argument(
        "--skip-evidence-files",
        action="store_true",
        help="Do not require claim evidence files to exist on disk.",
    )
    parser.add_argument(
        "--skip-validated-outputs",
        action="store_true",
        help="Do not require validated experiment primary_output files to exist on disk.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    docs_root = Path(args.research_docs_root).resolve() if args.research_docs_root else repo_root
    errors = validate_research_docs(
        repo_root,
        docs_root,
        check_evidence_files=not args.skip_evidence_files,
        check_validated_outputs=not args.skip_validated_outputs,
    )
    if errors:
        print("Research documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Research documentation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
