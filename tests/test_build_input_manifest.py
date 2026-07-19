import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def load_builder():
    module_path = Path.cwd() / "tools" / "build_input_manifest.py"
    spec = importlib.util.spec_from_file_location("build_input_manifest", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_validator():
    module_path = Path.cwd() / "tools" / "validate_reproducibility.py"
    spec = importlib.util.spec_from_file_location("validate_reproducibility", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_iter_input_like_files_excludes_results_and_registry_ledgers(tmp_path):
    builder = load_builder()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "results").mkdir()
    (repo_root / "2023_03_23_connectivity_630_final.parquet").write_bytes(b"parquet")
    (repo_root / "03_EXPERIMENT_REGISTRY.csv").write_text("id\n1\n", encoding="utf-8")
    (repo_root / "results" / "ignored.csv").write_text("x\n", encoding="utf-8")

    paths = builder.iter_input_like_files(repo_root, builder.DEFAULT_PATTERNS)

    assert [path.name for path in paths] == ["2023_03_23_connectivity_630_final.parquet"]


def test_main_writes_portable_repo_root_and_connectome_inputs_only(tmp_path):
    builder = load_builder()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "Completeness_783.csv").write_text("id\n1\n", encoding="utf-8")
    (repo_root / "04_RESULTS_LEDGER.csv").write_text("id\n1\n", encoding="utf-8")
    output = repo_root / "data" / "input_manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "tools" / "build_input_manifest.py"),
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
    assert manifest["repo_root"] == "."
    assert manifest["input_count"] == 1
    assert [record["path"] for record in manifest["inputs"]] == ["Completeness_783.csv"]
    assert manifest["inputs"][0]["validation_status"] == "checksum_recorded_provenance_missing"


def test_committed_input_manifest_passes_metadata_validation():
    repo_root = Path.cwd()
    manifest_path = repo_root / "data" / "input_manifest.json"
    if not manifest_path.exists():
        return

    validator = load_validator()
    errors: list[str] = []
    manifest = validator.validate_input_manifest(repo_root, manifest_path, errors)

    assert manifest is not None
    assert errors == []
    assert manifest["input_count"] == 5
    paths = {record["path"] for record in manifest["inputs"]}
    assert paths == {
        "2023_03_23_completeness_630_final.csv",
        "2023_03_23_connectivity_630_final.parquet",
        "Completeness_783.csv",
        "Connectivity_783.parquet",
        "flywire_annotations.tsv",
    }
    for record in manifest["inputs"]:
        assert record["validation_status"] == "provenance_complete"
        assert record["provenance"]["redistribution_status"] == "repository_tracked_under_upstream_license"
