"""Unit tests for connectome_analysis.validate_surrogates (CEO-071B Task A)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from connectome_analysis.validate_surrogates import (
    OUTPUT_COLUMNS,
    dynamic_leverage_residual,
    extract_provenance,
    fit_structural_prediction,
    motor_delta_hz,
    motor_population_rate_hz,
)


def test_output_schema_has_exactly_13_columns():
    assert len(OUTPUT_COLUMNS) == 13
    assert OUTPUT_COLUMNS[0] == "target_class"
    assert "delta_leverage" in OUTPUT_COLUMNS
    assert "commit_sha" in OUTPUT_COLUMNS
    assert "random_seed" in OUTPUT_COLUMNS
    assert "mean_modal_controllability" in OUTPUT_COLUMNS
    assert "path_attenuation_ratio" in OUTPUT_COLUMNS


def test_extract_provenance_truncates_commit_and_reads_seed():
    commit, seed = extract_provenance(
        {"repo_commit": "ab2140c74dd51feb812688d68740a7faf769c968", "random_seed": 42}
    )
    assert commit == "ab2140c"
    assert seed == 42


def test_motor_population_rate_and_delta_hz():
    # Baseline: 2 trials, 2 motor spikes total → rate = 2 / (2 * 1s) = 1.0 Hz
    baseline = pd.DataFrame(
        {
            "trial": [0, 0, 1, 1],
            "flywire_id": [1, 2, 99, 99],
        }
    )
    # Perturbed: 2 trials, 8 motor spikes → rate = 4.0 Hz; delta = +3.0
    perturbed = pd.DataFrame(
        {
            "trial": [0, 0, 0, 0, 1, 1, 1, 1],
            "flywire_id": [1, 1, 2, 2, 1, 1, 2, 2],
        }
    )
    motors = [1, 2]
    assert motor_population_rate_hz(baseline, motors, t_run_s=1.0) == pytest.approx(1.0)
    assert motor_population_rate_hz(perturbed, motors, t_run_s=1.0) == pytest.approx(4.0)
    assert motor_delta_hz(baseline, perturbed, motors, t_run_s=1.0) == pytest.approx(3.0)


def test_dynamic_leverage_residual_definition():
    assert dynamic_leverage_residual(-10.0, -4.0) == pytest.approx(-6.0)
    assert np.isnan(dynamic_leverage_residual(float("nan"), 1.0))


def test_fit_structural_prediction_recovers_linear_signal():
    rng = np.random.default_rng(0)
    modal = rng.normal(size=8)
    eta = rng.normal(size=8)
    # Exact linear generator.
    y = 1.5 + 2.0 * modal - 0.5 * eta
    y_hat = fit_structural_prediction(modal, eta, y)
    np.testing.assert_allclose(y_hat, y, rtol=1e-6, atol=1e-6)
    residuals = [dynamic_leverage_residual(float(a), float(b)) for a, b in zip(y, y_hat)]
    np.testing.assert_allclose(residuals, np.zeros(8), atol=1e-6)


def test_fit_structural_prediction_handles_nan_eta():
    modal = np.array([0.1, 0.2, 0.3, 0.4], dtype=float)
    eta = np.array([0.5, np.nan, 0.7, 0.8], dtype=float)
    delta = np.array([-1.0, -2.0, -3.0, -4.0], dtype=float)
    y_hat = fit_structural_prediction(modal, eta, delta)
    assert y_hat.shape == (4,)
    assert np.isfinite(y_hat).sum() >= 3
