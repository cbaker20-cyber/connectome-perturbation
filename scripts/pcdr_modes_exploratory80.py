"""Exploratory 21 September amendment; frozen original builder is unchanged."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.sparse.linalg import eigs

from eigencircuits.common import atomic_json, atomic_parquet, now, provenance, read_json, sha256, sugar_ids
from eigencircuits.graph import load_signed_matrix


def power75(v, frac=.75):
    v = np.asarray(v)
    if v.ndim != 1 or not np.isfinite(v).all() or not 0 < frac <= 1:
        raise ValueError("invalid eigenvector or power fraction")
    power = np.abs(v)**2
    if power.sum() <= 0:
        raise ValueError("zero eigenvector has no support")
    order = np.argsort(-power, kind="stable")
    k = min(len(order), int(np.searchsorted(np.cumsum(power[order]), frac*power.sum()))+1)
    return order[:k]


def unique_modes(values, tolerance=1e-7):
    """Pair conjugates, but do not collapse distinct eigenvalues of equal magnitude."""
    order = np.argsort(-np.abs(values), kind="stable")
    used, rows = set(), []
    for i in order:
        if int(i) in used:
            continue
        lam = values[i]
        used.add(int(i))
        partner = None
        complete = True
        if abs(lam.imag) > tolerance * max(1., abs(lam)):
            candidates = [int(j) for j in order if int(j) not in used and
                          abs(values[j]-lam.conjugate()) <= tolerance*max(1., abs(lam))]
            if candidates:
                partner = min(candidates, key=lambda j: abs(values[j]-lam.conjugate()))
                used.add(partner)
            else:
                complete = False
        rows.append((int(i), partner, complete))
    return rows


def solve(w, k, seed):
    n = w.shape[0]
    if n < 3 or k < 1:
        raise ValueError("need at least three neurons and positive k")
    if k >= n-1:
        vals, vecs = np.linalg.eig(w.toarray())
    else:
        vals, vecs = eigs(w, k=k, which="LM", v0=np.random.default_rng(seed).normal(size=n),
                          tol=1e-9, maxiter=10000, ncv=min(n, max(2*k+1, 40)))
    order = np.argsort(-abs(vals), kind="stable")
    vals, vecs = vals[order], vecs[:, order]
    action = w @ vecs
    residuals = np.linalg.norm(action-vecs*vals, axis=0) / np.maximum(
        np.linalg.norm(action, axis=0) + abs(vals)*np.linalg.norm(vecs, axis=0), 1e-30)
    if not np.all(residuals < 1e-6):
        raise ValueError("eigenpair residual exceeds 1e-6")
    return vals, vecs, residuals


def stability(values, vectors, other_values, other_vectors):
    cost = abs(values[:, None]-other_values[None, :]) / np.maximum(1., abs(values[:, None]))
    left, right = linear_sum_assignment(cost)
    matched = dict(zip(left, right))
    result = []
    for i, lam in enumerate(values):
        j = matched[i]
        distances = abs(values-lam) / max(1., abs(lam))
        distances[i] = np.inf
        degenerate = bool(np.any(distances < 1e-6))
        a, b = set(power75(vectors[:, i])), set(power75(other_vectors[:, j]))
        overlap = abs(np.vdot(vectors[:, i], other_vectors[:, j])) / (
            np.linalg.norm(vectors[:, i])*np.linalg.norm(other_vectors[:, j]))
        result.append({"stable": bool(not degenerate and cost[i, j] < 1e-6 and a == b and overlap > .999),
                       "near_degenerate": degenerate, "support_jaccard": len(a & b)/len(a | b),
                       "vector_overlap": float(overlap), "second_index": int(j)})
    return result


def build(out, baseline_features, seed=630400):
    out = Path(out)
    if (out / "manifest.json").exists():
        raise FileExistsError("mode output already exists; use a new directory")
    f = pd.read_parquet(baseline_features).set_index("root_id")
    baseline_manifest = read_json(Path(baseline_features).parent / "analysis_manifest.json")
    if baseline_manifest["n_trials"] != 5 or not baseline_manifest["prospective"]:
        raise ValueError("mode selection needs five prospective baseline trials")
    w, ids = load_signed_matrix()
    if not set(ids) <= set(f.index):
        raise ValueError("features missing model neurons")
    k = 80
    vals, vecs, residuals = solve(w, k, seed)
    vals2, vecs2, _ = solve(w, k, seed+1)
    stable = stability(vals, vecs, vals2, vecs2)
    counts = f.reindex(ids).spike_count.to_numpy()
    rows, members = [], []
    stable_rank = 0
    for rank, (i, partner, complete) in enumerate(unique_modes(vals)):
        support = power75(vecs[:, i])
        power = abs(vecs[:, i])**2
        recruited_power = float(power[counts > 0].sum()/power.sum())
        eligible_n = int(np.count_nonzero(counts[support] >= 5))
        row = {"mode_rank": rank, "eig_index": i, "partner": partner, "complete_pair": complete,
               "lambda_real": float(vals[i].real), "lambda_imag": float(vals[i].imag),
               "abs_lambda": float(abs(vals[i])), "residual": float(residuals[i]),
               "n_75": len(support), "recruited_power": recruited_power,
               "support_cells_with_five_spikes": eligible_n, **stable[i]}
        row["contains_sensory_input"] = bool(set(ids[support]) & set(sugar_ids()))
        row["stable_mode_rank"] = stable_rank if complete and row["stable"] else None
        if complete and row["stable"]:
            stable_rank += 1
        row["eligible"] = bool(row["stable_mode_rank"] is not None and row["stable_mode_rank"] < 40 and eligible_n >= 10
                               and not row["contains_sensory_input"])
        rows.append(row)
        members.extend({"mode_rank": rank, "root_id": str(ids[j]), "neuron_index": int(j),
                        "loading_real": float(vecs[j, i].real), "loading_imag": float(vecs[j, i].imag),
                        "power_frac": float(power[j]/power.sum())} for j in support)
    candidates = sorted((r for r in rows if r["eligible"]), key=lambda r: (-r["recruited_power"], -r["abs_lambda"], r["mode_rank"]))
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "eigenpairs.npz", eigenvalues=vals, eigenvectors=vecs, root_ids=ids)
    atomic_parquet(out / "modes.parquet", pd.DataFrame(rows))
    atomic_parquet(out / "membership.parquet", pd.DataFrame(members))
    selected = candidates[0]["mode_rank"] if candidates else None
    atomic_json(out / "selection.json", {"mode_rank": selected, "status": "selected" if candidates else "no_eligible_mode",
                "root_ids": [r["root_id"] for r in members if r["mode_rank"] == selected],
                "selection_rule": "greatest recruited power among first 40 stable complete modes; exploratory amendment; magnitude breaks ties"})
    atomic_json(out / "manifest.json", {"created_utc": now(), "k": k, "seeds": [seed, seed+1],
                "matrix": "W[post,pre] signed synapse counts; global .275mV scale does not change eigenvectors",
                "provenance": provenance(), "features_sha256": sha256(baseline_features),
                "status": "selected" if candidates else "no_eligible_mode",
                "claim_status": "exploratory_structural_search", "candidate_limit": 40, "complete_candidate_search": stable_rank >= 40})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--features", required=True)
    a = p.parse_args()
    build(a.out, a.features)


if __name__ == "__main__":
    main()
