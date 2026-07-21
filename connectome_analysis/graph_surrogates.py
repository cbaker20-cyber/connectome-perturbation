"""Graph-theoretical structural surrogates for connectome matrices.

Implements Modal Controllability and Path Attenuation Ratio on signed,
weighted connectivity matrices. These helpers are matrix algebra only; they do
not run Brian2 simulations and must not be interpreted as biological claims
without a full provenance/validation record.

Matrix convention
-----------------
``W[i, j]`` is the signed weight of the directed edge **from j to i**
(control-theoretic adjacency). With that convention:

- ``W @ e_S`` accumulates one-hop influence from sources ``S``;
- ``e_M.T @ (W ** k) @ e_S`` is the length-``k`` attenuated flow from ``S`` to ``M``.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from tools.path_resolver import repo_root_from, require_repo_path, resolve_input

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
    """Return node-wise modal controllability scores ``c_i``.

    For a signed weighted adjacency ``W`` with eigendecomposition
    ``W V = V diag(lambda)``:

        c_i = sum_j (1 - lambda_j(W)^2) * v_{ij}^2

    Complex eigenpairs (asymmetric ``W``) use the real-valued magnitude form
    ``(1 - |lambda_j|^2) * |v_{ij}|^2``, which reduces to the real formula when
    all eigenpairs are real.
    """
    matrix = _as_square_float_matrix(W)
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    # Columns of eigenvectors are right eigenvectors; rows index nodes.
    weights = 1.0 - np.abs(eigenvalues) ** 2
    contributions = (np.abs(eigenvectors) ** 2) * weights.reshape(1, -1)
    scores = np.real(np.sum(contributions, axis=1))
    return np.asarray(scores, dtype=float)


def remove_nodes(W: np.ndarray, node_indices: Sequence[int]) -> np.ndarray:
    """Return ``W`` with rows and columns for ``node_indices`` zeroed (``W_{\\G}``)."""
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
    """Compute ``sum_{k=1}^{K} gamma^k * e_M^T W^k e_S``."""
    if not (0.0 < gamma < 1.0):
        raise ValueError("gamma must lie in (0, 1)")
    if max_path_length < 1:
        raise ValueError("max_path_length must be >= 1")

    matrix = _as_square_float_matrix(W)
    n = matrix.shape[0]
    e_s = _indicator(n, source_indices, normalize=normalize_indicators)
    e_m = _indicator(n, target_indices, normalize=normalize_indicators)

    state = e_s.copy()
    total = 0.0
    factor = 1.0
    for _ in range(max_path_length):
        state = matrix @ state
        factor *= gamma
        total += factor * float(e_m @ state)
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
    """Return Path Attenuation Ratio ``eta(G)``.

        eta(G) = 1 - num / den

    where

        num = sum_k gamma^k e_M^T (W_{\\G})^k e_S
        den = sum_k gamma^k e_M^T W^k e_S

    and ``W_{\\G}`` is ``W`` with gate nodes ``G`` removed.
    """
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

    reduced = remove_nodes(W, gate_indices)
    numerator = attenuated_source_to_target_flow(
        reduced,
        source_indices,
        motor_indices,
        gamma=gamma,
        max_path_length=max_path_length,
        normalize_indicators=normalize_indicators,
    )
    return float(1.0 - (numerator / denominator))


def from_to_adjacency(weights_from_to: np.ndarray) -> np.ndarray:
    """Convert an i→j adjacency into the control-theoretic j→i layout used here."""
    matrix = _as_square_float_matrix(weights_from_to)
    return matrix.T.copy()


def build_synthetic_surrogate_fixture(*, seed: int = 57) -> dict[str, object]:
    """Deterministic signed digraph used for exports and unit-test anchors."""
    rng = np.random.default_rng(seed)
    # Nodes: 0 sugar, 1-2 gates, 3 feeding motor, 4 grooming motor, 5 distractor.
    n = 6
    from_to = np.zeros((n, n), dtype=float)
    # Sugar → gates / distractor
    from_to[0, 1] = 1.2
    from_to[0, 2] = 0.4
    from_to[0, 5] = 0.3
    # Gate 1 biases feeding; gate 2 biases grooming.
    from_to[1, 3] = 1.5
    from_to[1, 4] = 0.2
    from_to[2, 3] = 0.1
    from_to[2, 4] = 1.1
    # Mild recurrence / signed edges for modal controllability.
    from_to[3, 1] = -0.15
    from_to[4, 2] = -0.10
    from_to[5, 3] = 0.25
    from_to[1, 2] = 0.05
    # Scale to keep spectral radius comfortably below 1 for modal formula.
    scale = 0.35 / max(float(np.max(np.abs(np.linalg.eigvals(from_to.T)))), 1e-9)
    from_to *= scale
    # Tiny noise-free jitter slot kept deterministic via unused rng draw record.
    _ = float(rng.random())
    W = from_to_adjacency(from_to)
    return {
        "W": W,
        "from_to": from_to,
        "sugar": [0],
        "motor": [3, 4],
        "feeding_motor": [3],
        "grooming_motor": [4],
        "gate_feeding_biased": [1],
        "gate_grooming_biased": [2],
        "seed": seed,
        "claim_status": CLAIM_STATUS,
    }


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman rank correlation for small deterministic vectors (no SciPy)."""
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
    if denom == 0.0:
        return float("nan")
    return float(np.sum(ra * rb) / denom)


def compute_surrogate_correlation_rows(fixture: dict[str, object] | None = None) -> list[dict[str, object]]:
    """Compute modal/path-attenuation scores and pairwise correlations on a fixture."""
    data = fixture or build_synthetic_surrogate_fixture()
    W = np.asarray(data["W"], dtype=float)
    c = modal_controllability(W)
    eta_feed = path_attenuation_ratio(
        W,
        data["sugar"],  # type: ignore[arg-type]
        data["motor"],  # type: ignore[arg-type]
        data["gate_feeding_biased"],  # type: ignore[arg-type]
        gamma=0.8,
        max_path_length=4,
    )
    eta_groom = path_attenuation_ratio(
        W,
        data["sugar"],  # type: ignore[arg-type]
        data["motor"],  # type: ignore[arg-type]
        data["gate_grooming_biased"],  # type: ignore[arg-type]
        gamma=0.8,
        max_path_length=4,
    )

    # Synthetic "effect proxy": outbound strength toward motors (structural only).
    motor = list(data["motor"])  # type: ignore[arg-type]
    effect_proxy = np.array([float(np.sum(np.abs(W[motor, i]))) for i in range(W.shape[0])], dtype=float)
    rho_modal_effect = spearman_rho(c, effect_proxy)

    rows: list[dict[str, object]] = [
        {
            "metric": "modal_controllability_mean",
            "value": float(np.mean(c)),
            "node_or_group": "all",
            "paired_metric": "",
            "spearman_rho": "",
            "claim_status": CLAIM_STATUS,
            "fixture_seed": int(data["seed"]),  # type: ignore[arg-type]
        },
        {
            "metric": "path_attenuation_ratio",
            "value": float(eta_feed),
            "node_or_group": "gate_feeding_biased",
            "paired_metric": "",
            "spearman_rho": "",
            "claim_status": CLAIM_STATUS,
            "fixture_seed": int(data["seed"]),  # type: ignore[arg-type]
        },
        {
            "metric": "path_attenuation_ratio",
            "value": float(eta_groom),
            "node_or_group": "gate_grooming_biased",
            "paired_metric": "",
            "spearman_rho": "",
            "claim_status": CLAIM_STATUS,
            "fixture_seed": int(data["seed"]),  # type: ignore[arg-type]
        },
        {
            "metric": "surrogate_correlation",
            "value": float(rho_modal_effect),
            "node_or_group": "all",
            "paired_metric": "modal_controllability_vs_motor_outstrength_proxy",
            "spearman_rho": float(rho_modal_effect),
            "claim_status": CLAIM_STATUS,
            "fixture_seed": int(data["seed"]),  # type: ignore[arg-type]
        },
    ]
    for i, score in enumerate(c):
        rows.append(
            {
                "metric": "modal_controllability",
                "value": float(score),
                "node_or_group": str(i),
                "paired_metric": "",
                "spearman_rho": "",
                "claim_status": CLAIM_STATUS,
                "fixture_seed": int(data["seed"]),  # type: ignore[arg-type]
            }
        )
    return rows


def write_surrogate_correlations_csv(
    output_path: str | Path = "results/surrogate_correlations.csv",
    *,
    repo_root: Path | None = None,
) -> Path:
    """Write surrogate score / correlation table under the repository root."""
    root = repo_root_from(repo_root)
    out = require_repo_path(root, root / Path(output_path), "surrogate correlations output")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = compute_surrogate_correlation_rows()
    fieldnames = [
        "metric",
        "value",
        "node_or_group",
        "paired_metric",
        "spearman_rho",
        "claim_status",
        "fixture_seed",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out


def resolve_connectivity_matrix_path(
    identifier: str = "2023_03_23_connectivity_630_final.parquet",
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve a connectivity input through ``tools.path_resolver``."""
    return resolve_input(identifier, repo_root=repo_root)


def load_dense_signed_adjacency_from_edges(
    edges: Iterable[tuple[int, int, float]],
    *,
    n_nodes: int | None = None,
) -> np.ndarray:
    """Build control-theoretic ``W`` from ``(pre, post, weight)`` edges.

    Node labels must be contiguous integers ``0 .. n-1`` (or remapped by the
    caller). ``pre → post`` becomes ``W[post, pre] = weight``.
    """
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
    n = n_nodes if n_nodes is not None else max_id + 1
    if n <= max_id:
        raise ValueError("n_nodes is smaller than the largest edge endpoint")
    W = np.zeros((n, n), dtype=float)
    for pre, post, weight in edge_list:
        W[int(post), int(pre)] += float(weight)
    return W


if __name__ == "__main__":
    path = write_surrogate_correlations_csv()
    print(path)
