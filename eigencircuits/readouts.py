from __future__ import annotations

from pathlib import Path
import itertools

import numpy as np
import pandas as pd

from .common import MN9, atomic_json, atomic_parquet, now, read_json, sha256


def paired_deltas(baseline_dirs, lesion_dirs, ids):
    baseline = {read_json(Path(p)/"manifest.json")["seed"]: Path(p) for p in baseline_dirs}
    lesions = {read_json(Path(p)/"manifest.json")["seed"]: Path(p) for p in lesion_dirs}
    if len(baseline) != len(baseline_dirs) or len(lesions) != len(lesion_dirs):
        raise ValueError("repeated trial seeds")
    if set(baseline) != set(lesions) or not baseline:
        raise ValueError("paired seed sets differ or are empty")
    rows = []
    for seed in sorted(baseline):
        a, b = [read_json(p/"manifest.json") for p in [baseline[seed], lesions[seed]]]
        if a["status"] != "complete" or b["status"] != "complete":
            raise ValueError("incomplete trial")
        for key in ["duration_s", "dt_ms", "context", "input_hz", "input_protocol", "weight_scale", "inhibitory_scale", "strong_fraction", "backend", "input_digest"]:
            if a[key] != b[key]:
                raise ValueError(f"unmatched baseline/lesion {key}")
        if a["provenance"]["inputs"] != b["provenance"]["inputs"]:
            raise ValueError("different input datasets")
        for source in ["model.py", "eigencircuits/trials.py", "eigencircuits/common.py", "perturbation/baseline.py"]:
            sa = {k.replace("\\", "/"): v for k, v in a["provenance"]["sources"].items()}
            sb = {k.replace("\\", "/"): v for k, v in b["provenance"]["sources"].items()}
            if sa[source] != sb[source]:
                raise ValueError(f"simulation source differs: {source}")
        rates = []
        for path, m in [(baseline[seed], a), (lesions[seed], b)]:
            if sha256(path/"rates.parquet") != m["outputs"]["rates.parquet"]:
                raise ValueError("rate checksum mismatch")
            r = pd.read_parquet(path/"rates.parquet").set_index("root_id")
            if not r.index.is_unique or set(r.index) != set(ids):
                raise ValueError("rate neuron universe mismatch")
            rates.append(r.reindex(ids).rate_hz.to_numpy())
        rows.append(rates[1]-rates[0])
    return np.asarray(rows), sorted(baseline)


def footprint(delta, support):
    delta, support = np.asarray(delta, dtype=float), np.asarray(support, dtype=int)
    if delta.ndim != 1 or not np.isfinite(delta).all() or not len(support):
        raise ValueError("invalid delta or empty support")
    if len(set(support)) != len(support) or np.any((support < 0) | (support >= len(delta))):
        raise ValueError("duplicate or invalid support indices")
    absolute = abs(delta)
    inside = float(absolute[support].sum())
    total = float(absolute.sum())
    return {"A": inside/len(support), "F": inside/total if total else None,
            "on_absolute_sum_hz": inside, "off_absolute_sum_hz": total-inside,
            "on_signed_mean_hz": float(delta[support].mean()), "total_absolute_sum_hz": total}


def bootstrap_footprint(deltas, support, seed=630700, n=2000):
    deltas = np.asarray(deltas)
    if len(deltas) < 2:
        return {"status": "one_pair_no_interval"}
    active = np.any(deltas != 0, axis=0)
    active_indices = np.where(active)[0]
    inside = np.isin(active_indices, support)
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(deltas), np.full(len(deltas), 1/len(deltas)), size=n)/len(deltas)
    means = abs(weights @ deltas[:, active])
    sums = means[:, inside].sum(1)
    totals = means.sum(1)
    a = sums/len(support)
    f = np.divide(sums, totals, out=np.full(n, np.nan), where=totals > 0)
    return {"seed": seed, "replicates": n, "A_95pct": np.quantile(a, [.025, .975]).tolist(),
            "F_95pct": np.nanquantile(f, [.025, .975]).tolist() if np.isfinite(f).any() else None,
            "zero_response_bootstraps": int((totals == 0).sum())}


def reference_test(observed, controls):
    if not controls:
        raise ValueError("no controls")
    p_a = (1+sum(c["A"] >= observed["A"] for c in controls))/(1+len(controls))
    # Undefined concentration cannot establish superiority, either for target or controls.
    p_f = 1. if observed["F"] is None else (1+sum(c["F"] is None or c["F"] >= observed["F"] for c in controls))/(1+len(controls))
    return {"p_A": p_a, "p_F": p_f, "p_conjunction": max(p_a, p_f), "n_controls": len(controls),
            "interpretation": "conditional matched-reference test; no biological replication"}


def paired_signflip(values, seed=630701, n=9999):
    x = np.asarray(values, dtype=float)
    if len(x) < 2:
        return None
    if np.all(x == 0):
        return 1.
    statistic = abs(x.mean())
    if len(x) <= 15:
        signs = np.asarray(list(itertools.product([-1., 1.], repeat=len(x))))
        return float(np.mean(abs(signs @ x/len(x)) >= statistic-1e-12))
    signs = np.random.default_rng(seed).choice([-1., 1.], size=(n, len(x)))
    return float((1+np.count_nonzero(abs(signs @ x/len(x)) >= statistic-1e-12))/(n+1))


def bh(pvalues):
    p = np.asarray(pvalues, dtype=float)
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("invalid p values")
    order = np.argsort(p)
    q = np.minimum.accumulate((p[order]*len(p)/np.arange(1, len(p)+1))[::-1])[::-1]
    result = np.empty_like(q)
    result[order] = np.minimum(q, 1.)
    return result


def summarize_pair(baselines, lesions, ids, support_ids, motor_ids, out):
    for p in baselines:
        if read_json(Path(p)/"manifest.json")["lesion_ids"]:
            raise ValueError("baseline has a lesion")
    for p in lesions:
        if set(read_json(Path(p)/"manifest.json")["lesion_ids"]) != set(support_ids):
            raise ValueError("reported support differs from the actual lesion")
    delta, seeds = paired_deltas(baselines, lesions, ids)
    lookup = {v: i for i, v in enumerate(ids)}
    support = [lookup[v] for v in support_ids]
    mean = delta.mean(0)
    result = {**footprint(mean, support), "interval": bootstrap_footprint(delta, support),
              "n_pairs": len(seeds), "seeds": seeds, "support_ids": support_ids,
              "mn9_delta_hz": float(mean[lookup[MN9]]) if MN9 in lookup else None,
              "motor_total_delta_hz": float(sum(mean[lookup[i]] for i in motor_ids)),
              "motor_mean_delta_hz": float(np.mean([mean[lookup[i]] for i in motor_ids])) if motor_ids else None,
              "created_utc": now(), "claim_status": "pilot" if len(seeds) < 30 else "simulation_estimate",
              "source_manifests": {str(Path(p)/"manifest.json"): sha256(Path(p)/"manifest.json") for p in [*baselines, *lesions]}}
    out = Path(out)
    atomic_parquet(out/"footprint.parquet", pd.DataFrame({"root_id": ids, "delta_hz": mean}))
    atomic_json(out/"summary.json", result)
    return result, delta
