import importlib.util
import json
from pathlib import Path

import yaml


def load_module():
    module_path = Path.cwd() / "tools/validate_benchmarks.py"
    spec = importlib.util.spec_from_file_location("validate_benchmarks", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_minimal_registry(repo_root: Path, benchmarks: dict) -> Path:
    registry_path = repo_root / "data/benchmark_registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "0.1",
                "benchmarks": benchmarks,
            }
        ),
        encoding="utf-8",
    )
    return registry_path


def write_minimal_evaluation_config(repo_root: Path) -> Path:
    config_path = repo_root / "configs/benchmark_evaluation.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        (Path.cwd() / "configs/benchmark_evaluation.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return config_path


def base_benchmark(**overrides):
    record = {
        "name": "fixture",
        "description": "fixture benchmark",
        "claim_tier": "infrastructure",
        "experiment_id": None,
        "dataset": {"materialization": None, "required_inputs": []},
        "evaluation": {"primary_metric": "fixture_metric"},
        "reference_outputs": [],
    }
    record.update(overrides)
    return record


def test_committed_benchmark_registry_passes():
    module = load_module()
    repo_root = Path.cwd()
    errors, report = module.validate_benchmarks(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
        experiment_registry_path=repo_root / "03_EXPERIMENT_REGISTRY.csv",
        input_manifest_path=repo_root / "data/input_manifest.json",
        results_ledger_path=repo_root / "04_RESULTS_LEDGER.csv",
    )
    assert errors == [], errors
    assert report["summary"]["failed"] == 0
    assert report["summary"]["total"] == 3


def test_rejects_unknown_claim_tier(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_minimal_registry(
        repo_root,
        {
            "BM099": base_benchmark(claim_tier="not_a_real_tier"),
        },
    )
    write_minimal_evaluation_config(repo_root)

    errors, report = module.validate_benchmarks(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
        experiment_registry_path=repo_root / "03_EXPERIMENT_REGISTRY.csv",
        input_manifest_path=repo_root / "data/input_manifest.json",
        results_ledger_path=repo_root / "04_RESULTS_LEDGER.csv",
    )

    assert any("unknown claim_tier" in error for error in errors)
    assert report["benchmarks"][0]["status"] == "fail"


def test_rejects_unknown_experiment_reference(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_minimal_registry(
        repo_root,
        {
            "BM099": base_benchmark(
                experiment_id="E999",
                claim_tier="infrastructure",
            ),
        },
    )
    write_minimal_evaluation_config(repo_root)
    (repo_root / "03_EXPERIMENT_REGISTRY.csv").write_text(
        (Path.cwd() / "03_EXPERIMENT_REGISTRY.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    errors, report = module.validate_benchmarks(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
        experiment_registry_path=repo_root / "03_EXPERIMENT_REGISTRY.csv",
        input_manifest_path=repo_root / "data/input_manifest.json",
        results_ledger_path=repo_root / "04_RESULTS_LEDGER.csv",
    )

    assert any("unknown experiment_id: E999" in error for error in errors)
    assert report["benchmarks"][0]["status"] == "fail"


def test_rejects_reference_output_checksum_mismatch(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    output = repo_root / "results/statistics.csv"
    output.parent.mkdir(parents=True)
    output.write_text("wrong\n", encoding="utf-8")
    write_minimal_registry(
        repo_root,
        {
            "BM003": base_benchmark(
                claim_tier="validated",
                experiment_id="E007",
                dataset={"materialization": "630", "required_inputs": []},
                evaluation={
                    "primary_metric": "delta_hz",
                    "minimum_trials": 30,
                    "require_matched_trials": True,
                    "require_fdr_reporting": True,
                    "require_zero_spike_retention": True,
                },
                reference_outputs=[
                    {
                        "path": "results/statistics.csv",
                        "required": True,
                        "sha256": "0" * 64,
                    }
                ],
            ),
        },
    )
    write_minimal_evaluation_config(repo_root)
    (repo_root / "03_EXPERIMENT_REGISTRY.csv").write_text(
        (Path.cwd() / "03_EXPERIMENT_REGISTRY.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    errors, report = module.validate_benchmarks(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
        experiment_registry_path=repo_root / "03_EXPERIMENT_REGISTRY.csv",
        input_manifest_path=repo_root / "data/input_manifest.json",
        results_ledger_path=repo_root / "04_RESULTS_LEDGER.csv",
    )

    assert any("sha256 mismatch" in error for error in errors)
    assert report["benchmarks"][0]["status"] == "fail"


def test_rejects_missing_required_input(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_minimal_registry(
        repo_root,
        {
            "BM001": base_benchmark(
                dataset={
                    "materialization": "630",
                    "required_inputs": ["missing_input.csv"],
                }
            ),
        },
    )
    write_minimal_evaluation_config(repo_root)
    (repo_root / "data/input_manifest.json").write_text(
        json.dumps({"inputs": []}),
        encoding="utf-8",
    )

    errors, report = module.validate_benchmarks(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
        experiment_registry_path=repo_root / "03_EXPERIMENT_REGISTRY.csv",
        input_manifest_path=repo_root / "data/input_manifest.json",
        results_ledger_path=repo_root / "04_RESULTS_LEDGER.csv",
    )

    assert any("missing required input in manifest" in error for error in errors)
    assert report["benchmarks"][0]["status"] == "fail"


def test_report_writer_produces_json(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_minimal_registry(repo_root, {"BM001": base_benchmark()})
    write_minimal_evaluation_config(repo_root)
    report_path = repo_root / "benchmark_evaluation_report.json"

    errors, report = module.validate_benchmarks(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
        experiment_registry_path=repo_root / "03_EXPERIMENT_REGISTRY.csv",
        input_manifest_path=repo_root / "data/input_manifest.json",
        results_ledger_path=repo_root / "04_RESULTS_LEDGER.csv",
    )
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    assert errors == []
    loaded = json.loads(report_path.read_text(encoding="utf-8"))
    assert loaded["summary"]["total"] == 1


def test_backwards_compatible_when_benchmark_tool_not_invoked(tmp_path):
    module = load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    assert (repo_root / "data/benchmark_registry.yaml").exists() is False
    errors, report = module.validate_benchmarks(
        repo_root,
        registry_path=repo_root / "data/benchmark_registry.yaml",
        evaluation_config_path=repo_root / "configs/benchmark_evaluation.yaml",
        experiment_registry_path=repo_root / "03_EXPERIMENT_REGISTRY.csv",
        input_manifest_path=repo_root / "data/input_manifest.json",
        results_ledger_path=repo_root / "04_RESULTS_LEDGER.csv",
    )
    assert any("benchmark registry must be a YAML mapping" in error for error in errors)
    assert report == {}
