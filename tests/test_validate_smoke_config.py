import importlib.util
from pathlib import Path

import pytest
import yaml


def load_validator():
    module_path = Path.cwd() / "tools" / "validate_reproducibility.py"
    spec = importlib.util.spec_from_file_location("validate_reproducibility", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_validate_smoke_config_accepts_committed_smoke_run_yaml():
    validator = load_validator()
    repo_root = Path.cwd()
    errors: list[str] = []
    input_manifest = validator.validate_input_manifest(
        repo_root,
        repo_root / "data/input_manifest.json",
        errors,
    )
    validator.validate_smoke_config(
        repo_root,
        repo_root / "configs/smoke_run.yaml",
        errors,
        input_manifest=input_manifest,
    )
    assert errors == []


def test_validate_smoke_config_rejects_materialization_input_drift(tmp_path):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")
    config_path = repo_root / "configs/smoke_run.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        yaml.safe_dump(
            {
                "selected_materialization": "630",
                "selected_inputs": {
                    "completeness": "Completeness_783.csv",
                    "connectivity": "2023_03_23_connectivity_630_final.parquet",
                    "annotations": "flywire_annotations.tsv",
                },
            }
        ),
        encoding="utf-8",
    )

    errors: list[str] = []
    validator.validate_smoke_config(repo_root, config_path, errors)

    assert any("selected_inputs['completeness']" in error for error in errors)


def test_validate_smoke_config_requires_manifest_paths(tmp_path):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")
    config_path = repo_root / "configs/smoke_run.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        (Path.cwd() / "configs/smoke_run.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    input_manifest = {"inputs": [{"path": "2023_03_23_completeness_630_final.csv"}]}

    errors: list[str] = []
    validator.validate_smoke_config(repo_root, config_path, errors, input_manifest=input_manifest)

    assert "smoke config input missing from input manifest: 2023_03_23_connectivity_630_final.parquet" in errors
