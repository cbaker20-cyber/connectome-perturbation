"""Recheck the saved structural candidates without changing lesion selection."""
from itertools import combinations
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, now, read_json, root_ids, sha256, sugar_ids
from eigencircuits.graph import load_signed_matrix


def support(vector, fraction):
    vector = np.asarray(vector)
    if vector.ndim != 1 or not np.isfinite(vector).all() or not 0 < fraction <= 1:
        raise ValueError('Invalid vector or support fraction')
    power = np.square(np.abs(vector))
    total = power.sum()
    if not np.isfinite(total) or total <= 0:
        raise ValueError('Nonpositive or nonfinite vector power')
    order = np.argsort(-power, kind='stable')
    stop = min(len(order), np.searchsorted(np.cumsum(power[order]), fraction * total) + 1)
    return order[:stop], power / total


def aligned_features(features, ids):
    f = features.copy()
    f['root_id'] = root_ids(f.root_id)
    ids = root_ids(ids)
    if f.root_id.duplicated().any() or len(set(ids)) != len(ids):
        raise ValueError('Duplicate neuron IDs')
    if set(ids) != set(f.root_id):
        raise ValueError('Feature and eigenvector neuron IDs differ')
    f = f.set_index('root_id').loc[ids]
    for name in ['spike_count', 'trials_recruited']:
        values = f[name].to_numpy()
        if not np.isfinite(values).all() or (values < 0).any() or (values != np.floor(values)).any():
            raise ValueError(f'Invalid {name}')
    if (f.trials_recruited > 5).any() or ((f.spike_count > 0) != (f.trials_recruited > 0)).any():
        raise ValueError('Inconsistent recruitment counts')
    return f


def main():
    base = ROOT / 'results/pcdr/exploratory80_20260921'
    modes_dir = base / 'modes'
    out = ROOT / 'docs/pcdr/evidence/2026-09-29/candidate_review'
    protocol = out / 'protocol.json'
    outputs = ['sensitivity.csv', 'candidates.csv', 'overlap.csv', 'record.json']
    if not protocol.is_file() or any((out / name).exists() for name in outputs):
        raise FileExistsError('Need the prior protocol and an unused output location')
    manifest = read_json(modes_dir / 'manifest.json')
    features_path = ROOT / 'results/pcdr/corrected_20260919/analysis/features.parquet'
    if sha256(features_path) != manifest['features_sha256']:
        raise ValueError('Selection features changed')
    for name, digest in manifest['provenance']['inputs'].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f'Model input changed: {name}')
    modes = pd.read_parquet(modes_dir / 'modes.parquet')
    members = pd.read_parquet(modes_dir / 'membership.parquet')
    members['root_id'] = root_ids(members.root_id)
    if modes.mode_rank.duplicated().any() or members.duplicated(['mode_rank', 'root_id']).any():
        raise ValueError('Duplicate modes or memberships')
    with np.load(modes_dir / 'eigenpairs.npz', allow_pickle=False) as saved:
        ids = np.asarray(root_ids(saved['root_ids']))
        vectors = saved['eigenvectors']
        values = saved['eigenvalues']
    if vectors.shape != (len(ids), len(values)) or not np.isfinite(values).all():
        raise ValueError('Invalid eigenpair dimensions or values')
    f = aligned_features(pd.read_parquet(features_path), ids)
    counts = f.spike_count.to_numpy()
    inputs = set(sugar_ids())
    selected = modes[modes.stable & modes.complete_pair & (modes.stable_mode_rank < 40)]
    if len(selected) != 40 or set(selected.stable_mode_rank) != set(range(40)):
        raise ValueError('Incomplete stable-mode selection')
    rows, candidates, supports = [], [], {}
    for row in selected.itertuples():
        vector = vectors[:, row.eig_index]
        original, power = support(vector, .75)
        expected = members[members.mode_rank == row.mode_rank]
        if set(ids[original]) != set(expected.root_id) or len(original) != row.n_75:
            raise ValueError(f'Support mismatch for mode {row.mode_rank}')
        if not np.allclose(power[expected.neuron_index.to_numpy()], expected.power_frac, atol=1e-12, rtol=0):
            raise ValueError(f'Loading mismatch for mode {row.mode_rank}')
        recruited = float(power[counts > 0].sum())
        n_five = int((counts[original] >= 5).sum())
        if abs(recruited - row.recruited_power) > 1e-12 or n_five != row.support_cells_with_five_spikes:
            raise ValueError(f'Recruitment mismatch for mode {row.mode_rank}')
        eligible = n_five >= 10 and not (set(ids[original]) & inputs)
        if bool(eligible) != row.eligible:
            raise ValueError(f'Eligibility mismatch for mode {row.mode_rank}')
        for fraction in [.5, .75, .9]:
            indices, _ = support(vector, fraction)
            for threshold in [1, 5, 10]:
                n = int((counts[indices] >= threshold).sum())
                rows.append(dict(mode_rank=int(row.mode_rank), fraction=fraction, spike_threshold=threshold,
                    support_size=len(indices), qualifying_cells=n, recruited_power=recruited,
                    abs_lambda=float(row.abs_lambda), eligible=bool(n >= 10 and not (set(ids[indices]) & inputs))))
        if row.eligible:
            cell_features = f.iloc[original]
            supports[int(row.mode_rank)] = (set(ids[original]), set(ids[original[counts[original] > 0]]))
            candidates.append(dict(mode_rank=int(row.mode_rank), support_size=len(original),
                baseline_active=int((counts[original] > 0).sum()), five_spikes=n_five,
                active_all_five=int((cell_features.trials_recruited == 5).sum()),
                recruited_power=recruited, support_power=float(power[original].sum()),
                active_support_power=float(power[original[counts[original] > 0]].sum()),
                excitatory=int((cell_features.model_sign == 'excitatory').sum()),
                inhibitory=int((cell_features.model_sign == 'inhibitory').sum()),
                motor=int((cell_features.super_class == 'motor').sum()),
                missing_superclass=int(cell_features.super_class.isna().sum()),
                lambda_real=float(row.lambda_real), lambda_imag=float(row.lambda_imag)))
    choices = []
    frame = pd.DataFrame(rows)
    for (fraction, threshold), group in frame.groupby(['fraction', 'spike_threshold']):
        eligible = group[group.eligible].sort_values(['recruited_power', 'abs_lambda', 'mode_rank'], ascending=[False, False, True])
        choices.append(dict(fraction=float(fraction), spike_threshold=int(threshold),
            eligible_ranks=eligible.mode_rank.tolist(), selected_rank=int(eligible.iloc[0].mode_rank) if len(eligible) else None))
    original_choice = next(x for x in choices if x['fraction'] == .75 and x['spike_threshold'] == 5)
    selection = read_json(modes_dir / 'selection.json')
    if original_choice['selected_rank'] != selection['mode_rank'] or set(selection['root_ids']) != supports[selection['mode_rank']][0]:
        raise ValueError('Original selected candidate differs')
    w, matrix_ids = load_signed_matrix()
    if not np.array_equal(matrix_ids, ids):
        raise ValueError('Matrix order differs from eigenvector order')
    for candidate in candidates:
        row = selected[selected.mode_rank == candidate['mode_rank']].iloc[0]
        i = int(row.eig_index)
        vector = vectors[:, i]
        action = w @ vector
        residual = np.linalg.norm(action - values[i] * vector) / (np.linalg.norm(action) + abs(values[i]) * np.linalg.norm(vector))
        if not np.isfinite(residual) or residual >= 1e-6 or abs(values[i] - complex(row.lambda_real, row.lambda_imag)) > 1e-9:
            raise ValueError('Saved eigenpair fails matrix check')
        candidate['recomputed_residual'] = float(residual)
    overlaps = []
    for a, b in combinations(supports, 2):
        left, right = supports[a], supports[b]
        overlaps.append(dict(mode_a=a, mode_b=b, shared_support=len(left[0] & right[0]),
            support_jaccard=len(left[0] & right[0]) / len(left[0] | right[0]),
            shared_active=len(left[1] & right[1]), active_jaccard=len(left[1] & right[1]) / len(left[1] | right[1])))
    frame.to_csv(out / 'sensitivity.csv', index=False)
    pd.DataFrame(candidates).to_csv(out / 'candidates.csv', index=False)
    pd.DataFrame(overlaps).to_csv(out / 'overlap.csv', index=False)
    sources = [protocol, Path(__file__), features_path, modes_dir / 'manifest.json',
        modes_dir / 'modes.parquet', modes_dir / 'membership.parquet', modes_dir / 'eigenpairs.npz', modes_dir / 'selection.json']
    atomic_json(out / 'record.json', dict(completed_utc=now(), candidates=candidates, sensitivity_choices=choices,
        mode_checks=40, sensitivity_rows=len(frame), original_selection_reproduced=True,
        source_hashes={str(p.relative_to(ROOT)): sha256(p) for p in sources},
        model_input_hashes=manifest['provenance']['inputs'],
        output_hashes={name: sha256(out / name) for name in outputs[:-1]},
        limits='Retrospective same-selection-data review. No new lesion outcomes or solver starts. Stability flags inherited.'))
    print(pd.DataFrame(candidates).to_string(index=False))
    print(pd.DataFrame(choices).to_string(index=False))
    print(pd.DataFrame(overlaps).to_string(index=False))


if __name__ == '__main__':
    main()
