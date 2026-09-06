import pandas as pd
import numpy as np
from pathlib import Path

def aggregate_perms(perms_df, stats_df, prefix="distance"):
    records = []
    groups = perms_df["group"].unique()
    for grp in groups:
        grp_perms = perms_df[perms_df["group"] == grp]
        delta_hz_null = grp_perms["delta_hz"].values
        
        # Get observed
        obs = stats_df.loc[stats_df["label"] == grp, "delta_hz"].values[0]
        
        n_silenced = grp_perms["n_silenced"].iloc[0]
        n_trials = grp_perms["n_trials_per_sim"].iloc[0]
        seed = grp_perms["seed"].iloc[0]
        n_perms = len(delta_hz_null)
        
        null_mean = np.mean(delta_hz_null)
        null_std = np.std(delta_hz_null, ddof=1) if len(delta_hz_null) > 1 else np.nan
        z_score = (obs - null_mean) / null_std if not np.isnan(null_std) and null_std > 0 else np.nan
        
        # p-values
        less_count = np.sum(delta_hz_null <= obs)
        greater_count = np.sum(delta_hz_null >= obs)
        p_one_sided = (min(less_count, greater_count) + 1) / (n_perms + 1)
        
        n_extreme_two = np.sum(np.abs(delta_hz_null - null_mean) >= abs(obs - null_mean))
        p_two_sided = (n_extreme_two + 1) / (n_perms + 1)
        
        records.append({
            f"group": grp,
            f"n_silenced": n_silenced,
            f"observed_delta_hz": obs,
            f"null_mean": null_mean,
            f"null_std": null_std,
            f"z_score": z_score,
            f"empirical_p_one_sided": p_one_sided,
            f"empirical_p_two_sided": p_two_sided,
            f"n_permutations": n_perms,
            f"n_trials_per_sim": n_trials,
            f"seed": seed
        })
    
    return pd.DataFrame(records)

def main():
    p = Path('results/jo_ground_truth_n20')
    stats = pd.read_csv(p / "statistics.csv")
    
    # Distance
    dist_perms = []
    for f in p.glob('jo_distance_matched_nulls_*_perms.csv'):
        dist_perms.append(pd.read_csv(f))
    if dist_perms:
        dist_df = pd.concat(dist_perms)
        agg_dist = aggregate_perms(dist_df, stats)
        agg_dist.to_csv(p / "jo_distance_matched_nulls.csv", index=False)
        print("Aggregated distance nulls")
        
    # Degree
    deg_perms = []
    for f in p.glob('jo_degree_matched_nulls_*_perms.csv'):
        deg_perms.append(pd.read_csv(f))
    if deg_perms:
        deg_df = pd.concat(deg_perms)
        agg_deg = aggregate_perms(deg_df, stats)
        agg_deg.to_csv(p / "jo_degree_matched_nulls.csv", index=False)
        print("Aggregated degree nulls")

if __name__ == "__main__":
    main()
