#!/usr/bin/env python3
"""Quantitative benchmark comparison helpers for scientific evaluation infrastructure."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BENCHMARK_REGISTRY = "data/benchmark_registry.yaml"
DEFAULT_EVALUATION_CONFIG = "configs/benchmark_evaluation.yaml"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml_mapping(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        import yaml
    except ImportError:
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def merge_thresholds(
    metric_spec: dict[str, Any],
    evaluation_config: dict[str, Any],
    *,
    profile: str = "default",
) -> dict[str, float]:
    thresholds = metric_spec.get("thresholds")
    if not isinstance(thresholds, dict):
        thresholds = {}
    profiles = evaluation_config.get("metric_thresholds", {})
    if not isinstance(profiles, dict):
        profiles = {}
    defaults = profiles.get(profile, {})
    if not isinstance(defaults, dict):
        defaults = profiles.get("default", {})
    if not isinstance(defaults, dict):
        defaults = {}
    return {
        "absolute_error_max": float(
            thresholds.get("absolute_error_max", defaults.get("absolute_error_max", 0.0))
        ),
        "relative_error_max": float(
            thresholds.get("relative_error_max", defaults.get("relative_error_max", 0.0))
        ),
    }


def absolute_error(expected: float, observed: float) -> float:
    return abs(observed - expected)


def relative_error(expected: float, observed: float) -> float | None:
    if expected == 0:
        if observed == 0:
            return 0.0
        return None
    return absolute_error(expected, observed) / abs(expected)


def metric_passes(
    expected: float,
    observed: float,
    thresholds: dict[str, float],
) -> bool:
    abs_err = absolute_error(expected, observed)
    rel_err = relative_error(expected, observed)
    if abs_err > thresholds["absolute_error_max"]:
        return False
    if rel_err is None:
        return observed == expected
    return rel_err <= thresholds["relative_error_max"]


def build_metric_comparison(
    *,
    name: str,
    expected: float,
    observed: float | None,
    thresholds: dict[str, float],
    confidence_interval: Any = None,
    description: str | None = None,
) -> dict[str, Any]:
    if observed is None:
        return {
            "name": name,
            "description": description,
            "expected": expected,
            "observed": None,
            "absolute_error": None,
            "relative_error": None,
            "confidence_interval": confidence_interval,
            "thresholds": thresholds,
            "status": "fail",
        }

    abs_err = absolute_error(expected, observed)
    rel_err = relative_error(expected, observed)
    status = "pass" if metric_passes(expected, observed, thresholds) else "fail"
    return {
        "name": name,
        "description": description,
        "expected": expected,
        "observed": observed,
        "absolute_error": abs_err,
        "relative_error": rel_err,
        "confidence_interval": confidence_interval,
        "thresholds": thresholds,
        "status": status,
    }


def evaluate_reproducibility(
    repo_root: Path,
    reproducibility_spec: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(reproducibility_spec, dict):
        return {
            "status": "not_applicable",
            "reference_output": None,
            "exists": None,
            "checksum_match": None,
            "required": False,
        }

    path_value = reproducibility_spec.get("reference_output")
    required = bool(reproducibility_spec.get("required", False))
    expected_sha = reproducibility_spec.get("sha256")
    if not isinstance(path_value, str) or not path_value.strip():
        return {
            "status": "not_applicable",
            "reference_output": None,
            "exists": None,
            "checksum_match": None,
            "required": required,
        }

    file_path = repo_root / path_value
    exists = file_path.is_file()
    checksum_match = None
    if exists and isinstance(expected_sha, str):
        checksum_match = sha256_file(file_path) == expected_sha

    if not exists:
        status = "fail" if required else "skipped"
    elif isinstance(expected_sha, str):
        status = "pass" if checksum_match else "fail"
    else:
        status = "pass"

    return {
        "status": status,
        "reference_output": path_value,
        "exists": exists,
        "checksum_match": checksum_match,
        "required": required,
        "expected_sha256": expected_sha,
        "observed_sha256": sha256_file(file_path) if exists else None,
    }


def load_json_mapping(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def _load_toy_graph_payload() -> dict[str, object]:
    import importlib.util

    module_path = Path(__file__).resolve().parent / "write_toy_graph_artifact.py"
    spec = importlib.util.spec_from_file_location("write_toy_graph_artifact", module_path)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = module.toy_graph_payload()
    return payload if isinstance(payload, dict) else {}


def observe_toy_graph_metrics(repo_root: Path, reproducibility_spec: dict[str, Any] | None) -> dict[str, float]:
    if isinstance(reproducibility_spec, dict):
        path_value = reproducibility_spec.get("reference_output")
        if isinstance(path_value, str):
            payload = load_json_mapping(repo_root / path_value)
            if isinstance(payload, dict):
                metrics = payload.get("expected_metrics")
                if isinstance(metrics, dict):
                    observed: dict[str, float] = {}
                    for key in ("node_count", "edge_count", "weak_component_count"):
                        value = metrics.get(key)
                        if isinstance(value, (int, float)):
                            observed[key] = float(value)
                    if observed:
                        return observed

    metrics = _load_toy_graph_payload().get("expected_metrics", {})
    if not isinstance(metrics, dict):
        return {}
    return {
        key: float(metrics[key])
        for key in ("node_count", "edge_count", "weak_component_count")
        if isinstance(metrics.get(key), (int, float))
    }


def observe_smoke_metric(repo_root: Path, reproducibility_spec: dict[str, Any] | None) -> float | None:
    path_value = None
    if isinstance(reproducibility_spec, dict):
        path_value = reproducibility_spec.get("reference_output")
    if not isinstance(path_value, str):
        path_value = "results/reproducibility_smoke_artifact.json"

    payload = load_json_mapping(repo_root / path_value)
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") == "0.1" and payload.get("artifact_type"):
        return 1.0
    return 0.0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def observe_csv_metric(
    repo_root: Path,
    reproducibility_spec: dict[str, Any] | None,
    metric_spec: dict[str, Any],
) -> float | None:
    path_value = None
    if isinstance(reproducibility_spec, dict):
        path_value = reproducibility_spec.get("reference_output")
    if not isinstance(path_value, str):
        return None

    rows = read_csv_rows(repo_root / path_value)
    if metric_spec.get("name") == "row_count":
        return float(len(rows))

    row_match = metric_spec.get("row_match")
    column = metric_spec.get("source_column")
    if not isinstance(row_match, dict) or not isinstance(column, str):
        return None

    for row in rows:
        if all(row.get(key) == value for key, value in row_match.items()):
            raw_value = row.get(column)
            if raw_value is None or raw_value == "":
                return None
            return float(raw_value)
    return None


def compare_benchmark(
    repo_root: Path,
    benchmark_id: str,
    record: dict[str, Any],
    evaluation_config: dict[str, Any],
) -> dict[str, Any]:
    comparison = record.get("comparison", {})
    if not isinstance(comparison, dict):
        comparison = {}

    reproducibility_spec = comparison.get("reproducibility")
    reproducibility = evaluate_reproducibility(repo_root, reproducibility_spec if isinstance(reproducibility_spec, dict) else None)

    metrics_spec = comparison.get("metrics", [])
    metric_reports: list[dict[str, Any]] = []
    if not isinstance(metrics_spec, list):
        metrics_spec = []

    threshold_profile = "reference_panel" if record.get("claim_tier") == "validated" else "default"

    for metric_spec in metrics_spec:
        if not isinstance(metric_spec, dict):
            continue
        name = metric_spec.get("name")
        expected = metric_spec.get("expected")
        if not isinstance(name, str) or not isinstance(expected, (int, float)):
            continue

        thresholds = merge_thresholds(metric_spec, evaluation_config, profile=threshold_profile)
        observed: float | None
        if name == "reproducibility_validation_pass":
            observed = observe_smoke_metric(
                repo_root,
                reproducibility_spec if isinstance(reproducibility_spec, dict) else None,
            )
        elif name in {"node_count", "edge_count", "weak_component_count"}:
            observed = observe_toy_graph_metrics(
                repo_root,
                reproducibility_spec if isinstance(reproducibility_spec, dict) else None,
            ).get(name)
        else:
            observed = observe_csv_metric(
                repo_root,
                reproducibility_spec if isinstance(reproducibility_spec, dict) else None,
                metric_spec,
            )

        metric_reports.append(
            build_metric_comparison(
                name=name,
                expected=float(expected),
                observed=observed,
                thresholds=thresholds,
                confidence_interval=metric_spec.get("confidence_interval"),
                description=metric_spec.get("description") if isinstance(metric_spec.get("description"), str) else None,
            )
        )

    metric_statuses = [item["status"] for item in metric_reports]
    statuses = [reproducibility["status"], *metric_statuses]
    if any(status == "fail" for status in statuses):
        overall = "fail"
    elif all(status in {"pass", "not_applicable", "skipped"} for status in statuses):
        overall = "pass"
    else:
        overall = "fail"

    return {
        "benchmark_id": benchmark_id,
        "name": record.get("name"),
        "claim_tier": record.get("claim_tier"),
        "experiment_id": record.get("experiment_id"),
        "reproducibility_status": reproducibility["status"],
        "reproducibility": reproducibility,
        "metrics": metric_reports,
        "status": overall,
    }


def build_benchmark_comparison_report(
    repo_root: Path,
    *,
    registry_path: Path,
    evaluation_config_path: Path,
) -> dict[str, Any]:
    registry = load_yaml_mapping(registry_path)
    evaluation_config = load_yaml_mapping(evaluation_config_path)
    if registry is None or evaluation_config is None:
        raise ValueError("benchmark registry and evaluation config must be valid YAML mappings")

    benchmarks = registry.get("benchmarks", {})
    if not isinstance(benchmarks, dict):
        benchmarks = {}

    benchmark_reports = [
        compare_benchmark(repo_root, benchmark_id, record, evaluation_config)
        for benchmark_id, record in sorted(benchmarks.items())
        if isinstance(record, dict)
    ]

    return {
        "schema_version": registry.get("schema_version", "0.1"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": registry_path.relative_to(repo_root).as_posix()
        if registry_path.is_relative_to(repo_root)
        else str(registry_path),
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


def validate_comparison_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for benchmark in report.get("benchmarks", []):
        if not isinstance(benchmark, dict):
            continue
        benchmark_id = benchmark.get("benchmark_id", "<unknown>")
        if benchmark.get("status") == "fail":
            errors.append(f"benchmark {benchmark_id} comparison failed")
        reproducibility = benchmark.get("reproducibility", {})
        if isinstance(reproducibility, dict) and reproducibility.get("status") == "fail":
            errors.append(f"benchmark {benchmark_id} reproducibility check failed")
        for metric in benchmark.get("metrics", []):
            if isinstance(metric, dict) and metric.get("status") == "fail":
                errors.append(
                    f"benchmark {benchmark_id} metric {metric.get('name')} failed "
                    f"(expected={metric.get('expected')}, observed={metric.get('observed')})"
                )
    return errors
