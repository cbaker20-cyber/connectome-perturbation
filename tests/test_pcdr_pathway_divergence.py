import pandas as pd
import pytest
from scripts.pcdr_pathway_divergence import difference


def test_shift_is_missing_and_added_and_ties_preserved():
    a=pd.DataFrame({'id':['a','b','c'],'tick':[1,2,2]})
    b=pd.DataFrame({'id':['a','b','d'],'tick':[1,3,2]})
    d=difference(a,b)
    assert d.to_dict('records')==[
        {'id':'b','tick':2,'direction':'reference_only'},
        {'id':'c','tick':2,'direction':'reference_only'},
        {'id':'d','tick':2,'direction':'intervention_only'},
        {'id':'b','tick':3,'direction':'intervention_only'}]
    assert difference(a,a).empty


@pytest.mark.parametrize('fault',['duplicate','id','tick'])
def test_rejects_invalid_events(fault):
    a=pd.DataFrame({'id':['a'],'tick':[1]});b=a.copy()
    if fault=='duplicate':b=pd.concat([b,b])
    elif fault=='id':b['id']=[9007199254740993]
    else:b['tick']=[1.5]
    with pytest.raises(ValueError):difference(a,b)
