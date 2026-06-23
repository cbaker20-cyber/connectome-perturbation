#!/usr/bin/env python3
r"""
novel_architecture_analysis.py

Behavioral Opponent Routing Analysis (BORA) for connectome-to-behavior switch discovery.

This script tests whether a neuron set is structurally positioned to bias source-conditioned
influence between two mutually exclusive behavioral output modules, such as feeding vs grooming.
It is designed for the Drosophila connectome project and supports the native production schema:
    Presynaptic_ID -> Postsynaptic_ID with edge weight Connectivity

Core idea
---------
Standard centrality asks whether a node is important to the whole graph. BORA asks whether a node
is both:
    1. reached by the sensory/source condition, and
    2. selectively upstream of one competing output module over another.

For source set S, feeding outputs F, grooming outputs G, and transition matrix P:
    source_exposure(v) = [sum_{t=0..K} gamma^t alpha^t s P^t]_v
    downstream_F(v)   = [sum_{t=0..K} gamma^t alpha^t P^t 1_F]_v
    downstream_G(v)   = [sum_{t=0..K} gamma^t alpha^t P^t 1_G]_v
    BORA(v)           = source_exposure(v) * (downstream_F(v) - downstream_G(v))

A positive BORA score indicates source-conditioned routing toward feeding over grooming;
a negative BORA score indicates source-conditioned routing toward grooming over feeding;
a large absolute BORA score indicates opponent-output gate-like position.

Outputs
-------
results/novel_architecture_analysis/bora_node_metrics.csv
results/novel_architecture_analysis/bora_group_summary.csv
results/novel_architecture_analysis/bora_degree_matched_null_results.csv
results/novel_architecture_analysis/bora_degree_matched_null_distribution.csv
results/novel_architecture_analysis/bora_run_info.csv

Example
-------
python perturbation/novel_architecture_analysis.py `
  --connectivity "2023_03_23_connectivity_630_final.parquet" `
  --annotations "flywire_annotations.tsv" `
  --feed-ids-file "metadata\feeding_motor_ids.txt" `
  --groom-ids-file "metadata\grooming_motor_ids.txt" `
  --focus-query "cell_class == 'AN'" `
  --null-query "super_class == 'central'" `
  --sample-size 1500 `
  --n-bootstrap 1000
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
from scipy import sparse
from statsmodels.stats.multitest import multipletests


DEFAULT_SUGAR_IDS = [
    720575940624963786,
    720575940630233916,
    720575940637568838,
    720575940638202345,
    720575940617000768,
    720575940630797113,
    720575940632889389,
    720575940621754367,
    720575940621502051,
    720575940640649691,
    720575940639332736,
    720575940616885538,
    720575940639198653,
    720575940620900446,
    720575940617937543,
    720575940632425919,
    720575940633143833,
    720575940612670570,
    720575940628853239,
    720575940629176663,
    720575940611875570,
]

PRE_CANDIDATES = ["Presynaptic_ID", "pre_root_id", "pre_pt_root_id", "source", "source_id", "pre"]
POST_CANDIDATES = ["Postsynaptic_ID", "post_root_id", "post_pt_root_id", "target", "target_id", "post"]
WEIGHT_CANDIDATES = ["Connectivity", "Excitatory x Connectivity", "syn_count", "weight", "count"]


@dataclass(frozen=True)
class GraphData:
    nodes: np.ndarray
    node_to_idx: dict[int, int]
    P: sparse.csr_matrix
    in_degree: np.ndarray
    out_degree: np.ndarray
    total_degree: np.ndarray
    total_strength: np.ndarray


def bh(pvals: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=pvals.index, dtype=float)
    mask = pvals.notna()
    if mask.sum():
        out.loc[mask] = multipletests(pvals.loc[mask].to_numpy(float), method="fdr_bh")[1]
    return out


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".tsv", ".txt"}:
        return pd.read_csv(path, sep="\t", low_memory=False)
    return pd.read_csv(path, low_memory=False)


def pick_column(columns: Iterable[str], candidates: list[str], label: str) -> str:
    cols = list(columns)
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in lower:
            return lower[cand.lower()]
    raise ValueError(f"Could not identify {label} column. Available columns: {cols[:30]}")


def identify_edge_columns(df: pd.DataFrame, weight_col: Optional[str]) -> tuple[str, str, str]:
    pre = pick_column(df.columns, PRE_CANDIDATES, "pre/source")
    post = pick_column(df.columns, POST_CANDIDATES, "post/target")
    if weight_col:
        if weight_col not in df.columns:
            raise ValueError(f"Requested weight column {weight_col!r} not found")
        weight = weight_col
    else:
        weight = pick_column(df.columns, WEIGHT_CANDIDATES, "weight")
    return pre, post, weight


def parse_id_file(path: str | Path) -> list[int]:
    ids: list[int] = []
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.search(r"\d+", line)
        if match:
            ids.append(int(match.group(0)))
    if not ids:
        raise ValueError(f"No numeric IDs found in {path}")
    return sorted(set(ids))


def load_annotations(path: Path) -> pd.DataFrame:
    ann = read_table(path)
    root_col = pick_column(ann.columns, ["root_id", "pt_root_id", "id", "neuron_id"], "annotation id")
    ann = ann.rename(columns={root_col: "neuron_id"}).copy()
    ann["neuron_id"] = pd.to_numeric(ann["neuron_id"], errors="coerce")
    ann = ann.dropna(subset=["neuron_id"])
    ann["neuron_id"] = ann["neuron_id"].astype("int64").map(int)
    return ann.drop_duplicates("neuron_id")


def build_graph(connectivity_path: Path, *, weight_col: Optional[str] = None, min_weight: float = 0.0) -> GraphData:
    con = read_table(connectivity_path)
    pre, post, weight = identify_edge_columns(con, weight_col)

    df = con[[pre, post, weight]].copy()
    df.columns = ["source", "target", "weight"]
    df["source"] = pd.to_numeric(df["source"], errors="coerce")
    df["target"] = pd.to_numeric(df["target"], errors="coerce")
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df = df.dropna(subset=["source", "target", "weight"])
    if min_weight > 0:
        df = df[df["weight"] >= min_weight]
    df = df[df["weight"] > 0]
    df["source"] = df["source"].astype("int64").map(int)
    df["target"] = df["target"].astype("int64").map(int)
    df = df.groupby(["source", "target"], as_index=False)["weight"].sum()

    if df.empty:
        raise ValueError("No usable positive-weight edges after filtering")

    nodes = np.array(sorted(set(df["source"]).union(set(df["target"]))), dtype=np.int64)
    node_to_idx = {int(n): i for i, n in enumerate(nodes)}
    rows = df["source"].map(node_to_idx).to_numpy(dtype=np.int64)
    cols = df["target"].map(node_to_idx).to_numpy(dtype=np.int64)
    weights = df["weight"].to_numpy(dtype=float)
    n = len(nodes)

    A = sparse.csr_matrix((weights, (rows, cols)), shape=(n, n), dtype=float)
    out_strength = np.asarray(A.sum(axis=1)).ravel()
    in_strength = np.asarray(A.sum(axis=0)).ravel()
    total_strength = out_strength + in_strength
    out_degree = np.diff(A.indptr)
    in_degree = np.diff(A.tocsc().indptr)
    total_degree = out_degree + in_degree

    denom = out_strength.copy()
    denom[denom == 0] = 1.0
    P = sparse.diags(1.0 / denom).dot(A).tocsr()

    return GraphData(
        nodes=nodes,
        node_to_idx=node_to_idx,
        P=P,
        in_degree=in_degree.astype(float),
        out_degree=out_degree.astype(float),
        total_degree=total_degree.astype(float),
        total_strength=total_strength.astype(float),
    )


def make_indicator(ids: list[int], node_to_idx: dict[int, int], n: int, *, normalize: bool = True) -> np.ndarray:
    v = np.zeros(n, dtype=float)
    for rid in ids:
        idx = node_to_idx.get(int(rid))
        if idx is not None:
            v[idx] = 1.0
    if normalize and v.sum() > 0:
        v /= v.sum()
    return v


def discounted_forward_from_sources(P: sparse.csr_matrix, source_vec: np.ndarray, *, alpha: float, gamma: float, max_steps: int) -> np.ndarray:
    """Return sum_t gamma^t alpha^t source_vec P^t."""
    accum = source_vec.astype(float).copy()
    state = source_vec.astype(float).copy()
    factor = 1.0
    for _ in range(max_steps):
        state = state @ P
        factor *= alpha * gamma
        accum += factor * state
    return np.asarray(accum).ravel()


def discounted_backward_to_targets(P: sparse.csr_matrix, target_vec: np.ndarray, *, alpha: float, gamma: float, max_steps: int) -> np.ndarray:
    """Return sum_t gamma^t alpha^t P^t target_vec, interpreted as downstream reachability."""
    accum = target_vec.astype(float).copy()
    state = target_vec.astype(float).copy()
    PT = P.T.tocsr()
    factor = 1.0
    for _ in range(max_steps):
        state = PT @ state
        factor *= alpha * gamma
        accum += factor * state
    return np.asarray(accum).ravel()


def compute_bora_metrics(
    P: sparse.csr_matrix,
    source_vec: np.ndarray,
    feed_vec: np.ndarray,
    groom_vec: np.ndarray,
    *,
    alpha: float,
    gamma: float,
    max_steps: int,
) -> pd.DataFrame:
    source_exposure = discounted_forward_from_sources(P, source_vec, alpha=alpha, gamma=gamma, max_steps=max_steps)
    downstream_feed = discounted_backward_to_targets(P, feed_vec, alpha=alpha, gamma=gamma, max_steps=max_steps)
    downstream_groom = discounted_backward_to_targets(P, groom_vec, alpha=alpha, gamma=gamma, max_steps=max_steps)
    opponent_selectivity = downstream_feed - downstream_groom
    bora_signed = source_exposure * opponent_selectivity
    bora_abs = source_exposure * np.abs(opponent_selectivity)
    feed_gateway = source_exposure * downstream_feed
    groom_gateway = source_exposure * downstream_groom

    return pd.DataFrame(
        {
            "source_exposure": source_exposure,
            "downstream_feed": downstream_feed,
            "downstream_groom": downstream_groom,
            "opponent_selectivity": opponent_selectivity,
            "bora_signed": bora_signed,
            "bora_abs": bora_abs,
            "feed_gateway": feed_gateway,
            "groom_gateway": groom_gateway,
        }
    )


def safe_query(df: pd.DataFrame, query: str, label: str) -> pd.Series:
    try:
        idx = df.query(query, engine="python").index
    except Exception as exc:
        raise ValueError(f"Failed to evaluate {label} query {query!r}: {exc}") from exc
    mask = pd.Series(False, index=df.index)
    mask.loc[idx] = True
    return mask


def summarize_group(metrics: pd.DataFrame, group_mask: pd.Series, label: str) -> dict[str, float | str | int]:
    sub = metrics.loc[group_mask]
    row: dict[str, float | str | int] = {"group": label, "n": int(len(sub))}
    for col in [
        "source_exposure",
        "downstream_feed",
        "downstream_groom",
        "opponent_selectivity",
        "bora_signed",
        "bora_abs",
        "feed_gateway",
        "groom_gateway",
        "total_degree",
        "total_strength",
    ]:
        if len(sub):
            row[f"{col}_mean"] = float(sub[col].mean())
            row[f"{col}_median"] = float(sub[col].median())
        else:
            row[f"{col}_mean"] = math.nan
            row[f"{col}_median"] = math.nan
    return row


def matched_sample_pool(
    metrics: pd.DataFrame,
    focus_mask: pd.Series,
    null_mask: pd.Series,
    *,
    match_metric: str,
    bins: int,
) -> tuple[pd.Series, pd.Series]:
    m = metrics[match_metric].copy()
    valid = m.notna()
    focus = focus_mask & valid
    null = null_mask & valid & ~focus_mask
    if focus.sum() == 0 or null.sum() == 0:
        raise ValueError("Focus or null pool empty after filtering")

    ranks = m.rank(method="average")
    try:
        bin_series = pd.qcut(ranks, q=min(bins, int(valid.sum())), labels=False, duplicates="drop")
    except ValueError:
        bin_series = pd.Series(0, index=metrics.index)
    return focus, null & bin_series.notna()


def bootstrap_null(
    metrics: pd.DataFrame,
    focus_mask: pd.Series,
    null_mask: pd.Series,
    *,
    metrics_to_test: list[str],
    match_metric: str,
    bins: int,
    n_bootstrap: int,
    sample_size: Optional[int],
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    focus, null = matched_sample_pool(metrics, focus_mask, null_mask, match_metric=match_metric, bins=bins)
    focus_indices = metrics.index[focus].to_numpy()
    null_indices = metrics.index[null].to_numpy()

    n_focus = len(focus_indices)
    n_sample = n_focus if sample_size is None else min(sample_size, len(null_indices))
    if n_sample <= 0:
        raise ValueError("Null sample size is zero")

    rows = []
    dist_rows = []

    for metric in metrics_to_test:
        actual = float(metrics.loc[focus_indices, metric].mean())
        null_vals = np.empty(n_bootstrap, dtype=float)
        for i in range(n_bootstrap):
            draw = rng.choice(null_indices, size=n_sample, replace=False if n_sample <= len(null_indices) else True)
            null_vals[i] = float(metrics.loc[draw, metric].mean())
            dist_rows.append({"metric": metric, "iteration": i, "null_mean": null_vals[i]})
        null_mean = float(np.mean(null_vals))
        null_sd = float(np.std(null_vals, ddof=1)) if len(null_vals) > 1 else math.nan
        p_greater = float((np.sum(null_vals >= actual) + 1) / (len(null_vals) + 1))
        p_less = float((np.sum(null_vals <= actual) + 1) / (len(null_vals) + 1))
        p_two = float(min(1.0, 2.0 * min(p_greater, p_less)))
        z = float((actual - null_mean) / null_sd) if null_sd and not math.isnan(null_sd) and null_sd > 0 else math.nan
        rows.append(
            {
                "metric": metric,
                "focus_n": n_focus,
                "null_pool_n": len(null_indices),
                "sample_n": n_sample,
                "actual_mean": actual,
                "null_mean": null_mean,
                "null_sd": null_sd,
                "z": z,
                "p_greater": p_greater,
                "p_less": p_less,
                "p_two_sided": p_two,
            }
        )

    res = pd.DataFrame(rows)
    for pcol in ["p_greater", "p_less", "p_two_sided"]:
        res[f"q_{pcol[2:]}"] = bh(res[pcol])
    dist = pd.DataFrame(dist_rows)
    return res, dist


def generate_mock(output_dir: Path) -> tuple[Path, Path, Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(13)
    n = 300
    ids = np.arange(100000, 100000 + n, dtype=np.int64)
    rows = []
    for src in range(n):
        targets = rng.choice(n, size=12, replace=False)
        for tgt in targets:
            weight = rng.poisson(3) + 1
            rows.append((int(ids[src]), int(ids[tgt]), int(weight)))
    con = pd.DataFrame(rows, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity"])
    con_path = output_dir / "mock_connectivity.parquet"
    con.to_parquet(con_path, index=False)

    ann = pd.DataFrame(
        {
            "root_id": ids,
            "cell_class": np.where(np.arange(n) < 40, "AN", "other"),
            "super_class": np.where(np.arange(n) < 40, "ascending", "central"),
            "cell_type": [f"mock_{i%17}" for i in range(n)],
        }
    )
    ann_path = output_dir / "mock_annotations.tsv"
    ann.to_csv(ann_path, sep="\t", index=False)
    feed_path = output_dir / "mock_feed_ids.txt"
    groom_path = output_dir / "mock_groom_ids.txt"
    source_path = output_dir / "mock_source_ids.txt"
    feed_path.write_text("\n".join(map(str, ids[-20:-10])))
    groom_path.write_text("\n".join(map(str, ids[-10:])))
    source_path.write_text("\n".join(map(str, ids[:10])))
    return con_path, ann_path, feed_path, groom_path, source_path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Behavioral Opponent Routing Analysis (BORA)")
    p.add_argument("--connectivity", default="2023_03_23_connectivity_630_final.parquet")
    p.add_argument("--annotations", default="flywire_annotations.tsv")
    p.add_argument("--source-ids-file", default=None)
    p.add_argument("--feed-ids-file", required=False)
    p.add_argument("--groom-ids-file", required=False)
    p.add_argument("--weight-col", default=None)
    p.add_argument("--min-weight", type=float, default=0.0)
    p.add_argument("--focus-query", default="cell_class == 'AN'")
    p.add_argument("--fallback-focus-query", default="super_class == 'ascending'")
    p.add_argument("--null-query", default="super_class == 'central'")
    p.add_argument("--match-metric", default="total_strength_full")
    p.add_argument("--match-bins", type=int, default=20)
    p.add_argument("--sample-size", type=int, default=1500)
    p.add_argument("--n-bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--alpha", type=float, default=0.85)
    p.add_argument("--early-gamma", type=float, default=0.75)
    p.add_argument("--max-steps", type=int, default=8)
    p.add_argument("--output-dir", default="results/novel_architecture_analysis")
    p.add_argument("--mock", action="store_true")
    return p


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mock:
        con_path, ann_path, feed_path, groom_path, source_path = generate_mock(output_dir / "mock_inputs")
        args.connectivity = str(con_path)
        args.annotations = str(ann_path)
        args.feed_ids_file = str(feed_path)
        args.groom_ids_file = str(groom_path)
        args.source_ids_file = str(source_path)

    if not args.feed_ids_file or not args.groom_ids_file:
        raise SystemExit("Provide --feed-ids-file and --groom-ids-file, or use --mock")

    connectivity_path = Path(args.connectivity)
    annotations_path = Path(args.annotations)
    print(f"Loading graph from {connectivity_path}")
    graph = build_graph(connectivity_path, weight_col=args.weight_col, min_weight=args.min_weight)
    P = graph.P
    nodes = graph.nodes
    node_to_idx = graph.node_to_idx
    n = len(nodes)
    print(f"Graph nodes: {n:,}; nonzero edges: {P.nnz:,}")

    source_ids = parse_id_file(args.source_ids_file) if args.source_ids_file else DEFAULT_SUGAR_IDS
    feed_ids = parse_id_file(args.feed_ids_file)
    groom_ids = parse_id_file(args.groom_ids_file)

    source_vec = make_indicator(source_ids, node_to_idx, n, normalize=True)
    feed_vec = make_indicator(feed_ids, node_to_idx, n, normalize=True)
    groom_vec = make_indicator(groom_ids, node_to_idx, n, normalize=True)

    print(f"Sources found: {int((source_vec > 0).sum()):,} / {len(source_ids):,}")
    print(f"Feed targets found: {int((feed_vec > 0).sum()):,} / {len(feed_ids):,}")
    print(f"Groom targets found: {int((groom_vec > 0).sum()):,} / {len(groom_ids):,}")
    if source_vec.sum() == 0 or feed_vec.sum() == 0 or groom_vec.sum() == 0:
        raise SystemExit("Source/feed/groom target vector is empty after graph mapping; check IDs.")

    print("Computing BORA metrics")
    bora = compute_bora_metrics(P, source_vec, feed_vec, groom_vec, alpha=args.alpha, gamma=args.early_gamma, max_steps=args.max_steps)
    metrics = pd.DataFrame({"neuron_id": nodes})
    metrics = pd.concat([metrics, bora], axis=1)
    metrics["in_degree"] = graph.in_degree
    metrics["out_degree"] = graph.out_degree
    metrics["total_degree"] = graph.total_degree
    metrics["total_strength"] = graph.total_strength
    metrics["total_strength_full"] = graph.total_strength

    ann = load_annotations(annotations_path)
    metrics = metrics.merge(ann, on="neuron_id", how="left")
    metrics["is_source"] = metrics["neuron_id"].isin(set(source_ids))
    metrics["is_feed_target"] = metrics["neuron_id"].isin(set(feed_ids))
    metrics["is_groom_target"] = metrics["neuron_id"].isin(set(groom_ids))

    focus_mask = safe_query(metrics, args.focus_query, "focus")
    if focus_mask.sum() == 0 and args.fallback_focus_query:
        print(f"Focus query returned 0 rows; trying fallback: {args.fallback_focus_query}")
        focus_mask = safe_query(metrics, args.fallback_focus_query, "fallback focus")
    null_mask = safe_query(metrics, args.null_query, "null")

    print(f"Focus neurons: {int(focus_mask.sum()):,}")
    print(f"Null pool neurons: {int(null_mask.sum()):,}")

    metrics_to_test = [
        "source_exposure",
        "downstream_feed",
        "downstream_groom",
        "opponent_selectivity",
        "bora_signed",
        "bora_abs",
        "feed_gateway",
        "groom_gateway",
        "total_degree",
        "total_strength",
    ]

    group_summary = pd.DataFrame(
        [
            summarize_group(metrics, focus_mask, "focus"),
            summarize_group(metrics, null_mask, "null_pool"),
        ]
    )

    print("Running degree/strength-matched bootstrap null")
    null_results, null_dist = bootstrap_null(
        metrics,
        focus_mask,
        null_mask,
        metrics_to_test=metrics_to_test,
        match_metric=args.match_metric,
        bins=args.match_bins,
        n_bootstrap=args.n_bootstrap,
        sample_size=args.sample_size,
        seed=args.seed,
    )

    metrics.to_csv(output_dir / "bora_node_metrics.csv", index=False)
    group_summary.to_csv(output_dir / "bora_group_summary.csv", index=False)
    null_results.to_csv(output_dir / "bora_degree_matched_null_results.csv", index=False)
    null_dist.to_csv(output_dir / "bora_degree_matched_null_distribution.csv", index=False)

    run_info = pd.DataFrame(
        [
            {
                "connectivity": str(connectivity_path),
                "annotations": str(annotations_path),
                "source_ids_n": len(source_ids),
                "source_ids_found": int((source_vec > 0).sum()),
                "feed_ids_n": len(feed_ids),
                "feed_ids_found": int((feed_vec > 0).sum()),
                "groom_ids_n": len(groom_ids),
                "groom_ids_found": int((groom_vec > 0).sum()),
                "focus_query": args.focus_query,
                "fallback_focus_query": args.fallback_focus_query,
                "null_query": args.null_query,
                "match_metric": args.match_metric,
                "match_bins": args.match_bins,
                "sample_size": args.sample_size,
                "n_bootstrap": args.n_bootstrap,
                "alpha": args.alpha,
                "early_gamma": args.early_gamma,
                "max_steps": args.max_steps,
                "seed": args.seed,
            }
        ]
    )
    run_info.to_csv(output_dir / "bora_run_info.csv", index=False)

    print("Top null results by q_two_sided:")
    show_cols = ["metric", "actual_mean", "null_mean", "z", "p_greater", "p_less", "p_two_sided", "q_two_sided"]
    print(null_results.sort_values("q_two_sided")[show_cols].to_string(index=False))
    print("Wrote outputs to", output_dir)


if __name__ == "__main__":
    main()
