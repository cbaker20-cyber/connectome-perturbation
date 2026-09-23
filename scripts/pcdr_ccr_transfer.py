"""Freeze a portable source/data snapshot and run four deployment checks.

This prepares and tests files; it never contacts CCR or submits jobs.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA = ['2023_03_23_completeness_630_final.csv',
        '2023_03_23_connectivity_630_final.parquet', 'flywire_annotations.tsv']
PACKAGES = ['numpy','scipy','pandas','pyarrow','brian2','Cython','matplotlib',
            'psutil','pytest','statsmodels','joblib']
OUTPUTS = {'spikes.parquet','rates.parquet','input_events.parquet',
           'delivered_events.parquet','source_snapshot.zip','environment.json'}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(temp,path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def package_versions():
    versions={}
    for name in PACKAGES:
        try: versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name]=None
    return versions


def dependency_versions():
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    pending=[name for name,version in package_versions().items() if version is not None]
    versions={}
    while pending:
        name=canonicalize_name(pending.pop())
        if name in versions: continue
        versions[name]=importlib.metadata.version(name)
        for line in importlib.metadata.requires(name) or []:
            requirement=Requirement(line)
            if requirement.marker is None or requirement.marker.evaluate(
                {'extra':'','sys_platform':'linux','os_name':'posix','platform_system':'Linux'}):
                pending.append(requirement.name)
    return dict(sorted(versions.items()))


def safe_path(root, relative):
    p=PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe manifest path')
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path leaves snapshot')
    return path


def verify(root=ROOT):
    manifest=read(root/'transfer_manifest.json')
    for relative, expected in manifest['files'].items():
        path=safe_path(root,relative)
        if not path.is_file() or digest(path)!=expected:
            raise ValueError(f'Snapshot file changed or missing: {relative}')
    return manifest


def build(out,expanded=False):
    out=Path(out).resolve(); out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'connectome'; snapshot.mkdir()
    files={ROOT/'model.py', ROOT/'scripts/pcdr_ccr_transfer.py', ROOT/'scripts/pcdr_ccr_smoke.sh',
           ROOT/'scripts/pcdr_ccr_sensitivity.py',ROOT/'scripts/pcdr_bounded_process.py'}
    if expanded:files.add(ROOT/'scripts/pcdr_ccr_capacity.py')
    for folder in ['eigencircuits','perturbation','tools']:
        files.update((ROOT/folder).rglob('*.py'))
    files.update(ROOT/x for x in DATA)
    for optional in ['LICENSE','data/input_manifest.json','docs/pcdr/CCR_RUNBOOK.md']:
        if (ROOT/optional).exists(): files.add(ROOT/optional)
    for source in sorted(files):
        if '__pycache__' in source.parts: continue
        dest=snapshot/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,dest)
    notebook='CCR_Expanded_Study.ipynb' if expanded else 'CCR_Preliminary_Followup.ipynb'
    guide='CCR_EXPANDED_GUIDE.md' if expanded else 'CCR_NOTEBOOK_GUIDE.md'
    design='CCR_EXPANDED_DESIGN.json' if expanded else 'CCR_SENSITIVITY_DESIGN.json'
    for source,dest in [('notebooks/'+notebook,notebook),
                        ('docs/pcdr/'+guide,'START_HERE.md'),
                        ('docs/pcdr/'+design,'sensitivity_design.json')]:
        shutil.copyfile(ROOT/source,snapshot/dest)
    versions=package_versions()
    dependencies=dependency_versions()
    (snapshot/'requirements-ccr.txt').write_text(
        '# Transfer target from the working local environment; validate Linux wheels separately.\n'+
        '\n'.join(f'{name}=={version}' for name,version in dependencies.items())+'\n',encoding='utf-8')
    (snapshot/'ccr_config.example.sh').write_text(
        '# Fill in actual allocation and module/venv paths before use.\n'
        'export CCR_ACCOUNT=\nexport CCR_CLUSTER=\nexport CCR_PARTITION=\n'
        'export CCR_PYTHON=\n# Load your actual Python module here if required.\n',encoding='utf-8')
    (snapshot/'.gitignore').write_text('results/\n.ccr-venv/\n__pycache__/\n*.pyc\n*.zip\n'+ '\n'.join(DATA)+'\n',encoding='utf-8')
    manifest={'created_utc':utc(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'source_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
              'python':sys.version,'packages':versions,'dependency_versions':dependencies,
              'purpose':'Exact-byte deployment snapshot. New environment and smoke plan are recorded on the destination. No confirmation study or submission authorization certificate.',
              'editable_files':{name:digest(snapshot/name) for name in [notebook,'ccr_config.example.sh']},
              'files':{p.relative_to(snapshot).as_posix():digest(p) for p in sorted(snapshot.rglob('*'))
                       if p.is_file() and p.name not in [notebook,'ccr_config.example.sh']}}
    write(snapshot/'transfer_manifest.json',manifest)
    verify(snapshot)
    archive=out/'Connectome_CCR_Notebook.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
        for path in sorted(snapshot.rglob('*')):
            if path.is_file(): zipped.write(path,arcname='connectome/'+path.relative_to(snapshot).as_posix())
    write(out/'archive.json',{'archive':archive.name,'sha256':digest(archive),'bytes':archive.stat().st_size,
                            'manifest_sha256':digest(snapshot/'transfer_manifest.json')})
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size}))


def initialize():
    verify()
    if (ROOT/'.git').exists():
        raise FileExistsError('Snapshot Git repository already exists')
    subprocess.run(['git','init'],cwd=ROOT,check=True)
    # common.provenance expects Git. This technical snapshot is not project history.
    subprocess.run(['git','-c','core.autocrlf=false','add','.'],cwd=ROOT,check=True)
    subprocess.run(['git','-c','user.name=Research transfer snapshot',
                    '-c','user.email=snapshot@localhost','commit','-m',
                    'Record exact files in the transfer snapshot'],cwd=ROOT,check=True,capture_output=True)


def prepare(study):
    transfer=verify()
    versions=package_versions()
    if versions!=transfer['packages']:
        raise ValueError('Package versions differ; document and build a new amended snapshot')
    if any(importlib.metadata.version(name)!=version for name,version in transfer['dependency_versions'].items()):
        raise ValueError('Dependency versions differ from transfer snapshot')
    from eigencircuits.common import provenance, MN9
    study=Path(study); study.mkdir(parents=True,exist_ok=False)
    jobs=[{'trial_id':name,'seed':631301,'context':context,'lesion_ids':lesion}
          for name,context,lesion in [('baseline','sugar',[]),('replay','sugar',[]),
                                     ('no_input','no_input',[]),('lesion','sugar',[MN9])]]
    write(study/'jobs.json',{'created_utc':utc(),'purpose':'Technical deployment smoke only',
                           'transfer_sha256':digest(ROOT/'transfer_manifest.json'),
                           'provenance':provenance(),'jobs':jobs})


def load_plan(study):
    verify()
    plan=read(Path(study)/'jobs.json')
    if digest(ROOT/'transfer_manifest.json')!=plan['transfer_sha256']:
        raise ValueError('Transfer manifest changed')
    from eigencircuits.common import provenance
    current=provenance()
    for field in ['inputs','sources','environment']:
        if current[field]!=plan['provenance'][field]:
            raise ValueError(f'Environment or inputs changed since preparation: {field}')
    return plan


def worker(study,index):
    from eigencircuits.trials import trial
    study=Path(study); plan=load_plan(study)
    if index<0 or index>=len(plan['jobs']): raise ValueError('Job index outside plan')
    job=plan['jobs'][index]
    lock=study/(job['trial_id']+'.lock')
    with lock.open('x') as stream: stream.write(f'{os.getpid()} {utc()}\n')
    try:
        trial(study/'trials'/job['trial_id'],backend='numpy',**job)
    finally:
        lock.unlink()


def checked_trial(directory,job,plan):
    m=read(directory/'manifest.json')
    if m.get('status')!='complete': raise ValueError('Incomplete trial')
    for field,value in job.items():
        if m.get(field)!=value: raise ValueError(f'Trial differs from planned {field}')
    for field in ['inputs','sources','environment']:
        if m['provenance'][field]!=plan['provenance'][field]: raise ValueError('Trial provenance mismatch')
    if set(m['outputs'])!=OUTPUTS: raise ValueError('Required outputs missing from manifest')
    for name,expected in m['outputs'].items():
        if digest(directory/name)!=expected: raise ValueError(f'Corrupt output: {name}')
    for field,value in {'backend':'numpy','input_protocol':'fixed_binomial_tape_v1',
                        'duration_s':1.,'dt_ms':.1,'input_hz':150.,'weight_scale':1.,
                        'inhibitory_scale':1.,'strong_fraction':None}.items():
        if m.get(field)!=value: raise ValueError(f'Unexpected simulation parameter: {field}')
    return m


def collect(study):
    import pandas as pd
    import numpy as np
    from eigencircuits.common import neuron_ids, sugar_ids, fingerprint
    study=Path(study); plan=load_plan(study)
    ids=neuron_ids(); frames={}; manifests={}
    for job in plan['jobs']:
        directory=study/'trials'/job['trial_id']
        if (study/(job['trial_id']+'.lock')).exists(): raise ValueError('Job still locked')
        m=checked_trial(directory,job,plan)
        tables={name:pd.read_parquet(directory/(name+'.parquet')) for name in ['spikes','rates','input_events','delivered_events']}
        rates=tables['rates']; spikes=tables['spikes']
        if rates.root_id.astype(str).tolist()!=ids: raise ValueError('Incomplete or reordered neuron universe')
        actual=spikes.groupby('flywire_id').size().reindex(ids,fill_value=0).to_numpy()
        if not np.array_equal(actual,rates.spike_count) or not np.array_equal(actual,rates.rate_hz):
            raise ValueError('Spikes and one-second rates disagree')
        if len(spikes)!=m['spike_count'] or not set(spikes.flywire_id)<=set(ids): raise ValueError('Invalid spikes')
        if len(spikes) and (set(spikes.trial)!={job['trial_id']} or not spikes.t.between(0,1,inclusive='left').all()):
            raise ValueError('Invalid spike metadata')
        expected_inputs=sugar_ids() if job['context']=='sugar' else []
        if m['input_ids']!=expected_inputs: raise ValueError('Wrong inputs')
        for name,key in [('input_events','input_digest'),('delivered_events','delivered_input_digest')]:
            if fingerprint(tables[name].to_dict('list'))!=m[key]: raise ValueError('Event digest mismatch')
        if fingerprint(spikes[['t','flywire_id']].to_dict('list'))!=m['spike_digest']: raise ValueError('Spike digest mismatch')
        scheduled=set(map(tuple,tables['input_events'][['tick','flywire_id']].to_numpy()))
        delivered=set(map(tuple,tables['delivered_events'][['tick','flywire_id']].to_numpy()))
        if not delivered<=scheduled: raise ValueError('Delivered event not scheduled')
        manifests[job['trial_id']]=m; frames[job['trial_id']]=tables
    for name in ['replay','lesion']:
        if not frames['baseline']['input_events'].equals(frames[name]['input_events']): raise ValueError('Scheduled input mismatch')
    for name in ['rates','delivered_events']:
        if not frames['baseline'][name].equals(frames['replay'][name]): raise ValueError('Replay mismatch')
    if not frames['baseline']['spikes'][['t','flywire_id']].equals(frames['replay']['spikes'][['t','flywire_id']]):
        raise ValueError('Replay spike mismatch')
    if any(len(frames['no_input'][name]) for name in ['spikes','input_events','delivered_events']):
        raise ValueError('Undriven activity')
    result={'finished_utc':utc(),'passed':True,'location':'CCR' if os.environ.get('SLURM_JOB_ID') else 'local',
            'interpretation':'Technical smoke only; no scientific confirmation or scheduler fault-tolerance claim.',
            'jobs_sha256':digest(study/'jobs.json'),'neurons':len(ids),
            'trials':{name:{key:m[key] for key in ['wall_seconds','peak_rss_bytes','spike_count','mn9_hz']} for name,m in manifests.items()},
            'output_bytes':sum(p.stat().st_size for p in (study/'trials').rglob('*') if p.is_file())}
    write(study/'smoke_certificate.json',result)
    print(json.dumps(result))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['build','verify','initialize','prepare','worker','collect'])
    parser.add_argument('--out'); parser.add_argument('--study'); parser.add_argument('--index',type=int)
    parser.add_argument('--expanded',action='store_true')
    args=parser.parse_args()
    if args.action=='build':
        if not args.out: parser.error('--out required')
        build(args.out,args.expanded)
    elif args.action=='verify': print(json.dumps({'verified_files':len(verify()['files'])}))
    elif args.action=='initialize': initialize()
    else:
        if not args.study: parser.error('--study required')
        if args.action=='worker':
            if args.index is None: parser.error('--index required')
            worker(args.study,args.index)
        else: globals()[args.action](args.study)


if __name__=='__main__': main()
