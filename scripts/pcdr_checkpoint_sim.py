"""Checkpoint extension of fine-step replay; frozen simulator remains unchanged."""
from pathlib import Path
import hashlib
import json
import os
import sys
import uuid
import socket

class CheckpointSaved(Exception):
    """A validated chunk boundary was saved before the requested endpoint."""


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def simulate(*args, checkpoint_dir=None, stop_after_ms=None, **kwargs):
    if checkpoint_dir is None:
        raise ValueError("Explicit checkpoint directory required")
    folder = Path(checkpoint_dir)
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder/"owner.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    owner = dict(pid=os.getpid(), host=socket.gethostname(),
                 job=os.environ.get("SLURM_JOB_ID"), token=uuid.uuid4().hex)
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(owner, handle)
        return _simulate(*args, checkpoint_dir=folder, stop_after_ms=stop_after_ms, **kwargs)
    finally:
        if lock.exists() and lock.read_text() == json.dumps(owner):
            lock.unlink()

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


def _simulate(seed, inputs, lesion, *, tape, duration_s=1., dt_ms=.1, backend="numpy",
             weight_scale=1., inhibitory_scale=1., strong_fraction=None,
             completeness=COMP, connectivity=CON, return_delivered=False, chunk_ms=10., recorder=None, checkpoint_dir=None, stop_after_ms=None):
    """Replay state-independent Bernoulli input; retain Shiu voltage gating."""
    if recorder is not None:
        raise ValueError("Diagnostic recorders are not supported by this checkpoint extension")
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
                                            when="synapses", order=0, name=f"checkpoint_input_{column}"))
    tick, source = np.nonzero(tape)
    external = pd.DataFrame({"neuron_index": np.asarray(inputs, dtype="int64")[source],
                             "tick": tick.astype("int64")})
    external = external.sort_values(["tick", "neuron_index"]).reset_index(drop=True)
    model.silence(lesion, syn)
    network = b.Network(neu, syn, monitor, *pois)
    if recorder is not None:
        recorder.setup(network, neu, dt_ms, duration_s)
    config = dict(seed=int(seed), inputs=list(inputs), lesion=list(lesion),
                  duration_s=duration_s, dt_ms=dt_ms, chunk_ms=chunk_ms,
                  backend=backend, weight_scale=weight_scale,
                  inhibitory_scale=inhibitory_scale, strong_fraction=strong_fraction,
                  tape_hash=hashlib.sha256(memoryview(np.ascontiguousarray(tape))).hexdigest(),
                  completeness=file_hash(completeness), connectivity=file_hash(connectivity),
                  source=file_hash(__file__), model=file_hash(model.__file__),
                  python=sys.version, brian=b.__version__, numpy=np.__version__)
    stop = ticks if stop_after_ms is None else ticks_for(stop_after_ms, dt_ms)
    if stop > ticks or stop % chunk_ticks != 0:
        raise ValueError('Stop must be a chunk boundary within the full duration')
    pieces = []
    begin = 0
    latest = checkpoint_dir/'latest.json'
    if latest.exists():
        saved = json.loads(latest.read_text())
        if saved['config'] != config:
            raise ValueError('Checkpoint configuration changed')
        begin = saved['tick']
        if not isinstance(begin, int) or begin < 0 or begin > ticks or begin % chunk_ticks:
            raise ValueError('Invalid checkpoint tick')
        generation = saved['generation']
        if not isinstance(generation, str) or Path(generation).name != generation or not generation.startswith(f'tick_{begin}_'):
            raise ValueError('Invalid checkpoint generation')
        base = checkpoint_dir/generation
        if set(saved['hashes']) != {'network.pkl', 'delivered.parquet'}:
            raise ValueError('Invalid checkpoint file set')
        for name, expected in saved['hashes'].items():
            if file_hash(base/name) != expected:
                raise ValueError('Checkpoint hash mismatch: '+name)
        network.restore(filename=str(base/'network.pkl'), restore_random_state=True)
        if round(float(network.t/b.ms)/dt_ms) != begin:
            raise ValueError('Restored clock differs from recorded tick')
        pieces = [pd.read_parquet(base/'delivered.parquet')]
    if stop <= begin and begin < ticks:
        raise ValueError('Requested stop must advance the checkpoint')
    for start in range(begin, ticks, chunk_ticks):
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
        end = start + length
        if end < stop and end < ticks:
            continue
        base = checkpoint_dir/f'tick_{end}_{uuid.uuid4().hex}'
        base.mkdir(exist_ok=False)
        network.store(filename=str(base/'network.pkl'))
        history = (pd.concat(pieces, ignore_index=True) if pieces else
                   pd.DataFrame({'neuron_index': pd.Series(dtype='int64'), 'tick': pd.Series(dtype='int64')}))
        history.to_parquet(base/'delivered.parquet', index=False)
        for name in ('network.pkl', 'delivered.parquet'):
            with (base/name).open('r+b') as payload:
                os.fsync(payload.fileno())
        record = dict(config=config, tick=end, generation=base.name,
                      hashes={name:file_hash(base/name) for name in ('network.pkl','delivered.parquet')})
        temp = checkpoint_dir/'latest.tmp'
        with temp.open('w') as f:
            json.dump(record, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, latest)
        if end >= stop and end < ticks:
            raise CheckpointSaved(f'Saved tick {end} of {ticks}')
    delivered = (pd.concat(pieces, ignore_index=True) if pieces else
                 pd.DataFrame({'neuron_index': pd.Series(dtype='int64'), 'tick': pd.Series(dtype='int64')}))
    delivered = delivered.sort_values(['tick', 'neuron_index']).reset_index(drop=True)
    events = pd.DataFrame({"neuron_index": np.asarray(monitor.i[:], dtype="int64"),
                           "t": np.asarray(monitor.t[:] / b.second, dtype=float)})
    return (events, external, delivered) if return_delivered else (events, external)

