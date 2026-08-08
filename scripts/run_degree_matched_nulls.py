#!/usr/bin/env python3
"""Degree-matched dynamical null test for the JO perturbation sweep.

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
    python scripts/run_degree_matched_nulls.py --n-perms 20 --n-trials 5
    python scripts/run_degree_matched_nulls.py --n-perms 50 --groups AN
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


def compute_weighted_degree(edges: pd.DataFrame) -> pd.Series:
    """Total weighted degree (in + out) per neuron."""
    out_deg = edges.groupby("source")["weight"].sum()
    in_deg = edges.groupby("target")["weight"].sum()
    total = out_deg.add(in_deg, fill_value=0).rename("total_strength")
    total.index = total.index.astype("int64")
    total.index.name = "root_id"
    return total


def assign_degree_bins(strengths: pd.Series, n_bins: int = DEFAULT_N_BINS) -> pd.Series:
    """Assign neurons to quantile bins of log-total-strength."""
    values = np.log1p(strengths.values.astype(float))
    unique = np.unique(values[~np.isnan(values)])
    if len(unique) < 2:
        return pd.Series(0, index=strengths.index, name="degree_bin")
    bins = pd.qcut(values, q=min(n_bins, len(unique)), duplicates="drop", labels=False)
    return pd.Series(bins.astype(int), index=strengths.index, name="degree_bin")


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

def run_degree_matched_nulls(
    *,
    groups_to_test: list[str] | None = None,
    n_perms: int = DEFAULT_N_PERMS,
    n_trials: int = DEFAULT_N_TRIALS,
    seed: int = DEFAULT_SEED,
    n_bins: int = DEFAULT_N_BINS,
) -> pd.DataFrame:
    """Run the degree-matched dynamical null test for the requested groups."""
    import yaml

    root = repo_root_from()
    config = yaml.safe_load((root / DEFAULT_CONFIG).read_text(encoding="utf-8"))
    jo_ids, groups, resolved = prepare_jo_sweep(config, repo_root=root)
    results_dir = resolved["results_dir"]

    print("Loading data...")
    sim_ids = load_sim_ids(resolved["completeness"])
    edges = load_edge_weights(resolved["connectivity"])
    total_strength = compute_weighted_degree(edges)

    motor_ids = groups["motor"]
    baseline_mean = baseline_motor_mean(jo_ids, motor_ids, results_dir=results_dir)
    print(f"Motor neurons: {len(motor_ids)}; JO sensory: {len(jo_ids)}; baseline motor mean: {baseline_mean:.2f} Hz")

    stats_path = results_dir / "statistics.csv"
    if not stats_path.exists():
        raise FileNotFoundError(f"Missing {stats_path}; run the JO sweep first")
    observed_deltas = pd.read_csv(stats_path, index_col=0)["delta_hz"].to_dict()

    if groups_to_test:
        wanted = {g.lower() for g in groups_to_test}
        groups = {name: ids for name, ids in groups.items() if name.lower() in wanted}
    if not groups:
        raise ValueError(f"No configured groups matched {groups_to_test!r}")

    # Null pool: all simulated neurons except the JO sensory drive. Its
    # quantile bins define the shared degree-bin edges used for every group.
    pool_ids = np.array(sorted(sim_ids))
    pool_ids = pool_ids[~np.isin(pool_ids, list(jo_ids))]
    pool_bins = assign_degree_bins(total_strength.reindex(pool_ids).fillna(0), n_bins=n_bins)

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
        for perm_i in range(n_perms):
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

        pd.DataFrame(perm_records).to_csv(
            results_dir / f"jo_degree_matched_nulls_{group_name}_perms.csv", index=False)

        # Empirical p-values: how many null deltas are at least as extreme as observed.
        null_arr = np.array(null_deltas)
        null_mean = float(np.mean(null_arr))
        null_std = float(np.std(null_arr, ddof=1)) if len(null_arr) > 1 else float("nan")
        n_extreme = int(np.sum(null_arr <= obs_delta)) if obs_delta < 0 else int(np.sum(null_arr >= obs_delta))
        n_extreme_two = int(np.sum(np.abs(null_arr) >= abs(obs_delta)))
        p_one = (n_extreme + 1) / (len(null_arr) + 1)
        p_two = (n_extreme_two + 1) / (len(null_arr) + 1)
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
    results_df.to_csv(results_dir / "jo_degree_matched_nulls.csv", index=False)
    # Single-group runs also refresh the group-specific summary artifact
    # (e.g. jo_degree_matched_nulls_AN.csv), which the task treats as a deliverable.
    if len(groups) == 1:
        group_name = next(iter(groups))
        results_df.to_csv(results_dir / f"jo_degree_matched_nulls_{group_name}.csv", index=False)
    print(f"\nSaved results to {results_dir / 'jo_degree_matched_nulls.csv'}")
    return results_df


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-perms", type=int, default=DEFAULT_N_PERMS,
                        help=f"Null permutations per group (default: {DEFAULT_N_PERMS})")
    parser.add_argument("--n-trials", type=int, default=DEFAULT_N_TRIALS,
                        help=f"Brian2 trials per simulation (default: {DEFAULT_N_TRIALS})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"Random seed (default: {DEFAULT_SEED})")
    parser.add_argument("--n-bins", type=int, default=DEFAULT_N_BINS,
                        help=f"Degree bins for matching (default: {DEFAULT_N_BINS})")
    parser.add_argument("--groups", nargs="+", default=None,
                        help="Groups to test (default: all): AN descending LO Kenyon_Cell motor")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_degree_matched_nulls(
        groups_to_test=args.groups,
        n_perms=args.n_perms,
        n_trials=args.n_trials,
        seed=args.seed,
        n_bins=args.n_bins,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
