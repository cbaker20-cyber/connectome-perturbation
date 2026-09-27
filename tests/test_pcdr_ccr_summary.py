import pytest
from scripts.pcdr_analyze_ccr_summary import check_metrics, mean_interval


def test_known_footprint_and_undefined_zero_fraction():
    row=dict(A=2.,on_absolute_sum_hz=4.,off_absolute_sum_hz=6.,total_absolute_sum_hz=10.,F=.4,on_signed_mean_hz=-1.,mn9_delta_hz=0.)
    check_metrics(row,2)
    row['F']=.5
    with pytest.raises(ValueError,match='F'):check_metrics(row,2)
    row={key:0. for key in row};row['F']=None
    check_metrics(row,2)
    row['F']=0.
    with pytest.raises(ValueError,match='undefined'):check_metrics(row,2)


def test_negative_or_nonfinite_effect_rejected():
    row=dict(A=-1.,on_absolute_sum_hz=-1.,off_absolute_sum_hz=2.,total_absolute_sum_hz=1.,F=-1.,on_signed_mean_hz=0.,mn9_delta_hz=0.)
    with pytest.raises(ValueError,match='Negative'):check_metrics(row,1)
    row['A']=float('nan')
    with pytest.raises(ValueError,match='Nonfinite'):check_metrics(row,1)


def test_paired_constant_and_invalid_contrasts():
    import numpy as np
    result=mean_interval(np.full(30, -4.), n=100)
    np.testing.assert_allclose(list(result.values()), [-4., -4., -4.])
    for values in [[1.], [0., float('nan')], [[1.,2.],[3.,4.]]]:
        with pytest.raises(ValueError,match='Invalid paired'):mean_interval(values)


def test_secondary_mn9_preserves_seed_pairing(tmp_path):
    import pandas as pd
    from scripts.pcdr_analyze_ccr_summary import secondary_analysis
    rows=[]
    for seed in range(30):
        for condition, offset in [('mode',-5),('mode_without_mn9',-3),
                                  ('mn9_only',1),('motor_003',0),
                                  ('motor_004',0),('motor_005',0)]:
            rows.append(dict(variant='fixture',condition=condition,seed=seed,
                             mn9_delta_hz=seed+offset,A=1.,F=.5,total_absolute_sum_hz=2.))
    frame=pd.DataFrame(rows).sample(frac=1,random_state=1)
    secondary_analysis(frame,tmp_path)
    result=pd.read_csv(tmp_path/'mn9_paired_contrasts.csv').set_index('contrast')
    assert result.loc['adding_mn9_to_other_50','mean_hz']==-2
    assert result.loc['adding_mn9_to_other_50','low_hz']==pytest.approx(-2)
    assert result.loc['adding_mn9_to_other_50','high_hz']==pytest.approx(-2)
