from copy import deepcopy
import pytest
from scripts.pcdr_collect_existing import PLATFORMS, check_provenance


def records():
    saved = {'inputs': {'data': 'a'}, 'sources': {'model': 'b'},
             'environment': {'platform': PLATFORMS[0], 'python': '3.11.5',
                             'executable': '/venv/bin/python', 'packages': {'numpy': '1.26.4'}}}
    current = deepcopy(saved)
    current['environment']['platform'] = PLATFORMS[1]
    return saved, current


def test_reviewed_cpu_change_and_identical_environment():
    saved, current = records()
    check_provenance(saved, current)
    check_provenance(saved, deepcopy(saved))


@pytest.mark.parametrize('field', ['inputs', 'sources'])
def test_reject_changed_evidence(field):
    saved, current = records()
    current[field]['unexpected'] = 'changed'
    with pytest.raises(ValueError, match=field):
        check_provenance(saved, current)


@pytest.mark.parametrize('key,value', [('python', '3.12'), ('executable', '/other/python'),
                                     ('packages', {'numpy': '2.0'})])
def test_reject_changed_runtime(key, value):
    saved, current = records()
    current['environment'][key] = value
    with pytest.raises(ValueError, match='environment'):
        check_provenance(saved, current)


def test_reject_unreviewed_platform():
    saved, current = records()
    current['environment']['platform'] = PLATFORMS[1].replace('glibc2.38', 'glibc2.39')
    with pytest.raises(ValueError, match='Platform change'):
        check_provenance(saved, current)
