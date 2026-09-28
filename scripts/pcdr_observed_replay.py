"""Run four serial recorded replays, requiring exact saved-event agreement."""
import os
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
os.environ['MPLBACKEND'] = 'Agg'
import argparse
from pathlib import Path
import sys
import subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import sha256, atomic_json, now, neuron_ids, environment, fingerprint
from eigencircuits.memory import peak_rss
from scripts.pcdr_ccr_transfer import read
from scripts.pcdr_resolution import input_tape
from scripts.pcdr_observed_sim import simulate
from scripts.pcdr_bounded_process import run_bounded


def available_memory():
    if os.name != 'nt': raise RuntimeError('This local runner currently checks Windows memory only')
    value = subprocess.check_output(['powershell', '-NoProfile', '-Command',
        '(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'], text=True)
    return int(value.strip()) * 1024


def checked_frame(directory, name):
    m = read(directory / 'manifest.json')
    if m['status'] != 'complete' or sha256(directory / name) != m['outputs'][name]:
        raise ValueError('Incomplete or changed reference: ' + str(directory / name))
    return pd.read_parquet(directory / name)


def worker(plan, index, original, reference, out):
    j = plan['jobs'][index]
    ref = reference / 'trials' / j['id']
    if sha256(ref / 'manifest.json') != plan['reference_manifests'][j['id']]:
        raise ValueError('Reference manifest changed')
    m = read(ref / 'manifest.json')
    if m['spec'] != j: raise ValueError('Reference specification changed')
    source = original / 'trials' / j['source_trial']
    if sha256(source / 'manifest.json') != m['source_manifest_sha256']:
        raise ValueError('Original input source changed')
    old = read(source / 'manifest.json')
    events = checked_frame(source, 'input_events.parquet')
    if fingerprint(events.to_dict('list')) != m['physical_input_digest']:
        raise ValueError('Physical input mismatch')
    expected = checked_frame(ref, 'spikes.parquet')
    expected_delivery = checked_frame(ref, 'delivered_events.parquet')
    ids = neuron_ids(); lookup = {v: i for i, v in enumerate(ids)}
    tape = input_tape(events, old['input_ids'], j['dt_ms'])
    out.mkdir(exist_ok=False)
    record = {'status': 'running', 'started_utc': now(), 'spec': j, 'environment': environment()}
    atomic_json(out / 'manifest.json', record)
    try:
        spikes, external, delivered, traces = simulate(j['seed'], [lookup[x] for x in old['input_ids']],
            [lookup[x] for x in j['lesion_ids']], tape=tape,
            record_indices=[lookup[x] for x in plan['record_ids']], dt_ms=j['dt_ms'],
            weight_scale=1.2, inhibitory_scale=.8, return_delivered=True)
        for frame in [spikes, external, delivered]:
            frame['flywire_id'] = pd.Series([ids[i] for i in frame.pop('neuron_index')], dtype='string')
        spikes.to_parquet(out / 'spikes.parquet', index=False)
        delivered.to_parquet(out / 'delivered_events.parquet', index=False)
        schedule = traces.pop('schedule')
        (out / 'schedule.txt').write_text(schedule, encoding='utf-8')
        np.savez_compressed(out / 'states.npz', **traces)
        if fingerprint(spikes[['t', 'flywire_id']].to_dict('list')) != fingerprint(expected[['t', 'flywire_id']].to_dict('list')):
            raise ValueError('Recorded run changed the saved spike sequence')
        if fingerprint(delivered.to_dict('list')) != fingerprint(expected_delivery.to_dict('list')):
            raise ValueError('Recorded run changed delivered events')
        mapped = events.copy(); mapped['tick'] *= round(.1 / j['dt_ms'])
        if fingerprint(external.to_dict('list')) != fingerprint(mapped.to_dict('list')):
            raise ValueError('Scheduled input changed')
        if any(not np.isfinite(a).all() for k, a in traces.items() if k.endswith('_mV')):
            raise ValueError('Nonfinite state record')
        record.update(status='complete', exact_spike_replay=True, exact_delivery_replay=True,
                      spike_count=len(spikes), peak_rss_bytes=peak_rss())
    except BaseException as error:
        record.update(status='failed', error=repr(error))
        raise
    finally:
        record['finished_utc'] = now()
        record['outputs'] = {p.name: sha256(p) for p in out.iterdir() if p.name != 'manifest.json'}
        atomic_json(out / 'manifest.json', record)


def run(plan_path, original, reference, out):
    if out.exists(): raise FileExistsError(out)
    plan = read(plan_path)
    for name, expected in plan['sources'].items():
        if sha256(ROOT / name) != expected: raise ValueError('Changed source: ' + name)
    free = available_memory()
    if free < 6_000_000_000:
        raise RuntimeError(f'Need 6 GB available for one worker; currently {free/1e9:.2f} GB')
    out.mkdir(parents=True, exist_ok=False)
    atomic_json(out / 'plan.json', plan)
    progress = {'status': 'running', 'started_utc': now(), 'completed': 0, 'initial_free_bytes': free}
    atomic_json(out / 'progress.json', progress)
    try:
        for i, j in enumerate(plan['jobs']):
            if available_memory() < 6_000_000_000: raise RuntimeError('Available memory fell below 6 GB')
            cmd = [sys.executable, str(Path(__file__)), 'worker', '--plan', str(plan_path),
                   '--original', str(original), '--reference', str(reference), '--out', str(out), '--index', str(i)]
            result = run_bounded(cmd, out / 'logs' / j['id'], 1200, cwd=ROOT)
            atomic_json(out / 'logs' / j['id'] / 'process.json', result)
            if result['returncode'] or result['timed_out']: raise RuntimeError('Worker failed: ' + j['id'])
            progress['completed'] += 1
            atomic_json(out / 'progress.json', progress)
        progress['status'] = 'complete'
    except BaseException as error:
        progress.update(status='failed', error=repr(error))
        raise
    finally:
        progress['finished_utc'] = now()
        atomic_json(out / 'progress.json', progress)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['run', 'worker'])
    for name in ['plan', 'original', 'reference', 'out']: p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--index', type=int)
    args = p.parse_args()
    if args.action == 'run': run(args.plan.resolve(), args.original.resolve(), args.reference.resolve(), args.out.resolve())
    else:
        plan = read(args.plan)
        if args.index is None or not 0 <= args.index < len(plan['jobs']): p.error('Invalid worker index')
        worker(plan, args.index, args.original, args.reference, args.out / plan['jobs'][args.index]['id'])
