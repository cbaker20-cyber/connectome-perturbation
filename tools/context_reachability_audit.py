#!/usr/bin/env python3
"""
Context reachability audit for the final benchmark.

This script computes attenuated downstream flow from each input context to each
cell type, then compares observed exposure to a matched random-source null.

Primary output:
    results/context_reachability/context_by_cell_type_exposure.csv

Design goal:
    Do not label a cell type as biologically unimportant just because it has low
    effect under one stimulus. First determine whether that cell type is
    structurally exposed to the input context.

Example:
    python tools/context_reachability_audit.py \
        --connectivity 2023_03_23_connectivity_630_final.parquet \
        --annotations flywire_annotations.tsv \
        --contexts metadata/source_contexts/source_context_manifest.csv \
        --group-by cell_class \
        --max-steps 6 \
        --gamma 0.80 \
        --n-null 100 \
        --output-dir results/context_reachability
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import sparse
from statsmodels.stats.multitest import multipletests


PRE_CANDIDATES = [
    "Presynaptic_ID", "Presynaptic_Index", "pre_root_id", "pre_pt_root_id",
    "root_id_pre", "source", "source_id", "pre", "upstream_root_id",
]
POST_CANDIDATES = [
    "Postsynaptic_ID", "Postsynaptic_Index", "post_root_id", "post_pt_root_id",
    "root_id_post", "target", "target_id", "post", "downstream_root_id",
]
WEIGHT_CANDIDATES = [
    "Connectivity", "Excitatory x Connectivity", "syn_count", "synapse_count",
    "n_synapses", "synapses", "weight", "count", "nt_weight",
]


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower())


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    columns = list(columns)
    exact = set(columns)
    for cand in candidates:
        if cand in exact:
            return cand
    norm = {normalize_name(c): c for c in columns}
    for cand in candidates:
        if normalize_name(cand) in norm:
            return norm[normalize_name(cand)]
    return None


def parse_id_file(path: str | Path) -> list[int]:
    p = Path(path)
    text = p.read_text().strip()
    if not text:
        return []
    toks = re.split(r"[\s,;]+", text)
    return [int(t) for t in toks if t]


def load_annotations(path: Path) -> pd.DataFrame:
    ann = pd.read_csv(path, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError("annotations must contain root_id")
    ann = ann.copy()
    ann["root_id"] = pd.to_numeric(ann["root_id"], errors="coerce")
    ann = ann.dropna(subset=["root_id"])
    ann["root_id"] = ann["root_id"].astype("int64").map(int)
    for col in ["super_class", "cell_class", "cell_type", "hemibrain_type", "top_nt"]:
        if col not in ann.columns:
            ann[col] = ""
        ann[col] = ann[col].fillna("").astype(str)
    return ann


def load_edges(path: Path, weight_mode: str = "nonnegative") -> tuple[pd.DataFrame, str, str, str]:
    raw = pd.read_parquet(path)
    pre_col = first_existing(raw.columns, PRE_CANDIDATES)
    post_col = first_existing(raw.columns, POST_CANDIDATES)
    weight_col = first_existing(raw.columns, WEIGHT_CANDIDATES)
    if pre_col is None or post_col is None or weight_col is None:
        raise ValueError(f"Could not infer edge schema from columns: {list(raw.columns)}")
    edges = raw[[pre_col, post_col, weight_col]].copy()
    edges.columns = ["pre", "post", "weight"]
    edges["pre"] = pd.to_numeric(edges["pre"], errors="coerce")
    edges["post"] = pd.to_numeric(edges["post"], errors="coerce")
    edges["weight"] = pd.to_numeric(edges["weight"], errors="coerce")
    edges = edges.dropna(subset=["pre", "post", "weight"])
    edges["pre"] = edges["pre"].astype("int64").map(int)
    edges["post"] = edges["post"].astype("int64").map(int)

    if weight_mode == "absolute":
        edges["weight"] = edges["weight"].abs()
    elif weight_mode == "positive_only":
        edges = edges[edges["weight"] > 0].copy()
    elif weight_mode == "nonnegative":
        edges["weight"] = edges["weight"].clip(lower=0)
        edges = edges[edges["weight"] > 0].copy()
    else:
        raise ValueError("weight_mode must be nonnegative, positive_only, or absolute")

    edges = edges.groupby(["pre", "post"], as_index=False)["weight"].sum()
    return edges, pre_col, post_col, weight_col


def build_transition(edges: pd.DataFrame, node_ids: list[int]) -> tuple[sparse.csr_matrix, dict[int, int]]:
    id_to_idx = {int(n): i for i, n in enumerate(node_ids)}
    e = edges[edges["pre"].isin(id_to_idx) & edges["post"].isin(id_to_idx)].copy()
    rows = e["pre"].map(id_to_idx).to_numpy(dtype=int)
    cols = e["post"].map(id_to_idx).to_numpy(dtype=int)
    vals = e["weight"].to_numpy(dtype=float)
    n = len(node_ids)
    W = sparse.csr_matrix((vals, (rows, cols)), shape=(n, n))
    row_sums = np.asarray(W.sum(axis=1)).ravel()
    inv = np.zeros_like(row_sums, dtype=float)
    nz = row_sums > 0
    inv[nz] = 1.0 / row_sums[nz]
    Dinv = sparse.diags(inv)
    P = Dinv @ W
    return P.tocsr(), id_to_idx


def attenuated_flow(source_ids: list[int], id_to_idx: dict[int, int], P: sparse.csr_matrix, max_steps: int, gamma: float) -> np.ndarray:
    n = P.shape[0]
    x = np.zeros(n, dtype=float)
    found = [id_to_idx[int(s)] for s in source_ids if int(s) in id_to_idx]
    if not found:
        return x
    x[found] = 1.0 / len(found)
    flow = np.zeros(n, dtype=float)
    current = x.copy()
    for k in range(1, max_steps + 1):
        current = current @ P
        flow += (gamma ** (k - 1)) * current
    return flow


def make_group_table(ann: pd.DataFrame, node_ids: set[int], group_by: str, min_group_size: int) -> pd.DataFrame:
    a = ann[ann["root_id"].isin(node_ids)].copy()
    if group_by not in a.columns:
        raise ValueError(f"group_by column not found: {group_by}")
    a[group_by] = a[group_by].replace("", "unannotated")
    counts = a.groupby(group_by)["root_id"].count().rename("n_neurons").reset_index()
    counts = counts[counts["n_neurons"] >= min_group_size].copy()
    return counts.sort_values("n_neurons", ascending=False)


def aggregate_exposure(flow: np.ndarray, ann: pd.DataFrame, id_to_idx: dict[int, int], groups: pd.DataFrame, group_by: str, neuron_threshold: float) -> pd.DataFrame:
    rows = []
    for group in groups[group_by].tolist():
        ids = ann.loc[ann[group_by].replace("", "unannotated") == group, "root_id"].map(int).tolist()
        idx = [id_to_idx[i] for i in ids if i in id_to_idx]
        vals = flow[idx] if idx else np.array([], dtype=float)
        n = len(vals)
        rows.append({
            group_by: group,
            "n_neurons": n,
            "mean_source_exposure": float(vals.mean()) if n else 0.0,
            "median_source_exposure": float(np.median(vals)) if n else 0.0,
            "total_source_exposure": float(vals.sum()) if n else 0.0,
            "max_source_exposure": float(vals.max()) if n else 0.0,
            "fraction_exposed_neurons": float(np.mean(vals > neuron_threshold)) if n else 0.0,
            "n_exposed_neurons": int(np.sum(vals > neuron_threshold)) if n else 0,
        })
    return pd.DataFrame(rows)


def bh_fdr(p_values: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=p_values.index, dtype=float)
    valid = p_values.notna()
    if valid.any():
        _, q, _, _ = multipletests(p_values.loc[valid].to_numpy(float), method="fdr_bh")
        out.loc[valid] = q
    return out


def label_rows(df: pd.DataFrame, alpha: float, fold_cutoff: float, weak_fold: float) -> pd.Series:
    labels = []
    for r in df.itertuples(index=False):
        q = getattr(r, "q_exposure")
        fold = getattr(r, "fold_vs_null_median")
        frac = getattr(r, "fraction_exposed_neurons")
        n_exp = getattr(r, "n_exposed_neurons")
        mean_obs = getattr(r, "mean_source_exposure")
        if mean_obs <= 0 and frac == 0:
            labels.append("Out-of-Context")
        elif pd.notna(q) and q < alpha and fold >= fold_cutoff and (frac >= 0.10 or n_exp >= 3):
            labels.append("Robustly Exposed")
        elif mean_obs > 0 and fold >= weak_fold:
            labels.append("Weakly Exposed")
        else:
            labels.append("Ambiguous")
    return pd.Series(labels, index=df.index)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit source-context exposure by cell group.")
    parser.add_argument("--connectivity", default="2023_03_23_connectivity_630_final.parquet")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--contexts", default="metadata/source_contexts/source_context_manifest.csv")
    parser.add_argument("--output-dir", default="results/context_reachability")
    parser.add_argument("--group-by", default="cell_class", choices=["super_class", "cell_class", "cell_type"])
    parser.add_argument("--context-mode", default="complete", help="Use manifest rows with this mode, e.g. complete or matched_size")
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--gamma", type=float, default=0.80)
    parser.add_argument("--n-null", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--min-group-size", type=int, default=10)
    parser.add_argument("--neuron-threshold", type=float, default=1e-12)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--fold-cutoff", type=float, default=2.0)
    parser.add_argument("--weak-fold", type=float, default=1.25)
    parser.add_argument("--weight-mode", default="nonnegative", choices=["nonnegative", "positive_only", "absolute"])
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("Loading annotations...")
    ann = load_annotations(Path(args.annotations))
    print("Loading connectivity and building transition matrix...")
    edges, pre_col, post_col, weight_col = load_edges(Path(args.connectivity), weight_mode=args.weight_mode)
    node_ids = sorted(set(edges["pre"].map(int)).union(set(edges["post"].map(int))).union(set(ann["root_id"].map(int))))
    P, id_to_idx = build_transition(edges, node_ids)
    node_set = set(node_ids)
    print(f"Transition matrix: {P.shape[0]:,} nodes, {P.nnz:,} nonzero directed edges")
    print(f"Connectivity columns: pre={pre_col}, post={post_col}, weight={weight_col}")

    groups = make_group_table(ann, node_set, args.group_by, args.min_group_size)
    print(f"Groups to audit ({args.group_by}, n>={args.min_group_size}): {len(groups)}")

    manifest = pd.read_csv(args.contexts)
    manifest = manifest[manifest["mode"].astype(str).eq(args.context_mode)].copy()
    if manifest.empty:
        raise ValueError(f"No context manifest rows found with mode={args.context_mode}")

    all_rows = []
    null_rows = []
    all_node_ids = np.array(node_ids, dtype=np.int64)

    for ctx in manifest.itertuples(index=False):
        context_name = str(ctx.context_name)
        source_path = Path(str(ctx.path))
        if not source_path.exists():
            print(f"Skipping {context_name}: source file missing {source_path}")
            continue
        source_ids = parse_id_file(source_path)
        source_ids = [s for s in source_ids if s in id_to_idx]
        print(f"Context {context_name}: {len(source_ids)} source IDs found in graph")

        obs_flow = attenuated_flow(source_ids, id_to_idx, P, args.max_steps, args.gamma)
        obs = aggregate_exposure(obs_flow, ann, id_to_idx, groups, args.group_by, args.neuron_threshold)
        obs.insert(0, "input_context", context_name)
        obs["n_source_ids"] = len(source_ids)
        obs["context_mode"] = args.context_mode

        # Random-source null matched on source count. This is the first-pass null;
        # future versions can add degree/modality matching as additional strata.
        null_by_group = {g: [] for g in obs[args.group_by].tolist()}
        k = len(source_ids)
        if k > 0:
            for b in range(args.n_null):
                rand_ids = rng.choice(all_node_ids, size=k, replace=False).astype(int).tolist()
                nf = attenuated_flow(rand_ids, id_to_idx, P, args.max_steps, args.gamma)
                nagg = aggregate_exposure(nf, ann, id_to_idx, groups, args.group_by, args.neuron_threshold)
                nagg["bootstrap"] = b
                nagg["input_context"] = context_name
                null_rows.append(nagg)
                for row in nagg.itertuples(index=False):
                    null_by_group[getattr(row, args.group_by)].append(getattr(row, "mean_source_exposure"))

        pvals = []
        null_medians = []
        null_means = []
        null_stds = []
        for row in obs.itertuples(index=False):
            g = getattr(row, args.group_by)
            actual = getattr(row, "mean_source_exposure")
            vals = np.asarray(null_by_group.get(g, []), dtype=float)
            vals = vals[~np.isnan(vals)]
            if len(vals) == 0:
                pvals.append(np.nan)
                null_medians.append(np.nan)
                null_means.append(np.nan)
                null_stds.append(np.nan)
            else:
                pvals.append(float((np.sum(vals >= actual) + 1) / (len(vals) + 1)))
                null_medians.append(float(np.median(vals)))
                null_means.append(float(np.mean(vals)))
                null_stds.append(float(np.std(vals, ddof=1)) if len(vals) > 1 else np.nan)

        obs["null_median_exposure"] = null_medians
        obs["null_mean_exposure"] = null_means
        obs["null_std_exposure"] = null_stds
        obs["p_exposure"] = pvals
        obs["q_exposure"] = bh_fdr(obs["p_exposure"])
        obs["fold_vs_null_median"] = obs["mean_source_exposure"] / pd.Series(null_medians).replace(0, np.nan)
        obs["exposure_label"] = label_rows(obs, args.alpha, args.fold_cutoff, args.weak_fold)
        obs["reason"] = obs["exposure_label"].map({
            "Robustly Exposed": "flow exceeds matched source-count null and group-level exposure gate",
            "Weakly Exposed": "finite flow but below robust threshold",
            "Out-of-Context": "no meaningful attenuated source flow",
            "Ambiguous": "threshold-sensitive or null-comparable exposure",
        })
        all_rows.append(obs)

    final = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    output_path = out / "context_by_cell_type_exposure.csv"
    final.to_csv(output_path, index=False)

    if null_rows:
        null_df = pd.concat(null_rows, ignore_index=True)
        null_df.to_csv(out / "context_exposure_null_distribution.csv", index=False)

    run_info = pd.DataFrame([{
        "connectivity": args.connectivity,
        "annotations": args.annotations,
        "contexts": args.contexts,
        "group_by": args.group_by,
        "context_mode": args.context_mode,
        "max_steps": args.max_steps,
        "gamma": args.gamma,
        "n_null": args.n_null,
        "seed": args.seed,
        "weight_mode": args.weight_mode,
        "n_nodes": P.shape[0],
        "n_edges": P.nnz,
        "pre_col": pre_col,
        "post_col": post_col,
        "weight_col": weight_col,
    }])
    run_info.to_csv(out / "context_reachability_run_info.csv", index=False)

    print(f"Saved exposure table: {output_path}")
    if not final.empty:
        print(final.groupby(["input_context", "exposure_label"]).size().rename("n_groups").reset_index().to_string(index=False))


if __name__ == "__main__":
    main()
