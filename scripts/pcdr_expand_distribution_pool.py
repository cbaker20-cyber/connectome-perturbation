"""Expand the frozen distribution-matching pool without changing its optimization."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
import argparse
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_fullpool_relaxation import load_design
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_bounded_process import run_bounded
from eigencircuits.common import now


def nested_pool(ids, values, target_indices, eligible, groups, scale, references, neighbors):
    if type(neighbors) is not int or neighbors < 1:
        raise ValueError('Neighbor count must be a positive integer')
    ids=np.asarray(ids)
    if len(set(ids))!=len(ids) or any(not isinstance(v,str) for v in ids):
        raise ValueError('Invalid exact neuron IDs')
    chosen={v for r in references.values() for v in r}
    if not chosen<=set(ids[eligible]):raise ValueError('Reference contains ineligible cells')
    pools={key:np.array([j for j in eligible if groups[j]==key]) for key in {groups[i] for i in target_indices}}
    for i in target_indices:
        pool=pools[groups[i]]
        distance=np.square((values[pool]-values[i])/scale).sum(axis=1)
        order=np.lexsort((ids[pool],distance))
        chosen.update(ids[pool[order[:neighbors]]])
    return sorted(chosen)


def run(previous,out):
    protocol=read(previous/'protocol.json')
    verification=read(previous/'verification.json')
    if verification['status']!='verified':raise ValueError('Prior study not verified')
    for name,h in {**protocol['inputs'],**verification['inputs']}.items():
        if digest(name)!=h:raise ValueError('Changed prior evidence: '+name)
    f,values,ti,eligible,groups,_,scale,_=load_design()
    references=protocol['references']
    old=nested_pool(f.root_id.to_numpy(),values,ti,eligible,groups,scale,references,20)
    if old!=protocol['candidate_ids']:raise ValueError('Original 20-neighbor pool does not reconstruct')
    expanded=nested_pool(f.root_id.to_numpy(),values,ti,eligible,groups,scale,references,50)
    if not set(old)<set(expanded):raise ValueError('Pool did not strictly expand')
    out.mkdir(parents=True,exist_ok=False)
    inputs={**protocol['inputs'],str(Path(__file__)):digest(Path(__file__)),
            str(previous/'protocol.json'):digest(previous/'protocol.json'),
            str(previous/'verification.json'):digest(previous/'verification.json')}
    write(out/'protocol.json',dict(recorded_utc=now(),
        purpose='Test sensitivity to restricted candidate pool; preserve the prior objective, constraints, reference memberships and time budgets.',
        pool_rule='Same union and distance/tie rules as the verified original pool; increase from 20 to 50 nearest eligible cells per target within exact strata. Include no new outcome-selected references.',
        neighbors_per_target=50,candidate_ids=expanded,references=references,
        previous_study=str(previous),previous_pool_size=len(old),
        previous_pool_subset=True,solves=protocol['solves'],overlap_rule=protocol['overlap_rule'],
        budget='Two serial workers using unchanged optimizer: 60 seconds internal, 100 seconds external each. No retries, further expansion or changed cap.',
        limitations=protocol['limitations'],incumbent_rule=protocol['incumbent_rule'],inputs=inputs))
    print('Expanded pool:',len(old),'to',len(expanded),flush=True)
    worker=ROOT/'scripts/pcdr_distribution_match.py'
    for kind in protocol['solves']:
        dest=out/kind;dest.mkdir()
        process=run_bounded([sys.executable,str(worker),'--out',str(out),'--worker',kind],dest/'logs',100,cwd=ROOT)
        write(dest/'process.json',process)
        print(kind,process,flush=True)
    write(out/'execution.json',dict(finished_utc=now(),workers={k:read(out/k/'process.json') for k in protocol['solves']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,default=ROOT/'results/pcdr/distribution_match_20261008')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();run(args.previous,args.out)
