import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


def load_builder():
    module_path = Path.cwd() / "tools/build_input_manifest.py"
    spec = importlib.util.spec_from_file_location("build_input_manifest", module_path)
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


def test_provenance_registry_marks_known_inputs_complete(tmp_path):
    builder = load_builder()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    data_dir = repo_root / "data"
    data_dir.mkdir()
    input_file = repo_root / "Completeness_783.csv"
    input_file.write_text("id\n1\n", encoding="utf-8")
    registry = {
        "inputs": {
            "Completeness_783.csv": {
                "dataset_name": "FlyWire completeness",
                "release_or_materialization": "783",
                "canonical_url_or_doi": "https://codex.flywire.ai/",
                "citation": "Dorkenwald et al., 2024",
                "license_or_terms": "CC BY-NC 4.0",
                "access_date": "2026-06-10",
                "redistribution_status": "repository_tracked_under_upstream_license",
                "schema_notes": "CSV completeness table",
                "row_count": 1,
                "preprocessing_notes": "fixture",
            }
        }
    }
    registry_path = data_dir / "input_provenance_registry.yaml"
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    record = builder.build_record(input_file, repo_root, builder.load_provenance_registry(registry_path))

    assert record["validation_status"] == builder.PROVENANCE_COMPLETE_STATUS
    assert record["provenance"]["dataset_name"] == "FlyWire completeness"
    assert record["provenance"]["row_count"] == 1


def test_require_provenance_rejects_missing_registry_fields(tmp_path):
    builder = load_builder()
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    input_file = repo_root / "input.csv"
    input_file.write_text("id\n1\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "generated_at_utc": "2026-07-10T00:00:00+00:00",
        "input_count": 1,
        "inputs": [
            builder.build_record(input_file, repo_root, {}),
        ],
    }
    manifest_path = repo_root / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    validator.validate_input_manifest(repo_root, manifest_path, errors, require_provenance=True)

    assert any("provenance field" in error for error in errors)
    assert any("validation_status must be 'provenance_complete'" in error for error in errors)


def test_require_provenance_rejects_malformed_access_date_and_url(tmp_path):
    builder = load_builder()
    validator = load_validator()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    input_file = repo_root / "input.csv"
    input_file.write_text("id\n1\n", encoding="utf-8")
    record = builder.build_record(
        input_file,
        repo_root,
        {
            "input.csv": {
                "dataset_name": "FlyWire completeness",
                "release_or_materialization": "783",
                "canonical_url_or_doi": "not-a-url",
                "citation": "Dorkenwald et al., 2024",
                "license_or_terms": "CC BY-NC 4.0",
                "access_date": "June 10 2026",
                "redistribution_status": "repository_tracked_under_upstream_license",
                "schema_notes": "CSV completeness table",
                "row_count": 1,
                "preprocessing_notes": "fixture",
            }
        },
    )
    record["validation_status"] = builder.PROVENANCE_COMPLETE_STATUS
    manifest = {
        "schema_version": "0.1",
        "generated_at_utc": "2026-07-10T00:00:00+00:00",
        "input_count": 1,
        "inputs": [record],
    }
    manifest_path = repo_root / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors: list[str] = []
    validator.validate_input_manifest(repo_root, manifest_path, errors, require_provenance=True)

    assert any("access_date must be ISO-8601" in error for error in errors)
    assert any("canonical_url_or_doi must be an http(s) URL or doi: URI" in error for error in errors)


def test_committed_input_manifest_passes_claim_ready_provenance():
    repo_root = Path.cwd()
    manifest_path = repo_root / "data/input_manifest.json"
    if not manifest_path.exists():
        return

    validator = load_validator()
    errors: list[str] = []
    manifest = validator.validate_input_manifest(repo_root, manifest_path, errors, require_provenance=True)

    assert manifest is not None
    assert errors == [], errors
    for record in manifest["inputs"]:
        assert record["validation_status"] == validator.PROVENANCE_COMPLETE_STATUS
        assert record["provenance"]["canonical_url_or_doi"].startswith("https://")


def test_build_input_manifest_applies_registry_in_main(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    data_dir = repo_root / "data"
    data_dir.mkdir()
    input_file = repo_root / "Completeness_783.csv"
    input_file.write_text("id\n1\n", encoding="utf-8")
    registry = {
        "inputs": {
            "Completeness_783.csv": {
                "dataset_name": "FlyWire completeness",
                "release_or_materialization": "783",
                "canonical_url_or_doi": "https://codex.flywire.ai/",
                "citation": "Dorkenwald et al., 2024",
                "license_or_terms": "CC BY-NC 4.0",
                "access_date": "2026-06-10",
                "redistribution_status": "repository_tracked_under_upstream_license",
                "schema_notes": "CSV completeness table",
                "row_count": 1,
                "preprocessing_notes": "fixture",
            }
        }
    }
    (data_dir / "input_provenance_registry.yaml").write_text(yaml.safe_dump(registry), encoding="utf-8")
    output = data_dir / "input_manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "tools/build_input_manifest.py"),
            "--repo-root",
            str(repo_root),
            "--output",
            "data/input_manifest.json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["inputs"][0]["validation_status"] == "provenance_complete"
