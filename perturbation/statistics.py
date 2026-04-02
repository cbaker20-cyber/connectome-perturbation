import sys
sys.path.insert(0, "Drosophila_brain_model")
sys.path.insert(0, "perturbation")
import pandas as pd
import numpy as np
from scipy import stats
from cell_groups import get_group
from pathlib import Path

def trial_rates(df, neuron_ids, t_run=1.0):
    df = df[df["flywire_id"].isin(neuron_ids)]
    rates = []
    for t in sorted(df["trial"].unique()):
        rate = df[df["trial"]==t].groupby("flywire_id").size().div(t_run).sum()
        rates.append(rate)
    return np.array(rates)

def test_condition(exp_name, baseline_name="baseline_sugar"):
    base_df = pd.read_parquet(f"results/{baseline_name}.parquet")
    exp_df = pd.read_parquet(f"results/{exp_name}.parquet")
    motor_ids = get_group(super_class="motor")
    base_rates = trial_rates(base_df, motor_ids)
    exp_rates = trial_rates(exp_df, motor_ids)
    t_stat, p_val = stats.ttest_ind(base_rates, exp_rates)
    delta = exp_rates.mean() - base_rates.mean()
    pct = (delta / base_rates.mean()) * 100
    return {
        "exp_name": exp_name,
        "baseline_mean_hz": round(base_rates.mean(), 2),
        "perturbed_mean_hz": round(exp_rates.mean(), 2),
        "delta_hz": round(delta, 2),
        "pct_change": round(pct, 1),
        "t_stat": round(t_stat, 3),
        "p_value": round(p_val, 4),
        "significant": p_val < 0.05,
    }

targets = [
    ("hq_LO", "LO"),
    ("hq_AN", "AN"),
    ("hq_LOP>LO.ME", "LOP>LO.ME"),
    ("hq_LHCENT", "LHCENT"),
    ("hq_ME>LO", "ME>LO"),
    ("hq_Kenyon_Cell", "Kenyon_Cell"),
    ("perturb_descending", "descending"),
    ("perturb_sensory", "sensory"),
    ("perturb_central", "central"),
    ("perturb_ascending", "ascending"),
]

rows = []
for exp_name, label in targets:
    try:
        r = test_condition(exp_name)
        r["label"] = label
        rows.append(r)
        sig = "*" if r["significant"] else "ns"
        print(f"{label:20s}  delta={r['delta_hz']:8.1f} Hz  p={r['p_value']:.4f}  {sig}")
    except Exception as e:
        print(f"{label}: missing")

df = pd.DataFrame(rows).set_index("label")
df.to_csv("results/statistics.csv")
print("Saved to results/statistics.csv")