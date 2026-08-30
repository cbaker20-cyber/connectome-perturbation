import pandas as pd
from pathlib import Path

def build_effect_sizes(stats_path, out_path):
    stats_path = Path(stats_path)
    out_path = Path(out_path)
    if not stats_path.exists():
        return
        
    df = pd.read_csv(stats_path)
    effect_df = pd.DataFrame()
    effect_df["group"] = df["label"]
    effect_df["mean_delta_hz"] = df["delta_hz"]
    effect_df["abs_delta_hz"] = df["delta_hz"].abs()
    effect_df["percent_change"] = df["pct_change"]
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    effect_df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")

def build_null_comparison():
    degree = Path("results/jo_ground_truth_n20/jo_degree_matched_nulls.csv")
    dist = Path("results/jo_ground_truth_n20/jo_distance_matched_nulls.csv")
    
    groups = ["AN", "descending", "LO", "Kenyon_Cell", "motor"]
    
    df_deg = pd.read_csv(degree) if degree.exists() else pd.DataFrame(columns=["group"])
    df_dist = pd.read_csv(dist) if dist.exists() else pd.DataFrame(columns=["group"])
    
    # Just in case degree table is empty but we want to show all groups
    df_all = pd.DataFrame({"group": groups})
    
    if not df_deg.empty:
        df_deg = df_deg.add_prefix("degree_")
        df_deg = df_deg.rename(columns={"degree_group": "group"})
        df_all = pd.merge(df_all, df_deg, on="group", how="left")
    
    if not df_dist.empty:
        df_dist = df_dist.add_prefix("distance_")
        df_dist = df_dist.rename(columns={"distance_group": "group"})
        df_all = pd.merge(df_all, df_dist, on="group", how="left")
        
    out = Path("results/jo_ground_truth_n20/null_comparison.csv")
    df_all.to_csv(out, index=False)
    print(f"Wrote {out}")

def main():
    build_effect_sizes("results/jo_ground_truth_n20/statistics.csv", "results/effect_sizes_jo_n20.csv")
    build_effect_sizes("results/sugar_ground_truth/statistics.csv", "results/effect_sizes_sugar.csv")
    build_null_comparison()

if __name__ == "__main__":
    main()
