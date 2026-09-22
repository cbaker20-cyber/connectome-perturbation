"""Post-result audit of repeated outputs; no new trials or altered primary analysis."""
from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, sha256


def main():
    study = ROOT/'results/pcdr/motor_composition_pilot_20260922'
    out = study/'response_duplicates'
    out.mkdir(exist_ok=False)
    paths = [study/'jobs.json', study/'completion_audit.json', study/'analysis/results.json', Path(__file__)]
    atomic_json(out/'protocol.json', {
        'recorded_utc': now(), 'trigger': 'Completed verified results show identical summaries for three groups of comparisons.',
        'purpose': 'Post-result diagnostic: distinguish repeated trajectories from merely equal aggregate readouts. Not a prespecified test.',
        'method': 'Group conditions by the ordered tuple of five spike digests. Within each group verify complete spike tables and all-neuron rate tables equal for each seed; compare support identities; inspect rates of cells whose membership varies, in baseline and all group lesions.',
        'limits': 'No reclassification, exclusion or extra simulation. Silence/equality applies only to these five seeds and this model condition.',
        'hashes': {str(p.relative_to(ROOT)): sha256(p) for p in paths}})
    plan = json.loads((study/'jobs.json').read_text())
    audit = json.loads((study/'completion_audit.json').read_text())
    for rel, digest in audit['source_manifests'].items():
        assert sha256(study/rel) == digest
    conditions = {c['name']: set(c['ids']) for c in plan['conditions'] if c['name'].startswith('motor_')}
    groups = defaultdict(list)
    for name in conditions:
        signature = tuple(json.loads((study/'trials'/f'default_{name}_{seed}'/'manifest.json').read_text())['spike_digest'] for seed in plan['seeds'])
        groups[signature].append(name)
    records, counts = [], []
    for _, names in groups.items():
        union, shared = set.union(*(conditions[name] for name in names)), set.intersection(*(conditions[name] for name in names))
        varying = sorted(union-shared)
        for seed in plan['seeds']:
            reference = None
            reference_spikes = None
            for name in ['baseline']+names:
                directory = study/'trials'/f'default_{name}_{seed}'
                m = json.loads((directory/'manifest.json').read_text())
                assert sha256(directory/'rates.parquet') == m['outputs']['rates.parquet']
                assert sha256(directory/'spikes.parquet') == m['outputs']['spikes.parquet']
                rates = pd.read_parquet(directory/'rates.parquet').set_index('root_id').sort_index()
                assert rates.index.is_unique
                for rid in varying:
                    counts.append({'group': names[0], 'condition': name, 'seed': seed, 'root_id': rid,
                                   'rate_hz': float(rates.loc[rid, 'rate_hz']), 'spike_count': int(rates.loc[rid, 'spike_count'])})
                if name == 'baseline':
                    continue
                spikes = pd.read_parquet(directory/'spikes.parquet')[['t', 'flywire_id']].reset_index(drop=True)
                if reference is not None:
                    pd.testing.assert_frame_equal(rates, reference)
                    pd.testing.assert_frame_equal(spikes, reference_spikes)
                reference, reference_spikes = rates, spikes
        local_counts = [r for r in counts if r['group'] == names[0]]
        records.append({'conditions': names, 'varying_membership_ids': varying, 'shared_cells_within_group': len(shared),
                        'exact_spike_and_rate_equality_all_five_seeds': True,
                        'varying_cells_all_silent_baseline_and_group_lesions': all(r['spike_count'] == 0 for r in local_counts)})
    pd.DataFrame(counts).to_csv(out/'varying_cell_rates.csv', index=False)
    atomic_json(out/'summary.json', {'completed_utc': now(), 'distinct_membership_sets': len(conditions),
                'distinct_five_seed_spike_trajectories': len(groups), 'groups': records,
                'claim': 'Observed trajectory duplication only; no claim of equivalence in new seeds, input contexts or model variants.',
                'outputs': {p.name: sha256(p) for p in out.iterdir() if p.is_file()}})
    print((out/'summary.json').read_text())


if __name__ == '__main__':
    main()
