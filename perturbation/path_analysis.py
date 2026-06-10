#!/usr/bin/env python3
"""
Task-specific pathway analysis for Drosophila connectome perturbation project.

This script tests whether a target neuron set, such as AN / ascending neurons,
is overrepresented on pathways from sugar-sensory input neurons to motor-output
neurons, even if the same cells are not globally enriched for whole-brain
centrality.

Main outputs:
    results/path_analysis/path_node_metrics.csv
    results/path_analysis/path_group_summary.csv
    results/path_analysis/path_degree_matched_null_results.csv
    results/path_analysis/path_degree_matched_null_distribution.csv

Example:
    python perturbation/path_analysis.py \
        --connectivity 2023_03_23_connectivity_630_final.parquet \
        --annotations flywire_annotations.tsv \
        --target-super-class motor \
        --focus-cell-class AN \
        --sample-size 1500 \
        --n-bootstrap 1000 \
        --null-pool central

Notes:
    - Uses directed weighted edges: Presynaptic_ID -> Postsynaptic_ID.
    - Uses Connectivity as synaptic weight by default.
    - Converts synaptic weight to path distance as distance = 1 / weight.
    - Uses source-target betweenness, not whole-brain betweenness.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import networkx as nx
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests


# Sugar sensory neurons used by the original baseline sugar simulation.
# These are preferred over an annotation string such as "Sugar_Sensory", which
# is usually not present in flywire_annotations.tsv.
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
]


PRE_CANDIDATES = [
    "Presynaptic_ID",
    "Presynaptic_Index",
    "pre_root_id",
    "pre_pt_root_id",
    "root_id_pre",
    "bodyId_pre",
    "source",
    "source_id",
    "pre",
    "pre_id",
    "upstream_root_id",
]

POST_CANDIDATES = [
    "Postsynaptic_ID",
    "Postsynaptic_Index",
    "post_root_id",
    "post_pt_root_id",
    "root_id_post",
    "bodyId_post",
    "target",
    "target_id",
    "post",
    "post_id",
    "downstream_root_id",
]

WEIGHT_CANDIDATES = [
    "Connectivity",
    "Excitatory x Connectivity",
    "syn_count",
    "synapse_count",
    "n_synapses",
    "synapses",
    "weight",
    "count",
    "nt_weight",
]


@dataclass(frozen=True)
class EdgeSchema:
    pre_col: str
    post_col: str
    weight_col: str


def normalize_column_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower())


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    columns = list(columns)
    exact = set(columns)

    for candidate in candidates:
        if candidate in exact:
            return candidate

    normalized_to_original = {normalize_column_name(c): c for c in columns}
    for candidate in candidates:
        normalized = normalize_column_name(candidate)
        if normalized in normalized_to_original:
            return normalized_to_original[normalized]

    return None


def infer_edge_schema(
    columns: Iterable[str],
    pre_col: Optional[str] = None,
    post_col: Optional[str] = None,
    weight_col: Optional[str] = None,
) -> EdgeSchema:
    columns = list(columns)
    pre = pre_col or first_existing(columns, PRE_CANDIDATES)
    post = post_col or first_existing(columns, POST_CANDIDATES)
    weight = weight_col or first_existing(columns, WEIGHT_CANDIDATES)

    missing = []
    if pre is None:
        missing.append("pre/source")
    if post is None:
        missing.append("post/target")
    if weight is None:
        missing.append("weight")

    if missing:
        raise ValueError(
            "Could not infer connectivity schema. Missing: "
            + ", ".join(missing)
            + f". Available columns: {columns}"
        )

    return EdgeSchema(pre_col=pre, post_col=post, weight_col=weight)


def resolve_existing_path(path: str | Path, description: str = "file") -> Path:
    """
    Resolve paths without requiring a hard-coded Drosophila_brain_model prefix.
    """
    p = Path(path).expanduser()
    if p.exists():
        return p.resolve()

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    candidates = [
        Path.cwd() / p,
        script_dir / p,
        project_root / p,
        project_root / "Drosophila_brain_model" / p.name,
        project_root / "data" / p.name,
        Path.cwd() / "Drosophila_brain_model" / p.name,
        Path.cwd() / "data" / p.name,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        f"Could not find {description}: {path}. Tried: "
        + "; ".join(str(c) for c in candidates)
    )


def as_int_set(values: Iterable) -> set[int]:
    """Convert root IDs to Python ints and drop missing/unparseable values."""
    ser = pd.Series(list(values))
    numeric = pd.to_numeric(ser, errors="coerce").dropna()
    return set(numeric.astype("int64").map(int).tolist())


def parse_id_file(path: str | Path) -> list[int]:
    """Read a one-column or delimited ID file."""
    p = resolve_existing_path(path, "ID file")
    text = p.read_text().strip()
    if not text:
        return []
    tokens = re.split(r"[\s,;]+", text)
    return [int(float(tok)) for tok in tokens if tok]


def load_annotations(path: str | Path) -> pd.DataFrame:
    p = resolve_existing_path(path, "annotations file")
    ann = pd.read_csv(p, sep="\t", low_memory=False)
    if "root_id" not in ann.columns:
        raise ValueError(f"Annotation file must contain root_id. Columns: {list(ann.columns)}")
    ann = ann.copy()
    ann["root_id"] = pd.to_numeric(ann["root_id"], errors="coerce")
    ann = ann.dropna(subset=["root_id"])
    ann["root_id"] = ann["root_id"].astype("int64").map(int)
    return ann


def select_by_annotation(
    annotations: pd.DataFrame,
    *,
    super_class: Optional[str] = None,
    cell_class: Optional[str] = None,
    cell_type: Optional[str] = None,
    explicit_ids: Optional[Iterable[int]] = None,
) -> set[int]:
    if explicit_ids is not None:
        return set(map(int, explicit_ids))

    mask = pd.Series(True, index=annotations.index)

    if super_class is not None:
        if "super_class" not in annotations.columns:
            raise ValueError("annotations does not contain super_class")
        mask &= annotations["super_class"].astype(str).str.lower().eq(super_class.lower())

    if cell_class is not None:
        if "cell_class" not in annotations.columns:
            raise ValueError("annotations does not contain cell_class")
        mask &= annotations["cell_class"].astype(str).str.lower().eq(cell_class.lower())

    if cell_type is not None:
        if "cell_type" not in annotations.columns:
            raise ValueError("annotations does not contain cell_type")
        mask &= annotations["cell_type"].astype(str).str.lower().eq(cell_type.lower())

    return set(annotations.loc[mask, "root_id"].map(int).tolist())


def normalize_edges(edges: pd.DataFrame, schema: EdgeSchema) -> pd.DataFrame:
    required = [schema.pre_col, schema.post_col, schema.weight_col]
    missing = [c for c in required if c not in edges.columns]
    if missing:
        raise ValueError(f"Connectivity file is missing columns {missing}. Columns: {list(edges.columns)}")

    edges = edges.loc[:, required].copy()
    edges.columns = ["source", "target", "weight"]

    edges["source"] = pd.to_numeric(edges["source"], errors="coerce")
    edges["target"] = pd.to_numeric(edges["target"], errors="coerce")
    edges["weight"] = pd.to_numeric(edges["weight"], errors="coerce")

    edges = edges.dropna(subset=["source", "target", "weight"])
    edges = edges[edges["weight"] > 0]

    edges["source"] = edges["source"].astype("int64").map(int)
    edges["target"] = edges["target"].astype("int64").map(int)
    edges["weight"] = edges["weight"].astype(float)

    # Collapse duplicate directed edges by summing synaptic weights.
    edges = edges.groupby(["source", "target"], as_index=False)["weight"].sum()
    edges["distance"] = 1.0 / edges["weight"].clip(lower=1e-12)

    return edges


def load_edges(path: str | Path, schema: Optional[EdgeSchema] = None) -> tuple[pd.DataFrame, EdgeSchema]:
    path = resolve_existing_path(path, "connectivity file")
    raw_edges = pd.read_parquet(path)
    if schema is None:
        schema = infer_edge_schema(raw_edges.columns)
    return normalize_edges(raw_edges, schema), schema


def build_graph(edges: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    for row in edges.itertuples(index=False):
        G.add_edge(int(row.source), int(row.target), weight=float(row.weight), distance=float(row.distance))
    return G


def compute_strength_metrics(G: nx.DiGraph) -> pd.DataFrame:
    n = max(1, G.number_of_nodes() - 1)
    rows = []
    for node in G.nodes:
        in_strength = float(sum(data.get("weight", 1.0) for _, _, data in G.in_edges(node, data=True)))
        out_strength = float(sum(data.get("weight", 1.0) for _, _, data in G.out_edges(node, data=True)))
        total_strength = in_strength + out_strength
        rows.append(
            {
                "neuron_id": int(node),
                "in_strength": in_strength,
                "out_strength": out_strength,
                "total_strength": total_strength,
                "weighted_degree_centrality": total_strength / n,
                "weighted_in_degree_centrality": in_strength / n,
                "weighted_out_degree_centrality": out_strength / n,
            }
        )
    return pd.DataFrame(rows)


def count_reachable_pairs(G: nx.DiGraph, sources: list[int], targets: list[int]) -> tuple[int, int]:
    target_set = set(targets)
    total_pairs = len(sources) * len(targets)
    reachable = 0
    for s in sources:
        if s not in G:
            continue
        seen = nx.descendants(G, s)
        reachable += len(seen & target_set)
    return reachable, total_pairs


def compute_source_target_betweenness(
    G: nx.DiGraph,
    sources: list[int],
    targets: list[int],
    weight: Optional[str] = "distance",
    normalized: bool = True,
) -> dict[int, float]:
    """
    Compute source-target betweenness on directed paths from sources to targets.

    This is a task-specific centrality metric. It asks whether a node lies on
    shortest paths from sugar input neurons to motor-output neurons, rather than
    whether that node is globally central across the whole brain.
    """
    return nx.betweenness_centrality_subset(
        G,
        sources=sources,
        targets=targets,
        normalized=normalized,
        weight=weight,
    )


def annotate_node_metrics(metrics: pd.DataFrame, annotations: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["root_id", "super_class", "cell_class", "cell_type", "hemibrain_type", "top_nt"] if c in annotations.columns]
    return metrics.merge(
        annotations.loc[:, cols].drop_duplicates("root_id"),
        left_on="neuron_id",
        right_on="root_id",
        how="left",
    )


def summarize_groups(metrics: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    metric_cols = [
        "source_target_betweenness",
        "in_strength",
        "out_strength",
        "total_strength",
        "weighted_degree_centrality",
    ]
    for group_col in group_cols:
        if group_col not in metrics.columns:
            continue
        grouped = metrics.groupby(group_col, dropna=False)
        for name, g in grouped:
            row = {"group_column": group_col, "group": name, "n": len(g)}
            for m in metric_cols:
                if m in g.columns:
                    row[f"{m}_mean"] = float(g[m].mean())
                    row[f"{m}_sum"] = float(g[m].sum())
                    row[f"{m}_median"] = float(g[m].median())
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["group_column", "source_target_betweenness_sum"], ascending=[True, False])


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
    """
    Sample controls that match the degree-bin distribution of the actual target set.
    Falls back to replacement when a bin is sparse.
    """
    sampled_parts = []
    actual_bins = actual[bin_col].value_counts().sort_index()

    # Scale the bin counts if actual has more/fewer rows than requested sample_size.
    proportions = actual_bins / actual_bins.sum()
    desired = np.floor(proportions * sample_size).astype(int)
    remainder = sample_size - int(desired.sum())
    if remainder > 0:
        fractional = (proportions * sample_size) - desired
        for b in fractional.sort_values(ascending=False).index[:remainder]:
            desired.loc[b] += 1

    for b, n in desired.items():
        if n <= 0:
            continue
        candidates = pool[pool[bin_col] == b]
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
    return {"p_greater": p_greater, "p_less": p_less, "p_two_sided": p_two_sided}


def run_degree_matched_null(
    metrics: pd.DataFrame,
    focus_ids: set[int],
    null_pool_ids: set[int],
    *,
    sample_size: int = 1500,
    n_bootstrap: int = 1000,
    match_metric: str = "total_strength",
    n_bins: int = 10,
    metrics_to_test: tuple[str, ...] = ("source_target_betweenness", "weighted_degree_centrality", "total_strength"),
    statistics: tuple[str, ...] = ("mean", "sum"),
    seed: int = 7,
    alpha: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    if sample_size <= 0:
        sample_size = len(actual_all)

    if len(actual_all) >= sample_size:
        actual = actual_all.sample(n=sample_size, random_state=seed)
    else:
        actual = actual_all.copy()
        print(f"WARNING: requested sample_size={sample_size}, but only {len(actual)} focus neurons are available.")
        sample_size = len(actual)

    null_rows = []
    for b in range(n_bootstrap):
        sample = degree_matched_sample(rng, actual=actual, pool=pool, bin_col="degree_bin", sample_size=sample_size)
        row = {"bootstrap": b}
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
            if stat == "mean":
                actual_value = float(actual_values.mean())
            elif stat == "sum":
                actual_value = float(actual_values.sum())
            else:
                raise ValueError(f"Unsupported statistic: {stat}")

            null_values = null_dist[col].to_numpy(dtype=float)
            p = empirical_p_values(null_values, actual_value)
            null_mean = float(np.mean(null_values))
            null_std = float(np.std(null_values, ddof=1)) if len(null_values) > 1 else np.nan
            z = (actual_value - null_mean) / null_std if null_std and not math.isclose(null_std, 0.0) else np.nan
            percentile = float(np.mean(null_values <= actual_value) * 100.0)

            result_rows.append(
                {
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
                    "n_focus_available": len(actual_all),
                    "n_focus_tested": len(actual),
                    "n_null_pool": len(pool),
                    "n_bootstrap": n_bootstrap,
                    "match_metric": match_metric,
                }
            )

    results = pd.DataFrame(result_rows)
    if not results.empty:
        for p_col in ["p_greater", "p_two_sided"]:
            valid = results[p_col].notna()
            q_col = p_col.replace("p_", "q_") + "_bh"
            sig_col = p_col.replace("p_", "significant_") + "_bh"
            results[q_col] = np.nan
            results[sig_col] = False
            if valid.any():
                reject, qvals, _, _ = multipletests(results.loc[valid, p_col], alpha=alpha, method="fdr_bh")
                results.loc[valid, q_col] = qvals
                results.loc[valid, sig_col] = reject

    return results, null_dist


def generate_mock_data(output_dir: Path) -> tuple[Path, Path]:
    rng = np.random.default_rng(7)
    output_dir.mkdir(parents=True, exist_ok=True)

    n = 300
    ids = np.arange(10_000, 10_000 + n, dtype=np.int64)
    classes = np.array(["central"] * n, dtype=object)
    classes[:10] = "sensory"
    classes[10:30] = "AN"
    classes[30:45] = "motor"
    super_classes = np.array(["central"] * n, dtype=object)
    super_classes[:10] = "sensory"
    super_classes[10:30] = "ascending"
    super_classes[30:45] = "motor"

    annotations = pd.DataFrame(
        {
            "root_id": ids,
            "super_class": super_classes,
            "cell_class": classes,
            "cell_type": classes,
        }
    )
    ann_path = output_dir / "mock_annotations.tsv"
    annotations.to_csv(ann_path, sep="\t", index=False)

    edges = []
    for _ in range(1800):
        u = int(rng.choice(ids))
        v = int(rng.choice(ids))
        if u != v:
            edges.append((u, v, int(rng.integers(1, 8))))

    # Enrich AN nodes on source-to-motor paths in mock data.
    for s in ids[:10]:
        for a in ids[10:30]:
            if rng.random() < 0.12:
                edges.append((int(s), int(a), 10))
        for t in ids[30:45]:
            a = int(rng.choice(ids[10:30]))
            edges.append((a, int(t), 12))

    con = pd.DataFrame(edges, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity"])
    con_path = output_dir / "mock_connectivity.parquet"
    con.to_parquet(con_path, index=False)
    return con_path, ann_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task-specific source-to-target pathway analysis.")
    parser.add_argument("--connectivity", default="2023_03_23_connectivity_630_final.parquet")
    parser.add_argument("--annotations", default="flywire_annotations.tsv")
    parser.add_argument("--output-dir", default="results/path_analysis")

    parser.add_argument("--pre-col", default=None)
    parser.add_argument("--post-col", default=None)
    parser.add_argument("--weight-col", default=None)

    parser.add_argument("--source-ids", nargs="*", type=int, default=None, help="Explicit source/root IDs.")
    parser.add_argument("--source-ids-file", default=None, help="Text file containing source/root IDs.")
    parser.add_argument("--source-cell-class", default=None)
    parser.add_argument("--source-super-class", default=None)
    parser.add_argument("--source-cell-type", default=None)

    parser.add_argument("--target-ids", nargs="*", type=int, default=None, help="Explicit target/root IDs.")
    parser.add_argument("--target-ids-file", default=None, help="Text file containing target/root IDs.")
    parser.add_argument("--target-cell-class", default=None)
    parser.add_argument("--target-super-class", default="motor", help="Default is all motor neurons.")
    parser.add_argument("--target-cell-type", default=None)

    parser.add_argument("--focus-cell-class", default="AN")
    parser.add_argument("--focus-super-class", default=None)
    parser.add_argument("--focus-cell-type", default=None)

    parser.add_argument("--null-pool", choices=["central", "global", "same_super_class"], default="central")
    parser.add_argument("--sample-size", type=int, default=1500)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--n-bins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--match-metric", default="total_strength")
    parser.add_argument("--unweighted", action="store_true", help="Use unweighted shortest paths instead of distance=1/Connectivity.")

    parser.add_argument("--mock", action="store_true", help="Run a small mock-data sanity check.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mock:
        mock_dir = output_dir / "mock_inputs"
        con_path, ann_path = generate_mock_data(mock_dir)
        args.connectivity = str(con_path)
        args.annotations = str(ann_path)
        args.source_ids = list(range(10_000, 10_010))
        args.target_super_class = "motor"
        print(f"Running mock analysis with {con_path} and {ann_path}")

    con_path = resolve_existing_path(args.connectivity, "connectivity file")
    ann_path = resolve_existing_path(args.annotations, "annotations file")

    print("Loading annotations...")
    annotations = load_annotations(ann_path)

    print("Loading connectivity and building graph...")
    raw_edges = pd.read_parquet(con_path)
    schema = infer_edge_schema(
        raw_edges.columns,
        pre_col=args.pre_col,
        post_col=args.post_col,
        weight_col=args.weight_col,
    )
    print(f"Connectivity schema: {schema}")
    edges = normalize_edges(raw_edges, schema)
    del raw_edges
    G = build_graph(edges)
    print(f"Graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} directed weighted edges")

    # Select source neurons.
    if args.source_ids_file:
        source_ids = set(parse_id_file(args.source_ids_file))
    elif args.source_ids:
        source_ids = set(map(int, args.source_ids))
    elif args.source_cell_class or args.source_super_class or args.source_cell_type:
        source_ids = select_by_annotation(
            annotations,
            cell_class=args.source_cell_class,
            super_class=args.source_super_class,
            cell_type=args.source_cell_type,
        )
    else:
        source_ids = set(DEFAULT_SUGAR_IDS)

    # Select target neurons.
    if args.target_ids_file:
        target_ids = set(parse_id_file(args.target_ids_file))
    elif args.target_ids:
        target_ids = set(map(int, args.target_ids))
    else:
        target_ids = select_by_annotation(
            annotations,
            cell_class=args.target_cell_class,
            super_class=args.target_super_class,
            cell_type=args.target_cell_type,
        )

    # Select focus neurons, usually AN.
    focus_ids = select_by_annotation(
        annotations,
        cell_class=args.focus_cell_class,
        super_class=args.focus_super_class,
        cell_type=args.focus_cell_type,
    )
    if not focus_ids and args.focus_cell_class == "AN":
        print("No cell_class == 'AN' neurons found; falling back to super_class == 'ascending'.")
        focus_ids = select_by_annotation(annotations, super_class="ascending")

    sources = sorted(int(n) for n in source_ids if n in G)
    targets = sorted(int(n) for n in target_ids if n in G)
    focus_nodes = sorted(int(n) for n in focus_ids if n in G)

    print(f"Sources found in graph: {len(sources):,} / {len(source_ids):,}")
    print(f"Targets found in graph: {len(targets):,} / {len(target_ids):,}")
    print(f"Focus neurons found in graph: {len(focus_nodes):,} / {len(focus_ids):,}")

    if not sources:
        raise ValueError("No source neurons are present in the graph. Check source IDs/classes.")
    if not targets:
        raise ValueError("No target neurons are present in the graph. Check target IDs/classes.")
    if not focus_nodes:
        raise ValueError("No focus neurons are present in the graph. Check AN/ascending labels.")

    reachable, total_pairs = count_reachable_pairs(G, sources, targets)
    print(f"Reachable source-target pairs: {reachable:,} / {total_pairs:,}")

    print("Computing task-specific source-target betweenness...")
    weight_key = None if args.unweighted else "distance"
    st_btw = compute_source_target_betweenness(G, sources, targets, weight=weight_key, normalized=True)

    metrics = compute_strength_metrics(G)
    metrics["source_target_betweenness"] = metrics["neuron_id"].map(st_btw).fillna(0.0)
    metrics["is_source"] = metrics["neuron_id"].isin(sources)
    metrics["is_target"] = metrics["neuron_id"].isin(targets)
    metrics["is_focus"] = metrics["neuron_id"].isin(focus_nodes)
    metrics = annotate_node_metrics(metrics, annotations)

    node_path = output_dir / "path_node_metrics.csv"
    metrics.to_csv(node_path, index=False)

    summary = summarize_groups(metrics, ["super_class", "cell_class", "cell_type"])
    summary_path = output_dir / "path_group_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Define null pool.
    if args.null_pool == "central":
        null_ids = select_by_annotation(annotations, super_class="central")
    elif args.null_pool == "same_super_class":
        if args.focus_super_class:
            null_ids = select_by_annotation(annotations, super_class=args.focus_super_class)
        else:
            null_ids = select_by_annotation(annotations, super_class="ascending")
    else:
        null_ids = set(G.nodes())

    null_ids = set(int(n) for n in null_ids if n in G)
    print(f"Null pool '{args.null_pool}' neurons in graph: {len(null_ids):,}")

    print("Running degree-matched null model for task-specific metrics...")
    null_results, null_dist = run_degree_matched_null(
        metrics=metrics,
        focus_ids=set(focus_nodes),
        null_pool_ids=null_ids,
        sample_size=args.sample_size,
        n_bootstrap=args.n_bootstrap,
        match_metric=args.match_metric,
        n_bins=args.n_bins,
        seed=args.seed,
        alpha=args.alpha,
    )

    null_results_path = output_dir / "path_degree_matched_null_results.csv"
    null_dist_path = output_dir / "path_degree_matched_null_distribution.csv"
    null_results.to_csv(null_results_path, index=False)
    null_dist.to_csv(null_dist_path, index=False)

    run_info = pd.DataFrame(
        [
            {
                "connectivity_path": str(con_path),
                "annotations_path": str(ann_path),
                "schema_pre_col": schema.pre_col,
                "schema_post_col": schema.post_col,
                "schema_weight_col": schema.weight_col,
                "n_graph_nodes": G.number_of_nodes(),
                "n_graph_edges": G.number_of_edges(),
                "n_sources": len(sources),
                "n_targets": len(targets),
                "n_focus": len(focus_nodes),
                "reachable_source_target_pairs": reachable,
                "total_source_target_pairs": total_pairs,
                "weighted_paths": not args.unweighted,
                "sample_size": args.sample_size,
                "n_bootstrap": args.n_bootstrap,
                "null_pool": args.null_pool,
            }
        ]
    )
    run_info.to_csv(output_dir / "path_analysis_run_info.csv", index=False)

    print("\nPathway analysis complete.")
    print(f"Node metrics:       {node_path}")
    print(f"Group summary:      {summary_path}")
    print(f"Null results:       {null_results_path}")
    print(f"Null distribution:  {null_dist_path}")
    print("\nTop null-model tests:")
    print(
        null_results.sort_values("q_greater_bh")[[
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
        ]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
