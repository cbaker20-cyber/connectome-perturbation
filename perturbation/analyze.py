import pandas as pd
import numpy as np
from pathlib import Path

PATH_RES = "results"

def load_firing_rates(exp_name, t_run=1.0, path_res=PATH_RES):
    path = Path(path_res) / f"{exp_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No results for {exp_name}")
    df = pd.read_parquet(path)
    n_trials = df["trial"].nunique()
    rates = (
        df.groupby("flywire_id")
        .size()
        .div(n_trials * t_run)
        .rename(exp_name)
    )
    return rates

def compare_to_baseline(exp_name, baseline_name="baseline_sugar", t_run=1.0):
    baseline = load_firing_rates(baseline_name, t_run)
    perturbed = load_firing_rates(exp_name, t_run)
    df = pd.DataFrame({"baseline_hz": baseline, "perturbed_hz": perturbed})
    df = df.fillna(0)
    df["delta_hz"] = df["perturbed_hz"] - df["baseline_hz"]
    df["pct_change"] = (df["delta_hz"] / df["baseline_hz"].replace(0, np.nan)) * 100
    df = df.sort_values("delta_hz")
    return df

if __name__ == "__main__":
    baseline = load_firing_rates("baseline_sugar")
    print(f"Baseline: {len(baseline)} active neurons")
    print(baseline.sort_values(ascending=False).head(10))
