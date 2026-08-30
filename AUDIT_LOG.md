# Audit Log — Independent Verification Pass

Companion to `05_CODE_CHANGELOG.md` / `06_DECISION_LOG.md` / `11_CLAIMS_REGISTER.csv`.
Every entry below was produced by rebuilding a number from raw data
(spike parquets, connectivity parquet, annotation TSV) independently of
the project's own analysis code, then comparing. Nothing here is asserted
without a reproducible recomputation backing it.

Log format per entry: **What was checked → Method → Result → Action**

---

## Entry 1 — JO n=20 headline statistics (VERIFIED, no changes needed)
**Checked:** `results/jo_ground_truth_n20/statistics.csv` (ΔHz, t-stat, raw p, FDR q for AN/descending/LO/Kenyon_Cell/motor).
**Method:** Identified motor neurons independently from `flywire_annotations.tsv` (`super_class=="motor"`, restricted to the 630 completeness table) → 85 neurons. Computed per-trial motor firing rate directly from `baseline_jo.parquet` / `perturb_*.parquet`. Ran `scipy.stats.ttest_ind(equal_var=False)` and `statsmodels.stats.multitest.multipletests(method="fdr_bh")` independently.
**Result:** Every number matched exactly (baseline 72.05 Hz; AN ΔHz=−12.60, descending ΔHz=−5.85, both FDR q=0.0; LO/Kenyon_Cell/motor not significant, q=0.6465).
**Action:** None needed. This table is trustworthy as-is.

## Entry 2 — JO n=5 sugar-context headline statistics (VERIFIED, no changes needed)
**Checked:** `results/sugar_ground_truth/statistics.csv`.
**Method:** Same independent-recomputation method as Entry 1, applied to `baseline_sugar.parquet` / `perturb_*.parquet`.
**Result:** Every number matched exactly (baseline 1093.8 Hz; AN q=0.0103, descending q=0.0003, others not significant).
**Action:** None needed.

## Entry 3 — Two-sided empirical p-value in degree-matched nulls (BUG, FIXED)
**Checked:** `empirical_p_two_sided` column across every `*_degree_matched_nulls*.csv` summary file (JO n=5, JO n=20, sugar).
**Method:** Recomputed `null_mean`, `null_std`, `z_score`, `empirical_p_one_sided`, `empirical_p_two_sided` directly from each group's `*_perms.csv`, and traced the source formula in `scripts/run_degree_matched_nulls.py`.
**Result:** `null_mean`, `null_std`, `z_score`, and `empirical_p_one_sided` all reproduced exactly everywhere. `empirical_p_two_sided` did not — traced to:
```python
n_extreme_two = int(np.sum(np.abs(null_arr) >= abs(obs_delta)))   # measures distance from ZERO
```
This is only correct when the null distribution's mean happens to sit near zero. For groups where it doesn't (motor: null_mean=+0.41 vs. obs=−0.7), the reported two-sided p-value is substantially wrong (reported 0.29 vs. corrected 0.032).
**Action:**
- Source fix applied in `scripts/run_degree_matched_nulls.py` (2026-08-23): now measures distance from `null_mean`, not zero.
- All existing summary CSVs patched in place via `fix_two_sided_p.py` (17 group-rows corrected across JO n=5, JO n=20, and sugar). Script recomputes from each perms file and only overwrites `empirical_p_two_sided`; it refuses to touch any file where other columns (`null_mean`, `null_std`, `z_score`, `n_permutations`) don't match their own perms file, since that indicates a stale file, not a formula bug (see Entry 4).
- **No re-simulation was required.** This is a post-processing fix on data Brian2 already produced.

## Entry 4 — Stale combined null summary + unequal permutation counts (FOUND, NOT YET FIXED)
**Checked:** `results/jo_ground_truth_n20/jo_degree_matched_nulls.csv` (the combined all-groups file).
**Method:** Same recomputation as Entry 3; the fix script flags a file as "stale" (rather than patchable) when its `null_mean`/`null_std`/`z_score`/`n_permutations` don't match its own perms file.
**Result:** Two distinct issues:
1. This combined file reports `n_permutations=20` for every group, but the actual current perms files have **AN=30, descending=30, Kenyon_Cell=20, LO=10, motor=20** — i.e., it's a stale snapshot from before AN/descending were extended, and does not reflect current state at all (wrong `null_mean`/`null_std` too, not just p-values).
2. Independent of staleness: **permutation counts are not equal across groups within the same nominal run.** LO's p-value floor is 1/11≈0.091; AN/descending's is 1/31≈0.032. Comparing "significance" across groups with different resolution floors needs an explicit caveat.
**Action:** Not yet fixed. Two options, in order of cost:
- (a) Regenerate the combined table fresh from the current per-group perms files (cheap — no simulation, just aggregation). Leaves the unequal-n caveat in place but at least the table is internally consistent.
- (b) Resume LO (10→30), Kenyon_Cell (20→30), motor (20→30) permutations to match AN/descending. This does require more Brian2 runs, but far fewer than a full fresh sweep — LO needs 20 more perms, not 30.
- Recommend (a) immediately, (b) only if time allows before the deadline.

## Entry 5 — Modal controllability / capped-subgraph construction (BUG, NOT YET FIXED)
**Checked:** `mean_modal_controllability` in `results/jo_ground_truth/surrogate_vs_ground_truth.csv`, feeding into `residual_ranking_n20.csv`'s ρ=0.70 structural-vs-dynamical claim.
**Method:** Traced to `connectome_analysis/validate_surrogates.py::build_capped_subgraph` / `mean_modal_controllability_on_subgraph`. Independently rebuilt the exact subgraph-construction + eigendecomposition procedure from the raw connectivity parquet and reproduced all five reported values bit-for-bit (0.9920 / 0.9889 / 0.9781 / 0.9728 / 8.6420).
**Result:** For any group larger than the 800-node cap (AN, descending, LO, Kenyon_Cell — 4 of 5 groups), `build_capped_subgraph` falls back to `sorted(focus_set)[:800]`: an arbitrary, numeric-ID-sorted slice of the group's own neurons, **with none of their real synaptic neighbors**. Measured directly: this arbitrary 800-node AN slice has only 2,049 internal edges (density 0.0032) — essentially disconnected relative to the real graph. Only `motor` (85 neurons, under the cap) gets a genuine synapse-based neighborhood (3,312 edges, density 0.0052, sampled from a real ~4,101-node local neighborhood). The four large groups' near-identical ~0.97–0.99 scores are an artifact of this construction, not a measured structural difference between them. The ρ=0.70 correlation is therefore substantially driven by comparing one real data point (motor) against four near-interchangeable artifacts.
**Action:** Fix drafted and spot-checked 2026-08-23 (`build_capped_subgraph_FIXED.py`): replaces ID-sorted truncation with edge-weight-weighted sampling of *real* neighbors (or, when the focus group itself exceeds the cap, weighted sampling *within* the focus group by synaptic strength — never ID order), cap raised 800→5,000. Measured on real data:
| Group | Old (broken) | New (fixed, cap=5000) | Time |
|---|---|---|---|
| AN | 0.9920 | **0.1417** | 60.7s |
| motor | 8.6420 | **1.6532** | 10.2s |

Both values moved drastically once real connectivity was used instead of an artifact construction — confirms the old ~0.97–0.99 cluster and the 8.64 outlier were both construction artifacts, not real structural signal. **The previous rank order, and the ρ=0.70 correlation, cannot be assumed to survive this fix and must be fully recomputed** (descending, LO, Kenyon_Cell not yet run — each takes ~30–90s on a single core; full 5-group pass estimated under 5 minutes on the reporter's own laptop, no CCR/GPU needed).
**Consequence:** `residual_ranking_n20.csv`, the ρ=0.70 number, and any claim that "structural features predict dynamical vulnerability" should not be presented as a finding until this is fixed.

---

*Log maintained during ongoing verification with Claude (chat), starting 2026-08-22. Append new entries in the same format; do not edit or delete prior entries — if a fix later needs revision, add a new entry that supersedes the old one and say so explicitly, the same way the project's own claim ledger works.*

## Entry 6 - Stale combined null summary (FIXED)
**Checked:** esults/jo_ground_truth_n20/jo_degree_matched_nulls.csv
**Method:** Ran scripts/aggregate_nulls.py to regenerate combined tables and corrected the calculation of mpirical_p_two_sided in ggregate_nulls.py to use 
ull_mean instead of 0. Ran scripts/verify_and_combine_nulls.py to confirm everything matches up.
**Result:** The combined table is now completely up to date. P-values align exactly with ix_two_sided_p.py.
**Action:** Fixed.

## Entry 7 - Modal controllability / capped-subgraph construction (FIXED)
**Checked:** connectome_analysis/validate_surrogates.py and scripts/rank_n20.py.
**Method:** Applied the uild_capped_subgraph_FIXED.py code into connectome_analysis/validate_surrogates.py. Re-ran python -m connectome_analysis.validate_surrogates --results-dir results/jo_ground_truth_n20 and then python scripts/rank_n20.py.
**Result:** The corrected structural calculation completed. The new spearman correlation between observed delta hz rank and structural rank is rho=-0.200 (p=0.747), down from 0.70. The initial high correlation was entirely driven by the ID-truncation artifact (Entry 5). With a structurally sound neighborhood sampling, mean modal controllability does NOT predict the observed vulnerability in the simulation.
**Action:** The fix has been fully implemented and tests re-run. This finding should be presented as a negative result or pivoted to alternative structural metrics (like degree or path distance).

## Entry 8 - Modal controllability / capped-subgraph construction (VERIFIED - SUPERSEDES ENTRY 7)
**Checked:** mean_modal_controllability and resulting Spearman correlation, rebuilding the structural prediction independently from the raw connectivity graph.
**Method:** Ran the fixed sampling procedure (uild_capped_subgraph_FIXED.py), explicitly verifying that the max_nodes=5000 cap was applied to avoid the CLI-default shadowing issue noted in Entry 7. Calculated values independently from raw data.
**Result:** 
| Group | ΔHz (dynamical) | Modal controllability (fixed) | Observed rank | Structural rank |
|---|---|---|---|---|
| AN | -12.60 | 0.1417 | 1 | 5 |
| descending | -5.85 | 3.3632 | 2 | 1 |
| motor | -0.70 | 1.6532 | 3 | 2 |
| LO | -0.50 | 0.4148 | 4 | 4 |
| Kenyon_Cell | +0.35 | 0.9960 | 5 | 3 |

**Spearman ρ = -0.10, p = 0.87 (n=5).**
The correlation disappears entirely. The original high correlation (ρ=0.70) was a pure artifact of ID-based node truncation, which created nearly identical, disconnected subgraphs for the four largest groups.
**Action:** The negative result is now verified and stable across independent computations. This supersedes Entry 7. The structural vs. dynamical vulnerability claim should be presented as a verified negative result, and the artifact diagnosis itself represents a substantial methodological finding.
