from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_RESULTS_DIR = "results"


def load_firing_rates(exp_name: str, t_run: float = 1.0, path_res: str | Path = DEFAULT_RESULTS_DIR) -> pd.Series:
    """Load per-neuron firing rates for one experiment result file."""

    path = Path(path_res) / f"{exp_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No results for {exp_name}: {path}")
    df = pd.read_parquet(path)
    if df.empty:
        return pd.Series(dtype=float, name=exp_name)
    n_trials = df["trial"].nunique()
    if n_trials <= 0:
        raise ValueError(f"Result file has no trials: {path}")
    rates = (
        df.groupby("flywire_id")
        .size()
        .div(n_trials * t_run)
        .rename(exp_name)
    )
    return rates


def compare_to_baseline(
    exp_name: str,
    baseline_name: str = "baseline_sugar",
    t_run: float = 1.0,
    path_res: str | Path = DEFAULT_RESULTS_DIR,
) -> pd.DataFrame:
    """Compare an experiment against a baseline in the same results directory."""

    baseline = load_firing_rates(baseline_name, t_run=t_run, path_res=path_res)
    perturbed = load_firing_rates(exp_name, t_run=t_run, path_res=path_res)
    df = pd.DataFrame({"baseline_hz": baseline, "perturbed_hz": perturbed})
    df = df.fillna(0)
    df["delta_hz"] = df["perturbed_hz"] - df["baseline_hz"]
    df["pct_change"] = (df["delta_hz"] / df["baseline_hz"].replace(0, np.nan)) * 100
    df = df.sort_values("delta_hz")
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare perturbation result firing rates to a baseline.")
    parser.add_argument("exp_name", nargs="?", default="baseline_sugar")
    parser.add_argument("--baseline-name", default="baseline_sugar")
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--t-run", type=float, default=1.0)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args(argv)

    if args.exp_name == args.baseline_name:
        baseline = load_firing_rates(args.baseline_name, t_run=args.t_run, path_res=args.results_dir)
        print(f"Baseline: {len(baseline)} active neurons")
        print(baseline.sort_values(ascending=False).head(args.top))
    else:
        comparison = compare_to_baseline(
            args.exp_name,
            baseline_name=args.baseline_name,
            t_run=args.t_run,
            path_res=args.results_dir,
        )
        print(comparison.head(args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
