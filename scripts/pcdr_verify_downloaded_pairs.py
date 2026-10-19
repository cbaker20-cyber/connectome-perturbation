"""Verify downloaded pair archives and compare saved one-second responses locally."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/pcdr/pairs_verified_20261019'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compare(a, b, support, pa, pb):
    ids = sorted(set(a.index) | set(b.index) | set(support))
    x, y = [v.reindex(ids, fill_value=0).to_numpy() for v in (a, b)]
    inside = np.isin(ids, support)
    ax, ay = [float(abs(v[inside]).sum() / len(support)) for v in (x, y)]
    fx, fy = [float(abs(v[inside]).sum() / abs(v).sum()) if abs(v).sum() else None for v in (x, y)]
    rel = float(abs(x-y).sum() / max(1., abs(y).sum()))
    fd = abs(fx-fy) if fx is not None and fy is not None else None
    temporal = max(float(abs(u-v).sum()/max(1., abs(v).sum())) for u,v in zip(pa,pb))
    return dict(A_coarse_hz=ax, A_fine_hz=ay, F_coarse=fx, F_fine=fy,
                A_difference_hz=abs(ax-ay), F_difference=fd, response_relative_L1=rel,
                population_relative_L1=temporal,
                passes=bool(abs(ax-ay)<=max(1.,.05*ay) and fd is not None and fd<=.01 and rel<=.05 and temporal<=.05))


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    records, trials, seen = [], {}, set()
    try:
        with zipfile.ZipFile(ROOT/'exports/CCR_Four_Trial.zip') as upload:
            prefix = 'connectome_four_trial/'
            plan = json.loads(upload.read(prefix+'smaller_plan.json'))
            specs = {j['id']:j for j in plan['jobs']}
            for path in sorted(Path('C:/Users/Baker/Downloads').glob('*.tmp')):
                if not zipfile.is_zipfile(path):
                    continue
                raw = path.read_bytes(); sha = digest(raw)
                if sha in seen:
                    continue
                seen.add(sha)
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    if 'results/progress.json' not in z.namelist():
                        continue
                    names = z.namelist()
                    require(len(names)==len(set(names)) and z.testzip() is None, 'ZIP integrity')
                    progress = json.loads(z.read('results/progress.json'))
                    if progress['status'] != 'pair_complete':
                        continue
                    for name in ('package_manifest.json','smaller_plan.json','execution_plan.json'):
                        require(z.read('package/'+name)==upload.read(prefix+name), 'Frozen package mismatch: '+name)
                    manifests = [n for n in names if n.startswith('results/trials/') and n.endswith('/manifest.json')]
                    # Recovery archives also include previously saved anchors.
                    manifests = [n for n in manifests if n.split('/')[-2] in specs]
                    require(len(manifests)==2 and progress['scientific_completed']==2, 'Pair incomplete')
                    row = dict(source=str(path), sha256=sha, trials=[])
                    for name in manifests:
                        m = json.loads(z.read(name)); spec = m['spec']; base = name.rsplit('/',1)[0]+'/'
                        require(spec==specs[spec['id']] and m['status']=='complete', 'Trial specification mismatch')
                        require(m['environment']['packages']==plan['packages'], 'Environment mismatch')
                        require(set(m['outputs'])=={'spikes.parquet','rates.parquet','population.json','delivered_events.parquet'}, 'Output set')
                        for f,h in m['outputs'].items():
                            require(digest(z.read(base+f))==h, 'Output hash mismatch: '+base+f)
                        s,r,d = [pd.read_parquet(io.BytesIO(z.read(base+f))) for f in ('spikes.parquet','rates.parquet','delivered_events.parquet')]
                        require(not s.isna().any().any() and not s.duplicated().any(), 'Missing/duplicate spikes')
                        require(all(isinstance(v,str) and v.isdigit() for v in s.flywire_id), 'Spike ID precision')
                        require(all(isinstance(v,str) and v.isdigit() for v in r.root_id) and r.root_id.is_unique, 'Rate ID precision/duplicates')
                        require(s.t.ge(0).all() and s.t.lt(1).all() and s.t.is_monotonic_increasing, 'Spike bounds/order')
                        require(np.allclose(s.t*1000/spec['dt_ms'],np.rint(s.t*1000/spec['dt_ms']),atol=1e-6,rtol=0), 'Off-grid spike')
                        counts = s.flywire_id.value_counts().sort_index()
                        rates = r.set_index('root_id').sort_index()
                        require(counts.index.tolist()==rates.index.tolist() and np.array_equal(counts.values,rates.spike_count.values) and np.array_equal(counts.values,rates.rate_hz.values), 'Rates differ from spike counts')
                        require(len(s)==m['spike_count'], 'Spike count metadata')
                        pop = np.asarray(json.loads(z.read(base+'population.json')))
                        require(np.array_equal(pop,np.bincount(np.floor((s.t.to_numpy()+1e-12)/.01).astype(int),minlength=100)), 'Population bins differ')
                        oldbase = prefix+'original/trials/'+spec['source_trial']+'/'
                        oldraw = upload.read(oldbase+'manifest.json'); old = json.loads(oldraw)
                        require(digest(oldraw)==m['source_manifest_sha256'] and old['input_digest']==m['physical_input_digest'], 'Input provenance')
                        scheduled = pd.read_parquet(io.BytesIO(upload.read(oldbase+'input_events.parquet')))
                        actual = d[['tick','flywire_id']].copy()
                        factor = round(.1/spec['dt_ms'])
                        require((actual.tick%factor==0).all(), 'Delivered input grid')
                        actual['tick'] = actual.tick//factor
                        pd.testing.assert_frame_equal(actual.reset_index(drop=True),scheduled[['tick','flywire_id']].reset_index(drop=True),check_dtype=False)
                        key = (spec['seed'],spec['dt_ms'],spec['condition'])
                        require(key not in trials, 'Duplicate scientific trial')
                        trials[key] = (rates.rate_hz,pop)
                        row['trials'].append(dict(id=spec['id'],spikes=len(s),active_cells=len(r),delivered_events=len(d)))
                    archive = OUT/(str(progress.get('seed',631401))+'_'+str(progress.get('dt_ms',.00005))+'.zip')
                    require(not archive.exists(), 'Archive name conflict')
                    shutil.copyfile(path,archive)
                    row['archive']=archive.name
                    records.append(row)
        comparisons=[]
        for seed in (631401,631402,631403):
            for cond in ('baseline','mode'):
                folder=ROOT/f'results/pcdr/fine_download_20261005/trials/fine_0p0001_default_{cond}_{seed}'
                m=json.loads((folder/'manifest.json').read_text())
                for f,h in m['outputs'].items():
                    require(digest((folder/f).read_bytes())==h,'Anchor hash mismatch')
                trials[seed,.0001,cond]=(pd.read_parquet(folder/'rates.parquet').set_index('root_id').rate_hz,np.asarray(json.loads((folder/'population.json').read_text())))
            for coarse,fine in ((.0001,.00005),(.00005,.000025)):
                keys=[(seed,dt,c) for dt in (coarse,fine) for c in ('baseline','mode')]
                if not all(k in trials for k in keys):
                    continue
                b0,m0,b1,m1=[trials[k] for k in keys]
                delta0=m0[0].subtract(b0[0],fill_value=0); delta1=m1[0].subtract(b1[0],fill_value=0)
                result=compare(delta0,delta1,plan['mode_ids'],[b0[1],m0[1]],[b1[1],m1[1]])
                comparisons.append(dict(seed=seed,coarse_ms=coarse,fine_ms=fine,**result))
        report=dict(archives=records,comparisons=comparisons,criteria=plan['criteria'],
                    original_30_seed_requirement_established=False,
                    limitations=['Partial three-seed pilot; no full-study convergence claim.', 'Archive consistency and saved-output reconstruction do not independently establish simulation equations.'])
        (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        pd.DataFrame(comparisons).to_csv(OUT/'comparisons.csv',index=False)
        print(json.dumps(report,indent=2))
    except BaseException as error:
        (OUT/'failure.json').write_text(json.dumps(dict(error=repr(error)),indent=2))
        raise


if __name__=='__main__':
    main()
