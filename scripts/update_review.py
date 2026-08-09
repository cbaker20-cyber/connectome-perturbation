import pandas as pd
from pathlib import Path
import csv

f = Path("HUMAN_REVIEW/02_Current_Verified_Results.md")
content = f.read_text(encoding="utf-8")

def df_to_md(df):
    header = "| " + " | ".join(df.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(x) for x in row.values) + " |")
    return "\n".join([header, sep] + rows)

jo_n20 = pd.read_csv("results/jo_ground_truth_n20/statistics.csv")
sugar_stats = pd.read_csv("results/sugar_ground_truth/statistics.csv")
sugar_nulls = pd.read_csv("results/sugar_ground_truth/sugar_degree_matched_nulls.csv")
kenyon_null = pd.read_csv("results/jo_ground_truth/jo_degree_matched_nulls_Kenyon_Cell.csv")

new_content = f"""

---

## 4. JO n=20 Sweep Statistics

Source: `results/jo_ground_truth_n20/statistics.csv`

{df_to_md(jo_n20)}

---

## 5. Sugar Ground Truth Sweep Statistics

Source: `results/sugar_ground_truth/statistics.csv`

{df_to_md(sugar_stats)}

---

## 6. Sugar Degree-Matched Nulls

Source: `results/sugar_ground_truth/sugar_degree_matched_nulls.csv`

{df_to_md(sugar_nulls)}

---

## 7. Kenyon Cell Null Result (JO context)

Source: `results/jo_ground_truth/jo_degree_matched_nulls_Kenyon_Cell.csv`

{df_to_md(kenyon_null)}
"""

f.write_text(content + new_content, encoding="utf-8")

# If there is a raw_results directory inside HUMAN_REVIEW, update its copy as well
raw_copy = Path("HUMAN_REVIEW/raw_results/02_Current_Verified_Results.md")
if raw_copy.exists():
    raw_copy.write_text(content + new_content, encoding="utf-8")
print("Updated HUMAN_REVIEW")
