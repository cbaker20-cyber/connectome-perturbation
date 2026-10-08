"""Run the selected two-connection intervention or its unchanged reference."""
import argparse
from contextlib import nullcontext
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'

import pandas as pd
import numpy as np
from eigencircuits.common import environment, neuron_ids, now
from eigencircuits.memory import peak_rss
from scripts.pcdr_burst_diagnostic import exact_prefix
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_edge_intervention import connectivity_without
from scripts.pcdr_late_switch import LateSwitch
from scripts.pcdr_fine_sim import simulate, input_tape

SOURCE = '720575940628695043'
TARGETS = ['720575940629667639', '720575940623862015']


class TrialProgress:
    def __init__(self, path):
        self.path = path

    def setup(self, network, neurons, dt_ms, duration_s):
        self.dt_ms = dt_ms
        self.duration_ms = duration_s*1000

    def monitors(self, start, length):
        return []

    def progress(self, tick):
        write(self.path, dict(simulated_ms=tick*self.dt_ms, duration_ms=self.duration_ms))


def endpoints(spikes, input_ids, dt_ms):
    noninput = spikes.loc[~spikes.flywire_id.isin(input_ids)].copy()
    ticks = np.rint(noninput.t.to_numpy()*1000/dt_ms).astype(np.int64)
    window = noninput.loc[(ticks >= round(650/dt_ms)) & (ticks < round(730/dt_ms))]
    earlier = set(noninput.loc[ticks < round(650/dt_ms), 'flywire_id'])
    return dict(noninput_spikes_650_730=len(window),
                newly_recruited_noninput_650_730=len(set(window.flywire_id)-earlier),
                source_times_ms={v: (spikes.loc[spikes.flywire_id.eq(v), 't']*1000).tolist()
                                 for v in [SOURCE]+TARGETS})


def worker(plan_path, out, dt, condition, duration_ms):
    if dt not in [.0004, .0002] or condition not in ['reference', 'two_edges', 'late_reference', 'late_edges', 'late_g', 'late_h'] or duration_ms not in [2, 750]:
        raise ValueError('Use the declared time steps, conditions and 2-ms timing check or 750-ms trial')
    plan_path, out = Path(plan_path), Path(out)
    plan = read(plan_path)
    for name, expected in plan['model_files'].items():
        if digest(ROOT/name) != expected:
            raise ValueError('Changed model/data: '+name)
    for name, expected in plan['reference_files'].items():
        if digest(plan_path.parent/name) != expected:
            raise ValueError('Changed reference: '+name)
    current = environment()
    if current['packages'] != plan['packages'] or sys.version_info[:2] != (3, 11):
        raise ValueError('Simulation packages or Python differ from the reference')
    if plan['seed'] != 631430 or plan['variant'] != 'w120_i080' or plan['condition'] != 'mn9_only':
        raise ValueError('Wrong reference experiment')
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    sources = [ROOT/'model.py', *sorted((ROOT/'scripts').glob('*.py')),
               *sorted((ROOT/'eigencircuits').glob('*.py'))]
    record = dict(status='running', started_utc=now(), dt_ms=dt, condition=condition,
                  duration_ms=duration_ms, plan_sha256=digest(plan_path), environment=current,
                  sources={p.relative_to(ROOT).as_posix(): digest(p) for p in sources})
    write(out/'manifest.json', record)
    try:
        ids = neuron_ids(); lookup = {v: i for i, v in enumerate(ids)}
        events = pd.read_parquet(plan_path.parent/'input_events.parquet')
        events = events.loc[events.tick < round(duration_ms*10)].copy()
        tape = input_tape(events, plan['input_ids'], dt, duration_ms/1000)
        con = ROOT/'2023_03_23_connectivity_630_final.parquet'
        context = (connectivity_without(con, [(lookup[SOURCE], lookup[v]) for v in TARGETS])
                   if condition == 'two_edges' else nullcontext((con, None)))
        late = condition.startswith('late_')
        switch_ms = 600 if duration_ms == 750 else 1
        targets = TARGETS[:1] if condition == 'late_g' else TARGETS[1:] if condition == 'late_h' else TARGETS
        recorder = (LateSwitch([(lookup[SOURCE], lookup[v]) for v in targets], switch_ms,
                               condition != 'late_reference', out) if late else
                    TrialProgress(out/'simulation_progress.json'))
        with context as (connectivity, removed):
            if removed is not None:
                removed.to_csv(out/'removed_edges.csv', index=False)
            spikes, scheduled, delivered = simulate(plan['seed'], [lookup[v] for v in plan['input_ids']],
                [lookup[v] for v in plan['lesion_ids']], tape=tape, duration_s=duration_ms/1000,
                dt_ms=dt, weight_scale=1.2, inhibitory_scale=.8,
                connectivity=connectivity, return_delivered=True,
                recorder=recorder, chunk_ms=1 if duration_ms == 2 and late else 10)
        for frame in [spikes, scheduled, delivered]:
            frame['flywire_id'] = pd.Series([ids[i] for i in frame.pop('neuron_index')], dtype='string')
        # Keep returned events even if a comparison fails, so the failure can be examined.
        spikes.to_parquet(out/'spikes.parquet', index=False)
        scheduled.to_parquet(out/'scheduled_events.parquet', index=False)
        delivered.to_parquet(out/'delivered_events.parquet', index=False)
        expected = events.copy(); expected['tick'] *= round(.1/dt)
        exact_prefix(scheduled, expected, duration_ms, dt)
        ref = plan_path.parent/'reference'/str(dt)
        exact_prefix(delivered, pd.read_parquet(ref/'delivered_events.parquet'), duration_ms, dt)
        if late:
            if not recorder.applied:
                raise RuntimeError('Requested switch was not applied')
            exact_prefix(spikes.loc[spikes.t < switch_ms/1000].reset_index(drop=True),
                         pd.read_parquet(ref/'spikes.parquet'), switch_ms, dt, True)
            record.update(exact_pre_switch_spikes=True, switch_ms=switch_ms)
        if condition in ['reference', 'late_reference']:
            exact_prefix(spikes, pd.read_parquet(ref/'spikes.parquet'), duration_ms, dt, True)
        if duration_ms == 750:
            write(out/'endpoints.json', endpoints(spikes, plan['input_ids'], dt))
        record.update(status='complete', finished_utc=now(), elapsed_seconds=time.perf_counter()-started,
                      peak_rss_bytes=peak_rss(), exact_delivered_input=True,
                      exact_reference_spikes=True if condition in ['reference', 'late_reference'] else None,
                      outputs={p.name: digest(p) for p in out.iterdir() if p.name != 'manifest.json'})
        write(out/'manifest.json', record)
    except BaseException as error:
        record.update(status='failed', finished_utc=now(), error=repr(error))
        write(out/'manifest.json', record)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--dt', type=float, required=True)
    parser.add_argument('--condition', choices=['reference', 'two_edges', 'late_reference', 'late_edges', 'late_g', 'late_h'], required=True)
    parser.add_argument('--duration-ms', type=int, choices=[2, 750], default=750)
    args = parser.parse_args()
    worker(args.plan, args.out, args.dt, args.condition, args.duration_ms)
