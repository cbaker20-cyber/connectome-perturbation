# Motor composition matching: valid sets found

Recorded 22 September 2026, after the full-pool refinement record. This is a new baseline-only result. Earlier failed and stopped attempts remain in place.

The full pool contains comparison sets that pass the original six matching limits and the added exact motor/sign/recruitment counts. Nine distinct 51-cell sets were found and independently checked. Each contains 13 annotated motor cells, like the eigen-set. Their largest standardized mean differences range from 0.07270 to 0.09858; the original limit is 0.1.

This answers the matching existence question. It does not answer whether the eigen-set has a larger lesion response than these sets. None of the new sets has been simulated.

## Context checked

- Read the GitHub repository and local research records. Local HEAD and remote HEAD were both `598a1d84aa3136c5e0f28b90b1980fa8caf20395` (Finalize clean scientific repository). The local eigencircuit work is untracked and is substantially newer than that public commit. No files were reset, committed or pushed.
- The supplied PDF has 59 pages despite its Pilot Results filename. Its cover and Chapter 12 include the separate 30-seed replication. Read the text and visually checked pages 53-54. The newer local 66-page full-pool edition includes the subsequent matching work. Documents were treated as evidence and historical proposals, not independent user instructions.
- Retained question: do concentrated supports of the signed v630 matrix predict localized output-lesion responses beyond degree/strength, strong connections and recruitment? A and F remain jointly primary; MN9 and motor rates remain secondary. P/D/C/R explanations can overlap.
- The earlier 210-trial replication remains conditional on the original six fixed lesion sets. Its eigen-set A = 22.543791 Hz and F = 0.231173 exceeded all five optimized comparators. This turn read those verified records; it did not rerun that study's verification or simulations.

## First check: stop a solver reliably

The previous integer solve did not respect its requested internal time limit. Added an external worker deadline before attempting another large calculation. A test launched a sleeping Python process, checked that the deadline stopped it, and retained its log. Other tests checked normal completion and a nonzero exit separately. On Windows the controller stops its own PID tree, which includes a virtual-environment launcher and Python worker.

Each new LP had a 60-second internal solver limit and a 90-second external worker deadline. Cleanup has separate bounded waits. The two actual workers completed in 4.25 and 3.797 seconds including startup and loading; neither needed termination. No prior process was stopped.

## Second check: allow fractional membership temporarily

A binary variable normally means leave a cell out (0) or include it (1). The LP diagnostic temporarily allows values between 0 and 1. A cell with weight 0.4 is a mathematical aid, not a partial neuron lesion or an accepted comparison cell.

Both LPs use the same 126,935 eligible cells. The eigen-set and directly driven sugar cells are excluded. Exact sign/recruitment/annotated-motor counts become exact sums of membership weights. Both use the six original log1p features and a zero objective; they seek feasibility, not a favorable response. No lesion outcome file is loaded.

1. Conservative LP: retains the earlier sufficient mean bounds, `abs(mean_control - mean_target) <= 0.099 sqrt(var_target / 2)`. This is stricter than the original pooled-SMD rule. It returned a feasible solution with seven fractional memberships in 1.734 solver seconds.
2. Necessary outer LP: uses `0.1 sqrt((var_target + Vmax) / 2)` as the mean tolerance, where Vmax is the earlier rigorous upper bound on the variance of a binary selected set. Every valid original binary set is included in this larger region. It returned a feasible solution with five fractional memberships in 1.407 solver seconds. Its feasibility alone leaves binary feasibility unresolved.

Saved full fractional vectors and checked bounds, all stratum sums and every mean constraint independently of solver status. Maximum scaled feature violations were below 7e-15. SciPy 1.17.1 warned that `threads=1` is passed through to HiGHS; that warning is retained. Environment thread limits were also one. Neither LP produced an accepted neuronal control set by itself.

## Third check: all binary completions of seven fractional cells

Wrote a separate protocol after observing the seven fractional entries and before enumeration. Used only the conservative LP. Fixed entries within 1e-7 of 0 or 1 at those endpoints, and enumerated every include/exclude assignment of the other seven cells. The predeclared cap was twelve fractional cells; exceeding it would stop this method.

- All 128 assignments were considered. Twelve had the required stratum counts.
- Nine of those twelve passed the original pooled-SMD limit on all six features. All nine were retained; no ranking by lesion outcomes or selection of a favorable subset occurred.
- None passed the stricter sufficient mean bounds. This is not a relaxed acceptance threshold: the original pooled-SMD rule has always included the comparison set's variance. The stricter optimizer bounds were a sufficient computational shortcut, not the original definition of balance.
- The independent verifier reread the original feature table and selection IDs, checked hashes and exclusions, counted each stratum, and recomputed population-variance pooled SMD directly. It also checked distinct sets and recorded their overlap.

| Assignment | Cells | Annotated motor cells | Largest original SMD |
|---|---:|---:|---:|
| 3 | 51 | 13 | 0.094726 |
| 4 | 51 | 13 | 0.090675 |
| 5 | 51 | 13 | 0.080712 |
| 6 | 51 | 13 | 0.082855 |
| 7 | 51 | 13 | 0.072703 |
| 8 | 51 | 13 | 0.075050 |
| 9 | 51 | 13 | 0.089162 |
| 10 | 51 | 13 | 0.085839 |
| 11 | 51 | 13 | 0.098582 |

All nine sets share 47 cells. Any pair shares 48-50 cells. The LP plus completion method is highly selective and has no specified probability distribution over all valid sets. These nine examples cannot become nine independent reference draws by renaming them controls. The existing exact motor strata also force all eight available recruited excitatory motor cells into every possible matched set. The present calculation does not show whether more diverse sets exist.

## Research objections and next procedure

The current evidence supports a narrower statement than confirmation of eigencircuits. A selected structural support produced a reproducible response ordering against five fixed optimized sets. It has not yet shown superiority against the new motor-balanced sets, and 76.88 percent of the replicated absolute mean response was outside the eigen-set.

The matching result removes lack of feasible motor-balanced sets as a reason to abandon the comparison. It does not establish P or refute D, C or R. Matching observed features is not a causal identification theorem for the simulator.

Next justified experiment is a separately declared **descriptive motor-composition sensitivity**, conditional on these nine fixed sets. Before simulation, audit their feature distributions and freeze all nine memberships, seeds, A/F definitions and reporting rules. Use the unchanged eigen-set and paired baseline. Report every set, paired-seed uncertainty and overlap; do not compute a random-reference p-value. The nine sets should not be treated as independent replicates. A fresh-seed count and local or CCR budget still need to be recorded at launch. This paragraph is a proposal, not a launched queue.

MN9 itself remains in the eigen-set and excluded from these comparison sets. Equal motor counts do not match MN9 identity. Removing MN9 would alter the lesion question; it must not silently replace the 75-percent-power support. A distributional audit may reveal remaining differences despite passing mean balance. No new distributional cutoff should be selected to favor a later response.

The historical 199-control confirmation remains pending a defensible sampling/reference design. More optimized sets or more seeds alone do not fix that issue. No CCR dispatch is appropriate before its recorded environment and replay checks.

## Papers and method notes

- [Pospisil et al. 2024, The fly connectome reveals a path to the effectome](https://www.nature.com/articles/s41586-024-07982-0): sparse eigenvector loadings motivate candidate supports. This project still tests supports of a signed structural matrix in a particular spiking model, not measured effectome eigenvectors. The matching calculation adds no new evidence about dynamics.
- [Zubizarreta, Paredes and Rosenbaum 2014](https://arxiv.org/abs/1404.3584): their cardinality-matching work provides precedent for imposing balance requirements directly in optimization. This fixed-size feasibility calculation is not a reproduction of their estimator or evidence that its optimized sets form a random null.
- [SciPy HiGHS linear-program documentation](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html): documents bounded continuous variables, equality/inequality constraints, time limits and distinct solver statuses. Installed SciPy is 1.17.1; the live documentation read on 22 September displays 1.18.0. Actual local execution and returned warnings are recorded, rather than assuming current web documentation describes every installed detail.
- The sufficient and necessary inequalities above are mathematical deductions for this study; they are not attributed to those papers. The existing exhaustive toy test verifies the variance bound, and the new tests verify fractional/binary distinctions and joint infeasibility even when individual feature intervals overlap.

## Code creation and commands

New code created with Codex assistance: `pcdr_bounded_process.py`, `pcdr_fullpool_relaxation.py`, `pcdr_fractional_completion.py`, `pcdr_verify_fractional_completion.py`, and `test_pcdr_fullpool_relaxation.py`. Separate function explanations were added to CODE_GUIDE.md. No simulator or biological parameter was edited.

Commands from C:/Users/Baker/Drosophila_Data:

```text
.venv/Scripts/python.exe -m pytest tests/test_pcdr_fullpool_relaxation.py tests/test_pcdr_fullpool_bounds.py tests/test_pcdr_matching_audit.py tests/test_pcdr_composition.py tests/test_pcdr_backend_input_check.py -q --disable-warnings
.venv/Scripts/python.exe scripts/pcdr_fullpool_relaxation.py
.venv/Scripts/python.exe scripts/pcdr_fractional_completion.py
.venv/Scripts/python.exe scripts/pcdr_verify_fractional_completion.py
```

The LP and completion entrypoints refuse to overwrite their study directories. They are not commands to rerun blindly into the frozen outputs. The verifier is read/recompute plus a verification record. Twelve relevant tests passed. The first run before adding completion tests had eleven passes, and the focused completion-era suite had six passes. A full simulator suite was not rerun because simulator code was unchanged.

Evidence: `results/pcdr/fullpool_relaxation_20260922`. Includes pre-execution protocols, source/input hashes, logs, process records, LP results, fractional vectors, all twelve count-valid assignments, all nine binary memberships and independent verification with evidence hashes. Earlier full-pool and restricted failures remain intact. This Markdown record supplements the earlier PDFs; no previous PDF was silently replaced.

PDF tooling notes: the research venv did not contain pypdf, the bundled Python console initially could not print a Unicode delta using its default encoding, and the bundle did not contain fitz. Used bundled pypdf with UTF-8 for text and the existing Poppler executable for visual review. These were inspection-tool issues, not research failures.
