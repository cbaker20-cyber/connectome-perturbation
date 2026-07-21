"""Unit tests for surrogate vs CEO-007-shaped ground-truth correlation harness."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from connectome_analysis.graph_surrogates import write_surrogate_correlations_csv
from connectome_analysis.validate_surrogates import (
    CLAIM_STATUS,
    compute_surrogate_vs_ground_truth_rows,
    extract_condition_motor_deltas,
    load_surrogate_metrics,
    motor_delta_hz,
    pearson_r,
    per_neuron_firing_rates,
    write_surrogate_vs_ground_truth_csv,
    write_synthetic_sugar_ground_truth,
)


def test_pearson_r_perfect_and_inverse():
    assert pearson_r([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)
    assert pearson_r([1.0, 2.0, 3.0], [6.0, 4.0, 2.0]) == pytest.approx(-1.0)


def test_pearson_r_rejects_short_or_nonfinite():
    with pytest.raises(ValueError, match="length >= 2"):
        pearson_r([1.0], [1.0])
    with pytest.raises(ValueError, match="finite"):
        pearson_r([1.0, np.nan], [1.0, 2.0])


def test_per_neuron_firing_rates_and_motor_delta(tmp_path: Path):
    baseline = pd.DataFrame(
        {
            "t": [0.1, 0.2, 0.3, 0.4],
            "trial": [0, 0, 1, 1],
            "flywire_id": [3, 4, 3, 4],
            "exp_name": ["baseline_sugar"] * 4,
        }
    )
    # Trial 0+1: neuron 3 → 1 spike/trial = 1 Hz; neuron 4 → 1 Hz.
    # Perturb: neuron 3 silent; neuron 4 keeps 1 spike/trial.
    perturb = pd.DataFrame(
        {
            "t": [0.1, 0.2],
            "trial": [0, 1],
            "flywire_id": [4, 4],
            "exp_name": ["perturb_x"] * 2,
        }
    )
    rates = per_neuron_firing_rates(baseline, t_run=1.0)
    assert rates.loc[3] == pytest.approx(1.0)
    assert rates.loc[4] == pytest.approx(1.0)

    delta = motor_delta_hz(baseline, perturb, motor_ids=[3, 4], t_run=1.0)
    assert delta.loc[3] == pytest.approx(-1.0)
    assert delta.loc[4] == pytest.approx(0.0)


def test_load_surrogate_metrics_from_repo_csv(tmp_path: Path):
    (tmp_path / "README.md").write_text("fixture repo\n", encoding="utf-8")
    (tmp_path / "results").mkdir(parents=True, exist_ok=True)
    csv_path = write_surrogate_correlations_csv(
        "results/surrogate_correlations.csv",
        repo_root=tmp_path,
    )
    assert csv_path.is_file()
    metrics = load_surrogate_metrics("results/surrogate_correlations.csv", repo_root=tmp_path)
    assert len(metrics["modal_controllability"]) >= 2
    assert len(metrics["path_attenuation_ratio"]) >= 2


def test_synthetic_ground_truth_correlates_with_surrogates(tmp_path: Path):
    # Materialize surrogate CSV and CEO-007-shaped Parquets under a temp repo root.
    (tmp_path / "results").mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text("fixture repo\n", encoding="utf-8")
    surrogate_csv = write_surrogate_correlations_csv(
        "results/surrogate_correlations.csv",
        repo_root=tmp_path,
    )
    gt_dir = write_synthetic_sugar_ground_truth(
        "results/sugar_ground_truth",
        repo_root=tmp_path,
        n_trials=5,
        t_run=1.0,
    )
    assert (gt_dir / "baseline_sugar.parquet").is_file()
    assert list(gt_dir.glob("perturb_*.parquet"))

    metrics = load_surrogate_metrics("results/surrogate_correlations.csv", repo_root=tmp_path)
    assert "1" in metrics["modal_controllability"] or len(metrics["modal_controllability"]) >= 2
    assert len(metrics["path_attenuation_ratio"]) >= 2

    deltas = extract_condition_motor_deltas(
        "results/sugar_ground_truth",
        motor_ids=[3, 4],
        t_run=1.0,
        repo_root=tmp_path,
    )
    assert not deltas.empty
    assert set(deltas.columns) >= {
        "condition",
        "group",
        "motor_delta_hz_sum",
        "motor_drop_hz_sum",
    }

    rows = compute_surrogate_vs_ground_truth_rows(metrics, deltas)
    by_name = {r["comparison"]: r for r in rows if r["comparison"] != "ground_truth_condition"}

    path_row = by_name["path_attenuation_vs_motor_drop"]
    assert path_row["n_pairs"] >= 2
    assert path_row["spearman_rs"] == pytest.approx(1.0, abs=1e-9)
    assert path_row["pearson_r"] == pytest.approx(1.0, abs=1e-9)
    assert path_row["claim_status"] == CLAIM_STATUS

    modal_row = by_name["modal_controllability_vs_motor_drop"]
    assert modal_row["n_pairs"] >= 2
    # Higher |c_i| → larger motor drop by construction of the synthetic bundle.
    assert modal_row["spearman_rs"] == pytest.approx(1.0, abs=1e-9)
    assert modal_row["claim_status"] == CLAIM_STATUS

    out = write_surrogate_vs_ground_truth_csv(
        "results/surrogate_vs_ground_truth.csv",
        surrogate_csv="results/surrogate_correlations.csv",
        ground_truth_dir="results/sugar_ground_truth",
        repo_root=tmp_path,
        ensure_synthetic_ground_truth=False,
    )
    assert out.is_file()
    assert surrogate_csv.is_file()
    with out.open(encoding="utf-8", newline="") as handle:
        exported = list(csv.DictReader(handle))
    assert any(r["comparison"] == "path_attenuation_vs_motor_drop" for r in exported)
    assert all(r["claim_status"] == CLAIM_STATUS for r in exported)


def test_repo_export_writes_summary_csv():
    out = write_surrogate_vs_ground_truth_csv(
        "results/surrogate_vs_ground_truth.csv",
        ensure_synthetic_ground_truth=True,
    )
    assert out.name == "surrogate_vs_ground_truth.csv"
    assert out.is_file()
    with out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {"comparison", "spearman_rs", "pearson_r", "claim_status"} <= set(rows[0])
    corr_rows = [r for r in rows if r["comparison"].endswith("_motor_drop") or "per_motor" in r["comparison"]]
    assert corr_rows
    for row in corr_rows:
        if int(row["n_pairs"]) >= 2:
            assert row["spearman_rs"] != ""
            assert row["pearson_r"] != ""
