"""Observed copy of the saved-input simulator; original source remains unchanged.

Only record selection, two StateMonitors and returned traces are added. g is
voltage-valued synaptic drive, not current in amperes. No new equations or inputs.
"""
import numpy as np
import pandas as pd
from eigencircuits.common import COMP, CON


def input_tape(events, input_ids, dt_ms, duration_s=1.):
    if dt_ms not in (.1, .05, .025):
        raise ValueError('Use a declared time step')
    if len(set(input_ids)) != len(input_ids):
        raise ValueError('Duplicate input IDs')
    columns = pd.Index(input_ids).get_indexer(events.flywire_id)
    ticks = events.tick.to_numpy()
    if not np.issubdtype(ticks.dtype, np.integer) or np.any(ticks < 0) or np.any(ticks >= round(duration_s * 10000)) or np.any(columns < 0):
        raise ValueError('Invalid saved input event')
    mapped = ticks * round(.1 / dt_ms)
    if len(set(zip(mapped, columns))) != len(mapped):
        raise ValueError('Duplicate saved input event')
    tape = np.zeros((round(duration_s * 1000 / dt_ms), len(input_ids)), dtype=np.int8)
    tape[mapped, columns] = 1
    return tape


def simulate(seed, inputs, lesion, *, tape, record_indices, duration_s=1., dt_ms=.1, backend="numpy",
             weight_scale=1., inhibitory_scale=1., strong_fraction=None,
             completeness=COMP, connectivity=CON, return_delivered=False):
    """Replay state-independent Bernoulli input; retain Shiu voltage gating."""
    if not record_indices or len(set(record_indices)) != len(record_indices):
        raise ValueError("Recording indices must be nonempty and unique")
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
    tape = np.asarray(tape)
    if tape.shape != (ticks, len(inputs)) or not np.isin(tape, [0, 1]).all():
        raise ValueError("invalid saved input tape")
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
    if any(i < 0 or i >= len(neu) for i in record_indices):
        raise ValueError("Unknown recording index")
    state = [b.StateMonitor(neu, ["v", "g", "not_refractory"], record=record_indices,
                           when=slot, name="trace_" + slot)
             for slot in ["before_thresholds", "after_synapses"]]
    network = b.Network(neu, syn, monitor, *pois, *extra, *state)
    schedule = str(b.scheduling_summary(network))
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
    traces = {"indices": np.asarray(record_indices, dtype=np.int64), "schedule": schedule}
    for mon in state:
        traces[mon.when + "_t_s"] = np.asarray(mon.t / b.second)
        traces[mon.when + "_v_mV"] = np.asarray(mon.v / b.mV)
        traces[mon.when + "_g_mV"] = np.asarray(mon.g / b.mV)
        traces[mon.when + "_not_refractory"] = np.asarray(mon.not_refractory, dtype=bool)
    return events, external, delivered, traces

