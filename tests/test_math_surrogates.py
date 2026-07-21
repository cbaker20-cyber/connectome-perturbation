"""Unit tests for modal controllability, path attenuation, and BORA O(G)."""

from __future__ import annotations

import csv

import numpy as np
import pytest

from connectome_analysis.bora_routing import (
    degree_matched_null_opponent_scores,
    opponent_routing_score,
    write_bora_routing_scores_csv,
)
from connectome_analysis.graph_surrogates import (
    attenuated_source_to_target_flow,
    build_synthetic_surrogate_fixture,
    from_to_adjacency,
    load_dense_signed_adjacency_from_edges,
    modal_controllability,
    path_attenuation_ratio,
    remove_nodes,
    resolve_connectivity_matrix_path,
    spearman_rho,
    write_surrogate_correlations_csv,
)


def test_modal_controllability_matches_hand_formula_on_diagonalizable_real_matrix():
    # Symmetric matrix → real orthonormal eigenvectors; formula is exact.
    W = np.array(
        [
            [0.0, 0.2, 0.0],
            [0.2, 0.0, 0.1],
            [0.0, 0.1, 0.0],
        ],
        dtype=float,
    )
    eigenvalues, eigenvectors = np.linalg.eigh(W)
    expected = np.sum((1.0 - eigenvalues**2) * (eigenvectors**2), axis=1)
    got = modal_controllability(W)
    np.testing.assert_allclose(got, expected, rtol=1e-10, atol=1e-12)


def test_modal_controllability_rejects_non_square():
    with pytest.raises(ValueError, match="square"):
        modal_controllability(np.ones((2, 3)))


def test_path_attenuation_ratio_known_chain():
    # from-to: 0→1→2 with optional bypass gate node 3: 0→3→2
    # Control-theoretic W[post, pre].
    from_to = np.zeros((4, 4), dtype=float)
    from_to[0, 1] = 1.0
    from_to[1, 2] = 1.0
    from_to[0, 3] = 1.0
    from_to[3, 2] = 1.0
    W = from_to_adjacency(from_to)

    gamma = 0.5
    K = 2
    # Intact two-hop S→M flow: path 0→1→2 and 0→3→2 each contribute gamma^2.
    den = attenuated_source_to_target_flow(W, [0], [2], gamma=gamma, max_path_length=K)
    assert den == pytest.approx(2.0 * (gamma**2))

    # Remove gate node 3: only 0→1→2 remains.
    reduced = remove_nodes(W, [3])
    num = attenuated_source_to_target_flow(reduced, [0], [2], gamma=gamma, max_path_length=K)
    assert num == pytest.approx(gamma**2)

    eta = path_attenuation_ratio(W, [0], [2], [3], gamma=gamma, max_path_length=K)
    assert eta == pytest.approx(1.0 - (num / den))
    assert eta == pytest.approx(0.5)


def test_path_attenuation_requires_nonzero_denominator():
    W = np.zeros((3, 3), dtype=float)
    with pytest.raises(ValueError, match="denominator flow is zero"):
        path_attenuation_ratio(W, [0], [2], [1], gamma=0.5, max_path_length=2)


def test_opponent_routing_score_sign_and_magnitude():
    # Sugar 0 → gate 1 → feeding 2; sugar 0 → gate 3 → grooming 4.
    edges = [
        (0, 1, 2.0),  # S→G_feed
        (1, 2, 3.0),  # G_feed→Mf
        (0, 3, 2.0),  # S→G_groom
        (3, 4, 3.0),  # G_groom→Mg
    ]
    W = load_dense_signed_adjacency_from_edges(edges, n_nodes=5)

    o_feed = opponent_routing_score(W, [0], [1], [2], [4])
    o_groom = opponent_routing_score(W, [0], [3], [2], [4])

    # O = (e_G^T W e_S) * (e_Mf^T W e_G - e_Mg^T W e_G)
    # feed gate: exposure=2, (3 - 0) → 6
    # groom gate: exposure=2, (0 - 3) → -6
    assert o_feed == pytest.approx(6.0)
    assert o_groom == pytest.approx(-6.0)


def test_degree_matched_null_is_deterministic_and_uses_1000_permutations():
    fixture = build_synthetic_surrogate_fixture(seed=57)
    W = np.asarray(fixture["W"], dtype=float)
    reserved = set(fixture["sugar"]) | set(fixture["motor"])
    pool = [i for i in range(W.shape[0]) if i not in reserved]

    first = degree_matched_null_opponent_scores(
        W,
        source_indices=fixture["sugar"],
        focus_gate_indices=fixture["gate_feeding_biased"],
        feeding_motor_indices=fixture["feeding_motor"],
        grooming_motor_indices=fixture["grooming_motor"],
        null_pool_indices=pool,
        n_permutations=1000,
        seed=58,
    )
    second = degree_matched_null_opponent_scores(
        W,
        source_indices=fixture["sugar"],
        focus_gate_indices=fixture["gate_feeding_biased"],
        feeding_motor_indices=fixture["feeding_motor"],
        grooming_motor_indices=fixture["grooming_motor"],
        null_pool_indices=pool,
        n_permutations=1000,
        seed=58,
    )

    assert first["n_permutations"] == 1000
    assert first["observed_O"] == second["observed_O"]
    np.testing.assert_allclose(first["null_values"], second["null_values"])
    assert 0.0 < first["p_two_sided"] <= 1.0


def test_feeding_gate_has_higher_O_than_grooming_gate_on_fixture():
    fixture = build_synthetic_surrogate_fixture()
    W = np.asarray(fixture["W"], dtype=float)
    o_feed = opponent_routing_score(
        W,
        fixture["sugar"],
        fixture["gate_feeding_biased"],
        fixture["feeding_motor"],
        fixture["grooming_motor"],
    )
    o_groom = opponent_routing_score(
        W,
        fixture["sugar"],
        fixture["gate_grooming_biased"],
        fixture["feeding_motor"],
        fixture["grooming_motor"],
    )
    assert o_feed > 0
    assert o_groom < 0
    assert o_feed > o_groom


def test_spearman_rho_perfect_and_inverse():
    assert spearman_rho([1.0, 2.0, 3.0], [10.0, 20.0, 30.0]) == pytest.approx(1.0)
    assert spearman_rho([1.0, 2.0, 3.0], [30.0, 20.0, 10.0]) == pytest.approx(-1.0)


def test_path_resolver_used_for_connectivity_input():
    path = resolve_connectivity_matrix_path("2023_03_23_connectivity_630_final.parquet")
    assert path.name == "2023_03_23_connectivity_630_final.parquet"
    assert path.exists()


def test_export_csv_writers():
    repo_surrogate = write_surrogate_correlations_csv("results/surrogate_correlations.csv")
    repo_bora = write_bora_routing_scores_csv("results/bora_routing_scores.csv", n_permutations=1000)

    assert repo_surrogate.exists()
    assert repo_bora.exists()
    assert repo_surrogate.name == "surrogate_correlations.csv"
    assert repo_bora.name == "bora_routing_scores.csv"

    with repo_surrogate.open(encoding="utf-8", newline="") as handle:
        surrogate_rows = list(csv.DictReader(handle))
    with repo_bora.open(encoding="utf-8", newline="") as handle:
        bora_rows = list(csv.DictReader(handle))

    assert any(row["metric"] == "modal_controllability" for row in surrogate_rows)
    assert any(row["metric"] == "path_attenuation_ratio" for row in surrogate_rows)
    assert all(row["claim_status"] == "not_interpretable_as_neuroscience" for row in surrogate_rows)
    assert {row["group"] for row in bora_rows} == {"gate_feeding_biased", "gate_grooming_biased"}
    assert all(int(row["n_permutations"]) == 1000 for row in bora_rows)
    assert all(row["claim_status"] == "not_interpretable_as_neuroscience" for row in bora_rows)
