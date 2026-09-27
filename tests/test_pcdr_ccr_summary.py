import pytest
from scripts.pcdr_analyze_ccr_summary import check_metrics


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
