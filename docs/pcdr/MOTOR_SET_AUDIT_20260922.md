# What the motor-balanced sets still do not match

22 September 2026. Baseline-only audit completed before the new motor-composition pilot was prepared.

All nine sets still pass the original six pooled-SMD limits and exact motor/sign/recruitment counts. The distribution audit shows that this does not make the sets equivalent to the target.

The largest incoming-degree variance ratio is 19.117, calculated on log1p values. The largest empirical cumulative-distribution gap is 0.294118 for motor_006 incoming degree, despite an SMD of only 0.038027. These are descriptive differences, not significance tests. The earlier feasibility result remains correct; it established that sets meet the stated rules, not that those rules eliminate every meaningful difference.

## Why a small SMD can coexist with a broad distribution

The original SMD divides the difference between two means by `sqrt((target variance + comparison variance)/2)`. A large comparison variance makes that denominator larger. It is possible to pass the mean-balance rule while selecting both unusually small and unusually large values. The feasibility solver used a zero objective and was not asked to match higher moments. There is no evidence that it deliberately optimized this denominator.

The selected mode's incoming-degree log1p values range from 4.883 to 6.184. For motor_006 the range is 1.099 to 8.073. A similar mean cannot describe that difference in spread.

## Composition

All nine comparisons have 13 annotated motor cells, exactly matching the target. Each also has 17 central, 9 descending and 12 unavailable superclass labels, compared with the target's 23 central, 6 descending and 9 unavailable labels. Missing annotation is not a biological cell class.

The superclass total-variation distance is 6/51 = 0.117647. Cell-type total variation is 41/51 = 0.803922, but many specific cell types are rare and the focal neurons are excluded from comparison membership; this is descriptive, not a new rejection criterion. Known neurotransmitter labels are unavailable for all 51 target cells and 50 comparison cells; one comparison cell has a known GABA label. Model-sign matching relies on its recorded source, not on pretending missing measured transmitter labels are known.

MN9 belongs to the target and to none of the comparisons. All nine comparison sets share 47 neurons; any pair shares 48-50. Matching the number of motor cells does not match motor identity, network wiring or detailed cell types.

## Decision made before new lesion outcomes

Retain every set. Do not pick the comparison with the smallest distribution gap or discard an inconvenient set after simulation. Run a small, explicitly descriptive composition sensitivity, using the unchanged eigen-support, all nine sets and five fresh paired seeds. This asks whether the response ordering persists against these fixed alternatives. It does not isolate a causal effect of motor count because other features also differ from the earlier comparators.

The pilot has 55 trials: one baseline, the eigen-set and nine comparison lesions for each of seeds 631201-631205. A and F remain the primary descriptions. The added mode-minus-comparator intervals resample whole paired seeds jointly. MN9 and total/per-neuron motor changes remain secondary. No random-reference p-values or general eigencircuit claim will be made. The launch amendment fixes a thirty-minute serial limit, resource checks, reporting of every set and no automatic extension. A complete result requires all 55 trials and all 50 baseline/lesion input pairings to pass verification.

Future work should address distributional matching and comparison diversity before confirmation. Any new distribution criterion is a prospective amendment, not a reason to retroactively relabel these sets as having failed the original rules. It is also possible that simultaneously matching additional features substantially restricts the eligible pool; that must be tested rather than assumed.

## Reading notes behind the objection

[Austin 2009, Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples](https://pmc.ncbi.nlm.nih.gov/articles/3472075/) considers means, variance ratios, higher moments, five-number summaries and graphical diagnostics. That supports inspecting spread as well as means. Its subject is observational human data; it does not supply a fly-specific acceptance threshold or prove this simulator comparison is causal.

[Stuart 2010, Matching methods for causal inference: A review and a look forward](https://pmc.ncbi.nlm.nih.gov/articles/PMC2943670/) frames matching around covariate distributions and common support. Its discussion of variance ratios concerns particular statistical settings; no numerical ratio from that review was silently installed as a new biological cutoff here.

## Process and code

Created scripts/pcdr_motor_set_audit.py with Codex assistance. It checks the prior evidence hashes, includes all nine sets, recomputes the original acceptance rules and saves six-feature ECDF gaps, variance ratios, five-number summaries, complete annotation counts and per-cell annotation records. It reuses the already-tested ECDF helper. Categorical total variation is half the sum of absolute category-proportion differences. It reads only baseline features and fixed membership IDs.

Command: `.venv/Scripts/python.exe scripts/pcdr_motor_set_audit.py`. Evidence: results/pcdr/motor_set_audit_20260922. The protocol was written before the audit, and summary/output hashes were saved. No new cutoff, rematching or set substitution occurred.
