from pathlib import Path
import runpy
import numpy as np
from scripts.pcdr_ccr_transfer import read,write,utc
recurrence=runpy.run_path('tests/test_pcdr_local_replay.py')['recurrence']
p=Path('results/pcdr/baseline_count_replay_20261009')
r=read(p/'results.json')['records']
selected=[x for x in r if x['selection'] is not None]
checks=[]
for x in [selected[0],selected[-1]]:
    with np.load(p/f"{x['seed']}_inputs.npz") as data:
        actual=recurrence(data['coarse_arrivals'],data['coarse_weights'],x['stop_tick'],.0001)
    equal=np.array_equal(actual,x['fine_grid_coarse_history'])
    checks.append(dict(seed=x['seed'],exact_ticks=bool(equal),spikes=len(actual)))
    if not equal:raise ValueError('Sequential hybrid mismatch')
write(p/'hybrid_verification.json',dict(verified_utc=utc(),selection='Smallest and largest seed with selection, fixed before this numerical verification.',method='Independent sequential tick recurrence already used in prior known-answer tests; applied to these new hybrid histories.',checks=checks))
