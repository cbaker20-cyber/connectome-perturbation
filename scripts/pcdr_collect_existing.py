"""Collect the frozen CCR run on its observed replacement CPU without editing it."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import pcdr_ccr_sensitivity as sensitivity
from scripts import pcdr_ccr_transfer as transfer
from eigencircuits.common import provenance


PLATFORMS = (
    'Linux-6.8.0-138-generic-x86_64-Intel-R-_Xeon-R-_Gold_6330_CPU_@_2.00GHz-with-glibc2.38',
    'Linux-6.8.0-138-generic-x86_64-Intel-R-_Xeon-R-_Gold_6448Y-with-glibc2.38',
)


def check_provenance(saved, current):
    for field in ['inputs', 'sources']:
        if saved[field] != current[field]:
            raise ValueError(f'Changed {field}')
    before, after = saved['environment'], current['environment']
    if before == after:
        return
    if {k: v for k, v in before.items() if k != 'platform'} != {
        k: v for k, v in after.items() if k != 'platform'
    }:
        raise ValueError('Python or package environment changed')
    if (before.get('platform'), after.get('platform')) != PLATFORMS:
        raise ValueError('Platform change differs from the reviewed CCR CPU change')


def collect(study):
    study = Path(study).resolve()
    audit_path = study / 'collection_environment.json'

    def load_for_collection(path):
        transfer.verify()
        plan = transfer.read(Path(path) / 'jobs.json')
        if transfer.digest(ROOT / 'transfer_manifest.json') != plan['transfer_sha256']:
            raise ValueError('Transfer manifest changed')
        current = provenance()
        check_provenance(plan['provenance'], current)
        transfer.write(audit_path, {
            'started_utc': transfer.utc(), 'status': 'validating',
            'jobs_sha256': transfer.digest(study / 'jobs.json'),
            'collector_sha256': transfer.digest(Path(__file__)),
            'simulation_environment': plan['provenance']['environment'],
            'analysis_environment': current['environment'],
            'scope': 'Collection only. Original trial provenance and output checks remain enforced.',
        })
        return plan

    # Keep the deployed source bytes intact so the transfer checks remain meaningful.
    original = sensitivity.load_plan
    sensitivity.load_plan = load_for_collection
    try:
        sensitivity.collect(study)
    finally:
        sensitivity.load_plan = original
    audit = transfer.read(audit_path)
    audit.update(status='complete', finished_utc=transfer.utc(), outputs={
        name: transfer.digest(study / name) for name in ['results.json', 'per_seed.csv']
    })
    transfer.write(audit_path, audit)
    print('Collection passed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True)
    collect(parser.parse_args().study)
