import json

import numpy as np
import pytest

from scripts.pcdr_checkpoint_compare import compare, equal_state
from test_pcdr_checkpoint import fixture_files, worker


def test_nested_state_detects_tiny_change():
    a={'v': (np.array([1., 2.]), 2), 'rng': [np.array([1], dtype='uint32')]}
    equal_state(a, a)
    b={'v': (np.array([1., np.nextafter(2., 3.)]), 2), 'rng': [np.array([1], dtype='uint32')]}
    with pytest.raises(ValueError, match='different array'):
        equal_state(a, b)


@pytest.mark.parametrize('other',[np.array([1],dtype='int32'),np.array([[1]],dtype='int64'),[1]])
def test_state_rejects_type_dtype_shape(other):
    with pytest.raises(ValueError):
        equal_state(np.array([1],dtype='int64'),other)


def test_actual_full_state_after_fresh_process_restart(tmp_path):
    left=tmp_path/'left'; right=tmp_path/'right'
    left.mkdir(); right.mkdir()
    fixture_files(left); fixture_files(right)
    worker(left)
    worker(right,stop=1,expected=75)
    worker(right)
    result=compare(left/'checkpoint',right/'checkpoint')
    assert result['exact_state'] and result['exact_delivered']
    latest=right/'checkpoint/latest.json'
    record=json.loads(latest.read_text())
    record['tick']+=1
    latest.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        compare(left/'checkpoint',right/'checkpoint')
