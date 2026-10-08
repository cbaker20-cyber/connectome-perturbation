"""Describe fixed-comparator ordering across the already verified fine steps."""
import argparse
from itertools import combinations, product
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest
from eigencircuits.common import environment

METRICS = ['A', 'F', 'fixed_mode_A', 'fixed_mode_F']


def coverage(frame, keys, expected):
    if frame.duplicated(keys).any():
        raise ValueError('Duplicate response key')
    if set(frame[keys].itertuples(index=False, name=None)) != set(expected):
        raise ValueError('Missing or unexpected response coverage')
    if not np.isfinite(frame[METRICS].to_numpy()).all():
        raise ValueError('Missing, undefined or nonfinite readout; inspect before ordering')
    if (frame[METRICS] < 0).any().any() or (frame[['F', 'fixed_mode_F']] > 1).any().any():
        raise ValueError('Readout outside valid range')


def contrasts(pairs, means, steps, seeds, conditions):
    if not steps or not seeds or 'mode' not in conditions or len(conditions) < 2:
        raise ValueError('Empty or incomplete design')
    if any(len(v) != len(set(v)) for v in [steps, seeds, conditions]):
        raise ValueError('Duplicate design value')
    coverage(pairs, ['dt_ms', 'condition', 'seed'], product(steps, conditions, seeds))
    coverage(means, ['dt_ms', 'condition'], product(steps, conditions))
    if not (means.n_pairs == len(seeds)).all():
        raise ValueError('Wrong mean pair count')
    # The supplied means were computed from signed neuronwise vectors before abs.
    # Averaging per-seed A or F here would silently change the original estimand.
    aggregates, paired, envelopes, shifts = [], [], [], []
    p = pairs.set_index(['dt_ms', 'condition', 'seed'])
    m = means.set_index(['dt_ms', 'condition'])
    for condition in [c for c in conditions if c != 'mode']:
        for metric in METRICS:
            for dt in steps:
                gaps = np.array([p.loc[(dt, 'mode', s), metric] - p.loc[(dt, condition, s), metric]
                                 for s in seeds])
                for seed, value in zip(seeds, gaps):
                    paired.append(dict(dt_ms=dt, comparison=condition, seed=seed, metric=metric,
                                       mode_minus_comparison=float(value)))
                aggregates.append(dict(dt_ms=dt, comparison=condition, metric=metric,
                    mode=float(m.loc[(dt, 'mode'), metric]), comparison_value=float(m.loc[(dt, condition), metric]),
                    mean_response_gap=float(m.loc[(dt, 'mode'), metric] - m.loc[(dt, condition), metric]),
                    paired_min=float(gaps.min()), paired_median=float(np.median(gaps)), paired_max=float(gaps.max()),
                    positive=int((gaps > 0).sum()), tied=int((gaps == 0).sum()), negative=int((gaps < 0).sum())))
            margins = np.array([min(p.loc[(dt, 'mode', s), metric] for dt in steps) -
                                max(p.loc[(dt, condition, s), metric] for dt in steps) for s in seeds])
            envelopes.append(dict(comparison=condition, metric=metric,
                mean_response_envelope_gap=float(min(m.loc[(dt, 'mode'), metric] for dt in steps) -
                                                 max(m.loc[(dt, condition), metric] for dt in steps)),
                paired_envelope_min=float(margins.min()), paired_envelope_median=float(np.median(margins)),
                positive=int((margins > 0).sum()), tied=int((margins == 0).sum()), negative=int((margins < 0).sum())))
            for coarse, fine in zip(steps[:-1], steps[1:]):
                gaps = [np.array([p.loc[(dt, 'mode', s), metric] - p.loc[(dt, condition, s), metric]
                                  for s in seeds]) for dt in [coarse, fine]]
                shifts.append(dict(comparison=condition, metric=metric, coarse_ms=coarse, fine_ms=fine,
                    median_absolute_gap_change=float(np.median(np.abs(gaps[1]-gaps[0]))),
                    max_absolute_gap_change=float(np.max(np.abs(gaps[1]-gaps[0]))),
                    strict_sign_reversals=int((gaps[0]*gaps[1] < 0).sum()),
                    tie_transitions=int(((gaps[0] == 0) != (gaps[1] == 0)).sum())))
    return pd.DataFrame(aggregates), pd.DataFrame(paired), pd.DataFrame(envelopes), pd.DataFrame(shifts)


def memberships(plan, steps, seeds, conditions):
    jobs = [j for j in plan['jobs'] if j['stage'] == 'fine' and j['variant'] == 'default']
    keys = [(j['dt_ms'], j['condition'], j['seed']) for j in jobs]
    expected = set(product(steps, ['baseline']+conditions, seeds))
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('Plan job coverage differs')
    sets = {}
    for j in jobs:
        ids = j['lesion_ids']
        if any(type(v) is not str or not v.isdigit() for v in ids) or len(ids) != len(set(ids)):
            raise ValueError('Invalid or duplicate exact neuron IDs')
        c, members = j['condition'], set(ids)
        if len(members) != (0 if c == 'baseline' else 51):
            raise ValueError('Unexpected membership size')
        if c in sets and sets[c] != members:
            raise ValueError('Membership changes across seed or step')
        sets[c] = members
    if sets['mode'] != set(plan['mode_ids']):
        raise ValueError('Mode membership differs')
    return [dict(first=a, second=b, shared=len(sets[a] & sets[b]),
                 union=len(sets[a] | sets[b])) for a, b in combinations(conditions, 2)]


def run(evidence, plan_path, out):
    check = read(evidence/'full_check.json')
    if check['status'] != 'complete' or digest(plan_path) != check['plan_sha256']:
        raise ValueError('Unverified study or changed plan')
    names = ['checked_pairs.csv', 'checked_means.json', 'checked_agreement.json']
    for name in names:
        if digest(evidence/name) != check['outputs'][name]:
            raise ValueError('Changed verified evidence: '+name)
    pairs, all_means = pd.read_csv(evidence/names[0]), read(evidence/names[1])
    if len(pairs) != check['pairs_reproduced'] or len(all_means) != check['mean_rows_reproduced']:
        raise ValueError('Incomplete verified tables')
    plan = read(plan_path)
    steps = plan['steps_ms']
    conditions = ['mode', 'motor_003', 'motor_004', 'motor_005']
    seeds = sorted({j['seed'] for j in plan['jobs'] if j['stage'] == 'fine' and j['variant'] == 'default'})
    if steps != [.0008, .0004, .0002, .0001] or len(seeds) != 30:
        raise ValueError('Unexpected fine study design')
    overlaps = memberships(plan, steps, seeds, conditions)
    pairs = pairs.loc[pairs.stage.eq('fine') & pairs.variant.eq('default')]
    means = pd.DataFrame([{**r, 'fixed_mode_A': r['fixed_mode']['A'], 'fixed_mode_F': r['fixed_mode']['F']}
                          for r in all_means if r['stage'] == 'fine' and r['variant'] == 'default'])
    outputs = contrasts(pairs, means, steps, seeds, conditions)
    out.mkdir(parents=True, exist_ok=False)
    for name, frame in zip(['aggregate_contrasts.csv', 'paired_contrasts.csv', 'step_envelopes.csv', 'contrast_changes.csv'], outputs):
        frame.to_csv(out/name, index=False)
    agreement = read(evidence/'checked_agreement.json')
    write(out/'complete.json', dict(status='complete', analysis='Retrospective descriptive fixed-comparator contrasts; no new acceptance criterion.',
        seeds=seeds, steps_ms=steps, memberships=overlaps,
        original_agreement_groups=len(agreement['groups']),
        original_groups_passing=sum(bool(g['meets_declared_criteria']) for g in agreement['groups']),
        original_final_decision=agreement['final_two_halvings_meet_declared_criteria'],
        archive_sha256=check['archive_sha256'],
        inputs={str(p):digest(p) for p in [plan_path, evidence/'full_check.json', *[evidence/n for n in names]]},
        script_sha256=digest(Path(__file__)), environment=environment(),
        outputs={p.name:digest(p) for p in out.iterdir()}))
    print(outputs[0].loc[outputs[0].metric.isin(['A', 'F'])].to_string(index=False))
    print(outputs[2].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT/'results/pcdr/fine_verified_20261005')
    parser.add_argument('--plan', type=Path, default=ROOT/'results/pcdr/fine_download_20261005/plan.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.evidence, args.plan, args.out)
