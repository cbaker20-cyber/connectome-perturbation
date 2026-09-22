"""Bounded fresh-input-seed replication of the six frozen lesion sets."""
from pathlib import Path
import sys,time,json,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eigencircuits.common import read_json,atomic_json,sha256,now,provenance
from scripts import pcdr_optimized_pilot as controller
S=ROOT/'results/pcdr/seed_replication_20260921'
OLD=ROOT/'results/pcdr/optimized_pilot_20260921'

def prepare():
    assert read_json(OLD/'completion_record.json')['trials']==35
    old=read_json(OLD/'jobs.json');actual=provenance()
    for field in ['inputs','sources']:assert actual[field]==old['provenance'][field]
    seeds=list(range(631001,631031))
    assert not any(read_json(p).get('seed') in seeds for p in (ROOT/'results/pcdr').glob('*/trials/*/manifest.json'))
    S.mkdir(exist_ok=False)
    deadline=time.time()+6*3600
    amendment={'recorded_utc':now(),'authorization':'User authorized light autonomous tests until morning; CCR expected Tuesday.',
      'design':'Fresh-seed replication, conditional on the six previously fixed lesion sets. Not new modes or random controls.',
      'seeds':seeds,'trials':210,'deadline_epoch':deadline,'limit':'Six hours maximum, one serial worker, existing memory/disk guards. Stop on failure or deadline; no automatic extension.',
      'selection':'Identical eigen-set and five optimized sets from prior pilot. No changes after results.',
      'readouts':'Same A,F,MN9,total/per-neuron motor, full footprints and paired-seed bootstrap. Report all sets; no p-values. Keep this 30-seed dataset separate from the prior five seeds.',
      'interpretation':'Tests stability across stochastic inputs only; does not resolve optimized-reference sampling or cell-class/MN9 imbalance.',
      'source_jobs_sha256':sha256(OLD/'jobs.json'),'controller_sha256':sha256(controller.__file__),
      'code_sha256':sha256(__file__)}
    atomic_json(S/'amendment.json',amendment)
    jobs=[]
    for seed in seeds:
      for c in old['conditions']:
        jobs.append({'index':len(jobs),'condition':c['name'],'role':c['role'],'lesion_ids':c['ids'],'seed':seed,
                     'variant':old['variants'][0],'trial_id':f"default_{c['name']}_{seed}"})
    plan={**old,'phase':'optimized_seed_replication','claim_status':'conditional_seed_replication_not_confirmation',
       'created_utc':now(),'jobs':jobs,'seeds':seeds,'n_jobs':210,'amendment_sha256':sha256(S/'amendment.json'),
       'provenance':actual,'status':'prepared_not_submitted'}
    assert len({j['trial_id'] for j in jobs})==210
    atomic_json(S/'jobs.json',plan)
    atomic_json(S/'local_status.json',{'started_utc':now(),'deadline_epoch':deadline,'status':'starting','completed':0,'total':210})
    print(json.dumps({'prepared':210,'deadline_epoch':deadline}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');a=p.parse_args()
    if a.prepare:prepare()
    else:
      assert sha256(controller.__file__)==read_json(S/'amendment.json')['controller_sha256']
      controller.STUDY=S
      controller.run()
