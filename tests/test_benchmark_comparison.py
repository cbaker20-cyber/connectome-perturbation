import importlib.util
import json
import sys
import textwrap
from pathlib import Path

import yaml


def load_comparison_module():
    module_path = Path.cwd() / "tools/benchmark_comparison.py"
    spec = importlib.util.spec_from_file_location("benchmark_comparison", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_report_module():
    tools_dir = str(Path.cwd() / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    module_path = Path.cwd() / "tools/report_benchmark_comparison.py"
    spec = importlib.util.spec_from_file_location("report_benchmark_comparison", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_minimal_registry(repo_root: Path, benchmarks: dict) -> None:
    (repo_root / "data").mkdir(parents=True, exist_ok=True)
    (repo_root / "configs").mkdir(parents=True, exist_ok=True)
    (repo_root / "data/benchmark_registry.yaml").write_text(
        yaml.safe_dump({"schema_version": "0.1", "benchmarks": benchmarks}),
        encoding="utf-8",
    )
    (repo_root / "configs/benchmark_evaluation.yaml").write_text(
        (Path.cwd() / "configs/benchmark_evaluation.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def test_committed_registry_generates_quantitative_comparison_report():
    module = load_comparison_module()
    repo_root = Path.cwd()
    report = module.build_benchmark_comparison_report(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
    )
    assert report["summary"]["failed"] == 0
    bm003 = next(item for item in report["benchmarks"] if item["benchmark_id"] == "BM003")
    ascending = next(metric for metric in bm003["metrics"] if metric["name"] == "ascending_delta_hz")
    assert ascending["expected"] == -129.0
    assert ascending["observed"] == -129.0
    assert ascending["absolute_error"] == 0.0
    assert ascending["status"] == "pass"
    assert "thresholds" in ascending
    assert bm003["reproducibility_status"] == "pass"


def test_metric_comparison_reports_absolute_and_relative_error(tmp_path):
    module = load_comparison_module()
    comparison = module.build_metric_comparison(
        name="delta_hz",
        expected=10.0,
        observed=10.5,
        thresholds={"absolute_error_max": 1.0, "relative_error_max": 0.1},
    )
    assert comparison["absolute_error"] == 0.5
    assert comparison["relative_error"] == 0.05
    assert comparison["status"] == "pass"


def test_metric_comparison_marks_failures_against_thresholds(tmp_path):
    module = load_comparison_module()
    comparison = module.build_metric_comparison(
        name="node_count",
        expected=4.0,
        observed=5.0,
        thresholds={"absolute_error_max": 0.0, "relative_error_max": 0.0},
    )
    assert comparison["status"] == "fail"
    assert comparison["absolute_error"] == 1.0


def test_toy_graph_metrics_match_expected_outcomes(tmp_path):
    module = load_comparison_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_minimal_registry(
        repo_root,
        {
            "BM002": {
                "name": "toy_graph",
                "claim_tier": "infrastructure",
                "comparison": {
                    "reproducibility": {
                        "reference_output": "results/toy_graph_artifact.json",
                        "required": False,
                    },
                    "metrics": [
                        {"name": "node_count", "expected": 4, "thresholds": {"absolute_error_max": 0, "relative_error_max": 0}},
                        {"name": "edge_count", "expected": 3, "thresholds": {"absolute_error_max": 0, "relative_error_max": 0}},
                        {"name": "weak_component_count", "expected": 2, "thresholds": {"absolute_error_max": 0, "relative_error_max": 0}},
                    ],
                },
            }
        },
    )

    tools_dir = Path.cwd() / "tools"
    sys.path.insert(0, str(tools_dir))
    from write_toy_graph_artifact import write_toy_graph_artifact

    write_toy_graph_artifact("results/toy_graph_artifact.json")
    artifact_src = Path.cwd() / "results/toy_graph_artifact.json"
    (repo_root / "results").mkdir(parents=True)
    (repo_root / "results/toy_graph_artifact.json").write_text(
        artifact_src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = module.build_benchmark_comparison_report(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
    )
    benchmark = report["benchmarks"][0]
    assert benchmark["status"] == "pass"
    assert all(metric["absolute_error"] == 0.0 for metric in benchmark["metrics"])


def test_statistics_panel_regression_detects_metric_drift(tmp_path):
    module = load_comparison_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_minimal_registry(
        repo_root,
        {
            "BM003": {
                "name": "stats",
                "claim_tier": "validated",
                "comparison": {
                    "reproducibility": {
                        "reference_output": "results/statistics.csv",
                        "required": True,
                    },
                    "metrics": [
                        {
                            "name": "ascending_delta_hz",
                            "source_column": "delta_hz",
                            "row_match": {"label": "ascending"},
                            "expected": -129.0,
                            "thresholds": {"absolute_error_max": 0.01, "relative_error_max": 0.001},
                        }
                    ],
                },
            }
        },
    )
    (repo_root / "results").mkdir(parents=True)
    (repo_root / "results/statistics.csv").write_text(
        "label,exp_name,baseline_mean_hz,perturbed_mean_hz,delta_hz,pct_change,t_stat,p_value,significant\n"
        "ascending,perturb_ascending,1126.6,990.0,-136.6,-12.1,4.4,0.0021,True\n",
        encoding="utf-8",
    )

    report = module.build_benchmark_comparison_report(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
    )
    metric = report["benchmarks"][0]["metrics"][0]
    assert metric["status"] == "fail"
    assert metric["absolute_error"] > 0.01


def test_report_writer_emits_json_file(tmp_path):
    module = load_report_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_minimal_registry(
        repo_root,
        {
            "BM001": {
                "name": "smoke",
                "claim_tier": "infrastructure",
                "comparison": {
                    "reproducibility": {
                        "reference_output": "results/reproducibility_smoke_artifact.json",
                        "required": True,
                    },
                    "metrics": [
                        {
                            "name": "reproducibility_validation_pass",
                            "expected": 1,
                            "thresholds": {"absolute_error_max": 0, "relative_error_max": 0},
                        }
                    ],
                },
            }
        },
    )
    (repo_root / "results").mkdir(parents=True)
    (repo_root / "results/reproducibility_smoke_artifact.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "artifact_type": "metadata_only_reproducibility_smoke",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    output = repo_root / "benchmark_comparison_report.json"

    import subprocess

    completed = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "tools/report_benchmark_comparison.py"),
            "--repo-root",
            str(repo_root),
            "--output",
            "benchmark_comparison_report.json",
            "--fail-on-regression",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["passed"] == 1
    metric = payload["benchmarks"][0]["metrics"][0]
    assert metric["observed"] == 1.0
    assert "reproducibility_status" in payload["benchmarks"][0]


def test_confidence_interval_field_is_preserved_when_not_applicable(tmp_path):
    module = load_comparison_module()
    comparison = module.build_metric_comparison(
        name="row_count",
        expected=10.0,
        observed=10.0,
        thresholds={"absolute_error_max": 0.0, "relative_error_max": 0.0},
        confidence_interval=None,
    )
    assert comparison["confidence_interval"] is None
    assert comparison["status"] == "pass"
