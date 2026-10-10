"""Add a separate four-worker execution protocol to the verified frozen pilot."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT/'results/pcdr/four_trial_validation_20261010/source_pilot.zip'
    expected = '33c0db11ab9315de5d343a9a73b90986c256cb7e2451a615093c69c057e24476'
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Original pilot upload differs')
    target = ROOT/'results/pcdr/four_trial_validation_20261010/candidate.zip'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(target)
    with zipfile.ZipFile(source) as z:
        if z.testzip() is not None:
            raise ValueError('Source ZIP CRC failure')
        files = {n.removeprefix('connectome_smaller_pilot/'): z.read(n) for n in z.namelist()}
    original = json.loads(files.pop('package_manifest.json'))
    for name, digest in original.items():
        if hashlib.sha256(files[name]).hexdigest() != digest:
            raise ValueError('Original member differs: '+name)
    files['original_pilot_manifest.json'] = (json.dumps(original, indent=2)+'\n').encode()
    files['original_run_all.sh'] = files['run_all.sh']
    files['original_START_HERE.md'] = files['START_HERE.md']
    for name in ('scripts/pcdr_four_trial.py', 'tests/test_pcdr_four_trial.py'):
        files[name] = (ROOT/name).read_bytes()
    files['run_all.sh'] = (ROOT/'scripts/pcdr_four_run_all.sh').read_bytes().replace(b'\r\n', b'\n')
    files['START_HERE.md'] = (ROOT/'docs/pcdr/FOUR_TRIAL_RUN_20261010.md').read_bytes()
    files['execution_plan.json'] = (json.dumps({
        'version': 1, 'seed': 631401, 'workers': 4, 'scientific_trials': 4,
        'minimum_cpus': 8, 'minimum_memory_mb': 92000, 'maximum_controller_hours': 70,
        'allocation_reserve_seconds': 900, 'worker_address_space_limit_bytes': 20_000_000_000,
        'old_deadline_superseded_for_this_execution_only': True,
        'original_plan_unchanged': True, 'source_upload_sha256': expected,
        'criteria_unchanged': True, 'reference_prefixes': 2, 'concurrent_capacity_prefixes': 4,
        'scientific_panel': 'seed631401 baseline/mode at0.00005/0.000025ms,1second each',
        'relaunch': 'Refuse existing results; retain failures, no automatic restart or duplicate trial.',
        'capacity_rule': 'Two times slowest concurrent10ms prefix at each step scaled to1second; all4must fit.'
    }, indent=2)+'\n').encode()
    manifest = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
    files['package_manifest.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(files.items()):
            z.writestr('connectome_four_trial/'+name, data)
    print(target)


if __name__ == '__main__':
    main()
