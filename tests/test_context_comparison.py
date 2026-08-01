"""Unit tests for connectome_analysis.context_comparison."""

from __future__ import annotations

import numpy as np
import pytest

from connectome_analysis.context_comparison import (
    EPS,
    OUTPUT_COLUMNS,
    assign_dominant_context,
    compute_dvi,
)


def test_output_schema_has_exactly_15_columns():
    assert len(OUTPUT_COLUMNS) == 15
    assert "dvi" in OUTPUT_COLUMNS
    assert "dominant_context" in OUTPUT_COLUMNS
    assert "delta_hz_sugar" in OUTPUT_COLUMNS
    assert "delta_hz_jo" in OUTPUT_COLUMNS
    assert "spearman_rs" in OUTPUT_COLUMNS
    assert "commit_sha" in OUTPUT_COLUMNS
    assert "random_seed" in OUTPUT_COLUMNS
    assert "epsilon" in OUTPUT_COLUMNS


def test_compute_dvi_matches_ceo071b_formula():
    sugar = -100.0
    jo = -40.0
    expected = (sugar - jo) / (sugar + jo + EPS)
    assert compute_dvi(sugar, jo) == pytest.approx(expected)
    assert compute_dvi(sugar, jo, epsilon=1e-6) == pytest.approx(expected)


def test_compute_dvi_epsilon_avoids_zero_denominator():
    # Both deltas ~0; epsilon keeps denominator finite.
    dvi = compute_dvi(0.0, 0.0, epsilon=EPS)
    assert np.isfinite(dvi)
    assert dvi == pytest.approx(0.0)


def test_dominant_context_neutral_band():
    assert assign_dominant_context(0.05) == "neutral"
    assert assign_dominant_context(-0.09) == "neutral"
    assert assign_dominant_context(0.0) == "neutral"


def test_dominant_context_sugar_and_jo():
    assert assign_dominant_context(0.25) == "sugar"
    assert assign_dominant_context(-0.25) == "jo"


def test_dominant_context_boundary_at_threshold():
    # |DVI| == 0.1 is outside the strict < 0.1 neutral band.
    assert assign_dominant_context(0.1) == "sugar"
    assert assign_dominant_context(-0.1) == "jo"
