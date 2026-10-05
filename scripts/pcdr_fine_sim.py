"""Fine-step replay with bounded input-voltage recording windows."""
import numpy as np
import pandas as pd
from eigencircuits.common import COMP, CON


def ticks_for(milliseconds, dt_ms):
    if not np.isfinite(milliseconds) or not np.isfinite(dt_ms) or milliseconds <= 0 or dt_ms <= 0:
        raise ValueError('Positive finite duration and step required')
    ratio = milliseconds / dt_ms
    ticks = round(ratio)
    if ticks < 1 or not np.isclose(ratio, ticks, rtol=0, atol=1e-7):
        raise ValueError('Interval must be an integer number of ticks')
    return ticks


def input_tape(events, input_ids, dt_ms, duration_s=1.):
    factor = ticks_for(.1, dt_ms)
    total = ticks_for(duration_s * 1000, dt_ms)
    if len(set(input_ids)) != len(input_ids):
        raise ValueError('Duplicate input IDs')
    columns = pd.Index(input_ids).get_indexer(events.flywire_id)
    ticks = events.tick.to_numpy()
    if not np.issubdtype(ticks.dtype, np.integer) or np.any(ticks < 0) or np.any(columns < 0):
        raise ValueError('Invalid saved input event')
    if np.any(ticks >= total / factor):
        raise ValueError('Input event outside duration')
    mapped = ticks * factor
    if len(set(zip(mapped, columns))) != len(mapped):
        raise ValueError('Duplicate saved input event')
    tape = np.zeros((total, len(input_ids)), dtype=np.int8)
    tape[mapped, columns] = 1
    return tape


def simulate(seed, inputs, lesion, *, tape, duration_s=1., dt_ms=.1, backend="numpy",
             weight_scale=1., inhibitory_scale=1., strong_fraction=None,
             completeness=COMP, connectivity=CON, return_delivered=False, chunk_ms=10., recorder=None):
    """Replay state-independent Bernoulli input; retain Shiu voltage gating."""
    ticks_for(duration_s * 1000, dt_ms)
    chunk_ticks = ticks_for(chunk_ms, dt_ms)
    ticks_for(1.8, dt_ms)
    ticks_for(2.2, dt_ms)
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
    network = b.Network(neu, syn, monitor, *pois)
    if recorder is not None:
        recorder.setup(network, neu, dt_ms, duration_s)
    pieces = []
    for start in range(0, ticks, chunk_ticks):
        length = min(chunk_ticks, ticks - start)
        extra = []
        diagnostic = []
        if inputs:
            before = b.StateMonitor(neu, 'v', record=inputs, when='before_synapses')
            after = b.StateMonitor(neu, 'v', record=inputs, when='after_synapses')
            extra = [before, after]
            network.add(*extra)
        try:
            if recorder is not None:
                diagnostic = recorder.monitors(start, length)
                if diagnostic:
                    network.add(*diagnostic)
            network.run(length * dt_ms * b.ms)
            if diagnostic:
                recorder.save(start, length, diagnostic)
            if recorder is not None:
                recorder.progress(start+length)
            if inputs:
                jumps = np.asarray((after.v - before.v) / (params['w_syn'] * params['f_poi']))
                if not np.allclose(jumps, np.rint(jumps), atol=1e-10) or np.any(jumps < -.5) or np.any(jumps > 1.5):
                    raise ValueError('Invalid recorded external voltage increment')
                times = np.rint(np.asarray(before.t / b.ms) / dt_ms).astype(np.int64)
                if not np.array_equal(times, np.arange(start, start + length)):
                    raise ValueError('Recording window does not match simulation ticks')
                source, local_tick = np.nonzero(jumps > .5)
                event_ticks = times[local_tick]
                if not np.all(tape[event_ticks, source] == 1):
                    raise ValueError('Delivered input absent from schedule')
                pieces.append(pd.DataFrame({'neuron_index': np.asarray(inputs, dtype=np.int64)[source],
                                            'tick': event_ticks}))
        finally:
            if diagnostic:
                network.remove(*diagnostic)
                del diagnostic
            if extra:
                network.remove(*extra)
                del before, after, extra
        if inputs:
            del jumps
    delivered = (pd.concat(pieces, ignore_index=True) if pieces else
                 pd.DataFrame({'neuron_index': pd.Series(dtype='int64'), 'tick': pd.Series(dtype='int64')}))
    delivered = delivered.sort_values(['tick', 'neuron_index']).reset_index(drop=True)
    events = pd.DataFrame({"neuron_index": np.asarray(monitor.i[:], dtype="int64"),
                           "t": np.asarray(monitor.t[:] / b.second, dtype=float)})
    return (events, external, delivered) if return_delivered else (events, external)

