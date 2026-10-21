"""Compare locally trusted, hash-checked Brian checkpoint generations exactly."""
from pathlib import Path
import pickle

import numpy as np
import pandas as pd

from eigencircuits.common import read_json, sha256


def equal_state(left, right, path='state'):
    if type(left) is not type(right):
        raise ValueError(f'{path}: different types')
    if isinstance(left, np.ndarray):
        if left.dtype != right.dtype or left.shape != right.shape or not np.array_equal(left, right):
            raise ValueError(f'{path}: different array values, shape or dtype')
    elif isinstance(left, dict):
        if left.keys() != right.keys():
            raise ValueError(f'{path}: different keys')
        for key in left:
            equal_state(left[key], right[key], f'{path}/{key}')
    elif isinstance(left, (tuple, list)):
        if len(left) != len(right):
            raise ValueError(f'{path}: different sequence lengths')
        for i, (a, b) in enumerate(zip(left, right)):
            equal_state(a, b, f'{path}/{i}')
    elif not isinstance(left, (str, int, float, bool, type(None), np.generic)):
        raise ValueError(f'{path}: unsupported state type {type(left).__name__}')
    elif left != right:
        raise ValueError(f'{path}: different scalar values')


def checked_generation(folder):
    folder = Path(folder)
    record = read_json(folder/'latest.json')
    tick = record['tick']
    name = record['generation']
    if type(tick) is not int or tick <= 0 or not isinstance(name, str):
        raise ValueError('Invalid generation metadata')
    if Path(name).name != name or not name.startswith(f'tick_{tick}_'):
        raise ValueError('Invalid generation path')
    base = folder/name
    if set(record['hashes']) != {'network.pkl', 'delivered.parquet'}:
        raise ValueError('Invalid checkpoint file set')
    for member, digest in record['hashes'].items():
        if sha256(base/member) != digest:
            raise ValueError(f'Checkpoint hash mismatch: {member}')
    return record, base


def compare(left, right):
    a, pa = checked_generation(left)
    b, pb = checked_generation(right)
    if a['config'] != b['config'] or a['tick'] != b['tick']:
        raise ValueError('Checkpoint configuration or endpoint differs')
    # These are owned simulator outputs; hashes detect damage, not untrusted pickle code.
    with (pa/'network.pkl').open('rb') as stream:
        state_a = pickle.load(stream)
    with (pb/'network.pkl').open('rb') as stream:
        state_b = pickle.load(stream)
    equal_state(state_a, state_b)
    pd.testing.assert_frame_equal(pd.read_parquet(pa/'delivered.parquet'),
                                  pd.read_parquet(pb/'delivered.parquet'), check_exact=True)
    return dict(exact_state=True, exact_delivered=True, tick=a['tick'],
                left=a, right=b)
