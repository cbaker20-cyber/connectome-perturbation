import itertools
import sys
import time

import numpy as np
import pytest

from scripts.pcdr_bounded_process import run_bounded
from scripts.pcdr_fullpool_relaxation import solve_relaxation, validate_fractional
from scripts.pcdr_fullpool_bounds import smd_lower_bounds
from eigencircuits.controls import standardized_difference
from scripts.pcdr_fractional_completion import completions


def test_external_deadline_stops_owned_process(tmp_path):
    start = time.monotonic()
    result = run_bounded([sys.executable, '-c', 'import time; print("started", flush=True); time.sleep(30)'], tmp_path, 1)
    assert result['timed_out'] and result['returncode'] != 0
    assert time.monotonic()-start < 15
    assert 'started' in (tmp_path/'stdout.txt').read_text()


def test_worker_success_and_error_are_distinct_from_timeout(tmp_path):
    for code in [0, 3]:
        result = run_bounded([sys.executable, '-c', f'raise SystemExit({code})'], tmp_path/str(code), 10)
        assert not result['timed_out'] and result['returncode'] == code


def test_fractional_feasibility_does_not_prove_binary_feasibility():
    values = np.array([[0.], [2.]])
    result, _ = solve_relaxation(values, ['a', 'a'], {'a': 1}, np.array([1.]), np.array([0.]), np.ones(1))
    assert result.success
    checked = validate_fractional(result.x, values, ['a', 'a'], {'a': 1}, np.array([1.]), np.array([0.]), np.ones(1))
    assert checked['fractional_count'] == 2
    assert all(v != 1 for v in values[:, 0])
    with pytest.raises(ValueError):
        validate_fractional(np.array([1., 0.]), values, ['a', 'a'], {'a': 1}, np.array([1.]), np.array([0.]), np.ones(1))


def test_joint_infeasibility_despite_coordinatewise_feasibility():
    values = np.array([[0., 0.], [2., 2.]])
    result, _ = solve_relaxation(values, ['a', 'a'], {'a': 1}, np.array([0., 2.]), np.zeros(2), np.ones(2))
    assert result.status == 2


def test_outer_bounds_include_every_original_smd_valid_binary_set():
    values = np.array([[0., 9.], [2., 4.], [8., 1.], [3., 8.], [7., 2.]])
    counts = {'a': 2, 'b': 1}
    pools = {'a': np.array([0, 1, 2]), 'b': np.array([3, 4])}
    samples = [values[list(a)+[b]] for a in itertools.combinations([0, 1, 2], 2) for b in [3, 4]]
    checked = 0
    for target in samples:
        _, _, vmax, _ = smd_lower_bounds(target, values, counts, pools)
        tolerance = .1*np.sqrt((target.var(0)+vmax)/2)
        for sample in samples:
            if np.all(standardized_difference(target, sample) <= .1):
                assert np.all(abs(target.mean(0)-sample.mean(0)) <= tolerance+1e-12)
                checked += 1
    assert checked >= len(samples)


def test_completion_enumeration_preserves_fixed_cells_and_exact_strata():
    weights = np.array([1., .2, .8, 0., .5, .5])
    groups = ['a']*4+['b']*2
    result = {tuple(sorted(indices)) for indices in completions(weights, groups, {'a': 2, 'b': 1})}
    assert result == {(0, 1, 4), (0, 1, 5), (0, 2, 4), (0, 2, 5)}
    with pytest.raises(ValueError, match='budget'):
        list(completions(np.full(13, .5), ['a']*13, {'a': 6}))
