"""Further time-step comparisons; original completed follow-up files stay unchanged."""
import os
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
os.environ['MPLBACKEND'] = 'Agg'
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import time
import zipfile
import subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import environment, fingerprint, neuron_ids, MN9
from eigencircuits.readouts import footprint
from scripts.pcdr_ccr_transfer import read, write, digest, utc, verify
from scripts.pcdr_ccr_sensitivity import validated
from scripts.pcdr_bounded_process import run_bounded
from scripts.pcdr_followup_sim import simulate, input_tape as original_tape


def input_tape(events, input_ids, dt_ms, duration_s=1.):
    if dt_ms not in (.1, .05, .025, .0125, .00625):
        raise ValueError('Use a declared time step')
    base = original_tape(events, input_ids, .1, duration_s)
    factor = round(.1 / dt_ms)
    tape = np.zeros((len(base) * factor, len(input_ids)), dtype=np.int8)
    tape[::factor] = base
    return tape


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
        from eigencircuits.memory import peak_rss
        record.update(peak_rss_bytes=peak_rss(), status='complete', finished_utc=utc(), spike_count=len(spikes),
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


def rates(path, ids):
    frame = pd.read_parquet(path)
    if frame.root_id.duplicated().any() or not set(frame.root_id) <= set(ids):
        raise ValueError('Invalid rate IDs')
    values = frame.set_index('root_id').rate_hz.reindex(ids, fill_value=0).to_numpy()
    if not np.isfinite(values).all() or np.any(values < 0): raise ValueError('Invalid rates')
    return values


def collect(out, plan):
    ids = neuron_ids(); lookup = {v: i for i, v in enumerate(ids)}
    mode = [lookup[v] for v in plan['mode_ids']]
    jobs = {(j['stage'], j['dt_ms'], j['variant'], j['condition'], j['seed']): j for j in plan['jobs']}
    groups, per_seed, trials = {}, [], []
    for j in plan['jobs']:
        directory = out / 'trials' / j['id']
        m = read(directory / 'manifest.json')
        if m['status'] != 'complete' or m['spec'] != j: raise ValueError('Incomplete or changed trial')
        for name, expected in m['outputs'].items():
            if digest(directory / name) != expected: raise ValueError('Changed worker output')
        trials.append({'trial': j['id'], 'spikes': m['spike_count'], 'mn9_hz': m['mn9_hz'],
                       'recruited_noninput': m['recruited_noninput'], 'peak_rss_bytes': m['peak_rss_bytes']})
        if j['stage'] == 'replay' or j['condition'] == 'baseline': continue
        base = jobs[j['stage'], j['dt_ms'], j['variant'], 'baseline', j['seed']]
        bm = read(out / 'trials' / base['id'] / 'manifest.json')
        if bm['physical_input_digest'] != m['physical_input_digest']: raise ValueError('Unpaired input')
        delta = rates(directory / 'rates.parquet', ids) - rates(out / 'trials' / base['id'] / 'rates.parquet', ids)
        support = [lookup[v] for v in j['lesion_ids']]
        key = (j['stage'], j['dt_ms'], j['variant'], j['condition'])
        groups.setdefault(key, []).append(delta)
        per_seed.append({'stage': key[0], 'dt_ms': key[1], 'variant': key[2], 'condition': key[3], 'seed': j['seed'],
                         **footprint(delta, support), 'fixed_mode_A': footprint(delta, mode)['A'],
                         'fixed_mode_F': footprint(delta, mode)['F'], 'mn9_change_hz': delta[lookup[MN9]]})
    means = []
    for key, deltas in groups.items():
        example = next(j for j in plan['jobs'] if (j['stage'], j['dt_ms'], j['variant'], j['condition']) == key)
        support = [lookup[v] for v in example['lesion_ids']]
        mean = np.mean(deltas, axis=0)
        means.append({'stage': key[0], 'dt_ms': key[1], 'variant': key[2], 'condition': key[3], 'n_pairs': len(deltas),
                      **footprint(mean, support), 'fixed_mode': footprint(mean, mode), 'mn9_change_hz': float(mean[lookup[MN9]])})
    pd.DataFrame(trials).to_csv(out / 'trial_summary.csv', index=False)
    pd.DataFrame(per_seed).to_csv(out / 'per_seed.csv', index=False)
    write(out / 'mean_results.json', {'rows': means, 'interpretation': 'Descriptive time-step comparisons on previously used seeds. Completion is not a convergence claim.'})


def seconds_left(value):
    value = value.strip()
    if not value or value in ['UNLIMITED', 'NOT_SET', 'INVALID']: raise ValueError('Cannot establish Slurm time remaining')
    days, clock = value.split('-', 1) if '-' in value else ('0', value)
    fields = [int(x) for x in clock.split(':')]
    if len(fields) == 2: fields.insert(0, 0)
    if len(fields) != 3 or min(fields) < 0: raise ValueError('Invalid Slurm time remaining')
    return int(days) * 86400 + fields[0] * 3600 + fields[1] * 60 + fields[2]


def run(study, out, hours):
    from scripts.pcdr_ccr_capacity import allocation
    if not 0 < hours <= 12: raise ValueError('Set a positive run limit up to 12 hours')
    if out == study or study in out.parents: raise ValueError('Keep new outputs outside the old study')
    if list(study.glob('*.lock')): raise ValueError('Original study has worker locks')
    cpus, memory = allocation()
    workers = min(16, cpus - 2, (memory - 8000) // 8000)
    if workers < 1: raise ValueError('Insufficient CPU or memory allocation')
    remaining = seconds_left(subprocess.check_output(['squeue', '-h', '-j', os.environ['SLURM_JOB_ID'], '-o', '%L'], text=True))
    budget = min(hours * 3600, remaining - 1800)
    if budget < 1800: raise ValueError('Less than one hour remains; use a new allocation')
    deadline = time.monotonic() + budget
    verify()
    plan = read(ROOT / 'resolution_plan.json')
    if digest(study / 'jobs.json') != plan['original_jobs_sha256']: raise ValueError('Different original study')
    if digest(ROOT / 'followup_plan.json') != plan['previous_plan_sha256']: raise ValueError('Different previous selection plan')
    for name, expected in plan['sources'].items():
        if digest(ROOT / name) != expected: raise ValueError('Changed source: ' + name)
    original = read(study / 'jobs.json'); current = environment()
    for key in ['python', 'packages']:
        if current[key] != original['provenance']['environment'][key]: raise ValueError('Changed simulation environment')
    old = {j['trial_id']: j for j in original['jobs']}
    if len({j['id'] for j in plan['jobs']}) != len(plan['jobs']): raise ValueError('Duplicate jobs')
    for name in sorted({j['source_trial'] for j in plan['jobs']}): validated(study / 'trials' / name, old[name], original)
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'plan.json', plan)
    pd.DataFrame({'root_id': neuron_ids()}).to_csv(out / 'neurons.csv', index=False)
    status = {'status': 'running', 'started_utc': utc(), 'completed': 0, 'workers': workers,
              'budget_seconds': budget, 'environment': current, 'slurm_job_id': os.environ['SLURM_JOB_ID']}
    write(out / 'progress.json', status)
    def execute(index):
        j = plan['jobs'][index]
        remaining = deadline - time.monotonic()
        if remaining <= 0: raise TimeoutError('Worker time budget reached')
        command = [sys.executable, str(Path(__file__).resolve()), 'worker', '--study', str(study), '--out', str(out), '--index', str(index)]
        result = run_bounded(command, out / 'logs' / j['id'], min(3600, remaining), cwd=ROOT)
        write(out / 'logs' / j['id'] / 'process.json', result)
        if result['returncode'] or result['timed_out']: raise RuntimeError('Worker failed: ' + j['id'])
        return j['id']
    try:
        for stage in ['replay', 'finer', 'default']:
            indices = [i for i, j in enumerate(plan['jobs']) if j['stage'] == stage]
            status['stage'] = stage; write(out / 'progress.json', status)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for start in range(0, len(indices), workers):
                    for name in pool.map(execute, indices[start:start + workers]):
                        status['completed'] += 1; write(out / 'progress.json', status)
                        print(f"{status['completed']}/{len(plan['jobs'])}: {name}", flush=True)
        collect(out, plan)
        status.update(status='complete', finished_utc=utc()); write(out / 'progress.json', status)
    except BaseException as error:
        status.update(status='failed', error=repr(error), finished_utc=utc()); write(out / 'progress.json', status)
        raise
    finally:
        for name in plan['sources']:
            destination = out / 'source' / Path(name).name
            destination.parent.mkdir(exist_ok=True); destination.write_bytes((ROOT / name).read_bytes())
        # Include full trial evidence this time, avoiding a second download request.
        with zipfile.ZipFile(out / 'CCR_resolution_results.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for p in sorted(out.rglob('*')):
                if p.is_file() and p.name != 'CCR_resolution_results.zip': archive.write(p, p.relative_to(out))
        print('Download: ' + str(out / 'CCR_resolution_results.zip'), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['run', 'worker'])
    p.add_argument('--study', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--hours', type=float, default=3.5); p.add_argument('--index', type=int)
    args = p.parse_args()
    if args.action == 'run': run(args.study.resolve(), args.out.resolve(), args.hours)
    else:
        plan = read(args.out / 'plan.json')
        if args.index is None or not 0 <= args.index < len(plan['jobs']): p.error('Invalid worker index')
        spec = plan['jobs'][args.index]
        worker(args.study, args.out / 'trials' / spec['id'], spec)

