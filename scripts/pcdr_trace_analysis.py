"""Descriptive analysis of the four verified recorded replays."""
import os
os.environ['MPLBACKEND'] = 'Agg'
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eigencircuits.common import atomic_json, sha256, now
from scripts.pcdr_ccr_transfer import read

WINDOWS = [(0, 25), (25, 100), (100, 200), (200, 500), (500, 1000)]


def aligned(coarse, fine):
    if fine.shape[-1] != 2 * coarse.shape[-1]: raise ValueError('Clocks do not align two to one')
    return coarse, fine[..., ::2]


def main(out=None):
    run = ROOT / 'results/pcdr/observed_replay_20260928'
    out = Path(out) if out is not None else ROOT / 'docs/pcdr/evidence/2026-09-28/trace_analysis'
    out.mkdir(exist_ok=False)
    plan = read(run / 'plan.json')
    certificate_path = ROOT / 'docs/pcdr/evidence/2026-09-28/observed_replay_check.json'
    certificate = read(certificate_path)
    atomic_json(out / 'protocol.json', {'recorded_utc': now(), 'script_sha256': sha256(Path(__file__)),
        'verification_sha256': sha256(certificate_path), 'windows_ms': WINDOWS,
        'method': 'Retain all ten cells and four runs. Compare the same schedule slot at shared physical times by taking every second finer sample, with no interpolation or lag fitting. Full-population counts use 10 ms bins; selected-cell state summaries use the five fixed windows. Report per-cell voltage/drive differences, refractory disagreement and signed net synaptic-stage drive increments. No significance tests, new exclusions or causal cell rankings.',
        'limits': 'Windows follow previously seen response timing; this is retrospective. Cross-step state differences can include spike/reset phase differences. g is voltage-valued drive, not current. Net increments do not separate excitation from inhibition.'})
    states, events, rows, comparisons, population = {}, {}, [], [], []
    verified = {r['trial']: r for r in certificate['rows']}
    for j in plan['jobs']:
        p = run / j['id']; m = read(p / 'manifest.json')
        if sha256(p / 'manifest.json') != verified[j['id']]['manifest_sha256']: raise ValueError('Changed trial')
        for name, digest in m['outputs'].items():
            if sha256(p / name) != digest: raise ValueError('Changed output')
        key = (j['condition'], j['dt_ms'])
        with np.load(p / 'states.npz', allow_pickle=False) as z: states[key] = {k: z[k] for k in z.files}
        events[key] = pd.read_parquet(p / 'spikes.parquet')
        s = states[key]; t = s['before_thresholds_t_s'] * 1000
        counts = np.bincount(np.floor((events[key].t.to_numpy()+1e-12)/.01).astype(int), minlength=100)
        population.extend({'condition': key[0], 'dt_ms': key[1], 'start_ms': i*10, 'spikes': int(n)} for i,n in enumerate(counts))
        for i, rid in enumerate(plan['record_ids']):
            for start, end in WINDOWS:
                mask = (t >= start-1e-9) & (t < end-1e-9)
                g = s['before_thresholds_g_mV'][i, mask]
                jump = s['after_synapses_g_mV'][i, mask] - g
                spikes = events[key].loc[events[key].flywire_id == rid, 't'].to_numpy()*1000
                rows.append({'condition': key[0], 'dt_ms': key[1], 'root_id': rid, 'start_ms': start, 'end_ms': end,
                    'spikes': int(((spikes >= start-1e-9) & (spikes < end-1e-9)).sum()),
                    'mean_g_mV': float(g.mean()), 'refractory_fraction': float((~s['before_thresholds_not_refractory'][i,mask]).mean()),
                    'positive_net_jump_sum_mV': float(jump[jump>0].sum()), 'negative_net_jump_sum_mV': float(jump[jump<0].sum())})
    for condition in ['baseline', 'mode_without_mn9']:
        a, b = states[condition, .0125], states[condition, .00625]
        ta, tb = aligned(a['before_thresholds_t_s'], b['before_thresholds_t_s'])
        if not np.allclose(ta, tb, atol=1e-12, rtol=0): raise ValueError('Different physical sample times')
        for i,rid in enumerate(plan['record_ids']):
            for start,end in WINDOWS:
                mask = (ta*1000 >= start-1e-9) & (ta*1000 < end-1e-9)
                row = {'condition': condition, 'root_id': rid, 'start_ms': start, 'end_ms': end}
                for name in ['v_mV','g_mV','not_refractory']:
                    x,y = aligned(a['before_thresholds_'+name][i], b['before_thresholds_'+name][i])
                    row[name+'_mean_absolute_difference' if name != 'not_refractory' else 'refractory_disagreement_fraction'] = float(np.mean(x[mask]!=y[mask])) if name=='not_refractory' else float(np.mean(abs(x[mask]-y[mask])))
                comparisons.append(row)
    cell_rows = pd.DataFrame(rows)
    coverage = []
    for key, frame in events.items():
        selected = int(frame.flywire_id.isin(plan['record_ids']).sum())
        total = int(cell_rows[(cell_rows.condition == key[0]) & (cell_rows.dt_ms == key[1])].spikes.sum())
        if selected != total: raise ValueError('Window counts do not cover selected spikes exactly')
        coverage.append({'condition': key[0], 'dt_ms': key[1], 'total_spikes': len(frame),
                         'recorded_cell_spikes': selected, 'recorded_spike_fraction': selected/len(frame) if len(frame) else None,
                         'distinct_spiking_cells_including_inputs': int(frame.flywire_id.nunique())})
    atomic_json(out / 'coverage.json', coverage)
    cell_rows.to_csv(out / 'cell_windows.csv', index=False)
    pd.DataFrame(comparisons).to_csv(out / 'step_differences.csv', index=False)
    pop = pd.DataFrame(population); pop.to_csv(out / 'population.csv', index=False)
    import matplotlib.pyplot as plt
    fig,axes = plt.subplots(2,1,figsize=(8,6),sharex=True)
    for ax,condition in zip(axes,['baseline','mode_without_mn9']):
        for dt in [.0125,.00625]:
            frame = pop[(pop.condition==condition)&(pop.dt_ms==dt)]
            ax.plot(frame.start_ms+5,frame.spikes,label=f'{dt} ms')
        ax.set_title(condition.replace('_',' '));ax.set_ylabel('Spikes per 10 ms');ax.legend()
    axes[-1].set_xlabel('Time (ms)');fig.tight_layout();fig.savefig(out/'population.png',dpi=160);plt.close(fig)
    atomic_json(out / 'record.json', {'completed_utc': now(), 'status':'complete',
        'outputs':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})


if __name__ == '__main__': main()
