import json
import pytest
from scripts import pcdr_observed_replay as runner


def test_memory_refusal_writes_no_run_and_existing_output_is_preserved(tmp_path, monkeypatch):
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({'sources': {}}))
    monkeypatch.setattr(runner, 'available_memory', lambda: 3_000_000_000)
    out = tmp_path / 'out'
    with pytest.raises(RuntimeError, match='Need 6 GB'):
        runner.run(plan, tmp_path, tmp_path, out)
    assert not out.exists()
    out.mkdir(); (out / 'evidence').write_text('keep')
    with pytest.raises(FileExistsError): runner.run(plan, tmp_path, tmp_path, out)
    assert (out / 'evidence').read_text() == 'keep'


def test_changed_source_refused_before_memory_check(tmp_path):
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({'sources': {'model.py': 'changed'}}))
    with pytest.raises(ValueError, match='Changed source'):
        runner.run(plan, tmp_path, tmp_path, tmp_path / 'out')


def test_worker_failure_stops_later_trials_and_retains_record(tmp_path, monkeypatch):
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({'sources': {}, 'jobs': [{'id': 'first'}, {'id': 'second'}]}))
    monkeypatch.setattr(runner, 'available_memory', lambda: 8_000_000_000)
    called = []
    def fail(command, directory, *args, **kwargs):
        called.append(directory.name)
        return {'returncode': 1, 'timed_out': False}
    monkeypatch.setattr(runner, 'run_bounded', fail)
    out = tmp_path / 'out'
    with pytest.raises(RuntimeError, match='Worker failed'):
        runner.run(plan, tmp_path, tmp_path, out)
    assert called == ['first']
    progress = json.loads((out / 'progress.json').read_text())
    assert progress['status'] == 'failed' and progress['completed'] == 0
    assert (out / 'logs/first/process.json').is_file()
