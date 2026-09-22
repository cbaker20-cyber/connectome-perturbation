import itertools
import numpy as np
import pandas as pd
from eigencircuits.controls import matched_sets, FULL_FEATURES
from scripts.pcdr_matching_audit import mean_bounds, instrumented_sampler


def test_bounds_equal_exhaustive_coordinate_extrema():
    x = np.array([[0.,9.],[2.,4.],[8.,1.],[3.,8.],[7.,2.]])
    counts = {'a':2,'b':1}; pools = {'a':np.array([0,1,2]),'b':np.array([3,4])}
    means = np.array([x[list(a)+[b]].mean(0) for a in itertools.combinations([0,1,2],2) for b in [3,4]])
    low, high = mean_bounds(x,counts,pools)
    np.testing.assert_allclose(low,means.min(0))
    np.testing.assert_allclose(high,means.max(0))


def test_logging_does_not_change_sampler():
    f = pd.DataFrame({'root_id':[str(i) for i in range(12)],
                      'model_sign':['positive']*12,'recruited':[True]*12})
    for col in FULL_FEATURES: f[col] = 1.
    events=[]
    sample,_ = instrumented_sampler(lambda attempt,indices,balance: events.append((attempt,indices.copy(),balance.copy())))
    expected=matched_sets(f,['0','1'],['2'],n_sets=5,seed=31,max_attempts=100)
    actual=sample(f,['0','1'],['2'],n_sets=5,seed=31,max_attempts=100)
    assert actual==expected
    assert len(events)==5
    assert all(not {'0','1','2'} & set(s) and len(set(s))==2 for s in actual[0])
