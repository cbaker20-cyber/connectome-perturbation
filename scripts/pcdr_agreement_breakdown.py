"""Separate the existing agreement failures without changing their thresholds."""
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_transfer import read, write, digest


def components(agreement, pairs):
    keys = ['variant', 'condition', 'seed']
    columns = ['coarse_ms', 'fine_ms']+keys
    if agreement.duplicated(columns).any() or pairs.duplicated(['dt_ms']+keys).any():
        raise ValueError('Duplicate comparison or response row')
    if agreement.empty:
        raise ValueError('No comparisons')
    joined = agreement.merge(pairs[['dt_ms']+keys+['A']].rename(columns={'dt_ms':'fine_ms', 'A':'fine_A'}),
                             on=['fine_ms']+keys, how='left', validate='many_to_one')
    required = ['A_difference_hz', 'response_relative_L1', 'population_relative_L1', 'fine_A']
    if not np.isfinite(joined[required].to_numpy()).all() or (joined[required] < 0).any().any():
        raise ValueError('Missing or invalid response values')
    f = joined.F_difference.to_numpy()
    if np.isinf(f).any() or np.any(f < 0):
        raise ValueError('Invalid footprint difference')
    joined['A_pass'] = joined.A_difference_hz <= np.maximum(1., .05*joined.fine_A)
    joined['F_pass'] = joined.F_difference.notna() & (joined.F_difference <= .01)
    joined['vector_pass'] = joined.response_relative_L1 <= .05
    joined['population_pass'] = joined.population_relative_L1 <= .05
    response = joined.A_pass & joined.F_pass & joined.vector_pass
    if not np.array_equal(response, joined.passes_response) or not np.array_equal(response & joined.population_pass, joined.passes):
        raise ValueError('Component decisions differ from saved decisions')
    rows = []
    for key, group in joined.groupby(['coarse_ms', 'fine_ms', 'variant', 'condition'], sort=False):
        row = dict(zip(['coarse_ms', 'fine_ms', 'variant', 'condition'], key))
        row.update(n=len(group), **{name: int(group[name].sum()) for name in
            ['A_pass', 'F_pass', 'vector_pass', 'population_pass', 'passes_response', 'passes']})
        row['median_vector_relative_L1'] = float(group.response_relative_L1.median())
        row['median_population_relative_L1'] = float(group.population_relative_L1.median())
        rows.append(row)
    return rows


def run(evidence, out):
    check = read(evidence/'full_check.json')
    paths = [evidence/'checked_agreement.csv', evidence/'checked_pairs.csv']
    for path in paths:
        if digest(path) != check['outputs'][path.name]:
            raise ValueError('Changed checked evidence: '+path.name)
    agreement, pairs = [pd.read_csv(path) for path in paths]
    if len(agreement) != check['agreement_rows_reproduced']:
        raise ValueError('Incomplete comparison table')
    result = components(agreement, pairs)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'components.json', dict(groups=result, input_hashes={p.name:digest(p) for p in paths},
        script_sha256=digest(Path(__file__)), interpretation='Descriptive breakdown of unchanged criteria; not a new acceptance test.'))
    print(pd.DataFrame(result).to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path); parser.add_argument('out', type=Path)
    args = parser.parse_args(); run(args.evidence, args.out)
