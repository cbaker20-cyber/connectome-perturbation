# Preliminary testing and CCR notebook preparation

22 September 2026, evening, America/New_York. Some machine records are dated 23 September in UTC. Prepared with Codex assistance.

The preliminary work is enough to prepare a descriptive follow-up. It is not enough to confirm a Pospisil-style eigencircuit claim. The motor-matched pilot used nine memberships but yielded only three distinct five-seed spike trajectories. Mean matching also left large degree-distribution differences. More seeds alone would not repair either limitation.

## Distribution check

I added one baseline-only feasibility check after seeing the imbalance. The protocol was saved before the calculation. It kept the same 51-cell support, 126,935 eligible neurons, input/target exclusions and exact model-sign, recruitment and motor counts. It used the same six log1p features.

For each feature, the new sensitivity guard required a mean difference no larger than `0.099 sqrt(target population variance / 2)`. It also required `0.505 <= Q <= 2`, where Q is the average squared deviation from the target mean, divided by target variance. Since the comparison variance ratio is Q minus the squared normalized mean difference, this implies a variance ratio between 0.5000995 and 2 and the original pooled SMD below 0.1. These are explicit investigator-chosen bounds. They are not a biological threshold or a test that distributions are equal.

The single zero-objective full-pool LP allowed fractional memberships in [0,1]. HiGHS reported infeasible, with the externally bounded process finishing in 11.625 seconds. No binary sets were produced and no bounds were loosened afterward. This is a numerical infeasibility result for this stricter sufficient program, not a formal independently certified impossibility theorem. It does not contradict the nine existing sets that passed the older mean-only criterion. It does not reject the eigencircuit hypothesis or exclude every possible comparison design.

This check follows the general matching lesson that balance needs more than standardized mean differences. Austin discusses variance, distribution and graphical diagnostics; Stuart reviews overlap and balance. Neither supplies a validated fly-neuron cutoff. [Austin 2009](https://pmc.ncbi.nlm.nih.gov/articles/3472075/), [Stuart 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2943670/).

## Deployment checks

The transfer helper builds an exact-byte source/data archive, verifies hashes, initializes an explicitly labeled technical Git snapshot, records the destination environment, runs four jobs and checks their outputs. Simulation equations and historical eigencircuit modules were not changed.

An initial archive build failed because psutil was absent. The helper now records missing optional packages as null and pins only installed dependencies. A later prose check corrected an incorrect statement about statsmodels: statsmodels 0.14.6 was installed and is included in the environment. The package includes 28 pinned libraries, including transitive dependencies, for a Python 3.11 target. A fresh Linux installation remains untested.

The actual extracted ZIP was tested through its command-line entry points with four whole-brain trials at seed 631301:

| Trial | Spikes | MN9 Hz |
|---|---:|---:|
| Baseline | 13,793 | 87 |
| Identical-seed replay | 13,793 | 87 |
| No input | 0 | 0 |
| Outgoing-only MN9 lesion | 13,570 | 76 |

Replay spike tables, rates and delivered events matched exactly. Baseline and lesion scheduled inputs matched exactly. All 127,400 neurons appeared in rate tables, counts agreed with spikes, and every saved output hash passed. MN9 can still fire after an outgoing-only lesion; it is not voltage-clamped.

The tests also rejected all-missing and one-missing jobs, an occupied worker lock, altered configuration, and corrupt output. Resuming a completed real trial preserved file hashes and modification times. Corruption was introduced only in a disposable copied study. The original evidence was preserved.

Peak local worker RSS was about 2.84 GB; measured trial time was approximately 12–17 seconds, excluding some process startup and verification overhead. Four trial directories totaled about 4.23 MB. Those figures do not predict exact CCR performance. The default 2.8 GB notebook allocation is inadequate even before Jupyter overhead.

The final ZIP received extraction, CRC and payload-hash checks. It differs from the simulation-tested predecessor only in corrected library prose; Python/shell code, model inputs, scientific design, requirements and notebook code cells are identical. The exact relation is recorded in `ccr_release_verification_20260922/verification.json`. No simulations were repeated solely for that prose correction.

## Prepared follow-up

The user specified OnDemand and supplied account `smuldoon`, cluster UB-HPC and partition general-compute. The deliverable is `Connectome_CCR_Notebook.zip`, 95,169,881 bytes, containing the notebook, all three model inputs, code, dependency pins, instructions and hashes. No historical trial outputs or virtual environment are included. Suggested initial allocation: four cores, 16,000 MB RAM, four hours, no GPU, with two simulation workers. Use the Jupyter application's supported architecture and the allocation's actual valid QoS. [CCR OnDemand](https://docs.ccr.buffalo.edu/en/latest/portals/ood/), [CCR jobs](https://docs.ccr.buffalo.edu/en/latest/hpc/jobs/), [CCR modules](https://docs.ccr.buffalo.edu/en/latest/software/modules/).

The notebook first checks the environment and files and runs the four smoke trials. It then prepares 350 descriptive jobs: ten shared fresh seeds, five network settings and seven conditions. Settings are default, overall weights multiplied by 0.8 or 1.2, and inhibitory weights alone multiplied by 0.8 or 1.2. Conditions are baseline, mode, mode without MN9, MN9 alone, and motor_003/004/005. These are the first named representatives of the three previous response groups, not new random controls. Selection occurred after earlier outcomes, and the design says so.

This addresses two useful questions: whether the footprint is sensitive to modest changes in model weights, and whether including MN9 explains much of the response. The scale factors are sensitivity choices, not estimated biological uncertainty. Every lesion uses the baseline for its own variant and seed. Support membership stays fixed. Analysis reports A, F, whole-brain absolute response, MN9 change and conditional whole-seed bootstrap intervals, with no reference p-values. A has different denominators for one, 50 and 51 cells. Removing MN9 is not an additive causal decomposition in a recurrent model.

Actual preparation through the extracted helper successfully froze all 350 jobs locally. The study itself has not been run. The controller uses the existing OnDemand allocation, two workers, per-process timeouts, a three-hour budget and a STOP file; it does not submit additional Slurm jobs. Collection rejects incomplete studies. Local unit tests check the 350-job pairing and a known-answer collector example, including missing and corrupt output rejection.

Validation: the full suite passed 231 tests with three skipped, then the additional known-answer collection test passed in the eight-test targeted suite (232 distinct passing tests across these runs). The 40 full-suite warnings were Brian2/pyparsing deprecations. No CCR login, clean Linux installation, Slurm cancellation/requeue, Cython equivalence or confirmatory inference has been tested here.

The revised scientific question remains exploratory: how localized and robust is the selected structural support's effect in this particular model? It does not yet establish a dynamic eigencircuit or a biological behavioral circuit. The distinction from an experimentally estimated effectome remains important. [Pospisil et al. 2024](https://www.nature.com/articles/s41586-024-07982-0).
