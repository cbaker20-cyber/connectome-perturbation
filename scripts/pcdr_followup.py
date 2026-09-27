"""Run the recorded CCR follow-up in order and package its results."""
import os
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
os.environ['MPLBACKEND'] = 'Agg'
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import environment, fingerprint, neuron_ids, sugar_ids, MN9
from eigencircuits.readouts import footprint
from scripts.pcdr_ccr_transfer import read, write, digest, utc, verify
from scripts.pcdr_ccr_sensitivity import validated
from scripts.pcdr_bounded_process import run_bounded
from scripts.pcdr_followup_sim import input_tape, simulate


def worker(study, out, spec):
    plan = read(study / 'jobs.json')
    original = next(j for j in plan['jobs'] if j['trial_id'] == spec['source_trial'])
    source = study / 'trials' / spec['source_trial']
    old = validated(source, original, plan)
    ids = neuron_ids()
    lookup = {v: i for i, v in enumerate(ids)}
    inputs = old['input_ids']
    scheduled = pd.read_parquet(source / 'input_events.parquet')
    if fingerprint(scheduled.to_dict('list')) != old['input_digest']:
        raise ValueError('Source input digest mismatch')
    tape = input_tape(scheduled, inputs, spec['dt_ms'])
    out.mkdir(parents=True, exist_ok=False)
    record = {'status': 'running', 'started_utc': utc(), 'spec': spec,
              'environment': environment(), 'source_manifest_sha256': digest(source / 'manifest.json'),
              'physical_input_digest': old['input_digest']}
    write(out / 'manifest.json', record)
    try:
        spikes, external, delivered = simulate(original['seed'], [lookup[x] for x in inputs],
            [lookup[x] for x in spec['lesion_ids']], tape=tape, dt_ms=spec['dt_ms'],
            weight_scale=original['variant']['weight_scale'], inhibitory_scale=original['variant']['inhibitory_scale'],
            return_delivered=True)
        for frame in [spikes, external, delivered]:
            frame['flywire_id'] = pd.Series([ids[i] for i in frame.pop('neuron_index')], dtype='string')
        if not np.array_equal(external.tick.to_numpy(), scheduled.tick.to_numpy() * round(.1 / spec['dt_ms'])) or external.flywire_id.tolist() != scheduled.flywire_id.tolist():
            raise ValueError('Physical input times changed')
        if not pd.MultiIndex.from_frame(delivered).isin(pd.MultiIndex.from_frame(external)).all():
            raise ValueError('Delivered event absent from input tape')
        ticks = np.rint(spikes.t.to_numpy() * 1000 / spec['dt_ms']).astype(np.int64)
        if not np.allclose(spikes.t, ticks * spec['dt_ms'] / 1000, atol=1e-10, rtol=0) or np.any(ticks < 0) or np.any(ticks >= len(tape)):
            raise ValueError('Invalid spike time')
        ordered = spikes.sort_values(['flywire_id', 't'])
        gaps = ordered.groupby('flywire_id').t.diff()
        minimum = np.where(ordered.flywire_id.isin(inputs), spec['dt_ms'] / 1000, .0022)
        if np.any(gaps.to_numpy() < minimum - 1e-10):
            raise ValueError('Spike spacing violates the recorded refractory setting')
        counts = spikes.groupby('flywire_id').size()
        rates = pd.DataFrame({'root_id': counts.index, 'spike_count': counts.values, 'rate_hz': counts.values.astype(float)})
        spikes.to_parquet(out / 'spikes.parquet', index=False)
        rates.to_parquet(out / 'rates.parquet', index=False)
        delivered.to_parquet(out / 'delivered_events.parquet', index=False)
        trace = np.bincount(np.floor((spikes.t.to_numpy() + 1e-12) / .01).astype(int), minlength=100)
        write(out / 'population.json', trace.tolist())
        replay = fingerprint(spikes[['t', 'flywire_id']].to_dict('list')) == old['spike_digest']
        delivery_replay = fingerprint(delivered.to_dict('list')) == old['delivered_input_digest']
        if spec['stage'] == 'replay' and not (replay and delivery_replay):
            raise ValueError('Exact replay differs from saved spike or delivered-event records')
        record.update(status='complete', finished_utc=utc(), spike_count=len(spikes),
            recruited_noninput=len(set(counts.index) - set(inputs)), mn9_hz=float(counts.get(MN9, 0)),
            spike_digest=fingerprint(spikes[['t', 'flywire_id']].to_dict('list')),
            exact_spike_replay=replay, exact_delivery_replay=delivery_replay,
            sparse_rates='Missing root IDs mean zero; neuron universe is in the study package.',
            outputs={p.name: digest(p) for p in out.iterdir() if p.name != 'manifest.json'})
        write(out / 'manifest.json', record)
    except BaseException as error:
        record.update(status='failed', error=repr(error), finished_utc=utc())
        write(out / 'manifest.json', record)
        raise


def rate_vector(path, ids):
    frame = pd.read_parquet(path)
    if frame.root_id.duplicated().any() or not set(frame.root_id) <= set(ids):
        raise ValueError('Invalid rate IDs')
    result = frame.set_index('root_id').rate_hz.reindex(ids, fill_value=0).to_numpy()
    if not np.isfinite(result).all() or np.any(result < 0):
        raise ValueError('Invalid rate values')
    return result


def collect(study, out, plan):
    ids = neuron_ids(); lookup = {v: i for i, v in enumerate(ids)}
    support = [lookup[v] for v in plan['mode_ids']]
    rows, reduced = [], []
    for spec in plan['jobs']:
        directory = out / 'trials' / spec['id']
        m = read(directory / 'manifest.json')
        if m['status'] != 'complete' or m['spec'] != spec:
            raise ValueError('Incomplete or changed follow-up trial')
        for name, expected in m['outputs'].items():
            if digest(directory / name) != expected: raise ValueError('Changed worker output')
        values = rate_vector(directory / 'rates.parquet', ids)
        original = rate_vector(study / 'trials' / spec['source_trial'] / 'rates.parquet', ids)
        row = {**spec, 'spikes': m['spike_count'], 'mn9_hz': m['mn9_hz'],
               'difference_from_source_l1_hz': float(np.abs(values - original).sum())}
        row.pop('lesion_ids')
        rows.append(row)
        if spec['stage'] == 'active29':
            baseline = rate_vector(study / 'trials' / f"default_baseline_{spec['seed']}" / 'rates.parquet', ids)
            reduced.append(values - baseline)
    pd.DataFrame(rows).to_csv(out / 'trial_summary.csv', index=False)
    mean = np.mean(reduced, axis=0)
    full = np.mean([rate_vector(study / 'trials' / f'default_mode_{s}' / 'rates.parquet', ids) - rate_vector(study / 'trials' / f'default_baseline_{s}' / 'rates.parquet', ids) for s in plan['seeds']], axis=0)
    write(out / 'active29_summary.json', {'fixed_51_support': footprint(mean, support),
        'full_mode_fixed_51_support': footprint(full, support),
        'mean_vector_difference_l1_hz': float(np.abs(mean - full).sum()),
        'mn9_change_hz': float(mean[lookup[MN9]]),
        'interpretation': 'Retrospective comparison on existing seeds; no equivalence threshold or reference p-value.'})
    pairs = []
    for spec in plan['jobs']:
        if spec['stage'] not in ['replay', 'timestep'] or not spec['lesion_ids'] or not spec['source_trial'].startswith('w120_i080_'): continue
        baseline_id = (f"replay_w120_i080_baseline_{spec['seed']}" if spec['stage'] == 'replay'
                       else f"dt{str(spec['dt_ms']).replace('.', 'p')}_{spec['baseline_trial']}")
        a = rate_vector(out / 'trials' / spec['id'] / 'rates.parquet', ids)
        b = rate_vector(out / 'trials' / baseline_id / 'rates.parquet', ids)
        pairs.append({'trial': spec['id'], 'dt_ms': spec['dt_ms'], 'seed': spec['seed'],
                      **footprint(a - b, support), 'mn9_change_hz': float(a[lookup[MN9]] - b[lookup[MN9]])})
    pd.DataFrame(pairs).to_csv(out / 'timestep_pairs.csv', index=False)


def run(study, out, hours):
    if not 0 < hours <= 24: raise ValueError('Use a positive limit up to 24 hours')
    if out == study or study in out.parents:
        raise ValueError('Keep new outputs outside the original study')
    if list(study.glob('*.lock')):
        raise ValueError('Original study still has locks; check its workers first')
    from scripts.pcdr_ccr_capacity import allocation
    cpus, memory = allocation()
    if cpus < 4 or memory < 16000: raise ValueError('Request at least 4 cores and 16000 MB')
    workers = min(16, cpus - 2, (memory - 8000) // 8000)
    if workers < 1: raise ValueError('Insufficient memory for a worker')
    verify()
    frozen = read(study / 'jobs.json')
    plan = read(ROOT / 'followup_plan.json')
    if digest(study / 'jobs.json') != plan['original_jobs_sha256']:
        raise ValueError('Wrong original study')
    for name, expected in plan['sources'].items():
        if digest(ROOT / name) != expected: raise ValueError('Changed follow-up source: ' + name)
    current = environment()
    for key in ['python', 'packages']:
        if current[key] != frozen['provenance']['environment'][key]:
            raise ValueError('Simulation Python/packages differ from the original run')
    lookup = {j['trial_id']: j for j in frozen['jobs']}
    required = {j['source_trial'] for j in plan['jobs']} | {f'default_baseline_{s}' for s in plan['seeds']}
    for trial in sorted(required): validated(study / 'trials' / trial, lookup[trial], frozen)
    active = set()
    for seed in plan['seeds']:
        r = pd.read_parquet(study / 'trials' / f'default_baseline_{seed}' / 'rates.parquet')
        active.update(r.loc[r.rate_hz > 0, 'root_id'])
    if sorted(active & set(plan['mode_ids'])) != plan['active_ids']:
        raise ValueError('Active membership differs from the frozen plan')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'plan.json', plan)
    pd.DataFrame({'root_id': neuron_ids()}).to_csv(out / 'neurons.csv', index=False)
    status = {'status': 'running', 'started_utc': utc(), 'completed': 0, 'workers': workers,
              'analysis_environment': current, 'simulation_environment_original': frozen['provenance']['environment']}
    write(out / 'progress.json', status)
    deadline = time.monotonic() + hours * 3600
    def execute(spec):
        remaining = deadline - time.monotonic()
        if remaining <= 0: raise TimeoutError('Run time limit reached')
        command = [sys.executable, str(Path(__file__).resolve()), 'worker', '--study', str(study), '--out', str(out), '--index', str(plan['jobs'].index(spec))]
        result = run_bounded(command, out / 'logs' / spec['id'], min(1800, remaining), cwd=ROOT)
        write(out / 'logs' / spec['id'] / 'process.json', result)
        if result['returncode'] or result['timed_out']:
            raise RuntimeError('Worker failed: ' + spec['id'] + '; read its stderr.txt')
        return spec['id']
    try:
        for stage in ['replay', 'timestep', 'active29']:
            jobs = [j for j in plan['jobs'] if j['stage'] == stage]
            status['stage'] = stage
            write(out / 'progress.json', status)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for start in range(0, len(jobs), workers):
                    for name in pool.map(execute, jobs[start:start + workers]):
                        status['completed'] += 1
                        write(out / 'progress.json', status)
                        print(f"{status['completed']}/{len(plan['jobs'])}: {name}", flush=True)
        collect(study, out, plan)
        status.update(status='complete', finished_utc=utc(), interpretation='Time-step results require review; completion does not certify convergence.')
        write(out / 'progress.json', status)
    except BaseException as error:
        status.update(status='failed', error=repr(error), finished_utc=utc())
        write(out / 'progress.json', status)
        raise
    finally:
        # Even a stopped stage returns its records and logs for local diagnosis.
        for name in plan['sources']:
            destination = out / 'source' / Path(name).name
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes((ROOT / name).read_bytes())
        with zipfile.ZipFile(out / 'CCR_followup_results.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(out.rglob('*')):
                if path.is_file() and path.name not in ['CCR_followup_results.zip', 'spikes.parquet', 'delivered_events.parquet']:
                    archive.write(path, path.relative_to(out))
        print('Download: ' + str(out / 'CCR_followup_results.zip'), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['run', 'worker'])
    p.add_argument('--study', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--hours', type=float, default=6.)
    p.add_argument('--index', type=int)
    a = p.parse_args()
    if a.action == 'run': run(a.study.resolve(), a.out.resolve(), a.hours)
    else:
        plan = read(a.out / 'plan.json')
        if a.index is None or not 0 <= a.index < len(plan['jobs']): p.error('Invalid job index')
        spec = plan['jobs'][a.index]
        worker(a.study, a.out / 'trials' / spec['id'], spec)
