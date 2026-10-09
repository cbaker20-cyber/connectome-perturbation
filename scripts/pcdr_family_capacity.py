"""Enumerate the matching/diversity capacity of saved comparison sets."""
from collections import Counter
from pathlib import Path
import argparse
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import digest, read, write, utc
from scripts.pcdr_matching_audit import FEATURES, SELECTION
from scripts.pcdr_verify_diverse import distribution_check
from eigencircuits.controls import FULL_FEATURES
from eigencircuits.common import environment, sugar_ids


def capacity(gaps, overlaps, size):
    gaps, overlaps = np.asarray(gaps), np.asarray(overlaps)
    n = len(gaps)
    if n > 20 or gaps.shape != (n,) or overlaps.shape != (n, n):
        raise ValueError('Invalid dimensions or exhaustive-search budget')
    if size < 1 or not np.issubdtype(gaps.dtype, np.integer) or not np.issubdtype(overlaps.dtype, np.integer):
        raise ValueError('Counts must be integers')
    if np.any(gaps < 0) or np.any(gaps > size) or np.any(overlaps < 0) or np.any(overlaps > size):
        raise ValueError('Invalid counts')
    if not np.array_equal(overlaps, overlaps.T) or np.any(np.diag(overlaps) != size):
        raise ValueError('Invalid overlap matrix')
    # Every subset has one exact gap/overlap requirement. Retain one witness
    # per requirement before forming all threshold combinations.
    total = 1 << n
    gap = np.zeros(total, dtype=np.int16)
    shared = np.zeros(total, dtype=np.int16)
    counts = np.zeros(total, dtype=np.int8)
    best = np.zeros((size + 1, size + 1), dtype=np.int8)
    witness = np.zeros_like(best, dtype=np.int64)
    for mask in range(1, total):
        bit = mask & -mask
        i = bit.bit_length() - 1
        rest = mask ^ bit
        gap[mask] = max(gap[rest], gaps[i])
        cap = int(shared[rest])
        remaining = rest
        while remaining:
            other = remaining & -remaining
            cap = max(cap, int(overlaps[i, other.bit_length() - 1]))
            remaining ^= other
        shared[mask] = cap
        counts[mask] = counts[rest] + 1
        g = gap[mask]
        if counts[mask] > best[g, cap]:
            best[g, cap], witness[g, cap] = counts[mask], mask
    for g in range(size + 1):
        for cap in range(size + 1):
            for a, b in ((g - 1, cap), (g, cap - 1)):
                if a >= 0 and b >= 0 and best[a, b] > best[g, cap]:
                    best[g, cap], witness[g, cap] = best[a, b], witness[a, b]
    return best, witness


def clique_capacity(gaps, overlaps, gap, cap):
    """Independent graph search checks the subset dynamic program."""
    eligible = [i for i, value in enumerate(gaps) if value <= gap]
    best = 0
    def visit(chosen, remaining):
        nonlocal best
        best = max(best, chosen)
        while chosen + len(remaining) > best:
            i = remaining.pop()
            visit(chosen + 1, [j for j in remaining if overlaps[i, j] <= cap])
    visit(0, eligible)
    return best


def run(out):
    base = ROOT / 'results/pcdr'
    studies = [base / 'distribution_match_20261008', base / 'distribution_expand_20261008']
    inputs = {str(FEATURES): digest(FEATURES), str(SELECTION): digest(SELECTION),
              str(Path(__file__)): digest(__file__),
              str(ROOT / 'scripts/pcdr_verify_diverse.py'): digest(ROOT / 'scripts/pcdr_verify_diverse.py')}
    members = {}
    for k, study in enumerate(studies):
        protocol, verification = read(study / 'protocol.json'), read(study / 'verification.json')
        if verification['status'] != 'verified':
            raise ValueError('Unverified study')
        for name, expected in {**protocol['inputs'], **verification['inputs']}.items():
            if digest(name) != expected:
                raise ValueError('Changed evidence: ' + name)
        for name in ['protocol.json', 'verification.json']:
            inputs[str(study / name)] = digest(study / name)
        if k == 0:
            members.update(protocol['references'])
        elif protocol['references'] != read(studies[0] / 'protocol.json')['references']:
            raise ValueError('Reference families differ')
        for kind in protocol['solves']:
            path = study / kind / 'candidate.json'
            inputs[str(path)] = digest(path)
            members[f'pool_{verification["candidate_pool_size"]}_{kind}'] = read(path)['root_ids']
    if len(members) != 19 or len({tuple(sorted(v)) for v in members.values()}) != 19:
        raise ValueError('Expected nineteen distinct saved candidates')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol.json', dict(recorded_utc=utc(), inputs=inputs,
        question='How many of the nineteen saved candidates can coexist at every CDF-gap and pairwise-overlap limit?',
        design='Enumerate all 2^19 subsets. Use integer CDF count gaps 0..51 and pairwise shared-cell caps 0..51; no selected acceptance cutoff. Check the entire grid by independent maximum-clique search.',
        scope='Retrospective design audit of saved optimized sets, not full-pool feasibility or a random ensemble.',
        members=members, simulation=False))
    frame = pd.read_parquet(FEATURES)
    if not frame.root_id.is_unique or not frame.root_id.map(lambda v: isinstance(v, str)).all():
        raise ValueError('Invalid feature IDs')
    frame = frame.set_index('root_id')
    target = read(SELECTION)['root_ids']
    def strata(ids):
        f = frame.loc[ids]
        return Counter(zip(f.model_sign.astype(str), f.recruited.astype(bool), f.super_class.eq('motor')))
    audits = {}
    excluded = set(target) | set(sugar_ids())
    for name, ids in members.items():
        if len(ids) != 51 or len(set(ids)) != 51 or any(type(v) is not str for v in ids):
            raise ValueError('Invalid membership: ' + name)
        if not set(ids) <= set(frame.index) or excluded & set(ids) or strata(ids) != strata(target):
            raise ValueError('Invalid eligibility/strata: ' + name)
        smd, ratios, gaps = distribution_check(np.log1p(frame.loc[target, FULL_FEATURES].to_numpy(float)),
                                              np.log1p(frame.loc[ids, FULL_FEATURES].to_numpy(float)))
        if np.any(smd > .1):
            raise ValueError('Original SMD rule failed: ' + name)
        count = int(round(51 * max(gaps)))
        if abs(count / 51 - max(gaps)) > 1e-12:
            raise ValueError('CDF count mismatch')
        audits[name] = dict(maximum_cdf_count=count, maximum_smd=float(max(smd)), variance_ratios=ratios)
    names = list(members)
    overlaps = np.array([[len(set(members[a]) & set(members[b])) for b in names] for a in names])
    gaps = np.array([audits[name]['maximum_cdf_count'] for name in names])
    best, witnesses = capacity(gaps, overlaps, 51)
    rows = []
    for g in range(52):
        for cap in range(52):
            if int(best[g, cap]) != clique_capacity(gaps, overlaps, g, cap):
                raise ValueError('Independent family capacity mismatch')
        if g not in set(gaps):
            continue
        for n in range(1, int(best[g, 51]) + 1):
            cap = int(np.flatnonzero(best[g] >= n)[0])
            mask = int(witnesses[g, cap])
            chosen = [names[i] for i in range(len(names)) if mask & (1 << i)]
            rows.append(dict(maximum_cdf_count=g, family_size_at_least=n,
                             minimum_overlap_cap=cap, witness=chosen))
    write(out / 'results.json', dict(status='independently_verified', audits=audits, names=names,
        overlaps=overlaps.tolist(), frontier=rows, checked_threshold_pairs=2704,
        enumerated_subsets=2**19, capacity_at_cap_30={str(g):int(best[g, 30]) for g in sorted(set(gaps))},
        environment=environment(), completed_utc=utc()))
    write(out / 'complete.json', dict(status='complete', outputs={n:digest(out / n) for n in ['protocol.json','results.json']}))
    print('Verified all 2,704 threshold pairs; capacity at overlap cap 30:', {int(g):int(best[g,30]) for g in sorted(set(gaps))})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
