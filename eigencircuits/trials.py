from __future__ import annotations

import argparse
import gc
import hashlib
from pathlib import Path
import threading
import time
import zipfile

import numpy as np
import pandas as pd

from .common import (COMP, CON, MN9, ROOT, atomic_json, atomic_parquet, fingerprint,
                     neuron_ids, now, provenance, read_json, root_ids, sha256, sugar_ids)


def simulate(seed, inputs, lesion, *, duration_s=1., dt_ms=.1, backend="numpy",
             weight_scale=1., inhibitory_scale=1., strong_fraction=None,
             completeness=COMP, connectivity=CON, return_delivered=False):
    """Replay state-independent Bernoulli input; retain Shiu voltage gating."""
    import brian2 as b
    import model
    b.start_scope()
    b.prefs.codegen.target = backend
    b.defaultclock.dt = dt_ms * b.ms
    b.seed(int(seed))
    params = model.default_params.copy()
    params.update(t_run=duration_s * b.second, r_poi=150 * b.Hz)
    neu, syn, monitor = model.create_model(completeness, connectivity, params)
    if weight_scale != 1 or inhibitory_scale != 1 or strong_fraction is not None:
        weights = np.asarray(syn.w / b.mV).copy()
        if strong_fraction is not None:
            post = np.asarray(syn.j[:])
            incoming = np.bincount(post, weights=np.abs(weights), minlength=len(neu))
            weights[np.abs(weights) < strong_fraction * incoming[post]] = 0
        weights[weights < 0] *= inhibitory_scale
        weights *= weight_scale
        syn.w = weights * b.mV
    ticks = int(round(duration_s / (dt_ms / 1000)))
    if ticks <= 0 or not np.isclose(ticks * dt_ms / 1000, duration_s):
        raise ValueError("duration must contain a positive whole number of ticks")
    if len(set(inputs)) != len(inputs) or any(i < 0 or i >= len(neu) for i in inputs):
        raise ValueError("invalid or duplicate input indices")
    # N=1 PoissonInput uses Bernoulli(rate*dt). Generate all draws before
    # running so conditional voltage writes cannot advance a shared RNG.
    tape = np.random.default_rng(int(seed)).binomial(1, 150 * dt_ms / 1000,
                                                   size=(ticks, len(inputs)))
    pois = []
    neu.namespace["external_jump"] = params["w_syn"] * params["f_poi"]
    for column, index in enumerate(inputs):
        key = f"external_tape_{column}"
        neu.namespace[key] = b.TimedArray(tape[:, column], dt=dt_ms * b.ms)
        neu[index].rfc = 0 * b.ms
        pois.append(neu[index].run_regularly(f"v += {key}(t) * external_jump",
                                            when="synapses", order=0))
    tick, source = np.nonzero(tape)
    external = pd.DataFrame({"neuron_index": np.asarray(inputs, dtype="int64")[source],
                             "tick": tick.astype("int64")})
    external = external.sort_values(["tick", "neuron_index"]).reset_index(drop=True)
    model.silence(lesion, syn)
    extra = []
    if inputs:
        # PoissonInput changes v in the synapses slot; recurrent synapses change g.
        before = b.StateMonitor(neu, "v", record=inputs, when="before_synapses")
        after = b.StateMonitor(neu, "v", record=inputs, when="after_synapses")
        extra = [before, after]
    network = b.Network(neu, syn, monitor, *pois, *extra)
    network.run(params["t_run"])
    if inputs:
        jumps = np.asarray((after.v - before.v) / (params["w_syn"] * params["f_poi"]))
        if not np.allclose(jumps, np.rint(jumps), atol=1e-10):
            raise ValueError("input instrumentation found non-Poisson voltage changes")
        source, tick = np.nonzero(jumps > .5)
        delivered = pd.DataFrame({"neuron_index": np.asarray(inputs)[source], "tick": tick.astype("int64")})
        delivered = delivered.sort_values(["tick", "neuron_index"]).reset_index(drop=True)
    else:
        delivered = external.copy()
    events = pd.DataFrame({"neuron_index": np.asarray(monitor.i[:], dtype="int64"),
                           "t": np.asarray(monitor.t[:] / b.second, dtype=float)})
    return (events, external, delivered) if return_delivered else (events, external)


def trial(out, trial_id, seed, *, context="sugar", lesion_ids=(), backend="numpy",
          weight_scale=1., inhibitory_scale=1., strong_fraction=None):
    out = Path(out)
    ids = neuron_ids()
    lookup = {x: i for i, x in enumerate(ids)}
    lesion_ids = root_ids(lesion_ids)
    if len(set(lesion_ids)) != len(lesion_ids):
        raise ValueError("duplicate lesion IDs")
    if not set(lesion_ids) <= set(ids):
        raise ValueError("lesion contains unknown IDs")
    if context not in ("sugar", "no_input"):
        raise ValueError("unknown context")
    if min(weight_scale, inhibitory_scale) <= 0:
        raise ValueError("weight scales must be positive")
    if strong_fraction is not None and not 0 < strong_fraction <= 1:
        raise ValueError("invalid strong fraction")
    inputs = sugar_ids() if context == "sugar" else []
    if set(inputs) & set(lesion_ids):
        raise ValueError("sensory inputs are excluded from this lesion protocol")
    spec = {"trial_id": str(trial_id), "seed": int(seed), "context": context,
            "lesion_ids": sorted(lesion_ids), "input_ids": inputs, "backend": backend,
            "duration_s": 1., "dt_ms": .1, "input_hz": 150., "input_protocol": "fixed_binomial_tape_v1", "weight_scale": weight_scale,
            "inhibitory_scale": inhibitory_scale, "strong_fraction": strong_fraction}
    prov = provenance()
    simulation_sources = {k: v for k, v in prov["sources"].items()
                          if k.replace("\\", "/") in ["model.py", "perturbation/baseline.py",
                              "perturbation/cell_groups.py", "eigencircuits/common.py", "eigencircuits/trials.py"]}
    signature = fingerprint({"spec": spec, "inputs": prov["inputs"],
                             "sources": simulation_sources, "environment": prov["environment"]})
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        old = read_json(manifest_path)
        if old.get("signature") != signature:
            raise ValueError(f"existing run has different inputs/code/config: {out}")
        if old.get("status") == "complete":
            if not all(sha256(out / k) == v for k, v in old["outputs"].items()):
                raise ValueError("completed run output checksum mismatch")
            return old
    out.mkdir(parents=True, exist_ok=True)
    manifest = {**spec, "signature": signature, "provenance": prov,
                "started_utc": now(), "status": "running", "claim_status": "simulation_pilot"}
    atomic_json(manifest_path, manifest)
    with zipfile.ZipFile(out / "source_snapshot.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, expected in prov["sources"].items():
            source = ROOT / relative
            if sha256(source) != expected:
                raise ValueError("source changed while recording the run")
            archive.write(source, arcname=relative)
    atomic_json(out / "environment.json", prov["environment"])
    start = time.perf_counter()
    stop = threading.Event()
    memory = []
    def sample_memory():
        from .memory import peak_rss
        while not stop.is_set():
            memory.append(peak_rss())
            stop.wait(.5)
    sampler = threading.Thread(target=sample_memory, daemon=True)
    sampler.start()
    try:
        events, external, delivered = simulate(seed, [lookup[i] for i in inputs], [lookup[i] for i in lesion_ids],
                                    backend=backend, weight_scale=weight_scale,
                                    inhibitory_scale=inhibitory_scale, strong_fraction=strong_fraction,
                                    return_delivered=True)
        events["flywire_id"] = pd.Series([ids[i] for i in events.pop("neuron_index")], dtype="string")
        events["trial"] = str(trial_id)
        events["exp_name"] = context
        external["flywire_id"] = pd.Series([ids[i] for i in external.pop("neuron_index")], dtype="string")
        delivered["flywire_id"] = pd.Series([ids[i] for i in delivered.pop("neuron_index")], dtype="string")
        counts = events.groupby("flywire_id").size().reindex(ids, fill_value=0)
        rates = pd.DataFrame({"root_id": ids, "spike_count": counts.to_numpy(), "rate_hz": counts.to_numpy(dtype=float)})
        atomic_parquet(out / "spikes.parquet", events)
        atomic_parquet(out / "input_events.parquet", external)
        atomic_parquet(out / "delivered_events.parquet", delivered)
        atomic_parquet(out / "rates.parquet", rates)
        from .memory import peak_rss
        memory.append(peak_rss())
        manifest.update(status="complete", finished_utc=now(), wall_seconds=time.perf_counter()-start,
                        peak_rss_bytes=max(memory) if memory else None,
                        spike_count=len(events), recruited_noninput=len(set(events.flywire_id)-set(inputs)),
                        mn9_hz=float(counts.loc[MN9]) if MN9 in counts else None,
                        input_digest=fingerprint(external.to_dict("list")),
                        delivered_input_digest=fingerprint(delivered.to_dict("list")),
                        spike_digest=fingerprint(events[["t", "flywire_id"]].to_dict("list")),
                        outputs={p: sha256(out / p) for p in ["spikes.parquet", "input_events.parquet", "delivered_events.parquet", "rates.parquet", "source_snapshot.zip", "environment.json"]})
        atomic_json(manifest_path, manifest)
        print(f"{trial_id}: {manifest['wall_seconds']:.1f}s; {len(events)} spikes; MN9 {manifest['mn9_hz']} Hz", flush=True)
        return manifest
    except BaseException as exc:
        manifest.update(status="failed", error=repr(exc), finished_utc=now())
        atomic_json(manifest_path, manifest)
        raise
    finally:
        stop.set()
        sampler.join(timeout=2)
        gc.collect()


def main():
    p = argparse.ArgumentParser(description="One seed-logged whole-brain trial")
    p.add_argument("--out", required=True)
    p.add_argument("--trial-id", required=True)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--context", choices=["sugar", "no_input"], default="sugar")
    p.add_argument("--lesion-id", action="append", default=[])
    p.add_argument("--backend", choices=["numpy", "cython"], default="numpy")
    p.add_argument("--weight-scale", type=float, default=1.)
    p.add_argument("--inhibitory-scale", type=float, default=1.)
    p.add_argument("--strong-fraction", type=float)
    args = vars(p.parse_args())
    args["lesion_ids"] = args.pop("lesion_id")
    trial(**args)


if __name__ == "__main__":
    main()
