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


def manifest_for(tool, repo_root: Path, path: str = "input.csv") -> dict:
    data_file = repo_root / path
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("id\n1\n", encoding="utf-8")
    return {
        "schema_version": "0.1",
        "generated_at_utc": "2026-07-10T00:00:00+00:00",
        "input_count": 1,
        "inputs": [
            {
                "path": path,
                "filename": data_file.name,
                "extension": data_file.suffix,
                "size_bytes": data_file.stat().st_size,
                "sha256": tool.sha256_file(data_file),
                "guessed_role": "unknown_input_like_file",
                "provenance": {field: None for field in tool.REQUIRED_PROVENANCE_FIELDS},
            }
        ],
    }


def validate(tool, repo_root: Path, manifest: dict) -> list[str]:
    manifest_path = repo_root / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    errors: list[str] = []
    tool.validate_input_manifest(repo_root, manifest_path, errors)
    return errors


def test_rejects_filename_and_extension_drift(tmp_path):
    tool = load_validator()
    manifest = manifest_for(tool, tmp_path)
    manifest["inputs"][0]["filename"] = "other.csv"
    manifest["inputs"][0]["extension"] = ".parquet"

    errors = validate(tool, tmp_path, manifest)

    assert "input 0 filename does not match path: input.csv" in errors
    assert "input 0 extension does not match path: input.csv" in errors


def test_rejects_malformed_sha_and_size_before_disk_comparison(tmp_path):
    tool = load_validator()
    manifest = manifest_for(tool, tmp_path)
    manifest["inputs"][0]["sha256"] = "ABC"
    manifest["inputs"][0]["size_bytes"] = "5"

    errors = validate(tool, tmp_path, manifest)

    assert "input 0 sha256 must be a 64-character lowercase hex digest: input.csv" in errors
    assert "input 0 size_bytes must be a non-negative integer: input.csv" in errors
    assert "sha256 mismatch: input.csv" not in errors
    assert "size mismatch: input.csv" not in errors


def test_rejects_duplicate_literal_paths(tmp_path):
    tool = load_validator()
    manifest = manifest_for(tool, tmp_path)
    manifest["inputs"].append(dict(manifest["inputs"][0]))
    manifest["input_count"] = 2

    errors = validate(tool, tmp_path, manifest)

    assert "input 1 duplicates manifest path from input 0: input.csv" in errors
    assert "input 1 resolves to the same file as input 0: input.csv" in errors


def test_rejects_normalized_aliases_to_same_file(tmp_path):
    tool = load_validator()
    manifest = manifest_for(tool, tmp_path, "data/input.csv")
    alias = dict(manifest["inputs"][0])
    alias["path"] = "data/../data/input.csv"
    manifest["inputs"].append(alias)
    manifest["input_count"] = 2

    errors = validate(tool, tmp_path, manifest)

    assert "input 1 resolves to the same file as input 0: data/../data/input.csv" in errors


def test_accepts_two_distinct_valid_inputs(tmp_path):
    tool = load_validator()
    first = tmp_path / "alpha.csv"
    second = tmp_path / "beta.csv"
    first.write_text("id\n1\n", encoding="utf-8")
    second.write_text("id\n2\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.1",
        "generated_at_utc": "2026-07-10T00:00:00+00:00",
        "input_count": 2,
        "inputs": [
            {
                "path": "alpha.csv",
                "filename": "alpha.csv",
                "extension": ".csv",
                "size_bytes": first.stat().st_size,
                "sha256": tool.sha256_file(first),
                "guessed_role": "unknown_input_like_file",
                "provenance": {field: None for field in tool.REQUIRED_PROVENANCE_FIELDS},
            },
            {
                "path": "beta.csv",
                "filename": "beta.csv",
                "extension": ".csv",
                "size_bytes": second.stat().st_size,
                "sha256": tool.sha256_file(second),
                "guessed_role": "unknown_input_like_file",
                "provenance": {field: None for field in tool.REQUIRED_PROVENANCE_FIELDS},
            },
        ],
    }

    errors = validate(tool, tmp_path, manifest)

    assert errors == []
