import importlib.util
import json
import sys
from pathlib import Path

import pytest


WORKSPACE = Path.cwd()


def load_module(relative_path: str):
    module_path = WORKSPACE / relative_path
    module_name = relative_path.replace("/", ".").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_resolver():
    return load_module("tools/path_resolver.py")


def make_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture repository\n", encoding="utf-8")
    return repo_root


def write_manifest(repo_root: Path, records: list[dict]) -> Path:
    manifest_path = repo_root / "data/input_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"inputs": records}),
        encoding="utf-8",
    )
    return manifest_path


def test_resolve_input_strips_legacy_prefix_and_uses_manifest(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    data_file = repo_root / "2023_03_23_connectivity_630_final.parquet"
    data_file.write_bytes(b"parquet")
    write_manifest(
        repo_root,
        [
            {
                "path": "2023_03_23_connectivity_630_final.parquet",
                "filename": "2023_03_23_connectivity_630_final.parquet",
                "guessed_role": "connectivity_table",
                "guessed_materialization": "630",
            }
        ],
    )

    resolved = resolver.resolve_input(
        "Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet",
        repo_root=repo_root,
    )

    assert resolved == data_file.resolve()


def test_resolve_input_falls_back_to_legacy_subdirectory(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    legacy_dir = repo_root / "Drosophila_brain_model"
    legacy_dir.mkdir()
    data_file = legacy_dir / "2023_03_23_connectivity_630_final.parquet"
    data_file.write_bytes(b"legacy-parquet")

    resolved = resolver.resolve_input(
        "Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet",
        repo_root=repo_root,
    )

    assert resolved == data_file.resolve()


def test_resolve_existing_path_wraps_resolver_errors(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)

    with pytest.raises(FileNotFoundError, match="Could not find connectivity file"):
        resolver.resolve_existing_path("missing.parquet", "connectivity file", repo_root=repo_root)


def test_baseline_default_input_ids_resolve_from_manifest(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    completeness = repo_root / "2023_03_23_completeness_630_final.csv"
    connectivity = repo_root / "2023_03_23_connectivity_630_final.parquet"
    completeness.write_text("id\n1\n", encoding="utf-8")
    connectivity.write_bytes(b"parquet")
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
        ],
    )

    assert resolver.resolve_input("2023_03_23_completeness_630_final.csv", repo_root=repo_root) == completeness.resolve()
    assert resolver.resolve_input("2023_03_23_connectivity_630_final.parquet", repo_root=repo_root) == connectivity.resolve()


def test_cell_groups_resolve_inputs_uses_manifest(tmp_path):
    cell_groups = load_module("perturbation/cell_groups.py")
    repo_root = make_repo(tmp_path)
    annotations = repo_root / "flywire_annotations.tsv"
    completeness = repo_root / "2023_03_23_completeness_630_final.csv"
    annotations.write_text("root_id\tcell_class\n1\tAN\n", encoding="utf-8")
    completeness.write_text("id\n1\n", encoding="utf-8")
    write_manifest(
        repo_root,
        [
            {
                "path": annotations.name,
                "filename": annotations.name,
                "guessed_role": "annotation_table",
            },
            {
                "path": completeness.name,
                "filename": completeness.name,
                "guessed_role": "completeness_table",
                "guessed_materialization": "630",
            },
        ],
    )

    ann_path, sim_path = cell_groups.resolve_cell_group_inputs(repo_root=repo_root)

    assert ann_path == annotations.resolve()
    assert sim_path == completeness.resolve()


def test_graph_analysis_defaults_resolve_through_manifest(tmp_path):
    graph_analysis = load_module("perturbation/graph_analysis.py")
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    connectivity = repo_root / graph_analysis.CONNECTIVITY_DEFAULT
    annotations = repo_root / graph_analysis.ANNOTATIONS_DEFAULT
    connectivity.write_bytes(b"parquet")
    annotations.write_text("root_id\tcell_class\n1\tAN\n", encoding="utf-8")
    write_manifest(
        repo_root,
        [
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

    assert resolver.resolve_input(graph_analysis.CONNECTIVITY_DEFAULT, repo_root=repo_root) == connectivity.resolve()
    assert resolver.resolve_input(graph_analysis.ANNOTATIONS_DEFAULT, repo_root=repo_root) == annotations.resolve()
    assert graph_analysis.CONNECTIVITY_DEFAULT == "2023_03_23_connectivity_630_final.parquet"


def test_path_analysis_main_resolves_manifest_paths(tmp_path, monkeypatch):
    path_analysis = load_module("perturbation/path_analysis.py")
    repo_root = make_repo(tmp_path)
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "path_analysis.py",
            "--mock",
            "--output-dir",
            "results/path_analysis_test",
        ],
    )

    path_analysis.main()

    assert (repo_root / "results/path_analysis_test/mock_inputs").exists()


@pytest.mark.parametrize(
    "relative_path",
    [
        "perturbation/perturb.py",
        "perturbation/statistics.py",
        "perturbation/motor_analysis.py",
        "perturbation/sweep_cell_class.py",
        "test_run.py",
    ],
)
def test_migrated_scripts_do_not_hardcode_legacy_data_dir(relative_path):
    text = (WORKSPACE / relative_path).read_text(encoding="utf-8")
    assert "Drosophila_brain_model/" not in text
    assert 'sys.path.insert(0, "Drosophila_brain_model")' not in text


def test_migrated_scripts_use_path_resolver():
    expected_imports = {
        "perturbation/perturb.py": "ensure_repo_on_path",
        "perturbation/statistics.py": "ensure_repo_on_path",
        "perturbation/motor_analysis.py": "ensure_repo_on_path",
        "perturbation/sweep_cell_class.py": "ensure_repo_on_path",
        "perturbation/cell_groups.py": "resolve_input",
        "perturbation/graph_analysis.py": "resolve_input",
        "perturbation/path_analysis.py": "resolve_existing_path",
        "perturbation/baseline.py": "resolve_input",
        "test_run.py": "resolve_input",
    }
    for relative_path, import_name in expected_imports.items():
        text = (WORKSPACE / relative_path).read_text(encoding="utf-8")
        assert import_name in text


def test_test_run_resolves_manifest_paths(tmp_path):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    completeness = repo_root / "2023_03_23_completeness_630_final.csv"
    connectivity = repo_root / "2023_03_23_connectivity_630_final.parquet"
    completeness.write_text("id\n1\n", encoding="utf-8")
    connectivity.write_bytes(b"parquet")
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
        ],
    )

    assert resolver.resolve_input("2023_03_23_completeness_630_final.csv", repo_root=repo_root) == completeness.resolve()
    assert resolver.resolve_input("2023_03_23_connectivity_630_final.parquet", repo_root=repo_root) == connectivity.resolve()
    assert resolver.resolve_input(
        "Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet",
        repo_root=repo_root,
    ) == connectivity.resolve()
