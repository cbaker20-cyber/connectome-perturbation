#!/usr/bin/env python3
"""Lightweight validation for the living research documentation system."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    'README.md',
    '00_PROJECT_STATE.md',
    '01_LIVING_RESEARCH_LOG.md',
    '02_METHODS_MASTER.md',
    '03_EXPERIMENT_REGISTRY.csv',
    '04_RESULTS_LEDGER.csv',
    '05_CODE_CHANGELOG.md',
    '11_CLAIMS_REGISTER.csv',
]

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main() -> None:
    problems = []
    for name in REQUIRED_FILES:
        if not (ROOT / name).exists():
            problems.append(f'Missing required file: {name}')

    exp_path = ROOT / '03_EXPERIMENT_REGISTRY.csv'
    claim_path = ROOT / '11_CLAIMS_REGISTER.csv'
    result_path = ROOT / '04_RESULTS_LEDGER.csv'

    if exp_path.exists():
        experiments = read_csv(exp_path)
        for row in experiments:
            if not row.get('experiment_id') or not row.get('status'):
                problems.append(f'Experiment row missing id/status: {row}')
            if row.get('status') == 'validated' and not row.get('primary_output'):
                problems.append(f'Validated experiment lacks primary output: {row.get("experiment_id")}')

    if claim_path.exists():
        claims = read_csv(claim_path)
        for row in claims:
            if not row.get('claim_id') or not row.get('claim'):
                problems.append(f'Claim row missing id/claim: {row}')
            if row.get('status', '').startswith('validated') and not row.get('evidence_files'):
                problems.append(f'Validated claim lacks evidence files: {row.get("claim_id")}')

    if result_path.exists() and exp_path.exists():
        exp_ids = {r['experiment_id'] for r in read_csv(exp_path)}
        for row in read_csv(result_path):
            if row.get('experiment_id') not in exp_ids:
                problems.append(f'Result {row.get("result_id")} references unknown experiment {row.get("experiment_id")}')

    if problems:
        print('Documentation validation found problems:')
        for p in problems:
            print(f' - {p}')
        raise SystemExit(1)
    print('Documentation validation passed.')

if __name__ == '__main__':
    main()
