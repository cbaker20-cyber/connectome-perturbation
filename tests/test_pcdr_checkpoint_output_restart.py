"""Fresh-process simulator/output integration on a bounded three-cell fixture."""
import json
from pathlib import Path
import subprocess
import sys
import pandas as pd
from test_pcdr_checkpoint import fixture_files

ROOT=Path(__file__).resolve().parents[1]
PROGRAM=r'''
import sys,json
from pathlib import Path
import numpy as np,pandas as pd
from eigencircuits.common import fingerprint
from scripts import pcdr_checkpoint_worker as w
from scripts.pcdr_checkpoint_sim import simulate,CheckpointSaved
from scripts.pcdr_fine_sim import input_tape
base=Path(sys.argv[1]); action=sys.argv[2]
ids=['720575940643867296','720575940630868793','720575940600000003']
events=pd.DataFrame({'tick':[0,1,9,10,11,20,29,30,39,40,49,59],'flywire_id':[ids[0]]*12})
source=base/'original/trials/source';source.mkdir(parents=True,exist_ok=True)
events.to_parquet(source/'input_events.parquet',index=False)
(source/'manifest.json').write_text('{}')
(base/'original/jobs.json').write_text(json.dumps({'jobs':[dict(trial_id='source',seed=631401,variant=dict(weight_scale=1.,inhibitory_scale=1.))]}))
w.ROOT=base
w.resolution.neuron_ids=lambda:ids
w.resolution.validated=lambda *a:dict(input_ids=[ids[0]],input_digest=fingerprint(events.to_dict('list')),spike_digest='unused',delivered_input_digest='unused')
# The test uses six milliseconds to bound local compute; production duration stays one second.
w.input_tape=lambda *a:np.zeros((80000000,0),dtype=np.int8)
spec=dict(id='fixture',source_trial='source',seed=631401,condition='baseline',lesion_ids=[],dt_ms=.0000125,stage='fine')
with w.owned_attempt(base/'out','baseline',1000) as (attempt,owner):
 try:
  frames=simulate(631401,[0],[],tape=input_tape(events,[ids[0]],.0000125,.006),dt_ms=.0000125,duration_s=.006,chunk_ms=1.,completeness=base/'comp.csv',connectivity=base/'con.parquet',return_delivered=True,checkpoint_dir=base/'checkpoint',stop_after_ms=3 if action=='partial' else 6)
 except CheckpointSaved:
  sys.exit(75)
 if action=='fail_output':
  (attempt/'failure.txt').write_text('injected failure after completed checkpoint')
  raise RuntimeError('injected output failure')
 w.write_outputs(attempt/'trial',spec,frames)
 (attempt/'trial').rename(base/'trial')
'''


def test_final_checkpoint_survives_output_failure_and_fresh_process_recovery(tmp_path):
    fixture_files(tmp_path,dt=.0000125)
    def run(action,code):
        r=subprocess.run([sys.executable,'-c',PROGRAM,str(tmp_path),action],cwd=ROOT,
                         capture_output=True,text=True,timeout=180)
        assert r.returncode==code,r.stdout+'\n'+r.stderr
    run('partial',75)
    run('fail_output',1)
    before=(tmp_path/'checkpoint/latest.json').read_bytes()
    assert not (tmp_path/'trial').exists()
    assert list((tmp_path/'out').glob('segments/baseline/*/failure.txt'))
    run('recover',0)
    assert (tmp_path/'checkpoint/latest.json').read_bytes()==before
    manifest=json.loads((tmp_path/'trial/manifest.json').read_text())
    assert manifest['status']=='complete' and manifest['spike_count']>0
    spikes=pd.read_parquet(tmp_path/'trial/spikes.parquet')
    assert '720575940630868793' in spikes.flywire_id.values
    assert not (tmp_path/'out/segments/baseline/owner.lock').exists()
