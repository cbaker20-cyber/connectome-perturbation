from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_fine_contrasts import contrasts, memberships


def tables():
    rows = []
    for dt, values in [(.2, {'mode': [3, 1], 'other': [1, 2]}),
                       (.1, {'mode': [2, 1], 'other': [1, 1]})]:
        for c, vals in values.items():
            for s, v in enumerate(vals):
                rows.append(dict(dt_ms=dt, condition=c, seed=s, A=float(v), F=v/10,
                                 fixed_mode_A=v, fixed_mode_F=v/10))
    means = [dict(dt_ms=d, condition=c, n_pairs=2, A=a, F=a/10,
                  fixed_mode_A=a, fixed_mode_F=a/10)
             for d in [.2, .1] for c, a in [('mode', 1.25), ('other', .75)]]
    return pd.DataFrame(rows), pd.DataFrame(means)


def test_known_contrasts_envelopes_and_ties():
    p, m = tables()
    a, paired, envelope, change = contrasts(p, m, [.2, .1], [0, 1], ['mode', 'other'])
    assert a.loc[a.metric.eq('A'), 'mean_response_gap'].tolist() == [.5, .5]
    assert paired.loc[paired.metric.eq('A'), 'mode_minus_comparison'].tolist() == [2, -1, 1, 0]
    e = envelope.loc[envelope.metric.eq('A')].iloc[0]
    assert (e.paired_envelope_min, e.paired_envelope_median, e.positive, e.negative) == (-1, 0, 1, 1)
    c = change.loc[change.metric.eq('A')].iloc[0]
    assert (c.median_absolute_gap_change, c.strict_sign_reversals, c.tie_transitions) == (1, 0, 1)
    shuffled = contrasts(p.sample(frac=1, random_state=7), m.iloc[::-1], [.2, .1], [0, 1], ['mode', 'other'])
    for x, y in zip((a, paired, envelope, change), shuffled):
        pd.testing.assert_frame_equal(x, y)


def test_strict_sign_reversal():
    p, m = tables()
    p.loc[(p.dt_ms == .1) & p.condition.eq('mode') & p.seed.eq(1), 'A'] = 2
    result = contrasts(p, m, [.2, .1], [0, 1], ['mode', 'other'])[-1]
    assert result.loc[result.metric.eq('A'), 'strict_sign_reversals'].item() == 1


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'nan', 'infinity', 'negative', 'fraction', 'mean_count', 'mean_missing'])
def test_invalid_tables(fault):
    p, m = tables()
    if fault == 'missing': p = p.iloc[1:]
    elif fault == 'duplicate': p = pd.concat([p, p.iloc[:1]])
    elif fault in ['nan', 'infinity', 'negative']: p.loc[0, 'A'] = {'nan':np.nan, 'infinity':np.inf, 'negative':-1}[fault]
    elif fault == 'fraction': p.loc[0, 'F'] = 1.1
    elif fault == 'mean_count': m.loc[0, 'n_pairs'] = 1
    elif fault == 'mean_missing': m = m.iloc[1:]
    with pytest.raises(ValueError):
        contrasts(p, m, [.2, .1], [0, 1], ['mode', 'other'])


def test_plan_memberships_and_exact_ids():
    ids = [str(720575940600000000+i) for i in range(52)]
    jobs = [dict(stage='fine', variant='default', dt_ms=d, seed=1, condition=c,
                 lesion_ids=[] if c == 'baseline' else ids[:51] if c == 'mode' else ids[1:])
            for d in [.2, .1] for c in ['baseline', 'mode', 'other']]
    plan = dict(jobs=jobs, mode_ids=ids[:51])
    assert memberships(plan, [.2, .1], [1], ['mode', 'other'])[0]['shared'] == 50
    for fault in ['float_id', 'duplicate_id', 'changed_members', 'missing_job', 'duplicate_job']:
        bad = deepcopy(plan)
        if fault == 'float_id': bad['jobs'][1]['lesion_ids'][0] = float(ids[0])
        elif fault == 'duplicate_id': bad['jobs'][1]['lesion_ids'][0] = ids[1]
        elif fault == 'changed_members': bad['jobs'][1]['lesion_ids'] = ids[1:]
        elif fault == 'missing_job': bad['jobs'].pop()
        else: bad['jobs'].append(deepcopy(jobs[0]))
        with pytest.raises(ValueError): memberships(bad, [.2, .1], [1], ['mode', 'other'])


@pytest.mark.parametrize('changed', ['checked_pairs.csv', 'checked_means.json', 'checked_agreement.json'])
def test_changed_verified_inputs_rejected(tmp_path, changed):
    import json
    from scripts.pcdr_ccr_transfer import digest
    from scripts.pcdr_fine_contrasts import run
    plan = tmp_path/'plan.json'
    plan.write_text('{}')
    names = ['checked_pairs.csv', 'checked_means.json', 'checked_agreement.json']
    for name in names: (tmp_path/name).write_text('original')
    check = dict(status='complete', plan_sha256=digest(plan),
                 outputs={n:digest(tmp_path/n) for n in names})
    (tmp_path/'full_check.json').write_text(json.dumps(check))
    (tmp_path/changed).write_text('changed')
    with pytest.raises(ValueError, match='Changed verified evidence'):
        run(tmp_path, plan, tmp_path/'output')
    assert not (tmp_path/'output').exists()
