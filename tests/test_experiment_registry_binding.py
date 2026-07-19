import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


def load_writer():
    module_path = Path.cwd() / "tools/write_output_manifest.py"
    spec = importlib.util.spec_from_file_location("write_output_manifest", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_validator():
    module_path = Path.cwd() / "tools/validate_reproducibility.py"
    spec = importlib.util.spec_from_file_location("validate_reproducibility", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_registry(repo_root: Path, rows: list[dict[str, str]]) -> Path:
    registry_path = repo_root / "03_EXPERIMENT_REGISTRY.csv"
    fieldnames = [
        "experiment_id",
        "date",
        "short_name",
        "type",
        "stimulus",
        "perturbation_target",
        "n_trials",
        "duration_s",
        "script_or_file",
        "primary_output",
        "status",
        "key_outcome",
        "claim_ids",
        "notes",
    ]
    with registry_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return registry_path


def test_writer_records_experiment_id_from_config(tmp_path):
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")
    config_dir = repo_root / "configs"
    config_dir.mkdir()
    config_path = config_dir / "smoke_run.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "experiment_id": "E010",
                "experiment_registry_path": "03_EXPERIMENT_REGISTRY.csv",
                "random_seed": 42,
            }
        ),
        encoding="utf-8",
    )

    snapshot = writer.load_run_config_snapshot(config_path)

    assert snapshot["experiment_id"] == "E010"
    assert snapshot["experiment_registry_path"] == "03_EXPERIMENT_REGISTRY.csv"


def test_validate_experiment_binding_accepts_matching_outputs(tmp_path):
    validator = load_validator()
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        [
            {
                "experiment_id": "E010",
                "date": "2026-07-19",
                "short_name": "smoke",
                "type": "metadata",
                "stimulus": "none",
                "perturbation_target": "none",
                "n_trials": "0",
                "duration_s": "0",
                "script_or_file": "tools/write_smoke_artifact.py",
                "primary_output": "results/reproducibility_smoke_artifact.json",
                "status": "validated",
                "key_outcome": "ok",
                "claim_ids": "",
                "notes": "",
            }
        ],
    )
    artifact = repo_root / "results/reproducibility_smoke_artifact.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}\n", encoding="utf-8")
    config_path = repo_root / "configs/smoke_run.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("random_seed: 42\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-19T01:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "test",
        "repo_commit": "abc123",
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": writer.sha256_file(config_path),
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "run_config": {"random_seed": 42},
        "environment": {"python": "3.11", "platform": "linux", "executable": "/usr/bin/python3"},
        "experiment_id": "E010",
        "experiment_registry_path": "03_EXPERIMENT_REGISTRY.csv",
        "outputs": writer.output_artifact_records(repo_root, ["results/reproducibility_smoke_artifact.json"]),
        "claim_status": "not_interpretable_as_neuroscience",
    }
    manifest_path = repo_root / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    validator.validate_output_manifest(
        repo_root,
        manifest_path,
        errors,
        require_experiment_binding=True,
    )

    assert errors == []


def test_validate_experiment_binding_rejects_unknown_experiment_id(tmp_path):
    validator = load_validator()
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        [
            {
                "experiment_id": "E010",
                "date": "2026-07-19",
                "short_name": "smoke",
                "type": "metadata",
                "stimulus": "none",
                "perturbation_target": "none",
                "n_trials": "0",
                "duration_s": "0",
                "script_or_file": "tools/write_smoke_artifact.py",
                "primary_output": "results/reproducibility_smoke_artifact.json",
                "status": "validated",
                "key_outcome": "ok",
                "claim_ids": "",
                "notes": "",
            }
        ],
    )
    artifact = repo_root / "results/reproducibility_smoke_artifact.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}\n", encoding="utf-8")
    config_path = repo_root / "configs/smoke_run.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("random_seed: 42\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-19T01:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "test",
        "repo_commit": "abc123",
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": writer.sha256_file(config_path),
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "run_config": {"random_seed": 42},
        "environment": {"python": "3.11", "platform": "linux", "executable": "/usr/bin/python3"},
        "experiment_id": "E999",
        "experiment_registry_path": "03_EXPERIMENT_REGISTRY.csv",
        "outputs": writer.output_artifact_records(repo_root, ["results/reproducibility_smoke_artifact.json"]),
        "claim_status": "not_interpretable_as_neuroscience",
    }
    manifest_path = repo_root / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    validator.validate_output_manifest(repo_root, manifest_path, errors)

    assert "output manifest experiment_id not found in registry: E999" in errors


def test_validate_experiment_binding_rejects_output_mismatch(tmp_path):
    validator = load_validator()
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_registry(
        repo_root,
        [
            {
                "experiment_id": "E010",
                "date": "2026-07-19",
                "short_name": "smoke",
                "type": "metadata",
                "stimulus": "none",
                "perturbation_target": "none",
                "n_trials": "0",
                "duration_s": "0",
                "script_or_file": "tools/write_smoke_artifact.py",
                "primary_output": "results/reproducibility_smoke_artifact.json",
                "status": "validated",
                "key_outcome": "ok",
                "claim_ids": "",
                "notes": "",
            }
        ],
    )
    wrong = repo_root / "results/wrong.json"
    wrong.parent.mkdir(parents=True)
    wrong.write_text("{}\n", encoding="utf-8")
    config_path = repo_root / "configs/smoke_run.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("random_seed: 42\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-19T01:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "test",
        "repo_commit": "abc123",
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": writer.sha256_file(config_path),
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "run_config": {"random_seed": 42},
        "environment": {"python": "3.11", "platform": "linux", "executable": "/usr/bin/python3"},
        "experiment_id": "E010",
        "experiment_registry_path": "03_EXPERIMENT_REGISTRY.csv",
        "outputs": writer.output_artifact_records(repo_root, ["results/wrong.json"]),
        "claim_status": "not_interpretable_as_neuroscience",
    }
    manifest_path = repo_root / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    validator.validate_output_manifest(repo_root, manifest_path, errors)

    assert any("primary_output" in error for error in errors)


def test_smoke_end_to_end_with_experiment_binding():
    repo_root = Path.cwd()
    result = subprocess.run(
        [
            sys.executable,
            "tools/write_smoke_artifact.py",
            "--output",
            "results/reproducibility_smoke_artifact.json",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        [
            sys.executable,
            "tools/write_output_manifest.py",
            "--config",
            "configs/smoke_run.yaml",
            "--input-manifest",
            "data/input_manifest.json",
            "--output",
            "output_manifest.json",
            "--artifact",
            "results/reproducibility_smoke_artifact.json",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads((repo_root / "output_manifest.json").read_text(encoding="utf-8"))
    assert manifest.get("experiment_id") == "E010"

    validator = load_validator()
    errors: list[str] = []
    input_manifest = validator.validate_input_manifest(
        repo_root,
        repo_root / "data/input_manifest.json",
        errors,
        require_provenance=True,
    )
    validator.validate_smoke_config(repo_root, repo_root / "configs/smoke_run.yaml", errors, input_manifest=input_manifest)
    validator.validate_output_manifest(
        repo_root,
        repo_root / "output_manifest.json",
        errors,
        input_manifest=input_manifest,
        input_manifest_path=repo_root / "data/input_manifest.json",
        require_experiment_binding=True,
    )
    assert errors == [], errors


def test_backwards_compatible_without_experiment_id(tmp_path):
    validator = load_validator()
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    artifact = repo_root / "results/out.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}\n", encoding="utf-8")
    config_path = repo_root / "configs/smoke_run.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("random_seed: 42\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-19T01:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "test",
        "repo_commit": "abc123",
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": writer.sha256_file(config_path),
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "run_config": {"random_seed": 42},
        "environment": {"python": "3.11", "platform": "linux", "executable": "/usr/bin/python3"},
        "outputs": writer.output_artifact_records(repo_root, ["results/out.json"]),
        "claim_status": "not_interpretable_as_neuroscience",
    }
    manifest_path = repo_root / "output_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    validator.validate_output_manifest(repo_root, manifest_path, errors)

    assert errors == []
