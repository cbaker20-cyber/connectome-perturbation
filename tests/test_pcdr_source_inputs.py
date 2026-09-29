import numpy as np
from scripts.pcdr_source_inputs import arrivals


def test_arrivals_match_explicit_delayed_events_at_boundaries():
    ticks=np.array([0,2,4,9])
    assert arrivals(ticks,4,7,2)==2
    assert arrivals(ticks,0,2,2)==0
    assert arrivals(np.array([],dtype=int),0,100,2)==0
    rng=np.random.default_rng(631405)
    for _ in range(200):
        t=np.sort(rng.integers(0,100,size=30))
        start=int(rng.integers(0,100));end=start+int(rng.integers(1,25));delay=int(rng.integers(0,10))
        assert arrivals(t,start,end,delay)==int(((t+delay>=start)&(t+delay<end)).sum())
