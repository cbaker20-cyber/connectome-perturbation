import pandas as pd
import pytest
from scripts.pcdr_pathway_routes import arrivals


def test_signed_arrivals_boundary_and_zero_weight():
    events=pd.DataFrame({'id':['a','a'],'tick':[10,12],'direction':['reference_only','intervention_only']})
    r=arrivals(events,-2.,3,13)
    assert len(r)==1 and r[0]['arrival_tick']==13 and r[0]['intervention_minus_reference_increment_mv']==2
    assert len(arrivals(events,2.,3,15))==2
    assert arrivals(events,0.,3,15)==[]


def test_invalid_delay_and_duplicates():
    events=pd.DataFrame({'id':['a'],'tick':[10],'direction':['reference_only']})
    with pytest.raises(ValueError):arrivals(events,1.,-1,20)
    with pytest.raises(ValueError):arrivals(pd.concat([events,events]),1.,1,20)
