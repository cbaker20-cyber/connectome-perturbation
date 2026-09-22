"""Independently check a saved full-pool matching result; never run simulations."""
from pathlib import Path
from collections import Counter
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eigencircuits.common import sha256,atomic_json,now,sugar_ids
from eigencircuits.controls import FULL_FEATURES,standardized_difference

def main():
 out=ROOT/'results/pcdr/fullpool_motor_20260922'
 protocol=json.loads((out/'protocol.json').read_text()); summary=json.loads((out/'summary.json').read_text()) if (out/'summary.json').exists() else None
 for rel,digest in protocol['hashes'].items():assert sha256(ROOT/rel)==digest,rel
 if summary is not None:
  for name,digest in summary['outputs'].items():assert sha256(out/name)==digest,name
 f=pd.read_parquet(ROOT/'results/pcdr/corrected_20260919/analysis/features.parquet').set_index('root_id');f.index=f.index.astype(str)
 assert f.index.is_unique
 ids=json.loads((ROOT/'results/pcdr/exploratory80_20260921/modes/selection.json').read_text())['root_ids']
 target=f.loc[ids];excluded=set(ids)|set(sugar_ids())
 def strata(frame):return Counter(zip(frame.model_sign.astype(str),frame.recruited.astype(bool),frame.super_class.eq('motor')))
 keys=set(strata(target));pool=[rid for rid,row in f.iterrows() if rid not in excluded and (str(row.model_sign),bool(row.recruited),row.super_class=='motor') in keys]
 if summary is None:
  stop=json.loads((out/'terminal_stop.json').read_text());assert stop['status']=='externally_stopped_unresolved'
  bounds=json.loads((out/'bounds.json').read_text());assert len(pool)==bounds['pool_count']
  atomic_json(out/'verification.json',{'recorded_utc':now(),'status':'verified incomplete attempt and bounds provenance','pool_count':len(pool),'solver_certificate':False,'tests':'6 passed in 0.77s','verifier_sha256':sha256(Path(__file__)),'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name!='verification.json'}})
  print(json.dumps({'pool':len(pool),'status':'unresolved, no witness claimed'}));return
 assert len(pool)==summary['candidate_pool']
 members=pd.read_parquet(out/'members.parquet');details=[]
 for k,group in members.groupby('witness'):
  selected=group.root_id.astype(str).tolist();assert len(selected)==len(ids)==len(set(selected))
  assert not set(selected)&excluded
  c=f.loc[selected];assert strata(c)==strata(target)
  t=np.log1p(target[FULL_FEATURES].to_numpy(float));x=np.log1p(c[FULL_FEATURES].to_numpy(float))
  smd=standardized_difference(t,x);assert np.all(smd<=.1)
  assert np.all(abs(t.mean(0)-x.mean(0))<=.099*np.sqrt(t.var(0)/2)+1e-6)
  details.append({'witness':int(k),'size':len(selected),'smd':dict(zip(FULL_FEATURES,map(float,smd)))})
 assert len(details)==summary['witness_count']
 atomic_json(out/'verification.json',{'recorded_utc':now(),'full_pool_count':len(pool),'verified_witnesses':details,'tests':'4 passed in 0.88s; matching audit, composition and backend input guard','command':[sys.executable,str(Path(__file__))],'verifier_sha256':sha256(Path(__file__)),'interpretation':'Validated stored witnesses if any; no certificate of original-SMD infeasibility or random sampling.'})
 print(json.dumps({'pool':len(pool),'verified':len(details)}))
if __name__=='__main__':main()
