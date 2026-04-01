import sys
sys.path.insert(0, "Drosophila_brain_model")
sys.path.insert(0, "perturbation")
import pandas as pd
import numpy as np
from pathlib import Path
from model import run_exp, default_params
from brian2 import ms
from analyze import compare_to_baseline
from baseline import NEU_SUGAR, PATH_COMP, PATH_CON, PATH_RES, PARAMS

def run_single_perturbation(neuron_ids, exp_name, force=False):
    Path(PATH_RES).mkdir(exist_ok=True)
    params = PARAMS.copy()
    params["n_run"] = 5
    run_exp(
        exp_name=exp_name,
        neu_exc=NEU_SUGAR,
        neu_slnc=neuron_ids,
        path_res=PATH_RES,
        path_comp=PATH_COMP,
        path_con=PATH_CON,
        params=params,
        n_proc=1,
        force_overwrite=force
    )

def run_perturbation_sweep(groups, force=False):
    results = []
    for group_name, neuron_ids in groups.items():
        exp_name = f"perturb_{group_name}"
        print(f"--- Silencing group: {group_name} ({len(neuron_ids)} neurons) ---")
        run_single_perturbation(neuron_ids, exp_name, force=force)
        comparison = compare_to_baseline(exp_name)
        total_delta = comparison["delta_hz"].sum()
        n_affected = (comparison["delta_hz"].abs() > 0.5).sum()
        results.append({
            "group": group_name,
            "n_silenced": len(neuron_ids),
            "total_delta_hz": total_delta,
            "n_neurons_affected": n_affected,
        })
        print(f"    Total firing change: {total_delta:.1f} Hz | Neurons affected: {n_affected}")
    summary = pd.DataFrame(results).set_index("group")
    summary.to_csv(f"{PATH_RES}/perturbation_summary.csv")
    print(f"Summary saved to {PATH_RES}/perturbation_summary.csv")
    return summary

if __name__ == "__main__":
    df = pd.read_csv("Drosophila_brain_model/2023_03_23_completeness_630_final.csv", index_col=0)
    all_ids = df.index.tolist()
    candidates = [i for i in all_ids if i not in NEU_SUGAR]
    np.random.seed(42)
    test_groups = {
        "group_A": list(np.random.choice(candidates, 10, replace=False)),
        "group_B": list(np.random.choice(candidates, 10, replace=False)),
        "group_C": list(np.random.choice(candidates, 10, replace=False)),
    }
    summary = run_perturbation_sweep(test_groups, force=True)
    print(summary)
