import sys
from pathlib import Path
import json
import time

repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

if str(repo_root / "perturbation") not in sys.path:
    sys.path.insert(0, str(repo_root / "perturbation"))

from perturbation.statistics import run_statistics
import numpy as np
import pandas as pd
import importlib.util
from brian2 import Hz, ms

from scripts.run_degree_matched_nulls import (
    load_edge_weights, compute_weighted_degree, assign_degree_bins,
    degree_matched_sample, run_silencing_trial_rates, motor_rates_hz
)

def run():
    results_dir = repo_root / "results" / "sugar_ground_truth"
    
    # 1. Run statistics summary
    targets = [
        ("perturb_AN", "AN"),
        ("perturb_descending", "descending"),
        ("perturb_LO", "LO"),
        ("perturb_Kenyon_Cell", "Kenyon_Cell"),
        ("perturb_motor", "motor"),
    ]
    print("Running statistics summary...")
    stats_df = run_statistics(
        targets=targets,
        baseline_name="baseline_sugar",
        path_res=results_dir,
        output_name="statistics.csv",
        t_run=1.0
    )
    
    # 2. Run degree-matched nulls (20 perms)
    print("Preparing nulls...")
    jo_path = repo_root / "scripts" / "run_jo_sweep.py"
    spec = importlib.util.spec_from_file_location("run_jo_sweep", jo_path)
    jo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = jo
    spec.loader.exec_module(jo)
    
    from perturbation.baseline import NEU_SUGAR
    sugar_ids = list(NEU_SUGAR)
    
    group_specs = [
        {"name": "AN", "by": "cell_class", "value": "AN"},
        {"name": "descending", "by": "super_class", "value": "descending"},
        {"name": "LO", "by": "cell_class", "value": "LO"},
        {"name": "Kenyon_Cell", "by": "cell_class", "value": "Kenyon_Cell"},
        {"name": "motor", "by": "super_class", "value": "motor"},
    ]
    ann = jo.load_annotations(repo_root / "flywire_annotations.tsv")
    sim_ids = jo.load_sim_ids(repo_root / "2023_03_23_completeness_630_final.csv")
    groups = jo.select_perturbation_groups(ann, sim_ids, group_specs, exclude_ids=set(sugar_ids))
    
    edges = load_edge_weights(repo_root / "2023_03_23_connectivity_630_final.parquet")
    total_strength = compute_weighted_degree(edges)
    
    motor_ids = groups["motor"]
    
    baseline_df = pd.read_parquet(results_dir / "baseline_sugar.parquet")
    baseline_mean = float(np.mean(motor_rates_hz(baseline_df, motor_ids, t_run_s=1.0)))
    print(f"Motor neurons: {len(motor_ids)}; Sugar sensory: {len(sugar_ids)}; baseline motor mean: {baseline_mean:.2f} Hz")
    
    observed_deltas = stats_df["delta_hz"].to_dict()
    
    pool_ids = np.array(sorted(sim_ids))
    pool_ids = pool_ids[~np.isin(pool_ids, list(sugar_ids))]
    pool_bins = assign_degree_bins(total_strength.reindex(pool_ids).fillna(0), n_bins=10)
    
    rng = np.random.default_rng(42)
    all_results = []
    
    n_perms = 20
    n_trials = 5
    
    for group_name, group_ids in groups.items():
        print(f"\n{'=' * 60}\nGroup: {group_name} ({len(group_ids)} neurons)\n{'=' * 60}")
        obs_delta = observed_deltas[group_name]
        
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
                neuron_ids=null_sample,
                jo_ids=sugar_ids,
                motor_ids=motor_ids,
                path_comp=repo_root / "2023_03_23_completeness_630_final.csv",
                path_con=repo_root / "2023_03_23_connectivity_630_final.parquet",
                n_trials=n_trials,
                t_run_s=1.0
            )
            
            null_delta = float(np.mean(null_rates)) - baseline_mean
            null_deltas.append(null_delta)
            perm_records.append({
                "group": group_name,
                "perm_index": perm_i + 1,
                "delta_hz": round(null_delta, 4),
                "n_silenced": len(group_ids),
                "n_trials_per_sim": n_trials,
                "seed": 42,
            })
            print(f"  perm {perm_i + 1}/{n_perms}: dHz={null_delta:.2f} ({time.time() - t0:.0f}s)", flush=True)
            
        pd.DataFrame(perm_records).to_csv(
            results_dir / f"sugar_degree_matched_nulls_{group_name}_perms.csv", index=False)
        
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
            "seed": 42,
        })
        print(f"  obs={obs_delta:.2f} null_mean={null_mean:.2f} z={z_score:.2f} "
              f"p_one={p_one:.4f} p_two={p_two:.4f}")
              
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(results_dir / "sugar_degree_matched_nulls.csv", index=False)
    print(f"\nSaved results to {results_dir / 'sugar_degree_matched_nulls.csv'}")

if __name__ == "__main__":
    run()
