from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list, fcluster, dendrogram
from scipy.spatial.distance import squareform

from .common import (ANN, MN9, atomic_json, atomic_parquet, load_trials, now,
                     root_ids, sha256, sugar_ids, provenance, SELECTION_SEEDS)
from .graph import features, load_signed_matrix
from .recruitment_from_parquet import bin_spikes, recruitment


def cluster_matrix(x):
    flat = x.reshape(len(x), -1)
    valid = flat.std(axis=1) > 0
    if valid.sum() < 2:
        return valid, np.empty((0, 0)), np.empty((0, 4)), np.array([], dtype=int)
    corr = np.clip(np.corrcoef(flat[valid]), -1., 1.)
    np.fill_diagonal(corr, 1.)
    distance = np.maximum(0., 1.-corr)
    tree = linkage(squareform(distance, checks=False), method="average", optimal_ordering=False)
    labels = fcluster(tree, t=.7, criterion="distance")
    return valid, corr, tree, labels


def adjusted_rand(a, b):
    if len(a) != len(b) or len(a) < 2:
        return None
    _, ai = np.unique(a, return_inverse=True)
    _, bi = np.unique(b, return_inverse=True)
    n = np.zeros((ai.max()+1, bi.max()+1), dtype=int)
    np.add.at(n, (ai, bi), 1)
    pairs = lambda v: np.sum(v*(v-1)/2)
    nij, na, nb, total = pairs(n), pairs(n.sum(1)), pairs(n.sum(0)), len(a)*(len(a)-1)/2
    expected = na*nb/total
    denominator = (na+nb)/2-expected
    return float((nij-expected)/denominator) if denominator else 1.


def coherence(corr, labels):
    ii, jj = np.triu_indices(len(corr), 1)
    mask = labels[ii] == labels[jj]
    return float(corr[ii[mask], jj[mask]].mean()) if mask.any() else 0.


def surrogate_checks(x, seed=630400, n=99):
    rng = np.random.default_rng(seed)
    rows = []
    for kind in ["circular_shift", "trial_shuffle"]:
        for replicate in range(n):
            y = x.copy()
            for cell in range(len(y)):
                if kind == "trial_shuffle":
                    y[cell] = y[cell, rng.permutation(y.shape[1])]
                else:
                    for trial in range(y.shape[1]):
                        shift = rng.integers(1, y.shape[2])
                        y[cell, trial] = np.roll(y[cell, trial], shift)
            _, c, _, labels = cluster_matrix(y)
            rows.append({"surrogate": kind, "replicate": replicate,
                         "within_group_mean_r": coherence(c, labels) if len(labels) else 0.})
    return pd.DataFrame(rows)


def select_cells(f, clusters, n_trials, seed=630500):
    rng = np.random.default_rng(seed)
    table = f.merge(clusters[["root_id", "cluster"]], on="root_id", how="left")
    table = table[~table.root_id.isin(sugar_ids())].copy()
    selected, selected_ids = [], set()
    for label in ["excitatory", "inhibitory"]:
        pool = table[(table.model_sign == label) & (table.classical_fast == label)
                     & (table.shiu_2024 == label) & (table.trials_recruited >= max(2, (n_trials+1)//2))
                     & table.cluster.notna()].copy()
        if len(pool) < 10:
            raise ValueError(f"only {len(pool)} eligible {label} cells; cannot freeze 10")
        pool["rate_bin"] = pd.qcut(pool.baseline_hz.rank(method="first"), 3, labels=False)
        # Round-robin through cluster/rate strata; randomize ties within strata.
        bins = []
        for _, g in pool.groupby(["cluster", "rate_bin"], sort=True):
            bins.append(rng.permutation(g.index).tolist())
        rng.shuffle(bins)
        chosen = []
        while len(chosen) < 10:
            for bucket in bins:
                if bucket and len(chosen) < 10:
                    chosen.append(bucket.pop())
        for idx in chosen:
            r = table.loc[idx]
            selected.append({"root_id": r.root_id, "role": label, "cluster": int(r.cluster),
                             "rate_bin": int(pool.loc[idx, "rate_bin"]),
                             "baseline_hz": float(r.baseline_hz), "model_sign": r.model_sign,
                             "classical_fast": r.classical_fast, "shiu_2024": r.shiu_2024})
            selected_ids.add(r.root_id)
    used_clusters = {x["cluster"] for x in selected}
    outside = table[table.recruited & table.cluster.notna() & ~table.cluster.isin(used_clusters)]
    for idx in rng.permutation(outside.index)[:2]:
        r = table.loc[idx]
        selected.append({"root_id": r.root_id, "role": "outside_block", "cluster": int(r.cluster),
                         "baseline_hz": float(r.baseline_hz)})
    silent = table[(~table.recruited) & table.annotation_available & (table.model_sign == "inhibitory")]
    if len(silent):
        r = silent.iloc[int(rng.integers(len(silent)))]
        selected.append({"root_id": r.root_id, "role": "silent_control", "baseline_hz": 0.})
    return {"seed": seed, "created_utc": now(), "cells": selected,
            "n_trials": n_trials, "outside_block_available": min(2, len(outside)),
            "selection_basis": "baseline only; ACh/GABA labels agree with model sign; repeated recruitment"}


def analyze(pilot, out=None, n_surrogates=99):
    pilot = Path(pilot)
    out = Path(out) if out else pilot / "analysis"
    if (out / "selection.json").exists():
        raise FileExistsError("selection is frozen; use a new output directory for a new analysis")
    paths = sorted(pilot.glob("trials/baseline_*/manifest.json"))
    paths = [p.parent for p in paths if __import__('json').loads(p.read_text())["status"] == "complete"]
    spikes, manifests = load_trials(paths)
    signatures = {(tuple(sorted(m["provenance"]["inputs"].items())), m["duration_s"], m["dt_ms"],
                   m["input_hz"], m["backend"], m.get("input_protocol"),
                   tuple((key, m["provenance"]["sources"].get(key)) for key in
                         ["model.py", "eigencircuits/trials.py", "eigencircuits/common.py"])) for m in manifests}
    if len(signatures) != 1 or len({m["seed"] for m in manifests}) != len(manifests):
        raise ValueError("baseline inputs/settings differ or seeds repeat")
    if any(m["provenance"]["inputs"] != provenance()["inputs"] for m in manifests):
        raise ValueError("current input files differ from baseline inputs")
    for m in manifests:
        if m.get("input_protocol") != "fixed_binomial_tape_v1":
            raise ValueError("selection requires corrected state-independent input protocol")
        if m["context"] != "sugar" or m["lesion_ids"] or m["weight_scale"] != 1 or m["inhibitory_scale"] != 1 or m["strong_fraction"] is not None:
            raise ValueError("selection requires unmodified sugar baselines")
    if len(manifests) == 5 and {m["seed"] for m in manifests} != set(SELECTION_SEEDS):
        raise ValueError("unexpected selection seeds")
    w, ids = load_signed_matrix()
    f = features(w, ids)
    del w
    trials = [m["trial_id"] for m in manifests]
    r = recruitment(spikes, ids, trials)
    f = f.merge(r, on="root_id", validate="one_to_one")
    out.mkdir(parents=True, exist_ok=True)
    atomic_parquet(out / "features.parquet", f)
    # Keep all annotation-missing neurons in the activity analysis.
    sensory = set(sugar_ids())
    eligible = f.loc[f.recruited & ~f.root_id.isin(sensory), "root_id"].to_numpy()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    summaries = []
    primary_clusters = None
    for bin_ms, floor in [(10, 1), (5, 1), (20, 1), (10, 5)]:
        chosen = f.loc[(f.spike_count >= floor) & ~f.root_id.isin(sensory), "root_id"].to_numpy()
        x = bin_spikes(spikes, chosen, trials, bin_ms)
        valid, corr, tree, labels = cluster_matrix(x)
        name = f"bins_{bin_ms}ms_min_{floor}"
        atomic_json(out / (name+"_excluded.json"), {"constant_rows": chosen[~valid].tolist()})
        if not len(labels):
            summaries.append({"analysis": name, "status": "too_few_variable_neurons"})
            continue
        chosen = chosen[valid]
        x = x[valid]
        order = leaves_list(tree)
        np.savez_compressed(out / (name+".npz"), correlation=corr, root_ids=chosen, order=order, linkage=tree)
        clusters = pd.DataFrame({"root_id": chosen, "cluster": labels})
        atomic_parquet(out / (name+"_clusters.parquet"), clusters)
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
        for ax, matrix, title in zip(axes, [corr, corr[np.ix_(order, order)]], ["Original neuron order", "Average-linkage order"]):
            im = ax.imshow(matrix, vmin=-1, vmax=1, cmap="RdBu_r", interpolation="nearest")
            ax.set(title=title, xlabel="Neuron index", ylabel="Neuron index")
        fig.colorbar(im, ax=axes, label="Pearson r", shrink=.7)
        fig.suptitle(f"Sugar baseline: {bin_ms} ms bins, {len(trials)} trials, minimum {floor} spike(s)")
        fig.savefig(out / (name+".png"), dpi=160)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(10, 3))
        dendrogram(tree, no_labels=True, ax=ax)
        ax.axhline(.7, color="black", linestyle="--", linewidth=.7)
        ax.set(xlabel="Neuron ordering", ylabel="1 - correlation", title="Provisional grouping; cut = 0.7")
        fig.tight_layout()
        fig.savefig(out / (name+"_dendrogram.png"), dpi=150)
        plt.close(fig)
        summary = {"analysis": name, "n_neurons": len(chosen), "n_clusters": len(set(labels)),
                   "largest_cluster": int(pd.Series(labels).value_counts().max()),
                   "within_group_mean_r": coherence(corr, labels)}
        if bin_ms == 10 and floor == 1:
            primary_clusters = clusters
            atomic_parquet(out / "surrogates.parquet", surrogate_checks(x, n=n_surrogates))
            split = len(trials)//2
            if split:
                av, _, _, al = cluster_matrix(x[:, :split])
                bv, _, _, bl = cluster_matrix(x[:, split:])
                common = av & bv
                if len(al) and len(bl):
                    aa = dict(zip(np.where(av)[0], al)); bb = dict(zip(np.where(bv)[0], bl))
                    summary["split_trial_ARI"] = adjusted_rand([aa[i] for i in np.where(common)[0]], [bb[i] for i in np.where(common)[0]])
                    summary["split_common_cells"] = int(common.sum())
        summaries.append(summary)
    atomic_json(out / "correlation_summary.json", summaries)
    per_trial = []
    motor = set(f.loc[f.super_class == "motor", "root_id"])
    for m in manifests:
        d = spikes[spikes.trial == m["trial_id"]]
        motor_hz = float(d.flywire_id.isin(motor).sum())/m["duration_s"]
        per_trial.append({"trial": m["trial_id"], "seed": m["seed"], "recruited_noninput": len(set(d.flywire_id)-sensory),
                          "mn9_hz": float((d.flywire_id == MN9).sum())/m["duration_s"],
                          "motor_total_hz": motor_hz, "motor_mean_hz": motor_hz/len(motor) if motor else None,
                          "wall_seconds": m["wall_seconds"], "peak_rss_bytes": m["peak_rss_bytes"]})
    atomic_json(out / "baseline_summary.json", per_trial)
    atomic_json(out / "analysis_manifest.json", {"created_utc": now(), "prospective": True,
                "input_protocol": "fixed_binomial_tape_v1", "provenance": provenance(),
                "n_trials": len(trials), "trial_ids": trials, "seeds": [m["seed"] for m in manifests],
                "sources": {str(p / "manifest.json"): sha256(p / "manifest.json") for p in paths},
                "bin_widths_ms": [10, 5, 20], "cut_distance": .7, "n_surrogates_each": n_surrogates,
                "surrogate_seed": 630400, "claim_status": "descriptive_functional_clusters"})
    if primary_clusters is not None and len(trials) == 5:
        selected = select_cells(f, primary_clusters, len(trials))
        selected["features_sha256"] = sha256(out / "features.parquet")
        atomic_json(out / "selection.json", selected)
    print(f"Analyzed {len(trials)} trials; output: {out}", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", required=True)
    p.add_argument("--out")
    p.add_argument("--n-surrogates", type=int, default=99)
    a = p.parse_args()
    analyze(a.pilot, a.out, a.n_surrogates)


if __name__ == "__main__":
    main()
