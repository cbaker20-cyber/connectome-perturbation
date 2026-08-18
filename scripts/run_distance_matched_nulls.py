#!/usr/bin/env python3
"""Distance-matched dynamical null test for the JO perturbation sweep.

For each perturbation group (AN, descending, LO, Kenyon_Cell, motor) this
script draws random neuron sets matched in size and weighted-degree
distribution, runs full Brian2 silencing simulations under JO sensory drive,
and measures the motor-neuron firing-rate change (dHz) of each null sample.

Observed dHz values come from ``results/jo_ground_truth/statistics.csv`` and
the motor baseline from ``baseline_jo.parquet`` (both produced by
``scripts/run_jo_sweep.py``). The empirical null tests whether an observed
effect (e.g. AN ~ -9.6 Hz) is more extreme than silencing any similarly sized,
similarly connected random group.

Usage:
    python scripts/run_distance_matched_nulls.py --n-perms 20 --n-trials 5
    python scripts/run_distance_matched_nulls.py --n-perms 50 --groups AN
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_jo_sweep import load_sim_ids, prepare_jo_sweep  # noqa: E402
from tools.path_resolver import repo_root_from  # noqa: E402


DEFAULT_CONFIG = "configs/jo_ground_truth_30trial.yaml"
DEFAULT_N_PERMS = 20
DEFAULT_N_TRIALS = 5
DEFAULT_SEED = 42
DEFAULT_N_BINS = 10
TMP_DIR = REPO_ROOT / "results" / "_degree_null_tmp"


# ---------------------------------------------------------------------------
# Connectivity / degree helpers
# ---------------------------------------------------------------------------

def load_edge_weights(path: Path) -> pd.DataFrame:
    """Load connectivity as (source, target, weight) edges."""
    raw = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    pre = next((c for c in ("Presynaptic_ID", "pre_root_id", "source", "pre") if c in raw.columns), None)
    post = next((c for c in ("Postsynaptic_ID", "post_root_id", "target", "post") if c in raw.columns), None)
    wt = next((c for c in ("Connectivity", "weight", "syn_count", "synapse_count") if c in raw.columns), None)
    if not all([pre, post, wt]):
        raise ValueError(f"Cannot infer edge columns from {list(raw.columns)}")
    edges = raw[[pre, post, wt]].copy()
    edges.columns = ["source", "target", "weight"]
    for col in ("source", "target"):
        edges[col] = pd.to_numeric(edges[col], errors="coerce")
    edges["weight"] = pd.to_numeric(edges["weight"], errors="coerce")
    edges = edges.dropna().query("weight > 0").copy()
    edges["source"] = edges["source"].astype("int64")
    edges["target"] = edges["target"].astype("int64")
    return edges


import networkx as nx

def compute_shortest_path_distance(edges: pd.DataFrame, jo_ids: list[int], all_ids: np.ndarray) -> pd.Series:
    """Shortest path (hop count) from JO sensory nodes to all nodes."""
    G = nx.from_pandas_edgelist(edges, source='source', target='target', create_using=nx.DiGraph)
    # Add dummy source node connected to all JO nodes
    G.add_node('JO_SOURCE')
    for jid in jo_ids:
        if jid in G:
            G.add_edge('JO_SOURCE', jid)
            
    lengths = nx.single_source_shortest_path_length(G, 'JO_SOURCE')
    
    # map to series
    dist_map = {}
    for node in all_ids:
        if node == 'JO_SOURCE' or node in jo_ids:
            continue
        dist_map[node] = lengths.get(node, 999) - 1 # -1 because JO_SOURCE to JO is 1
        if dist_map[node] < 0:
            dist_map[node] = 0
    
    dist_series = pd.Series(dist_map)
    dist_series.index = dist_series.index.astype("int64")
    dist_series.name = "distance_bin"
    return dist_series


def degree_matched_sample(
    rng: np.random.Generator,
    target_bins: pd.Series,
    pool_bins: pd.Series,
    pool_ids: np.ndarray,
    sample_size: int,
) -> list[int]:
    """Draw a random set matching the target group's degree-bin proportions."""
    target_counts = target_bins.value_counts().sort_index()
    proportions = target_counts / target_counts.sum()
    desired = np.floor(proportions * sample_size).astype(int)
    remainder = sample_size - int(desired.sum())
    if remainder > 0:
        fractional = (proportions * sample_size) - desired
        for bin_id in fractional.sort_values(ascending=False).index[:remainder]:
            desired.loc[bin_id] += 1

    sampled = []
    for bin_id, n in desired.items():
        if n <= 0:
            continue
        mask = (pool_bins == bin_id).values if isinstance(pool_bins, pd.Series) else (pool_bins == bin_id)
        candidates = pool_ids[mask]
        if len(candidates) == 0:
            candidates = pool_ids  # fallback
        chosen = rng.choice(candidates, size=int(n), replace=len(candidates) < n)
        sampled.extend(int(x) for x in chosen)

    # Trim or pad to exact size
    if len(sampled) > sample_size:
        sampled = list(rng.choice(sampled, size=sample_size, replace=False))
    return sampled


# ---------------------------------------------------------------------------
# Brian2 simulation helpers
# ---------------------------------------------------------------------------

def motor_rates_hz(spike_table: pd.DataFrame, motor_ids: Sequence[int], *, t_run_s: float = 1.0) -> np.ndarray:
    """Per-trial total motor firing rate (Hz) from a spike table."""
    motor_set = set(motor_ids)
    trials = sorted(spike_table["trial"].unique())
    counts = spike_table[spike_table["flywire_id"].isin(motor_set)].groupby("trial").size()
    return counts.reindex(trials, fill_value=0).astype(float).values / t_run_s


def run_silencing_trial_rates(
    neuron_ids: list[int],
    jo_ids: list[int],
    motor_ids: list[int],
    *,
    path_comp: Path,
    path_con: Path,
    n_trials: int = DEFAULT_N_TRIALS,
    t_run_s: float = 1.0,
) -> np.ndarray:
    """Run one Brian2 silencing simulation; return per-trial motor rates (Hz)."""
    from brian2 import Hz, ms
    from model import default_params, run_exp

    exp_name = f"_null_{hashlib.md5(str(sorted(neuron_ids)).encode()).hexdigest()[:12]}"
    params = default_params.copy()
    params["n_run"] = n_trials
    params["t_run"] = t_run_s * 1000 * ms
    params["r_poi"] = 150 * Hz

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TMP_DIR / f"{exp_name}.parquet"
    if out_path.exists():
        out_path.unlink()

    run_exp(
        exp_name=exp_name,
        neu_exc=jo_ids,
        neu_slnc=neuron_ids,
        path_res=str(TMP_DIR),
        path_comp=str(path_comp),
        path_con=str(path_con),
        params=params,
        n_proc=1,
        force_overwrite=True,
    )

    try:
        return motor_rates_hz(pd.read_parquet(out_path), motor_ids, t_run_s=t_run_s)
    finally:
        out_path.unlink(missing_ok=True)


def baseline_motor_mean(jo_ids: list[int], motor_ids: list[int], *, results_dir: Path, t_run_s: float = 1.0) -> float:
    """Mean motor rate (Hz) from the existing JO baseline spike table."""
    baseline_path = results_dir / "baseline_jo.parquet"
    if not baseline_path.exists():
        raise FileNotFoundError(f"Missing {baseline_path}; run scripts/run_jo_sweep.py first")
    return float(np.mean(motor_rates_hz(pd.read_parquet(baseline_path), motor_ids, t_run_s=t_run_s)))


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run_distance_matched_nulls(
    *,
    groups_to_test: list[str] | None = None,
    n_perms: int = DEFAULT_N_PERMS,
    n_trials: int | None = None,
    seed: int = DEFAULT_SEED,
    n_bins: int = DEFAULT_N_BINS,
    config_path: str = DEFAULT_CONFIG,
) -> pd.DataFrame:
    """Run the degree-matched dynamical null test for the requested groups."""
    import yaml

    root = repo_root_from()
    config = yaml.safe_load((root / config_path).read_text(encoding="utf-8"))
    jo_ids, groups, resolved = prepare_jo_sweep(config, repo_root=root)
    results_dir = resolved["results_dir"]

    print("Loading data...")
    sim_ids = load_sim_ids(resolved["completeness"])
    edges = load_edge_weights(resolved["connectivity"])
    pool_ids_full = np.array(sorted(sim_ids))
    node_distances = compute_shortest_path_distance(edges, jo_ids, pool_ids_full)

    motor_ids = groups["motor"]
    baseline_mean = baseline_motor_mean(jo_ids, motor_ids, results_dir=results_dir)
    print(f"Motor neurons: {len(motor_ids)}; JO sensory: {len(jo_ids)}; baseline motor mean: {baseline_mean:.2f} Hz")

    stats_path = results_dir / "statistics.csv"
    if not stats_path.exists():
        raise FileNotFoundError(f"Missing {stats_path}; run the JO sweep first")
    stats_df = pd.read_csv(stats_path, index_col=0)
    observed_deltas = stats_df["delta_hz"].to_dict()
    observed_n_trials = int(stats_df["n_baseline_trials"].iloc[0]) if "n_baseline_trials" in stats_df else None
    if n_trials is None:
        if observed_n_trials is None:
            raise ValueError("statistics.csv has no n_baseline_trials column; pass --n-trials explicitly.")
        n_trials = observed_n_trials
        print(f"Auto-matching null n_trials to observed sweep: {n_trials}")
    elif observed_n_trials is not None and n_trials != observed_n_trials:
        raise ValueError(
            f"n_trials={n_trials} != observed n_baseline_trials={observed_n_trials}. "
            f"Pass --n-trials {observed_n_trials} or the comparison isn't fair."
        )

    if groups_to_test:
        wanted = {g.lower() for g in groups_to_test}
        groups = {name: ids for name, ids in groups.items() if name.lower() in wanted}
    if not groups:
        raise ValueError(f"No configured groups matched {groups_to_test!r}")

    # Null pool: all simulated neurons except the JO sensory drive. Its
    # quantile bins define the shared degree-bin edges used for every group.
    pool_ids = np.array(sorted(sim_ids))
    pool_ids = pool_ids[~np.isin(pool_ids, list(jo_ids))]
    pool_bins = node_distances.reindex(pool_ids).fillna(999)

    rng = np.random.default_rng(seed)
    all_results = []

    for group_name, group_ids in groups.items():
        print(f"\n{'=' * 60}\nGroup: {group_name} ({len(group_ids)} neurons)\n{'=' * 60}")
        obs_delta = observed_deltas[group_name]

        # Target and null-pool bins reuse the pool's bin edges, so bin IDs
        # correspond to the same absolute degree ranges for both sides.
        target_bins = pool_bins.reindex(group_ids)
        group_set = set(group_ids)
        null_pool = pool_ids[~np.isin(pool_ids, list(group_set))]
        null_pool_bins = pool_bins.reindex(null_pool)

        null_deltas = []
        perm_records = []
        perms_csv = results_dir / f"jo_distance_matched_nulls_{group_name}_perms.csv"
        start_perm = 0
        if perms_csv.exists():
            try:
                existing_df = pd.read_csv(perms_csv)
                if not existing_df.empty and "n_trials_per_sim" in existing_df.columns and existing_df["n_trials_per_sim"].iloc[0] == n_trials:
                    null_deltas = existing_df["delta_hz"].tolist()
                    perm_records = existing_df.to_dict(orient="records")
                    start_perm = len(perm_records)
                    print(f"  Resuming from perm {start_perm + 1} (found {start_perm} existing records for {group_name})")
            except Exception as e:
                print(f"  Warning: Could not read {perms_csv}: {e}")

        for perm_i in range(start_perm, n_perms):
            t0 = time.time()
            null_sample = degree_matched_sample(rng, target_bins, null_pool_bins, null_pool, len(group_ids))
            null_rates = run_silencing_trial_rates(
                null_sample, jo_ids, motor_ids,
                path_comp=resolved["completeness"],
                path_con=resolved["connectivity"],
                n_trials=n_trials,
            )
            null_delta = float(np.mean(null_rates)) - baseline_mean
            null_deltas.append(null_delta)
            perm_records.append({
                "group": group_name,
                "perm_index": perm_i + 1,
                "delta_hz": round(null_delta, 4),
                "n_silenced": len(group_ids),
                "n_trials_per_sim": n_trials,
                "seed": seed,
            })
            print(f"  perm {perm_i + 1}/{n_perms}: dHz={null_delta:.2f} ({time.time() - t0:.0f}s)", flush=True)

            pd.DataFrame(perm_records).to_csv(perms_csv, index=False)

        # Empirical p-values: how many null deltas are at least as extreme as observed.
        MIN_PERMS_FOR_P_VALUE = 10
        null_arr = np.array(null_deltas)
        if len(null_arr) < MIN_PERMS_FOR_P_VALUE:
            print(f"  WARNING: only {len(null_arr)} perms for {group_name} — below floor, no p-value reported.")
        null_mean = float(np.mean(null_arr)) if len(null_arr) else float("nan")
        null_std = float(np.std(null_arr, ddof=1)) if len(null_arr) > 1 else float("nan")
        if len(null_arr) >= MIN_PERMS_FOR_P_VALUE:
            n_extreme = int(np.sum(null_arr <= obs_delta)) if obs_delta < 0 else int(np.sum(null_arr >= obs_delta))
            n_extreme_two = int(np.sum(np.abs(null_arr) >= abs(obs_delta)))
            p_one = (n_extreme + 1) / (len(null_arr) + 1)
            p_two = (n_extreme_two + 1) / (len(null_arr) + 1)
        else:
            p_one = p_two = float("nan")
        z_score = (obs_delta - null_mean) / null_std if null_std > 0 else float("nan")

        all_results.append({
            "group": group_name,
            "n_silenced": len(group_ids),
            "observed_delta_hz": round(obs_delta, 3),
            "null_mean": round(null_mean, 3),
            "null_std": round(null_std, 3),
            "z_score": round(z_score, 3),
            "empirical_p_one_sided": round(p_one, 4),
            "empirical_p_two_sided": round(p_two, 4),
            "n_permutations": n_perms,
            "n_trials_per_sim": n_trials,
            "seed": seed,
        })
        print(f"  obs={obs_delta:.2f} null_mean={null_mean:.2f} z={z_score:.2f} "
              f"p_one={p_one:.4f} p_two={p_two:.4f}")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(results_dir / "jo_distance_matched_nulls.csv", index=False)
    # Single-group runs also refresh the group-specific summary artifact
    # (e.g. jo_distance_matched_nulls_AN.csv), which the task treats as a deliverable.
    if len(groups) == 1:
        group_name = next(iter(groups))
        results_df.to_csv(results_dir / f"jo_distance_matched_nulls_{group_name}.csv", index=False)
    print(f"\nSaved results to {results_dir / 'jo_distance_matched_nulls.csv'}")
    return results_df


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-perms", type=int, default=DEFAULT_N_PERMS,
                        help=f"Null permutations per group (default: {DEFAULT_N_PERMS})")
    parser.add_argument("--n-trials", type=int, default=None,
                        help="Brian2 trials per null sim (default: auto-match observed sweep)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"Random seed (default: {DEFAULT_SEED})")
    parser.add_argument("--n-bins", type=int, default=DEFAULT_N_BINS,
                        help=f"Distance bins for matching (default: {DEFAULT_N_BINS})")
    parser.add_argument("--groups", nargs="+", default=None,
                        help="Groups to test (default: all): AN descending LO Kenyon_Cell motor")
    parser.add_argument("positional_groups", nargs="*", default=None,
                        help="Positional fallback for groups")
    parser.add_argument("--config", type=str, default=DEFAULT_CONFIG,
                        help=f"Config file to use (default: {DEFAULT_CONFIG})")
    
    args = parser.parse_args(argv)
    if args.positional_groups and not args.groups:
        args.groups = args.positional_groups
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_distance_matched_nulls(
        groups_to_test=args.groups,
        n_perms=args.n_perms,
        n_trials=args.n_trials,
        seed=args.seed,
        n_bins=args.n_bins,
        config_path=args.config,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
