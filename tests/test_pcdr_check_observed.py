import json
import numpy as np
import pandas as pd
import pytest
from scripts import pcdr_check_observed as checker


@pytest.mark.parametrize('bad_voltage', [False, True])
def test_threshold_check_uses_recorded_state(tmp_path, monkeypatch, bad_voltage):
    run, ref = tmp_path / 'run', tmp_path / 'ref'
    worker, saved = run / 'trial', ref / 'trials/trial'
    worker.mkdir(parents=True); saved.mkdir(parents=True)
    spec = {'id': 'trial', 'dt_ms': 500.}
    spikes = pd.DataFrame({'t': [0.], 'flywire_id': ['101']})
    delivery = pd.DataFrame({'tick': [0], 'flywire_id': ['101']})
    for directory in [worker, saved]:
        spikes.to_parquet(directory / 'spikes.parquet', index=False)
        delivery.to_parquet(directory / 'delivered_events.parquet', index=False)
    state = {'indices': np.array([0])}
    slots = ['before_thresholds', 'after_synapses']
    for slot in slots:
        state[slot + '_t_s'] = np.array([0., .5])
        state[slot + '_v_mV'] = np.array([[-52. if bad_voltage else -44., -52.]])
        state[slot + '_g_mV'] = np.zeros((1, 2))
        state[slot + '_not_refractory'] = np.ones((1, 2), dtype=bool)
    np.savez_compressed(worker / 'states.npz', **state)
    for directory in [worker, saved]:
        record = {'status': 'complete', 'spec': spec, 'peak_rss_bytes': 100,
                  'started_utc': 'start', 'finished_utc': 'end',
                  'outputs': {p.name: checker.sha256(p) for p in directory.iterdir()}}
        (directory / 'manifest.json').write_text(json.dumps(record))
    plan = {'jobs': [spec], 'record_ids': ['101'], 'slots': slots,
            'reference_manifests': {'trial': checker.sha256(saved / 'manifest.json')}}
    (run / 'plan.json').write_text(json.dumps(plan))
    (run / 'progress.json').write_text(json.dumps({'status': 'complete', 'completed': 1}))
    (run / 'logs/trial').mkdir(parents=True)
    (run / 'logs/trial/process.json').write_text(json.dumps({'returncode': 0, 'timed_out': False}))
    (tmp_path / 'docs/pcdr').mkdir(parents=True)
    (tmp_path / 'docs/pcdr/OBSERVED_REPLAY_PLAN.json').write_text(json.dumps(plan))
    monkeypatch.setattr(checker, 'ROOT', tmp_path)
    monkeypatch.setattr(checker, 'neuron_ids', lambda: ['101'])
    out = tmp_path / 'checked.json'
    if bad_voltage:
        with pytest.raises(ValueError, match='threshold'): checker.check(run, ref, out)
        assert not out.exists()
    else:
        checker.check(run, ref, out)
        assert json.loads(out.read_text())['status'] == 'complete'
