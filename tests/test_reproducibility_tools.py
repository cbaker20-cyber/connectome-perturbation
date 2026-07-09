import importlib.util
import json
from pathlib import Path


def load_module(repo_root: Path, relative_path: str):
    module_path = repo_root / relative_path
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_input_manifest_records_checksums_and_roles(tmp_path):
    repo_root = tmp_path
    tool = load_module(Path.cwd(), "tools/build_input_manifest.py")
    data_file = repo_root / "connections_630_connectivity.csv"
    data_file.write_text("source,target,weight\n1,2,3\n", encoding="utf-8")

    record = tool.build_record(data_file, repo_root)

    assert record["path"] == "connections_630_connectivity.csv"
    assert record["filename"] == "connections_630_connectivity.csv"
    assert record["extension"] == ".csv"
    assert record["size_bytes"] == data_file.stat().st_size
    assert record["sha256"] == tool.sha256_file(data_file)
    assert record["guessed_role"] == "connectivity_table"
    assert record["guessed_materialization"] == "630"
    assert record["provenance"]["release_or_materialization"] == "630"
    assert record["validation_status"] == "checksum_recorded_provenance_missing"


def test_path_resolver_resolves_exact_filename_and_rejects_ambiguous_roles(tmp_path):
    tool = load_module(Path.cwd(), "tools/path_resolver.py")
    repo_root = tmp_path
    (repo_root / "README.md").write_text("fixture repo\n", encoding="utf-8")
    data_dir = repo_root / "data"
    data_dir.mkdir()
    file_a = repo_root / "a_connectivity.csv"
    file_b = repo_root / "b_connectivity.csv"
    file_a.write_text("a\n", encoding="utf-8")
    file_b.write_text("b\n", encoding="utf-8")
    manifest = {
        "inputs": [
            {"path": "a_connectivity.csv", "filename": "a_connectivity.csv", "guessed_role": "connectivity_table", "guessed_materialization": "630"},
            {"path": "b_connectivity.csv", "filename": "b_connectivity.csv", "guessed_role": "connectivity_table", "guessed_materialization": "783"},
        ]
    }
    (data_dir / "input_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    assert tool.resolve_input("a_connectivity.csv", repo_root=repo_root) == file_a.resolve()

    try:
        tool.resolve_input("connectivity_table", repo_root=repo_root)
    except ValueError as exc:
        assert "Ambiguous input identifier" in str(exc)
        assert "a_connectivity.csv" in str(exc)
        assert "b_connectivity.csv" in str(exc)
    else:
        raise AssertionError("ambiguous role should raise ValueError")


def test_validate_reproducibility_accepts_metadata_only_manifests(tmp_path):
    tool = load_module(Path.cwd(), "tools/validate_reproducibility.py")
    repo_root = tmp_path
    data_file = repo_root / "input.csv"
    data_file.write_text("id\n1\n", encoding="utf-8")
    input_manifest = {
        "input_count": 1,
        "inputs": [
            {
                "path": "input.csv",
                "filename": "input.csv",
                "extension": ".csv",
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
        ],
    }
    output_manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-09T00:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "python tools/write_output_manifest.py",
        "repo_commit": None,
        "config_path": "configs/smoke_run.yaml",
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": True,
        "input_count": 1,
        "input_checksums": [{"path": "input.csv", "sha256": input_manifest["inputs"][0]["sha256"], "size_bytes": data_file.stat().st_size}],
        "claim_status": "not_interpretable_as_neuroscience",
    }
    (repo_root / "input_manifest.json").write_text(json.dumps(input_manifest), encoding="utf-8")
    (repo_root / "output_manifest.json").write_text(json.dumps(output_manifest), encoding="utf-8")

    errors = []
    validated_input_manifest = tool.validate_input_manifest(repo_root, repo_root / "input_manifest.json", errors)
    tool.validate_output_manifest(repo_root / "output_manifest.json", errors, input_manifest=validated_input_manifest)

    assert errors == []


def test_validate_reproducibility_strict_provenance_rejects_unknown_fields(tmp_path):
    tool = load_module(Path.cwd(), "tools/validate_reproducibility.py")
    repo_root = tmp_path
    data_file = repo_root / "input.csv"
    data_file.write_text("id\n1\n", encoding="utf-8")
    input_manifest = {
        "input_count": 1,
        "inputs": [
            {
                "path": "input.csv",
                "filename": "input.csv",
                "extension": ".csv",
                "size_bytes": data_file.stat().st_size,
                "sha256": tool.sha256_file(data_file),
                "guessed_role": "unknown_input_like_file",
                "provenance": {
                    "dataset_name": "FlyWire",
                    "release_or_materialization": "630",
                    "canonical_url_or_doi": None,
                    "citation": "source-backed citation required",
                    "license_or_terms": "unknown",
                    "access_date": "2026-07-09",
                    "redistribution_status": "unknown",
                    "schema_notes": "source,target,weight",
                    "row_count": 1,
                    "preprocessing_notes": "none",
                },
            }
        ],
    }
    manifest_path = repo_root / "input_manifest.json"
    manifest_path.write_text(json.dumps(input_manifest), encoding="utf-8")

    errors = []
    tool.validate_input_manifest(repo_root, manifest_path, errors, require_provenance=True)

    assert "input 0 provenance field `canonical_url_or_doi` is required for claim-ready validation" in errors
    assert "input 0 provenance field `license_or_terms` is required for claim-ready validation" in errors
    assert "input 0 provenance field `redistribution_status` is required for claim-ready validation" in errors


def test_validate_reproducibility_reports_checksum_mismatch(tmp_path):
    tool = load_module(Path.cwd(), "tools/validate_reproducibility.py")
    repo_root = tmp_path
    data_file = repo_root / "input.csv"
    data_file.write_text("id\n1\n", encoding="utf-8")
    manifest = {
        "input_count": 1,
        "inputs": [
            {
                "path": "input.csv",
                "filename": "input.csv",
                "extension": ".csv",
                "size_bytes": data_file.stat().st_size,
                "sha256": "0" * 64,
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
    manifest_path = repo_root / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    errors = []
    tool.validate_input_manifest(repo_root, manifest_path, errors)

    assert "sha256 mismatch: input.csv" in errors


def test_validate_reproducibility_rejects_stale_output_input_checksums(tmp_path):
    tool = load_module(Path.cwd(), "tools/validate_reproducibility.py")
    repo_root = tmp_path
    data_file = repo_root / "input.csv"
    data_file.write_text("id\n1\n", encoding="utf-8")
    input_manifest = {
        "input_count": 1,
        "inputs": [
            {
                "path": "input.csv",
                "filename": "input.csv",
                "extension": ".csv",
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
        ],
    }
    stale_output_manifest = {
        "schema_version": "0.1",
        "created_at_utc": "2026-07-09T00:00:00+00:00",
        "status": "metadata_only_smoke",
        "command": "python tools/write_output_manifest.py",
        "repo_commit": None,
        "config_path": "configs/smoke_run.yaml",
        "input_manifest_path": "data/input_manifest.json",
        "input_manifest_present": True,
        "input_count": 1,
        "input_checksums": [{"path": "input.csv", "sha256": "0" * 64, "size_bytes": data_file.stat().st_size}],
        "claim_status": "not_interpretable_as_neuroscience",
    }
    (repo_root / "input_manifest.json").write_text(json.dumps(input_manifest), encoding="utf-8")
    (repo_root / "output_manifest.json").write_text(json.dumps(stale_output_manifest), encoding="utf-8")

    errors = []
    validated_input_manifest = tool.validate_input_manifest(repo_root, repo_root / "input_manifest.json", errors)
    tool.validate_output_manifest(repo_root / "output_manifest.json", errors, input_manifest=validated_input_manifest)

    assert "output input_checksums do not match validated input manifest" in errors
