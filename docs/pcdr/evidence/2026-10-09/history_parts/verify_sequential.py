from pathlib import Path
import runpy
import numpy as np
from scripts.pcdr_ccr_transfer import read,write,utc
p=Path('results/pcdr/history_parts_20261009')
recurrence=runpy.run_path('tests/test_pcdr_local_replay.py')['recurrence']
r=read(p/'results.json')['records']
seeds=sorted({x['seed'] for x in r if x['selection'] is not None})
checks=[]
for x in r:
    if x['selection'] is None or x['seed'] not in (seeds[0],seeds[-1]):continue
    for key in ('cf','fc'):
        with np.load(p/f"{x['seed']}_{x['rule']}_{key}.npz") as z:
            actual=recurrence(z['arrivals'],z['weights'],x['selection']['stop_tick'],.0001)
        equal=np.array_equal(actual,x['histories'][key]['spikes'])
        checks.append(dict(seed=x['seed'],rule=x['rule'],history=key,exact_ticks=bool(equal)))
        if not equal:raise ValueError('Sequential recurrence differs')
write(p/'sequential_verification.json',dict(verified_utc=utc(),checks=checks))
