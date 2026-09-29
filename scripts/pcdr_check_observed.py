"""Check the completed recorded replay without changing simulation outputs."""
from pathlib import Path
import argparse
import sys
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import sha256, neuron_ids, fingerprint, atomic_json, now
from scripts.pcdr_ccr_transfer import read


def check(run, reference, out):
    if out.exists(): raise FileExistsError(out)
    plan = read(run / 'plan.json')
    if plan != read(ROOT / 'docs/pcdr/OBSERVED_REPLAY_PLAN.json'): raise ValueError('Changed plan')
    progress = read(run / 'progress.json')
    if progress['status'] != 'complete' or progress['completed'] != len(plan['jobs']):
        raise ValueError('Incomplete recorded run')
    ids = neuron_ids(); lookup = {v: i for i, v in enumerate(ids)}
    rows = []
    for j in plan['jobs']:
        directory = run / j['id']; m = read(directory / 'manifest.json')
        if m['status'] != 'complete' or m['spec'] != j: raise ValueError('Incomplete or changed worker')
        for name, expected in m['outputs'].items():
            if sha256(directory / name) != expected: raise ValueError('Changed output')
        process = read(run / 'logs' / j['id'] / 'process.json')
        if process['returncode'] or process['timed_out']: raise ValueError('Worker failed')
        ref = reference / 'trials' / j['id']
        if sha256(ref / 'manifest.json') != plan['reference_manifests'][j['id']]: raise ValueError('Reference changed')
        rm = read(ref / 'manifest.json')
        for name in ['spikes.parquet', 'delivered_events.parquet']:
            if sha256(ref / name) != rm['outputs'][name]: raise ValueError('Reference output changed')
            a, b = pd.read_parquet(directory / name), pd.read_parquet(ref / name)
            if fingerprint(a.to_dict('list')) != fingerprint(b.to_dict('list')): raise ValueError('Replay mismatch')
        spikes = pd.read_parquet(directory / 'spikes.parquet')
        ticks = round(1000 / j['dt_ms'])
        with np.load(directory / 'states.npz', allow_pickle=False) as state:
            if not np.array_equal(state['indices'], [lookup[v] for v in plan['record_ids']]):
                raise ValueError('Recording index mismatch')
            for slot in plan['slots']:
                time = state[slot + '_t_s']
                if time.shape != (ticks,) or not np.allclose(time, np.arange(ticks)*j['dt_ms']/1000, atol=1e-12, rtol=0):
                    raise ValueError('State clock mismatch')
                for variable in ['v_mV', 'g_mV', 'not_refractory']:
                    a = state[slot + '_' + variable]
                    if a.shape != (len(plan['record_ids']), ticks) or not np.isfinite(a).all():
                        raise ValueError('Invalid state array')
                    if variable == 'not_refractory' and a.dtype != bool: raise ValueError('Invalid refractory flag')
            v, eligible = state['before_thresholds_v_mV'], state['before_thresholds_not_refractory']
            for i, rid in enumerate(plan['record_ids']):
                actual = np.rint(spikes.loc[spikes.flywire_id == rid, 't'].to_numpy()*1000/j['dt_ms']).astype(int)
                predicted = np.flatnonzero((v[i] > -45) & eligible[i])
                if not np.array_equal(actual, predicted): raise ValueError('Recorded threshold states disagree with spikes')
        rows.append({'trial': j['id'], 'spikes': len(spikes), 'exact_replay': True,
                     'state_samples_per_slot': ticks, 'recorded_cells': len(plan['record_ids']),
                     'peak_rss_bytes': m['peak_rss_bytes'], 'started_utc': m['started_utc'],
                     'finished_utc': m['finished_utc'], 'manifest_sha256': sha256(directory / 'manifest.json')})
    differences = []
    paired = {(j['dt_ms'], j.get('condition')): j for j in plan['jobs']}
    for dt in sorted({j['dt_ms'] for j in plan['jobs']}):
        if (dt, 'baseline') not in paired or (dt, 'mode_without_mn9') not in paired:
            continue
        baseline = run / paired[dt, 'baseline']['id'] / 'states.npz'
        lesion = run / paired[dt, 'mode_without_mn9']['id'] / 'states.npz'
        with np.load(baseline, allow_pickle=False) as b, np.load(lesion, allow_pickle=False) as a:
            for i, rid in enumerate(plan['record_ids']):
                row = {'dt_ms': dt, 'root_id': rid}
                for variable in ['before_thresholds_v_mV', 'after_synapses_g_mV']:
                    indices = np.flatnonzero(a[variable][i] != b[variable][i])
                    row[variable + '_first_exact_difference_ms'] = float(indices[0]*dt) if len(indices) else None
                differences.append(row)
    atomic_json(out, {'checked_utc': now(), 'status': 'complete', 'rows': rows,
                     'first_state_differences': differences,
                     'plan_sha256': sha256(run / 'plan.json'), 'checker_sha256': sha256(Path(__file__)),
                     'limit': 'First state differences use exact stored floats and selected cells, not a physiological threshold or causal attribution. Exact events and threshold-state agreement do not establish a mechanism or time-step convergence.'})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['run', 'reference', 'out']: p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    check(a.run, a.reference, a.out)
