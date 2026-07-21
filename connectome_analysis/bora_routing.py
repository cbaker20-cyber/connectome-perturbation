"""Behavioral Opponent Routing Analysis (BORA) on connectivity matrices.

Implements the one-hop opponent routing score

    O(G) = (e_G^T W e_S) * (e_{M_feeding}^T W e_G - e_{M_grooming}^T W e_G)

and a degree-matched permutation null (default 1,000 draws). Matrix convention
matches ``connectome_analysis.graph_surrogates``: ``W[i, j]`` is the signed
weight of the directed edge from ``j`` to ``i``.

These scores are structural only. They are not Brian2 results and must remain
labeled ``not_interpretable_as_neuroscience`` until a full provenance chain
exists.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from connectome_analysis.graph_surrogates import (
    CLAIM_STATUS,
    build_synthetic_surrogate_fixture,
    load_dense_signed_adjacency_from_edges,
)
from tools.path_resolver import repo_root_from, require_repo_path, resolve_input


def _as_square_float_matrix(W: np.ndarray) -> np.ndarray:
    arr = np.asarray(W, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError("W must be a square 2-D matrix")
    if not np.all(np.isfinite(arr)):
        raise ValueError("W must contain only finite values")
    return arr


def _indicator(n: int, indices: Sequence[int]) -> np.ndarray:
    vec = np.zeros(n, dtype=float)
    if not indices:
        raise ValueError("index set must be non-empty")
    seen: set[int] = set()
    for idx in indices:
        i = int(idx)
        if i < 0 or i >= n:
            raise IndexError(f"index {i} out of bounds for size {n}")
        if i in seen:
            continue
        seen.add(i)
        vec[i] = 1.0
    return vec


def node_degrees(W: np.ndarray) -> np.ndarray:
    """Return total absolute degree ``in + out`` per node for matching."""
    matrix = _as_square_float_matrix(W)
    incoming = np.sum(np.abs(matrix), axis=1)
    outgoing = np.sum(np.abs(matrix), axis=0)
    return np.asarray(incoming + outgoing, dtype=float)


def opponent_routing_score(
    W: np.ndarray,
    source_indices: Sequence[int],
    gate_indices: Sequence[int],
    feeding_motor_indices: Sequence[int],
    grooming_motor_indices: Sequence[int],
) -> float:
    """Return ``O(G)`` for gate set ``G``.

    ``O(G) = e_G^T W e_S * (e_{M_f}^T W e_G - e_{M_g}^T W e_G)``
    """
    matrix = _as_square_float_matrix(W)
    n = matrix.shape[0]
    e_s = _indicator(n, source_indices)
    e_g = _indicator(n, gate_indices)
    e_mf = _indicator(n, feeding_motor_indices)
    e_mg = _indicator(n, grooming_motor_indices)

    source_exposure = float(e_g @ (matrix @ e_s))
    downstream_feed = float(e_mf @ (matrix @ e_g))
    downstream_groom = float(e_mg @ (matrix @ e_g))
    return float(source_exposure * (downstream_feed - downstream_groom))


def _degree_bin_labels(degrees: np.ndarray, *, n_bins: int) -> np.ndarray:
    values = np.asarray(degrees, dtype=float)
    if values.size == 0:
        raise ValueError("degrees must be non-empty")
    bins = max(1, min(int(n_bins), int(values.size)))
    # Rank-based bins keep matching defined even with many tied degrees.
    order = values.argsort(kind="mergesort")
    ranks = np.empty(values.size, dtype=float)
    ranks[order] = np.arange(values.size, dtype=float)
    edges = np.linspace(0.0, float(values.size), bins + 1)
    labels = np.digitize(ranks, edges[1:-1], right=False)
    return labels.astype(int)


def degree_matched_gate_sample(
    rng: np.random.Generator,
    *,
    focus_indices: Sequence[int],
    pool_indices: Sequence[int],
    degrees: np.ndarray,
    n_bins: int = 5,
) -> list[int]:
    """Sample a degree-bin-matched gate set of the same size as ``focus_indices``."""
    focus = [int(i) for i in focus_indices]
    pool = [int(i) for i in pool_indices]
    if not focus:
        raise ValueError("focus_indices must be non-empty")
    if not pool:
        raise ValueError("pool_indices must be non-empty")
    focus_set = set(focus)
    eligible = [i for i in pool if i not in focus_set]
    if len(eligible) < len(focus):
        raise ValueError("eligible null pool is smaller than the focus set")

    labels = _degree_bin_labels(degrees, n_bins=n_bins)
    focus_bins = [int(labels[i]) for i in focus]
    bin_to_candidates: dict[int, list[int]] = {}
    for idx in eligible:
        bin_to_candidates.setdefault(int(labels[idx]), []).append(idx)

    chosen: list[int] = []
    used: set[int] = set()
    for b in focus_bins:
        candidates = [c for c in bin_to_candidates.get(b, []) if c not in used]
        if not candidates:
            candidates = [c for c in eligible if c not in used]
        if not candidates:
            raise ValueError("unable to draw a degree-matched null sample")
        pick = int(rng.choice(candidates))
        chosen.append(pick)
        used.add(pick)
    return chosen


def degree_matched_null_opponent_scores(
    W: np.ndarray,
    *,
    source_indices: Sequence[int],
    focus_gate_indices: Sequence[int],
    feeding_motor_indices: Sequence[int],
    grooming_motor_indices: Sequence[int],
    null_pool_indices: Sequence[int] | None = None,
    n_permutations: int = 1000,
    n_bins: int = 5,
    seed: int = 58,
) -> dict[str, object]:
    """Run a degree-matched permutation null for ``O(G)``.

    Returns the observed score, null mean/sd, and empirical two-sided tail
    proportion with the finite-sample ``(+1)/(n+1)`` correction used elsewhere
    in this repository.
    """
    if n_permutations < 1:
        raise ValueError("n_permutations must be >= 1")

    matrix = _as_square_float_matrix(W)
    n = matrix.shape[0]
    degrees = node_degrees(matrix)
    if null_pool_indices is None:
        pool = list(range(n))
    else:
        pool = [int(i) for i in null_pool_indices]

    observed = opponent_routing_score(
        matrix,
        source_indices,
        focus_gate_indices,
        feeding_motor_indices,
        grooming_motor_indices,
    )

    rng = np.random.default_rng(seed)
    null_values = np.empty(n_permutations, dtype=float)
    for i in range(n_permutations):
        sample = degree_matched_gate_sample(
            rng,
            focus_indices=focus_gate_indices,
            pool_indices=pool,
            degrees=degrees,
            n_bins=n_bins,
        )
        null_values[i] = opponent_routing_score(
            matrix,
            source_indices,
            sample,
            feeding_motor_indices,
            grooming_motor_indices,
        )

    null_mean = float(np.mean(null_values))
    null_sd = float(np.std(null_values, ddof=1)) if n_permutations > 1 else float("nan")
    p_greater = float((np.sum(null_values >= observed) + 1) / (n_permutations + 1))
    p_less = float((np.sum(null_values <= observed) + 1) / (n_permutations + 1))
    p_two_sided = float(min(1.0, 2.0 * min(p_greater, p_less)))
    return {
        "observed_O": observed,
        "null_mean": null_mean,
        "null_sd": null_sd,
        "p_greater": p_greater,
        "p_less": p_less,
        "p_two_sided": p_two_sided,
        "n_permutations": int(n_permutations),
        "seed": int(seed),
        "null_values": null_values,
        "claim_status": CLAIM_STATUS,
    }


def compute_bora_routing_rows(
    fixture: dict[str, object] | None = None,
    *,
    n_permutations: int = 1000,
    seed: int = 58,
) -> list[dict[str, object]]:
    """Score synthetic gate groups and attach degree-matched null summaries."""
    data = fixture or build_synthetic_surrogate_fixture()
    W = np.asarray(data["W"], dtype=float)
    n = W.shape[0]
    # Exclude sources and motors from the null pool so matched draws stay gates.
    reserved = set(data["sugar"]) | set(data["motor"])  # type: ignore[arg-type]
    pool = [i for i in range(n) if i not in reserved]

    rows: list[dict[str, object]] = []
    for group_name, gate in (
        ("gate_feeding_biased", list(data["gate_feeding_biased"])),  # type: ignore[list-item]
        ("gate_grooming_biased", list(data["gate_grooming_biased"])),  # type: ignore[list-item]
    ):
        result = degree_matched_null_opponent_scores(
            W,
            source_indices=list(data["sugar"]),  # type: ignore[arg-type]
            focus_gate_indices=gate,
            feeding_motor_indices=list(data["feeding_motor"]),  # type: ignore[arg-type]
            grooming_motor_indices=list(data["grooming_motor"]),  # type: ignore[arg-type]
            null_pool_indices=pool,
            n_permutations=n_permutations,
            seed=seed,
        )
        rows.append(
            {
                "group": group_name,
                "gate_indices": ",".join(str(i) for i in gate),
                "O_score": float(result["observed_O"]),  # type: ignore[arg-type]
                "null_mean": float(result["null_mean"]),  # type: ignore[arg-type]
                "null_sd": float(result["null_sd"]),  # type: ignore[arg-type]
                "p_greater": float(result["p_greater"]),  # type: ignore[arg-type]
                "p_less": float(result["p_less"]),  # type: ignore[arg-type]
                "p_two_sided": float(result["p_two_sided"]),  # type: ignore[arg-type]
                "n_permutations": int(result["n_permutations"]),  # type: ignore[arg-type]
                "seed": int(result["seed"]),  # type: ignore[arg-type]
                "claim_status": CLAIM_STATUS,
                "fixture_seed": int(data["seed"]),  # type: ignore[arg-type]
            }
        )
    return rows


def write_bora_routing_scores_csv(
    output_path: str | Path = "results/bora_routing_scores.csv",
    *,
    repo_root: Path | None = None,
    n_permutations: int = 1000,
    seed: int = 58,
) -> Path:
    """Write BORA routing scores with null summaries under the repository root."""
    root = repo_root_from(repo_root)
    out = require_repo_path(root, root / Path(output_path), "bora routing output")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = compute_bora_routing_rows(n_permutations=n_permutations, seed=seed)
    fieldnames = [
        "group",
        "gate_indices",
        "O_score",
        "null_mean",
        "null_sd",
        "p_greater",
        "p_less",
        "p_two_sided",
        "n_permutations",
        "seed",
        "claim_status",
        "fixture_seed",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out


def resolve_annotations_path(
    identifier: str = "flywire_annotations.tsv",
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve annotation inputs through ``tools.path_resolver``."""
    return resolve_input(identifier, repo_root=repo_root)


# Re-export for callers that want a single import surface for matrix builds.
build_W_from_edges = load_dense_signed_adjacency_from_edges


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--permutations",
        type=int,
        default=1000,
        help="Number of degree-matched null permutations (default: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=58,
        help="RNG seed for the null (default: 58)",
    )
    parser.add_argument(
        "--output",
        default="results/bora_routing_scores.csv",
        help="Repo-relative CSV output path",
    )
    args = parser.parse_args(argv)
    if args.permutations < 1:
        parser.error("--permutations must be >= 1")
    path = write_bora_routing_scores_csv(
        args.output,
        n_permutations=args.permutations,
        seed=args.seed,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
