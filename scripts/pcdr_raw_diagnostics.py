"""Audit saved CCR trials and export sparse paired rates; never simulate."""
import argparse
from contextlib import ExitStack
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from eigencircuits.common import environment, fingerprint, neuron_ids, root_ids, sugar_ids
from scripts.pcdr_ccr_transfer import digest, read, write, utc, verify
from scripts.pcdr_ccr_sensitivity import validated, planned_jobs


def event_keys(frame, ids, ticks):
    if list(frame.columns) != ['tick', 'flywire_id']:
        raise ValueError('Unexpected input event columns')
    cells = pd.Index(ids).get_indexer(root_ids(frame.flywire_id))
    values = frame.tick.to_numpy()
    if not np.issubdtype(values.dtype, np.integer) or np.any(values < 0) or np.any(values >= ticks) or np.any(cells < 0):
        raise ValueError('Invalid input cell or tick')
    keys = values * len(ids) + cells
    if len(np.unique(keys)) != len(keys):
        raise ValueError('Duplicate input event')
    return keys


def inspect_trial(directory, manifest, ids):
    rates = pd.read_parquet(directory / 'rates.parquet')
    rate_ids = root_ids(rates.root_id)
    if len(rate_ids) != len(ids) or len(set(rate_ids)) != len(ids) or set(rate_ids) != set(ids):
        raise ValueError('Wrong rate neuron universe')
    rates.index = rate_ids
    rates = rates.loc[ids]
    spikes = pd.read_parquet(directory / 'spikes.parquet')
    cells = pd.Index(ids).get_indexer(root_ids(spikes.flywire_id))
    t = spikes.t.to_numpy(dtype=float)
    dt = manifest['dt_ms'] / 1000
    duration = manifest['duration_s']
    if np.any(cells < 0) or not np.isfinite(t).all() or np.any(t < 0) or np.any(t >= duration):
        raise ValueError('Invalid spike ID or time')
    tick = np.rint(t / dt).astype(np.int64)
    if not np.allclose(t, tick * dt, atol=1e-10, rtol=0):
        raise ValueError('Spike off simulation time grid')
    if len(spikes) and (set(spikes.trial) != {manifest['trial_id']} or set(spikes.exp_name) != {manifest['context']}):
        raise ValueError('Spike labels disagree with manifest')
    counts = np.bincount(cells, minlength=len(ids))
    if not np.array_equal(counts, rates.spike_count) or not np.array_equal(counts / duration, rates.rate_hz):
        raise ValueError('Rates disagree with spikes')
    if len(spikes) != manifest['spike_count'] or fingerprint(spikes[['t', 'flywire_id']].to_dict('list')) != manifest['spike_digest']:
        raise ValueError('Spike manifest mismatch')
    sensory = np.isin(np.asarray(ids), manifest['input_ids'])
    if len(set(manifest['input_ids'])) != len(manifest['input_ids']) or not set(manifest['input_ids']) <= set(ids):
        raise ValueError('Invalid sensory IDs')
    recruited = int(np.count_nonzero(counts[~sensory]))
    if recruited != manifest['recruited_noninput']:
        raise ValueError('Recruitment manifest mismatch')
    order = np.lexsort((tick, cells))
    same = np.diff(cells[order]) == 0
    gaps = np.diff(tick[order])
    noninput = ~sensory[cells[order][1:]]
    # The sugar cells have zero refractory time; all other cells use 2.2 ms.
    if np.any(same & ((gaps < 1) | (noninput & (gaps * dt < .0022 - 1e-10)))):
        raise ValueError('Duplicate spike or refractory violation')
    inputs = pd.read_parquet(directory / 'input_events.parquet')
    delivered = pd.read_parquet(directory / 'delivered_events.parquet')
    a = event_keys(inputs, manifest['input_ids'], round(duration / dt))
    b = event_keys(delivered, manifest['input_ids'], round(duration / dt))
    if not np.isin(b, a).all():
        raise ValueError('Delivered event absent from scheduled tape')
    for frame, key in [(inputs, 'input_digest'), (delivered, 'delivered_input_digest')]:
        if fingerprint(frame.to_dict('list')) != manifest[key]:
            raise ValueError(f'Wrong {key}')
    trace = np.bincount(np.floor((tick * dt + 1e-12) / .01).astype(int), minlength=round(duration / .01))
    return counts / duration, trace, {
        'spikes': len(spikes), 'recruited_noninput': recruited,
        'max_noninput_hz': float(np.max(counts[~sensory], initial=0) / duration),
        'scheduled_events': len(inputs), 'delivered_events': len(delivered),
        'input_digest': manifest['input_digest'],
        'min_noninput_isi_ms': float(gaps[same & noninput].min() * dt * 1000) if np.any(same & noninput) else None,
    }


def run(study, out):
    study, out = Path(study).resolve(), Path(out).resolve()
    if out == study or study in out.parents:
        raise ValueError('Keep diagnostic outputs outside the frozen study')
    if list(study.glob('*.lock')):
        raise ValueError('Study has locks; check the original workers before reading it')
    verify()
    plan = read(study / 'jobs.json')
    if digest(ROOT / 'transfer_manifest.json') != plan['transfer_sha256']:
        raise ValueError('Changed transfer manifest')
    if plan['jobs'] != planned_jobs(plan['conditions'], plan['variants'], plan['design']['seeds']):
        raise ValueError('Jobs differ from the recorded design')
    ids = neuron_ids()
    inputs = set(sugar_ids())
    mode = next(c['ids'] for c in plan['conditions'] if c['name'] == 'mode')
    mask = np.isin(np.asarray(ids), mode)
    if mask.sum() != len(mode):
        raise ValueError('Invalid mode support')
    out.mkdir(parents=True, exist_ok=False)
    audit = {'status': 'running', 'started_utc': utc(), 'jobs_sha256': digest(study / 'jobs.json'),
             'script_sha256': digest(Path(__file__)), 'simulation_environment': plan['provenance']['environment'],
             'analysis_environment': environment(), 'completed_trials': 0,
             'scope': 'Read-only arithmetic and event checks. Analysis platform may differ; no simulations run.',
             'sparse_rates': 'Absent neuron_index rows mean zero. All neurons are listed in neurons.csv. Rates and deltas are Hz.'}
    write(out / 'audit.json', audit)
    try:
        pd.DataFrame({'neuron_index': range(len(ids)), 'root_id': ids, 'mode_member': mask}).to_csv(out / 'neurons.csv', index=False)
        schema = pa.schema([('trial_id', pa.string()), ('neuron_index', pa.int32()), ('rate_or_delta_hz', pa.float64())])
        with ExitStack() as stack:
            delta_writer = stack.enter_context(pq.ParquetWriter(out / 'paired_deltas.parquet', schema, compression='zstd'))
            baseline_writer = stack.enter_context(pq.ParquetWriter(out / 'baseline_rates.parquet', schema, compression='zstd'))
            fields = ['trial_id', 'variant', 'condition', 'seed', 'spikes', 'recruited_noninput', 'max_noninput_hz', 'scheduled_events', 'delivered_events', 'input_digest', 'min_noninput_isi_ms', 'paired_total_abs_hz', 'paired_fixed_mode_abs_hz', 'spike_file_identical_to_baseline']
            summary = csv.DictWriter(stack.enter_context((out / 'trial_diagnostics.csv').open('w', newline='', encoding='utf-8')), fieldnames=fields)
            summary.writeheader()
            traces = csv.writer(stack.enter_context((out / 'population_10ms.csv').open('w', newline='', encoding='utf-8')))
            traces.writerow(['trial_id'] + [f'bin_{i:03d}' for i in range(100)])
            baseline = base_manifest = group = None
            for job in plan['jobs']:
                directory = study / 'trials' / job['trial_id']
                manifest = validated(directory, job, plan)
                if set(manifest['input_ids']) != inputs:
                    raise ValueError('Input membership differs from the sugar protocol')
                rates, trace, row = inspect_trial(directory, manifest, ids)
                key = (job['variant']['name'], job['seed'])
                if job['condition'] == 'baseline':
                    baseline, base_manifest, group = rates, manifest, key
                    values, writer = rates, baseline_writer
                else:
                    if group != key or base_manifest['input_digest'] != manifest['input_digest']:
                        raise ValueError('Missing paired baseline or different scheduled inputs')
                    values, writer = rates - baseline, delta_writer
                    row.update(paired_total_abs_hz=float(np.abs(values).sum()), paired_fixed_mode_abs_hz=float(np.abs(values[mask]).sum()),
                               spike_file_identical_to_baseline=manifest['spike_digest'] == base_manifest['spike_digest'])
                indices = np.flatnonzero(values)
                writer.write_table(pa.Table.from_arrays([pa.array([job['trial_id']] * len(indices)), pa.array(indices, type=pa.int32()), pa.array(values[indices])], schema=schema))
                row.update(trial_id=job['trial_id'], variant=key[0], condition=job['condition'], seed=job['seed'])
                summary.writerow(row)
                traces.writerow([job['trial_id']] + trace.tolist())
                audit['completed_trials'] += 1
                if audit['completed_trials'] % 30 == 0:
                    write(out / 'audit.json', audit)
                    print(f"Checked {audit['completed_trials']}/{len(plan['jobs'])}", flush=True)
        if digest(study / 'jobs.json') != audit['jobs_sha256']:
            raise ValueError('Plan changed during analysis')
        audit.update(status='complete', finished_utc=utc(), outputs={p.name: digest(p) for p in out.iterdir() if p.name != 'audit.json'})
        write(out / 'audit.json', audit)
        print('Complete. No trials were simulated or changed.', flush=True)
    except BaseException as exc:
        audit.update(status='failed', error=repr(exc), finished_utc=utc())
        write(out / 'audit.json', audit)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    run(args.study, args.out)
