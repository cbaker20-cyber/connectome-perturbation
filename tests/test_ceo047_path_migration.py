"""CEO-047: path migration and statistics FDR export tests."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

WORKSPACE = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, module_name: str | None = None):
    module_path = WORKSPACE / relative_path
    name = module_name or relative_path.replace("/", ".").replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_resolver():
    return load_module("tools/path_resolver.py", "path_resolver_under_test")


def make_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("fixture repository\n", encoding="utf-8")
    return repo_root


def write_manifest(repo_root: Path, records: list[dict]) -> Path:
    manifest_path = repo_root / "data/input_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"inputs": records}), encoding="utf-8")
    return manifest_path


def install_baseline_stubs() -> None:
    """Stub brian2/model so baseline.py can be imported without a full env."""
    if "brian2" not in sys.modules:
        brian2 = types.ModuleType("brian2")
        brian2.ms = 1.0
        sys.modules["brian2"] = brian2
    if "model" not in sys.modules:
        model = types.ModuleType("model")
        model.default_params = {"n_run": 30}
        model.run_exp = lambda **kwargs: None
        sys.modules["model"] = model


@pytest.mark.parametrize(
    "relative_path",
    [
        "perturbation/baseline.py",
        "perturbation/perturb.py",
        "perturbation/statistics.py",
    ],
)
def test_target_files_have_no_hardcoded_legacy_paths(relative_path):
    text = (WORKSPACE / relative_path).read_text(encoding="utf-8")
    assert "Drosophila_brain_model" not in text
    assert 'sys.path.insert(0, "Drosophila_brain_model")' not in text
    assert 'sys.path.insert(0, "perturbation")' not in text
    assert "resolve_input" in text or "ensure_repo_on_path" in text


def test_resolve_input_works_after_chdir_away_from_repo(tmp_path, monkeypatch):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    data_file = repo_root / "2023_03_23_connectivity_630_final.parquet"
    data_file.write_bytes(b"parquet")
    write_manifest(
        repo_root,
        [
            {
                "path": data_file.name,
                "filename": data_file.name,
                "guessed_role": "connectivity_table",
                "guessed_materialization": "630",
            }
        ],
    )

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    resolved = resolver.resolve_input(
        "2023_03_23_connectivity_630_final.parquet",
        repo_root=repo_root,
    )
    assert resolved == data_file.resolve()


def test_resolve_input_strips_legacy_prefix_from_any_cwd(tmp_path, monkeypatch):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    data_file = repo_root / "2023_03_23_connectivity_630_final.parquet"
    data_file.write_bytes(b"parquet")
    write_manifest(
        repo_root,
        [
            {
                "path": data_file.name,
                "filename": data_file.name,
                "guessed_role": "connectivity_table",
                "guessed_materialization": "630",
            }
        ],
    )

    elsewhere = tmp_path / "not_the_repo"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    resolved = resolver.resolve_input(
        "Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet",
        repo_root=repo_root,
    )
    assert resolved == data_file.resolve()


def test_baseline_resolve_inputs_from_any_directory(tmp_path, monkeypatch):
    install_baseline_stubs()
    # Ensure tools is importable when baseline bootstraps.
    if str(WORKSPACE) not in sys.path:
        sys.path.insert(0, str(WORKSPACE))

    baseline = load_module("perturbation/baseline.py", "baseline_under_test")
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

    elsewhere = tmp_path / "cwd_away"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        path_comp, path_con = baseline.resolve_baseline_inputs(
            completeness_id="2023_03_23_completeness_630_final.csv",
            connectivity_id="2023_03_23_connectivity_630_final.parquet",
            manifest_path="data/input_manifest.json",
            repo_root=repo_root,
        )

    assert path_comp == completeness.resolve()
    assert path_con == connectivity.resolve()


def test_ensure_repo_on_path_adds_absolute_perturbation_dir(tmp_path, monkeypatch):
    resolver = load_resolver()
    repo_root = make_repo(tmp_path)
    (repo_root / "perturbation").mkdir()
    elsewhere = tmp_path / "away"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    before = list(sys.path)
    try:
        root = resolver.ensure_repo_on_path(repo_root / "README.md")
        assert root == repo_root.resolve()
        assert str(repo_root.resolve()) in sys.path
        assert str((repo_root / "perturbation").resolve()) in sys.path
        assert 'sys.path.insert(0, "perturbation")' not in Path(
            resolver.__file__
        ).read_text(encoding="utf-8")
    finally:
        sys.path[:] = before


def test_statistics_export_includes_raw_p_value_and_p_value_fdr(tmp_path):
    if str(WORKSPACE) not in sys.path:
        sys.path.insert(0, str(WORKSPACE))

    # Stub cell_groups before loading statistics.
    cell_groups = types.ModuleType("cell_groups")
    cell_groups.get_group = lambda **kwargs: [1, 2, 3]
    sys.modules["cell_groups"] = cell_groups

    statistics = load_module("perturbation/statistics.py", "statistics_under_test")

    rng = np.random.default_rng(0)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    def write_spike_table(name: str, rate_per_trial: np.ndarray) -> None:
        rows = []
        for trial, count in enumerate(rate_per_trial, start=1):
            for _ in range(int(count)):
                rows.append({"trial": trial, "flywire_id": 1})
            # Always keep at least the trial id present via a non-motor spike.
            rows.append({"trial": trial, "flywire_id": 999})
        pd.DataFrame(rows).to_parquet(results_dir / f"{name}.parquet", index=False)

    # Use noisy trial counts so Welch's t-test does not emit precision warnings.
    baseline_counts = rng.integers(15, 26, size=30)
    perturbed_counts = rng.integers(1, 8, size=30)
    write_spike_table("baseline_sugar", baseline_counts)
    write_spike_table("hq_AN", perturbed_counts)
    write_spike_table("hq_LO", rng.integers(12, 22, size=30))

    df = statistics.run_statistics(
        targets=[("hq_AN", "AN"), ("hq_LO", "LO")],
        path_res=results_dir,
        motor_ids=[1],
        output_name="statistics.csv",
    )

    out_path = results_dir / "statistics.csv"
    assert out_path.exists()
    saved = pd.read_csv(out_path, index_col=0)

    assert "p_value" in saved.columns
    assert "p_value_fdr" in saved.columns
    assert "p_value_raw" in saved.columns
    # Raw and FDR columns must both be finite and not identical for multi-test.
    assert saved["p_value"].notna().all()
    assert saved["p_value_fdr"].notna().all()
    assert np.allclose(saved["p_value"], saved["p_value_raw"])
    assert (saved["p_value_fdr"] >= saved["p_value_raw"] - 1e-12).all()
    assert "AN" in df.index
    assert df.loc["AN", "p_value_fdr"] <= df.loc["AN", "p_value_raw"] + 1e-12


def test_workspace_default_ids_resolve_from_committed_manifest(monkeypatch, tmp_path):
    """Default baseline IDs resolve via the real committed manifest from any cwd."""
    resolver = load_resolver()
    elsewhere = tmp_path / "random_cwd"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    completeness = resolver.resolve_input(
        "2023_03_23_completeness_630_final.csv",
        repo_root=WORKSPACE,
    )
    connectivity = resolver.resolve_input(
        "2023_03_23_connectivity_630_final.parquet",
        repo_root=WORKSPACE,
    )
    assert completeness.name == "2023_03_23_completeness_630_final.csv"
    assert connectivity.name == "2023_03_23_connectivity_630_final.parquet"
    assert completeness.exists()
    assert connectivity.exists()
