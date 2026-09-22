"""Known-answer checks for the scientific contracts of the P/D/C/R workflow."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix

from eigencircuits.analysis import adjusted_rand, cluster_matrix, select_cells
from eigencircuits.build_modes import power75, solve, stability, unique_modes
from eigencircuits.common import atomic_json, atomic_parquet, load_trials, root_ids, sha256
from eigencircuits.controls import matched_sets, standardized_difference
from eigencircuits.graph import load_signed_matrix, strong_matrix
from eigencircuits.readouts import bh, bootstrap_footprint, footprint, paired_signflip, reference_test
from eigencircuits.recruitment_from_parquet import bin_spikes, recruitment
from eigencircuits.toy_eigencircuit import build_toy_w


def test_id_precision():
    assert root_ids([720575940660219265]) == ["720575940660219265"]
    with pytest.raises(ValueError):
        root_ids([float(720575940660219265)])


def test_complex_power_and_exact_boundary():
    v = np.array([1, 1j, 1, 1j])
    assert power75(v).tolist() == [0, 1, 2]
    assert set(power75(v*1j)) == set(power75(v))
    with pytest.raises(ValueError):
        power75(np.zeros(3))
    with pytest.raises(ValueError):
        power75(np.array([np.nan, 1]))


def test_complex_toy_does_not_take_real_part():
    values, vectors = np.linalg.eig(build_toy_w())
    i = next(i for i, v in enumerate(values) if v.imag > .1)
    assert len(power75(vectors[:, i])) == 3
    assert len(power75(vectors[:, i].real)) == 2


def test_conjugates_equal_magnitude_and_incomplete_pairs():
    groups = unique_modes(np.array([2+0j, -2+0j, 1+1j, 1-1j, .5+.5j]))
    assert len(groups) == 4
    assert sum(g[2] for g in groups) == 3
    assert groups[0][0] != groups[1][0]


def test_repeated_eigenvalues_are_unresolved():
    v = np.eye(3, dtype=complex)
    vals = np.array([2., 2., 1.])
    report = stability(vals, v, vals, v)
    assert not report[0]["stable"] and not report[1]["stable"]
    assert report[2]["stable"]


def test_directed_orientation_and_edge_ids(tmp_path):
    comp = tmp_path/"comp.csv"
    con = tmp_path/"con.parquet"
    pd.DataFrame({"Completed": [1, 1, 1]}, index=[101, 102, 103]).to_csv(comp)
    e = pd.DataFrame({"Presynaptic_ID": [101, 102], "Postsynaptic_ID": [102, 103],
                      "Presynaptic_Index": [0, 1], "Postsynaptic_Index": [1, 2],
                      "Excitatory x Connectivity": [2, -3]})
    e.to_parquet(con)
    w, ids = load_signed_matrix(comp, con)
    assert (w @ np.array([1., 0., 0.])).tolist() == [0., 2., 0.]
    assert ids.tolist() == ["101", "102", "103"]
    e.loc[0, "Presynaptic_ID"] = 103
    e.to_parquet(con)
    with pytest.raises(ValueError, match="mismatch"):
        load_signed_matrix(comp, con)


def test_strong_mask_preserves_sign_and_postsynaptic_denominator():
    w = csr_matrix([[0., 0., 0.], [-95., 0., 5.], [1., 0., 0.]])
    kept = strong_matrix(w, .05).toarray()
    assert kept[1, 0] == -95 and kept[1, 2] == 5
    assert kept[2, 0] == 1
    assert strong_matrix(w, .06)[1, 2] == 0


def test_eigen_solver_residual_known_directed_graph():
    w = csr_matrix([[2., 1., 0.], [0., 1., 2.], [0., 0., -1.]])
    vals, vecs, residuals = solve(w, 2, 42)
    assert np.all(residuals < 1e-6)
    assert set(np.round(vals.real)) == {2, 1, -1}


def spikes():
    return pd.DataFrame({"trial": ["a", "a", "b"], "flywire_id": ["101", "101", "102"],
                         "t": [.001, .011, .005]})


def test_silent_trials_and_partial_recruitment():
    r = recruitment(spikes(), ["101", "102", "103"], ["a", "b", "silent"]).set_index("root_id")
    assert r.loc["101", "spike_count"] == 2
    assert r.loc["101", "baseline_hz"] == pytest.approx(2/3)
    assert r.loc["101", "fraction_trials_recruited"] == pytest.approx(1/3)
    assert r.loc["103", "baseline_hz"] == 0


def test_bins_keep_trial_boundaries_and_exact_time_units():
    x = bin_spikes(spikes(), ["101", "102"], ["a", "b", "silent"], 10)
    assert x.shape == (2, 3, 100)
    assert x[0, 0, 0] == x[0, 0, 1] == x[1, 1, 0] == 1
    assert x[:, 2].sum() == 0
    bad = spikes(); bad.loc[0, "t"] = 1.
    with pytest.raises(ValueError):
        bin_spikes(bad, ["101", "102"], ["a", "b"], 10)


def test_clustering_constant_rows_and_known_groups():
    x = np.array([[[1, 0, 1, 0]], [[2, 0, 2, 0]], [[0, 1, 0, 1]], [[0, 0, 0, 0]]], dtype=float)
    valid, corr, tree, labels = cluster_matrix(x)
    assert valid.tolist() == [True, True, True, False]
    assert labels[0] == labels[1] and labels[0] != labels[2]
    assert corr[0, 2] == pytest.approx(-1.)
    assert adjusted_rand([1, 1, 2], [7, 7, 9]) == 1.


def test_manifest_retains_zero_spike_trial(tmp_path):
    d = pd.DataFrame({"t": pd.Series(dtype=float), "trial": pd.Series(dtype=str),
                      "flywire_id": pd.Series(dtype=str), "exp_name": pd.Series(dtype=str)})
    atomic_parquet(tmp_path/"spikes.parquet", d)
    atomic_json(tmp_path/"manifest.json", {"status": "complete", "trial_id": "silent", "seed": 42,
                "outputs": {"spikes.parquet": sha256(tmp_path/"spikes.parquet")}})
    rows, manifest = load_trials([tmp_path])
    assert len(rows) == 0 and manifest[0]["trial_id"] == "silent"


def matching_features(n=30):
    return pd.DataFrame({"root_id": [str(i) for i in range(n)], "model_sign": ["excitatory"]*n,
        "recruited": [True]*n, **{c: np.ones(n) for c in ["in_degree", "out_degree", "in_strength", "out_strength", "baseline_hz", "strong_out_mass"]}})


def test_controls_are_distinct_excluded_and_reproducible():
    f = matching_features()
    a, summary = matched_sets(f, ["0", "1"], ["2"], n_sets=5, max_attempts=100)
    b, _ = matched_sets(f, ["0", "1"], ["2"], n_sets=5, max_attempts=100)
    assert a == b and summary["complete"]
    assert len(set(tuple(x) for x in a)) == 5
    assert all(len(set(x)) == 2 and not set(x)&{"0", "1", "2"} for x in a)


def test_controls_fail_instead_of_replacement_or_relaxing_strata():
    f = matching_features(3)
    with pytest.raises(ValueError, match="insufficient"):
        matched_sets(f, ["0", "1"], n_sets=5)
    f = matching_features(10); f.loc[0, "model_sign"] = "inhibitory"
    with pytest.raises(ValueError, match="insufficient"):
        matched_sets(f, ["0"], n_sets=5)


def test_constant_matching_features_must_match_exactly():
    assert standardized_difference(np.ones((3, 1)), np.ones((3, 1)))[0] == 0
    assert np.isinf(standardized_difference(np.ones((3, 1)), np.ones((3, 1))*2)[0])


def test_footprint_is_mean_signed_change_then_absolute():
    delta = np.array([[-2., 2., 0.], [0., 2., 0.]])
    f = footprint(delta.mean(0), [0, 1])
    assert f["A"] == 1.5 and f["F"] == 1.
    assert footprint(np.zeros(3), [0])["F"] is None
    with pytest.raises(ValueError):
        footprint(np.ones(3), [0, 0])


def test_reference_resolution_and_undefined_concentration():
    c = [{"A": 1., "F": .1}]*5
    result = reference_test({"A": 2., "F": .5}, c)
    assert result["p_conjunction"] == pytest.approx(1/6)
    assert reference_test({"A": 0., "F": None}, c)["p_conjunction"] == 1.
    assert reference_test({"A": 2., "F": .5}, c*40)["p_conjunction"] == pytest.approx(1/201)


def test_bootstrap_and_secondary_testing_silent_data():
    b = bootstrap_footprint(np.zeros((5, 3)), [0], n=20)
    assert b["F_95pct"] is None and b["A_95pct"] == [0., 0.]
    assert paired_signflip(np.zeros(5)) == 1.
    assert paired_signflip([3.]) is None
    assert bh([.01, .04, .03]).tolist() == pytest.approx([.03, .04, .04])


def test_original_degree_sampler_no_replacement():
    from scripts.run_degree_matched_nulls import degree_matched_sample
    with pytest.raises(ValueError, match="insufficient"):
        degree_matched_sample(np.random.default_rng(1), pd.Series([0, 0]),
                              pd.Series([0]), np.array([101]), 2)


def test_actual_brian_input_replay_and_outgoing_lesion(monkeypatch):
    import model
    from eigencircuits.trials import simulate
    c = pd.DataFrame(index=[101, 102, 103])
    e = pd.DataFrame({"Presynaptic_Index": [0, 1, 2], "Postsynaptic_Index": [1, 2, 0],
                      "Excitatory x Connectivity": [30, 30, -1]})
    monkeypatch.setattr(model.pd, "read_csv", lambda *a, **k: c)
    monkeypatch.setattr(model.pd, "read_parquet", lambda *a, **k: e)
    a, u = simulate(42, [0], [], duration_s=.1)
    b, v = simulate(42, [0], [], duration_s=.1)
    lesion, inp = simulate(42, [0], [0], duration_s=.1)
    silent, no_input = simulate(42, [], [], duration_s=.1)
    assert a.equals(b) and u.equals(v) and inp.equals(u)
    assert len(silent) == len(no_input) == 0
    assert set(lesion.neuron_index) <= {0}


def test_selection_has_20_distinct_sign_consistent_cells():
    n = 90
    f = matching_features(n)
    f["model_sign"] = ["excitatory"]*40+["inhibitory"]*50
    f["classical_fast"] = f.model_sign; f["shiu_2024"] = f.model_sign
    f["annotation_available"] = True; f["trials_recruited"] = 5
    f["baseline_hz"] = np.arange(n)+1.
    clusters = pd.DataFrame({"root_id": f.root_id, "cluster": np.arange(n)%8})
    selection = select_cells(f, clusters, 5)
    cells = [r for r in selection["cells"] if r["role"] in ["excitatory", "inhibitory"]]
    assert len(cells) == len({r["root_id"] for r in cells}) == 20
    assert sum(r["role"] == "excitatory" for r in cells) == 10


def test_scheduled_input_is_independent_of_feedback_and_gating(monkeypatch):
    import model
    from eigencircuits.trials import simulate
    c = pd.DataFrame(index=[101, 102, 103])
    e = pd.DataFrame({"Presynaptic_Index": [0, 2, 1], "Postsynaptic_Index": [2, 0, 2],
                      "Excitatory x Connectivity": [100, 100, 100]})
    monkeypatch.setattr(model.pd, "read_csv", lambda *a, **k: c)
    monkeypatch.setattr(model.pd, "read_parquet", lambda *a, **k: e)
    a, schedule, delivered = simulate(630101, [0, 1], [], return_delivered=True)
    b, paired, delivered_b = simulate(630101, [0, 1], [2], return_delivered=True)
    assert schedule.equals(paired)
    assert not a.equals(b)
    expected = np.random.default_rng(630101).binomial(1, .015, size=(10000, 2))
    assert len(schedule) == expected.sum()
    scheduled = set(map(tuple, schedule[["neuron_index", "tick"]].to_numpy()))
    for d in [delivered, delivered_b]:
        assert set(map(tuple, d[["neuron_index", "tick"]].to_numpy())) <= scheduled
    # A feedback-dependent refractory mask can remove scheduled voltage writes.
    assert len(delivered) < len(schedule)


def test_incomplete_ccr_jobs_cannot_be_collected(tmp_path):
    from eigencircuits.ccr import collect
    feature = tmp_path / "features.parquet"
    atomic_parquet(feature, pd.DataFrame({"root_id": ["101"]}))
    atomic_json(tmp_path / "jobs.json", {"features_sha256": sha256(feature),
                "jobs": [{"index": 0, "trial_id": "missing"}]})
    with pytest.raises(ValueError, match="no partial confirmation"):
        collect(tmp_path, feature)
    assert json.loads((tmp_path / "missing_jobs.json").read_text())["indices"] == [0]
