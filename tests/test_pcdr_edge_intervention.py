import numpy as np
import pandas as pd
import pytest
from scripts.pcdr_edge_intervention import remove_edges, connectivity_without, WEIGHT
from scripts.pcdr_fine_sim import simulate, input_tape


def graph():
    return pd.DataFrame({'Presynaptic_Index': [0, 0, 1], 'Postsynaptic_Index': [1, 2, 0],
                         WEIGHT: [1000., 1000., -10.]})


def test_only_requested_direction_changes():
    original = graph()
    changed, removed = remove_edges(original, [(0, 1)])
    assert changed[WEIGHT].tolist() == [0., 1000., -10.]
    assert original[WEIGHT].tolist() == [1000., 1000., -10.]
    assert len(removed) == 1
    pd.testing.assert_frame_equal(remove_edges(original, [])[0], original)


@pytest.mark.parametrize('pairs', [[(2, 0)], [(0, 1), (0, 1)], [(0.0, 1)], [(-1, 0)], [(True, 1)]])
def test_invalid_requests(pairs):
    with pytest.raises(ValueError):
        remove_edges(graph(), pairs)


def test_invalid_graphs():
    duplicate = pd.concat([graph(), graph().iloc[:1]])
    nonfinite = graph(); nonfinite.loc[0, WEIGHT] = np.nan
    zero = graph(); zero.loc[0, WEIGHT] = 0
    for frame in [duplicate, nonfinite, zero, graph().drop(columns=WEIGHT)]:
        with pytest.raises(ValueError):
            remove_edges(frame, [(0, 1)])


def test_targeted_delivery_and_cleanup(tmp_path):
    comp, con = tmp_path/'comp.csv', tmp_path/'con.parquet'
    pd.DataFrame({'Completed': [1, 1, 1]}, index=[101, 102, 103]).to_csv(comp)
    graph().to_parquet(con, index=False)
    original = con.read_bytes()
    tape = input_tape(pd.DataFrame({'tick': [0], 'flywire_id': ['101']}), ['101'], .1, .01)
    args = dict(tape=tape, dt_ms=.1, duration_s=.01, completeness=comp, return_delivered=True)
    baseline = simulate(42, [0], [], connectivity=con, **args)
    with connectivity_without(con, [(0, 1)]) as (path, removed):
        changed = simulate(42, [0], [], connectivity=path, **args)
        assert len(removed) == 1
    assert not path.exists()
    assert con.read_bytes() == original
    assert set(baseline[0].neuron_index) == {0, 1, 2}
    assert set(changed[0].neuron_index) == {0, 2}
    for before, after in zip(baseline[1:], changed[1:]):
        pd.testing.assert_frame_equal(before, after)


def test_cleanup_on_failed_simulation(tmp_path):
    con = tmp_path/'con.parquet'
    graph().to_parquet(con)
    with pytest.raises(RuntimeError, match='simulation failed'):
        with connectivity_without(con, [(0, 1)]) as (path, _):
            assert path.exists()
            raise RuntimeError('simulation failed')
    assert not path.exists()
    pd.testing.assert_frame_equal(pd.read_parquet(con), graph())
