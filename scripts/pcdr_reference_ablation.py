"""Factorial old-reference-cap diagnostics and separately amended partner searches."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
from pathlib import Path
import argparse
import sys
import numpy as np
from scipy.optimize import linprog

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_anchor_bound import matrices, box_dual_bound
from scripts.pcdr_fullpool_relaxation import load_design
from scripts.pcdr_bounded_process import run_bounded
from eigencircuits.common import environment


def reference_groups(refs):
    original={k:v for k,v in refs.items() if k in ['motor_003','motor_004','motor_005']}
    newer={k:v for k,v in refs.items() if k.startswith('new_')}
    if len(original)!=3 or len(newer)!=12 or set(original)|set(newer)!=set(refs):
        raise ValueError('Unexpected reference inventory')
    return {'neither':{},'original_three':original,'newer_twelve':newer,'both':dict(refs)}


def worker(out):
    p=read(out/'protocol.json')
    for path,h in p['inputs'].items():
        if digest(path)!=h:raise ValueError('Changed frozen input: '+path)
    f,values,ti,_,groups,counts,scale,_=load_design()
    lookup={v:i for i,v in enumerate(f.root_id)}
    pool=np.array([lookup[v] for v in p['candidate_ids']])
    pg=[groups[i] for i in pool];results={}
    for group,refs in reference_groups(p['references']).items():
        masks=[np.isin(p['candidate_ids'],ids).astype(float) for ids in refs.values()]
        a,b,eq,rhs=matrices(values[pool],pg,counts,values[ti],scale,masks)
        for anchor,ids in p['anchors'].items():
            key=anchor+'__'+group
            c=np.isin(p['candidate_ids'],ids).astype(float)
            r=linprog(c,A_ub=a,b_ub=b,A_eq=eq,b_eq=rhs,bounds=(0,1),method='highs',options={'time_limit':10})
            record=dict(status=int(r.status),message=r.message)
            if r.success:
                violation=max(0,float((a@r.x-b).max()),float(np.abs(eq@r.x-rhs).max()),float((-r.x).max()),float((r.x-1).max()))
                if violation>1e-7:raise ValueError('Primal constraint violation')
                bound=box_dual_bound(c,a,b,eq,rhs,r.ineqlin.marginals,r.eqlin.marginals)
                if bound['raw_lower_bound']>float(c@r.x)+1e-7:raise ValueError('Bound ordering failed')
                np.savez(out/(key+'.npz'),weights=r.x,c=c,a=a,b=b,eq=eq,rhs=rhs)
                record.update(primal_objective=float(c@r.x),primal_violation=violation,certificate=bound)
            results[key]=record
            write(out/'lp_results.json',dict(cases=results,environment=environment(),updated_utc=utc()))


def run(out):
    source=ROOT/'results/pcdr/anchor_family_20261008'
    p=read(source/'anchor_538/protocol.json')
    inputs=dict(p['inputs'])
    for path in [Path(__file__),ROOT/'scripts/pcdr_anchor_bound.py',source/'summary.json']:
        inputs[str(path)]=digest(path)
    anchors={}
    for name in ['anchor_538','anchor_999']:
        path=source/name/'protocol.json';inputs[str(path)]=digest(path)
        anchors[name]=read(path)['references']['fixed_anchor']
    for path,h in inputs.items():
        if digest(path)!=h:raise ValueError('Changed source input: '+path)
    refs={k:v for k,v in p['references'].items() if k!='fixed_anchor'}
    reference_groups(refs)
    out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs=inputs,candidate_ids=p['candidate_ids'],references=refs,anchors=anchors,
        question='Which old-reference group obstructs fixed-anchor diversity, and can the weaker mutual-only design produce partners?',
        diagnostic='Complete 2x2 factorial retention of original-three and newer-twelve reference caps, for each of two fixed anchors: eight fractional minimum-overlap problems. Retain pool, exact strata, exclusions and sufficient mean bounds; no CDF rows.',
        amendment='Two companion CDF searches retain only the fixed-anchor overlap cap of thirty. Drop all old-reference caps explicitly; these cannot solve the stronger earlier problem. Use both anchors regardless of diagnostic outcomes.',
        budget='Eight LPs at ten seconds each within one one-hundred-second external worker, followed by two serial sixty-second MILPs with one-hundred-second external deadlines each. No retries, threshold tuning, pool expansion or simulation.',
        interpretation='Fractional feasibility is not an integer witness. Valid lower bounds can exclude a cap only in their declared regime. Verified partners show conditional feasibility of the amended design, not global optimality or biological specificity.'))
    # Both companion protocols precede the diagnostic and either integer solve.
    for anchor,ids in anchors.items():
        case=out/anchor;(case/'cap_30').mkdir(parents=True)
        write(case/'protocol.json',dict(recorded_utc=utc(),inputs=inputs,candidate_ids=p['candidate_ids'],
            references={'fixed_anchor':ids},solves=['cap_30'],
            purpose='Explicit mutual-only amendment: minimize companion CDF gap with one fixed-anchor cap; old-reference caps removed.'))
    process=run_bounded([sys.executable,str(Path(__file__).resolve()),'--out',str(out),'--worker'],out/'lp_logs',100,cwd=ROOT)
    write(out/'lp_process.json',process);print('LP diagnostics',process,flush=True)
    for anchor in anchors:
        case=out/anchor
        process=run_bounded([sys.executable,str(ROOT/'scripts/pcdr_distribution_match.py'),'--out',str(case),'--worker','cap_30'],case/'cap_30/logs',100,cwd=ROOT)
        write(case/'cap_30/process.json',process);print(anchor,process,flush=True)
    write(out/'execution.json',dict(completed_utc=utc(),lp_process=read(out/'lp_process.json'),
        partner_processes={a:read(out/a/'cap_30/process.json') for a in anchors}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.worker:worker(args.out)
    else:run(args.out)
