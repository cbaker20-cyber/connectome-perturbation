"""CEO-007 sugar ground-truth plumbing and fast integration tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

WORKSPACE = Path(__file__).resolve().parents[1]


def _load(relative: str, name: str):
    path = WORKSPACE / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_sugar_config_is_30_trial_ground_truth():
    config = yaml.safe_load(
        (WORKSPACE / "configs/sugar_ground_truth_30trial.yaml").read_text(encoding="utf-8")
    )
    assert config["n_run"] == 30
    assert config["t_run_ms"] == 1000
    assert config["random_seed"] == 47
    assert config["selected_materialization"] == "630"
    assert "baseline_sugar" in config["baseline_exp_name"]


@pytest.mark.parametrize(
    "relative_path",
    [
        "perturbation/baseline.py",
        "perturbation/perturb.py",
        "perturbation/statistics.py",
        "tools/run_sugar_ground_truth.py",
    ],
)
def test_ceo007_targets_have_no_hardcoded_data_dir(relative_path):
    text = (WORKSPACE / relative_path).read_text(encoding="utf-8")
    assert "Drosophila_brain_model" not in text
    assert 'sys.path.insert(0, "Drosophila_brain_model")' not in text


def test_zero_spike_trials_retained_in_trial_rates():
    if str(WORKSPACE) not in sys.path:
        sys.path.insert(0, str(WORKSPACE))
    import types

    sys.modules.setdefault(
        "cell_groups",
        types.SimpleNamespace(get_group=lambda **kwargs: [1]),
    )
    statistics = _load("perturbation/statistics.py", "stats_ceo007")
    df = pd.DataFrame(
        {
            "trial": [0, 0, 2, 2],
            "flywire_id": [1, 999, 1, 999],
        }
    )
    rates = statistics.trial_rates(df, neuron_ids=[1], t_run=1.0, trial_ids=[0, 1, 2])
    assert list(rates) == [1.0, 0.0, 1.0]


def test_resolve_motor_ids_uses_path_resolver():
    if str(WORKSPACE) not in sys.path:
        sys.path.insert(0, str(WORKSPACE))
    runner = _load("tools/run_sugar_ground_truth.py", "sugar_runner_ceo007")
    motor_ids = runner.resolve_motor_ids(
        "data/input_manifest.json",
        "2023_03_23_completeness_630_final.csv",
    )
    assert len(motor_ids) > 0
    assert all(isinstance(i, int) for i in motor_ids[:5])


@pytest.mark.brian2
def test_mini_sugar_panel_writes_parquet_and_fdr_stats(tmp_path, monkeypatch):
    pytest.importorskip("brian2")
    if str(WORKSPACE) not in sys.path:
        sys.path.insert(0, str(WORKSPACE))

    # Keep the mini run inside the real repo so large connectome inputs resolve.
    results_dir = WORKSPACE / "results" / "sugar_ground_truth_mini"
    if results_dir.exists():
        for child in results_dir.glob("*"):
            if child.is_file():
                child.unlink()
    results_dir.mkdir(parents=True, exist_ok=True)

    mini_config = {
        "run_name": "sugar_ground_truth_mini",
        "experiment_id": "E010_mini",
        "random_seed": 47,
        "selected_materialization": "630",
        "mode": "brian2_simulation",
        "n_run": 2,
        "t_run_ms": 50,
        "n_proc": 1,
        "codegen_target": "numpy",
        "poisson_rate_hz": 150,
        "completeness_id": "2023_03_23_completeness_630_final.csv",
        "connectivity_id": "2023_03_23_connectivity_630_final.parquet",
        "input_manifest": "data/input_manifest.json",
        "output_manifest": "results/sugar_ground_truth_mini/output_manifest.json",
        "results_dir": "results/sugar_ground_truth_mini",
        "baseline_exp_name": "baseline_sugar",
        "perturbation_group_size": 21,
        "control_seed": 47,
        "statistics_output": "statistics.csv",
        "claim_status": "simulation_bound_pending_independent_validation",
        "notes": ["mini integration test"],
    }
    config_path = WORKSPACE / "configs" / "sugar_ground_truth_mini.yaml"
    config_path.write_text(yaml.safe_dump(mini_config), encoding="utf-8")

    runner = _load("tools/run_sugar_ground_truth.py", "sugar_runner_ceo007_mini")
    rc = runner.main(["--config", "configs/sugar_ground_truth_mini.yaml", "--force"])
    assert rc == 0

    baseline = results_dir / "baseline_sugar.parquet"
    assert baseline.exists()
    spikes = pd.read_parquet(baseline)
    assert {"trial", "flywire_id", "t", "exp_name"} <= set(spikes.columns)
    assert spikes["trial"].nunique() == 2

    stats_path = results_dir / "statistics.csv"
    assert stats_path.exists()
    stats = pd.read_csv(stats_path, index_col=0)
    assert "p_value" in stats.columns
    assert "p_value_fdr" in stats.columns
    assert stats["p_value"].notna().any()

    manifest = json.loads(
        (results_dir / "output_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["run_config"]["random_seed"] == 47
    assert manifest["run_config"]["n_run"] == 2
    assert manifest["input_checksums"]
    assert any(o["path"].endswith("baseline_sugar.parquet") for o in manifest["outputs"])
