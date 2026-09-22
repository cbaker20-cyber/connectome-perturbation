"""Bounded, serial exploratory follow-up; independent of the chat runtime."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pcdr_local_queue import write, execute, available_memory, stamp

BASE = ROOT/'results/pcdr/exploratory80_20260921'
PILOT = ROOT/'results/pcdr/corrected_20260919'
OLD = ROOT/'results/pcdr/local_followthrough_20260920/modes'


def audit():
    import pandas as pd
    from eigencircuits.common import ANN, sha256
    out = BASE/'support_audit';out.mkdir(parents=True, exist_ok=True)
    ann = pd.read_csv(ANN, sep='\t', dtype={'root_id':str}, low_memory=False)
    f = pd.read_parquet(PILOT/'analysis/features.parquet')
    members = pd.read_parquet(OLD/'membership.parquet')
    joined = members.merge(f[['root_id','spike_count']],on='root_id',validate='many_to_one')
    assert len(joined)==len(members)
    joined = joined.merge(ann[['root_id','super_class','cell_class','cell_type']],on='root_id',how='left',validate='many_to_one',indicator=True)
    joined.to_parquet(out/'annotated_membership.parquet',index=False)
    rows=[]
    for rank,g in joined.groupby('mode_rank'):
        classes=g.cell_class.fillna('unavailable').value_counts()
        rows.append({'mode_rank':int(rank),'support_size':len(g),'recruited_cells':int((g.spike_count>0).sum()),
                     'annotation_matches':int((g['_merge']=='both').sum()),'cell_classes':classes.to_dict()})
    write(out/'summary.json',{'created_utc':stamp(),'modes':rows,'limitation':'No neuropil column in supplied annotation table; cell class is not a neuropil measurement.',
          'sources':{str(p):sha256(p) for p in [ANN,OLD/'membership.parquet',PILOT/'analysis/features.parquet']}})
    lines=['# Saved-support annotation audit','','Cell classes are annotations, not measured functional identity. No neuropil field is present in the supplied table.','',
           '| Rank (zero based) | Cells | Spiking cells | Annotated | Most frequent cell classes |','|---|---:|---:|---:|---|']
    for r in rows:
        labels=', '.join(f'{k}: {v}' for k,v in list(r['cell_classes'].items())[:3])
        lines.append(f"| {r['mode_rank']} | {r['support_size']} | {r['recruited_cells']} | {r['annotation_matches']} | {labels} |")
    (out/'FINDINGS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def action(name):
    from eigencircuits.common import read_json
    if name=='audit':audit()
    elif name=='modes':
        from scripts.pcdr_modes_exploratory80 import build
        build(BASE/'modes',PILOT/'analysis/features.parquet')
    elif name=='matching':
        from eigencircuits.controls import generate
        generate(PILOT/'analysis/features.parquet',BASE/'modes',BASE/'controls',full=True,n_sets=5)
    elif name=='prepare':
        from scripts.pcdr_local_followthrough import create_pilot
        create_pilot(PILOT,BASE/'modes',BASE/'controls',BASE/'mode_pilot')
        path=BASE/'mode_pilot/jobs.json';d=read_json(path)
        d['amendment']='Exploratory 80-pair / first-40-mode search, 21 September 2026'
        write(path,d)
    elif name=='summarize':
        from scripts.pcdr_local_followthrough import summarize_mode
        from scripts.pcdr_local_findings import report
        summarize_mode(BASE/'mode_pilot');report(BASE/'mode_pilot')


def main():
    p=argparse.ArgumentParser();p.add_argument('--action',default='run');args=p.parse_args()
    if args.action!='run':action(args.action);return
    config=json.loads((BASE/'amendment.json').read_text())
    deadline=config['deadline_epoch']
    lock=BASE/'controller.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    state={'status':'starting','pid':os.getpid(),'started_utc':stamp(),'deadline_epoch':deadline}
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    def phase(name,limit,command=None):
        while True:
            if time.time()>=deadline or (BASE/'STOP').exists():raise TimeoutError('Deadline or STOP')
            memory=available_memory()
            if memory is None or memory>=4*1024**3:break
            state.update(status='waiting_for_memory',phase=name,updated_utc=stamp());write(BASE/'status.json',state);time.sleep(30)
        command=command or [sys.executable,str(Path(__file__).resolve()),'--action',name]
        state.update(status='running',phase=name,command=command,updated_utc=stamp());write(BASE/'status.json',state)
        with (BASE/(name+'.log')).open('a',encoding='utf-8') as log:
            log.write(stamp()+' '+json.dumps(command)+'\n');log.flush()
            execute(command,ROOT,env,log,min(limit,max(1,deadline-time.time())))
    try:
        if os.name=='nt':ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        assert json.loads((ROOT/'results/pcdr/ccr_singles_20260919/summary.json').read_text())['status']=='complete'
        phase('audit',300);phase('modes',7200)
        mode_manifest=json.loads((BASE/'modes/manifest.json').read_text())
        selected=json.loads((BASE/'modes/selection.json').read_text())
        if not mode_manifest['complete_candidate_search']:
            state.update(status='complete_incomplete_candidate_search',finding='Fewer than 40 stable complete modes from fixed 80-pair budget; no lesion selection used.')
        elif selected['status']!='selected':
            state.update(status='complete_no_eligible_mode',finding='Exploratory first-40 search failed unchanged recruitment criterion.')
        else:
            phase('matching',3600);phase('prepare',120)
            study=BASE/'mode_pilot'
            write(study/'local_status.json',{'started_utc':stamp(),'deadline_epoch':deadline,'status':'starting','completed':0,'total':35})
            phase('pilot',max(1,deadline-time.time()),[sys.executable,str(ROOT/'scripts/pcdr_local_queue.py'),'--study',str(study),'--features',str(PILOT/'analysis/features.parquet')])
            if json.loads((study/'local_status.json').read_text())['status']!='complete':raise RuntimeError('Pilot incomplete; do not summarize')
            phase('summarize',180)
            state.update(status='complete_exploratory_pilot',finding='Five-control five-seed result only; not confirmation.')
        state['updated_utc']=stamp();write(BASE/'status.json',state)
        (BASE/'STAGE_OUTCOME.md').write_text('# Exploratory follow-up outcome\n\n'+state['finding']+'\n\nSee status.json, amendment.json, support_audit/FINDINGS.md and modes/manifest.json.\n',encoding='utf-8')
    except BaseException as e:
        state.update(status='stopped',error=repr(e),updated_utc=stamp());write(BASE/'status.json',state);raise
    finally:
        if os.name=='nt':ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        lock.unlink(missing_ok=True)


if __name__=='__main__':main()
