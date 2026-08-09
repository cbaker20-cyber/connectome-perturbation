import shutil
import hashlib
from pathlib import Path

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    raw_results_dir = Path("HUMAN_REVIEW/raw_results")
    raw_results_dir.mkdir(parents=True, exist_ok=True)
    
    key_csvs = [
        "results/context_comparison_JO_vs_sugar.csv",
        "results/effect_sizes_jo_n20.csv",
        "results/effect_sizes_sugar.csv",
        "results/jo_ground_truth_n20/null_comparison.csv",
        "results/jo_ground_truth_n20/statistics.csv",
        "results/sugar_ground_truth/statistics.csv",
        "results/jo_ground_truth_n20/residual_ranking_n20.csv"
    ]
    
    # Parquets might be too large to copy into git trackable HUMAN_REVIEW, so just hash them for manifest
    key_parquets = [
        "results/jo_ground_truth_n20/baseline_jo.parquet",
        "results/jo_ground_truth_n20/perturb_AN.parquet",
        "results/jo_ground_truth_n20/perturb_descending.parquet",
        "results/sugar_ground_truth/baseline_sugar.parquet",
        "results/sugar_ground_truth/perturb_AN.parquet",
        "results/sugar_ground_truth/perturb_descending.parquet",
    ]
    
    manifest_lines = ["# Freeze Manifest\n", "| File | Size (bytes) | SHA-256 |", "|---|---|---|"]
    
    for f in key_csvs:
        p = Path(f)
        if p.exists():
            dest = raw_results_dir / p.name
            # If name conflict, prefix it
            if "sugar_ground_truth" in str(p):
                dest = raw_results_dir / ("sugar_" + p.name)
            elif "jo_ground_truth_n20" in str(p) and p.name == "statistics.csv":
                dest = raw_results_dir / ("jo_n20_" + p.name)
            
            shutil.copy2(p, dest)
            size = p.stat().st_size
            sha = file_sha256(p)
            manifest_lines.append(f"| {p.as_posix()} | {size} | {sha} |")
    
    for f in key_parquets:
        p = Path(f)
        if p.exists():
            size = p.stat().st_size
            sha = file_sha256(p)
            manifest_lines.append(f"| {p.as_posix()} | {size} | {sha} |")
            
    manifest_path = Path("results/FREEZE_MANIFEST.md")
    manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")
    print(f"Wrote {manifest_path}")

if __name__ == "__main__":
    main()
