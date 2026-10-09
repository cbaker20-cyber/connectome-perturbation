"""Locate saved baseline count disagreement without aligning spike trains."""
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest, utc
from eigencircuits.common import environment

ENDS = [100, 200, 300, 400, 500, 600, 700, 800, 900, 950, 980, 990, 995, 999, 1000]


def counts_at(t, cells, n, ends, dt_ms):
    t, cells, ends = np.asarray(t), np.asarray(cells), np.asarray(ends)
    if (t.ndim != 1 or t.shape != cells.shape or not np.isfinite(t).all()
            or np.any(t < 0) or np.any(t >= 1) or n < 1
            or not np.issubdtype(cells.dtype, np.integer)
            or np.any(cells < 0) or np.any(cells >= n)
            or ends.ndim != 1 or not len(ends) or not np.isfinite(ends).all()
            or np.any(ends <= 0) or np.any(ends > 1000) or np.any(np.diff(ends) <= 0)
            or dt_ms not in (.0002, .0001)):
        raise ValueError('Invalid spikes, cells, endpoints or step')
    native = t * 1000 / dt_ms
    if not np.allclose(native, np.rint(native), rtol=0, atol=1e-6):
        raise ValueError('Off-grid spike')
    # Compare integers so events exactly at a cut belong to the following window.
    ticks = np.rint(native).astype(np.int64) * round(dt_ms / .0001)
    cuts = np.rint(ends / .0001).astype(np.int64)
    if not np.allclose(ends / .0001, cuts, rtol=0, atol=1e-6):
        raise ValueError('Off-grid endpoint')
    return np.stack([np.bincount(cells[ticks < cut], minlength=n) for cut in cuts])


def measures(a, b):
    delta = a - b
    total = delta[-1]
    previous = np.zeros(a.shape[1], dtype=np.int64)
    rows = []
    for i, current in enumerate(delta):
        tail_capacity = (a[-1] - a[i]) + (b[-1] - b[i])
        rows.append(dict(prefix_L1=int(abs(current).sum()),
            interval_L1=int(abs(current - previous).sum()),
            final_L1=int(abs(total).sum()),
            tail_L1=int(abs(total - current).sum()),
            residual_after_arbitrary_tail_deletion_lower_bound=int(np.maximum(abs(total) - tail_capacity, 0).sum())))
        previous = current
    return rows


def run(out):
    prior = ROOT / 'docs/pcdr/evidence/2026-10-09/baseline_counts'
    snapshot = read(prior / 'snapshot.json')
    for name, expected in snapshot['files'].items():
        if digest(prior / name) != expected:
            raise ValueError('Changed prior evidence: ' + name)
    protocol, summary = read(prior / 'protocol.json'), read(prior / 'summary.json')
    source = ROOT / 'results/pcdr/fine_download_20261005'
    plan_path = source / 'plan.json'
    if digest(plan_path) != protocol['inputs'][str(plan_path)]:
        raise ValueError('Changed plan')
    jobs = [j for j in read(plan_path)['jobs'] if j['stage'] == 'fine' and j['variant'] == 'default'
            and j['condition'] == 'baseline' and j['dt_ms'] in (.0002, .0001)]
    keys = {(j['seed'], j['dt_ms']): j for j in jobs}
    seeds = sorted({j['seed'] for j in jobs})
    if len(seeds) != 30 or len(keys) != len(jobs) or set(keys) != {(s, d) for s in seeds for d in (.0002, .0001)}:
        raise ValueError('Unexpected trial coverage')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol.json', dict(recorded_utc=utc(), environment=environment(),
        inputs={str(p): digest(p) for p in [Path(__file__), prior / 'snapshot.json', prior / 'summary.json', plan_path]},
        endpoints_ms=ENDS, window='Half-open [0,end) prefixes; adjacent intervals; all 30 baseline pairs.',
        design='Descriptive count L1, without dividing by prefix duration. Integer native ticks mapped to common 0.0001-ms grid. Also bound remaining final count L1 after arbitrary removal of observed spikes from the suffix: sum max(abs(final difference) - combined suffix counts, 0). No new scientific tolerance or seed selection.',
        limitations='New descriptive windows selected before these results, after prior count findings. Truncation changes the endpoint. Bounds concern deletion of saved suffix spikes, not unobserved future spikes, causal attribution, or convergence.'))
    prior_pairs = pd.read_csv(prior / 'pairs.csv').set_index('seed')
    rows, hashes = [], {}
    for seed in seeds:
        frames = []
        for dt in (.0002, .0001):
            path = source / 'trials' / keys[seed, dt]['id'] / 'spikes.parquet'
            hashes[str(path)] = digest(path)
            if hashes[str(path)] != summary['input_hashes'][str(path)]:
                raise ValueError('Changed spikes: ' + str(path))
            frame = pd.read_parquet(path)
            if not frame.flywire_id.map(lambda x: type(x) is str).all() or frame.duplicated(['flywire_id', 't']).any():
                raise ValueError('Invalid spike IDs or duplicates')
            frames.append(frame)
        ids = pd.Index(sorted(set(frames[0].flywire_id) | set(frames[1].flywire_id)))
        # A silent pair still needs one zero column for the count representation.
        matrices = [counts_at(f.t.to_numpy(), ids.get_indexer(f.flywire_id), max(1, len(ids)), ENDS, d)
                    for f, d in zip(frames, (.0002, .0001))]
        values = measures(*matrices)
        if values[-1]['final_L1'] != prior_pairs.loc[seed, 'total_L1']:
            raise ValueError('Final count check failed')
        rows.extend(dict(seed=seed, end_ms=end, **value) for end, value in zip(ENDS, values))
    frame = pd.DataFrame(rows)
    frame.to_csv(out / 'windows.csv', index=False)
    metrics = list(rows[0])[2:]
    write(out / 'summary.json', dict(completed_utc=utc(), input_hashes=hashes,
        groups=[dict(end_ms=int(end), medians={c: float(g[c].median()) for c in metrics},
            sums={c: int(g[c].sum()) for c in metrics}, nonzero_prefix_seeds=int((g.prefix_L1 > 0).sum()))
            for end, g in frame.groupby('end_ms')]))
    print(frame.groupby('end_ms')[metrics].median().to_string())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
