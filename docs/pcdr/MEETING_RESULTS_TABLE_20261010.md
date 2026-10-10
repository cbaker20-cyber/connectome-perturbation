# Meeting results and explanation guide — 10 October 2026

**Original eigencircuit question ([PLAN.md](PLAN.md#question)):** Do concentrated eigenvector supports of the materialization-630 Shiu matrix predict localized firing-rate responses to output lesions, beyond connectivity, strong connections, and recruitment?

**Main finding:** the selected 51-cell group has a larger descriptive localized response than the fixed comparison groups under default settings. **Main unresolved problem:** the declared numerical convergence criteria failed, and the comparison groups do not isolate eigenvector membership from other influential features. The original eigencircuit hypothesis remains unresolved.

This is a consolidated table of research stages, with detailed numeric tables below. Related software checks are grouped by the research result they validate; this is not a claim that every unit test is a separate experiment. Source links retain all per-seed rows, failures and protocols. Counts from different stages reuse seeds, conditions and reference runs; do not add them into an independent sample size. Prepared with Codex assistance for explanation, not as an independently authored submission.

**How to use this in the meeting:** start with the short table below, explain convergence using section 2, then show the numeric tables in section 8. Sections 3–7 are the complete stage-by-stage lookup; section 9 gives direct answers to likely questions.

| Main result to show | Number or outcome | Convergence status | One-sentence explanation |
|---|---|---|---|
| Smaller-step CCR pilot, current | 27 software tests passed; mode reference worker active at 0.0001 ms on cpn-d02-23 (user-supplied terminal output) | Pending; no new convergence result | New 0.00005/0.000025 ms probes and twelve scientific trials are planned behind reproduction/time gates; completion not confirmed. |
| Selected group at finest tested step | A=22.508 Hz; F=22.977% | Full agreement failed | The response is more concentrated than the fixed comparators, but most remains outside the group. |
| Full numerical study | 0/18 groups meet the full rule | FAILED | Smaller steps still change the detailed response more than the declared tolerances allow. |
| Baseline disagreement | Median final-halving L1=578.5 summed Hz | Failed criteria unchanged | The unlesioned network also changes with resolution; this is not solely a lesion issue. |
| Separate G/H removals | Coarse new recruitment falls from 7,623 to one cell under either removal | Not established | Either connection can interrupt the selected burst, but this does not establish a converged mechanism. |
| Actual-history local replays | 112 native baseline target prefixes match saved spike ticks | Reproduction only | We can reproduce selected local outputs using the recorded inputs; that is not full-network convergence. |
| CB4058 source lead | Largest inhibitory contributor in 16 selected cases across six targets | Conditional analysis only | Inhibition and reset history help explain selected states, but the initiating cause is unresolved. |

## 1. Terms to explain before presenting results

| Term | Plain explanation | Important boundary |
|---|---|---|
| Connectome | A map of neurons and their connections. Here, a signed matrix uses modeled positive and negative connection effects. | One anatomical reconstruction and model assumptions, not a direct measurement of all physiology. |
| Eigenvector / mode | A pattern of weights over neurons that the connectivity matrix maps to a scaled version of itself. | A structural pattern need not be a functional circuit in the spiking model. |
| Support | The smallest ranked set containing 75% of that eigenvector's squared magnitude; selected support has 51 cells. | The 75% selection rule does not predict 75% of the lesion response will stay there. |
| Outgoing lesion | Set selected cells' outgoing connection weights to zero. | Cells can still receive input and fire. This is not clamping their firing to zero. |
| Baseline / paired response | Compare lesion with unlesioned network using the same scheduled physical input events. Response is lesion minus baseline for each neuron. | Same random seed alone was insufficient in early work; saved input events were checked. |
| Seed | One realization of the simulated input. | Thirty seeds are not thirty flies. |
| A, internal response | Average magnitude of the rate change inside the selected set, in Hz. For the primary mean, first average signed changes across seeds, then take magnitudes. | A is not the whole-network response and not the mean of per-seed magnitudes. |
| F, concentration | Fraction of total absolute mean rate change inside the set. F=0.23 means about 23% inside and 77% outside. | Larger than a comparator does not mean isolated. If total change is zero, F is undefined. |
| L1 distance | Add up absolute differences, so increases and decreases do not cancel within that sum. | Summed Hz across neurons is not a typical neuron's firing rate or net population change. |
| Relative L1 | Divide that difference by the finer reference magnitude, with the frozen denominator floor. | It is a numerical disagreement measure, not a p-value. |
| Population trace | Total spikes in consecutive 10-ms windows. | Equal population totals can hide different neurons or spike times. |
| Recruitment | A neuron starts firing according to the specified window/rule. | Any-spike baseline recruitment differs from newly recruited cells in the burst window; use each table's definition. |
| Refractory interval / reset | After a spike, this model resets voltage and drive and imposes a 2.2-ms non-firing interval; specified incoming writes are blocked then. | Different reset histories change how later inputs contribute. |
| Conditional reconstruction | Calculate a target's state from saved network inputs, with the stated reset rule. | Does not rerun network feedback or prove an isolated causal effect. |
| Comparator matching | Choose other cell sets similar on recorded features such as connection counts, strength and baseline activity. | Similar means do not ensure similar distributions; overlapping sets are not independent random controls. |
| Degree / strength | Degree counts connections; strength sums their weights under the recorded sign/absolute-weight definition. | A neuron can have many weak connections or a few strong ones. They are distinct alternative explanations. |
| SMD / CDF gap / variance ratio | SMD compares means in spread units; CDF gap compares cumulative distributions; variance ratio compares spread. | Matching one does not guarantee matching the others. A large variance ratio indicates unequal spread. |
| P / D / C / R | P: extra prediction from mode membership; D: degree/strength; C: concentrated strong connections; R: recruitment under input. | These explanations overlap; they are not four exclusive answers. |
| Bootstrap interval / BH adjustment | Bootstrap resamples seeds to describe conditional uncertainty; BH adjusts a family of statistical tests for multiple comparisons. | Neither removes selection bias, numerical error or model limitations. |

## 2. What convergence means here

**Meeting wording:** “We make the simulation timestep smaller while keeping the physical experiment fixed. If the quantities used for our claim agree within the declared tolerances over successive refinements, we have evidence of numerical agreement over that range. Our full criteria did not pass.”

The timestep is how often the model checks and updates its clocked events. Exact integration between events does not make threshold crossings, resets and delayed-event trajectories independent of that clock. The fine study used 0.0008, 0.0004, 0.0002 and 0.0001 ms. A smaller step is not automatically the exact answer.

| Check | Frozen requirement | Selected default mode, final halving | Meaning |
|---|---|---|---|
| A | Difference ≤ max(1 Hz, 5% of finer A) | 24/30 individual pairs pass | Internal amplitude often close, but not enough for the full rule. |
| F | Absolute difference ≤0.01; undefined fails | 28/30 pass | One percentage point, not 1% relative change. |
| Full paired response vector | Relative L1 ≤0.05 | 1/30 pass; median difference 13.73% | The neuron-by-neuron response remains step sensitive. |
| Population time courses | 10-ms relative L1 ≤0.05 for both baseline and lesion | 1/30 pass; reported median population difference 15.41% | Activity over time remains step sensitive. |
| Full group | Passing mean response plus ≥95% individual passes under the joint rule | 1/30 joint passes; need 29/30 | **FAILED.** |
| Final study decision | Both final successive halvings meet the rule | Neither establishes the required result | **Convergence not established. All 18 condition-by-halving groups failed.** |

These tolerances permit different individual spike times; failure is not merely failure of exact spike identity. Stable means can hide individual disagreements because signed seed differences can cancel. Conversely, exact replay at one timestep demonstrates reproducibility of that calculation, not agreement across timesteps. The frozen [criteria](CCR_FINE_PLAN.json), [fine report](FINE_TIMESTEP_RESULTS_20261005.md) and [component review](OVERNIGHT_DECISION_20261009.md) remain authoritative.

Every research row below has a convergence column. **Not tested** is not a pass or a retroactive failure of that specific experiment. **Not applicable** means the task is structural or analytical rather than a timestep experiment; downstream simulated claims still need numerical support. **Not established** means a limited cross-step or diagnostic result does not satisfy the full requirement.

## 3. Original selection and lesion experiments

| Test and source | Completed result | Convergence status | What to say / limitation |
|---|---|---|---|
| [Input pairing and pipeline](RESEARCH_OVERVIEW.md), 18–19 Sep | Early input-pairing failure corrected; invalid runs preserved and excluded from valid paired-lesion evidence. | Not tested by pairing checks. | “We verified actual input schedules rather than trusting the seed.” This fixes a known early problem, not every later numerical issue. |
| [Correlation, clustering and initial individual lesions](RESEARCH_OVERVIEW.md) | Clustering sensitive to bins/surrogates; 720 single-cell jobs completed. One of 40 secondary tests passed BH; none of the MN9 tests did. | Not tested in this stage. | Correlated firing and clustering do not establish an eigencircuit. Failure of a significance test is not proof of no effect. |
| [Original eigenmode screen](RESEARCH_OVERVIEW.md) | 40 eigenpairs; 22 stable complete modes, but first 20 had no baseline-spiking support cells. No eligible candidate. | Eigensolver checks are separate from dynamical convergence. | The original selection stopped; do not present it as a successful confirmatory screen. |
| [Exploratory deeper screen](RESEARCH_OVERVIEW.md) | 80 eigenpairs / first 40 stable complete modes; four eligible. Selected zero-based rank 33, support 51. | Not applicable to structural selection. | Candidate selection was broadened exploratorily. Only one selected mode's lesion study follows. |
| [Optimized pilot](OPTIMIZED_PILOT_RESULTS_20260921.md) | 35 trials; mode A=22.576 Hz, F=0.2294; larger A/F than five fixed alternatives. | Not tested at multiple steps in this pilot. | Supports a descriptive comparison, not calibrated significance against random matched sets. |
| [Fresh-seed replication](SEED_REPLICATION_RESULTS_20260922.md) | 210 trials; mode A=22.544 Hz, F=0.2312; ordering persists. | Seed replication is not timestep convergence. | New inputs reproduce ordering for the same selected memberships; comparator bias remains. |
| [Motor-composition pilot](MOTOR_COMPOSITION_RESULTS_20260922.md) | Nine comparison memberships; 55 trials; only three distinct response patterns. Mode A=22.604, F=0.2324. | Not tested in this stage. | Matching motor counts did not match identity/distributions. Nine sets are not nine distinct response replications. |
| [Expanded sensitivity grid](CCR_RESULTS_20260927.md) | 3,390 trials verified. Across nine weight settings, mode A exceeds three comparisons in 27/27 contrasts, F in 26/27. | Broad grid not established converged; later selected numerical studies show sensitivity. | One F exception occurs at weight1.2/inhibition0.8; do not call superiority universal. |
| [MN9 and component lesions](CCR_RESULTS_20260927.md) | Default MN9 rate change: full mode −82.47 Hz; mode without MN9 −82.40; MN9 alone +1.47. | Component comparison at original setting not established converged. | Directly removing MN9 outputs is not required for its large rate decrease under the combined lesion. Different supports prevent treating A/F as additive effects. |
| [Expanded individual lesions](CCR_RESULTS_20260927.md) | 22/51 cells have zero total rate response in every default paired seed; others can have large effects. CB4058 total absolute mean response 1,898.63 summed Hz. | Not independently established converged for these single-cell results. | Zero rate change does not mean identical spikes or biological irrelevance. CB4058 influence was already known at the older step. |
| [Active29 versus full51](CCR_RESULTS_20260927.md) | Mean vectors differ by 79 summed Hz, 1.5852%; signed cosine0.999896 at default0.1 ms. | One-step descriptive comparison; no equivalence/convergence claim. | Active cells reproduce much of this footprint; selected using the same baselines, not a held-out result. |

## 4. Numerical studies and recorded-state checks

| Test and source | Completed result | Convergence status | What to say / limitation |
|---|---|---|---|
| [101-trial replay/step study](CCR_RESULTS_20260927.md) | All 25 exact replays match; selected large effects change substantially across0.1/0.05/0.025 ms. MN9-only effect is non-monotonic. | Not established. | “The large responses are reproducible at a fixed step, but finer steps do not give a consistent trajectory.” |
| [530-trial resolution study](CCR_RESULTS_20260927.md) | Four exact replays match; default mode mean A22.503/22.282/22.309 at 0.1/0.05/0.025 ms. Selected altered cases remain unstable. | Not established. | Stable aggregate A does not validate all neuron responses or altered parameters. |
| [Four instrumented full-network replays](CCR_RESULTS_20260927.md), 28 Sep | Exact spike/input matches. Selected lesion has629,557 versus 17,959 spikes at 0.0125/0.00625 ms. | Recording fidelity passed; convergence not established. | Recorder did not cause the difference. Counts are full-second totals, not lesion-minus-baseline responses. |
| [Recording coverage and recruitment](CCR_RESULTS_20260927.md), 29 Sep | Ten recorded cells account for about 0.103% of large-run spikes. 11,530 cells fire only in large run;577 recruit before 180 ms. | Diagnostic of step-sensitive outputs, not convergence. | The early monitored cells missed most later recruitment; groups/windows were outcome-informed. |
| [Saved incoming-event reconstruction](CCR_RESULTS_20260927.md) | 4.8 million recorded cell/tick increments agree within 1e−9 mV; max error 5.68e−14 mV. | Reconstruction check, not convergence. | Validates event accounting in recorded cases, not complete voltage dynamics or initiating cause. |
| [Early recruited-cell drive/source analysis](CCR_RESULTS_20260927.md) | Larger positive increments in 576/577 selected cells; negative magnitude also increases. Ten early targets lack positive arrivals from the defined early group in preceding20 ms. | Conditional analysis; convergence not assessed. | Does not support a blanket loss-of-inhibition explanation or a universal early-group trigger. |
| [620-trial fine study](FINE_TIMESTEP_RESULTS_20261005.md) | 600 default + 16 altered + 4 replays; all saved-output checks complete. Mode mean A≈22.5 Hz and F≈23%; all 18 full groups fail. | **FAILED declared agreement.** | Main numerical result. Finest step is not certified as exact. |
| [Same-step contrast audit](RESEARCH_CONTINUATION_20261008.md) | Mode A/F exceed all three fixed comparators for all 30 seeds at all four fine steps. | Ordering persists; full convergence still failed. | Strong descriptive ordering under this design, not eigencircuit specificity. |
| [Step versus seed differences](FINE_DIFFERENCES_20261005.md) | Mode median same-seed cross-step L1=693.5 Hz versus different-seed1,009 Hz; ratio 0.687. Bin size changes apparent divergence time. | Failed criteria unchanged. | Numerical differences smaller than seed differences does not make them acceptable. Seed pairs share observations. |
| [Two burst-state recordings](DIAGNOSTIC_RESULTS_20261005.md) | Both750-ms replays match original events;34 cells recorded600–750 ms;68 cell/run crossing checks pass. | Recorder validated; convergence not established. | States are available for selected cells/windows, not the whole initiating history. |
| [Recorded event/voltage equations](DIAGNOSTIC_EVENT_RESULTS_20261006.md) | Recurrent increments and subthreshold updates agree to about1e−13 mV or better; resets match. Two upstream spikes dominate one selected crossing's positive contribution. | Implementation check; no convergence claim. | Explains immediate recorded input, not necessity for the burst. |
| [Time-zero upstream reconstruction](UPSTREAM_INPUT_CHECKS_20261006.md) | Three never-fired targets reconstructed from rest; coarse first crossings versus finer subthreshold states. | Conditional state calculation, not convergence. | Known initial state avoids guessing prior resets; inputs still come from saved network trajectories. |
| [Source reset histories](SOURCE_RESET_CHECKS_20261006.md) | Twelve source voltage evaluations match recordings; CRE011 input is largest positive contribution at four coarser crossings. | Conditional state calculation, not convergence. | Starting at the last reset handles prior firing; still no isolated initiating-cause test. |

## 5. Connection interventions and local propagation

G and H denote two connections from source 720575940628695043 to targets 720575940629667639 and 720575940623862015. These studies use one selected altered-weight MN9-lesion case, seed 631430. They are not default-mode confirmation. Primary window is **[650,730)ms**, excluding stimulated input cells; “new” means no spike before650ms and at least one in that window.

| Test and source | Completed result | Convergence status | What to say / limitation |
|---|---|---|---|
| [Pair removal from time zero](PATHWAY_RESULTS_20261007.md) | Coarse0.0004 ms:15,093→1,381 window spikes,7,623→0 new cells. Fine0.0002 ms:1,435→1,436 spikes. | Two resolutions disagree in reference behavior; no convergence established. | Suppresses selected late burst but changes earlier history too. |
| [Pair removal at600ms](PATHWAY_RESULTS_20261007.md) | Coarse15,093→1,442 spikes and7,623→1 new cell; fine1,435→1,459. Earlier events match exactly. | No convergence established. | Intervention can act late; not just an artifact of changing all earlier events. |
| [Separate G/H removal](SEPARATE_PATHWAY_RESULTS_20261008.md) | Eight trials complete/verified. Either single removal suppresses broad coarse recruitment; full numeric table below. | No convergence established; original 18 failures unchanged. | Joint removal not required among these interventions; effects are not additive or generalized across seeds. |
| [Early intervention divergence](PATHWAY_DIVERGENCE_20261008.md) | Singles first alter different outside neurons; many later early changes overlap. Finer non-burst case has more early changed neurons. | Diagnostic only. | More early changed neurons does not by itself explain the burst. |
| [Direct routes](PATHWAY_ROUTES_20261008.md) | Six earliest outside differences each have one changed incoming emission able to arrive first. | No convergence test. | Localizes first changed input, not complete network mechanism. |
| [Conditional downstream states](DOWNSTREAM_CROSSINGS_20261009.md) | All six endpoint checks support reference crossing versus intervention below threshold. | No convergence test. | Uses saved reset history, so follow-up local replay was needed. |
| [Local replay generating resets](OVERNIGHT_DECISION_20261009.md) | All 12 target prefixes reproduce every saved spike tick; four distinct target/step situations. | Exact local reproduction only. | Target evolves itself with fixed archived incoming spikes; network feedback and full late aftermath are not reproduced. |

## 6. Default-network disagreement and latest source lead

| Test and source | Completed result | Convergence status | What to say / limitation |
|---|---|---|---|
| [Baseline/lesion decomposition](STEP_CANCELLATION_20261009.md) | Final-halving median baseline L1=578.5 Hz, lesion309.5 Hz, paired693.5 Hz. Pooled cancellation≈19%. | Failed criteria unchanged. | Baseline itself changes across steps. Medians cannot be added to assign a causal fraction. |
| [Which neurons differ?](BASELINE_COUNTS_20261009.md) | 96.43% of pooled baseline L1 belongs to cells active at both steps. | Failed criteria unchanged. | Mostly different counts in shared active cells, not merely different recruited identities. |
| [Endpoint test](BASELINE_TIME_20261009.md) | At least97.45% L1 remains after arbitrary deletion of saved final1-ms spikes; differences substantial before 900 ms. | Failed criteria unchanged. | Rules out a narrow last-window explanation, not all earlier timing effects or unobserved future spikes. |
| [Early timing replay](BASELINE_REPLAY_20261009.md) | 30 selected seeds;60 native prefixes match. Common fine grid with coarse input changes timing but no short-prefix counts. | Local reproduction, not convergence. | Early timing selection did not explain later count gaps; retain this negative result. |
| [Count-selected replay](BASELINE_REPLAY_20261009.md) | 26 cases/15 targets, four seeds absent;52 native prefixes match. Coarse history at fine dt retains coarse count in26/26. | Local reproduction, not convergence. | Differing upstream history carries these local count differences; does not locate its first cause. |
| [Constructed timing/count mixtures](HISTORY_PARTS_20261009.md) | Results depend on pairing rule in21/26; many constructed histories violate source refractory spacing. | Not a valid convergence or unique attribution test. | Stop this branch; cannot assign a unique timing-versus-count causal percentage. |
| [Exact shared-event gating](BASELINE_GATING_20261010.md) | Zero acceptance differences among366exact shared events, only1.54%coverage. | No convergence test. | Narrow negative finding cannot exclude effects involving shifted events. |
| [First cumulative two-spike gaps](COUNT_CROSSINGS_20261010.md) | All 26 other-run cells outside refractoriness but below threshold;17 below rest. 78 states and923 source contributions checked separately. | Conditional reconstruction, not convergence. | Immediate lack of firing is subthreshold state, not being refractory at that instant; earlier refractory history still matters. |
| [CB4058 actual histories](CB4058_HISTORY_20261010.md) | Largest inhibitory contribution 16 cases/six targets. Latest arrival retained 19 other versus 6 leading histories; more negative other contribution 17, equal7, opposite2. | Conditional reconstruction, not convergence. | Source timing and target resets both differ; voltage contribution is not the effect of removing this neuron. |
| [Repeated-target sensitivity](CB4058_HISTORY_20261010.md) | Across15 targets, median contribution difference negative 8/zero 6/positive 1. Remove most repeated target:10 negative/6 equal/1 opposite. | Descriptive regrouping; no convergence test. | Lead extends beyond one repeated target but is neither universal nor independently replicated. |
| [Source comparison membership](CB4058_HISTORY_20261010.md) | CB4058 is in mode, absent all three fixed controls; old individual effect already known. | Structural membership not a timestep test. | Influential-cell explanation remains an alternative to eigenvector-specific organization. |

## 7. Comparison-design feasibility: why more controls are not automatically better

| Test and source | Completed result | Convergence status | What to say / limitation |
|---|---|---|---|
| [Motor pool and distribution audit](RESEARCH_OVERVIEW.md) | Eight eligible active excitatory motor alternatives are forced into every exact-strata set; mean balance leaves distribution imbalance. | Not applicable: structural selection. | Repeatedly optimizing the same scarce pool does not create independent controls. |
| [New lower-overlap witnesses](RESEARCH_CONTINUATION_20261008.md) | Twelve alternatives found under the recorded design; not simulated. | Not tested dynamically. | Feasible membership is not an observed lesion result. |
| [Distribution matching](DISTRIBUTION_MATCHING_20261008.md) | Pools 538/999; uncapped gap 8/51; capped gap improves11/51→10/51, incoming-degree variance worsens. Exact strata force gap≥5/51. | Not applicable to optimization; simulations unrun. | Improving one matching feature can worsen another. CDF gap is maximum difference between cumulative feature distributions. |
| [Saved-family capacity](FAMILY_CAPACITY_20261008.md) | All 19 candidates checked: overlap cap 30 permits only one set with CDFgap≤11/51; three-set family needs≥16/51. | Not applicable. | Limitation of saved family, not proof that full-pool alternatives are impossible. |
| [Joint search](JOINT_FAMILY_20261008.md) | Solver limit reached without a feasible incumbent or reported bound. | Not applicable. | Unresolved, not proof of impossibility. |
| [Fixed anchors](ANCHOR_FAMILY_20261008.md) | Both tested anchors fail partner construction; separate bound requires≥32 shared cells versus cap 30. | Not applicable. | Infeasibility applies to these anchors/constraints, not every possible design. |
| [Removing old-reference caps](REFERENCE_ABLATION_20261008.md) | Two pairs feasible with30 shared cells, but partner degree-variance ratios9.14–10.43. | Not tested dynamically. | Feasible under weaker constraints; poor distribution balance remains. |

## 8. Numeric tables to show

The following tables reproduce saved result rows; they do not rerun simulations. Each carries a convergence status. Historical A/F support definitions differ between component lesions; compare only under the stated design.

### Pilot: all six lesion sets

Source: [OPTIMIZED_PILOT_RESULTS_20260921](OPTIMIZED_PILOT_RESULTS_20260921.md).

| Set | A Hz | F | MN9 change Hz | Motor total change Hz | Motor mean change Hz  Convergence status |
|---|---:|---:|---:|---:|---:---|
| mode | 22.576 | 0.2294 | -82.2 | 27.6 | 0.325  Not tested in pilot |
| optimized_000 | 11.486 | 0.1853 | -4.2 | -406.2 | -4.779  Not tested in pilot |
| optimized_001 | 12.894 | 0.2162 | -1.2 | -440.8 | -5.186  Not tested in pilot |
| optimized_002 | 16.467 | 0.1936 | -20.0 | -671.4 | -7.899  Not tested in pilot |
| optimized_003 | 13.753 | 0.2147 | -2.6 | -419.0 | -4.929  Not tested in pilot |
| optimized_004 | 14.502 | 0.1863 | -17.4 | -597.4 | -7.028  Not tested in pilot |

### Fresh-seed replication: all six lesion sets

Source: [SEED_REPLICATION_RESULTS_20260922](SEED_REPLICATION_RESULTS_20260922.md).

| Set | A Hz | F | MN9 change Hz | Motor total change Hz | Motor mean change Hz  Convergence status |
|---|---:|---:|---:|---:|---:---|
| mode | 22.544 | 0.2312 | -82.633 | 39.267 | 0.462  Seed replication only |
| optimized_000 | 11.341 | 0.1855 | 0.367 | -353.800 | -4.162  Seed replication only |
| optimized_001 | 12.664 | 0.2168 | -1.700 | -418.033 | -4.918  Seed replication only |
| optimized_002 | 15.758 | 0.1968 | -16.367 | -607.800 | -7.151  Seed replication only |
| optimized_003 | 13.080 | 0.2079 | 0.467 | -362.433 | -4.264  Seed replication only |
| optimized_004 | 14.172 | 0.1867 | -19.500 | -580.867 | -6.834  Seed replication only |

### Motor-composition pilot: all ten lesion sets

Source: [MOTOR_COMPOSITION_RESULTS_20260922](MOTOR_COMPOSITION_RESULTS_20260922.md).

| Set | A (Hz) | F | MN9 change (Hz) | Motor total change (Hz)  Convergence status |
|---|---:|---:|---:|---:---|
| mode | 22.604 | 0.2324 | -81.8 | 20.0  Not tested in pilot |
| motor_003 | 12.059 | 0.1940 | 0.2 | -480.4  Not tested in pilot |
| motor_004 | 12.969 | 0.1985 | -3.2 | -503.2  Not tested in pilot |
| motor_005 | 12.722 | 0.1959 | -0.6 | -487.8  Not tested in pilot |
| motor_006 | 12.059 | 0.1940 | 0.2 | -480.4  Not tested in pilot |
| motor_007 | 12.969 | 0.1985 | -3.2 | -503.2  Not tested in pilot |
| motor_008 | 12.722 | 0.1959 | -0.6 | -487.8  Not tested in pilot |
| motor_009 | 12.059 | 0.1940 | 0.2 | -480.4  Not tested in pilot |
| motor_010 | 12.969 | 0.1985 | -3.2 | -503.2  Not tested in pilot |
| motor_011 | 12.722 | 0.1959 | -0.6 | -487.8  Not tested in pilot |

### Expanded study: default component and comparison means

Source: [CCR_RESULTS_20260927](CCR_RESULTS_20260927.md).

| Lesioned set | A, Hz | F | Total absolute change, summed Hz | MN9 change, Hz  Convergence status |
| --- | ---: | ---: | ---: | ---: ---|
| Mode, 51 cells | 22.503 | 0.23029 | 4983.57 | -82.47  Not established |
| Mode without MN9, 50 cells | 21.276 | 0.21378 | 4976.23 | -82.40  Not established |
| MN9 alone | 1.467 | 0.00831 | 176.50 | +1.47  Not established |
| Comparison 003 | 12.078 | 0.19564 | 3148.67 | -4.87  Not established |
| Comparison 004 | 12.540 | 0.20003 | 3197.13 | -4.13  Not established |
| Comparison 005 | 12.486 | 0.19735 | 3226.70 | -5.10  Not established |

### Fine study: selected-mode averages at all four steps

Source: [FINE_TIMESTEP_RESULTS_20261005](FINE_TIMESTEP_RESULTS_20261005.md).

| Step (ms) | A (Hz) | F, expressed as percent | Mean MN9 rate change (Hz)  Convergence status |
| --- | ---: | ---: | ---: ---|
| 0.0008 | 22.443 | 23.085% | -80.567  Full agreement FAILED |
| 0.0004 | 22.535 | 23.057% | -82.600  Full agreement FAILED |
| 0.0002 | 22.635 | 23.033% | -83.000  Full agreement FAILED |
| 0.0001 | 22.508 | 22.977% | -82.233  Full agreement FAILED |

### Finest-step default comparisons

All values at 0.0001 ms. F is expressed as a percent. Source: [fine results](FINE_TIMESTEP_RESULTS_20261005.md).

| Set | A (Hz) | F (%) | Full convergence status |
|---|---:|---:|---|
| Mode | 22.508 | 22.977 | FAILED |
| motor_003 | 12.140 | 19.663 | FAILED |
| motor_004 | 12.548 | 19.730 | FAILED |
| motor_005 | 12.540 | 19.481 | FAILED |

About 77% of the mode's absolute mean response lies outside the support. This is relative localization, not confinement.

### All 18 full agreement groups

Three adjacent halvings × six condition/variant groups = 18. Four default groups each use 30 paired seeds; two altered-weight groups each use one selected seed. The two altered groups are different lesions/seeds, not a population sample. Each lesion is paired with its same-step baseline. Passing the mean column alone is insufficient. Values below come directly from the independently checked saved agreement summary.

| Variant / lesion | Step change (ms) | Mean-vector relative L1 (%) | Mean response check | Joint individual passes | Full agreement |
|---|---|---:|---|---:|---|
| default / mode | 0.0008 → 0.0004 | 2.95 | Pass | 0/30 | FAILED |
| default / motor_003 | 0.0008 → 0.0004 | 4.79 | Pass | 0/30 | FAILED |
| default / motor_004 | 0.0008 → 0.0004 | 5.88 | Fail | 0/30 | FAILED |
| default / motor_005 | 0.0008 → 0.0004 | 5.07 | Fail | 0/30 | FAILED |
| w120_i080 / mode_without_mn9 | 0.0008 → 0.0004 | 19.20 | Fail | 0/1 | FAILED |
| w120_i080 / mn9_only | 0.0008 → 0.0004 | 100.35 | Fail | 0/1 | FAILED |
| default / mode | 0.0004 → 0.0002 | 2.91 | Pass | 0/30 | FAILED |
| default / motor_003 | 0.0004 → 0.0002 | 6.05 | Fail | 0/30 | FAILED |
| default / motor_004 | 0.0004 → 0.0002 | 4.31 | Pass | 0/30 | FAILED |
| default / motor_005 | 0.0004 → 0.0002 | 4.23 | Pass | 0/30 | FAILED |
| w120_i080 / mode_without_mn9 | 0.0004 → 0.0002 | 17.96 | Fail | 0/1 | FAILED |
| w120_i080 / mn9_only | 0.0004 → 0.0002 | 26082.90 | Fail | 0/1 | FAILED |
| default / mode | 0.0002 → 0.0001 | 2.21 | Pass | 1/30 | FAILED |
| default / motor_003 | 0.0002 → 0.0001 | 5.10 | Fail | 1/30 | FAILED |
| default / motor_004 | 0.0002 → 0.0001 | 3.56 | Pass | 0/30 | FAILED |
| default / motor_005 | 0.0002 → 0.0001 | 3.29 | Pass | 1/30 | FAILED |
| w120_i080 / mode_without_mn9 | 0.0002 → 0.0001 | 14.23 | Fail | 0/1 | FAILED |
| w120_i080 / mn9_only | 0.0002 → 0.0001 | 113.03 | Fail | 0/1 | FAILED |

`w120_i080` means overall connection multiplier 1.2 and additional inhibitory multiplier 0.8: inhibitory weights become 0.96 times default. Differences above 100% are possible; the denominator is the finer response magnitude, not a maximum possible distance. Source: [checked agreement](../../results/pcdr/fine_verified_20261005/checked_agreement.json).

### Separate G/H interventions: all eight primary results

Source: [SEPARATE_PATHWAY_RESULTS_20261008](SEPARATE_PATHWAY_RESULTS_20261008.md).

| Step (ms) | Connection removal at 600 ms | Non-input spikes | Newly recruited cells  Convergence status |
|---|---|---:|---:---|
| 0.0004 | None | 15,093 | 7,623  Not established |
| 0.0004 | Both | 1,442 | 1  Not established |
| 0.0004 | G only | 1,388 | 1  Not established |
| 0.0004 | H only | 1,489 | 1  Not established |
| 0.0002 | None | 1,435 | 4  Not established |
| 0.0002 | Both | 1,459 | 6  Not established |
| 0.0002 | G only | 1,388 | 6  Not established |
| 0.0002 | H only | 1,388 | 6  Not established |

## 9. Questions you should be ready to answer

| Question | Direct answer |
|---|---|
| “Did you find an eigencircuit?” | “We found a selected structural support with a larger descriptive localized lesion response. We have not established that eigenvector membership explains it beyond influential cells, connectivity and recruitment.” |
| “Did anything work?” | “Yes: fixed-step reproduction, input pairing, selected state reconstruction and interventions are verified within their scopes. The convergence requirement did not pass.” |
| “Is all the data invalid?” | “No. These are results at the stated model settings. Failed convergence limits resolution-independent claims; it does not erase the recorded observations.” |
| “Was drift just a coding mistake?” | “No specific defect explaining it has been demonstrated. Bounded schedule, reset, delay and replay checks passed. That does not prove every detail correct.” |
| “Why not use only stable averages?” | “That changes the question. An ensemble study needs its own prospective estimand, margins and confirmation design. Stable averages cannot be substituted for the failed individual-response criteria.” |
| “Does suppression prove G or H caused the whole burst?” | “Removing either connection changes the selected burst outcome, but does not prove a unique initiating cause, a shared mediator across seeds, or convergence.” |
| “Why not lesion CB4058 next?” | “It is a concrete lead, but its conditional contribution is confounded with source and reset histories. A new lesion needs a design and numerical interpretation; it will not itself repair convergence.” |
| “What should happen next?” | “Agree on the required numerical claim, then choose one bounded resolution or event-handling study. Comparison validity remains a separate problem.” |

The [next-study proposal](NUMERICAL_DECISION_PROPOSAL_20261010.md) is **not executed**. A candidate three-seed baseline/mode feasibility gate at two further halvings would have12 new trials; the original 30-seed requirement cannot pass on that pilot alone. Illustrative prior-duration scaling gives≈545 worker-hours, not a measured future runtime or approved allocation. No new simulation follows automatically from this guide.
