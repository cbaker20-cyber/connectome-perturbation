import numpy as np
import pytest
from scripts.pcdr_trace_analysis import aligned, WINDOWS


def test_alignment_retains_physical_times_without_interpolation():
    coarse = np.array([[10., 20., 30.]])
    fine = np.array([[11., 999., 21., 999., 31., 999.]])
    a,b = aligned(coarse, fine)
    np.testing.assert_array_equal(b-a, [[1.,1.,1.]])
    with pytest.raises(ValueError): aligned(coarse, fine[:,:-1])


def test_windows_partition_both_clocks():
    for dt in [.0125,.00625]:
        time = np.arange(round(1000/dt))*dt
        coverage = np.zeros(len(time), dtype=int)
        for start,end in WINDOWS: coverage += (time >= start-1e-9) & (time < end-1e-9)
        assert np.all(coverage == 1)
