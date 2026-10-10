"""Read-only verification of the four-prefix smaller-step result archive."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    archive = root / 'CCR_smaller_pilot_results.zip'
    out = root / 'results/pcdr/smaller_verified_20261010'
    out.mkdir(exist_ok=False)
    try:
        with zipfile.ZipFile(archive) as z, zipfile.ZipFile(root / 'exports/CCR_Smaller_Pilot.zip') as upload:
            names = z.namelist()
            require(len(names) == len(set(names)), 'Duplicate ZIP member')
            require(z.testzip() is None, 'CRC failure')
            def read(name):
                return json.loads(z.read(name))
            prefix = upload.namelist()[0].split('/')[0] + '/'
            package_files = [n for n in names if n.startswith('package/')]
            for name in package_files:
                require(z.read(name) == upload.read(prefix + name.removeprefix('package/')), 'Source mismatch: ' + name)
            plan = read('package/smaller_plan.json')
            progress = read('results/progress.json')
            require(progress['scientific_completed'] == 0 and progress['status'] == 'budget_insufficient', 'Unexpected scientific status')
            require(len(plan['jobs']) == 12 and len({j['id'] for j in plan['jobs']}) == 12, 'Panel mismatch')
            require(not any(n.startswith('results/trials/') for n in names), 'Unexpected scientific outputs')
            rows, frames, inputs = [], {}, {}
            input_ids = set(read('package/original/trials/default_baseline_631401/manifest.json')['input_ids'])
            checked_hashes = {}
            for name in ['reference_baseline_0.0001', 'reference_mode_0.0001', 'probe_5e-05', 'probe_2.5e-05']:
                base = 'results/' + name + '/'
                m = read(base + 'measurement.json')
                process = read('results/logs/' + name + '/process.json')
                require(m['status'] == 'complete' and process['returncode'] == 0 and not process['timed_out'], 'Incomplete worker')
                require(m['duration_s'] == .01, 'Unexpected duration')
                for file, expected in m['outputs'].items():
                    actual = sha(z.read(base + file))
                    require(actual == expected, 'Output hash mismatch: ' + base + file)
                    checked_hashes[base + file] = actual
                s, scheduled, delivered = [pd.read_parquet(io.BytesIO(z.read(base + f + '.parquet'))) for f in ['spikes', 'scheduled', 'delivered']]
                for frame in [s, scheduled, delivered]:
                    require(not frame.isna().any().any() and not frame.duplicated().any(), 'Missing/duplicate event')
                    require(all(isinstance(v, str) and v.isdigit() for v in frame.flywire_id), 'ID precision/type')
                require(s.t.is_monotonic_increasing and s.t.ge(0).all() and s.t.lt(.01).all(), 'Spike bounds/order')
                require(np.allclose(s.t * 1000 / m['dt_ms'], np.rint(s.t * 1000 / m['dt_ms']), rtol=0, atol=1e-7), 'Off-grid spikes')
                pd.testing.assert_frame_equal(scheduled, delivered)
                # Integer 0.1-ms input ticks compare physical schedules across different simulation grids.
                factor = round(.1 / m['dt_ms'])
                require((scheduled.tick % factor == 0).all(), 'Input not on original physical grid')
                physical = scheduled.copy()
                physical['tick'] = physical.tick // factor
                source = pd.read_parquet(root / 'results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity/trials/default_baseline_631401/input_events.parquet')
                source = source.loc[source.tick < 100, ['tick', 'flywire_id']].reset_index(drop=True)
                pd.testing.assert_frame_equal(physical[['tick', 'flywire_id']], source, check_dtype=False)
                reference_match = None
                if name.startswith('reference'):
                    condition = 'mode' if 'mode' in name else 'baseline'
                    anchor = root / f'results/pcdr/fine_download_20261005/trials/fine_0p0001_default_{condition}_631401'
                    # Direct half-open physical-time selection, separate from the runner's rounded-tick selection.
                    original = pd.read_parquet(anchor / 'spikes.parquet')
                    original = original.loc[original.t < .01, ['t', 'flywire_id']].reset_index(drop=True)
                    pd.testing.assert_frame_equal(s, original, check_dtype=False, check_exact=True)
                    arrivals = pd.read_parquet(anchor / 'delivered_events.parquet')
                    arrivals = arrivals.loc[arrivals.tick < 100000].reset_index(drop=True)
                    pd.testing.assert_frame_equal(delivered, arrivals, check_dtype=False, check_exact=True)
                    reference_match = True
                frames[name] = s
                inputs[name] = physical
                rows.append(dict(run=name, dt_ms=m['dt_ms'], duration_ms=10, spikes=len(s), cells=s.flywire_id.nunique(), non_input_spikes=int((~s.flywire_id.isin(input_ids)).sum()), scheduled=len(scheduled), delivered=len(delivered), seconds=m['seconds'], peak_gb=m['peak_rss_bytes']/1e9, exact_old_reference=reference_match))
            comparisons = []
            order = ['reference_baseline_0.0001', 'probe_5e-05', 'probe_2.5e-05']
            for a, b in zip(order, order[1:]):
                x, y = frames[a], frames[b]
                require(x.flywire_id.tolist() == y.flywire_id.tolist(), 'Ordered spike identities differ; do not use ordinal timing match')
                delta = (y.t.to_numpy()-x.t.to_numpy())*1000
                counts = x.flywire_id.value_counts().subtract(y.flywire_id.value_counts(), fill_value=0)
                comparisons.append(dict(coarse=a, fine=b, count_l1=int(counts.abs().sum()), changed_spike_times=int(np.count_nonzero(delta)), max_abs_time_difference_ms=float(np.max(np.abs(delta))), mean_abs_time_difference_ms=float(np.mean(np.abs(delta)))))
            gate = read('results/capacity_gate.json')
            estimate = sum(6*2*r['seconds']*100 for r in rows if r['run'].startswith('probe'))
            require(np.isclose(estimate, gate['required_serial_seconds']) and not gate['allowed'], 'Capacity arithmetic mismatch')
            record = dict(archive_sha256=sha(archive.read_bytes()), package_files_matched=len(package_files), checked_output_hashes=checked_hashes, progress=progress, runs=rows, comparisons=comparisons, gate=gate, twelve_jobs=[dict(id=j['id'], seed=j['seed'], condition=j['condition'], dt_ms=j['dt_ms'], status='not_started', convergence='not_evaluated') for j in plan['jobs']], limitations=['Ten-ms prefixes only; no new-step lesion trial.', 'No new one-second footprint or convergence result.', 'Source identity and saved-output agreement are not independent human review.'])
            (out/'verification.json').write_text(json.dumps(record, indent=2)+'\n')
            print(json.dumps(record, indent=2))
    except BaseException as error:
        (out/'failure.json').write_text(json.dumps({'error':repr(error)}, indent=2)+'\n')
        raise


if __name__ == '__main__':
    main()
