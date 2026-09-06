"""Task-specific AN path-betweenness with degree-matched FDR control.

Issue #63 / experiment E009: compute sugar→motor source-target betweenness for
Ascending Neurons (``cell_class == AN`` in ``flywire_annotations.tsv``) and test
whether AN pathway impact exceeds a degree-matched permutation null after
Benjamini–Hochberg FDR correction.

Outputs are structural graph controls, not Brian2 lesion effects. Do not promote
them to neuroscience claims without the repository reproducibility spine.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, Optional, Sequence

import networkx as nx
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from tools.path_resolver import resolve_input

DEFAULT_SUGAR_IDS: list[int] = [
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
]

PRE_CANDIDATES = ("Presynaptic_ID", "pre_root_id", "source", "pre")
POST_CANDIDATES = ("Postsynaptic_ID", "post_root_id", "target", "post")
WEIGHT_CANDIDATES = ("Connectivity", "weight", "syn_count", "synapse_count")


def resolve_analysis_path(identifier: str, *, manifest_path: str = "data/input_manifest.json") -> Path:
    return resolve_input(identifier, manifest_path=manifest_path)


def _first_existing(columns: Iterable[str], candidates: Sequence[str]) -> Optional[str]:
    cols = set(columns)
    for name in candidates:
        if name in cols:
            return name
    return None


def load_annotations(path: Path) -> pd.DataFrame:
    ann = pd.read_csv(path, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError(f"annotations must contain root_id; columns={list(ann.columns)}")
    out = ann.copy()
    out["root_id"] = pd.to_numeric(out["root_id"], errors="coerce")
    out = out.dropna(subset=["root_id"])
    out["root_id"] = out["root_id"].astype("int64").map(int)
    return out


def load_unsigned_edges(path: Path) -> pd.DataFrame:
    raw = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    pre = _first_existing(raw.columns, PRE_CANDIDATES)
    post = _first_existing(raw.columns, POST_CANDIDATES)
    weight = _first_existing(raw.columns, WEIGHT_CANDIDATES)
    missing = [label for label, value in (("pre", pre), ("post", post), ("weight", weight)) if value is None]
    if missing:
        raise ValueError(f"Could not infer edge schema ({missing}). Columns: {list(raw.columns)}")

    edges = raw.loc[:, [pre, post, weight]].copy()
    edges.columns = ["source", "target", "weight"]
    edges["source"] = pd.to_numeric(edges["source"], errors="coerce")
    edges["target"] = pd.to_numeric(edges["target"], errors="coerce")
    edges["weight"] = pd.to_numeric(edges["weight"], errors="coerce")
    edges = edges.dropna(subset=["source", "target", "weight"])
    edges = edges[edges["weight"] > 0]
    edges["source"] = edges["source"].astype("int64").map(int)
    edges["target"] = edges["target"].astype("int64").map(int)
    edges["weight"] = edges["weight"].astype(float)
    edges = edges.groupby(["source", "target"], as_index=False)["weight"].sum()
    edges["distance"] = 1.0 / edges["weight"].clip(lower=1e-12)
    return edges


def build_digraph(edges: pd.DataFrame) -> nx.DiGraph:
    graph = nx.DiGraph()
    for row in edges.itertuples(index=False):
        graph.add_edge(int(row.source), int(row.target), weight=float(row.weight), distance=float(row.distance))
    return graph


def select_ids(
    annotations: pd.DataFrame,
    *,
    super_class: Optional[str] = None,
    cell_class: Optional[str] = None,
) -> set[int]:
    mask = pd.Series(True, index=annotations.index)
    if super_class is not None:
        mask &= annotations["super_class"].astype(str).str.lower().eq(super_class.lower())
    if cell_class is not None:
        mask &= annotations["cell_class"].astype(str).str.lower().eq(cell_class.lower())
    return set(annotations.loc[mask, "root_id"].map(int).tolist())


def ascending_neuron_ids(annotations: pd.DataFrame) -> set[int]:
    """Prefer ``cell_class == AN``; fall back to ``super_class == ascending``."""
    an_ids = select_ids(annotations, cell_class="AN")
    if an_ids:
        return an_ids
    return select_ids(annotations, super_class="ascending")


def compute_strength_metrics(graph: nx.DiGraph) -> pd.DataFrame:
    n = max(1, graph.number_of_nodes() - 1)
    rows = []
    for node in graph.nodes:
        in_strength = float(sum(data.get("weight", 1.0) for _, _, data in graph.in_edges(node, data=True)))
        out_strength = float(sum(data.get("weight", 1.0) for _, _, data in graph.out_edges(node, data=True)))
        total_strength = in_strength + out_strength
        rows.append(
            {
                "neuron_id": int(node),
                "in_strength": in_strength,
                "out_strength": out_strength,
                "total_strength": total_strength,
                "weighted_degree_centrality": total_strength / n,
            }
        )
    return pd.DataFrame(rows)


def compute_source_target_betweenness(
    graph: nx.DiGraph,
    sources: Sequence[int],
    targets: Sequence[int],
    *,
    weight: Optional[str] = "distance",
    normalized: bool = True,
) -> dict[int, float]:
    """Task-specific betweenness on directed paths from sources to targets."""
    return nx.betweenness_centrality_subset(
        graph,
        sources=list(sources),
        targets=list(targets),
        normalized=normalized,
        weight=weight,
    )


def assign_degree_bins(metrics: pd.DataFrame, metric: str, n_bins: int) -> pd.Series:
    values = np.log1p(metrics[metric].astype(float).to_numpy())
    unique = np.unique(values)
    if len(unique) < 2:
        return pd.Series(0, index=metrics.index)
    q = min(n_bins, len(unique))
    return pd.qcut(values, q=q, duplicates="drop", labels=False).astype(int)


def degree_matched_sample(
    rng: np.random.Generator,
    actual: pd.DataFrame,
    pool: pd.DataFrame,
    bin_col: str,
    sample_size: int,
) -> pd.DataFrame:
    sampled_parts = []
    actual_bins = actual[bin_col].value_counts().sort_index()
    proportions = actual_bins / actual_bins.sum()
    desired = np.floor(proportions * sample_size).astype(int)
    remainder = sample_size - int(desired.sum())
    if remainder > 0:
        fractional = (proportions * sample_size) - desired
        for bin_id in fractional.sort_values(ascending=False).index[:remainder]:
            desired.loc[bin_id] += 1

    for bin_id, n in desired.items():
        if n <= 0:
            continue
        candidates = pool[pool[bin_col] == bin_id]
        if candidates.empty:
            candidates = pool
        replace = len(candidates) < n
        chosen_idx = rng.choice(candidates.index.to_numpy(), size=int(n), replace=replace)
        sampled_parts.append(pool.loc[chosen_idx])

    if not sampled_parts:
        raise ValueError("No null sample could be drawn. Check null pool and degree bins.")
    sample = pd.concat(sampled_parts, axis=0)
    if len(sample) > sample_size:
        sample = sample.sample(n=sample_size, random_state=int(rng.integers(0, 2**32 - 1)))
    return sample


def empirical_p_values(null_values: np.ndarray, actual: float) -> dict[str, float]:
    null_values = np.asarray(null_values, dtype=float)
    null_values = null_values[~np.isnan(null_values)]
    n = len(null_values)
    p_greater = (np.sum(null_values >= actual) + 1) / (n + 1)
    p_less = (np.sum(null_values <= actual) + 1) / (n + 1)
    p_two_sided = min(1.0, 2.0 * min(p_greater, p_less))
    return {"p_greater": float(p_greater), "p_less": float(p_less), "p_two_sided": float(p_two_sided)}


def run_degree_matched_fdr_control(
    metrics: pd.DataFrame,
    focus_ids: set[int],
    null_pool_ids: set[int],
    *,
    sample_size: Optional[int] = None,
    n_permutations: int = 200,
    match_metric: str = "total_strength",
    n_bins: int = 10,
    metrics_to_test: tuple[str, ...] = ("source_target_betweenness", "total_strength"),
    statistics: tuple[str, ...] = ("mean", "sum"),
    seed: int = 7,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Degree-matched permutation null with Benjamini–Hochberg FDR."""
    rng = np.random.default_rng(seed)
    df = metrics.copy()
    df = df[df["neuron_id"].notna()].copy()
    df["neuron_id"] = df["neuron_id"].astype("int64").map(int)
    df = df.dropna(subset=[match_metric])
    df["degree_bin"] = assign_degree_bins(df, match_metric, n_bins=n_bins)

    actual_all = df[df["neuron_id"].isin(focus_ids)].copy()
    pool = df[df["neuron_id"].isin(null_pool_ids) & ~df["neuron_id"].isin(focus_ids)].copy()
    if actual_all.empty:
        raise ValueError("No focus neurons were found in graph metrics.")
    if pool.empty:
        raise ValueError("No null-pool neurons were found in graph metrics.")

    n_focus = len(actual_all)
    if sample_size is None or sample_size <= 0 or sample_size > n_focus:
        sample_size = n_focus
    actual = actual_all.sample(n=sample_size, random_state=seed) if n_focus > sample_size else actual_all

    null_rows = []
    for perm in range(n_permutations):
        sample = degree_matched_sample(
            rng, actual=actual, pool=pool, bin_col="degree_bin", sample_size=sample_size
        )
        row: dict[str, float | int] = {"permutation": perm}
        for metric in metrics_to_test:
            values = sample[metric].astype(float)
            if "mean" in statistics:
                row[f"{metric}_mean"] = float(values.mean())
            if "sum" in statistics:
                row[f"{metric}_sum"] = float(values.sum())
        null_rows.append(row)
    null_dist = pd.DataFrame(null_rows)

    result_rows = []
    for metric in metrics_to_test:
        for stat in statistics:
            col = f"{metric}_{stat}"
            if col not in null_dist.columns:
                continue
            actual_values = actual[metric].astype(float)
            actual_value = float(actual_values.mean() if stat == "mean" else actual_values.sum())
            null_values = null_dist[col].to_numpy(dtype=float)
            p = empirical_p_values(null_values, actual_value)
            null_mean = float(np.mean(null_values))
            null_std = float(np.std(null_values, ddof=1)) if len(null_values) > 1 else float("nan")
            z = (actual_value - null_mean) / null_std if null_std and not math.isclose(null_std, 0.0) else float("nan")
            percentile = float(np.mean(null_values <= actual_value) * 100.0)
            result_rows.append(
                {
                    "focus_group": "AN",
                    "metric": metric,
                    "statistic": stat,
                    "actual_value": actual_value,
                    "null_mean": null_mean,
                    "null_std": null_std,
                    "z_score": z,
                    "percentile_vs_null": percentile,
                    "p_greater": p["p_greater"],
                    "p_less": p["p_less"],
                    "p_two_sided": p["p_two_sided"],
                    "n_focus_available": n_focus,
                    "n_focus_tested": len(actual),
                    "n_null_pool": len(pool),
                    "n_permutations": n_permutations,
                    "match_metric": match_metric,
                    "seed": seed,
                    "alpha": alpha,
                    "claim_status": "not_interpretable_as_neuroscience",
                }
            )

    results = pd.DataFrame(result_rows)
    if results.empty:
        return results

    for p_col in ("p_greater", "p_two_sided"):
        valid = results[p_col].notna()
        q_col = p_col.replace("p_", "q_") + "_bh"
        sig_col = p_col.replace("p_", "significant_") + "_bh"
        results[q_col] = np.nan
        results[sig_col] = False
        if valid.any():
            reject, qvals, _, _ = multipletests(results.loc[valid, p_col], alpha=alpha, method="fdr_bh")
            results.loc[valid, q_col] = qvals
            results.loc[valid, sig_col] = reject
    return results


def build_an_betweenness_table(
    graph: nx.DiGraph,
    annotations: pd.DataFrame,
    *,
    sources: Sequence[int],
    targets: Sequence[int],
    n_permutations: int = 200,
    seed: int = 7,
    null_pool_super_class: str = "central",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Compute AN pathway betweenness and degree-matched FDR control rows."""
    sources_in_graph = [int(n) for n in sources if n in graph]
    targets_in_graph = [int(n) for n in targets if n in graph]
    if not sources_in_graph or not targets_in_graph:
        raise ValueError("Sources or targets are missing from the graph.")

    betweenness = compute_source_target_betweenness(
        graph, sources_in_graph, targets_in_graph, weight="distance", normalized=True
    )
    metrics = compute_strength_metrics(graph)
    metrics["source_target_betweenness"] = metrics["neuron_id"].map(betweenness).fillna(0.0)

    focus_ids = {n for n in ascending_neuron_ids(annotations) if n in graph}
    null_ids = {n for n in select_ids(annotations, super_class=null_pool_super_class) if n in graph}
    if not focus_ids:
        raise ValueError("No Ascending Neurons (AN / ascending) found in the graph.")

    control = run_degree_matched_fdr_control(
        metrics,
        focus_ids=focus_ids,
        null_pool_ids=null_ids,
        n_permutations=n_permutations,
        seed=seed,
        alpha=alpha,
    )
    control.insert(1, "n_sources", len(sources_in_graph))
    control.insert(2, "n_targets", len(targets_in_graph))
    control.insert(3, "n_an_in_graph", len(focus_ids))
    return control


def run_an_betweenness_control(
    *,
    connectivity_id: str = "2023_03_23_connectivity_630_final.parquet",
    annotations_id: str = "flywire_annotations.tsv",
    manifest_path: str = "data/input_manifest.json",
    output_path: str | Path = "results/an_betweenness_control.csv",
    n_permutations: int = 200,
    seed: int = 7,
    alpha: float = 0.05,
    null_pool_super_class: str = "central",
    source_ids: Optional[Sequence[int]] = None,
) -> pd.DataFrame:
    con_path = resolve_analysis_path(connectivity_id, manifest_path=manifest_path)
    ann_path = resolve_analysis_path(annotations_id, manifest_path=manifest_path)

    annotations = load_annotations(ann_path)
    edges = load_unsigned_edges(con_path)
    graph = build_digraph(edges)

    sources = list(source_ids) if source_ids is not None else list(DEFAULT_SUGAR_IDS)
    targets = sorted(select_ids(annotations, super_class="motor"))

    control = build_an_betweenness_table(
        graph,
        annotations,
        sources=sources,
        targets=targets,
        n_permutations=n_permutations,
        seed=seed,
        null_pool_super_class=null_pool_super_class,
        alpha=alpha,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    control.to_csv(out, index=False)
    return control


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connectivity", default="2023_03_23_connectivity_630_final.parquet")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--manifest", default="data/input_manifest.json")
    parser.add_argument("--output", default="results/an_betweenness_control.csv")
    parser.add_argument("--n-permutations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--null-pool-super-class", default="central")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    control = run_an_betweenness_control(
        connectivity_id=args.connectivity,
        annotations_id=args.annotations,
        manifest_path=args.manifest,
        output_path=args.output,
        n_permutations=args.n_permutations,
        seed=args.seed,
        alpha=args.alpha,
        null_pool_super_class=args.null_pool_super_class,
    )
    print(f"Wrote {len(control)} control rows to {args.output}")
    cols = [
        c
        for c in [
            "metric",
            "statistic",
            "actual_value",
            "null_mean",
            "z_score",
            "p_greater",
            "q_greater_bh",
            "significant_greater_bh",
            "p_two_sided",
            "q_two_sided_bh",
            "significant_two_sided_bh",
        ]
        if c in control.columns
    ]
    if cols:
        print(control[cols].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
