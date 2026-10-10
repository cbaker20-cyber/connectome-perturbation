"""Build a new pilot package without rewriting any earlier plan or source."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json,read_json,sha256
from scripts.pcdr_ccr_sensitivity import validated


def make_plan(old, packages):
    anchors=[j for j in old['jobs'] if j['variant']=='default' and j['dt_ms']==.0001
             and j['seed'] in (631401,631402,631403) and j['condition'] in ('baseline','mode')]
    if len(anchors)!=6:raise ValueError('Expected six existing anchor trials')
    jobs=[]
    for dt in (.00005,.000025):
        for a in anchors:
            jobs.append(dict(a,id=f"smaller_{dt}_{a['condition']}_{a['seed']}",dt_ms=dt,stage='smaller'))
    return {'version':1,'created_date':'2026-10-10','deadline_utc':'2026-10-10T16:30:00+00:00',
            'duration_s':1.,'steps_ms':[.0001,.00005,.000025],'mode_ids':old['mode_ids'],
            'criteria':old['criteria'],'anchors':anchors,'jobs':jobs,'packages':packages,
            'pilot_only':True,'original_30_seed_requirement_established':False,
            'probe_duration_s':.01,'workers':1,'scientific_jobs':12}


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists() or args.evidence.exists():raise FileExistsError('New destinations required')
    old=read_json(ROOT/'docs/pcdr/CCR_FINE_PLAN.json')
    fine=ROOT/'results/pcdr/fine_download_20261005'
    archived=fine/'package'
    frozen=read_json(archived/'package_manifest.json')
    original=ROOT/'results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity'
    original_plan=read_json(original/'jobs.json')
    refs=[j for j in old['jobs'] if j['dt_ms']==.0001 and j['variant']=='default'
          and j['seed'] in (631401,631402,631403) and j['condition'] in ('baseline','mode')]
    packages=read_json(fine/'trials'/refs[0]['id']/'manifest.json')['environment']['packages']
    plan=make_plan(old,packages)
    files={}; provenance={}
    code=['model.py','scripts/pcdr_fine_sim.py','scripts/pcdr_fine_ccr.py','scripts/pcdr_resolution.py',
          'scripts/pcdr_followup_sim.py','scripts/pcdr_ccr_capacity.py','scripts/pcdr_ccr_transfer.py',
          'scripts/pcdr_ccr_sensitivity.py','scripts/pcdr_bounded_process.py',
          'eigencircuits/__init__.py','eigencircuits/common.py','eigencircuits/readouts.py','eigencircuits/memory.py']
    for name in code:
        path=archived/name
        if sha256(path)!=frozen[name]:raise ValueError('Archived source changed: '+name)
        files[name]=path.read_bytes();provenance[name]=sha256(path)
    for name in ('2023_03_23_completeness_630_final.csv','2023_03_23_connectivity_630_final.parquet'):
        if sha256(ROOT/name)!=original_plan['provenance']['inputs'][name]:raise ValueError('Frozen data changed: '+name)
        files[name]=(ROOT/name).read_bytes()
    files['requirements-ccr.txt']=(archived/'requirements-ccr.txt').read_bytes()
    if hashlib.sha256(files['requirements-ccr.txt']).hexdigest()!=frozen['requirements-ccr.txt']:
        raise ValueError('Archived requirements changed')
    inputs={}
    by_id={j['trial_id']:j for j in original_plan['jobs']}
    for anchor in refs:
        name=anchor['source_trial'];source=original/'trials'/name
        m=validated(source,by_id[name],original_plan)
        inputs[anchor['seed'],anchor['condition']]=m['input_digest']
        for path in source.iterdir():
            if path.is_file():files['original/trials/'+name+'/'+path.name]=path.read_bytes()
        ref=fine/'trials'/anchor['id'];record=read_json(ref/'manifest.json')
        if record['status']!='complete' or record['spec']!=anchor or record['environment']['packages']!=packages:
            raise ValueError('Incomplete/different anchor or environment')
        if record['source_manifest_sha256']!=sha256(source/'manifest.json') or record['physical_input_digest']!=m['input_digest']:
            raise ValueError('Anchor does not match original input source')
        for name,digest in record['outputs'].items():
            if sha256(ref/name)!=digest:raise ValueError('Anchor output changed: '+str(ref/name))
            files['anchors/'+anchor['id']+'/'+name]=(ref/name).read_bytes()
        files['anchors/'+anchor['id']+'/manifest.json']=(ref/'manifest.json').read_bytes()
    if any(inputs[s,'baseline']!=inputs[s,'mode'] for s in (631401,631402,631403)):
        raise ValueError('Baseline/mode scheduled inputs differ')
    files['original/jobs.json']=(original/'jobs.json').read_bytes()
    files['anchor_plan.json']=(ROOT/'docs/pcdr/CCR_FINE_PLAN.json').read_bytes()
    for name in ('scripts/pcdr_smaller_pilot.py','tests/test_pcdr_smaller_pilot.py'):
        files[name]=(ROOT/name).read_bytes()
    files['run_all.sh']=(ROOT/'scripts/pcdr_smaller_run_all.sh').read_bytes().replace(b'\r\n',b'\n')
    files['START_HERE.md']=(ROOT/'docs/pcdr/SMALLER_STEP_PILOT_20261010.md').read_bytes()
    files['smaller_plan.json']=(json.dumps(plan,indent=2)+'\n').encode()
    files['source_provenance.json']=(json.dumps({'archived_source_sha256':provenance,
        'fine_archive_sha256':read_json(ROOT/'results/pcdr/fine_verified_20261005/full_check.json')['archive_sha256'],
        'original_jobs_sha256':sha256(original/'jobs.json'),'anchor_plan_sha256':sha256(ROOT/'docs/pcdr/CCR_FINE_PLAN.json')},indent=2)+'\n').encode()
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
    files['package_manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    temp=args.out.with_suffix('.zip.tmp')
    if temp.exists():raise FileExistsError('Temporary package already exists')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in sorted(files.items()):z.writestr('connectome_smaller_pilot/'+name,data)
    with zipfile.ZipFile(temp) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC failure')
        for name,digest in manifest.items():
            if hashlib.sha256(z.read('connectome_smaller_pilot/'+name)).hexdigest()!=digest:raise ValueError('Package hash mismatch')
    temp.rename(args.out)
    atomic_json(args.evidence,{'archive_sha256':sha256(args.out),'archive_bytes':args.out.stat().st_size,
                'member_count':len(files),'scientific_jobs':12,'anchors':6,'prefix_jobs':4,
                'all_member_hashes_checked':True,'original_source_reused':True,'launched':False})
    print(args.out, args.out.stat().st_size,'bytes; not launched',flush=True)


if __name__=='__main__':main()
