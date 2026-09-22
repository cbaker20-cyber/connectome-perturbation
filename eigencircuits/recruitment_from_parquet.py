from __future__ import annotations

import numpy as np
import pandas as pd


def recruitment(spikes, ids, trial_ids, duration_s=1.):
    """All model cells and all declared trials, including entirely silent ones."""
    if duration_s <= 0 or not trial_ids or len(set(trial_ids)) != len(trial_ids):
        raise ValueError("invalid duration or declared trial IDs")
    ids, trial_ids = list(map(str, ids)), list(map(str, trial_ids))
    d = spikes.copy()
    d["trial"] = d.trial.astype(str)
    d["flywire_id"] = d.flywire_id.astype(str)
    if not set(d.trial) <= set(trial_ids) or not set(d.flywire_id) <= set(ids):
        raise ValueError("undeclared spike trial or neuron")
    counts = d.groupby(["flywire_id", "trial"]).size().unstack(fill_value=0).reindex(
        index=ids, columns=trial_ids, fill_value=0).fillna(0).astype("int64")
    return pd.DataFrame({"root_id": ids, "spike_count": counts.sum(axis=1).to_numpy(),
                         "trials_recruited": (counts > 0).sum(axis=1).to_numpy(),
                         "fraction_trials_recruited": (counts > 0).mean(axis=1).to_numpy(),
                         "baseline_hz": counts.mean(axis=1).to_numpy()/duration_s,
                         "recruited": counts.sum(axis=1).to_numpy() > 0})


def bin_spikes(spikes, ids, trial_ids, bin_ms=10., duration_s=1.):
    n_bins = round(duration_s*1000/bin_ms)
    if bin_ms <= 0 or not np.isclose(n_bins*bin_ms/1000, duration_s):
        raise ValueError("bin width must divide trial duration")
    id_map = {str(v): i for i, v in enumerate(ids)}
    trial_map = {str(v): i for i, v in enumerate(trial_ids)}
    x = np.zeros((len(ids), len(trial_ids), n_bins), dtype=float)
    d = spikes[spikes.flywire_id.astype(str).isin(id_map)].copy()
    if not set(d.trial.astype(str)) <= set(trial_map):
        raise ValueError("undeclared trial")
    if not np.isfinite(d.t).all() or np.any((d.t < 0) | (d.t >= duration_s)):
        raise ValueError("spike time outside trial")
    np.add.at(x, (d.flywire_id.astype(str).map(id_map).to_numpy(dtype=int),
                  d.trial.astype(str).map(trial_map).to_numpy(dtype=int),
                  np.floor(d.t.to_numpy()*1000/bin_ms + 1e-9).astype(int)), 1.)
    return x
