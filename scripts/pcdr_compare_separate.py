"""Compare verified separate-connection results with the prior late-pair study."""
import argparse
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_review_pathway import digest, require


def compare(archive, previous, review, previous_review):
    for path, evidence in [(archive, review), (previous, previous_review)]:
        require(evidence['checks_passed'] is True, 'Archive lacks a successful review')
        require(digest(path.read_bytes()) == evidence['archive_sha256'], 'Archive differs from reviewed bytes')
    with zipfile.ZipFile(archive) as z, zipfile.ZipFile(previous) as old:
        frame = lambda source, name: pd.read_parquet(io.BytesIO(source.read(name)))
        repeated = []
        for dt in [.0004, .0002]:
            for condition in ['late_reference', 'late_edges']:
                trial = f'{condition}_{dt}'
                for name in ['spikes.parquet', 'scheduled_events.parquet', 'delivered_events.parquet']:
                    pd.testing.assert_frame_equal(frame(z, trial+'/'+name), frame(old, trial+'/'+name),
                                                  check_dtype=False, check_exact=True)
                require(json.loads(z.read(trial+'/endpoints.json')) ==
                        json.loads(old.read(trial+'/endpoints.json')), 'Repeated endpoints differ: '+trial)
                repeated.append(dict(trial=trial, exact_spikes=True, exact_inputs=True, exact_endpoints=True))
        plan = json.loads(z.read('diagnostic_plan.json'))
        windows, singles = [], []
        for dt in [.0004, .0002]:
            events = {}
            for condition in ['late_reference', 'late_edges', 'late_g', 'late_h']:
                trial = f'{condition}_{dt}'
                spikes = frame(z, trial+'/spikes.parquet')
                ticks = np.rint(spikes.t.to_numpy()*1000/dt).astype(np.int64)
                all_events = pd.DataFrame({'id': spikes.flywire_id, 'tick': ticks})
                events[condition] = all_events
                noninput = all_events.loc[~all_events.id.isin(plan['input_ids'])]
                first = noninput.groupby('id').tick.min()
                lo, hi = round(730/dt), round(750/dt)
                histories = {v: (all_events.loc[all_events.id.eq(v) & (ticks >= round(600/dt)),
                                               'tick'].to_numpy()*dt).tolist()
                             for v in ['720575940628695043', '720575940629667639', '720575940623862015']}
                windows.append(dict(trial=trial,
                    noninput_spikes_730_750=int(noninput.tick.between(lo, hi-1).sum()),
                    newly_recruited_noninput_730_750=int(first.between(lo, hi-1).sum()),
                    post_switch_times_ms=histories))
            g, h = events['late_g'], events['late_h']
            different = g.merge(h, on=['id', 'tick'], how='outer', indicator=True)
            different = different.loc[different._merge.ne('both')]
            change = h.id.value_counts().subtract(g.id.value_counts(), fill_value=0)
            singles.append(dict(dt_ms=dt, identical_spike_events=different.empty,
                unmatched_spike_events=len(different), neurons_with_changed_total_count=int(change.ne(0).sum()),
                absolute_count_difference=int(change.abs().sum()),
                first_changed_spike_ms=None if different.empty else float(different.tick.min()*dt)))
        return dict(archive_sha256=review['archive_sha256'], previous_sha256=previous_review['archive_sha256'],
                    repeated_conditions=repeated, supplementary_windows=windows, single_comparisons=singles,
                    limitation='Supplementary descriptions selected after the primary review; original endpoints unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT/'CCR_separate_pathway_results.zip')
    parser.add_argument('--previous', type=Path, default=ROOT/'CCR_late_pathway_results.zip')
    parser.add_argument('--review', type=Path, default=ROOT/'docs/pcdr/evidence/2026-10-08/separate_review.json')
    parser.add_argument('--previous-review', type=Path, default=ROOT/'docs/pcdr/evidence/2026-10-07/late_review.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.archive, args.previous, json.loads(args.review.read_text()),
                     json.loads(args.previous_review.read_text()))
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))
