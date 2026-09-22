"""Write an all-target findings table from completed studies, without a model call."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json, now, sha256


def report(study):
    import pandas as pd
    study=Path(study)
    summary=json.loads((study/'summary.json').read_text())
    if summary['status']!='complete': raise ValueError('Study is incomplete')
    results=json.loads((study/'analysis/results.json').read_text())
    lines=['# Local study findings','', 'Generated: '+now(),'',
           'Phase: '+summary['phase'], '',
           'These are changes in a connectome-constrained simulation. MN9 is not a direct measurement of feeding behavior.', '',
           '| Role | Target | Paired seeds | MN9 change (Hz) | Total motor change (Hz) | Mean motor change (Hz) | A (Hz) | F |',
           '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in results:
        target=r['support_ids'][0] if len(r['support_ids'])==1 else r['condition']
        concentration='undefined' if r['F'] is None else f"{r['F']:.4f}"
        lines.append(f"| {r['role']} | {target} | {r['n_pairs']} | {r['mn9_delta_hz']:.3f} | {r['motor_total_delta_hz']:.3f} | {r['motor_mean_delta_hz']:.3f} | {r['A']:.3f} | {concentration} |")
    secondary=study/'analysis/secondary_tests.parquet'
    if secondary.exists():
        table=pd.read_parquet(secondary)
        lines+=['','## Secondary single-cell tests','','BH correction includes all 20 cells × 2 endpoints. Cells and time bins are not independent replicates.', '',
                '| Condition | Readout | Mean change (Hz) | p | BH q |','|---|---|---:|---:|---:|']
        for row in table.to_dict('records'):
            lines.append(f"| {row['condition']} | {row['readout']} | {row['delta_hz']:.3f} | {row['p']:.5f} | {row['q_bh']:.5f} |")
        lines+=['','A small adjusted p-value supports a simulated effect for that selected cell under these seeds. It does not establish an eigen-set advantage or a general E/I population effect.']
    if summary['phase']=='local_mode_pilot':
        lines+=['','Only five controls and five seeds: exploratory evidence, not the prespecified confirmation. The best possible corrected reference p-value is 1/6.',
                'See pilot_comparison.json for the conditional matched-reference comparison.']
    lines+=['','All targets are shown; the table is not filtered for favorable findings.',
            'Full per-neuron footprints, paired-seed intervals for A/F, and input/source manifest hashes are in analysis/results.json and its referenced files.']
    (study/'FINDINGS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    atomic_json(study/'findings_manifest.json',{'created_utc':now(),'report_sha256':sha256(study/'FINDINGS.md'),
        'results_sha256':sha256(study/'analysis/results.json'),'summary_sha256':sha256(study/'summary.json'),
        'code_sha256':sha256(__file__),'command':f'python scripts/pcdr_local_findings.py --study {study}'})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--study',required=True);report(p.parse_args().study)
