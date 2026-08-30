import pandas as pd
from scipy import stats
from pathlib import Path

def main():
    surrogate_csv = Path("results/jo_ground_truth/surrogate_vs_ground_truth.csv")
    stats_csv = Path("results/jo_ground_truth_n20/statistics.csv")
    out_path = Path("results/jo_ground_truth_n20/residual_ranking_n20.csv")
    
    surrogate = pd.read_csv(surrogate_csv)
    stats_df = pd.read_csv(stats_csv)
    
    # Merge on group name
    surrogate = surrogate.rename(columns={"target_class": "group"})
    stats_df = stats_df.rename(columns={"label": "group"})
    
    merged = pd.merge(stats_df[["group", "delta_hz"]], surrogate[["group", "mean_modal_controllability", "n_silenced"]], on="group")
    
    # Rank groups by observed |ΔHz| or ΔHz.
    # The original script did: 1 = most negative dHz (strongest suppression)
    merged["rank_by_observed_delta_hz"] = merged["delta_hz"].rank(method="min", ascending=True).astype(int)
    # Rank by structural predictor(s)
    # 1 = highest mean modal controllability
    merged["rank_by_structural"] = merged["mean_modal_controllability"].rank(method="min", ascending=False).astype(int)
    
    merged["rank_difference"] = merged["rank_by_structural"] - merged["rank_by_observed_delta_hz"]
    
    merged = merged.sort_values("rank_by_observed_delta_hz").reset_index(drop=True)
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)
    
    print("\n=== Residual / ranking comparison (metric: mean modal controllability) ===")
    print(merged.to_string(index=False))
    
    rho, p = stats.spearmanr(merged["rank_by_observed_delta_hz"], merged["rank_by_structural"])
    print(f"\nSpearman(observed rank, structural rank): rho={rho:.3f}, p={p:.3f} (n={len(merged)})")
    print(f"Mean |rank difference|: {merged['rank_difference'].abs().mean():.2f}")
    
if __name__ == "__main__":
    main()
