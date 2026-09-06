"""Unit tests for reusable structural predictor mathematics."""

from __future__ import annotations

import numpy as np
import pytest

from connectome_analysis.graph_surrogates import (
    attenuated_source_to_target_flow,
    from_to_adjacency,
    load_dense_signed_adjacency_from_edges,
    modal_controllability,
    path_attenuation_ratio,
    remove_nodes,
    resolve_connectivity_matrix_path,
    spearman_rho,
)


def test_modal_controllability_matches_hand_formula_on_diagonalizable_real_matrix():
    W = np.array([[0.0, 0.2, 0.0], [0.2, 0.0, 0.1], [0.0, 0.1, 0.0]])
    eigenvalues, eigenvectors = np.linalg.eigh(W)
    expected = np.sum((1.0 - eigenvalues**2) * (eigenvectors**2), axis=1)
    np.testing.assert_allclose(modal_controllability(W), expected, rtol=1e-10, atol=1e-12)


def test_modal_controllability_rejects_non_square():
    with pytest.raises(ValueError, match="square"):
        modal_controllability(np.ones((2, 3)))


def test_path_attenuation_ratio_known_chain():
    from_to = np.zeros((4, 4), dtype=float)
    from_to[0, 1] = 1.0
    from_to[1, 2] = 1.0
    from_to[0, 3] = 1.0
    from_to[3, 2] = 1.0
    W = from_to_adjacency(from_to)

    den = attenuated_source_to_target_flow(W, [0], [2], gamma=0.5, max_path_length=2)
    assert den == pytest.approx(2.0 * 0.5**2)
    reduced = remove_nodes(W, [3])
    num = attenuated_source_to_target_flow(reduced, [0], [2], gamma=0.5, max_path_length=2)
    assert num == pytest.approx(0.5**2)
    assert path_attenuation_ratio(W, [0], [2], [3], gamma=0.5, max_path_length=2) == pytest.approx(0.5)


def test_path_attenuation_requires_nonzero_denominator():
    with pytest.raises(ValueError, match="denominator flow is zero"):
        path_attenuation_ratio(np.zeros((3, 3)), [0], [2], [1], gamma=0.5, max_path_length=2)


def test_spearman_rho_perfect_and_inverse():
    assert spearman_rho([1.0, 2.0, 3.0], [10.0, 20.0, 30.0]) == pytest.approx(1.0)
    assert spearman_rho([1.0, 2.0, 3.0], [30.0, 20.0, 10.0]) == pytest.approx(-1.0)


def test_path_resolver_used_for_connectivity_input():
    path = resolve_connectivity_matrix_path("2023_03_23_connectivity_630_final.parquet")
    assert path.name == "2023_03_23_connectivity_630_final.parquet"
    assert path.exists()


def test_load_dense_signed_adjacency_preserves_direction_and_accumulates_edges():
    W = load_dense_signed_adjacency_from_edges([(0, 1, 2.0), (0, 1, -0.5)], n_nodes=2)
    assert W[1, 0] == pytest.approx(1.5)
    assert W[0, 1] == pytest.approx(0.0)
