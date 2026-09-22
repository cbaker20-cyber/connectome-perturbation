"""Check all motor-composition trials and shared-seed descriptive contrasts."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import now, sha256, atomic_json, MN9

STUDY = ROOT/'results/pcdr/motor_composition_pilot_20260922'


def contrast_interval(mode_delta, other_delta, mode_support, other_support, seed=631250, n=2000):
    if mode_delta.shape != other_delta.shape or len(mode_delta) < 2:
        raise ValueError('Paired delta arrays differ or too few seeds')
    active = np.any((mode_delta != 0) | (other_delta != 0), axis=0)
    active_ids = np.flatnonzero(active)
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(mode_delta), np.full(len(mode_delta), 1/len(mode_delta)), size=n)/len(mode_delta)
    scores = []
    for delta, support in [(mode_delta, mode_support), (other_delta, other_support)]:
        means = abs(weights @ delta[:, active])
        inside = means[:, np.isin(active_ids, support)].sum(1)
        total = means.sum(1)
        scores.append((inside/len(support), np.divide(inside, total, out=np.full(n, np.nan), where=total > 0)))
    a = scores[0][0]-scores[1][0]
    f = scores[0][1]-scores[1][1]
    valid = np.isfinite(f)
    return {'A_difference_95pct': np.quantile(a, [.025, .975]).tolist(),
            'F_difference_95pct': np.quantile(f[valid], [.025, .975]).tolist() if valid.any() else None,
            'undefined_F_resamples': int((~valid).sum()), 'resamples': n, 'seed': seed}


def main():
    plan = json.loads((STUDY/'jobs.json').read_text())
    summary = json.loads((STUDY/'summary.json').read_text())
    amendment = json.loads((STUDY/'amendment.json').read_text())
    assert sha256(STUDY/'amendment.json') == plan['amendment_sha256']
    assert len(plan['jobs']) == plan['n_jobs'] == 55 and len(plan['seeds']) == 5
    assert summary['primary'] == [] and summary['status'] == 'complete'
    assert summary['jobs_sha256'] == sha256(STUDY/'jobs.json')
    for rel, digest in amendment['source_hashes'].items():
        assert sha256(ROOT/rel) == digest, rel
    assert not (STUDY/'analysis/secondary_tests.parquet').exists()
    assert not (STUDY/'pilot_comparison.json').exists()
    features = pd.read_parquet(ROOT/'results/pcdr/corrected_20260919/analysis/features.parquet').set_index('root_id')
    features.index = features.index.astype(str)
    ids = features.index.tolist()
    motor = features.index[features.super_class == 'motor'].tolist()
    lookup = {rid: i for i, rid in enumerate(ids)}
    conditions = {c['name']: c for c in plan['conditions']}
    results = json.loads((STUDY/'analysis/results.json').read_text())
    assert len(results) == 10 and {r['condition'] for r in results} == set(conditions)-{'baseline'}
    rates, manifests, source_hashes = {}, {}, {}
    for job in plan['jobs']:
        directory = STUDY/'trials'/job['trial_id']
        m = json.loads((directory/'manifest.json').read_text())
        assert m['status'] == 'complete' and m['seed'] == job['seed'] and m['trial_id'] == job['trial_id']
        assert sorted(m['lesion_ids']) == sorted(job['lesion_ids'])
        for key in ['inputs', 'sources']:
            assert m['provenance'][key] == plan['provenance'][key]
        for key in ['weight_scale', 'inhibitory_scale', 'strong_fraction']:
            assert m[key] == job['variant'][key]
        assert m['backend'] == 'numpy' and m['input_protocol'] == 'fixed_binomial_tape_v1'
        assert m['duration_s'] == 1 and m['dt_ms'] == .1 and m['input_hz'] == 150
        for name, digest in m['outputs'].items():
            assert sha256(directory/name) == digest, name
        r = pd.read_parquet(directory/'rates.parquet').set_index('root_id')
        r.index = r.index.astype(str)
        assert r.index.is_unique and set(r.index) == set(ids) and len(r) == 127400
        rates[(job['condition'], job['seed'])] = r.reindex(ids).rate_hz
        manifests[(job['condition'], job['seed'])] = m
        source_hashes[str((directory/'manifest.json').relative_to(STUDY))] = sha256(directory/'manifest.json')
    rows, checks, deltas = [], [], {}
    paired = delivered = 0
    for result in results:
        condition = result['condition']
        support = result['support_ids']
        assert sorted(support) == sorted(conditions[condition]['ids'])
        assert result['seeds'] == plan['seeds'] and result['n_pairs'] == 5
        ds = []
        for seed in plan['seeds']:
            a, b = manifests[('baseline', seed)], manifests[(condition, seed)]
            for key in ['input_digest', 'input_protocol', 'duration_s', 'dt_ms', 'context', 'input_hz', 'weight_scale', 'inhibitory_scale', 'strong_fraction', 'backend']:
                assert a[key] == b[key], key
            paired += 1
            delivered += int(a['delivered_input_digest'] == b['delivered_input_digest'])
            delta = rates[(condition, seed)]-rates[('baseline', seed)]
            assert np.isfinite(delta.to_numpy()).all()
            ds.append(delta.to_numpy())
            inside, total = float(abs(delta.loc[support]).sum()), float(abs(delta).sum())
            rows.append({'condition': condition, 'seed': seed, 'A_single_seed': inside/len(support),
                         'F_single_seed': inside/total if total else None, 'MN9_delta_hz': float(delta.loc[MN9]),
                         'motor_total_delta_hz': float(delta.loc[motor].sum())})
        deltas[condition] = np.asarray(ds)
        mean = pd.Series(np.mean(ds, axis=0), index=ids)
        inside, total = float(abs(mean.loc[support]).sum()), float(abs(mean).sum())
        expected = {'A': inside/len(support), 'F': inside/total if total else None,
                    'mn9_delta_hz': float(mean.loc[MN9]), 'motor_total_delta_hz': float(mean.loc[motor].sum()),
                    'motor_mean_delta_hz': float(mean.loc[motor].mean()), 'off_absolute_sum_hz': total-inside}
        for key, value in expected.items():
            if value is None:
                assert result[key] is None
            else:
                np.testing.assert_allclose(result[key], value, rtol=1e-12, atol=1e-10)
        path = STUDY/'analysis/default'/condition/'footprint.parquet'
        footprint = pd.read_parquet(path).set_index('root_id')
        assert footprint.index.is_unique and set(footprint.index) == set(ids)
        np.testing.assert_allclose(footprint.reindex(ids).delta_hz, mean, rtol=1e-12, atol=1e-10)
        checks.append({'condition': condition, 'footprint_sha256': sha256(path),
                       'motor_cells': len(set(support) & set(motor)), 'mn9_in_support': MN9 in support})
    mode = next(r for r in results if r['condition'] == 'mode')
    contrasts = []
    for other in results:
        if other['condition'] == 'mode':
            continue
        contrasts.append({'comparison': other['condition'], 'A_difference': mode['A']-other['A'],
                          'F_difference': mode['F']-other['F'] if mode['F'] is not None and other['F'] is not None else None,
                          **contrast_interval(deltas['mode'], deltas[other['condition']],
                                              [lookup[x] for x in mode['support_ids']], [lookup[x] for x in other['support_ids']])})
    atomic_json(STUDY/'paired_contrasts.json', contrasts)
    pd.DataFrame(rows).to_csv(STUDY/'per_seed_readouts.csv', index=False)
    atomic_json(STUDY/'completion_audit.json', {'checked_utc': now(), 'trials_verified': 55,
                'scheduled_input_pairs_verified': paired, 'delivered_input_pairs_equal': delivered,
                'lesion_summaries_and_full_footprints_verified': len(checks), 'checks': checks,
                'source_manifests': source_hashes, 'reference_p_values': 'absent',
                'verifier_sha256': sha256(Path(__file__)),
                'analysis_hashes': {str(p.relative_to(STUDY)): sha256(p) for p in [STUDY/'analysis/results.json', STUDY/'summary.json', STUDY/'paired_contrasts.json', STUDY/'per_seed_readouts.csv']}})
    print(json.dumps({'verified': 55, 'paired': paired, 'delivered_equal': delivered, 'results': [
        {k: r[k] for k in ['condition', 'A', 'F', 'mn9_delta_hz', 'motor_total_delta_hz']} for r in results], 'contrasts': contrasts}))


if __name__ == '__main__':
    main()
