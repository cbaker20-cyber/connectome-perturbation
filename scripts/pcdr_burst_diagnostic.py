"""Replay two saved burst cases with state recording and exact prefix checks."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import environment, neuron_ids, now
from eigencircuits.memory import peak_rss
from scripts.pcdr_ccr_transfer import read, write, digest
from scripts.pcdr_bounded_process import run_bounded
from scripts.pcdr_fine_sim import simulate, input_tape
from scripts.pcdr_state_recorder import StateRecorder


def exact_prefix(actual, expected, duration_ms, dt_ms, spikes=False):
    expected = expected.loc[expected.t < duration_ms/1000] if spikes else expected.loc[expected.tick < round(duration_ms/dt_ms)]
    columns = ['t','flywire_id'] if spikes else ['tick','flywire_id']
    pd.testing.assert_frame_equal(actual[columns].reset_index(drop=True), expected[columns].reset_index(drop=True),
                                  check_dtype=False, check_exact=True)


def worker(plan_path, out, dt, duration_ms=None, window=None):
    plan_path, out = Path(plan_path), Path(out)
    plan = read(plan_path)
    if dt not in plan['dt_ms']:
        raise ValueError('Unplanned step')
    for name, h in plan['model_files'].items():
        if digest(ROOT/name) != h:raise ValueError('Changed model/data: '+name)
    for name, h in plan['reference_files'].items():
        if digest(plan_path.parent/name) != h:raise ValueError('Changed reference: '+name)
    current = environment()
    if current['packages'] != plan['packages'] or sys.version_info[:2] != (3,11):
        raise ValueError('Simulation environment differs from recorded packages')
    duration_ms = plan['duration_ms'] if duration_ms is None else duration_ms
    window = plan['record_window_ms'] if window is None else window
    if duration_ms > plan['duration_ms']:raise ValueError('Cannot extend fixed replay')
    out.mkdir(parents=True,exist_ok=False)
    record = {'status':'running','started_utc':now(),'dt_ms':dt,'duration_ms':duration_ms,
        'record_window_ms':window,'plan_sha256':digest(plan_path),'environment':current,
        'sources':{name:digest(ROOT/name) for name in ['model.py','scripts/pcdr_fine_sim.py','scripts/pcdr_state_recorder.py','scripts/pcdr_burst_diagnostic.py']}}
    write(out/'manifest.json',record)
    try:
        ids = neuron_ids(); lookup = {v:i for i,v in enumerate(ids)}
        source = pd.read_parquet(plan_path.parent/'input_events.parquet')
        source = source.loc[source.tick < round(duration_ms*10)].copy()
        inputs = plan['input_ids']
        tape = input_tape(source,inputs,dt,duration_ms/1000)
        recorder = StateRecorder(out/'state',[lookup[v] for v in plan['record_ids']],window)
        spikes, scheduled, delivered = simulate(plan['seed'],[lookup[v] for v in inputs],[lookup[v] for v in plan['lesion_ids']],
            tape=tape,duration_s=duration_ms/1000,dt_ms=dt,weight_scale=1.2,inhibitory_scale=.8,
            return_delivered=True,recorder=recorder)
        for frame in [spikes, scheduled, delivered]:
            frame['flywire_id'] = pd.Series([ids[i] for i in frame.pop('neuron_index')],dtype='string')
        expected_scheduled = source.copy()
        expected_scheduled['tick'] *= round(.1/dt)
        exact_prefix(scheduled,expected_scheduled,duration_ms,dt)
        ref = plan_path.parent/'reference'/str(dt)
        spikes.to_parquet(out/'spikes.parquet',index=False)
        delivered.to_parquet(out/'delivered_events.parquet',index=False)
        exact_prefix(spikes,pd.read_parquet(ref/'spikes.parquet'),duration_ms,dt,True)
        exact_prefix(delivered,pd.read_parquet(ref/'delivered_events.parquet'),duration_ms,dt)
        record.update(status='complete',finished_utc=now(),peak_rss_bytes=peak_rss(),spikes=len(spikes),
            exact_spike_prefix=True,exact_delivery_prefix=True,record_ids=plan['record_ids'],
            outputs={p.relative_to(out).as_posix():digest(p) for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'})
        write(out/'manifest.json',record)
    except BaseException as error:
        record.update(status='failed',finished_utc=now(),error=repr(error));write(out/'manifest.json',record)
        raise


def verified_trial(path, plan_path, dt):
    m = read(path/'manifest.json')
    plan = read(plan_path)
    if (m['status']!='complete' or m['plan_sha256']!=digest(plan_path) or m['dt_ms']!=dt
            or m['duration_ms']!=plan['duration_ms'] or m['record_window_ms']!=plan['record_window_ms']
            or not m['exact_spike_prefix'] or not m['exact_delivery_prefix']):
        raise ValueError('Incomplete or different diagnostic: '+str(path))
    for name,h in m['sources'].items():
        if digest(ROOT/name)!=h:raise ValueError('Diagnostic source changed')
    expected = {'spikes.parquet','delivered_events.parquet','state/schedule.json','state/progress.json'}
    for start in range(round(plan['record_window_ms'][0]/dt),round(plan['record_window_ms'][1]/dt),round(10/dt)):
        expected.update(f'state/{start:010d}_{phase}.npz' for phase in StateRecorder.phases)
    if set(m['outputs']) != expected:raise ValueError('Missing or unexpected recording files')
    for name,h in m['outputs'].items():
        if digest(path/name)!=h:raise ValueError('Diagnostic output changed')
    return m


def run_all(plan_path, out, hours):
    plan_path,out=Path(plan_path).resolve(),Path(out).resolve()
    if hours<=0:raise ValueError('Positive time allowance required')
    out.mkdir(parents=True,exist_ok=True)
    lock=out/'.controller.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    try:
        plan=read(plan_path)
        write(out/'progress.json',{'status':'running','total':2,'started_utc':now()})
        pending=[]
        for dt in plan['dt_ms']:
            directory=out/str(dt)
            if directory.exists():verified_trial(directory,plan_path,dt)
            else:pending.append(dt)
        def launch(dt):
            log=out/'logs'/str(dt)
            if log.exists():raise FileExistsError(log)
            result=run_bounded([sys.executable,str(Path(__file__).resolve()),'worker','--plan',str(plan_path),
                '--out',str(out/str(dt)),'--dt',str(dt)],log,hours*3600,cwd=ROOT)
            write(log/'process.json',result)
            if result['returncode'] or result['timed_out']:raise RuntimeError('Worker failed: '+str(dt))
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(launch,pending))
        summaries=[verified_trial(out/str(dt),plan_path,dt) for dt in plan['dt_ms']]
        write(out/'progress.json',{'status':'complete','completed':2,'total':2,'finished_utc':now()})
        write(out/'summary.json',summaries)
        target=out.parent/'CCR_diagnostic_results.zip'
        temporary=target.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(out.rglob('*')):
                if p.is_file() and p!=lock:z.write(p,p.relative_to(out).as_posix())
            z.write(plan_path,'diagnostic_plan.json')
            for folder in ['scripts','eigencircuits']:
                for p in (ROOT/folder).glob('*.py'):z.write(p,'source/'+p.relative_to(ROOT).as_posix())
            z.write(ROOT/'model.py','source/model.py')
        with zipfile.ZipFile(temporary) as z:
            if z.testzip() is not None:raise ValueError('Result archive CRC failure')
        temporary.replace(target)
    except BaseException as error:
        write(out/'progress.json',{'status':'failed','error':repr(error),'finished_utc':now()})
        raise
    finally:
        lock.unlink()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['worker','run']);p.add_argument('--plan',required=True);p.add_argument('--out',required=True)
    p.add_argument('--dt',type=float);p.add_argument('--hours',type=float,default=11)
    p.add_argument('--duration-ms',type=float);p.add_argument('--window',type=float,nargs=2)
    a=p.parse_args()
    if a.action=='worker':worker(a.plan,a.out,a.dt,a.duration_ms,a.window)
    else:run_all(a.plan,a.out,a.hours)
