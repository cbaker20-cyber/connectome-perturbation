"""
graph_analysis.py

Graph-theory expansion for the connectome-perturbation project.

Purpose
-------
1. Load the FlyWire connectivity parquet file and build a directed weighted graph.
2. Compute weighted degree/strength and approximate weighted betweenness centrality.
3. Compare the Ascending Neuron / AN population against other classes.
4. Run a degree-matched bootstrap null model to test whether AN centrality is
   larger than expected from similarly connected neurons.

Default expected files (resolved via tools.path_resolver / data/input_manifest.json)
------------------------------------------------------------------------------------
2023_03_23_connectivity_630_final.parquet
flywire_annotations.tsv

Example usage
-------------
# Real data, AN class, central-neuron degree-matched null:
python perturbation/graph_analysis.py \
    --connectivity 2023_03_23_connectivity_630_final.parquet \
    --annotations flywire_annotations.tsv \
    --target-col cell_class \
    --target-value AN \
    --null-pool central \
    --sample-size 1500 \
    --n-bootstrap 1000 \
    --betweenness-k 1000

# Dry run with synthetic connectome data:
python perturbation/graph_analysis.py --mock --n-bootstrap 100 --betweenness-k 100
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import networkx as nx
import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.path_resolver import resolve_input

CONNECTIVITY_DEFAULT_ID = "2023_03_23_connectivity_630_final.parquet"
ANNOTATIONS_DEFAULT_ID = "flywire_annotations.tsv"
RESULTS_DEFAULT = Path("results/graph_analysis")
DEFAULT_MANIFEST = "data/input_manifest.json"


PRE_CANDIDATES = [
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
    """Column names used to interpret the connectivity table."""

    pre_col: str
    post_col: str
    weight_col: str


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    """Return the first candidate that exists in columns."""
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def infer_connectivity_schema(
    columns: Iterable[str],
    pre_col: Optional[str] = None,
    post_col: Optional[str] = None,
    weight_col: Optional[str] = None,
) -> EdgeSchema:
    """
    Infer source, target, and synaptic-weight columns.

    The FlyWire model file is expected to contain one presynaptic neuron column,
    one postsynaptic neuron column, and one synaptic count/weight column. This
    function accepts explicit column names, but can also infer common names.
    """
    columns = list(columns)

    pre = pre_col or first_existing(columns, PRE_CANDIDATES)
    post = post_col or first_existing(columns, POST_CANDIDATES)
    weight = weight_col or first_existing(columns, WEIGHT_CANDIDATES)

    missing = []
    if pre is None:
        missing.append("pre/source neuron column")
    if post is None:
        missing.append("post/target neuron column")
    if weight is None:
        missing.append("synaptic weight column")

    if missing:
        raise ValueError(
            "Could not infer connectivity schema. Missing: "
            + ", ".join(missing)
            + f". Available columns: {columns}"
        )

    return EdgeSchema(pre_col=pre, post_col=post, weight_col=weight)


def parquet_columns(path: Path) -> list[str]:
    """Read parquet schema without loading the full file when pyarrow is present."""
    try:
        import pyarrow.parquet as pq

        return list(pq.ParquetFile(path).schema.names)
    except Exception:
        # Fallback: load one row through pandas.
        return list(pd.read_parquet(path).head(1).columns)


def load_connectivity(
    path: Path,
    pre_col: Optional[str] = None,
    post_col: Optional[str] = None,
    weight_col: Optional[str] = None,
) -> tuple[pd.DataFrame, EdgeSchema]:
    """
    Load only the columns required to build the graph.

    Returns a compact table with columns:
        pre_col, post_col, weight_col
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Connectivity parquet not found: {path}")

    columns = parquet_columns(path)
    schema = infer_connectivity_schema(columns, pre_col, post_col, weight_col)

    edges = pd.read_parquet(
        path,
        columns=[schema.pre_col, schema.post_col, schema.weight_col],
    )

    edges = edges.dropna(subset=[schema.pre_col, schema.post_col, schema.weight_col])
    edges[schema.weight_col] = pd.to_numeric(edges[schema.weight_col], errors="coerce")
    edges = edges.dropna(subset=[schema.weight_col])
    edges = edges[edges[schema.weight_col] > 0]

    return edges, schema


def load_annotations(path: Path) -> pd.DataFrame:
    """Load FlyWire annotations with root_id and cell metadata."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Annotation TSV not found: {path}")

    ann = pd.read_csv(path, sep="\t", low_memory=False)

    if "root_id" not in ann.columns:
        raise ValueError("Annotation table must contain a 'root_id' column.")

    ann = ann.dropna(subset=["root_id"]).drop_duplicates("root_id")
    return ann


def build_directed_weighted_graph(edges: pd.DataFrame, schema: EdgeSchema) -> nx.DiGraph:
    """
    Build a directed weighted graph from a synapse table.

    Edge interpretation:
        u -> v means presynaptic neuron u synapses onto postsynaptic neuron v.

    Edge attributes:
        weight: summed synapse count / synaptic strength
        distance: inverse weight, used for weighted shortest-path betweenness
    """
    grouped = (
        edges.groupby([schema.pre_col, schema.post_col], as_index=False)[schema.weight_col]
        .sum()
        .rename(
            columns={
                schema.pre_col: "source",
                schema.post_col: "target",
                schema.weight_col: "weight",
            }
        )
    )

    graph = nx.from_pandas_edgelist(
        grouped,
        source="source",
        target="target",
        edge_attr="weight",
        create_using=nx.DiGraph(),
    )

    for _, _, data in graph.edges(data=True):
        weight = max(float(data.get("weight", 1.0)), 1e-12)
        data["weight"] = weight
        # NetworkX treats smaller distance as a stronger/shorter connection.
        data["distance"] = 1.0 / weight

    return graph


def compute_weighted_degree_metrics(graph: nx.DiGraph) -> pd.DataFrame:
    """
    Compute weighted in-strength, out-strength, total strength, and normalized
    weighted degree centrality.

    NetworkX degree(weight='weight') gives raw weighted degree/strength. This
    script also reports a normalized value divided by n - 1 so graphs of
    different sizes are easier to compare.
    """
    n = max(graph.number_of_nodes(), 1)
    denom = max(n - 1, 1)

    node_ids = list(graph.nodes())

    in_strength = dict(graph.in_degree(weight="weight"))
    out_strength = dict(graph.out_degree(weight="weight"))
    total_strength = dict(graph.degree(weight="weight"))
    unweighted_degree = dict(graph.degree())

    metrics = pd.DataFrame(
        {
            "root_id": node_ids,
            "in_strength": [float(in_strength.get(node, 0.0)) for node in node_ids],
            "out_strength": [float(out_strength.get(node, 0.0)) for node in node_ids],
            "total_strength": [float(total_strength.get(node, 0.0)) for node in node_ids],
            "unweighted_degree": [int(unweighted_degree.get(node, 0)) for node in node_ids],
        }
    )

    metrics["weighted_degree_centrality"] = metrics["total_strength"] / denom
    metrics["weighted_in_degree_centrality"] = metrics["in_strength"] / denom
    metrics["weighted_out_degree_centrality"] = metrics["out_strength"] / denom

    return metrics


def compute_betweenness_metrics(
    graph: nx.DiGraph,
    k: Optional[int] = 1000,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Compute weighted betweenness centrality.

    For large connectomes, exact betweenness is often too slow. If k is given and
    k < number of nodes, NetworkX uses approximate betweenness using k sampled
    source nodes. Edge distance is inverse synaptic weight.
    """
    n = graph.number_of_nodes()

    if k is not None and k >= n:
        k = None

    print(
        f"Computing {'exact' if k is None else f'approximate k={k}'} "
        f"weighted betweenness centrality on {n:,} nodes..."
    )

    bet = nx.betweenness_centrality(
        graph,
        k=k,
        normalized=True,
        weight="distance",
        seed=seed,
    )

    return pd.DataFrame(
        {
            "root_id": list(bet.keys()),
            "betweenness_centrality": list(bet.values()),
        }
    )


def attach_annotations(metrics: pd.DataFrame, annotations: pd.DataFrame) -> pd.DataFrame:
    """Merge node metrics with annotation metadata."""
    cols_to_keep = [
        col
        for col in [
            "root_id",
            "super_class",
            "cell_class",
            "cell_sub_class",
            "supertype",
            "cell_type",
            "top_nt",
            "side",
            "flow",
        ]
        if col in annotations.columns
    ]

    out = metrics.merge(annotations[cols_to_keep], on="root_id", how="left")

    for col in ["super_class", "cell_class", "cell_type"]:
        if col in out.columns:
            out[col] = out[col].fillna("unannotated")

    return out


def summarize_by_group(metrics: pd.DataFrame, group_col: str = "super_class") -> pd.DataFrame:
    """
    Summarize centrality and strength metrics by annotation group.
    """
    if group_col not in metrics.columns:
        raise ValueError(f"'{group_col}' does not exist in metrics table.")

    numeric_cols = [
        "in_strength",
        "out_strength",
        "total_strength",
        "weighted_degree_centrality",
        "weighted_in_degree_centrality",
        "weighted_out_degree_centrality",
        "betweenness_centrality",
    ]
    numeric_cols = [col for col in numeric_cols if col in metrics.columns]

    agg = metrics.groupby(group_col)[numeric_cols].agg(["count", "mean", "median", "sum"])
    agg.columns = [f"{metric}_{stat}" for metric, stat in agg.columns]
    agg = agg.sort_values("betweenness_centrality_mean", ascending=False)
    return agg


def get_target_nodes(
    metrics: pd.DataFrame,
    target_col: str = "cell_class",
    target_value: str = "AN",
    fallback_col: str = "super_class",
    fallback_value: str = "ascending",
) -> pd.Index:
    """
    Select target nodes. By default, use cell_class == 'AN'. If no AN labels are
    found, fall back to super_class == 'ascending'.
    """
    if target_col in metrics.columns:
        nodes = metrics.loc[metrics[target_col].astype(str) == target_value, "root_id"]
        if len(nodes) > 0:
            return pd.Index(nodes.dropna().unique())

    warnings.warn(
        f"No nodes found for {target_col} == {target_value!r}; "
        f"falling back to {fallback_col} == {fallback_value!r}."
    )

    if fallback_col not in metrics.columns:
        raise ValueError(
            f"Neither target column '{target_col}' nor fallback column "
            f"'{fallback_col}' exists."
        )

    nodes = metrics.loc[metrics[fallback_col].astype(str) == fallback_value, "root_id"]
    return pd.Index(nodes.dropna().unique())


def get_null_pool(
    metrics: pd.DataFrame,
    null_pool: str = "central",
    target_nodes: Optional[Iterable] = None,
) -> pd.Index:
    """
    Select the bootstrap pool.

    null_pool options:
        - 'central': nodes with super_class == 'central'
        - 'global': all annotated/non-target graph nodes
        - any other string: treated as a super_class value
    """
    target_set = set([] if target_nodes is None else target_nodes)

    if null_pool == "global":
        pool = metrics.loc[~metrics["root_id"].isin(target_set), "root_id"]
    else:
        if "super_class" not in metrics.columns:
            raise ValueError("super_class column is required for non-global null pools.")
        pool = metrics.loc[
            (metrics["super_class"].astype(str) == null_pool)
            & (~metrics["root_id"].isin(target_set)),
            "root_id",
        ]

    return pd.Index(pool.dropna().unique())


def group_statistic(sample: pd.DataFrame, metric: str, statistic: str = "mean") -> float:
    """Compute one group-level centrality statistic."""
    values = sample[metric].to_numpy(dtype=float)

    if len(values) == 0:
        return np.nan

    if statistic == "mean":
        return float(np.mean(values))
    if statistic == "median":
        return float(np.median(values))
    if statistic == "sum":
        return float(np.sum(values))
    if statistic == "max":
        return float(np.max(values))

    raise ValueError("statistic must be one of: mean, median, sum, max")


def make_degree_bins(
    metrics: pd.DataFrame,
    nodes: Iterable,
    match_metric: str = "total_strength",
    n_bins: int = 20,
) -> pd.Series:
    """
    Assign nodes to quantile bins based on log-transformed degree/strength.

    Log-transforming prevents a few giant hub neurons from dominating binning.
    """
    sub = metrics.loc[metrics["root_id"].isin(nodes), ["root_id", match_metric]].copy()
    sub["match_value"] = np.log1p(pd.to_numeric(sub[match_metric], errors="coerce").fillna(0))

    n_unique = sub["match_value"].nunique()
    q = int(min(n_bins, max(n_unique, 1)))

    if q <= 1:
        sub["degree_bin"] = 0
    else:
        # Rank first so qcut can handle repeated strength values.
        sub["degree_bin"] = pd.qcut(
            sub["match_value"].rank(method="first"),
            q=q,
            labels=False,
            duplicates="drop",
        ).astype(int)

    return sub.set_index("root_id")["degree_bin"]


def degree_matched_sample(
    rng: np.random.Generator,
    metrics: pd.DataFrame,
    target_nodes: Iterable,
    pool_nodes: Iterable,
    sample_size: int,
    match_metric: str = "total_strength",
    n_bins: int = 20,
) -> np.ndarray:
    """
    Draw a bootstrap sample from the null pool with a degree distribution matched
    to the target neurons.

    For each degree/strength bin, the function samples the same number of null
    neurons as the target group has in that bin. If a bin has too few available
    null neurons, sampling uses replacement for that bin.
    """
    target_nodes = pd.Index(target_nodes)
    pool_nodes = pd.Index(pool_nodes)

    if len(target_nodes) == 0:
        raise ValueError("No target nodes available for degree matching.")
    if len(pool_nodes) == 0:
        raise ValueError("No null-pool nodes available for degree matching.")

    if len(target_nodes) > sample_size:
        target_nodes = pd.Index(rng.choice(target_nodes.to_numpy(), size=sample_size, replace=False))
    else:
        sample_size = len(target_nodes)

    combined_nodes = target_nodes.union(pool_nodes)
    bins = make_degree_bins(metrics, combined_nodes, match_metric=match_metric, n_bins=n_bins)

    target_bins = bins.loc[target_nodes].value_counts().sort_index()

    chosen = []
    pool_bins = bins.loc[pool_nodes]

    for degree_bin, count in target_bins.items():
        candidates = pool_bins.index[pool_bins == degree_bin].to_numpy()

        if len(candidates) == 0:
            # If the null pool lacks this exact degree bin, fall back to global
            # pool sampling for this bin. This should be rare with enough bins.
            candidates = pool_nodes.to_numpy()

        replace = len(candidates) < count
        draw = rng.choice(candidates, size=int(count), replace=replace)
        chosen.append(draw)

    sampled = np.concatenate(chosen)

    if len(sampled) > sample_size:
        sampled = rng.choice(sampled, size=sample_size, replace=False)

    return sampled


def bootstrap_degree_matched_null(
    metrics: pd.DataFrame,
    target_nodes: Iterable,
    pool_nodes: Iterable,
    sample_size: int = 1500,
    n_bootstrap: int = 1000,
    metric: str = "betweenness_centrality",
    statistic: str = "mean",
    match_metric: str = "total_strength",
    n_bins: int = 20,
    seed: int = 0,
) -> tuple[pd.DataFrame, dict]:
    """
    Run a degree-matched bootstrap/permutation null model.

    Returns:
        null_distribution_df, result_dict
    """
    rng = np.random.default_rng(seed)

    target_nodes = pd.Index(target_nodes)
    pool_nodes = pd.Index(pool_nodes)

    if len(target_nodes) > sample_size:
        actual_nodes = pd.Index(rng.choice(target_nodes.to_numpy(), size=sample_size, replace=False))
    else:
        actual_nodes = target_nodes
        sample_size = len(actual_nodes)

    actual_df = metrics.loc[metrics["root_id"].isin(actual_nodes)]
    actual_value = group_statistic(actual_df, metric=metric, statistic=statistic)

    null_values = np.empty(n_bootstrap, dtype=float)

    for i in range(n_bootstrap):
        sampled_nodes = degree_matched_sample(
            rng=rng,
            metrics=metrics,
            target_nodes=actual_nodes,
            pool_nodes=pool_nodes,
            sample_size=sample_size,
            match_metric=match_metric,
            n_bins=n_bins,
        )
        sample_df = metrics.loc[metrics["root_id"].isin(sampled_nodes)]
        null_values[i] = group_statistic(sample_df, metric=metric, statistic=statistic)

    # Empirical p-values with +1 correction to avoid returning p=0.
    p_greater = (np.sum(null_values >= actual_value) + 1) / (n_bootstrap + 1)
    p_less = (np.sum(null_values <= actual_value) + 1) / (n_bootstrap + 1)
    p_two_sided = min(1.0, 2.0 * min(p_greater, p_less))

    null_mean = float(np.mean(null_values))
    null_std = float(np.std(null_values, ddof=1)) if n_bootstrap > 1 else np.nan
    z_score = float((actual_value - null_mean) / null_std) if null_std > 0 else np.nan
    percentile = float(np.mean(null_values <= actual_value) * 100.0)

    result = {
        "metric": metric,
        "statistic": statistic,
        "match_metric": match_metric,
        "sample_size": int(sample_size),
        "n_bootstrap": int(n_bootstrap),
        "actual_value": float(actual_value),
        "null_mean": null_mean,
        "null_std": null_std,
        "z_score": z_score,
        "percentile_vs_null": percentile,
        "p_greater": float(p_greater),
        "p_less": float(p_less),
        "p_two_sided": float(p_two_sided),
    }

    null_df = pd.DataFrame(
        {
            "bootstrap_iteration": np.arange(n_bootstrap),
            f"null_{metric}_{statistic}": null_values,
        }
    )

    return null_df, result


def generate_mock_data(
    n_nodes: int = 5000,
    n_edges: int = 50000,
    seed: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame, EdgeSchema]:
    """
    Generate synthetic annotations and connectivity for dry runs.

    The mock data intentionally gives AN/ascending neurons elevated bridge-like
    connectivity so the null-model code has a signal to detect.
    """
    rng = np.random.default_rng(seed)
    root_ids = np.arange(1, n_nodes + 1, dtype=np.int64)

    super_classes = rng.choice(
        ["central", "ascending", "descending", "sensory", "motor", "optic", "visual_projection"],
        size=n_nodes,
        p=[0.55, 0.30, 0.05, 0.03, 0.02, 0.03, 0.02],
    )

    cell_classes = np.full(n_nodes, "other", dtype=object)
    ascending_mask = super_classes == "ascending"
    cell_classes[ascending_mask] = rng.choice(
        ["AN", "other_ascending"],
        size=int(ascending_mask.sum()),
        p=[0.80, 0.20],
    )

    annotations = pd.DataFrame(
        {
            "root_id": root_ids,
            "super_class": super_classes,
            "cell_class": cell_classes,
            "cell_type": cell_classes,
        }
    )

    central_nodes = root_ids[super_classes == "central"]
    sensory_nodes = root_ids[super_classes == "sensory"]
    motor_nodes = root_ids[super_classes == "motor"]
    an_nodes = root_ids[cell_classes == "AN"]
    all_nodes = root_ids

    # Background random edges.
    pre = rng.choice(all_nodes, size=n_edges, replace=True)
    post = rng.choice(all_nodes, size=n_edges, replace=True)
    weights = rng.poisson(2.0, size=n_edges) + 1

    # Add bridge-like sensory -> AN -> motor edges.
    bridge_edges = max(1000, n_edges // 10)
    pre_bridge_1 = rng.choice(sensory_nodes if len(sensory_nodes) else all_nodes, size=bridge_edges, replace=True)
    post_bridge_1 = rng.choice(an_nodes if len(an_nodes) else all_nodes, size=bridge_edges, replace=True)
    w_bridge_1 = rng.poisson(8.0, size=bridge_edges) + 1

    pre_bridge_2 = rng.choice(an_nodes if len(an_nodes) else all_nodes, size=bridge_edges, replace=True)
    post_bridge_2 = rng.choice(motor_nodes if len(motor_nodes) else all_nodes, size=bridge_edges, replace=True)
    w_bridge_2 = rng.poisson(8.0, size=bridge_edges) + 1

    # Central pool remains large, but less bridge-specific.
    central_edges = max(1000, n_edges // 20)
    pre_central = rng.choice(central_nodes if len(central_nodes) else all_nodes, size=central_edges, replace=True)
    post_central = rng.choice(all_nodes, size=central_edges, replace=True)
    w_central = rng.poisson(3.0, size=central_edges) + 1

    edges = pd.DataFrame(
        {
            "pre_root_id": np.concatenate([pre, pre_bridge_1, pre_bridge_2, pre_central]),
            "post_root_id": np.concatenate([post, post_bridge_1, post_bridge_2, post_central]),
            "syn_count": np.concatenate([weights, w_bridge_1, w_bridge_2, w_central]),
        }
    )

    schema = EdgeSchema("pre_root_id", "post_root_id", "syn_count")
    return edges, annotations, schema


def run_graph_analysis(args: argparse.Namespace) -> None:
    """Main analysis workflow."""
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mock:
        print("Using synthetic mock connectome data.")
        edges, annotations, schema = generate_mock_data(
            n_nodes=args.mock_nodes,
            n_edges=args.mock_edges,
            seed=args.seed,
        )
    else:
        connectivity_path = resolve_input(
            args.connectivity,
            manifest_path=args.manifest,
        )
        annotations_path = resolve_input(
            args.annotations,
            manifest_path=args.manifest,
        )
        print(f"Loading connectivity from {connectivity_path}")
        edges, schema = load_connectivity(
            path=connectivity_path,
            pre_col=args.pre_col,
            post_col=args.post_col,
            weight_col=args.weight_col,
        )
        print(f"Loading annotations from {annotations_path}")
        annotations = load_annotations(annotations_path)

    print(
        f"Connectivity schema: pre={schema.pre_col!r}, "
        f"post={schema.post_col!r}, weight={schema.weight_col!r}"
    )
    print(f"Loaded {len(edges):,} raw edges and {len(annotations):,} annotated neurons.")

    graph = build_directed_weighted_graph(edges, schema)
    print(
        f"Built directed graph with {graph.number_of_nodes():,} nodes and "
        f"{graph.number_of_edges():,} weighted edges."
    )

    degree_metrics = compute_weighted_degree_metrics(graph)
    betweenness_metrics = compute_betweenness_metrics(
        graph,
        k=args.betweenness_k,
        seed=args.seed,
    )

    metrics = degree_metrics.merge(betweenness_metrics, on="root_id", how="left")
    metrics = attach_annotations(metrics, annotations)

    node_out = out_dir / "graph_node_metrics.csv"
    metrics.to_csv(node_out, index=False)
    print(f"Saved node metrics to {node_out}")

    super_summary = summarize_by_group(metrics, "super_class")
    super_out = out_dir / "graph_super_class_summary.csv"
    super_summary.to_csv(super_out)
    print(f"Saved super_class summary to {super_out}")

    if "cell_class" in metrics.columns:
        cell_summary = summarize_by_group(metrics, "cell_class")
        cell_out = out_dir / "graph_cell_class_summary.csv"
        cell_summary.to_csv(cell_out)
        print(f"Saved cell_class summary to {cell_out}")

    target_nodes = get_target_nodes(
        metrics,
        target_col=args.target_col,
        target_value=args.target_value,
        fallback_col=args.fallback_target_col,
        fallback_value=args.fallback_target_value,
    )

    pool_nodes = get_null_pool(
        metrics,
        null_pool=args.null_pool,
        target_nodes=target_nodes,
    )

    if len(target_nodes) == 0:
        raise ValueError("Target neuron set is empty; cannot run null model.")
    if len(pool_nodes) == 0:
        raise ValueError("Null pool is empty; cannot run null model.")

    print(
        f"Target neurons: {len(target_nodes):,}; null pool '{args.null_pool}': "
        f"{len(pool_nodes):,}; bootstrap sample size: {min(args.sample_size, len(target_nodes)):,}."
    )

    results = []
    null_tables = []

    for metric in args.null_metrics:
        if metric not in metrics.columns:
            raise ValueError(f"Null metric '{metric}' not found in metrics table.")

        for statistic in args.null_statistics:
            null_df, result = bootstrap_degree_matched_null(
                metrics=metrics,
                target_nodes=target_nodes,
                pool_nodes=pool_nodes,
                sample_size=args.sample_size,
                n_bootstrap=args.n_bootstrap,
                metric=metric,
                statistic=statistic,
                match_metric=args.match_metric,
                n_bins=args.n_bins,
                seed=args.seed,
            )
            result["target_col"] = args.target_col
            result["target_value"] = args.target_value
            result["null_pool"] = args.null_pool
            results.append(result)

            value_col = null_df.columns[-1]
            null_tables.append(null_df.rename(columns={value_col: f"{metric}_{statistic}"}))

            print(
                f"Null test {metric}/{statistic}: actual={result['actual_value']:.6g}, "
                f"null={result['null_mean']:.6g} ± {result['null_std']:.6g}, "
                f"z={result['z_score']:.3f}, p_greater={result['p_greater']:.4g}"
            )

    results_df = pd.DataFrame(results)
    results_out = out_dir / "degree_matched_null_results.csv"
    results_df.to_csv(results_out, index=False)
    print(f"Saved null-model results to {results_out}")

    if null_tables:
        merged_null = null_tables[0]
        for table in null_tables[1:]:
            merged_null = merged_null.merge(table, on="bootstrap_iteration", how="outer")
        null_out = out_dir / "degree_matched_null_distribution.csv"
        merged_null.to_csv(null_out, index=False)
        print(f"Saved null distributions to {null_out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Graph-theory analysis for Drosophila connectome perturbations."
    )

    parser.add_argument("--connectivity", default=CONNECTIVITY_DEFAULT_ID)
    parser.add_argument("--annotations", default=ANNOTATIONS_DEFAULT_ID)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", default=str(RESULTS_DEFAULT))

    parser.add_argument("--pre-col", default=None)
    parser.add_argument("--post-col", default=None)
    parser.add_argument("--weight-col", default=None)

    parser.add_argument("--target-col", default="cell_class")
    parser.add_argument("--target-value", default="AN")
    parser.add_argument("--fallback-target-col", default="super_class")
    parser.add_argument("--fallback-target-value", default="ascending")

    parser.add_argument(
        "--null-pool",
        default="central",
        help="Bootstrap pool: 'central', 'global', or any super_class value.",
    )
    parser.add_argument("--sample-size", type=int, default=1500)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--match-metric", default="total_strength")
    parser.add_argument("--n-bins", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)

    parser.add_argument(
        "--betweenness-k",
        type=int,
        default=1000,
        help="Approximation sample size for betweenness. Use a larger value for final runs.",
    )

    parser.add_argument(
        "--null-metrics",
        nargs="+",
        default=["betweenness_centrality", "weighted_degree_centrality", "total_strength"],
    )
    parser.add_argument(
        "--null-statistics",
        nargs="+",
        default=["mean", "sum"],
        choices=["mean", "median", "sum", "max"],
    )

    parser.add_argument("--mock", action="store_true", help="Run on synthetic mock data.")
    parser.add_argument("--mock-nodes", type=int, default=5000)
    parser.add_argument("--mock-edges", type=int, default=50000)

    return parser.parse_args()


if __name__ == "__main__":
    run_graph_analysis(parse_args())
