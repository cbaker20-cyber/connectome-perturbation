Eigencircuit update for James
23 September 2026

The question is whether a small eigenvector-defined set in the signed connectome produces a more localized response to perturbation than comparable sets. Pospisil et al. motivate the eigenvector approach [1]; the simulations use the Shiu model [2]. These are structural eigenvectors, not eigenvectors of the spiking model's Jacobian or an experimentally measured effectome.

Procedure and checks

The sequence was spike correlations, reordered matrices and clustering, individual excitatory/inhibitory lesions, then eigenvector-defined set lesions. The model has 127,400 neurons from materialization 630. Each trial runs for one second at a 0.1 ms timestep, with 21 sugar-input neurons receiving 150 Hz stochastic drive. Lesions remove outgoing synaptic transmission; the lesioned cells can still receive input and fire.

An early pairing check found that the same random seed did not guarantee the same input events. The corrected runner generates the input schedule before simulation and reuses it across each baseline/lesion pair. Exact replay and no-input checks now pass. Delivered events can differ with network state, so pairing is checked against the scheduled events. Saved rates include silent neurons, and output files have checksums.

At 10 ms bins, the baseline correlation analysis included 387 neurons and gave 170 groups. At 5 and 20 ms, it gave 286 and 114 groups. That dependence on bin width is why these remain provisional functional groups. The subsequent single-cell screen covered 10 excitatory and 10 inhibitory cells over 30 seeds. One motor-total effect survived correction across the 40 secondary tests; no MN9 effect did.

The initial eigenmode search did not yield a recruited support among the first 20 candidates. An exploratory expansion selected rank 33: 51 cells accounting for at least 75% of the mode's squared complex magnitude. It contains MN9 and 13 annotated motor cells. This was an amended search, not a successful outcome of the original fixed confirmation plan.

For each neuron, the analysis averages its signed lesion-minus-baseline rate difference across paired seeds before taking the absolute value. A is the mean absolute change inside the lesioned set, in Hz. F is that set's fraction of the whole-network absolute change. MN9 and motor rates are secondary model readouts, not measurements of behavior.

Results so far

A separate 30-seed replication completed 210 trials. The mode had A = 22.544 Hz and F = 0.2312, higher than all five optimized comparison sets. Those sets had fewer motor cells. A later motor-matched pilot completed 55 trials over five fresh seeds. The mode had A = 22.604 Hz and F = 0.2324; the nine comparisons ranged from 12.059 to 12.969 Hz and from 0.1940 to 0.1985. About 76.8% of the mode lesion's absolute response was outside its support, so this does not show an independent circuit.

The nine comparison sets shared 47 cells and produced only three distinct five-seed spike trajectories. Some membership differences were substitutions among cells silent in these runs. Mean-balance checks also missed substantial distribution differences: incoming-degree variance reached 19.1 times the target's. A later, stricter mean/variance feasibility problem was reported infeasible even with fractional memberships. That rules out the specified stricter program numerically, not every possible control design. Distribution checks matter beyond mean matching [3]. No random-control p-value is justified for these optimized sets.

---PAGE---

Proposed CCR work

The prepared study has 3,390 trials and has not run. Its first 1,890 trials cover a 3 by 3 grid of overall weight scale and inhibitory multiplier, each 0.8, 1.0 or 1.2, with seven conditions and 30 paired seeds. The conditions are baseline, the full mode, mode without MN9, MN9 alone, and one representative from each of the three previous comparison-response groups. Inhibitory weights receive the product of the two multipliers.

The other 1,500 trials lesion each of the remaining 50 mode cells separately, using the same 30 default-network baselines. MN9-only is already included, so all 51 cells are covered. The grid tests parameter interactions; the individual lesions test whether a few cells account for much of the set's response. Single-cell effects need not add up to the combined effect in a recurrent model. The scale factors are sensitivity choices, not estimates of biological uncertainty.

Every lesion uses its own variant's baseline and identical scheduled input. Memberships stay fixed. All conditions will be reported using A, F, whole-network response and MN9 change, with whole-seed bootstrap intervals. This remains a descriptive follow-up. A more diverse, defensible comparison design is still needed before claiming that eigenvector structure explains something beyond degree, strength or recruitment.

The OnDemand notebook is packaged with the data. The proposed allocation is 32 cores, 128,000 MB RAM and eight hours, with no GPU. It checks replay, undriven silence and file integrity, then measures throughput at increasing concurrency up to 24 workers. Those calibration trials are retained. The extracted package passed local smoke, missing-job, corruption, locking and resume checks. Linux installation and actual CCR scaling still need testing there.

Python environment

Use Python 3.11; the local runs used 3.11.9. The main packages are Brian2 2.9.0, NumPy 1.26.4, SciPy 1.17.1, pandas 3.0.3, PyArrow 24.0.0, matplotlib 3.11.0 and joblib 1.5.3. Cython 3.2.5, statsmodels 0.14.6 and pytest 9.1.1 are retained in the recorded environment. The notebook uses the NumPy backend; having Cython installed does not establish backend equivalence.

The pinned dependencies are contourpy 1.3.3, cycler 0.12.1, fonttools 4.63.0, iniconfig 2.3.0, Jinja2 3.1.6, kiwisolver 1.5.0, MarkupSafe 3.0.3, mpmath 1.3.0, packaging 26.2, patsy 1.0.2, Pillow 12.2.0, pluggy 1.6.0, Pygments 2.20.0, pyparsing 3.3.2, python-dateutil 2.9.0.post0, setuptools 82.0.1, six 1.17.0 and SymPy 1.14.0. The ZIP includes requirements-ccr.txt. NetworkX 3.6.1 is used by the repo's separate graph/path analyses, not this CCR notebook. JupyterLab/IPython come from OnDemand. ReportLab and pypdf are documentation tools only.

References and record

[1] Pospisil et al. (2024), The fly connectome reveals a path to the effectome. Nature. doi:10.1038/s41586-024-07982-0.

[2] Shiu et al. (2024), A Drosophila computational brain model reveals sensorimotor processing. Nature. doi:10.1038/s41586-024-07763-9.

[3] Austin (2009), Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples. Statistics in Medicine. doi:10.1002/sim.3697. This supports the balance diagnostic, not a fly-specific cutoff.

Code and detailed records: github.com/cbaker20-cyber/connectome-perturbation, under eigencircuits and docs/pcdr. Code, analysis checks and this summary were prepared with Codex assistance. The complete dated record preserves the earlier failed runs and protocol changes.
