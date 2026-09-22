from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .common import atomic_json, atomic_parquet, fingerprint, now, read_json, sha256, sugar_ids

DEGREE_FEATURES = ["in_degree", "out_degree", "in_strength", "out_strength"]
FULL_FEATURES = DEGREE_FEATURES + ["baseline_hz", "strong_out_mass"]


def standardized_difference(target, sample):
    denominator = np.sqrt((np.var(target, axis=0) + np.var(sample, axis=0))/2)
    difference = np.abs(target.mean(0)-sample.mean(0))
    return np.divide(difference, denominator, out=np.where(difference == 0, 0., np.inf), where=denominator > 0)


def matched_sets(features, target_ids, excluded_ids=(), n_sets=199, seed=630600,
                 full=True, max_attempts=50000):
    f = features.copy()
    f.root_id = f.root_id.astype(str)
    if f.root_id.duplicated().any() or len(set(target_ids)) != len(target_ids):
        raise ValueError("duplicate feature or target IDs")
    if not len(target_ids) or not set(target_ids) <= set(f.root_id):
        raise ValueError("empty/unknown target")
    columns = FULL_FEATURES if full else DEGREE_FEATURES
    values = f[columns].to_numpy(dtype=float)
    if not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("matching features must be finite and nonnegative")
    transformed = np.log1p(values)
    scale = transformed.std(0)
    scale[scale == 0] = 1.
    z = transformed/scale
    target_mask = f.root_id.isin(target_ids).to_numpy()
    pool_mask = ~f.root_id.isin(set(target_ids) | set(excluded_ids)).to_numpy()
    target_idx = np.where(target_mask)[0]
    if full:
        strata = list(zip(f.model_sign.astype(str), f.recruited.astype(bool)))
    else:
        strata = [("all", True)] * len(f)
    # Each neuron can only draw from its exact sign/recruitment stratum.
    groups = {}
    for key in {strata[i] for i in target_idx}:
        pool = np.asarray([i for i in np.where(pool_mask)[0] if strata[i] == key], dtype=int)
        needed = sum(strata[i] == key for i in target_idx)
        if len(pool) < needed:
            raise ValueError(f"insufficient distinct controls in stratum {key}: {len(pool)} < {needed}")
        groups[key] = (pool, cKDTree(z[pool]))
    neighbors = {}
    for i in target_idx:
        pool, tree = groups[strata[i]]
        distance, index = tree.query(z[i], k=min(64, len(pool)))
        neighbors[i] = (pool[np.atleast_1d(index)], np.atleast_1d(distance))
    rng = np.random.default_rng(seed)
    accepted, seen, balances = [], set(), []
    target = transformed[target_idx]
    attempts = 0
    for attempts in range(1, max_attempts+1):
        used = set()
        for i in rng.permutation(target_idx):
            candidates, distances = neighbors[i]
            keep = np.asarray([j not in used for j in candidates])
            if not keep.any():
                break
            candidates, distances = candidates[keep], distances[keep]
            weights = np.exp(-(distances-distances.min()))
            used.add(int(rng.choice(candidates, p=weights/weights.sum())))
        if len(used) != len(target_idx):
            continue
        indices = sorted(used)
        selected = tuple(sorted(f.iloc[indices].root_id))
        if selected in seen:
            continue
        balance = standardized_difference(target, transformed[indices])
        if np.any(balance > .1):
            continue
        seen.add(selected)
        accepted.append(list(selected))
        balances.append(dict(zip(columns, map(float, balance))))
        if len(accepted) == n_sets:
            break
    return accepted, {"attempts": attempts, "requested": n_sets, "accepted": len(accepted),
                      "complete": len(accepted) == n_sets, "seed": seed, "features": columns,
                      "smd_limit": .1, "balances": balances,
                      "sampler": "randomized nearest-64 matching; exp(-distance), exact strata when full",
                      "inference": "conditional matched-reference comparison, not uniform graph randomization"}


def generate(features_path, mode_dir, out, full=True, n_sets=199):
    out = Path(out)
    if (out / "manifest.json").exists():
        raise FileExistsError("control output exists")
    f = pd.read_parquet(features_path)
    selected = read_json(Path(mode_dir) / "selection.json")
    if selected["status"] != "selected":
        raise ValueError("no selected mode")
    sets, summary = matched_sets(f, selected["root_ids"], sugar_ids(), n_sets=n_sets, full=full)
    out.mkdir(parents=True, exist_ok=True)
    rows = [{"control": i, "root_id": neuron} for i, ids in enumerate(sets) for neuron in ids]
    atomic_parquet(out / "controls.parquet", pd.DataFrame(rows, columns=["control", "root_id"]))
    overlap = [{"a": i, "b": j, "shared": len(set(a)&set(b)),
                "jaccard": len(set(a)&set(b))/len(set(a)|set(b))}
               for i, a in enumerate(sets) for j, b in enumerate(sets) if i < j]
    atomic_parquet(out / "overlap.parquet", pd.DataFrame(overlap, columns=["a", "b", "shared", "jaccard"]))
    atomic_json(out / "manifest.json", {**summary, "created_utc": now(), "full_matching": full,
                "target_ids": selected["root_ids"], "features_sha256": sha256(features_path),
                "selection_sha256": sha256(Path(mode_dir) / "selection.json"),
                "controls_sha256": sha256(out / "controls.parquet"),
                "status": "ready" if summary["complete"] else "insufficient_matches"})
    if not summary["complete"]:
        raise RuntimeError(f"Only {len(sets)}/{n_sets} acceptable sets; confirmation is blocked")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--features", required=True)
    p.add_argument("--modes", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--pilot", action="store_true")
    a = p.parse_args()
    generate(a.features, a.modes, a.out, full=not a.pilot, n_sets=5 if a.pilot else 199)


if __name__ == "__main__":
    main()
