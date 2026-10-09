"""Describe baseline count disagreement at the two saved finest steps."""
import argparse
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from eigencircuits.common import environment


def partition(coarse, fine):
    a, b = np.asarray(coarse), np.asarray(fine)
    if (a.ndim != 1 or a.shape != b.shape or not len(a)
            or not np.issubdtype(a.dtype, np.integer)
            or not np.issubdtype(b.dtype, np.integer)
            or np.any(a < 0) or np.any(b < 0)):
        raise ValueError('Matching nonempty nonnegative integer count vectors required')
    # Object integers avoid overflow in differences and sums for arbitrary inputs.
    a, b = a.astype(object), b.astype(object)
    only_a, only_b, both = (a > 0) & (b == 0), (b > 0) & (a == 0), (a > 0) & (b > 0)
    difference = abs(a - b)
    return dict(coarse_active=int((a > 0).sum()), fine_active=int((b > 0).sum()),
        coarse_only_cells=int(only_a.sum()), fine_only_cells=int(only_b.sum()),
        shared_changed_cells=int((both & (a != b)).sum()),
        coarse_only_L1=int(difference[only_a].sum()), fine_only_L1=int(difference[only_b].sum()),
        shared_active_L1=int(difference[both].sum()), total_L1=int(difference.sum()))


def run(out):
    source = ROOT / 'results/pcdr/fine_download_20261005'
    verified = ROOT / 'results/pcdr/fine_verified_20261005/full_check.json'
    archive = ROOT / 'CCR_fine_results.zip'
    check = read(verified)
    if check['status'] != 'complete' or digest(archive) != check['archive_sha256']:
        raise ValueError('Archive verification mismatch')
    if digest(source / 'plan.json') != check['plan_sha256']:
        raise ValueError('Changed plan')
    jobs = [j for j in read(source / 'plan.json')['jobs'] if j['stage'] == 'fine'
            and j['variant'] == 'default' and j['condition'] == 'baseline'
            and j['dt_ms'] in (.0002, .0001)]
    keys = {(j['seed'], j['dt_ms']): j for j in jobs}
    seeds = sorted({j['seed'] for j in jobs})
    if len(seeds) != 30 or len(keys) != len(jobs) or set(keys) != {(s, d) for s in seeds for d in (.0002, .0001)}:
        raise ValueError('Unexpected baseline coverage')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol.json', dict(recorded_utc=utc(), environment=environment(),
        inputs={str(p): digest(p) for p in [Path(__file__), verified, source / 'plan.json']},
        archive_sha256=check['archive_sha256'],
        design='All 30 saved default baseline pairs at 0.0002 and 0.0001 ms. Full-second per-neuron counts, including stimulated cells. Partition count L1 into coarse-only active, fine-only active, and active at both steps. No onset inference or timing alignment. Hash-check spikes and rates; count spikes independently of saved rates.',
        limitations='Exploratory diagnostic following baseline decomposition. Activity is specific to the one-second observation window. Count differences can include endpoint effects; this does not establish persistent recruitment, timing mechanism, or convergence.'))
    rows, cells, hashes = [], [], {}
    with zipfile.ZipFile(archive) as z:
        if (source / 'neurons.csv').read_bytes() != z.read('neurons.csv'):
            raise ValueError('Changed neuron inventory')
        ids = pd.Index(pd.read_csv(source / 'neurons.csv', dtype=str).root_id)
        if not ids.is_unique:
            raise ValueError('Duplicate neuron IDs')
        for seed in seeds:
            counts = []
            for dt in (.0002, .0001):
                job = keys[seed, dt]
                manifest = json.loads(z.read('trials/' + job['id'] + '/manifest.json'))
                if manifest['status'] != 'complete' or manifest['spec'] != job:
                    raise ValueError('Invalid trial manifest')
                for name in ['spikes.parquet', 'rates.parquet']:
                    path = source / 'trials' / job['id'] / name
                    hashes[str(path)] = digest(path)
                    if hashes[str(path)] != manifest['outputs'][name]:
                        raise ValueError('Changed output: ' + str(path))
                spikes = pd.read_parquet(source / 'trials' / job['id'] / 'spikes.parquet')
                indices = ids.get_indexer(spikes.flywire_id)
                if (not spikes.flywire_id.map(lambda x: type(x) is str).all() or np.any(indices < 0)
                        or not np.isfinite(spikes.t).all() or (spikes.t < 0).any() or (spikes.t >= 1).any()
                        or spikes.duplicated(['flywire_id', 't']).any()):
                    raise ValueError('Invalid saved spikes')
                count = np.bincount(indices, minlength=len(ids))
                rates = pd.read_parquet(source / 'trials' / job['id'] / 'rates.parquet')
                if (rates.root_id.duplicated().any() or not rates.root_id.map(lambda x: type(x) is str).all()
                        or not set(rates.root_id) <= set(ids)):
                    raise ValueError('Invalid rate IDs')
                saved = rates.set_index('root_id').rate_hz.reindex(ids, fill_value=0).to_numpy()
                if not np.array_equal(saved, count):
                    raise ValueError('Spike counts differ from saved one-second rates')
                counts.append(count)
            row = partition(*counts)
            rows.append(dict(seed=seed, **row))
            changed = np.flatnonzero(counts[0] != counts[1])
            cells.extend(dict(seed=seed, root_id=ids[i], coarse_count=int(counts[0][i]), fine_count=int(counts[1][i])) for i in changed)
    frame = pd.DataFrame(rows)
    frame.to_csv(out / 'pairs.csv', index=False)
    pd.DataFrame(cells).to_csv(out / 'changed_cells.csv', index=False)
    total = int(frame.total_L1.sum())
    write(out / 'summary.json', dict(completed_utc=utc(), n=30, input_hashes=hashes,
        medians={c: float(frame[c].median()) for c in frame.columns if c != 'seed'},
        pooled={c: int(frame[c].sum()) for c in ['coarse_only_L1', 'fine_only_L1', 'shared_active_L1', 'total_L1']},
        pooled_one_step_only_fraction=None if not total else float((frame.coarse_only_L1.sum() + frame.fine_only_L1.sum()) / total)))
    print(frame.drop(columns='seed').median().to_string())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
