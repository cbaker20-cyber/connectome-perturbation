"""Bounded CCR checkpoint validation using the full fixed-case input tape."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from eigencircuits.common import atomic_json, environment, fingerprint, neuron_ids, now, read_json, sha256
from eigencircuits.memory import peak_rss
from scripts.pcdr_checkpoint_sim import simulate, CheckpointSaved
from scripts.pcdr_checkpoint_compare import checked_generation
from scripts.pcdr_fine_sim import input_tape
from scripts.pcdr_smaller_pilot import package_plan, compare_prefix
from scripts import pcdr_resolution as resolution


def settings(condition, kind, stop_ms):
    if condition not in ('baseline', 'mode'):
        raise ValueError('Only the fixed baseline/mode pair is authorized')
    if kind == 'reference' and stop_ms == 10:
        return .0001, .01
    if kind == 'checkpoint' and stop_ms in (10, 20):
        return .0000125, 1.
    raise ValueError('Undeclared checkpoint probe')


def probe(out, checkpoint, condition, kind, stop_ms):
    dt, duration = settings(condition, kind, stop_ms)
    from scripts.pcdr_ccr_capacity import allocation
    cpus, memory = allocation()
    if cpus < 2 or memory < 64000 or not os.uname().nodename.startswith('cpn-'):
        raise ValueError('Require compute-node allocation with 2 CPUs and 64000 MB')
    plan = package_plan()
    if environment()['packages'] != plan['packages'] or sys.version_info[:3] != (3, 11, 5):
        raise ValueError('Environment differs from frozen CCR study')
    out.mkdir(parents=True, exist_ok=False)
    record = dict(status='running', condition=condition, kind=kind, stop_ms=stop_ms,
                  dt_ms=dt, tape_duration_s=duration, seed=631401, started_utc=now(),
                  environment=environment(), slurm_job=os.environ['SLURM_JOB_ID'],
                  cpus=cpus, memory_mb=memory, host=os.uname().nodename,
                  source_hashes={p:sha256(ROOT/p) for p in (
                      'scripts/pcdr_checkpoint_probe.py','scripts/pcdr_checkpoint_sim.py',
                      'scripts/pcdr_checkpoint_compare.py','model.py')})
    atomic_json(out/'measurement.json', record)
    import brian2 as b
    timings = {'store_seconds': [], 'restore_seconds': []}
    original_store, original_restore = b.Network.store, b.Network.restore
    def timed_store(network, *args, **kwargs):
        start=time.perf_counter()
        try:
            return original_store(network, *args, **kwargs)
        finally:
            timings['store_seconds'].append(time.perf_counter()-start)
    def timed_restore(network, *args, **kwargs):
        start=time.perf_counter()
        try:
            return original_restore(network, *args, **kwargs)
        finally:
            timings['restore_seconds'].append(time.perf_counter()-start)
    started=time.perf_counter()
    b.Network.store, b.Network.restore = timed_store, timed_restore
    try:
        original_plan=read_json(ROOT/'original/jobs.json')
        trial=f'default_{condition}_631401'
        original=next(j for j in original_plan['jobs'] if j['trial_id']==trial)
        source=ROOT/'original/trials'/trial
        saved=resolution.validated(source, original, original_plan)
        events=pd.read_parquet(source/'input_events.parquet')
        if fingerprint(events.to_dict('list')) != saved['input_digest']:
            raise ValueError('Physical input digest mismatch')
        record['physical_input_digest']=saved['input_digest']
        if kind=='reference':
            events=events.loc[events.tick<100].copy()
        ids=neuron_ids(); lookup={v:i for i,v in enumerate(ids)}
        tape_start=time.perf_counter()
        tape=input_tape(events,saved['input_ids'],dt,duration)
        record.update(tape_seconds=time.perf_counter()-tape_start, tape_bytes=tape.nbytes)
        try:
            frames=simulate(631401,[lookup[v] for v in saved['input_ids']],
                            [lookup[v] for v in (plan['mode_ids'] if condition=='mode' else [])],
                            tape=tape, dt_ms=dt, duration_s=duration, chunk_ms=10.,
                            weight_scale=original['variant']['weight_scale'],
                            inhibitory_scale=original['variant']['inhibitory_scale'],
                            return_delivered=True, checkpoint_dir=checkpoint, stop_after_ms=stop_ms)
        except CheckpointSaved:
            if kind!='checkpoint':
                raise
        else:
            if kind!='reference':
                raise ValueError('Probe unexpectedly completed a scientific duration')
            for frame in frames:
                frame['flywire_id']=pd.Series([ids[i] for i in frame.pop('neuron_index')],dtype='string')
            compare_prefix(frames[0],frames[2],ROOT/'anchors'/f'fine_0p0001_default_{condition}_631401',duration,dt)
            for name, frame in zip(('spikes','scheduled','delivered'),frames):
                frame.to_parquet(out/(name+'.parquet'),index=False)
            record['exact_reference']=True
        saved, base=checked_generation(checkpoint)
        if saved['tick']!=round(stop_ms/dt):
            raise ValueError('Checkpoint did not reach declared endpoint')
        record.update(status='complete', checkpoint_record=saved,
                      checkpoint_bytes=sum(p.stat().st_size for p in base.iterdir() if p.is_file()))
    except BaseException as error:
        record.update(status='failed', error=repr(error))
        raise
    finally:
        b.Network.store, b.Network.restore = original_store, original_restore
        record.update(seconds=time.perf_counter()-started, peak_rss_bytes=peak_rss(),
                      finished_utc=now(), timings=timings)
        atomic_json(out/'measurement.json',record)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--condition',required=True)
    parser.add_argument('--kind',required=True)
    parser.add_argument('--stop-ms',type=int,required=True)
    args=parser.parse_args()
    probe(args.out.resolve(),args.checkpoint.resolve(),args.condition,args.kind,args.stop_ms)

