#!/usr/bin/env python3
"""Validate the living research documentation system and minimum claim standards."""

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

NON_TRIAL_MARKERS = (
    "bootstrap",
    "na",
    "n/a",
    "not applicable",
    "not recorded",
)

INFRASTRUCTURE_MARKERS = (
    "metadata smoke",
    "metadata-only",
    "reproducibility_smoke",
    "ci reproducibility",
)


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


def load_optional_benchmark_registry(repo_root: Path) -> dict[str, dict[str, Any]]:
    path = repo_root / "data/benchmark_registry.yaml"
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}
    benchmarks = loaded.get("benchmarks")
    if not isinstance(benchmarks, dict):
        return {}
    parsed: dict[str, dict[str, Any]] = {}
    for benchmark_id, record in benchmarks.items():
        if isinstance(benchmark_id, str) and isinstance(record, dict):
            parsed[benchmark_id] = record
    return parsed


def status_contains_label(status: str, label: str) -> bool:
    normalized = status.strip().lower()
    token = label.strip().lower()
    if not normalized or not token:
        return False
    if normalized == token:
        return True
    if normalized.startswith(f"{token}/") or normalized.startswith(f"{token} ") or normalized.startswith(f"{token}-"):
        return True
    if f"/{token}" in normalized or f" {token}" in normalized:
        return True
    return False


def parse_trial_counts(value: str | None) -> list[int]:
    if not value:
        return []
    digits: list[int] = []
    current: list[str] = []
    for char in value:
        if char.isdigit():
            current.append(char)
        elif current:
            digits.append(int("".join(current)))
            current = []
    if current:
        digits.append(int("".join(current)))
    return digits


def classify_trial_mode(value: str | None) -> str:
    if not value or not value.strip():
        return "unknown"
    normalized = value.strip().lower()
    if any(marker in normalized for marker in NON_TRIAL_MARKERS):
        return "non_trial"
    if parse_trial_counts(value):
        return "numeric"
    return "unknown"


def infer_claim_tier(status: str, row: dict[str, str]) -> str:
    combined = " ".join(
        [
            status,
            row.get("short_name") or "",
            row.get("type") or "",
            row.get("notes") or "",
            row.get("primary_output") or "",
        ]
    ).lower()
    if any(marker in combined for marker in INFRASTRUCTURE_MARKERS):
        return "infrastructure"
    trial_mode = classify_trial_mode(row.get("n_trials"))
    if trial_mode == "non_trial":
        return "non_trial"
    if status_contains_label(status, "exploratory"):
        return "exploratory"
    if status_contains_label(status, "validated"):
        return "validated"
    if status_contains_label(status, "planned") or status_contains_label(status, "active"):
        return "non_trial"
    return "other"


def parse_claim_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[;,]", value) if part.strip()]


def text_mentions_exploratory_caveat(*values: str | None) -> bool:
    combined = " ".join(value for value in values if value).lower()
    markers = (
        "5 trial",
        "5-trial",
        "exploratory",
        "do not cite",
        "do not headline",
        "rerun",
        "revised",
    )
    return any(marker in combined for marker in markers)


def text_mentions_fdr(*values: str | None) -> bool:
    combined = " ".join(value for value in values if value).lower()
    return bool(re.search(r"\bfdr\b", combined)) or "q-value" in combined or "q value" in combined


def text_mentions_zero_spike_retention(*values: str | None) -> bool:
    combined = " ".join(value for value in values if value).lower()
    markers = (
        "zero-spike",
        "zero spike",
        "0 hz",
        "retain",
        "retention",
        "statistics.py",
        "c006",
    )
    return any(marker in combined for marker in markers)


def is_statistical_experiment(row: dict[str, str]) -> bool:
    combined = " ".join(
        [
            row.get("type") or "",
            row.get("script_or_file") or "",
            row.get("primary_output") or "",
            row.get("short_name") or "",
        ]
    ).lower()
    return "statistic" in combined or "statistics.py" in combined


def is_perturbation_experiment(row: dict[str, str]) -> bool:
    combined = " ".join(
        [
            row.get("type") or "",
            row.get("perturbation_target") or "",
            row.get("short_name") or "",
        ]
    ).lower()
    if "metadata" in combined or "graph" in combined or "pathway" in combined:
        return False
    return "perturbation" in combined or "sweep" in combined or "rerun" in combined


def claim_status_is_validated(status: str) -> bool:
    return status_contains_label(status, "validated")


def validate_required_files(docs_root: Path, errors: list[str]) -> None:
    for name in REQUIRED_FILES:
        if not (docs_root / name).exists():
            errors.append(f"missing required research document: {name}")


def validate_basic_registry_rows(
    experiments: list[dict[str, str]],
    claims: list[dict[str, str]],
    results: list[dict[str, str]],
    errors: list[str],
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    experiment_by_id: dict[str, dict[str, str]] = {}
    for row in experiments:
        experiment_id = (row.get("experiment_id") or "").strip()
        status = (row.get("status") or "").strip()
        if not experiment_id or not status:
            errors.append(f"experiment row missing id/status: {row}")
            continue
        if experiment_id in experiment_by_id:
            errors.append(f"duplicate experiment_id: {experiment_id}")
        experiment_by_id[experiment_id] = row
        if status == "validated" and not (row.get("primary_output") or "").strip():
            errors.append(f"validated experiment lacks primary output: {experiment_id}")

    claim_by_id: dict[str, dict[str, str]] = {}
    for row in claims:
        claim_id = (row.get("claim_id") or "").strip()
        claim = (row.get("claim") or "").strip()
        status = (row.get("status") or "").strip()
        if not claim_id or not claim:
            errors.append(f"claim row missing id/claim: {row}")
            continue
        if claim_id in claim_by_id:
            errors.append(f"duplicate claim_id: {claim_id}")
        claim_by_id[claim_id] = row
        if status.startswith("validated") and not (row.get("evidence_files") or "").strip():
            errors.append(f"validated claim lacks evidence files: {claim_id}")

    seen_result_ids: set[str] = set()
    for row in results:
        result_id = (row.get("result_id") or "").strip()
        experiment_id = (row.get("experiment_id") or "").strip()
        if not result_id:
            errors.append(f"result row missing result_id: {row}")
            continue
        if result_id in seen_result_ids:
            errors.append(f"duplicate result_id: {result_id}")
        seen_result_ids.add(result_id)
        if experiment_id not in experiment_by_id:
            errors.append(
                f"result {result_id} references unknown experiment {experiment_id or '<missing>'}"
            )

    for row in experiments:
        experiment_id = (row.get("experiment_id") or "").strip()
        for claim_id in parse_claim_ids(row.get("claim_ids")):
            if claim_id not in claim_by_id:
                errors.append(f"experiment {experiment_id} references unknown claim_id: {claim_id}")

    return experiment_by_id, claim_by_id


def validate_minimum_claim_standard(
    experiments: list[dict[str, str]],
    results: list[dict[str, str]],
    claim_by_id: dict[str, dict[str, str]],
    config: dict[str, Any],
    benchmarks: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    standard = config.get("minimum_claim_standard")
    if not isinstance(standard, dict):
        errors.append("docs_config.yaml missing minimum_claim_standard mapping")
        return

    exploratory_trials = 5
    label = standard.get("exploratory_trial_count_label")
    if isinstance(label, str):
        label_counts = parse_trial_counts(label)
        if label_counts:
            exploratory_trials = label_counts[0]

    preferred_validation_trials = standard.get("preferred_validation_trials")
    if not isinstance(preferred_validation_trials, int):
        preferred_validation_trials = 30

    require_matched = bool(standard.get("require_matched_trial_counts", True))
    require_zero_spike = bool(standard.get("require_zero_spike_trial_retention", True))
    require_fdr = bool(standard.get("require_fdr_correction", True))

    benchmark_by_experiment: dict[str, str] = {}
    for benchmark_id, record in benchmarks.items():
        experiment_id = record.get("experiment_id")
        claim_tier = record.get("claim_tier")
        if isinstance(experiment_id, str) and experiment_id.strip() and isinstance(claim_tier, str):
            benchmark_by_experiment[experiment_id.strip()] = claim_tier

    results_by_experiment: dict[str, list[dict[str, str]]] = {}
    for row in results:
        experiment_id = (row.get("experiment_id") or "").strip()
        if experiment_id:
            results_by_experiment.setdefault(experiment_id, []).append(row)

    for row in experiments:
        experiment_id = (row.get("experiment_id") or "").strip()
        status = (row.get("status") or "").strip()
        claim_tier = infer_claim_tier(status, row)
        trial_mode = classify_trial_mode(row.get("n_trials"))
        trial_counts = parse_trial_counts(row.get("n_trials"))

        if experiment_id in benchmark_by_experiment:
            expected_tier = benchmark_by_experiment[experiment_id]
            if claim_tier != expected_tier and not (
                claim_tier == "other" and expected_tier == "infrastructure"
            ):
                errors.append(
                    f"experiment {experiment_id} claim tier {claim_tier} "
                    f"does not match benchmark tier {expected_tier}"
                )

        if claim_tier == "exploratory":
            if trial_mode == "numeric":
                max_trials = max(trial_counts)
                if max_trials >= preferred_validation_trials:
                    errors.append(
                        f"experiment {experiment_id} is exploratory but records "
                        f"{max_trials} trials (preferred validation is {preferred_validation_trials})"
                    )
                elif max_trials > exploratory_trials:
                    errors.append(
                        f"experiment {experiment_id} is exploratory but records "
                        f"{max_trials} trials (expected {exploratory_trials}-trial screen)"
                    )
            for claim_id in parse_claim_ids(row.get("claim_ids")):
                claim = claim_by_id.get(claim_id)
                if claim and claim_status_is_validated(claim.get("status") or ""):
                    if not text_mentions_exploratory_caveat(row.get("notes"), row.get("key_outcome")):
                        errors.append(
                            f"experiment {experiment_id} is exploratory but references "
                            f"validated claim {claim_id} without an exploratory caveat"
                        )

        if claim_tier == "validated":
            if trial_mode != "numeric":
                errors.append(
                    f"experiment {experiment_id} is validated but n_trials is not recorded numerically"
                )
            else:
                min_trials = min(trial_counts)
                max_trials = max(trial_counts)
                if min_trials < preferred_validation_trials:
                    errors.append(
                        f"experiment {experiment_id} is validated but records "
                        f"{min_trials} trials (minimum required: {preferred_validation_trials})"
                    )
                if require_matched and len(set(trial_counts)) > 1:
                    errors.append(
                        f"experiment {experiment_id} is validated but trial counts are not matched: "
                        f"{trial_counts}"
                    )
                if status_contains_label(status, "exploratory"):
                    errors.append(
                        f"experiment {experiment_id} status mixes validated and exploratory labels"
                    )

            if require_fdr and is_statistical_experiment(row):
                if not text_mentions_fdr(
                    row.get("notes"),
                    row.get("key_outcome"),
                    row.get("primary_output"),
                ):
                    errors.append(
                        f"experiment {experiment_id} is a validated statistical experiment "
                        "but does not document FDR correction"
                    )

            if require_zero_spike and is_perturbation_experiment(row):
                if not text_mentions_zero_spike_retention(
                    row.get("notes"),
                    row.get("script_or_file"),
                    row.get("claim_ids"),
                ):
                    errors.append(
                        f"experiment {experiment_id} is a validated perturbation experiment "
                        "but does not document zero-spike trial retention"
                    )

        experiment_results = results_by_experiment.get(experiment_id, [])
        for result_row in experiment_results:
            result_id = (result_row.get("result_id") or "").strip()
            result_status = (result_row.get("status") or "").strip()
            raw_p = (result_row.get("raw_p") or "").strip()
            fdr_q = (result_row.get("fdr_q") or "").strip()

            if claim_tier == "exploratory" and claim_status_is_validated(result_status):
                if not text_mentions_exploratory_caveat(
                    result_row.get("caveat"),
                    result_row.get("interpretation"),
                ):
                    errors.append(
                        f"result {result_id} for exploratory experiment {experiment_id} "
                        "uses a validated status without an exploratory caveat"
                    )

            if claim_tier == "validated" and claim_status_is_validated(result_status) and raw_p:
                if require_fdr and not fdr_q and not text_mentions_fdr(
                    row.get("notes"),
                    result_row.get("caveat"),
                    result_row.get("interpretation"),
                ):
                    errors.append(
                        f"result {result_id} for validated experiment {experiment_id} "
                        "reports raw p-values without FDR q-values or an FDR caveat"
                    )


def validate_research_docs(
    repo_root: Path,
    docs_root: Path | None = None,
    *,
    require_minimum_claim_standard: bool = True,
) -> list[str]:
    """Return validation errors for the canonical research documentation pack."""
    docs_root = (docs_root or repo_root).resolve()
    errors: list[str] = []

    validate_required_files(docs_root, errors)

    exp_path = docs_root / "03_EXPERIMENT_REGISTRY.csv"
    claim_path = docs_root / "11_CLAIMS_REGISTER.csv"
    result_path = docs_root / "04_RESULTS_LEDGER.csv"

    experiments = read_csv(exp_path) if exp_path.exists() else []
    claims = read_csv(claim_path) if claim_path.exists() else []
    results = read_csv(result_path) if result_path.exists() else []

    experiment_by_id, claim_by_id = validate_basic_registry_rows(experiments, claims, results, errors)

    if require_minimum_claim_standard:
        config = load_docs_config(docs_root)
        benchmarks = load_optional_benchmark_registry(repo_root)
        validate_minimum_claim_standard(
            experiments,
            results,
            claim_by_id,
            config,
            benchmarks,
            errors,
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve optional benchmark registry files.",
    )
    parser.add_argument(
        "--research-docs-root",
        default=None,
        help="Directory containing the canonical research documentation pack (defaults to repo root).",
    )
    parser.add_argument(
        "--skip-minimum-claim-standard",
        action="store_true",
        help="Skip minimum_claim_standard enforcement for legacy fixtures.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    docs_root = Path(args.research_docs_root).resolve() if args.research_docs_root else repo_root
    errors = validate_research_docs(
        repo_root,
        docs_root,
        require_minimum_claim_standard=not args.skip_minimum_claim_standard,
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
