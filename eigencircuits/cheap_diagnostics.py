"""Descriptive overlap/strength diagnostics, without scientific rejection cutoffs."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from .common import atomic_json, atomic_parquet, sha256


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b)/len(a | b) if a or b else 1.


def diagnose(mode_dir, features_path):
    mode_dir = Path(mode_dir)
    membership = pd.read_parquet(mode_dir/"membership.parquet")
    f = pd.read_parquet(features_path).set_index("root_id")
    rows, sets = [], {}
    for rank, members in membership.groupby("mode_rank"):
        s = set(members.root_id)
        sets[int(rank)] = s
        selected = f.reindex(members.root_id)
        topn = f.out_strength.nlargest(len(s)).index
        rho = spearmanr(members.power_frac.to_numpy(), selected.out_strength.to_numpy()).statistic
        rows.append({"mode_rank": rank, "jaccard_topn_outstrength": jaccard(s, topn),
                     "loading_strength_spearman": float(rho),
                     "n_members": len(s), "n_recruited": int(selected.recruited.sum()),
                     "mean_strong_out_mass": float(selected.strong_out_mass.mean())})
    atomic_parquet(mode_dir/"diagnostics.parquet", pd.DataFrame(rows))
    overlaps = [{"mode_a": a, "mode_b": b, "support_jaccard": jaccard(sa, sb)}
                for a, sa in sets.items() for b, sb in sets.items() if a < b]
    atomic_parquet(mode_dir/"support_overlap.parquet", pd.DataFrame(overlaps))
    atomic_json(mode_dir/"diagnostics_manifest.json", {"features_sha256": sha256(features_path),
                "membership_sha256": sha256(mode_dir/"membership.parquet"),
                "interpretation": "descriptive overlaps; neither orthogonality nor support overlap proves dynamical independence"})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modes", required=True)
    p.add_argument("--features", required=True)
    a = p.parse_args()
    diagnose(a.modes, a.features)
