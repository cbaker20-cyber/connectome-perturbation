import importlib.util
import json
from pathlib import Path

import pytest
import yaml


WORKSPACE = Path.cwd()


def load_resolver():
    module_path = WORKSPACE / "tools/path_resolver.py"
    spec = importlib.util.spec_from_file_location("path_resolver", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture repository\n", encoding="utf-8")
    return repo_root


def write_manifest(repo_root: Path, records: list[dict]) -> None:
    manifest_path = repo_root / "data/input_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"inputs": records}), encoding="utf-8")


def test_materialization_policy_documents_smoke_target():
    text = (WORKSPACE / "docs/materialization-policy.md").read_text(encoding="utf-8")
    assert "Canonical smoke target: materialization 630" in text
    assert "2023_03_23_connectivity_630_final.parquet" in text
    assert "Connectivity_783.parquet" in text
    assert "Ambiguity is rejected" in text


def test_smoke_config_records_materialization_630():
    config = yaml.safe_load((WORKSPACE / "configs/smoke_run.yaml").read_text(encoding="utf-8"))
    assert config["selected_materialization"] == "630"
    assert config["selected_inputs"]["connectivity"] == "2023_03_23_connectivity_630_final.parquet"
    assert config["selected_inputs"]["completeness"] == "2023_03_23_completeness_630_final.csv"
    assert config["selected_inputs"]["annotations"] == "flywire_annotations.tsv"


def test_resolve_materialization_inputs_returns_630_bundle(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    completeness = repo_root / "2023_03_23_completeness_630_final.csv"
    connectivity = repo_root / "2023_03_23_connectivity_630_final.parquet"
    annotations = repo_root / "flywire_annotations.tsv"
    completeness.write_text("id\n1\n", encoding="utf-8")
    connectivity.write_bytes(b"parquet")
    annotations.write_text("root_id\n1\n", encoding="utf-8")
    write_manifest(
        repo_root,
        [
            {
                "path": completeness.name,
                "filename": completeness.name,
                "guessed_role": "completeness_table",
                "guessed_materialization": "630",
            },
            {
                "path": connectivity.name,
                "filename": connectivity.name,
                "guessed_role": "connectivity_table",
                "guessed_materialization": "630",
            },
            {
                "path": annotations.name,
                "filename": annotations.name,
                "guessed_role": "annotation_table",
            },
        ],
    )

    bundle = resolver.resolve_materialization_inputs("630", repo_root=repo_root)

    assert bundle["completeness"] == completeness.resolve()
    assert bundle["connectivity"] == connectivity.resolve()
    assert bundle["annotations"] == annotations.resolve()


def test_resolve_materialization_inputs_supports_783(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    completeness = repo_root / "Completeness_783.csv"
    connectivity = repo_root / "Connectivity_783.parquet"
    completeness.write_text("id\n1\n", encoding="utf-8")
    connectivity.write_bytes(b"parquet")
    write_manifest(
        repo_root,
        [
            {
                "path": completeness.name,
                "filename": completeness.name,
                "guessed_role": "completeness_table",
                "guessed_materialization": "783",
            },
            {
                "path": connectivity.name,
                "filename": connectivity.name,
                "guessed_role": "connectivity_table",
                "guessed_materialization": "783",
            },
        ],
    )

    bundle = resolver.resolve_materialization_inputs("783", repo_root=repo_root, include_annotations=False)

    assert bundle["completeness"] == completeness.resolve()
    assert bundle["connectivity"] == connectivity.resolve()
    assert "annotations" not in bundle


def test_bare_materialization_identifier_is_ambiguous(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    write_manifest(
        repo_root,
        [
            {
                "path": "2023_03_23_completeness_630_final.csv",
                "filename": "2023_03_23_completeness_630_final.csv",
                "guessed_role": "completeness_table",
                "guessed_materialization": "630",
            },
            {
                "path": "2023_03_23_connectivity_630_final.parquet",
                "filename": "2023_03_23_connectivity_630_final.parquet",
                "guessed_role": "connectivity_table",
                "guessed_materialization": "630",
            },
        ],
    )

    with pytest.raises(ValueError, match="Ambiguous input identifier '630'"):
        resolver.resolve_input("630", repo_root=repo_root)


def test_committed_input_manifest_lists_both_materializations():
    manifest = json.loads((WORKSPACE / "data/input_manifest.json").read_text(encoding="utf-8"))
    materializations = {
        record.get("guessed_materialization")
        for record in manifest["inputs"]
        if record.get("guessed_materialization") is not None
    }
    assert materializations == {"630", "783"}
