"""Audit the returned CCR summary and report descriptive results without raw spikes."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_ccr_sensitivity import planned_jobs


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_metrics(row, size):
    a, inside, outside, total = [float(row[k]) for k in
        ['A', 'on_absolute_sum_hz', 'off_absolute_sum_hz', 'total_absolute_sum_hz']]
    require(np.isfinite([a, inside, outside, total, row['on_signed_mean_hz'], row['mn9_delta_hz']]).all(), 'Nonfinite metric')
    require(min(a, inside, outside, total) >= 0, 'Negative absolute metric')
    require(np.isclose(a * size, inside) and np.isclose(inside + outside, total), 'Inconsistent footprint')
    f = row['F']
    if total == 0:
        require(pd.isna(f), 'Zero response needs undefined F')
    else:
        require(np.isfinite(f) and np.isclose(f, inside / total), 'Inconsistent F')
    require(abs(row['on_signed_mean_hz']) <= a + 1e-8, 'Signed mean exceeds absolute mean')


def mean_interval(values, seed=630727, n=10000):
    values = np.asarray(values, dtype=float)
    require(values.ndim == 1 and len(values) >= 2 and np.isfinite(values).all(), 'Invalid paired contrast')
    weights = np.random.default_rng(seed).multinomial(
        len(values), np.full(len(values), 1 / len(values)), size=n) / len(values)
    low, high = np.quantile(weights @ values, [.025, .975])
    return {'mean_hz': float(values.mean()), 'low_hz': float(low), 'high_hz': float(high)}


def secondary_analysis(seeds, out):
    """Post-result scalar diagnostics; none replaces the primary vector footprint."""
    mn9, counts, influence = [], [], []
    for variant, group in seeds.groupby('variant', sort=True):
        wide = group.pivot(index='seed', columns='condition', values='mn9_delta_hz').sort_index()
        incremental = wide['mode'] - wide['mode_without_mn9']
        contrasts = {
            'adding_mn9_to_other_50': incremental,
            'mn9_by_other_50_interaction': incremental - wide['mn9_only'],
        }
        if variant == 'default':
            singles = sorted(c for c in wide if c.startswith('mode_cell_')) + ['mn9_only']
            require(len(singles) == 51, 'Incomplete single-cell map')
            contrasts['joint_minus_sum_of_51_singles'] = wide['mode'] - wide[singles].sum(axis=1)
        for name, values in contrasts.items():
            mn9.append({'variant': variant, 'contrast': name, 'n_pairs': len(values),
                        **mean_interval(values), 'bootstrap_seed': 630727, 'replicates': 10000})
        mode = group[group.condition == 'mode'].set_index('seed').sort_index()
        for c in ['motor_003', 'motor_004', 'motor_005']:
            comp = group[group.condition == c].set_index('seed').sort_index()
            require(mode.index.equals(comp.index), 'Unpaired comparison')
            counts.append({'variant': variant, 'comparison': c, 'n_pairs': len(mode),
                'A_mode_greater': int((mode.A > comp.A).sum()),
                'F_mode_greater': int((mode.F > comp.F).sum()),
                'A_mode_equal': int(np.isclose(mode.A, comp.A).sum()),
                'F_mode_equal': int(np.isclose(mode.F, comp.F).sum())})
        for c, frame in group.groupby('condition'):
            total = frame.total_absolute_sum_hz
            largest = frame.loc[total.idxmax()]
            influence.append({'variant': variant, 'condition': c,
                'largest_seed': int(largest.seed), 'largest_total_hz': float(total.max()),
                'median_total_hz': float(total.median()),
                'largest_share_of_sum_of_seed_totals': float(total.max()/total.sum()) if total.sum() else None})
    pd.DataFrame(mn9).to_csv(out/'mn9_paired_contrasts.csv', index=False)
    pd.DataFrame(counts).to_csv(out/'paired_seed_orderings.csv', index=False)
    pd.DataFrame(influence).to_csv(out/'seed_influence.csv', index=False)


def analyze(archive, out):
    prefix = 'results/expanded_sensitivity/'
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'Duplicate archive entries')
        require(z.testzip() is None, 'ZIP CRC failure')
        payload = {name: z.read(name) for name in names}
    def read(name):
        return json.loads(payload[prefix + name])
    plan, result, audit, capacity, progress = [read(n) for n in
        ['jobs.json', 'results.json', 'collection_environment.json', 'capacity.json', 'progress.json']]
    job_hash = digest(payload[prefix + 'jobs.json'])
    for record in [result, audit, capacity]:
        require(record['jobs_sha256'] == job_hash, 'Job hash mismatch')
    require(audit['status'] == 'complete', 'Remote collection incomplete')
    for name in ['results.json', 'per_seed.csv']:
        require(digest(payload[prefix + name]) == audit['outputs'][name], 'Collected output hash mismatch')
    require(audit['collector_sha256'] == digest((ROOT/'scripts/pcdr_collect_existing.py').read_bytes()), 'Unknown collector source')
    for field in ['inputs', 'sources']:
        for name, expected_hash in plan['provenance'][field].items():
            path = (ROOT / name).resolve()
            require(path.is_relative_to(ROOT), 'Unexpected provenance path')
            require(digest(path.read_bytes()) == expected_hash, f'Local {field} differ: {name}')
    require(plan['design'] == json.loads((ROOT/'docs/pcdr/CCR_EXPANDED_DESIGN.json').read_text()), 'Amended design differs')
    design = plan['design']
    require(plan['conditions'] == design['conditions'] and plan['variants'] == design['network_variants'], 'Plan metadata differs')
    require(plan['jobs'] == planned_jobs(plan['conditions'], plan['variants'], design['seeds']), 'Job list differs')
    require(progress['finished'] == progress['total'] == 3390, 'Incomplete progress')
    require(sorted(x['index'] for x in progress['results']) == list(range(3390)), 'Missing or repeated trial indices')
    for row in progress['results']:
        require(row['status'] == 'complete', 'Unfinished trial')
        if not row.get('reused'):
            require(row['execution']['returncode'] == 0 and not row['execution']['timed_out'], 'Failed worker')
    calibrated = [i for wave in capacity['waves'] for i in wave['indices']]
    require(len(calibrated) == len(set(calibrated)), 'Repeated calibration trial')
    require(set(calibrated) == {r['index'] for r in progress['results'] if r.get('reused')}, 'Calibration reuse differs')
    smoke_bytes = payload['results/smoke/smoke_certificate.json']
    require(digest(smoke_bytes) == plan['smoke_certificate_sha256'], 'Smoke certificate differs')
    require(json.loads(smoke_bytes)['passed'] is True, 'Smoke failed')
    require(audit['simulation_environment'] == plan['provenance']['environment'], 'Original environment differs')
    seeds = pd.read_csv(io.BytesIO(payload[prefix + 'per_seed.csv']))
    summaries = pd.DataFrame(result['rows'])
    members = {c['name']: c['ids'] for c in plan['conditions']}
    expected = {(j['variant']['name'], j['condition'], j['seed']) for j in plan['jobs'] if j['condition'] != 'baseline'}
    require(len(seeds) == 3120 and set(seeds[['variant','condition','seed']].itertuples(index=False, name=None)) == expected, 'Per-seed coverage differs')
    pairs = {(v,c) for v,c,s in expected}
    require(len(summaries) == 104 and set(summaries[['variant','condition']].itertuples(index=False,name=None)) == pairs, 'Summary coverage differs')
    for row in seeds.to_dict('records') + result['rows']:
        check_metrics(row, len(members[row['condition']]))
    for row in result['rows']:
        group = seeds[(seeds.variant == row['variant']) & (seeds.condition == row['condition'])]
        require(row['n_pairs'] == len(group) == 30, 'Wrong pair count')
        for key in ['on_signed_mean_hz', 'mn9_delta_hz']:
            require(np.isclose(row[key], group[key].mean()), 'Signed average mismatch')
        # Absolute value follows averaging in the primary readout; seed means differ.
        for key in ['A', 'on_absolute_sum_hz', 'off_absolute_sum_hz', 'total_absolute_sum_hz']:
            require(row[key] <= group[key].mean() + 1e-7, 'Jensen inequality failed')
        require(row['replicates'] == 2000 and row['seed'] == 630700, 'Bootstrap settings differ')
    contrasts = []
    for variant in plan['variants']:
        v = variant['name']; frame = summaries[summaries.variant == v].set_index('condition')
        for c in ['motor_003','motor_004','motor_005']:
            contrasts.append({'variant': v, 'comparison': c,
                'A_difference': frame.loc['mode','A'] - frame.loc[c,'A'],
                'F_difference': frame.loc['mode','F'] - frame.loc[c,'F']})
    contrasts = pd.DataFrame(contrasts)
    singles = summaries[(summaries.variant == 'default') & (summaries.condition.str.startswith('mode_cell_') | summaries.condition.eq('mn9_only'))].copy()
    singles['root_id'] = singles.condition.map(lambda c: members[c][0])
    maximum = seeds[seeds.variant == 'default'].groupby('condition').total_absolute_sum_hz.max()
    singles['zero_all_seeds'] = singles.condition.map(maximum).eq(0)
    distributions = seeds.groupby(['variant','condition']).total_absolute_sum_hz.agg(['min','median','max','mean']).reset_index()
    elapsed = (pd.Timestamp(audit['finished_utc']) - pd.Timestamp(audit['started_utc'])).total_seconds()
    controller_interval = (pd.Timestamp(progress['updated_utc']) - pd.Timestamp(capacity['created_utc'])).total_seconds()
    facts = {'archive_sha256': digest(Path(archive).read_bytes()), 'payload_sha256': {n:digest(b) for n,b in payload.items()},
        'trials': 3390, 'summaries': 104, 'paired_readouts': 3120,
        'selected_workers': capacity['selected_workers'], 'collection_seconds': elapsed,
        'capacity_certificate_to_controller_finish_seconds': controller_interval,
        'A_positive_comparisons': int(contrasts.A_difference.gt(0).sum()),
        'F_positive_comparisons': int(contrasts.F_difference.gt(0).sum()),
        'zero_response_single_cells': int(singles.zero_all_seeds.sum()),
        'limits': 'Remote collector reports raw-output checks passed. This local audit checks supplied hashes, design, coverage and summary arithmetic; raw spikes/rates and bootstrap intervals cannot be independently recomputed from this bundle.'}
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    (out/'summary_audit.json').write_text(json.dumps(facts,indent=2)+'\n')
    # Keep one compact copy of scientific records alongside the analysis for reproducibility.
    for name in ['results.json','per_seed.csv','jobs.json','capacity.json','collection_environment.json']:
        (out/name).write_bytes(payload[prefix+name])
    contrasts.to_csv(out/'mode_comparisons.csv',index=False)
    singles.to_csv(out/'individual_lesions.csv',index=False)
    distributions.to_csv(out/'seed_response_ranges.csv',index=False)
    secondary_analysis(seeds, out)
    plot(summaries, seeds, out)
    print(json.dumps({k:v for k,v in facts.items() if k!='payload_sha256'},indent=2))


def plot(summary, seeds, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(14,4.4), layout='constrained')
    variants = ['w080_i080','w080_i100','w080_i120','w100_i080','default','w100_i120','w120_i080','w120_i100','w120_i120']
    for c,label,color in [('mode','Mode','#205c93'),('motor_003','Comparison 003','#ae5a22'),('motor_004','Comparison 004','#608a3e'),('motor_005','Comparison 005','#92669e')]:
        f = summary[summary.condition == c].set_index('variant').loc[variants]
        for ax,metric in zip(axes[:2],['A','F']):
            ax.plot(range(9),f[metric],'.-',label=label,color=color)
    for ax in axes[:2]:
        ax.set_xticks(range(9), ['.8/.8','.8/1','.8/1.2','1/.8','1/1','1/1.2','1.2/.8','1.2/1','1.2/1.2'],rotation=60)
        ax.set_xlabel('Overall weight / inhibitory multiplier')
    axes[0].set_ylabel('Within-set mean absolute change A (Hz)')
    axes[1].set_ylabel('Within-set fraction F')
    axes[0].legend(frameon=False,fontsize=8)
    for n,c in enumerate(['mode','mode_without_mn9','mn9_only','motor_003','motor_004','motor_005']):
        y=seeds[(seeds.variant=='w120_i080') & (seeds.condition==c)].total_absolute_sum_hz.to_numpy()
        axes[2].scatter(n+np.linspace(-.15,.15,len(y)),y,s=10,alpha=.65,color='#205c93')
    axes[2].set_xticks(range(6),['Mode','Without MN9','MN9 only','003','004','005'],rotation=60)
    axes[2].set_yscale('log');axes[2].set_ylabel('Per-seed total absolute change (sum of Hz)')
    axes[2].set_title('Weight 1.2 / inhibition 0.8',fontsize=10)
    fig.savefig(out/'ccr_results.png',dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();analyze(args.archive,args.out)
