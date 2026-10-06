"""Remove specified directed connections without changing other model inputs."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

KEYS = ['Presynaptic_Index', 'Postsynaptic_Index']
WEIGHT = 'Excitatory x Connectivity'


def remove_edges(frame, pairs):
    if any(name not in frame for name in KEYS + [WEIGHT]):
        raise ValueError('Missing connectivity columns')
    pairs = list(pairs)
    if any(len(pair) != 2 or any(isinstance(i, (bool, np.bool_)) or
           not isinstance(i, (int, np.integer)) or i < 0 for i in pair) for pair in pairs):
        raise ValueError('Edges require nonnegative integer neuron indices')
    pairs = [tuple(pair) for pair in pairs]
    if len(set(pairs)) != len(pairs):
        raise ValueError('Duplicate requested edge')
    for name in KEYS:
        values = frame[name].to_numpy()
        if not np.issubdtype(values.dtype, np.integer) or np.any(values < 0):
            raise ValueError('Connectivity indices must be nonnegative integers')
    if not np.isfinite(frame[WEIGHT].to_numpy()).all():
        raise ValueError('Nonfinite connectivity weight')
    index = pd.MultiIndex.from_frame(frame[KEYS])
    if index.has_duplicates:
        raise ValueError('Duplicate connectivity edges require review before intervention')
    positions = index.get_indexer(pairs) if pairs else np.array([], dtype=int)
    if np.any(positions < 0):
        raise ValueError('Requested edge absent from connectivity')
    if np.any(frame.iloc[positions][WEIGHT].to_numpy() == 0):
        raise ValueError('Requested edge already has zero weight')
    changed = frame.copy()
    changed.iloc[positions, changed.columns.get_loc(WEIGHT)] = 0
    return changed, frame.iloc[positions].copy()


@contextmanager
def connectivity_without(path, pairs):
    frame, removed = remove_edges(pd.read_parquet(path), pairs)
    # Keep the original dataset untouched; the simulator receives a temporary copy.
    with TemporaryDirectory(prefix='pcdr_edges_') as directory:
        target = Path(directory)/'connectivity.parquet'
        frame.to_parquet(target, index=False)
        del frame
        yield target, removed
