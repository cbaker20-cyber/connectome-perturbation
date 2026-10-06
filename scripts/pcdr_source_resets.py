"""Reconstruct two recorded source cells between resets using their saved incoming spikes."""
import argparse
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import neuron_ids
from scripts.pcdr_ccr_transfer import digest, write
from scripts.pcdr_recurrent_delivery import accepted
from scripts.pcdr_upstream_inputs import contribution

TARGETS = ['720575940629667639', '720575940623862015']


def segment(arrivals, post, tick, refractory):
    post = np.asarray(post, dtype=np.int64)
    arrivals = np.asarray(arrivals, dtype=np.int64)
    if np.any(np.diff(post) < 0) or np.any(post < 0) or np.any(arrivals < 0):
        raise ValueError('Spike ticks must be nonnegative and postsynaptic spikes sorted')
    previous = post[post < tick]
    if not len(previous):
        raise ValueError('A previous reset is required')
    last = int(previous[-1])
    picked = arrivals[(arrivals > last) & (arrivals < tick)]
    return last, picked, accepted(picked, post, refractory)


def run(archive, out):
    validation = json.loads((ROOT/'docs/pcdr/evidence/2026-10-05/diagnostic_return/validation.json').read_text(encoding='utf-8'))
    if digest(archive) != validation['archive_sha256']:
        raise ValueError('Changed archive')
    ids = neuron_ids()
    lookup = {v: i for i, v in enumerate(ids)}
    summaries, rows = [], []
    with zipfile.ZipFile(archive) as z:
        plan = json.loads(z.read('diagnostic_plan.json'))
        path = ROOT/'2023_03_23_connectivity_630_final.parquet'
        if digest(path) != plan['model_files'][path.name]:
            raise ValueError('Changed connectivity')
        con = pd.read_parquet(path)
        con = con[con.Postsynaptic_Index.isin([lookup[v] for v in TARGETS]) &
                  ~con.Presynaptic_Index.isin([lookup[v] for v in plan['lesion_ids']])].copy()
        con['weight'] = con['Excitatory x Connectivity']*.275*1.2
        con.loc[con.weight < 0, 'weight'] *= .8
        trains = {}
        for dt in [.0004, .0002]:
            frame = pd.read_parquet(io.BytesIO(z.read(f'{dt}/spikes.parquet')))
            trains[dt] = {lookup[v]: np.sort(np.rint(g.t.to_numpy()*1000/dt).astype(np.int64))
                          for v, g in frame.groupby('flywire_id')}
        for target in TARGETS:
            if target in plan['input_ids']:
                raise ValueError('Externally stimulated targets unsupported')
            # Compare both runs at the union of their observed crossings, without selecting new maxima.
            times = sorted({int(t)*dt for dt in trains for t in trains[dt][lookup[target]]
                            if 600 < t*dt < 640})
            for dt in trains:
                post = trains[dt][lookup[target]]
                for time in times:
                    tick = round(time/dt)
                    if abs(tick*dt-time) > 1e-8:
                        raise ValueError('Comparison time does not lie on both grids')
                    predicted = -52.
                    count = rejected = 0
                    last = int(post[post < tick][-1])
                    for edge in con[con.Postsynaptic_Index == lookup[target]].itertuples():
                        arrivals = trains[dt].get(edge.Presynaptic_Index, np.array([], dtype=np.int64))+round(1.8/dt)
                        last, selected, gate = segment(arrivals, post, tick, round(2.2/dt))
                        value = contribution(selected[gate], edge.weight, tick, dt)
                        predicted += value
                        count += int(gate.sum())
                        rejected += int((~gate).sum())
                        if len(selected):
                            rows.append(dict(target_id=target, dt_ms=dt, time_ms=time,
                                source_id=ids[edge.Presynaptic_Index], weight_mV=edge.weight,
                                accepted=int(gate.sum()), rejected=int((~gate).sum()),
                                accepted_arrivals_ms=json.dumps((selected[gate]*dt).tolist()),
                                voltage_contribution_mV=value))
                    start = tick//round(10/dt)*round(10/dt)
                    with np.load(io.BytesIO(z.read(f'{dt}/state/{start:010d}_before_thresholds.npz')), allow_pickle=False) as state:
                        i = plan['record_ids'].index(target)
                        observed = float(state['v_mV'][i, tick-start])
                        drive = float(state['g_mV'][i, tick-start])
                        ready = bool(state['not_refractory'][i, tick-start])
                    error = abs(predicted-observed)
                    if error > 1e-8:
                        raise ValueError(f'{target}, {dt}, {time}: reconstruction error {error}')
                    summaries.append(dict(target_id=target, dt_ms=dt, time_ms=time,
                        last_reset_ms=last*dt, recorded_voltage_mV=observed, drive_mV=drive,
                        ready=ready, spike=bool(np.any(post == tick)), accepted=count,
                        rejected=rejected, reconstructed_voltage_mV=predicted, absolute_error_mV=error))
    out.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(rows).to_csv(out/'contributions.csv', index=False)
    write(out/'summary.json', dict(comparisons=summaries, archive_sha256=validation['archive_sha256'],
        script_sha256=digest(Path(__file__)),
        interpretation='Conditional decomposition since each last reset. Incoming spikes remain observed, not recomputed under intervention.'))
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    run(args.archive, args.out)
