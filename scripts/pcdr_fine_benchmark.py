"""Bounded local timing tests, not one-second scientific comparisons."""
import os
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
from pathlib import Path
import argparse
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from eigencircuits.common import atomic_json, now, sha256, neuron_ids, environment
from scripts.pcdr_fine_sim import simulate, input_tape
from scripts.pcdr_bounded_process import run_bounded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=['reference', 'chunked', 'fine'])
    args = parser.parse_args()
    out = ROOT/'results/pcdr/fine_benchmark_20260929'
    source = ROOT/'results/pcdr/results_ccr_20260927/raw_download/expanded_sensitivity/trials/default_baseline_631401'
    import json
    if args.case:
        target = out/args.case
        target.mkdir(exist_ok=False)
        saved = json.loads((source/'manifest.json').read_text())
        if sha256(source/'input_events.parquet') != saved['outputs']['input_events.parquet']:
            raise ValueError('Input source changed')
        duration = .001 if args.case == 'fine' else .02
        dt = .0001 if args.case == 'fine' else .1
        events = pd.read_parquet(source/'input_events.parquet')
        events = events[events.tick < round(duration*10000)].copy()
        ids = neuron_ids(); lookup = {rid:i for i,rid in enumerate(ids)}
        inputs = saved['input_ids']
        tape = input_tape(events, inputs, dt, duration)
        runner = simulate
        kwargs = {'chunk_ms': 1. if args.case == 'fine' else 5.}
        if args.case == 'reference':
            from scripts.pcdr_followup_sim import simulate as runner
            kwargs = {}
        atomic_json(target/'started.json', {'created_utc':now(),'duration_s':duration,'dt_ms':dt,'environment':environment()})
        started = time.monotonic()
        frames = runner(631401, [lookup[rid] for rid in inputs], [], tape=tape, duration_s=duration,
                        dt_ms=dt, return_delivered=True, **kwargs)
        elapsed = time.monotonic()-started
        for name, frame in zip(['spikes','external','delivered'], frames):
            frame.to_parquet(target/(name+'.parquet'),index=False)
        atomic_json(target/'complete.json', {'completed_utc':now(),'elapsed_seconds':elapsed,
            'ticks':len(tape),'spikes':len(frames[0]),'duration_s':duration,'dt_ms':dt,
            'outputs':{p.name:sha256(p) for p in target.glob('*.parquet')}})
        return
    out.mkdir(exist_ok=False)
    atomic_json(out/'protocol.json', {'created_utc':now(),'purpose':'Resource and recording-preservation check only. Full-network 20ms reference/chunked at 0.1ms, and 1ms at 0.0001ms. Fixed first seed, no lesions. No scientific convergence claim.',
        'source_manifest_sha256':sha256(source/'manifest.json'),
        'sources':{name:sha256(ROOT/name) for name in ['scripts/pcdr_fine_sim.py','scripts/pcdr_fine_benchmark.py','scripts/pcdr_followup_sim.py','model.py']}})
    for case in ['reference','chunked','fine']:
        record = run_bounded([sys.executable, str(Path(__file__)), '--case',case], out/(case+'_logs'),180,cwd=ROOT)
        atomic_json(out/(case+'_process.json'),record)
        if record['returncode'] != 0 or record['timed_out']:
            raise RuntimeError(f'{case} failed; retained logs in {out}')
        print(case, record['elapsed_seconds'],flush=True)
    for name in ['spikes','external','delivered']:
        a=pd.read_parquet(out/'reference'/(name+'.parquet'))
        b=pd.read_parquet(out/'chunked'/(name+'.parquet'))
        pd.testing.assert_frame_equal(a.astype({'neuron_index':'int64'}),b.astype({'neuron_index':'int64'}))
    atomic_json(out/'comparison.json',{'checked_utc':now(),'reference_chunked_events_exact':True,
        'limits':'Short prefixes only; no full-duration convergence or measured peak-memory claim.'})


if __name__ == '__main__':
    main()
