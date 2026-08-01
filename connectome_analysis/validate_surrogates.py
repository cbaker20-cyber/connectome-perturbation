"""Validate structural surrogates against JO ground-truth motor ΔHz drops.

Computes per-target motor population firing-rate change from Parquet spike tables,
structural surrogates (mean modal controllability and path attenuation ratio) on a
capped subgraph, Spearman/Pearson correlations, and dynamic leverage residuals.

Claim status: not_interpretable_as_neuroscience until a full provenance record
is attached. Full-graph modal/path metrics are intractable at FlyWire scale;
surrogates are evaluated on a capped subgraph around each silenced class.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from connectome_analysis.graph_surrogates import (
    CLAIM_STATUS,
    load_dense_signed_adjacency_from_edges,
    modal_controllability,
    path_attenuation_ratio,
)
from tools.path_resolver import require_repo_path, resolve_input, repo_root_from

LOGGER = logging.getLogger(__name__)

DEFAULT_RESULTS_DIR = "results/jo_ground_truth"
DEFAULT_OUTPUT = "results/jo_ground_truth/surrogate_vs_ground_truth.csv"
DEFAULT_CONNECTIVITY_ID = "2023_03_23_connectivity_630_final.parquet"
DEFAULT_ANNOTATIONS_ID = "flywire_annotations.tsv"
DEFAULT_COMPLETENESS_ID = "2023_03_23_completeness_630_final.csv"
DEFAULT_MANIFEST = "data/input_manifest.json"
DEFAULT_JO_CONFIG = "configs/jo_ground_truth_30trial.yaml"
DEFAULT_MAX_SUBGRAPH_NODES = 800
DEFAULT_GAMMA = 0.8
DEFAULT_MAX_PATH_LENGTH = 4
EPS = 1e-12

TARGET_CLASSES = ["AN", "descending", "LO", "Kenyon_Cell", "motor"]

# Required output schema (exactly 13 columns).
OUTPUT_COLUMNS = [
    "target_class",
    "n_silenced",
    "delta_hz_obs",
    "mean_modal_controllability",
    "path_attenuation_ratio",
    "y_hat_struct",
    "delta_leverage",
    "spearman_rs",
    "pearson_r",
    "spearman_p",
    "pearson_p",
    "commit_sha",
    "random_seed",
]


def _setup_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )


def resolve_repo_input(identifier: str, *, manifest_path: str = DEFAULT_MANIFEST, repo_root: Path | None = None) -> Path:
    """Resolve any repo-relative input through ``resolve_input``."""
    return resolve_input(identifier, manifest_path=manifest_path, repo_root=repo_root)


def load_output_manifest(results_dir_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    path = resolve_repo_input(f"{results_dir_id.rstrip('/')}/output_manifest.json", repo_root=repo_root)
    return json.loads(path.read_text(encoding="utf-8"))


def extract_provenance(manifest: dict[str, Any]) -> tuple[str, int]:
    """Return ``(commit_sha, random_seed)`` from an output manifest."""
    raw_commit = (
        manifest.get("repo_commit")
        or manifest.get("commit_sha")
        or manifest.get("git_commit")
        or manifest.get("commit")
        or ""
    )
    commit_sha = str(raw_commit)[:7] if raw_commit else ""
    seed = manifest.get("random_seed")
    if seed is None:
        seed = (manifest.get("simulation") or {}).get("random_seed", 42)
    return commit_sha, int(seed)


def resolve_baseline_exp_name(manifest: dict[str, Any], *, fallback: str = "baseline_jo") -> str:
    """Read baseline parquet stem from an output manifest (top-level or simulation)."""
    name = manifest.get("baseline_exp_name")
    if name:
        return str(name)
    sim = manifest.get("simulation") or {}
    name = sim.get("baseline_exp_name")
    if name:
        return str(name)
    return fallback


def load_spike_table(parquet_id: str, *, repo_root: Path | None = None) -> pd.DataFrame:
    path = resolve_repo_input(parquet_id, repo_root=repo_root)
    df = pd.read_parquet(path)
    required = {"trial", "flywire_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns: {sorted(missing)}")
    return df


def mean_neuron_rates_hz(
    spikes: pd.DataFrame,
    neuron_ids: Sequence[int],
    *,
    t_run_s: float = 1.0,
) -> pd.Series:
    """Per-neuron mean firing rate (Hz) across that table's available trials.

    For each neuron ``i`` and trial ``t``::

        r_{i,t} = spikes_{i,t} / duration_sec

    then ``r̄_i = mean_t(r_{i,t})`` over trials present in ``spikes``. Trials with
    no spikes for a neuron contribute 0. Neurons in ``neuron_ids`` that never
    spike still receive a 0 Hz entry so readout sets stay aligned.
    """
    if t_run_s <= 0:
        raise ValueError("t_run_s must be positive")
    ids = [int(x) for x in neuron_ids]
    index = pd.Index(ids, name="flywire_id")
    if not ids:
        return pd.Series(dtype=float, index=index)
    if spikes.empty:
        return pd.Series(0.0, index=index)

    trials = pd.unique(spikes["trial"])
    if len(trials) == 0:
        return pd.Series(0.0, index=index)

    selected = spikes[spikes["flywire_id"].isin(ids)]
    counts = (
        selected.groupby(["flywire_id", "trial"]).size().astype(float)
        if not selected.empty
        else pd.Series(dtype=float)
    )
    full_index = pd.MultiIndex.from_product([ids, trials], names=["flywire_id", "trial"])
    counts = counts.reindex(full_index, fill_value=0.0)
    per_trial_hz = counts / float(t_run_s)
    return per_trial_hz.groupby(level="flywire_id").mean().reindex(index, fill_value=0.0)


def motor_population_rate_hz(
    spikes: pd.DataFrame,
    motor_ids: Sequence[int],
    *,
    t_run_s: float = 1.0,
) -> float:
    """Sum of per-neuron mean rates over the motor readout set (Hz)."""
    return float(mean_neuron_rates_hz(spikes, motor_ids, t_run_s=t_run_s).sum())


def motor_delta_hz(
    baseline: pd.DataFrame,
    perturbed: pd.DataFrame,
    motor_ids: Sequence[int],
    *,
    t_run_s: float = 1.0,
) -> float:
    """Motor readout ΔHz via per-neuron mean rates.

    1. ``r_{i,t} = spikes_{i,t} / duration_sec``
    2. ``r̄_i`` = mean over available trials in each condition
    3. ``Δr_i = r̄_i^(c) - r̄_i^(0)``
    4. ``ΔHz(c) = sum_{i in M} Δr_i`` (signed; matches ``motor_analysis.motor_impact``)

    Each condition uses its own trial set, so mismatched parquet trial counts no
    longer share one inconsistent population denominator.
    """
    base_rates = mean_neuron_rates_hz(baseline, motor_ids, t_run_s=t_run_s)
    pert_rates = mean_neuron_rates_hz(perturbed, motor_ids, t_run_s=t_run_s)
    delta = pert_rates.reindex(base_rates.index, fill_value=0.0) - base_rates
    return float(delta.sum())


def load_connectivity_edges(connectivity_id: str, *, repo_root: Path | None = None) -> pd.DataFrame:
    path = resolve_repo_input(connectivity_id, repo_root=repo_root)
    edges = pd.read_parquet(path)
    pre_col = "Presynaptic_ID" if "Presynaptic_ID" in edges.columns else None
    post_col = "Postsynaptic_ID" if "Postsynaptic_ID" in edges.columns else None
    if pre_col is None or post_col is None:
        raise ValueError(f"Connectivity missing Presynaptic_ID/Postsynaptic_ID: {list(edges.columns)[:12]}")
    weight_col = (
        "Excitatory x Connectivity"
        if "Excitatory x Connectivity" in edges.columns
        else ("Connectivity" if "Connectivity" in edges.columns else None)
    )
    if weight_col is None:
        raise ValueError("Connectivity table missing weight column")
    out = edges[[pre_col, post_col, weight_col]].copy()
    out.columns = ["pre", "post", "weight"]
    out["pre"] = pd.to_numeric(out["pre"], errors="coerce")
    out["post"] = pd.to_numeric(out["post"], errors="coerce")
    out["weight"] = pd.to_numeric(out["weight"], errors="coerce")
    out = out.dropna()
    out["pre"] = out["pre"].astype("int64")
    out["post"] = out["post"].astype("int64")
    out["weight"] = out["weight"].astype(float)
    return out


def default_jo_group_specs() -> list[dict[str, str]]:
    return [
        {"name": "AN", "by": "cell_class", "value": "AN"},
        {"name": "descending", "by": "super_class", "value": "descending"},
        {"name": "LO", "by": "cell_class", "value": "LO"},
        {"name": "Kenyon_Cell", "by": "cell_class", "value": "Kenyon_Cell"},
        {"name": "motor", "by": "super_class", "value": "motor"},
    ]


def select_groups_and_jo_ids(
    *,
    annotations_id: str = DEFAULT_ANNOTATIONS_ID,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    jo_config_id: str = DEFAULT_JO_CONFIG,
    manifest_path: str = DEFAULT_MANIFEST,
    repo_root: Path | None = None,
) -> tuple[dict[str, list[int]], list[int], list[int]]:
    """Return ``(group_ids, jo_source_ids, motor_ids)``."""
    import importlib.util
    import sys

    import yaml

    root = repo_root_from(repo_root)
    module_path = resolve_repo_input("scripts/run_jo_sweep.py", repo_root=root)
    spec = importlib.util.spec_from_file_location("run_jo_sweep", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    annotations_path = resolve_repo_input(annotations_id, manifest_path=manifest_path, repo_root=root)
    completeness_path = resolve_repo_input(completeness_id, manifest_path=manifest_path, repo_root=root)
    config_path = resolve_repo_input(jo_config_id, repo_root=root)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    ann = module.load_annotations(annotations_path)
    sim_ids = module.load_sim_ids(completeness_path)
    jo_ids = module.select_jo_neurons(ann, sim_ids, config["sensory_input"])
    groups = module.select_perturbation_groups(
        ann,
        sim_ids,
        default_jo_group_specs(),
        exclude_ids=set(jo_ids),
    )
    motor_ids = groups.get("motor") or module.select_perturbation_groups(
        ann, sim_ids, [{"name": "motor", "by": "super_class", "value": "motor"}]
    )["motor"]
    return groups, list(jo_ids), list(motor_ids)


def build_capped_subgraph(
    edges: pd.DataFrame,
    focus_ids: Sequence[int],
    *,
    always_keep: Sequence[int] | None = None,
    max_nodes: int = DEFAULT_MAX_SUBGRAPH_NODES,
    seed: int = 42,
) -> tuple[np.ndarray, dict[int, int]]:
    """Build control-theoretic ``W`` and id→index map for a capped neighborhood."""
    focus = [int(x) for x in focus_ids]
    keep = {int(x) for x in (always_keep or [])}
    focus_set = set(focus) | keep
    if not focus_set:
        raise ValueError("focus_ids/always_keep must be non-empty")

    incident = edges[edges["pre"].isin(focus_set) | edges["post"].isin(focus_set)]
    nodes = sorted(set(incident["pre"].tolist()) | set(incident["post"].tolist()) | focus_set)
    if len(nodes) > max_nodes:
        rng = np.random.default_rng(seed)
        neighbors = [n for n in nodes if n not in focus_set]
        keep_n = max(0, max_nodes - len(focus_set))
        if keep_n <= 0:
            # Prefer focus IDs; truncate deterministically.
            nodes = sorted(focus_set)[:max_nodes]
        else:
            chosen = rng.choice(neighbors, size=min(keep_n, len(neighbors)), replace=False)
            nodes = sorted(set(focus_set) | {int(x) for x in chosen})

    index = {node: i for i, node in enumerate(nodes)}
    local_edges: list[tuple[int, int, float]] = []
    for pre, post, weight in incident[["pre", "post", "weight"]].itertuples(index=False):
        if int(pre) in index and int(post) in index:
            local_edges.append((index[int(pre)], index[int(post)], float(weight)))
    if not local_edges:
        n = len(nodes)
        return np.zeros((n, n), dtype=float), index

    W = load_dense_signed_adjacency_from_edges(local_edges, n_nodes=len(nodes))
    radius = float(np.max(np.abs(np.linalg.eigvals(W)))) if W.size else 0.0
    if radius > 0.9:
        W = W * (0.85 / radius)
    return W, index


def mean_modal_controllability_on_subgraph(
    edges: pd.DataFrame,
    focus_ids: Sequence[int],
    *,
    max_nodes: int = DEFAULT_MAX_SUBGRAPH_NODES,
    seed: int = 42,
) -> float:
    if not focus_ids:
        return float("nan")
    W, index = build_capped_subgraph(edges, focus_ids, max_nodes=max_nodes, seed=seed)
    if W.size == 0:
        return 0.0
    scores = modal_controllability(W)
    focus_scores = [float(scores[index[i]]) for i in focus_ids if int(i) in index]
    if not focus_scores:
        return float("nan")
    return float(np.mean(focus_scores))


def path_attenuation_for_gate(
    edges: pd.DataFrame,
    gate_ids: Sequence[int],
    source_ids: Sequence[int],
    motor_ids: Sequence[int],
    *,
    max_nodes: int = DEFAULT_MAX_SUBGRAPH_NODES,
    seed: int = 42,
    gamma: float = DEFAULT_GAMMA,
    max_path_length: int = DEFAULT_MAX_PATH_LENGTH,
) -> float:
    """Path attenuation ratio η(c) with gate = silenced class."""
    if not gate_ids or not source_ids or not motor_ids:
        return float("nan")
    # Cap source/motor pools so always_keep fits under max_nodes with gates.
    rng = np.random.default_rng(seed)
    gate = [int(x) for x in gate_ids]
    sources = [int(x) for x in source_ids]
    motors = [int(x) for x in motor_ids]
    budget = max(10, max_nodes // 3)
    if len(sources) > budget:
        sources = sorted(int(x) for x in rng.choice(sources, size=budget, replace=False))
    if len(motors) > budget:
        motors = sorted(int(x) for x in rng.choice(motors, size=budget, replace=False))
    # Cap gate set similarly if huge (e.g. Kenyon cells).
    gate_budget = max(10, max_nodes // 3)
    if len(gate) > gate_budget:
        gate = sorted(int(x) for x in rng.choice(gate, size=gate_budget, replace=False))

    W, index = build_capped_subgraph(
        edges,
        gate,
        always_keep=sources + motors,
        max_nodes=max_nodes,
        seed=seed,
    )
    src_idx = [index[i] for i in sources if i in index]
    mot_idx = [index[i] for i in motors if i in index]
    gate_idx = [index[i] for i in gate if i in index]
    if not src_idx or not mot_idx or not gate_idx:
        return float("nan")
    try:
        return float(
            path_attenuation_ratio(
                W,
                src_idx,
                mot_idx,
                gate_idx,
                gamma=gamma,
                max_path_length=max_path_length,
            )
        )
    except ValueError:
        return float("nan")


def fit_structural_prediction(
    modal: np.ndarray,
    eta: np.ndarray,
    delta_obs: np.ndarray,
) -> np.ndarray:
    """OLS ``Ŷ_struct = β0 + β1 c̄ + β2 η``; falls back to mean when underdetermined."""
    y = np.asarray(delta_obs, dtype=float)
    x1 = np.asarray(modal, dtype=float)
    x2 = np.asarray(eta, dtype=float)
    mask = np.isfinite(y) & np.isfinite(x1) & np.isfinite(x2)
    if int(mask.sum()) < 3:
        # Degenerate: predict the observed mean (leverage → centered residuals).
        mu = float(np.nanmean(y)) if np.isfinite(y).any() else 0.0
        return np.full_like(y, mu, dtype=float)

    X = np.column_stack([np.ones(int(mask.sum())), x1[mask], x2[mask]])
    beta, *_ = np.linalg.lstsq(X, y[mask], rcond=None)
    y_hat = np.full_like(y, float("nan"), dtype=float)
    # Predict for all rows with finite surrogates; otherwise fall back to mean.
    mu = float(np.mean(y[mask]))
    for i in range(len(y)):
        if np.isfinite(x1[i]) and np.isfinite(x2[i]):
            y_hat[i] = float(beta[0] + beta[1] * x1[i] + beta[2] * x2[i])
        else:
            y_hat[i] = mu
    return y_hat


def dynamic_leverage_residual(delta_obs: float, y_hat_struct: float) -> float:
    """δ_leverage(c) = ΔHz_obs(c) − Ŷ_struct(c)."""
    if not (np.isfinite(delta_obs) and np.isfinite(y_hat_struct)):
        return float("nan")
    return float(delta_obs - y_hat_struct)


def validate_surrogates(
    results_dir_id: str = DEFAULT_RESULTS_DIR,
    *,
    connectivity_id: str = DEFAULT_CONNECTIVITY_ID,
    annotations_id: str = DEFAULT_ANNOTATIONS_ID,
    completeness_id: str = DEFAULT_COMPLETENESS_ID,
    jo_config_id: str = DEFAULT_JO_CONFIG,
    manifest_path: str = DEFAULT_MANIFEST,
    max_subgraph_nodes: int = DEFAULT_MAX_SUBGRAPH_NODES,
    baseline_name: str = "baseline_jo",
    targets: Sequence[str] | None = None,
    repo_root: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run surrogate-vs-ground-truth validation and return ``(table, metrics)``."""
    root = repo_root_from(repo_root)
    results_dir_id = results_dir_id.replace("\\", "/").rstrip("/")
    targets = list(targets or TARGET_CLASSES)

    manifest = load_output_manifest(results_dir_id, repo_root=root)
    commit_sha, random_seed = extract_provenance(manifest)
    sim = manifest.get("simulation") or {}
    t_run_s = float(sim.get("t_run_ms", 1000)) / 1000.0
    resolved_baseline = resolve_baseline_exp_name(manifest, fallback=baseline_name)

    LOGGER.info(
        "validate_surrogates: dir=%s baseline=%s commit_sha=%s random_seed=%s claim_status=%s",
        results_dir_id,
        resolved_baseline,
        commit_sha,
        random_seed,
        CLAIM_STATUS,
    )

    baseline = load_spike_table(f"{results_dir_id}/{resolved_baseline}.parquet", repo_root=root)
    groups, jo_ids, motor_ids = select_groups_and_jo_ids(
        annotations_id=annotations_id,
        completeness_id=completeness_id,
        jo_config_id=jo_config_id,
        manifest_path=manifest_path,
        repo_root=root,
    )
    edges = load_connectivity_edges(connectivity_id, repo_root=root)

    rows: list[dict[str, Any]] = []
    for name in targets:
        perturb = load_spike_table(f"{results_dir_id}/perturb_{name}.parquet", repo_root=root)
        ids = groups.get(name, [])
        delta = motor_delta_hz(baseline, perturb, motor_ids, t_run_s=t_run_s)
        modal_mean = mean_modal_controllability_on_subgraph(
            edges, ids, max_nodes=max_subgraph_nodes, seed=random_seed
        )
        eta = path_attenuation_for_gate(
            edges,
            ids,
            jo_ids,
            motor_ids,
            max_nodes=max_subgraph_nodes,
            seed=random_seed,
        )
        rows.append(
            {
                "target_class": name,
                "n_silenced": int(len(ids)),
                "delta_hz_obs": float(delta),
                "mean_modal_controllability": float(modal_mean),
                "path_attenuation_ratio": float(eta) if np.isfinite(eta) else float("nan"),
            }
        )

    table = pd.DataFrame(rows)
    y_hat = fit_structural_prediction(
        table["mean_modal_controllability"].to_numpy(dtype=float),
        table["path_attenuation_ratio"].to_numpy(dtype=float),
        table["delta_hz_obs"].to_numpy(dtype=float),
    )
    table["y_hat_struct"] = y_hat
    table["delta_leverage"] = [
        dynamic_leverage_residual(float(o), float(y))
        for o, y in zip(table["delta_hz_obs"], table["y_hat_struct"], strict=True)
    ]

    valid = table.dropna(subset=["mean_modal_controllability", "delta_hz_obs"])
    if len(valid) >= 3:
        rs, p_rs = stats.spearmanr(valid["mean_modal_controllability"], valid["delta_hz_obs"])
        r, p_r = stats.pearsonr(valid["mean_modal_controllability"], valid["delta_hz_obs"])
        spearman_rs, spearman_p = float(rs), float(p_rs)
        pearson_r, pearson_p = float(r), float(p_r)
    else:
        spearman_rs = spearman_p = pearson_r = pearson_p = float("nan")

    table["spearman_rs"] = spearman_rs
    table["pearson_r"] = pearson_r
    table["spearman_p"] = spearman_p
    table["pearson_p"] = pearson_p
    table["commit_sha"] = commit_sha
    table["random_seed"] = int(random_seed)
    table = table[OUTPUT_COLUMNS]

    metrics: dict[str, Any] = {
        "claim_status": CLAIM_STATUS,
        "n_targets": int(len(table)),
        "spearman_rs": spearman_rs,
        "spearman_p": spearman_p,
        "pearson_r": pearson_r,
        "pearson_p": pearson_p,
        "commit_sha": commit_sha,
        "random_seed": int(random_seed),
        "results_dir": results_dir_id,
    }
    return table, metrics


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--connectivity-id", default=DEFAULT_CONNECTIVITY_ID)
    parser.add_argument("--annotations-id", default=DEFAULT_ANNOTATIONS_ID)
    parser.add_argument("--completeness-id", default=DEFAULT_COMPLETENESS_ID)
    parser.add_argument("--jo-config", default=DEFAULT_JO_CONFIG)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--max-subgraph-nodes", type=int, default=DEFAULT_MAX_SUBGRAPH_NODES)
    args = parser.parse_args(argv)

    root = repo_root_from()
    table, metrics = validate_surrogates(
        args.results_dir,
        connectivity_id=args.connectivity_id,
        annotations_id=args.annotations_id,
        completeness_id=args.completeness_id,
        jo_config_id=args.jo_config,
        manifest_path=args.manifest,
        max_subgraph_nodes=args.max_subgraph_nodes,
        repo_root=root,
    )
    out_path = require_repo_path(root, root / args.output, "surrogate output")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)

    LOGGER.info("Wrote %s", out_path)
    print(f"Wrote {out_path}")
    print(f"claim_status: {metrics['claim_status']}")
    print(f"commit_sha: {metrics['commit_sha']} random_seed: {metrics['random_seed']}")
    print(
        f"Spearman modal vs delta_hz_obs: r_s={metrics['spearman_rs']:.4f}, p={metrics['spearman_p']:.4g}"
    )
    print(
        f"Pearson modal vs delta_hz_obs: r={metrics['pearson_r']:.4f}, p={metrics['pearson_p']:.4g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
