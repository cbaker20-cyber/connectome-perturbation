import pandas as pd
from pathlib import Path
import numpy as np

def main():
    jo_n20 = pd.read_csv("results/jo_ground_truth_n20/statistics.csv")
    jo_n5 = pd.read_csv("results/jo_ground_truth/statistics.csv")
    sugar = pd.read_csv("results/sugar_ground_truth/statistics.csv")
    
    jo_nulls_all = pd.read_csv("results/jo_ground_truth/jo_degree_matched_nulls_ALL_GROUPS.csv")
    jo_null_kc = pd.read_csv("results/jo_ground_truth/jo_degree_matched_nulls_Kenyon_Cell.csv")
    jo_nulls = pd.concat([jo_nulls_all, jo_null_kc], ignore_index=True)
    sugar_nulls = pd.read_csv("results/sugar_ground_truth/sugar_degree_matched_nulls.csv")
    
    # Prefix columns
    jo_n20 = jo_n20.rename(columns={"label": "group", "delta_hz": "delta_hz_jo_n20", "p_value_fdr": "fdr_jo"})
    sugar = sugar.rename(columns={"label": "group", "delta_hz": "delta_hz_sugar", "p_value_fdr": "fdr_sugar"})
    
    # Nulls
    jo_nulls = jo_nulls.rename(columns={"group": "group", "empirical_p_two_sided": "null_p_jo"})
    # Normalize group names just in case
    jo_nulls['group'] = jo_nulls['group'].str.lower()
    
    sugar_nulls = sugar_nulls.rename(columns={"group": "group", "empirical_p_two_sided": "null_p_sugar"})
    
    # Merge
    groups = jo_n20["group"].unique()
    rows = []
    
    for g in groups:
        g_lower = g.lower()
        
        # JO stats
        jo_stats_row = jo_n20[jo_n20["group"].str.lower() == g_lower]
        delta_hz_jo = jo_stats_row.iloc[0]["delta_hz_jo_n20"] if not jo_stats_row.empty else np.nan
        fdr_jo = jo_stats_row.iloc[0]["fdr_jo"] if not jo_stats_row.empty else np.nan
        
        # Sugar stats
        sugar_stats_row = sugar[sugar["group"].str.lower() == g_lower]
        delta_hz_sugar = sugar_stats_row.iloc[0]["delta_hz_sugar"] if not sugar_stats_row.empty else np.nan
        fdr_sugar = sugar_stats_row.iloc[0]["fdr_sugar"] if not sugar_stats_row.empty else np.nan
        
        # JO nulls
        jo_null_row = jo_nulls[jo_nulls["group"] == g_lower]
        null_p_jo = jo_null_row.iloc[0]["null_p_jo"] if not jo_null_row.empty else np.nan
        
        # Sugar nulls
        sugar_null_row = sugar_nulls[sugar_nulls["group"].str.lower() == g_lower]
        null_p_sugar = sugar_null_row.iloc[0]["null_p_sugar"] if not sugar_null_row.empty else np.nan
        
        rows.append({
            "group": g,
            "delta_hz_jo_n20": delta_hz_jo,
            "delta_hz_sugar": delta_hz_sugar,
            "fdr_jo": fdr_jo,
            "fdr_sugar": fdr_sugar,
            "null_p_jo": null_p_jo,
            "null_p_sugar": null_p_sugar,
            "notes": "null_p_jo is from n=5 sweep"
        })
        
    df = pd.DataFrame(rows)
    out_path = Path("results/context_comparison_JO_vs_sugar.csv")
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    print(df.to_markdown(index=False))

if __name__ == "__main__":
    main()
