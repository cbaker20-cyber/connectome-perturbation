# 06 Decision Log

This file records why important scientific and computational decisions were made.

| Decision ID | Date | Decision | Reason | Consequence | Revisit when |
|---|---|---|---|---|---|
| D001 | 2026-03-20 | Use the Shiu et al. whole-brain LIF model as the base model. | It already integrates FlyWire connectivity and neurotransmitter-informed signs in Brian2. | Project can focus on perturbation and interpretation instead of rebuilding the model. | Upstream model changes or new version released. |
| D002 | 2026-03-26 | Use output silencing by zeroing outgoing synaptic weights. | This is available in the model and directly tests downstream influence. | Interpret as output removal, not full biological ablation. | If adding partial silencing or receptor-level mechanisms. |
| D003 | 2026-03-26 | Run sequentially on local machine. | Parallel runs caused OOM under WSL. | Stable but slower compute. | If moving to cloud/HPC or more RAM. |
| D004 | 2026-03-30 | Use 5 trials for broad screens. | Needed fast candidate discovery. | Exploratory only; cannot support final claims. | Replace with 10-trial screen or direct 30-trial validation when compute improves. |
| D005 | 2026-04-02 | Validate candidates with 30 trials. | Stochastic Poisson input made 5-trial signs unreliable. | LO interpretation revised; AN strengthened. | If power analysis suggests different n per effect size. |
| D006 | 2026-04-02 | Match baseline and perturbation trial counts. | Mismatched n made significance unstable/underpowered. | Current inferential results are more defensible. | Always. This should not be relaxed without justification. |
| D007 | 2026-06-10 | Treat negative graph enrichment as a useful control. | A group can be functionally important without being globally central. | Shift toward task-specific source-to-motor pathway analysis. | After path-analysis output is validated. |
| D008 | 2026-07-21 | Prefer conda `brian2` env for overnight JO/BORA jobs; keep pip `requirements.txt` as a secondary install path. | System `python3` lacked pandas/brian2; project lock is `environment.yml`. | Overnight jobs must prepend `$HOME/miniconda3/envs/brian2/bin` to `PATH` so `python3` resolves correctly. | If a dedicated venv or lockfile replaces conda. |
