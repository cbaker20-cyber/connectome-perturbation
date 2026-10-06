"""Verify downloaded diagnostic records and summarize the observed source cells."""
import argparse
import hashlib
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
from scripts.pcdr_burst_diagnostic import exact_prefix


def sha(data):
    return hashlib.sha256(data).hexdigest()


def analyze(archive, out):
    out.mkdir(parents=True, exist_ok=False)
    rows, trials = [], []
    ids = neuron_ids()
    with zipfile.ZipFile(archive) as z, zipfile.ZipFile(ROOT/'exports/CCR_Diagnostic.zip') as upload:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive members')
        plan_bytes = z.read('diagnostic_plan.json')
        if plan_bytes != upload.read('connectome_diagnostic/diagnostic_plan.json'):
            raise ValueError('Downloaded plan differs from uploaded plan')
        plan = json.loads(plan_bytes)
        if json.loads(z.read('progress.json'))['status'] != 'complete':
            raise ValueError('Incomplete controller')
        indices = np.array([ids.index(v) for v in plan['record_ids']])
        for dt in plan['dt_ms']:
            base = str(dt)+'/'
            m = json.loads(z.read(base+'manifest.json'))
            if (m['status'] != 'complete' or m['plan_sha256'] != sha(plan_bytes)
                    or m['record_ids'] != plan['record_ids'] or m['dt_ms'] != dt
                    or m['duration_ms'] != 750 or m['record_window_ms'] != [600, 750]
                    or m['environment']['packages'] != plan['packages']):
                raise ValueError('Invalid trial manifest')
            for name, h in m['sources'].items():
                data = z.read('source/'+name)
                if sha(data) != h or data != upload.read('connectome_diagnostic/'+name):
                    raise ValueError('Source mismatch: '+name)
            expected = {'spikes.parquet','delivered_events.parquet','state/schedule.json','state/progress.json'}
            expected.update(f'state/{round(t/dt):010d}_{phase}.npz'
                            for t in range(600,750,10) for phase in ('before_thresholds','after_synapses','end'))
            if set(m['outputs']) != expected:
                raise ValueError('Unexpected output set')
            spikes = pd.read_parquet(io.BytesIO(z.read(base+'spikes.parquet')))
            events = pd.read_parquet(io.BytesIO(z.read(base+'delivered_events.parquet')))
            for frame, name, is_spike in [(spikes,'spikes',True),(events,'delivered_events',False)]:
                reference = pd.read_parquet(io.BytesIO(upload.read(f'connectome_diagnostic/reference/{dt}/{name}.parquet')))
                exact_prefix(frame, reference, 750, dt, is_spike)
            crossings = {v:[] for v in plan['record_ids']}
            for name, h in m['outputs'].items():
                data = z.read(base+name)
                if sha(data) != h:
                    raise ValueError('Output hash mismatch: '+name)
                if not name.endswith('.npz'):
                    continue
                with np.load(io.BytesIO(data), allow_pickle=False) as a:
                    tick, v, g, ready = (a[k] for k in ('tick','v_mV','g_mV','not_refractory'))
                    start = int(Path(name).name.split('_')[0])
                    if (not np.array_equal(tick,np.arange(start,start+round(10/dt)))
                            or not np.array_equal(a['indices'],indices)
                            or v.shape != (34,len(tick)) or g.shape != v.shape or ready.shape != v.shape
                            or ready.dtype != np.bool_ or not np.isfinite(v).all() or not np.isfinite(g).all()):
                        raise ValueError('Invalid recorded array: '+name)
                    if name.endswith('_before_thresholds.npz'):
                        for i, root in enumerate(plan['record_ids']):
                            crossings[root].extend(tick[(v[i] > -45) & ready[i]].tolist())
                            rows.append(dict(dt_ms=dt,root_id=root,start_ms=round(start*dt),
                                initial_v_mV=float(v[i,0]),initial_g_mV=float(g[i,0]),
                                v_min_mV=float(v[i].min()),v_max_mV=float(v[i].max()),
                                g_min_mV=float(g[i].min()),g_max_mV=float(g[i].max()),
                                refractory_fraction=float((~ready[i]).mean())))
            for root, observed in crossings.items():
                times = spikes.loc[spikes.flywire_id.astype(str).eq(root),'t'].to_numpy()
                ticks = np.rint(times*1000/dt).astype(np.int64)
                wanted = ticks[(ticks >= round(600/dt)) & (ticks < round(750/dt))]
                if not np.array_equal(observed,wanted):
                    raise ValueError('Threshold/spike mismatch: '+root)
            trials.append({k:m[k] for k in ['dt_ms','spikes','started_utc','finished_utc','peak_rss_bytes']})
            trials[-1].update(verified_output_files=len(expected),threshold_spike_matches=34,
                              exact_spike_prefix=True,exact_delivery_prefix=True)
        # Reading every remaining member also checks CRCs on logs and archived metadata.
        for name in names:
            if '/state/' not in name:
                z.read(name)
    pd.DataFrame(rows).to_csv(out/'state_windows.csv',index=False)
    with archive.open('rb') as f:
        archive_hash = hashlib.file_digest(f,'sha256').hexdigest()
    result = dict(archive=str(archive.resolve()),archive_sha256=archive_hash,
                  archive_bytes=archive.stat().st_size,plan_sha256=sha(plan_bytes),trials=trials,
                  scope='Recorded states cover 600–750 ms, 34 selected cells. No causal intervention performed.')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('out',type=Path)
    args = parser.parse_args()
    analyze(args.archive,args.out)
