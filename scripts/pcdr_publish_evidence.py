"""Copy a small, explicit set of completed research records into version control."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, sha256

OUT = ROOT/'docs/pcdr/evidence/2026-09-22'
SOURCES = {
    'corrected_20260919': ['replay_check.json', 'analysis/selection.json', 'analysis/baseline_summary.json', 'analysis/correlation_summary.json'],
    'ccr_singles_20260919': ['summary.json', 'analysis/secondary_tests.parquet'],
    'exploratory80_20260921': ['modes/selection.json'],
    'optimized_pilot_20260921': ['amendment.json', 'analysis/results.json', 'per_seed_readouts.csv', 'completion_audit.json'],
    'seed_replication_20260921': ['amendment.json', 'analysis/results.json', 'per_seed_readouts.csv', 'completion_audit.json'],
    'fullpool_relaxation_20260922': ['protocol.json', 'execution.json', 'conservative/result.json', 'necessary_outer/result.json',
                                  'binary_completion/protocol.json', 'binary_completion/summary.json', 'binary_completion/assignments.csv',
                                  'binary_completion/members.parquet', 'binary_completion/verification.json'],
    'motor_set_audit_20260922': ['protocol.json', 'summary.json', 'distributions.csv', 'composition.csv', 'composition_distances.csv', 'annotated_members.csv'],
    'motor_composition_pilot_20260922': ['amendment.json', 'jobs.json', 'summary.json', 'analysis/results.json',
                                       'completion_audit.json', 'per_seed_readouts.csv', 'paired_contrasts.json',
                                       'response_duplicates/protocol.json', 'response_duplicates/summary.json', 'response_duplicates/varying_cell_rates.csv'],
}


def main():
    import pandas as pd
    source_dir = ROOT/'results/pcdr'
    audit = json.loads((source_dir/'motor_composition_pilot_20260922/completion_audit.json').read_text())
    assert audit['trials_verified'] == 55 and audit['scheduled_input_pairs_verified'] == 50
    for rel, digest in audit['analysis_hashes'].items():
        assert sha256(source_dir/'motor_composition_pilot_20260922'/rel) == digest, rel
    paths = [(study, relative, source_dir/study/relative) for study, files in SOURCES.items() for relative in files]
    assert all(p.is_file() for _, _, p in paths), [str(p) for _, _, p in paths if not p.is_file()]
    OUT.mkdir(parents=True, exist_ok=False)
    records = []
    for study, relative, source in paths:
        target = OUT/study/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = sha256(source)
        assert sha256(target) == digest
        records.append({'source': str(source.relative_to(ROOT)).replace('\\', '/'),
                        'published': str(target.relative_to(OUT)).replace('\\', '/'),
                        'sha256': digest, 'bytes': source.stat().st_size})
        if source.suffix == '.parquet':
            pd.read_parquet(source).to_csv(target.with_suffix('.csv'), index=False)
            records.append({'derived_from': str(source.relative_to(ROOT)).replace('\\', '/'),
                            'published': str(target.with_suffix('.csv').relative_to(OUT)).replace('\\', '/'),
                            'sha256': sha256(target.with_suffix('.csv')), 'format': 'CSV view; root IDs are exact strings'})
    atomic_json(OUT/'manifest.json', {'created_utc': now(), 'purpose': 'Compact committed evidence, not a substitute for full trial archives.',
                'records': records, 'exporter_sha256': sha256(Path(__file__))})
    (OUT/'README.md').write_text(
        '# Research evidence snapshot, 22 September 2026\n\n'
        'These are selected completed records copied from the local results directory. The manifest records original paths, exact hashes and exported paths. CSV copies accompany small parquet tables for reading on GitHub. Read neuron IDs as strings; spreadsheet rounding would corrupt them.\n\n'
        'Includes original input-pairing checks, single-cell test table, the frozen exploratory mode, the five-seed pilot, its separate thirty-seed replication, motor-matching feasibility, the pre-lesion distribution audit and the completed motor-composition pilot. Every result retains its limitations. Comparison sets are optimized, overlap, and do not constitute a calibrated random null.\n\n'
        'The complete spikes, input-event tapes, per-neuron trial rates, source ZIPs and full footprints remain in local results/pcdr. This compact snapshot alone cannot independently reproduce every rate from spikes. Its completion audits identify the full archived evidence by hash. No raw connectome files are duplicated here. Historical absolute paths in manifests refer to the original local machine.\n', encoding='utf-8')
    print(json.dumps({'files': len(records), 'bytes': sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())}))


if __name__ == '__main__':
    main()
