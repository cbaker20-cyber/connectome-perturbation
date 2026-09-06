"""Reusable structural predictors for connectome-vs-dynamics comparisons.

These functions implement matrix algebra only. They do not run Brian2 and their
outputs are structural proxies, not biological findings.

Matrix convention: ``W[i, j]`` is the signed weight of the directed edge from
node ``j`` to node ``i``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from tools.path_resolver import resolve_input

CLAIM_STATUS = "not_interpretable_as_neuroscience"


def _as_square_float_matrix(W: np.ndarray) -> np.ndarray:
    arr = np.asarray(W, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError("W must be a square 2-D matrix")
    if not np.all(np.isfinite(arr)):
        raise ValueError("W must contain only finite values")
    return arr


def _indicator(n: int, indices: Sequence[int], *, normalize: bool = False) -> np.ndarray:
    vec = np.zeros(n, dtype=float)
    if not indices:
        raise ValueError("index set must be non-empty")
    for idx in indices:
        if not isinstance(idx, (int, np.integer)):
            raise TypeError("indices must be integers")
        i = int(idx)
        if i < 0 or i >= n:
            raise IndexError(f"index {i} out of bounds for size {n}")
        vec[i] = 1.0
    if normalize:
        total = float(vec.sum())
        if total <= 0:
            raise ValueError("indicator vector has zero mass")
        vec /= total
    return vec


def modal_controllability(W: np.ndarray) -> np.ndarray:
    """Return node-wise modal-controllability scores for a stable matrix."""
    matrix = _as_square_float_matrix(W)
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    weights = 1.0 - np.abs(eigenvalues) ** 2
    contributions = (np.abs(eigenvectors) ** 2) * weights.reshape(1, -1)
    return np.asarray(np.real(np.sum(contributions, axis=1)), dtype=float)


def remove_nodes(W: np.ndarray, node_indices: Sequence[int]) -> np.ndarray:
    """Return ``W`` with rows and columns for ``node_indices`` zeroed."""
    matrix = _as_square_float_matrix(W).copy()
    n = matrix.shape[0]
    for idx in node_indices:
        i = int(idx)
        if i < 0 or i >= n:
            raise IndexError(f"node index {i} out of bounds for size {n}")
        matrix[i, :] = 0.0
        matrix[:, i] = 0.0
    return matrix


def attenuated_source_to_target_flow(
    W: np.ndarray,
    source_indices: Sequence[int],
    target_indices: Sequence[int],
    *,
    gamma: float,
    max_path_length: int,
    normalize_indicators: bool = False,
) -> float:
    """Compute ``sum_k gamma**k * e_target.T W**k e_source``."""
    if not (0.0 < gamma < 1.0):
        raise ValueError("gamma must lie in (0, 1)")
    if max_path_length < 1:
        raise ValueError("max_path_length must be >= 1")

    matrix = _as_square_float_matrix(W)
    n = matrix.shape[0]
    e_source = _indicator(n, source_indices, normalize=normalize_indicators)
    e_target = _indicator(n, target_indices, normalize=normalize_indicators)

    state = e_source.copy()
    total = 0.0
    factor = 1.0
    for _ in range(max_path_length):
        state = matrix @ state
        factor *= gamma
        total += factor * float(e_target @ state)
    return float(total)


def path_attenuation_ratio(
    W: np.ndarray,
    source_indices: Sequence[int],
    motor_indices: Sequence[int],
    gate_indices: Sequence[int],
    *,
    gamma: float = 0.8,
    max_path_length: int = 4,
    normalize_indicators: bool = False,
) -> float:
    """Return the fraction of source-to-motor flow removed by a node set."""
    denominator = attenuated_source_to_target_flow(
        W,
        source_indices,
        motor_indices,
        gamma=gamma,
        max_path_length=max_path_length,
        normalize_indicators=normalize_indicators,
    )
    if denominator == 0.0:
        raise ValueError("denominator flow is zero; cannot compute path attenuation ratio")

    numerator = attenuated_source_to_target_flow(
        remove_nodes(W, gate_indices),
        source_indices,
        motor_indices,
        gamma=gamma,
        max_path_length=max_path_length,
        normalize_indicators=normalize_indicators,
    )
    return float(1.0 - numerator / denominator)


def from_to_adjacency(weights_from_to: np.ndarray) -> np.ndarray:
    """Convert an ordinary ``i -> j`` adjacency to the ``W[j, i]`` layout."""
    return _as_square_float_matrix(weights_from_to).T.copy()


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float:
    """Return Spearman rank correlation for finite equal-length vectors."""
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.shape != b.shape or a.size < 2:
        raise ValueError("x and y must be same-length vectors with length >= 2")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("x and y must be finite")
    ra = a.argsort().argsort().astype(float)
    rb = b.argsort().argsort().astype(float)
    ra -= ra.mean()
    rb -= rb.mean()
    denom = float(np.sqrt(np.sum(ra**2) * np.sum(rb**2)))
    return float("nan") if denom == 0.0 else float(np.sum(ra * rb) / denom)


def resolve_connectivity_matrix_path(
    identifier: str = "2023_03_23_connectivity_630_final.parquet",
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve a connectivity input through the repository manifest."""
    return resolve_input(identifier, repo_root=repo_root)


def load_dense_signed_adjacency_from_edges(
    edges: Iterable[tuple[int, int, float]],
    *,
    n_nodes: int | None = None,
) -> np.ndarray:
    """Build control-theoretic ``W`` from ``(pre, post, signed_weight)`` edges."""
    edge_list = list(edges)
    if not edge_list:
        raise ValueError("edges must be non-empty")
    max_id = 0
    for pre, post, weight in edge_list:
        if pre < 0 or post < 0:
            raise ValueError("node ids must be non-negative")
        if not np.isfinite(weight):
            raise ValueError("edge weights must be finite")
        max_id = max(max_id, int(pre), int(post))
    n = max_id + 1 if n_nodes is None else int(n_nodes)
    if n <= max_id:
        raise ValueError("n_nodes is smaller than the largest edge endpoint")
    W = np.zeros((n, n), dtype=float)
    for pre, post, weight in edge_list:
        W[int(post), int(pre)] += float(weight)
    return W
