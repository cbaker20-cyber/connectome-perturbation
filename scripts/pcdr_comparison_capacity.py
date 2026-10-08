"""Bound overlap forced by the existing comparison strata, without fitting outcomes."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_fullpool_relaxation import load_design, FEATURES, SELECTION
from scripts.pcdr_ccr_transfer import read, write, digest
from eigencircuits.common import environment, now


def overlap_bounds(pool_size, required, reference_size):
    if any(type(v) is not int for v in [pool_size, required, reference_size]):
        raise ValueError('Counts must be integers')
    if not 0 <= required <= pool_size or not 0 <= reference_size <= pool_size:
        raise ValueError('Impossible stratum counts')
    return dict(minimum_with_reference=max(0, required-(pool_size-reference_size)),
                minimum_between_two_sets=max(0, 2*required-pool_size))


def run(plan_path, evidence, out):
    if digest(plan_path) != read(evidence/'full_check.json')['plan_sha256']:
        raise ValueError('Changed fine-study plan')
    out.mkdir(parents=True, exist_ok=False)
    write(out/'protocol.json', dict(recorded_utc=now(),
        question='How much overlap is forced by exact sign/recruitment/motor counts alone?',
        method='For pool N, required k and reference membership r: max(0,k-(N-r)); between any two size-k subsets: max(0,2k-N). Sum across disjoint strata.',
        limitation='Ignoring six-feature balance enlarges the feasible set. These are lower bounds on required overlap, not proofs that balanced low-overlap sets exist.',
        no_new_sets=True, no_simulation=True, no_outcome_file_loaded=True,
        plan_sha256=digest(plan_path), script_sha256=digest(Path(__file__))))
    f, _, _, pool, groups, counts, _, _ = load_design()
    plan = read(plan_path)
    conditions = ['motor_003', 'motor_004', 'motor_005']
    references = {}
    for condition in conditions:
        jobs = [j for j in plan['jobs'] if j['stage'] == 'fine' and j['variant'] == 'default' and j['condition'] == condition]
        members = [frozenset(j['lesion_ids']) for j in jobs]
        if not members or len(set(members)) != 1 or len(members[0]) != 51:
            raise ValueError('Inconsistent comparison memberships')
        references[condition] = members[0]
    eligible_ids = set(f.iloc[pool].root_id)
    if any(not v <= eligible_ids for v in references.values()):
        raise ValueError('Comparison contains an ineligible cell')
    rows = []
    forced = []
    for group, required in sorted(counts.items()):
        members = {str(f.iloc[i].root_id) for i in pool if groups[i] == group}
        if len(members) == required:
            forced.extend(sorted(members))
        row = dict(model_sign=group[0], recruited=bool(group[1]), motor=bool(group[2]),
                   pool_size=len(members), required=required, comparisons={})
        for condition, reference in references.items():
            r = len(members & reference)
            if r != required:
                raise ValueError('Comparison violates original stratum counts')
            row['comparisons'][condition] = overlap_bounds(len(members), required, r)
        rows.append(row)
    write(out/'complete.json', dict(status='complete', eligible_count=len(pool), strata=rows,
        forced_ids_from_exhausted_strata=forced,
        lower_bound_with_each_comparison={c:sum(r['comparisons'][c]['minimum_with_reference'] for r in rows) for c in conditions},
        lower_bound_between_any_two=sum(r['comparisons'][conditions[0]]['minimum_between_two_sets'] for r in rows),
        inputs={str(p):digest(p) for p in [FEATURES, SELECTION, plan_path,
            ROOT/'results/pcdr/exploratory80_20260921/controls/manifest.json', ROOT/'scripts/pcdr_fullpool_relaxation.py']},
        environment=environment(), protocol_sha256=digest(out/'protocol.json'),
        limitation='Bounds use strata only; six-feature balance and distribution matching remain untested here. No candidate set is accepted.'))
    print(read(out/'complete.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=ROOT/'results/pcdr/fine_download_20261005/plan.json')
    parser.add_argument('--evidence', type=Path, default=ROOT/'results/pcdr/fine_verified_20261005')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.evidence, args.out)
