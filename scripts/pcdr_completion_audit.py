"""Read completed records; independently check mode recruitment by root-ID joins."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
singles = ROOT/'results/pcdr/ccr_singles_20260919'
follow = ROOT/'results/pcdr/local_followthrough_20260920'
modes = follow/'modes'
features = ROOT/'results/pcdr/corrected_20260919/analysis/features.parquet'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
jobs = read(singles/'jobs.json')['jobs']
assert len(jobs) == 720
assert all(read(singles/'trials'/j['trial_id']/'manifest.json')['status'] == 'complete' for j in jobs)
assert read(singles/'summary.json')['status'] == 'complete'
f = pd.read_parquet(features)
m = pd.read_parquet(modes/'modes.parquet')
members = pd.read_parquet(modes/'membership.parquet')
joined = members.merge(f[['root_id','spike_count']], on='root_id', how='left', validate='many_to_one')
assert joined.spike_count.notna().all()
counts = joined.assign(five=joined.spike_count >= 5, any_spike=joined.spike_count > 0).groupby('mode_rank')[['five','any_spike']].sum()
assert all(int(counts.loc[r.mode_rank,'five']) == r.support_cells_with_five_spikes for r in m.itertuples())
first = m.loc[m.stable & m.complete_pair & (m.stable_mode_rank < 20)]
assert len(first) == 20
assert (first.support_cells_with_five_spikes == 0).all()
record = {'recorded_utc':datetime.now(timezone.utc).isoformat(), 'command':'.venv/Scripts/python.exe scripts/pcdr_completion_audit.py',
          'completed_trials':len(jobs), 'mode_solver_k':read(modes/'manifest.json')['k'],
          'stable_complete_modes':int((m.stable & m.complete_pair).sum()),
          'first_twenty':{'five_spike_cells_per_support':[int(counts.loc[r,'five']) for r in first.mode_rank],
                          'any_spike_cells_per_support':[int(counts.loc[r,'any_spike']) for r in first.mode_rank],
                          'max_residual':float(first.residual.max()),
                          'max_recruited_loading_power':float(first.recruited_power.max())},
          'claim':'Prespecified recruitment selection failed; no eigen-set lesion or matched-control test was run.',
          'sources':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__), singles/'jobs.json',singles/'summary.json',singles/'analysis/results.json',singles/'FINDINGS.md',modes/'manifest.json',modes/'modes.parquet',modes/'membership.parquet',modes/'selection.json',features]}}
(follow/'completion_audit.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k != 'sources'},indent=2))
