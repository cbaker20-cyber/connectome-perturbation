from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_PERTURBATION_DIR = Path(__file__).resolve().parent
if str(_PERTURBATION_DIR) not in sys.path:
    sys.path.insert(0, str(_PERTURBATION_DIR))

from analyze import compare_to_baseline
from cell_groups import get_group

def motor_impact(exp_name, motor_ids):
    result = compare_to_baseline(exp_name)
    motor = result[result.index.isin(motor_ids)]
    return {
        "exp_name": exp_name,
        "motor_delta_hz": motor["delta_hz"].sum(),
        "motor_neurons_affected": (motor["delta_hz"].abs() > 0.5).sum(),
        "motor_neurons_inhibited": (motor["delta_hz"] < -0.5).sum(),
        "motor_neurons_disinhibited": (motor["delta_hz"] > 0.5).sum(),
        "strongest_effect": motor["delta_hz"].min(),
    }

if __name__ == "__main__":
    motor_ids = get_group(super_class="motor")
    print(f"Tracking {len(motor_ids)} motor neurons")

    results = []
    for p in sorted(Path("results").glob("perturb_*.parquet")):
        exp = p.stem
        try:
            r = motor_impact(exp, motor_ids)
            results.append(r)
        except Exception as e:
            print(f"Skipping {exp}: {e}")

    df = pd.DataFrame(results).set_index("exp_name")
    df = df.sort_values("motor_delta_hz")
    print(df.to_string())
    df.to_csv("results/motor_impact.csv")
    print("Saved to results/motor_impact.csv")
