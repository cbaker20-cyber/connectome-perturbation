"""Require exact scheduled-input identity across completed backend benchmarks."""
import argparse,json
from pathlib import Path

def check(directory):
    directory=Path(directory);checks=[]
    for seed in range(630801,630831):
      for condition in ['baseline','lesion']:
        manifests=[json.loads((directory/b/f'{condition}_{seed}'/'manifest.json').read_text()) for b in ['numpy','cython']]
        a,b=manifests
        assert a['status']==b['status']=='complete'
        for key in ['seed','input_digest','input_protocol','duration_s','dt_ms','input_hz','context','lesion_ids','weight_scale','inhibitory_scale','strong_fraction']:
          if a[key]!=b[key]:raise ValueError(f'{condition} {seed}: backend mismatch in {key}')
        checks.append({'seed':seed,'condition':condition,'scheduled_inputs_equal':True})
    return checks

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--benchmark',required=True);a=p.parse_args()
    print(json.dumps({'passed':True,'checks':check(a.benchmark)}))
