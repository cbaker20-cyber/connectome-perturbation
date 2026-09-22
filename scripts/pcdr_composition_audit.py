"""Baseline-only distribution and motor-stratum capacity audit; no new lesions."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eigencircuits.common import atomic_json,now,sha256,sugar_ids
from eigencircuits.controls import FULL_FEATURES,standardized_difference

def ecdf_gap(a,b):
    a,b=np.sort(a),np.sort(b)
    points=np.unique(np.r_[a,b])
    return float(np.max(abs(np.searchsorted(a,points,side='right')/len(a)-np.searchsorted(b,points,side='right')/len(b))))

def main():
    out=ROOT/'results/pcdr/composition_audit_20260922';out.mkdir(exist_ok=False)
    fp=ROOT/'results/pcdr/corrected_20260919/analysis/features.parquet'
    jp=ROOT/'results/pcdr/optimized_pilot_20260921/jobs.json'
    atomic_json(out/'protocol.json',{'recorded_utc':now(),'command':[sys.executable,str(Path(__file__).resolve())],
      'scope':'Use only frozen baseline features and lesion IDs. Describe ECDF gaps, quantiles, variances and annotation composition; check exact sign/recruitment/motor capacity. No significance tests or new balance cutoff.',
      'limitation':'Capacity is necessary, not sufficient for joint matching. Post-pilot diagnostic cannot retroactively amend original criteria.',
      'sha256':{str(p):sha256(p) for p in [fp,jp,Path(__file__)]}})
    f=pd.read_parquet(fp).set_index('root_id');f.index=f.index.astype(str)
    plan=json.loads(jp.read_text());conditions=[c for c in plan['conditions'] if c['role']!='baseline']
    target=f.loc[conditions[0]['ids']];rows=[];classes=[]
    for c in conditions:
      sample=f.loc[c['ids']]
      for label in ['super_class','model_sign','recruited']:
        for value,count in sample[label].fillna('unavailable').value_counts().items():
          classes.append({'condition':c['name'],'field':label,'value':str(value),'count':int(count)})
      for col in FULL_FEATURES:
        a=np.log1p(target[col].to_numpy(float));b=np.log1p(sample[col].to_numpy(float))
        rows.append({'condition':c['name'],'feature':col,'smd':float(standardized_difference(a[:,None],b[:,None])[0]),
            'ecdf_gap':ecdf_gap(a,b),'variance_ratio':float(b.var()/a.var()) if a.var()>0 else None,
            **{f'target_q{q}':float(np.quantile(a,q/100)) for q in [0,25,50,75,100]},
            **{f'sample_q{q}':float(np.quantile(b,q/100)) for q in [0,25,50,75,100]}})
    pool=f.loc[~f.index.isin(set(conditions[0]['ids'])|set(sugar_ids()))].copy()
    capacity=[]
    for frame in [target,pool]:frame['is_motor']=frame.super_class.eq('motor')
    keys=['model_sign','recruited','is_motor']
    for key,n in target.groupby(keys,dropna=False).size().items():
      mask=np.ones(len(pool),dtype=bool)
      for k,v in zip(keys,key):mask &= pool[k].eq(v).to_numpy()
      capacity.append({**dict(zip(keys,[str(key[0]),bool(key[1]),bool(key[2])])), 'needed':int(n),'available':int(mask.sum()),'enough':int(mask.sum())>=int(n)})
    pd.DataFrame(rows).to_csv(out/'distributions.csv',index=False)
    pd.DataFrame(classes).to_csv(out/'composition.csv',index=False)
    pd.DataFrame(capacity).to_csv(out/'motor_strata_capacity.csv',index=False)
    comparisons=[r for r in rows if r['condition']!='mode']
    worst=max(comparisons,key=lambda r:r['ecdf_gap'])
    atomic_json(out/'summary.json',{'completed_utc':now(),'largest_ecdf_gap':worst,'motor_strata':capacity,
      'all_motor_strata_have_capacity':all(r['enough'] for r in capacity),
      'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})
    lines=['# Baseline composition audit 22 September 2026','',
      '- This audit uses baseline features and frozen lesion IDs only. It describes differences that the original mean-balance rules did not constrain. No new simulations or p-values.',
      f'- Largest empirical cumulative-distribution gap: {worst["ecdf_gap"]:.3f}, for {worst["condition"]}, {worst["feature"]}. A gap is a descriptive maximum difference in cumulative proportions, not a significance result.',
      '- The motor label comes from available annotations. Missing annotations remain unavailable; non-motor here includes unavailable classifications and must not be interpreted as a verified biological identity.',
      '', '| Sign | Recruited | Annotated motor | Needed | Available outside support and inputs |','|---|---|---|---:|---:|']
    for r in capacity:lines.append(f'| {r["model_sign"]} | {r["recruited"]} | {r["is_motor"]} | {r["needed"]} | {r["available"]} |')
    lines+=['',f'- Every exact motor/sign/recruitment stratum has enough candidates: {all(r["enough"] for r in capacity)}. This does not establish simultaneous continuous-feature feasibility.',
      '- Next design step is a separately declared joint matching feasibility check with motor counts added, preserving the original six feature limits. If capacity fails, report it rather than silently merging strata. MN9 membership cannot be exactly matched while the whole focal support is excluded; its secondary interpretation remains limited.',
      '- Code created with Codex assistance: scripts/pcdr_composition_audit.py. ecdf_gap sorts both samples, evaluates cumulative fractions at every unique observed value and returns the largest absolute gap. Main writes a protocol before analysis, then saves all feature quantiles/variances and class counts.',
      '- Evidence: results/pcdr/composition_audit_20260922/protocol.json, distributions.csv, composition.csv, motor_strata_capacity.csv and summary.json. Command: .venv/Scripts/python.exe scripts/pcdr_composition_audit.py. No new distributional acceptance cutoff was chosen from these results.', '']
    text='\n'.join(lines);(out/'FINDINGS.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/pcdr/COMPOSITION_AUDIT_20260922.md').write_text(text,encoding='utf-8')
    print(json.dumps({'worst':worst,'capacity':capacity}))

if __name__=='__main__':main()
