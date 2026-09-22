from scripts.pcdr_composition_audit import ecdf_gap

def test_ecdf_ties_and_order():
    assert ecdf_gap([2,1,1],[1,2,1])==0
    assert ecdf_gap([0,0],[1,1])==1
    assert ecdf_gap([0,1],[1,1])==.5
