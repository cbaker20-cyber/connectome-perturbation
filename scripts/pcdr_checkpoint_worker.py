"""Run one bounded segment of the fixed pair using saved physical inputs."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import socket
import sys
import time
import uuid
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from eigencircuits.common import atomic_json, environment, fingerprint, neuron_ids, now, read_json, sha256
from scripts.pcdr_fixed_pair import select_pair
from scripts.pcdr_smaller_pilot import package_plan
from scripts.pcdr_checkpoint_sim import CheckpointSaved, simulate
from scripts.pcdr_fine_sim import input_tape
from scripts import pcdr_resolution as resolution
from scripts.pcdr_checkpoint_compare import checked_generation


@contextmanager
def owned_attempt(out, condition, stop_ms):
    folder = out/'segments'/condition
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder/'owner.lock'
    owner = dict(pid=os.getpid(), host=socket.gethostname(),
                 job=os.environ.get('SLURM_JOB_ID'), token=uuid.uuid4().hex)
    payload = json.dumps(owner)
    # Cover preparation and final output writing as well as the simulator itself.
    with lock.open('x') as stream:
        stream.write(payload)
    try:
        stage = folder/f'{stop_ms}_{owner["token"]}'
        stage.mkdir()
        yield stage, owner
    finally:
        if lock.exists() and lock.read_text() == payload:
            lock.unlink()


def endpoint(checkpoint, stop_ms):
    if not (checkpoint/'latest.json').exists():
        if stop_ms != 100:
            raise ValueError('First segment must end at 100 ms')
        return 0
    record, _ = checked_generation(checkpoint)
    tick = record['tick']
    target = round(stop_ms/.0000125)
    if tick != target-round(100/.0000125) and not (stop_ms == 1000 and tick == target):
        raise ValueError('Segment must advance exactly 100 ms; only final output recovery may repeat')
    return tick


def write_outputs(out, spec, frames):
    previous_tape, previous_simulate = resolution.input_tape, resolution.simulate
    try:
        resolution.input_tape = input_tape
        resolution.simulate = lambda *args, **kwargs: frames
        resolution.worker(ROOT/'original', out, spec)
    finally:
        resolution.input_tape, resolution.simulate = previous_tape, previous_simulate


def run(out, condition, stop_ms):
    if condition not in ('baseline', 'mode') or type(stop_ms) is not int or stop_ms not in range(100, 1001, 100):
        raise ValueError('Require one declared condition and a 100 ms segment boundary')
    from scripts.pcdr_ccr_capacity import allocation
    cpus, memory = allocation()
    if cpus < 2 or memory < 64000 or not socket.gethostname().startswith('cpn-'):
        raise ValueError('Require compute allocation with 2 CPUs and 64000 MB')
    with owned_attempt(out, condition, stop_ms) as (stage, owner):
        record = dict(status='running', condition=condition, stop_ms=stop_ms,
                      started_utc=now(), owner=owner, cpus=cpus, memory_mb=memory)
        started = time.perf_counter()
        atomic_json(stage/'segment.json', record)
        try:
            execute(out, condition, stop_ms, stage, record)
        except BaseException as error:
            record.update(status='failed', error=repr(error))
            raise
        finally:
            from eigencircuits.memory import peak_rss
            record.update(seconds=time.perf_counter()-started, peak_rss_bytes=peak_rss())
            record['finished_utc'] = now()
            atomic_json(stage/'segment.json', record)


def execute(out, condition, stop_ms, stage, record):
    plan = package_plan()
    if environment()['packages'] != plan['packages'] or sys.version_info[:3] != (3, 11, 5):
        raise ValueError('Environment differs from frozen study')
    spec = next(j for _, j in select_pair(plan)[2] if j['condition'] == condition)
    trial = out/'trials'/spec['id']
    if trial.exists():
        raise FileExistsError(f'Existing trial preserved: {trial}')
    checkpoint = out/'checkpoints'/condition
    record['begin_tick'] = endpoint(checkpoint, stop_ms)
    source = ROOT/'original/trials'/spec['source_trial']
    original_plan = read_json(ROOT/'original/jobs.json')
    original = next(j for j in original_plan['jobs'] if j['trial_id'] == spec['source_trial'])
    saved = resolution.validated(source, original, original_plan)
    events = pd.read_parquet(source/'input_events.parquet')
    if fingerprint(events.to_dict('list')) != saved['input_digest']:
        raise ValueError('Physical input digest mismatch')
    ids = neuron_ids()
    lookup = {v:i for i,v in enumerate(ids)}
    tape = input_tape(events, saved['input_ids'], spec['dt_ms'])
    record.update(spec=spec, physical_input_digest=saved['input_digest'],
                  source_manifest_sha256=sha256(source/'manifest.json'), environment=environment(),
                  source_hashes={name:sha256(ROOT/name) for name in
                                 ('scripts/pcdr_checkpoint_worker.py','scripts/pcdr_checkpoint_sim.py','model.py')})
    atomic_json(stage/'segment.json', record)
    try:
        frames = simulate(spec['seed'], [lookup[x] for x in saved['input_ids']],
                          [lookup[x] for x in spec['lesion_ids']], tape=tape,
                          dt_ms=spec['dt_ms'], return_delivered=True,
                          weight_scale=original['variant']['weight_scale'],
                          inhibitory_scale=original['variant']['inhibitory_scale'],
                          checkpoint_dir=checkpoint, stop_after_ms=stop_ms)
        del tape
        if stop_ms != 1000:
            raise ValueError('Unexpected full completion before final segment')
        # Retain the established output checks and format after the final resumed segment.
        write_outputs(stage/'trial', spec, frames)
        trial.parent.mkdir(parents=True, exist_ok=True)
        (stage/'trial').rename(trial)
        record.update(status='complete', finished_utc=now())
    except CheckpointSaved:
        if stop_ms == 1000:
            raise ValueError('Final segment did not finish')
        saved_checkpoint, _ = checked_generation(checkpoint)
        if saved_checkpoint['tick'] != round(stop_ms/spec['dt_ms']):
            raise ValueError('Checkpoint stopped at wrong endpoint')
        record['checkpoint_record'] = saved_checkpoint
        _, base = checked_generation(checkpoint)
        record['checkpoint_bytes'] = sum(p.stat().st_size for p in base.iterdir() if p.is_file())
        record.update(status='checkpoint_saved', finished_utc=now())
    except BaseException as error:
        record.update(status='failed', error=repr(error), finished_utc=now())
        raise
    finally:
        atomic_json(stage/'segment.json', record)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--condition', choices=['baseline', 'mode'], required=True)
    parser.add_argument('--stop-ms', type=int, required=True)
    args = parser.parse_args()
    run(args.out.resolve(), args.condition, args.stop_ms)
