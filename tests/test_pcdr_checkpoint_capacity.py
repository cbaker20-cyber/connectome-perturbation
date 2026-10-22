import pytest
from scripts.pcdr_checkpoint_capacity import segment_screen


def measures():
    return {f'{c}_{b}_{s}':dict(condition=c,status='complete',stop_ms=s,dt_ms=.0000125,
             tape_duration_s=1.,seed=631401,seconds=200*(20 if b=='uninterrupted' else 10),
             peak_rss_bytes=17e9,checkpoint_bytes=250e6)
             for c in ('baseline','mode') for b,s in [('uninterrupted',20),('restarted',10),('restarted',20)]}


def test_known_screen_and_boundary():
    r=segment_screen(measures(),43600,64000,20e9)
    assert r['allowed'] and r['segment_screen_seconds']==40000
    assert r['memory_screen_bytes']==34e9 and r['storage_screen_bytes']==20e9
    assert not segment_screen(measures(),43599,64000,20e9)['allowed']
    assert not segment_screen(measures(),43600,32000,20e9)['allowed']
    assert not segment_screen(measures(),43600,64000,19e9)['allowed']


@pytest.mark.parametrize('field,value',[('seconds',float('nan')),('seconds',0),('seed',631402),('dt_ms',.000025),('status','failed')])
def test_changed_or_invalid_measurement_refused(field,value):
    m=measures(); next(iter(m.values()))[field]=value
    with pytest.raises(ValueError): segment_screen(m,100000,64000,1e12)


def test_missing_stage_refused():
    m=measures(); m.pop(next(iter(m)))
    with pytest.raises(ValueError): segment_screen(m,100000,64000,1e12)


def test_later_segment_can_only_tighten_screen():
    m=measures()
    history=[dict(status='checkpoint_saved',stop_ms=200,begin_tick=8000000,
                  seconds=30000,peak_rss_bytes=20e9,checkpoint_bytes=500e6)]
    r=segment_screen(m,100000,64000,1e12,history)
    assert r['segment_screen_seconds']==60000
    assert r['memory_screen_bytes']==40e9
    assert r['storage_screen_bytes']==40e9
    history[0]['seconds']=1
    assert segment_screen(m,100000,64000,1e12,history)['segment_screen_seconds']==40000
    history[0]['begin_tick']=0
    with pytest.raises(ValueError,match='100 ms'):segment_screen(m,100000,64000,1e12,history)
