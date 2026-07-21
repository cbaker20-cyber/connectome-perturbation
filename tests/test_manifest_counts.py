import importlib.util
import json
from pathlib import Path


def load_validator():
    module_path = Path.cwd() / "tools" / "validate_reproducibility.py"
    spec = importlib.util.spec_from_file_location("validate_reproducibility", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def input_record(tool, data_file: Path) -> dict:
    return {
        "path": data_file.name,
        "filename": data_file.name,
        "extension": data_file.suffix,
        "size_bytes": data_file.stat().st_size,
        "sha256": tool.sha256_file(data_file),
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


def test_input_manifest_rejects_input_count_mismatch(tmp_path):
    tool = load_validator()
    data_file = tmp_path / "input.csv"
    data_file.write_text("id\n1\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "generated_at_utc": "2026-07-10T00:00:00+00:00",
        "input_count": 2,
        "inputs": [input_record(tool, data_file)],
    }
    manifest_path = tmp_path / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    tool.validate_input_manifest(tmp_path, manifest_path, errors)

    assert "input_count does not match inputs length" in errors


def test_output_manifest_rejects_count_drift_from_validated_inputs(tmp_path):
    tool = load_validator()
    data_file = tmp_path / "input.csv"
    data_file.write_text("id\n1\n", encoding="utf-8")
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_path = config_dir / "smoke_run.yaml"
    config_path.write_text("run_name: smoke\n", encoding="utf-8")

    input_manifest = {
        "schema_version": "0.1",
        "generated_at_utc": "2026-07-10T00:00:00+00:00",
        "input_count": 1,
        "inputs": [input_record(tool, data_file)],
    }
    output_manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-10T00:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "python tools/write_output_manifest.py",
        "repo_commit": None,
        "config_path": "configs/smoke_run.yaml",
        "config_sha256": tool.sha256_file(config_path),
        "input_manifest_path": "input_manifest.json",
        "input_manifest_present": True,
        "input_count": 2,
        "input_checksums": [
            {
                "path": data_file.name,
                "sha256": input_manifest["inputs"][0]["sha256"],
                "size_bytes": data_file.stat().st_size,
            }
        ],
        "claim_status": "not_interpretable_as_neuroscience",
    }
    output_path = tmp_path / "output_manifest.json"
    output_path.write_text(json.dumps(output_manifest), encoding="utf-8")

    errors = []
    tool.validate_output_manifest(tmp_path, output_path, errors, input_manifest=input_manifest)

    assert "output input_count does not match validated input manifest" in errors
