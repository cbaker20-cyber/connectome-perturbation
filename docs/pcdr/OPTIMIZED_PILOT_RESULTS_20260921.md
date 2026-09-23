# Completed optimized comparison pilot 21 September 2026

## Findings and scope

- All 35 frozen trials completed at 20:07:50 UTC. The independent verifier checked all trial output hashes, 30 baseline/lesion input pairings, six summaries and all six 127,400-neuron footprints.
- The eigen-set had A = 22.576 Hz and F = 0.2294. Both exceed all five optimized comparisons in this pilot. This is descriptive support for the predicted ordering in this selected mode and model context, not confirmation or a calibrated significance result.
- Only 22.94% of the absolute mean response lay inside the eigen-set; 77.06% lay outside. A higher concentration than these comparisons does not establish dynamical independence.
- MN9 changed by -82.2 Hz while total motor firing changed by +27.6 Hz (+0.325 Hz per motor cell). The five comparisons had smaller MN9 reductions but larger total motor reductions. These secondary patterns are model readouts, not feeding behavior.
- MN9 itself is in the eigen-set and excluded from every comparison set by the focal-support exclusion rule. Therefore MN9 membership is not balanced. The MN9 contrast cannot establish a special downstream pathway effect. Output-only silencing removes outgoing weights, not the neuron’s incoming drive; rate changes still arise through network dynamics.
- The eigen-set contains 13 annotated motor cells; the five comparisons contain 5, 4, 3, 3 and 4. Motor-class membership was not matched, so secondary motor contrasts also require this qualification.
- Five comparison sets were optimized from baseline features and share 31–37 cells with one another. The mode was selected in an exploratory expanded search. Five seeds measure limited simulation variability; they are not five animals. No random-reference p-values or new significance tests were computed.

## All six lesion results

| Set | A Hz | F | MN9 change Hz | Motor total change Hz | Motor mean change Hz |
|---|---:|---:|---:|---:|---:|
| mode | 22.576 | 0.2294 | -82.2 | 27.6 | 0.325 |
| optimized_000 | 11.486 | 0.1853 | -4.2 | -406.2 | -4.779 |
| optimized_001 | 12.894 | 0.2162 | -1.2 | -440.8 | -5.186 |
| optimized_002 | 16.467 | 0.1936 | -20.0 | -671.4 | -7.899 |
| optimized_003 | 13.753 | 0.2147 | -2.6 | -419.0 | -4.929 |
| optimized_004 | 14.502 | 0.1863 | -17.4 | -597.4 | -7.028 |

## Seed uncertainty and footprint interpretation

| Set | A bootstrap 95 percent interval | F bootstrap 95 percent interval | Off support absolute sum Hz |
|---|---|---|---:|
| mode | 22.165 to 22.988 | 0.2248 to 0.2326 | 3867.6 |
| optimized_000 | 10.725 to 12.278 | 0.1781 to 0.1879 | 2575.4 |
| optimized_001 | 12.125 to 13.725 | 0.2049 to 0.2221 | 2383.4 |
| optimized_002 | 15.682 to 17.125 | 0.1862 to 0.2008 | 3497.4 |
| optimized_003 | 13.067 to 14.349 | 0.2064 to 0.2179 | 2565.0 |
| optimized_004 | 13.722 to 15.169 | 0.1823 to 0.1894 | 3230.8 |

- Intervals use 2,000 paired-seed bootstrap resamples, seed 630700. They describe seed variation conditional on these fixed sets and the model; they do not cover uncertainty in mode selection, matching, anatomy or model assumptions.
- Aggregate A and F are computed after averaging signed neuron changes across seeds. The single-seed A and F below are descriptive diagnostics; their arithmetic averages are not substitutes for the declared aggregate estimands.

## Every paired seed

| Set | Seed | A single seed | F single seed | MN9 change Hz | Motor total change Hz |
|---|---:|---:|---:|---:|---:|
| mode | 630901 | 22.255 | 0.2231 | -88.0 | 40.0 |
| mode | 630902 | 23.216 | 0.2310 | -86.0 | 25.0 |
| mode | 630903 | 21.941 | 0.2237 | -78.0 | 21.0 |
| mode | 630904 | 23.039 | 0.2324 | -83.0 | -44.0 |
| mode | 630905 | 22.431 | 0.2238 | -76.0 | 96.0 |
| optimized_000 | 630901 | 11.824 | 0.1835 | -8.0 | -408.0 |
| optimized_000 | 630902 | 11.353 | 0.1843 | -12.0 | -425.0 |
| optimized_000 | 630903 | 11.824 | 0.1842 | -3.0 | -432.0 |
| optimized_000 | 630904 | 12.922 | 0.1829 | -4.0 | -405.0 |
| optimized_000 | 630905 | 10.137 | 0.1689 | 6.0 | -361.0 |
| optimized_001 | 630901 | 14.176 | 0.2210 | -1.0 | -423.0 |
| optimized_001 | 630902 | 12.588 | 0.2029 | -9.0 | -441.0 |
| optimized_001 | 630903 | 12.412 | 0.1994 | -2.0 | -442.0 |
| optimized_001 | 630904 | 13.882 | 0.2186 | 1.0 | -491.0 |
| optimized_001 | 630905 | 11.804 | 0.1983 | 5.0 | -407.0 |
| optimized_002 | 630901 | 17.059 | 0.2034 | -15.0 | -603.0 |
| optimized_002 | 630902 | 16.804 | 0.1876 | -27.0 | -705.0 |
| optimized_002 | 630903 | 16.373 | 0.1826 | -23.0 | -728.0 |
| optimized_002 | 630904 | 17.510 | 0.2008 | -23.0 | -737.0 |
| optimized_002 | 630905 | 15.020 | 0.1883 | -12.0 | -584.0 |
| optimized_003 | 630901 | 14.706 | 0.2175 | -14.0 | -490.0 |
| optimized_003 | 630902 | 13.922 | 0.2059 | 0.0 | -385.0 |
| optimized_003 | 630903 | 13.980 | 0.2129 | -1.0 | -455.0 |
| optimized_003 | 630904 | 14.176 | 0.2049 | -10.0 | -457.0 |
| optimized_003 | 630905 | 12.490 | 0.1984 | 12.0 | -308.0 |
| optimized_004 | 630901 | 15.431 | 0.1854 | -19.0 | -595.0 |
| optimized_004 | 630902 | 14.510 | 0.1820 | -24.0 | -583.0 |
| optimized_004 | 630903 | 14.431 | 0.1788 | -13.0 | -643.0 |
| optimized_004 | 630904 | 15.392 | 0.1919 | -26.0 | -658.0 |
| optimized_004 | 630905 | 13.020 | 0.1853 | -5.0 | -508.0 |

## Verification process code and next step

- The queue ran serially from 19:57:10 to 20:07:50 UTC, about 10 minutes 40 seconds including collection. No scientific code, thresholds, seeds or comparison IDs were changed after launch. The original deadline was not reached.
- All 30 scheduled-input digests matched their baselines. Delivered-input digests matched in 30/30 pairs; the scheduled input is the pairing requirement, while delivered events can depend on neuronal refractoriness.
- New verification code: scripts/pcdr_verify_optimized.py, created with Codex assistance on 21 September. It reads frozen jobs and completed trial manifests; checks hashes, supports, seeds and provenance; reconstructs paired rate differences; recomputes A, F, MN9 and motor readouts; compares every footprint with those calculations; and saves the per-seed table and completion audit. It does not simulate or change data.
- Command: .venv/Scripts/python.exe scripts/pcdr_verify_optimized.py. All assertions passed. Did not rerun simulations or introduce post-outcome inferential tests. The frozen model was unchanged; full-array readout comparisons were the relevant completion check.
- Evidence: results/pcdr/optimized_pilot_20260921/amendment.json, jobs.json, analysis/results.json, per_seed_readouts.csv and completion_audit.json. Each trial directory retains spikes, rates, input records and its manifest. The audit records the exact command, code hash and source manifest hashes.
- Recommended next work: an adviser review of the exploratory result and reference-sampling design before confirmation. Check distributional balance and readout membership as design diagnostics. More seeds alone would not make the optimized sets a random null. Any MN9-membership sensitivity would need a separately stated question and amendment, not a revision of this completed result.
- Finished: original single-cell study, matching feasibility audit and this 35-trial descriptive pilot. Pending: justified confirmatory reference sampling, the 199-control/30-seed study, and declared sensitivity/context extensions. No extra computational stage was started. Pause the monitor after the completed handoff.
