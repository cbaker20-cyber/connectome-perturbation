"""CCR backend validation with frozen margins; never select a backend by speed alone."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

from .common import ANN, MN9, atomic_json, now, provenance, read_json, sha256
from .trials import trial


def equivalence(a, b, margin):
    a, b = np.asarray(a), np.asarray(b)
    difference = float(b.mean()-a.mean())
    va, vb = a.var(ddof=1)/len(a), b.var(ddof=1)/len(b)
    se = np.sqrt(va+vb)
    if se == 0:
        interval = [difference, difference]
    else:
        df = (va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1))
        radius = float(t.ppf(.95, df)*se)
        interval = [difference-radius, difference+radius]
    return {"difference": difference, "interval_90pct": interval, "margin": margin,
            "passed": bool(interval[0] >= -margin and interval[1] <= margin)}


def benchmark(selection, out):
    selected = read_json(selection)
    neuron = next(r["root_id"] for r in selected["cells"] if r["role"] == "excitatory")
    out = Path(out).resolve()
    ann = pd.read_csv(ANN, sep="\t", dtype={"root_id": str}, usecols=["root_id", "super_class"])
    motor = set(ann.loc[ann.super_class == "motor", "root_id"])
    measurements, checks = {}, []
    # Independent benchmark seeds, disjoint from selection and confirmation.
    for backend in ["numpy", "cython"]:
        measurements[backend] = {"mn9": [], "motor": [], "inputs": [], "lesion_mn9_delta": [], "seconds": []}
        for seed in range(630801, 630831):
            base = trial(out/backend/f"baseline_{seed}", f"baseline_{seed}", seed, backend=backend)
            lesion = trial(out/backend/f"lesion_{seed}", f"lesion_{seed}", seed, backend=backend, lesion_ids=[neuron])
            checks.append(base["input_digest"] == lesion["input_digest"])
            rates = pd.read_parquet(out/backend/f"baseline_{seed}"/"rates.parquet").set_index("root_id")
            measurements[backend]["mn9"].append(base["mn9_hz"])
            measurements[backend]["motor"].append(float(rates.loc[rates.index.isin(motor), "rate_hz"].sum()))
            measurements[backend]["inputs"].append(len(pd.read_parquet(out/backend/f"baseline_{seed}"/"input_events.parquet")))
            measurements[backend]["lesion_mn9_delta"].append(lesion["mn9_hz"]-base["mn9_hz"])
            measurements[backend]["seconds"].append(base["wall_seconds"])
        replay = trial(out/backend/"replay", "replay", 630801, backend=backend)
        first = read_json(out/backend/"baseline_630801/manifest.json")
        checks.extend([replay["input_digest"] == first["input_digest"], replay["spike_digest"] == first["spike_digest"]])
        silent = trial(out/backend/"no_input", "no_input", 630801, backend=backend, context="no_input")
        checks.append(silent["spike_count"] == 0)
    comparisons = {}
    for key, floor, relative in [("mn9", 5., .1), ("motor", 10., .1), ("inputs", 0., .05), ("lesion_mn9_delta", 5., .1)]:
        a, b = measurements["numpy"][key], measurements["cython"][key]
        comparisons[key] = equivalence(a, b, max(floor, relative*abs(np.mean(a))))
    atomic_json(out/"benchmark.json", {"passed": all(checks) and all(r["passed"] for r in comparisons.values()),
                "comparisons": comparisons, "checks": checks, "measurements": measurements,
                "selection_sha256": sha256(selection), "provenance": provenance(), "created_utc": now(),
                "margin_note": "predeclared numerical acceptance tolerances, not biological equivalence margins"})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--selection", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    benchmark(a.selection, a.out)
