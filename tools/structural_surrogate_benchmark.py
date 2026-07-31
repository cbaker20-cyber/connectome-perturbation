#!/usr/bin/env python3
"""
Instant Structural Surrogate Benchmark.

This is a fast, non-Brian2 benchmark layer for the connectome project. It gives
professor-facing data even when full spiking sweeps are slow.

Core idea:
    Estimate which (input_context, lesion_target) pairs should matter for motor
    output using only sparse graph propagation and motor reach.

It does NOT replace the spiking simulator. It creates the structural prediction
matrix that the spiking simulator is supposed to beat.

For each context and perturbation group, it computes:
  - source exposure to the target group,
  - target downstream exposure to motor neurons,
  - intercepted source-to-motor flow proxy,
  - lesion size / degree / strength baselines,
  - an overall surrogate vulnerability score.

Outputs:
  results/structural_surrogate_benchmark/context_target_surrogate_scores.csv
  results/structural_surrogate_benchmark/top_surrogate_hits.csv
  results/structural_surrogate_benchmark/structural_surrogate_run_info.csv

Example:
  python tools/structural_surrogate_benchmark.py \
    --connectivity 2023_03_23_connectivity_630_final.parquet \
    --annotations flywire_annotations.tsv \
    --contexts metadata/source_contexts/source_context_manifest.csv \
    --context-mode matched_size \
    --group-by cell_class \
    --max-steps-source 3 \
    --max-steps-motor 3 \
    --gamma 0.80 \
    --min-group-size 20 \
    --output-dir results/structural_surrogate_benchmark
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from time import time
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import sparse


PRE_CANDIDATES = [
    "Presynaptic_ID", "Presynaptic_Index", "pre_root_id", "pre_pt_root_id",
    "root_id_pre", "source", "source_id", "pre", "upstream_root_id",
]
POST_CANDIDATES = [
    "Postsynaptic_ID", "Postsynaptic_Index", "post_root_id", "post_pt_root_id",
    "root_id_post", "target", "target_id", "post", "downstream_root_id",
]
WEIGHT_CANDIDATES = [
    "Excitatory x Connectivity", "Connectivity", "syn_count", "synapse_count",
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
        key = normalize_name(cand)
        if key in norm:
            return norm[key]
    return None


def parse_id_file(path: str | Path) -> list[int]:
    p = Path(path)
    if not p.exists():
        return []
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
    for col in ["super_class", "cell_class", "cell_type", "top_nt"]:
        if col not in ann.columns:
            ann[col] = ""
        ann[col] = ann[col].fillna("").astype(str)
    return ann


def load_edges(path: Path, weight_mode: str) -> tuple[pd.DataFrame, str, str, str]:
    raw = pd.read_parquet(path)
    pre_col = first_existing(raw.columns, PRE_CANDIDATES)
    post_col = first_existing(raw.columns, POST_CANDIDATES)
    weight_col = first_existing(raw.columns, WEIGHT_CANDIDATES)
    if pre_col is None or post_col is None or weight_col is None:
        raise ValueError(f"Could not infer connectivity schema from columns: {list(raw.columns)}")

    e = raw[[pre_col, post_col, weight_col]].copy()
    e.columns = ["pre", "post", "weight"]
    e["pre"] = pd.to_numeric(e["pre"], errors="coerce")
    e["post"] = pd.to_numeric(e["post"], errors="coerce")
    e["weight"] = pd.to_numeric(e["weight"], errors="coerce")
    e = e.dropna(subset=["pre", "post", "weight"])
    e["pre"] = e["pre"].astype("int64").map(int)
    e["post"] = e["post"].astype("int64").map(int)
    if weight_mode == "absolute":
        e["weight"] = e["weight"].abs()
    elif weight_mode == "positive_only":
        e = e[e["weight"] > 0].copy()
    elif weight_mode == "nonnegative":
        e["weight"] = e["weight"].clip(lower=0)
        e = e[e["weight"] > 0].copy()
    else:
        raise ValueError("weight_mode must be nonnegative, positive_only, or absolute")
    e = e.groupby(["pre", "post"], as_index=False)["weight"].sum()
    return e, pre_col, post_col, weight_col


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
    P = sparse.diags(inv) @ W
    return P.tocsr(), id_to_idx


def attenuated_flow(source_ids: list[int], id_to_idx: dict[int, int], P: sparse.csr_matrix, max_steps: int, gamma: float) -> np.ndarray:
    n = P.shape[0]
    x = np.zeros(n, dtype=float)
    idx = [id_to_idx[int(s)] for s in source_ids if int(s) in id_to_idx]
    if not idx:
        return x
    x[idx] = 1.0 / len(idx)
    flow = np.zeros(n, dtype=float)
    current = x.copy()
    for k in range(1, max_steps + 1):
        current = current @ P
        flow += (gamma ** (k - 1)) * current
    return np.asarray(flow).ravel()


def attenuated_reverse_motor_reach(motor_ids: list[int], id_to_idx: dict[int, int], P: sparse.csr_matrix, max_steps: int, gamma: float) -> np.ndarray:
    # Reverse propagation from motor neurons through transpose(P) estimates which
    # upstream neurons can reach the motor pool through short weighted paths.
    n = P.shape[0]
    x = np.zeros(n, dtype=float)
    idx = [id_to_idx[int(s)] for s in motor_ids if int(s) in id_to_idx]
    if not idx:
        return x
    x[idx] = 1.0 / len(idx)
    flow = np.zeros(n, dtype=float)
    current = x.copy()
    PT = P.T.tocsr()
    for k in range(1, max_steps + 1):
        current = current @ PT
        flow += (gamma ** (k - 1)) * current
    return np.asarray(flow).ravel()


def minmax(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan)
    if v.notna().sum() == 0:
        return pd.Series(0.0, index=s.index)
    lo, hi = v.min(), v.max()
    if hi == lo:
        return pd.Series(0.5, index=s.index)
    return ((v - lo) / (hi - lo)).fillna(0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast structural surrogate benchmark for context-target motor vulnerability.")
    parser.add_argument("--connectivity", default="2023_03_23_connectivity_630_final.parquet")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--contexts", default="metadata/source_contexts/source_context_manifest.csv")
    parser.add_argument("--context-mode", default="matched_size")
    parser.add_argument("--context-names", default="gustatory,mechanosensory,visual_projection,sensory_ascending,all_sensory")
    parser.add_argument("--group-by", default="cell_class", choices=["super_class", "cell_class", "cell_type"])
    parser.add_argument("--min-group-size", type=int, default=20)
    parser.add_argument("--max-steps-source", type=int, default=3)
    parser.add_argument("--max-steps-motor", type=int, default=3)
    parser.add_argument("--gamma", type=float, default=0.80)
    parser.add_argument("--weight-mode", default="nonnegative", choices=["nonnegative", "positive_only", "absolute"])
    parser.add_argument("--output-dir", default="results/structural_surrogate_benchmark")
    args = parser.parse_args()

    start = time()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("Loading annotations...")
    ann = load_annotations(Path(args.annotations))
    print("Loading connectivity...")
    edges, pre_col, post_col, weight_col = load_edges(Path(args.connectivity), args.weight_mode)

    node_ids = sorted(set(edges["pre"].map(int)).union(set(edges["post"].map(int))).union(set(ann["root_id"].map(int))))
    print(f"Building transition matrix for {len(node_ids):,} nodes and {len(edges):,} edges...")
    P, id_to_idx = build_transition(edges, node_ids)

    ann = ann[ann["root_id"].isin(id_to_idx)].copy()
    ann[args.group_by] = ann[args.group_by].replace("", "unannotated")

    motor_ids = ann.loc[ann["super_class"].str.lower().eq("motor"), "root_id"].map(int).tolist()
    print(f"Motor IDs in annotations/graph: {len(motor_ids):,}")
    motor_reach = attenuated_reverse_motor_reach(motor_ids, id_to_idx, P, args.max_steps_motor, args.gamma)

    group_counts = ann.groupby(args.group_by)["root_id"].count().rename("n_neurons").reset_index()
    group_counts = group_counts[group_counts["n_neurons"] >= args.min_group_size].copy()
    group_counts = group_counts.sort_values("n_neurons", ascending=False)
    groups = group_counts[args.group_by].astype(str).tolist()
    print(f"Groups: {len(groups)} using {args.group_by} with min_group_size={args.min_group_size}")

    # Group-level static baselines.
    out_strength_by_pre = edges.groupby("pre")["weight"].sum()
    out_degree_by_pre = edges.groupby("pre")["post"].nunique()
    group_static = []
    for group in groups:
        ids = ann.loc[ann[args.group_by] == group, "root_id"].map(int).tolist()
        idx = [id_to_idx[i] for i in ids if i in id_to_idx]
        group_static.append({
            args.group_by: group,
            "n_neurons": len(ids),
            "n_in_graph": len(idx),
            "removed_outgoing_weight": float(out_strength_by_pre.reindex(ids).fillna(0).sum()),
            "mean_out_strength": float(out_strength_by_pre.reindex(ids).fillna(0).mean()) if ids else 0.0,
            "mean_out_degree": float(out_degree_by_pre.reindex(ids).fillna(0).mean()) if ids else 0.0,
            "mean_motor_reach": float(motor_reach[idx].mean()) if idx else 0.0,
            "total_motor_reach": float(motor_reach[idx].sum()) if idx else 0.0,
        })
    group_static_df = pd.DataFrame(group_static)

    manifest = pd.read_csv(args.contexts)
    manifest = manifest[manifest["mode"].astype(str).eq(args.context_mode)].copy()
    if args.context_names:
        wanted = {x.strip() for x in args.context_names.split(",") if x.strip()}
        manifest = manifest[manifest["context_name"].astype(str).isin(wanted)].copy()
    if manifest.empty:
        raise ValueError("No context manifest rows selected. Run create_source_contexts.py or adjust --context-names.")

    rows = []
    for ctx in manifest.itertuples(index=False):
        context_name = str(ctx.context_name)
        source_path = str(ctx.path)
        source_ids = parse_id_file(source_path)
        source_ids = [s for s in source_ids if s in id_to_idx]
        print(f"Context {context_name}: {len(source_ids)} source IDs")
        source_flow = attenuated_flow(source_ids, id_to_idx, P, args.max_steps_source, args.gamma)

        for group in groups:
            ids = ann.loc[ann[args.group_by] == group, "root_id"].map(int).tolist()
            idx = [id_to_idx[i] for i in ids if i in id_to_idx]
            if idx:
                mean_source_exposure = float(source_flow[idx].mean())
                total_source_exposure = float(source_flow[idx].sum())
                mean_motor_reach = float(motor_reach[idx].mean())
                total_motor_reach = float(motor_reach[idx].sum())
                intercepted_flow_proxy = float(np.sum(source_flow[idx] * motor_reach[idx]))
            else:
                mean_source_exposure = 0.0
                total_source_exposure = 0.0
                mean_motor_reach = 0.0
                total_motor_reach = 0.0
                intercepted_flow_proxy = 0.0
            rows.append({
                "input_context": context_name,
                "source_path": source_path,
                "n_source_ids": len(source_ids),
                args.group_by: group,
                "mean_source_exposure": mean_source_exposure,
                "total_source_exposure": total_source_exposure,
                "mean_motor_reach": mean_motor_reach,
                "total_motor_reach": total_motor_reach,
                "intercepted_flow_proxy": intercepted_flow_proxy,
            })

    df = pd.DataFrame(rows)
    df = df.merge(group_static_df, on=args.group_by, how="left", suffixes=("", "_static"))
    df = df.rename(columns={args.group_by: "perturbation_target"})

    # Composite score: deliberately decomposable, not magic.
    df["source_exposure_z01"] = minmax(df["mean_source_exposure"])
    df["motor_reach_z01"] = minmax(df["mean_motor_reach"])
    df["intercepted_flow_z01"] = minmax(df["intercepted_flow_proxy"])
    df["lesion_size_z01"] = minmax(np.log1p(df["n_in_graph"].fillna(0)))
    df["removed_weight_z01"] = minmax(np.log1p(df["removed_outgoing_weight"].fillna(0)))
    df["surrogate_vulnerability_score"] = (
        0.35 * df["intercepted_flow_z01"] +
        0.25 * df["source_exposure_z01"] +
        0.20 * df["motor_reach_z01"] +
        0.10 * df["removed_weight_z01"] +
        0.10 * df["lesion_size_z01"]
    )

    df = df.sort_values("surrogate_vulnerability_score", ascending=False).reset_index(drop=True)
    df["surrogate_rank"] = np.arange(1, len(df) + 1)

    full_path = out / "context_target_surrogate_scores.csv"
    top_path = out / "top_surrogate_hits.csv"
    info_path = out / "structural_surrogate_run_info.csv"
    df.to_csv(full_path, index=False)
    df.head(50).to_csv(top_path, index=False)

    run_info = pd.DataFrame([{
        "connectivity": args.connectivity,
        "annotations": args.annotations,
        "contexts": args.contexts,
        "context_mode": args.context_mode,
        "context_names": args.context_names,
        "group_by": args.group_by,
        "min_group_size": args.min_group_size,
        "max_steps_source": args.max_steps_source,
        "max_steps_motor": args.max_steps_motor,
        "gamma": args.gamma,
        "weight_mode": args.weight_mode,
        "n_nodes": P.shape[0],
        "n_edges": P.nnz,
        "n_contexts": len(manifest),
        "n_groups": len(groups),
        "elapsed_s": time() - start,
        "pre_col": pre_col,
        "post_col": post_col,
        "weight_col": weight_col,
    }])
    run_info.to_csv(info_path, index=False)

    print(f"Saved full surrogate table: {full_path}")
    print(f"Saved top hits: {top_path}")
    print(f"Saved run info: {info_path}")
    print(df[["surrogate_rank", "input_context", "perturbation_target", "surrogate_vulnerability_score", "mean_source_exposure", "mean_motor_reach", "intercepted_flow_proxy", "n_in_graph"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
