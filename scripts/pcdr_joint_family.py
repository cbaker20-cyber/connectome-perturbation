"""Choose two comparison sets together under a declared pairwise overlap cap."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
from pathlib import Path
import argparse
import sys
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from scripts.pcdr_fullpool_relaxation import load_design
from scripts.pcdr_distribution_match import validate
from scripts.pcdr_bounded_process import run_bounded
from eigencircuits.common import environment


def solve_pair(values, groups, counts, target, scale, references, cap, seconds=60):
    values, target, scale = np.asarray(values, float), np.asarray(target, float), np.asarray(scale, float)
    if values.ndim != 2 or target.ndim != 2 or not len(values) or not len(target) or values.shape[1] != target.shape[1]:
        raise ValueError('Invalid feature dimensions')
    m, n = len(values), len(target)
    if not np.isfinite(values).all() or not np.isfinite(target).all() or not np.isfinite(scale).all() or scale.shape != (values.shape[1],) or np.any(scale <= 0):
        raise ValueError('Invalid feature values or scale')
    if len(groups) != m or sum(counts.values()) != n or any(type(v) is not int or v < 0 for v in counts.values()) or set(groups) - set(counts):
        raise ValueError('Invalid strata')
    if type(cap) is not int or not 0 <= cap <= n or seconds <= 0:
        raise ValueError('Invalid cap or budget')
    references = [np.asarray(r) for r in references]
    if any(r.shape != (m,) or not np.isin(r, [0, 1]).all() for r in references):
        raise ValueError('Invalid reference masks')
    row_ids, col_ids, data, lower, upper = [], [], [], [], []
    def add(cols, vals, lo, hi):
        cols, vals = np.asarray(cols), np.asarray(vals, float)
        keep = vals != 0
        col_ids.append(cols[keep]); data.append(vals[keep])
        row_ids.append(np.full(int(keep.sum()), len(lower), dtype=np.int32))
        lower.append(lo); upper.append(hi)
    t = 3*m
    tolerance = .099*np.sqrt(target.var(axis=0)/2)
    for k in range(2):
        cols = np.arange(m) + k*m
        for group, count in sorted(counts.items()):
            add(cols, [float(g == group) for g in groups], count, count)
        for j in range(values.shape[1]):
            add(cols, values[:, j]/n/scale[j], (target[:, j].mean()-tolerance[j])/scale[j],
                (target[:, j].mean()+tolerance[j])/scale[j])
            for point in np.unique(np.r_[values[:, j], target[:, j]]):
                cdf = (target[:, j] <= point).mean()
                row = (values[:, j] <= point).astype(float)/n
                add(np.r_[cols, t], np.r_[row, -1], -np.inf, cdf)
                add(np.r_[cols, t], np.r_[-row, -1], -np.inf, -cdf)
        for reference in references:
            add(cols, reference, -np.inf, cap)
    # With binary memberships these inequalities force z_i = x_i * y_i.
    for i in range(m):
        add([i, m+i, 2*m+i], [1, 1, -1], -np.inf, 1)
        add([2*m+i, i], [1, -1], -np.inf, 0)
        add([2*m+i, m+i], [1, -1], -np.inf, 0)
    add(np.arange(2*m, 3*m), np.ones(m), -np.inf, cap)
    matrix = coo_matrix((np.concatenate(data), (np.concatenate(row_ids), np.concatenate(col_ids))),
                        shape=(len(lower), t+1)).tocsc()
    result = milp(np.r_[np.zeros(t), 1.], integrality=np.r_[np.ones(2*m), np.zeros(m+1)],
                  bounds=Bounds(np.zeros(t+1), np.ones(t+1)),
                  constraints=LinearConstraint(matrix, lower, upper),
                  options={'time_limit':seconds, 'mip_rel_gap':0.})
    return result, dict(variables=t+1, constraints=len(lower), matrix_nonzeros=matrix.nnz)


def validate_pair(weights, values, groups, counts, target, references, cap):
    m = len(values)
    weights = np.asarray(weights)
    if weights.shape != (3*m+1,) or not np.isfinite(weights).all():
        raise ValueError('Invalid joint solution')
    selected, audits = [], []
    for k in range(2):
        ids, audit = validate(np.r_[weights[k*m:(k+1)*m], weights[-1]], values, groups, counts, target, references, cap)
        selected.append(ids); audits.append(audit)
    overlap = len(set(selected[0]) & set(selected[1]))
    if overlap > cap:
        raise ValueError('Pairwise overlap failed')
    expected = np.zeros(m)
    expected[list(set(selected[0]) & set(selected[1]))] = 1
    if not np.allclose(weights[2*m:3*m], expected, rtol=0, atol=1e-6):
        raise ValueError('Intersection variables failed')
    return selected, dict(members=audits, pairwise_overlap=overlap,
                          maximum_ecdf_gap=max(a['maximum_ecdf_gap'] for a in audits))


def worker(out):
    p = read(out/'protocol.json')
    for path, h in p['inputs'].items():
        if digest(path) != h: raise ValueError('Changed frozen input: '+path)
    f, values, ti, _, groups, counts, scale, _ = load_design()
    lookup = {v:i for i,v in enumerate(f.root_id)}
    pool = np.array([lookup[v] for v in p['candidate_ids']])
    pg = [groups[i] for i in pool]
    refs = [np.isin(p['candidate_ids'], r).astype(int) for r in p['references'].values()]
    result, dimensions = solve_pair(values[pool], pg, dict(counts), values[ti], scale, refs, p['cap'])
    def finite(value):
        return None if value is None or not np.isfinite(value) else float(value)
    record = dict(solver_status=int(result.status), solver_message=result.message,
        objective=finite(result.fun), dual_bound=finite(getattr(result, 'mip_dual_bound', None)),
        mip_gap=finite(getattr(result, 'mip_gap', None)), dimensions=dimensions,
        environment=environment(), candidate_verified=False, completed_utc=utc())
    if result.x is not None:
        np.save(out/'solution.npy', result.x)
        selected, audit = validate_pair(result.x, values[pool], pg, counts, values[ti], refs, p['cap'])
        write(out/'candidate.json', dict(root_ids=[[p['candidate_ids'][i] for i in ids] for ids in selected], audit=audit))
        record['candidate_verified'] = True
    write(out/'result.json', record)


def run(out):
    previous = ROOT/'results/pcdr/distribution_expand_20261008'
    p, v = read(previous/'protocol.json'), read(previous/'verification.json')
    if v['status'] != 'verified': raise ValueError('Unverified pool study')
    for path, h in {**p['inputs'], **v['inputs']}.items():
        if digest(path) != h: raise ValueError('Changed prior evidence: '+path)
    inputs = dict(p['inputs'])
    for path in [Path(__file__), previous/'protocol.json', previous/'verification.json',
                 ROOT/'scripts/pcdr_distribution_match.py', ROOT/'scripts/pcdr_bounded_process.py']:
        inputs[str(path)] = digest(path)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'protocol.json', dict(recorded_utc=utc(), inputs=inputs, candidate_ids=p['candidate_ids'],
        references=p['references'], cap=30, family_size=2,
        question='Can jointly constructed sets improve the matching/diversity tradeoff beyond the saved family?',
        design='Two simultaneous binary 51-cell sets from the frozen 999-cell pool; same exact strata and sufficient mean bounds. Each shares at most thirty cells with each of fifteen prior references and with the other new set. Minimize worst six-feature CDF gap across both sets.',
        reason='Two is the smallest family that tests mutual diversity. Thirty preserves the earlier design contrast, not a biological acceptance standard. No new distribution cutoff.',
        budget='One worker, sixty seconds internal and one hundred seconds external. No retry, expanded pool, changed cap, or simulation.',
        outcomes='Validate any incumbent independently. A timeout without one is unresolved; solver infeasibility applies only to this restricted design. Neither a feasible pair nor an optimum establishes a random ensemble or biological specificity.'))
    process = run_bounded([sys.executable, str(Path(__file__).resolve()), '--out', str(out), '--worker'], out/'logs', 100, cwd=ROOT)
    write(out/'process.json', process)
    print(process)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker: worker(args.out)
    else: run(args.out)
