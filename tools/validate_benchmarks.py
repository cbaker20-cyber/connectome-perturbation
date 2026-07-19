#!/usr/bin/env python3
"""Validate the perturbation benchmark registry and evaluation configuration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BENCHMARK_REGISTRY = "data/benchmark_registry.yaml"
DEFAULT_EVALUATION_CONFIG = "configs/benchmark_evaluation.yaml"
DEFAULT_EXPERIMENT_REGISTRY = "03_EXPERIMENT_REGISTRY.csv"
DEFAULT_INPUT_MANIFEST = "data/input_manifest.json"
DEFAULT_RESULTS_LEDGER = "04_RESULTS_LEDGER.csv"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_yaml_mapping(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        import yaml
    except ImportError:
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_input_manifest_paths(repo_root: Path, manifest_path: Path) -> set[str]:
    if not manifest_path.exists():
        return set()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        record.get("path")
        for record in manifest.get("inputs", [])
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    }


def parse_minimum_trials(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None
    digits = []
    current = []
    for char in value:
        if char.isdigit():
            current.append(char)
        elif current:
            digits.append(int("".join(current)))
            current = []
    if current:
        digits.append(int("".join(current)))
    return max(digits) if digits else None


def validate_registry_shape(registry: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    require(isinstance(registry.get("benchmarks"), dict), "benchmark registry benchmarks must be a mapping", errors)
    benchmarks = registry.get("benchmarks")
    if not isinstance(benchmarks, dict):
        return {}
    parsed: dict[str, dict[str, Any]] = {}
    for benchmark_id, record in benchmarks.items():
        require(isinstance(benchmark_id, str) and benchmark_id.strip(), f"benchmark id must be a non-empty string: {benchmark_id!r}", errors)
        require(isinstance(record, dict), f"benchmark {benchmark_id} must be a mapping", errors)
        if not isinstance(record, dict):
            continue
        if benchmark_id in parsed:
            errors.append(f"duplicate benchmark_id: {benchmark_id}")
        parsed[benchmark_id] = record
        for key in ("name", "description", "claim_tier", "dataset", "evaluation"):
            require(key in record, f"benchmark {benchmark_id} missing required field: {key}", errors)
    return parsed


def validate_benchmark_record(
    repo_root: Path,
    benchmark_id: str,
    record: dict[str, Any],
    *,
    experiments: dict[str, dict[str, str]],
    results_ledger_ids: set[str],
    input_paths: set[str],
    tier_requirements: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    """Validate one benchmark and return a standardized report record."""
    report: dict[str, Any] = {
        "benchmark_id": benchmark_id,
        "name": record.get("name"),
        "claim_tier": record.get("claim_tier"),
        "status": "pass",
        "checks": [],
    }

    claim_tier = record.get("claim_tier")
    tier_rules = tier_requirements.get(claim_tier) if isinstance(claim_tier, str) else None
    require(isinstance(tier_rules, dict), f"benchmark {benchmark_id} has unknown claim_tier: {claim_tier}", errors)
    if not isinstance(tier_rules, dict):
        report["status"] = "fail"
        return report

    experiment_id = record.get("experiment_id")
    if experiment_id not in (None, "null", ""):
        require(isinstance(experiment_id, str), f"benchmark {benchmark_id} experiment_id must be a string or null", errors)
        if isinstance(experiment_id, str):
            ok = experiment_id in experiments
            require(ok, f"benchmark {benchmark_id} references unknown experiment_id: {experiment_id}", errors)
            report["experiment_id"] = experiment_id
            if not ok:
                report["status"] = "fail"
            elif experiment_id in experiments:
                exp_row = experiments[experiment_id]
                eval_block = record.get("evaluation", {})
                if isinstance(eval_block, dict) and tier_rules.get("minimum_trials", 0):
                    expected_trials = eval_block.get("minimum_trials") or tier_rules.get("minimum_trials")
                    observed_trials = parse_minimum_trials(exp_row.get("n_trials"))
                    ok = observed_trials is not None and observed_trials >= int(expected_trials)
                    report["checks"].append(
                        {
                            "name": "experiment_minimum_trials",
                            "status": "pass" if ok else "fail",
                            "expected_minimum_trials": expected_trials,
                            "observed_trials": observed_trials,
                        }
                    )
                    require(ok, f"benchmark {benchmark_id} experiment {experiment_id} does not meet minimum_trials", errors)
                    if not ok:
                        report["status"] = "fail"

    dataset = record.get("dataset", {})
    if isinstance(dataset, dict):
        required_inputs = dataset.get("required_inputs", [])
        if isinstance(required_inputs, list):
            missing_inputs = [path for path in required_inputs if path not in input_paths]
            ok = not missing_inputs
            report["checks"].append(
                {
                    "name": "dataset_integrity",
                    "status": "pass" if ok else "fail",
                    "missing_inputs": missing_inputs,
                }
            )
            for path in missing_inputs:
                errors.append(f"benchmark {benchmark_id} missing required input in manifest: {path}")
            if not ok:
                report["status"] = "fail"
            else:
                present = []
                for path in required_inputs:
                    file_path = repo_root / path
                    if file_path.is_file():
                        present.append({"path": path, "sha256": sha256_file(file_path)})
                report["dataset_checksums"] = present

    evaluation = record.get("evaluation", {})
    if isinstance(evaluation, dict):
        for flag in ("require_matched_trials", "require_fdr_reporting", "require_zero_spike_retention"):
            if flag in evaluation and bool(evaluation.get(flag)) != bool(tier_rules.get(flag)):
                errors.append(
                    f"benchmark {benchmark_id} evaluation.{flag} does not match claim tier requirements"
                )
                report["status"] = "fail"
        ledger_ids = evaluation.get("reference_results_ledger_ids", [])
        if isinstance(ledger_ids, list) and ledger_ids:
            missing_ids = [item for item in ledger_ids if item not in results_ledger_ids]
            ok = not missing_ids
            report["checks"].append(
                {
                    "name": "results_ledger_references",
                    "status": "pass" if ok else "fail",
                    "missing_result_ids": missing_ids,
                }
            )
            for missing_id in missing_ids:
                errors.append(f"benchmark {benchmark_id} references unknown result_id: {missing_id}")
            if not ok:
                report["status"] = "fail"

    reference_outputs = record.get("reference_outputs", [])
    output_reports = []
    if isinstance(reference_outputs, list):
        for idx, output_record in enumerate(reference_outputs):
            if not isinstance(output_record, dict):
                errors.append(f"benchmark {benchmark_id} reference_outputs[{idx}] must be a mapping")
                report["status"] = "fail"
                continue
            path_value = output_record.get("path")
            required = bool(output_record.get("required", False))
            if not isinstance(path_value, str) or not path_value.strip():
                errors.append(f"benchmark {benchmark_id} reference output missing path")
                report["status"] = "fail"
                continue
            file_path = repo_root / path_value
            exists = file_path.is_file()
            checksum_match = None
            expected_sha = output_record.get("sha256")
            if exists and isinstance(expected_sha, str):
                checksum_match = sha256_file(file_path) == expected_sha
            entry = {
                "path": path_value,
                "required": required,
                "exists": exists,
                "checksum_match": checksum_match,
            }
            output_reports.append(entry)
            if required:
                require(exists, f"benchmark {benchmark_id} required reference output missing: {path_value}", errors)
                if not exists:
                    report["status"] = "fail"
            if isinstance(expected_sha, str) and exists:
                require(
                    checksum_match is True,
                    f"benchmark {benchmark_id} reference output sha256 mismatch: {path_value}",
                    errors,
                )
                if checksum_match is not True:
                    report["status"] = "fail"
    report["reference_outputs"] = output_reports
    return report


def validate_benchmarks(
    repo_root: Path,
    *,
    registry_path: Path,
    evaluation_config_path: Path,
    experiment_registry_path: Path,
    input_manifest_path: Path,
    results_ledger_path: Path,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    registry = load_yaml_mapping(registry_path)
    evaluation_config = load_yaml_mapping(evaluation_config_path)
    require(registry is not None, f"benchmark registry must be a YAML mapping: {registry_path}", errors)
    require(evaluation_config is not None, f"benchmark evaluation config must be a YAML mapping: {evaluation_config_path}", errors)
    if registry is None or evaluation_config is None:
        return errors, {}

    benchmarks = validate_registry_shape(registry, errors)
    tier_requirements = evaluation_config.get("claim_tier_requirements", {})
    require(isinstance(tier_requirements, dict), "benchmark evaluation claim_tier_requirements must be a mapping", errors)
    if not isinstance(tier_requirements, dict):
        tier_requirements = {}

    experiments: dict[str, dict[str, str]] = {}
    if experiment_registry_path.exists():
        for row in read_csv_rows(experiment_registry_path):
            exp_id = (row.get("experiment_id") or "").strip()
            if exp_id:
                experiments[exp_id] = row

    results_ledger_ids: set[str] = set()
    if results_ledger_path.exists():
        results_ledger_ids = {
            (row.get("result_id") or "").strip()
            for row in read_csv_rows(results_ledger_path)
            if (row.get("result_id") or "").strip()
        }

    input_paths = load_input_manifest_paths(repo_root, input_manifest_path)
    benchmark_reports = []
    for benchmark_id, record in sorted(benchmarks.items()):
        benchmark_reports.append(
            validate_benchmark_record(
                repo_root,
                benchmark_id,
                record,
                experiments=experiments,
                results_ledger_ids=results_ledger_ids,
                input_paths=input_paths,
                tier_requirements=tier_requirements,
                errors=errors,
            )
        )

    report = {
        "schema_version": registry.get("schema_version", "0.1"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": registry_path.relative_to(repo_root).as_posix() if registry_path.is_relative_to(repo_root) else str(registry_path),
        "evaluation_config_path": evaluation_config_path.relative_to(repo_root).as_posix()
        if evaluation_config_path.is_relative_to(repo_root)
        else str(evaluation_config_path),
        "summary": {
            "total": len(benchmark_reports),
            "passed": sum(1 for item in benchmark_reports if item.get("status") == "pass"),
            "failed": sum(1 for item in benchmark_reports if item.get("status") == "fail"),
        },
        "benchmarks": benchmark_reports,
    }
    return errors, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=DEFAULT_BENCHMARK_REGISTRY)
    parser.add_argument("--evaluation-config", default=DEFAULT_EVALUATION_CONFIG)
    parser.add_argument("--experiment-registry", default=DEFAULT_EXPERIMENT_REGISTRY)
    parser.add_argument("--input-manifest", default=DEFAULT_INPUT_MANIFEST)
    parser.add_argument("--results-ledger", default=DEFAULT_RESULTS_LEDGER)
    parser.add_argument(
        "--report",
        default=None,
        help="Optional repo-relative path to write standardized JSON evaluation report.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors, report = validate_benchmarks(
        repo_root,
        registry_path=(repo_root / args.registry).resolve(),
        evaluation_config_path=(repo_root / args.evaluation_config).resolve(),
        experiment_registry_path=(repo_root / args.experiment_registry).resolve(),
        input_manifest_path=(repo_root / args.input_manifest).resolve(),
        results_ledger_path=(repo_root / args.results_ledger).resolve(),
    )
    if args.report:
        report_path = (repo_root / args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote {report_path}")

    if errors:
        print("Benchmark validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Benchmark validation passed")
    if report.get("summary"):
        print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
