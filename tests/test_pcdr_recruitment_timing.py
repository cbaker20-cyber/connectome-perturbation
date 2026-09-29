import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_recruitment_timing import activity


def test_counts_first_times_and_silent_cells_preserve_large_ids():
    ids = ['720575940660219265','720575940660219266','720575940660219267']
    f = pd.DataFrame({'flywire_id':[ids[0],ids[1],ids[0]],'t':[.2,.1,.05]})
    count, first = activity(f,ids)
    assert count.tolist()==[2,1,0]
    assert first.iloc[0]==.05 and first.iloc[1]==.1 and np.isnan(first.iloc[2])
    count, first = activity(f.iloc[:0],ids)
    assert count.sum()==0 and first.isna().all()


@pytest.mark.parametrize('rid,t',[('unknown',.1),('101',np.nan),('101',-.1),('101',1.)])
def test_invalid_spikes_are_rejected(rid,t):
    with pytest.raises(ValueError):activity(pd.DataFrame({'flywire_id':[rid],'t':[t]}),['101'])
