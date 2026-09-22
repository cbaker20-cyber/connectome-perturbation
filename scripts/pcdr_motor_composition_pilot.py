"""Freeze and run a bounded descriptive pilot of all nine motor-balanced witnesses."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import time
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, provenance, read_json, sha256, sugar_ids
from eigencircuits.controls import FULL_FEATURES, standardized_difference
from scripts import pcdr_optimized_pilot as controller
from scripts.pcdr_motor_set_audit import OUT as AUDIT, FEATURES, SELECTION, COMPLETION

STUDY = ROOT/'results/pcdr/motor_composition_pilot_20260922'
SEEDS = list(range(631201, 631206))


def prepare():
    audit = read_json(AUDIT/'summary.json')
    for name, digest in audit['outputs'].items():
        assert sha256(AUDIT/name) == digest, name
    validation = read_json(COMPLETION/'verification.json')
    for rel, digest in validation['evidence_hashes'].items():
        assert sha256(COMPLETION.parent/rel) == digest, rel
    for rel, digest in read_json(AUDIT/'protocol.json')['hashes'].items():
        assert sha256(ROOT/rel) == digest, rel
    assert not any(read_json(p).get('seed') in SEEDS for p in (ROOT/'results/pcdr').glob('*/trials/*/manifest.json'))
    old = read_json(ROOT/'results/pcdr/seed_replication_20260921/jobs.json')
    actual = provenance()
    for key in ['inputs', 'sources']:
        assert old['provenance'][key] == actual[key], key
    assert actual['environment']['packages'] == old['provenance']['environment']['packages']
    f = pd.read_parquet(FEATURES).set_index('root_id')
    f.index = f.index.astype(str)
    ids = read_json(SELECTION)['root_ids']
    target = f.loc[ids]
    def strata(frame):
        return Counter(zip(frame.model_sign.astype(str), frame.recruited.astype(bool), frame.super_class.eq('motor')))
    conditions = [{'name': 'baseline', 'ids': [], 'role': 'baseline'},
                  {'name': 'mode', 'ids': ids, 'role': 'mode'}]
    seen = set()
    for number, group in pd.read_parquet(COMPLETION/'members.parquet').groupby('assignment'):
        chosen = group.root_id.astype(str).tolist()
        assert len(chosen) == len(set(chosen)) == 51
        assert not set(chosen) & (set(ids) | set(sugar_ids()))
        assert strata(f.loc[chosen]) == strata(target)
        balance = standardized_difference(np.log1p(target[FULL_FEATURES].to_numpy(float)),
                                          np.log1p(f.loc[chosen, FULL_FEATURES].to_numpy(float)))
        assert np.all(balance <= .1)
        assert tuple(sorted(chosen)) not in seen
        seen.add(tuple(sorted(chosen)))
        conditions.append({'name': f'motor_{int(number):03}', 'ids': chosen, 'role': 'optimized_motor_comparison'})
    assert len(conditions) == 11
    times = [read_json(p)['wall_seconds'] for p in (ROOT/'results/pcdr/seed_replication_20260921/trials').glob('*/manifest.json')]
    STUDY.mkdir(exist_ok=False)
    deadline = time.time()+30*60
    source_paths = [Path(__file__), Path(controller.__file__), ROOT/'scripts/pcdr_local_queue.py',
                    ROOT/'scripts/pcdr_verify_motor_pilot.py', FEATURES, SELECTION,
                    COMPLETION/'members.parquet', COMPLETION/'verification.json', AUDIT/'summary.json', AUDIT/'protocol.json']
    amendment = {
        'recorded_utc': now(), 'authorization_context': 'User requested continued research and local tests. This continuation selects a bounded descriptive follow-up, not a confirmatory study or cluster dispatch.',
        'question': 'Does the previously selected eigen-set retain larger A and F than each of the nine fixed motor-count-balanced optimized comparison sets under five fresh input seeds?',
        'scope': 'Conditional descriptive composition sensitivity. Does not isolate a causal effect of motor count or establish superiority over a random reference ensemble.',
        'selection': 'All nine independently verified assignments 3 through 11 retained. Exact original eigen-support. No rematching, favorable subset, mode substitution or altered thresholds.',
        'audit_objections': 'Degree variance up to 19.117 times target despite pooled SMD<=0.1; ECDF gap up to .294118; all nine share47cells; MN9 identity and detailed cell types unmatched. These limitations are known before new outcomes.',
        'seeds': SEEDS, 'trials': 55, 'deadline_epoch': deadline,
        'budget': '30 minutes maximum from preparation, one serial NumPy worker, BLAS1, existing >=4GiB free RAM and >=10GiB free disk guards. Stop on deadline, STOP or failure. No automatic extension.',
        'estimates_minutes': {'median_trial_times55': float(np.median(times)*55/60), 'p95_trial_times55': float(np.quantile(times,.95)*55/60)},
        'model': 'Unchanged v630 LIF, one second, dt .1ms, 21 sugar inputs at150Hz, fixed_binomial_tape_v1, output-only lesions; matching scheduled inputs required. Delivered inputs can vary by state.',
        'primary_description': 'For every set average signed paired per-neuron changes over all five seeds first; then A=mean absolute response inside own support and F=inside share of whole-model absolute response. Show both, and each mode-minus-comparator difference. Do not average single-seed A/F in place of these estimands.',
        'uncertainty': 'Existing per-set 2000 paired-seed bootstrap(seed630700). Added mode-minus-comparator percentile intervals use2000 shared multinomial whole-seed resamples(seed631250); same resampled seeds for mode and comparator. No p-values, no reference ranking significance, no population generalization. Five seeds are exploratory; sets/neurons are not independent replicates. Undefined F stays undefined.',
        'secondary': 'MN9 and total/per-neuron motor DeltaHz; off-support absolute response; all50 per-seed paired summaries. All ten full mean footprints and all sets reported regardless of ordering.',
        'completion': 'No complete-study conclusions until55/55 trials,50 paired inputs, source/output hashes and all ten full footprints independently checked. Incomplete study stays incomplete.',
        'source_hashes': {str(p.relative_to(ROOT)): sha256(p) for p in source_paths}}
    atomic_json(STUDY/'amendment.json', amendment)
    variant = {'name': 'default', 'weight_scale': 1., 'inhibitory_scale': 1., 'strong_fraction': None}
    jobs = []
    for seed in SEEDS:
        for c in conditions:
            jobs.append({'index': len(jobs), 'condition': c['name'], 'role': c['role'], 'lesion_ids': c['ids'],
                         'seed': seed, 'variant': variant, 'trial_id': f"default_{c['name']}_{seed}"})
    plan = {**old, 'phase': 'motor_composition_pilot', 'claim_status': 'descriptive_fixed_optimized_sets',
            'created_utc': now(), 'jobs': jobs, 'conditions': conditions, 'seeds': SEEDS, 'n_jobs': 55,
            'variants': [variant], 'amendment_sha256': sha256(STUDY/'amendment.json'),
            'provenance': actual, 'status': 'prepared_not_submitted'}
    atomic_json(STUDY/'jobs.json', plan)
    atomic_json(STUDY/'local_status.json', {'started_utc': now(), 'deadline_epoch': deadline, 'status': 'starting', 'completed': 0, 'total': 55})
    print(json.dumps({'prepared': 55, 'seeds': SEEDS, 'estimates_minutes': amendment['estimates_minutes'], 'deadline_epoch': deadline}))


def run():
    amendment = read_json(STUDY/'amendment.json')
    assert sha256(STUDY/'amendment.json') == read_json(STUDY/'jobs.json')['amendment_sha256']
    for rel, digest in amendment['source_hashes'].items():
        assert sha256(ROOT/rel) == digest, rel
    controller.STUDY = STUDY
    controller.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    prepare() if parser.parse_args().prepare else run()
