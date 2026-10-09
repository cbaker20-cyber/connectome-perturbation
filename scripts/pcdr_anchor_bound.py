"""Numerically check overlap lower bounds for the two fixed anchors."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
from pathlib import Path
import argparse
import sys
import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_fullpool_relaxation import load_design
from scripts.pcdr_bounded_process import run_bounded
from eigencircuits.common import environment


def box_dual_bound(c, a, b, eq, rhs, y, z):
    c,a,b,eq,rhs,y,z = [np.asarray(v,float) for v in (c,a,b,eq,rhs,y,z)]
    if c.ndim != 1 or a.shape != (len(b),len(c)) or eq.shape != (len(rhs),len(c)) or y.shape != b.shape or z.shape != rhs.shape:
        raise ValueError('Invalid certificate dimensions')
    if not all(np.isfinite(v).all() for v in [c,a,b,eq,rhs,y,z]):
        raise ValueError('Nonfinite certificate')
    # Any nonpositive inequality multipliers give a lower bound after exact
    # minimization of the residual linear expression over the unit box.
    y = np.minimum(y,0)
    residual = c-a.T@y-eq.T@z
    raw = float(b@y+rhs@z+np.minimum(residual,0).sum())
    magnitude = float(np.abs(b*y).sum()+np.abs(rhs*z).sum()+np.abs(c).sum()
                      +(np.abs(a).T@np.abs(y)).sum()+(np.abs(eq).T@np.abs(z)).sum())
    guard = 1e-9*(1+magnitude)
    return dict(raw_lower_bound=raw, floating_guard=guard, guarded_lower_bound=raw-guard,
                inequality_multipliers=y.tolist(), equality_multipliers=z.tolist())


def matrices(values,groups,counts,target,scale,refs):
    n = len(target)
    tolerance = .099*np.sqrt(target.var(axis=0)/2)
    means = values.T/n/scale[:,None]
    a = np.vstack([means,-means,*[np.asarray(r)[None,:] for r in refs]])
    b = np.r_[(target.mean(axis=0)+tolerance)/scale,
              -(target.mean(axis=0)-tolerance)/scale,np.full(len(refs),30.)]
    keys = sorted(counts)
    eq = np.array([[g==k for g in groups] for k in keys],float)
    rhs = np.array([counts[k] for k in keys],float)
    return a,b,eq,rhs


def worker(out):
    p = read(out/'protocol.json')
    for path,h in p['inputs'].items():
        if digest(path)!=h: raise ValueError('Changed frozen input: '+path)
    source = Path(p['anchor_study'])
    first = read(source/'anchor_538/protocol.json')
    f,values,ti,_,groups,counts,scale,_ = load_design()
    lookup = {v:i for i,v in enumerate(f.root_id)}
    pool = np.array([lookup[v] for v in first['candidate_ids']])
    refs = [np.isin(first['candidate_ids'],ids).astype(float) for name,ids in first['references'].items() if name!='fixed_anchor']
    a,b,eq,rhs = matrices(values[pool],[groups[i] for i in pool],counts,values[ti],scale,refs)
    results = {}
    for name in ['anchor_538','anchor_999']:
        anchor = read(source/name/'protocol.json')['references']['fixed_anchor']
        c = np.isin(first['candidate_ids'],anchor).astype(float)
        r = linprog(c,A_ub=a,b_ub=b,A_eq=eq,b_eq=rhs,bounds=(0,1),method='highs',options={'time_limit':10})
        if not r.success: raise RuntimeError('Relaxation failed for '+name+': '+r.message)
        violation = max(0,float((a@r.x-b).max()),float(np.abs(eq@r.x-rhs).max()),float((-r.x).max()),float((r.x-1).max()))
        if violation>1e-7: raise ValueError('Invalid primal solution')
        bound = box_dual_bound(c,a,b,eq,rhs,r.ineqlin.marginals,r.eqlin.marginals)
        if bound['raw_lower_bound']>float(c@r.x)+1e-7: raise ValueError('Invalid bound ordering')
        np.savez(out/(name+'.npz'),weights=r.x,c=c,a=a,b=b,eq=eq,rhs=rhs)
        results[name]=dict(primal_objective=float(c@r.x),primal_maximum_violation=violation,
            certificate=bound,excludes_overlap_cap_30=bound['guarded_lower_bound']>30,
            fractional_cells=int(np.count_nonzero((r.x>1e-7)&(r.x<1-1e-7))))
    write(out/'result.json',dict(cases=results,environment=environment(),completed_utc=utc(),
        limitation='Floating-point lower bounds with an explicit guard, not formal exact-arithmetic certificates. Only fixed anchors, frozen pool, old-reference caps and sufficient mean constraints.'))


def run(source,out):
    files=[source/'protocol.json',source/'summary.json']
    for name in ['anchor_538','anchor_999']:
        files.extend([source/name/'protocol.json',source/name/'cap_30/result.json',source/name/'verification.json'])
    inputs=dict(read(source/'protocol.json')['inputs'])
    for path in files+[Path(__file__)]:inputs[str(path)]=digest(path)
    for path,h in inputs.items():
        if digest(path)!=h:raise ValueError('Changed source input: '+path)
    out.mkdir(parents=True,exist_ok=False)
    write(out/'protocol.json',dict(recorded_utc=utc(),inputs=inputs,anchor_study=str(source),
        reason='Follow up both conditional infeasibility reports with a smaller independent lower-bound problem.',
        design='Minimize overlap with each fixed anchor over fractional memberships in [0,1], retaining exact strata, sufficient mean bounds and fifteen old-reference caps. Remove CDF constraints and anchor cap. No integer lesion candidate can improve on a valid relaxation lower bound.',
        budget='Two LPs, ten seconds each inside one worker with forty-second external deadline; no retry.',
        verification='Check primal constraints and a box-minimized Lagrangian lower bound. Clip inequality multipliers nonpositive; report rounding guard and scope, do not claim formal exact proof.'))
    process=run_bounded([sys.executable,str(Path(__file__).resolve()),'--out',str(out),'--worker'],out/'logs',40,cwd=ROOT)
    write(out/'process.json',process)
    print(process)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=ROOT/'results/pcdr/anchor_family_20261008')
    parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.worker:worker(args.out)
    else:run(args.source,args.out)
