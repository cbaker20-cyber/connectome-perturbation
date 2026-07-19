import importlib.util
import json
import shutil
import subprocess
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


def test_writer_records_run_config_snapshot(tmp_path):
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
                "random_seed": 42,
                "selected_materialization": "630",
                "selected_inputs": {
                    "completeness": "2023_03_23_completeness_630_final.csv",
                    "connectivity": "2023_03_23_connectivity_630_final.parquet",
                    "annotations": "flywire_annotations.tsv",
                },
            }
        ),
        encoding="utf-8",
    )

    snapshot = writer.load_run_config_snapshot(config_path)

    assert snapshot["random_seed"] == 42
    assert snapshot["selected_materialization"] == "630"
    assert snapshot["selected_inputs"]["connectivity"] == "2023_03_23_connectivity_630_final.parquet"


def test_end_to_end_smoke_output_manifest_passes_validation(tmp_path):
    writer = load_writer()
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo_root, check=True, capture_output=True)
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    config_dir = repo_root / "configs"
    config_dir.mkdir()
    config_path = config_dir / "smoke_run.yaml"
    config_path.write_text((Path.cwd() / "configs/smoke_run.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copy(Path.cwd() / "03_EXPERIMENT_REGISTRY.csv", repo_root / "03_EXPERIMENT_REGISTRY.csv")
    data_dir = repo_root / "data"
    data_dir.mkdir()
    input_manifest_path = data_dir / "input_manifest.json"
    input_manifest_path.write_text((Path.cwd() / "data/input_manifest.json").read_text(encoding="utf-8"), encoding="utf-8")
    for record in json.loads(input_manifest_path.read_text())["inputs"]:
        source = Path.cwd() / record["path"]
        target = repo_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    artifact = repo_root / "results" / "reproducibility_smoke_artifact.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text('{"claim_status":"not_interpretable_as_neuroscience"}\n', encoding="utf-8")
    output_manifest_path = repo_root / "output_manifest.json"

    manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-18T12:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "python tools/write_output_manifest.py",
        "repo_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip(),
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": writer.sha256_file(config_path),
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": True,
        "input_count": 5,
        "input_checksums": writer.input_manifest_checksums(json.loads(input_manifest_path.read_text())),
        "run_config": writer.load_run_config_snapshot(config_path),
        "experiment_id": "E010",
        "experiment_registry_path": "03_EXPERIMENT_REGISTRY.csv",
        "environment": {"python": "3.11", "platform": "linux", "executable": "/usr/bin/python3"},
        "outputs": writer.output_artifact_records(repo_root, ["results/reproducibility_smoke_artifact.json"]),
        "claim_status": "not_interpretable_as_neuroscience",
    }
    output_manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    input_manifest = validator.validate_input_manifest(repo_root, input_manifest_path, errors)
    validator.validate_output_manifest(
        repo_root,
        output_manifest_path,
        errors,
        input_manifest=input_manifest,
        input_manifest_path=input_manifest_path,
    )

    assert errors == []


def test_validator_rejects_stale_run_config_seed(tmp_path):
    validator = load_validator()
    writer = load_writer()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")
    config_dir = repo_root / "configs"
    config_dir.mkdir()
    config_path = config_dir / "smoke_run.yaml"
    config_path.write_text("random_seed: 42\n", encoding="utf-8")
    artifact = repo_root / "results/out.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-18T12:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "test",
        "repo_commit": "abc",
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": writer.sha256_file(config_path),
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "run_config": {"random_seed": 99},
        "environment": {"python": "3.11", "platform": "linux", "executable": "/usr/bin/python3"},
        "outputs": writer.output_artifact_records(repo_root, ["results/out.json"]),
        "claim_status": "not_interpretable_as_neuroscience",
    }
    output_manifest_path = repo_root / "output_manifest.json"
    output_manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    validator.validate_output_manifest(repo_root, output_manifest_path, errors)

    assert "output run_config.random_seed does not match config file contents" in errors
