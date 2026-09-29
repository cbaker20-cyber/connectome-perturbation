import numpy as np
import pandas as pd
import pytest

from scripts.pcdr_candidate_review import aligned_features, support


def test_complex_power_and_boundary():
    indices, power = support(np.array([2j, 1, 1, 0]), 2 / 3)
    assert indices.tolist() == [0]
    np.testing.assert_allclose(power, [4 / 6, 1 / 6, 1 / 6, 0])
    assert support(np.array([1, 1, 1]), .5)[0].tolist() == [0, 1]
    assert support(np.array([1, 1, 1]), 1)[0].tolist() == [0, 1, 2]


@pytest.mark.parametrize('vector,fraction', [([], .75), ([0, 0], .75), ([np.nan], .75), ([1], 0), ([[1]], .75)])
def test_invalid_support(vector, fraction):
    with pytest.raises(ValueError):
        support(vector, fraction)


def test_exact_ids_and_feature_order():
    ids = ['720575940619473624', '720575940619473625']
    f = pd.DataFrame(dict(root_id=ids, spike_count=[5, 0], trials_recruited=[2, 0]))
    assert aligned_features(f, ids[::-1]).spike_count.tolist() == [0, 5]
    for invalid in [pd.concat([f, f.iloc[:1]]), f.assign(root_id=[float(ids[0]), float(ids[1])]),
                    f.assign(spike_count=[-1, 0]), f.assign(trials_recruited=[6, 0]),
                    f.assign(trials_recruited=[0, 0])]:
        with pytest.raises(ValueError):
            aligned_features(invalid, ids)
    with pytest.raises(ValueError):
        aligned_features(f.iloc[:1], ids)
