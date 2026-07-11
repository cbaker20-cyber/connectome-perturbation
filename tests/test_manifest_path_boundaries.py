import importlib.util
import json
import sys
from pathlib import Path


SCHEMA_VERSION = "0.1"
AWARE_TIMESTAMP = "2026-07-09T00:00:00+00:00"


def load_validator():
    module_path = Path.cwd() / "tools/validate_reproducibility.py"
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_config(repo_root: Path) -> None:
    config_dir = repo_root / "configs"
    config_dir.mkdir()
    (config_dir / "smoke_run.yaml").write_text("run_name: smoke\nrandom_seed: 42\n", encoding="utf-8")


def input_manifest_for(data_file: Path, validator):
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": AWARE_TIMESTAMP,
        "input_count": 1,
        "inputs": [
            {
                "path": data_file.name,
                "filename": data_file.name,
                "extension": data_file.suffix,
                "size_bytes": data_file.stat().st_size,
                "sha256": validator.sha256_file(data_file),
                "guessed_role": "unknown_input_like_file",
                "provenance": {
                    "dataset_name": None,
                    "release_or_materialization": None,
                    "canonical_url_or_doi": None,
                    "citation": None,
                    "license_or_terms": None,
                    "access_date": None,
                    "redistribution_status": "unknown",
                    "schema_notes": None,
                    "row_count": None,
                    "preprocessing_notes": None,
                },
            }
        ],
    }


def output_manifest_for(repo_root: Path, validator):
    config_path = repo_root / "configs/smoke_run.yaml"
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": AWARE_TIMESTAMP,
        "status": "metadata_only_smoke",
        "command": "python tools/write_output_manifest.py",
        "repo_commit": None,
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": validator.sha256_file(config_path),
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "claim_status": "not_interpretable_as_neuroscience",
    }


def test_validate_reproducibility_rejects_parent_directory_input_path(tmp_path):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    data_file = repo_root / "input.csv"
    data_file.write_text("id\n1\n", encoding="utf-8")
    manifest = input_manifest_for(data_file, validator)
    manifest["inputs"][0]["path"] = "../input.csv"
    manifest_path = repo_root / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    validator.validate_input_manifest(repo_root, manifest_path, errors)

    assert "input 0 path must stay within the repository: ../input.csv" in errors


def test_validate_reproducibility_rejects_absolute_config_path(tmp_path):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    write_config(repo_root)
    manifest = output_manifest_for(repo_root, validator)
    manifest["config_path"] = str(repo_root / "configs/smoke_run.yaml")
    output_path = repo_root / "output_manifest.json"
    output_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    validator.validate_output_manifest(repo_root, output_path, errors)

    assert any(error.startswith("output config_path must be repo-relative, not absolute:") for error in errors)


def test_main_rejects_parent_directory_input_manifest_arg(tmp_path, monkeypatch, capsys):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_reproducibility.py",
            "--repo-root",
            str(repo_root),
            "--input-manifest",
            "../outside_input_manifest.json",
            "--output-manifest",
            "output_manifest.json",
        ],
    )

    assert validator.main() == 1
    captured = capsys.readouterr()

    assert "--input-manifest must stay within the repository: ../outside_input_manifest.json" in captured.out


def test_main_rejects_absolute_output_manifest_arg(tmp_path, monkeypatch, capsys):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside_output = tmp_path / "outside_output_manifest.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_reproducibility.py",
            "--repo-root",
            str(repo_root),
            "--input-manifest",
            "data/input_manifest.json",
            "--output-manifest",
            str(outside_output),
        ],
    )

    assert validator.main() == 1
    captured = capsys.readouterr()

    assert "--output-manifest must be repo-relative, not absolute:" in captured.out
