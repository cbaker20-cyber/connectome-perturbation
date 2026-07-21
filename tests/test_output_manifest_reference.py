import importlib.util
import json
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


def write_config(repo_root: Path, validator):
    config_dir = repo_root / "configs"
    config_dir.mkdir()
    config_path = config_dir / "smoke_run.yaml"
    config_path.write_text("run_name: smoke\nrandom_seed: 42\n", encoding="utf-8")
    return config_path, validator.sha256_file(config_path)


def output_manifest(repo_root: Path, validator):
    _, config_sha256 = write_config(repo_root, validator)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": AWARE_TIMESTAMP,
        "status": "metadata_only_smoke",
        "command": "python tools/write_output_manifest.py",
        "repo_commit": None,
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": config_sha256,
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": False,
        "input_checksums": [],
        "claim_status": "not_interpretable_as_neuroscience",
    }


def test_output_manifest_rejects_absolute_input_manifest_path(tmp_path):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest = output_manifest(repo_root, validator)
    manifest["input_manifest_path"] = str(repo_root / "data/input_manifest.json")
    output_path = repo_root / "output_manifest.json"
    output_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    validator.validate_output_manifest(repo_root, output_path, errors)

    assert any(error.startswith("output input_manifest_path must be repo-relative, not absolute:") for error in errors)


def test_output_manifest_rejects_mismatched_validated_input_manifest_path(tmp_path):
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest = output_manifest(repo_root, validator)
    output_path = repo_root / "output_manifest.json"
    output_path.write_text(json.dumps(manifest), encoding="utf-8")

    alternate_manifest_path = repo_root / "other/input_manifest.json"
    errors = []
    validator.validate_output_manifest(
        repo_root,
        output_path,
        errors,
        input_manifest_path=alternate_manifest_path,
    )

    assert "output input_manifest_path does not match validated input manifest path" in errors
