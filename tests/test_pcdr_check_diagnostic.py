import json
import zipfile

import pytest

from scripts import pcdr_check_diagnostic as check


@pytest.fixture(autouse=True)
def local_package(tmp_path, monkeypatch):
    (tmp_path/'exports').mkdir()
    with zipfile.ZipFile(tmp_path/'exports/CCR_Diagnostic.zip','w') as z:
        z.writestr('connectome_diagnostic/diagnostic_plan.json','{"record_ids": ["1"]}')
    monkeypatch.setattr(check,'ROOT',tmp_path)
    monkeypatch.setattr(check,'neuron_ids',lambda: ['1'])


def test_duplicate_members_rejected(tmp_path):
    archive = tmp_path/'duplicate.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('progress.json','{}')
        with pytest.warns(UserWarning,match='Duplicate name'):
            z.writestr('progress.json','{}')
    with pytest.raises(ValueError,match='Duplicate archive members'):
        check.analyze(archive,tmp_path/'out')


def test_changed_plan_rejected(tmp_path):
    archive = tmp_path/'changed.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('diagnostic_plan.json','{}')
    with pytest.raises(ValueError,match='plan differs'):
        check.analyze(archive,tmp_path/'out')


def test_partial_controller_rejected(tmp_path):
    with zipfile.ZipFile(check.ROOT/'exports/CCR_Diagnostic.zip') as upload:
        plan = upload.read('connectome_diagnostic/diagnostic_plan.json')
    archive = tmp_path/'partial.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('diagnostic_plan.json',plan)
        z.writestr('progress.json',json.dumps({'status':'running'}))
    with pytest.raises(ValueError,match='Incomplete controller'):
        check.analyze(archive,tmp_path/'out')
