# Exact shared-event acceptance — 10 October 2026

No refractory-acceptance difference was found among the 366 incoming events shared at exactly the same source ID and physical time in the 26 previously selected baseline target/checkpoint cases. This is a narrow negative result. Those shared events account for only 1.54% of incoming event records when counted on both sides, so the check cannot exclude differences involving shifted arrivals.

## Recorded method and result

Kept all 26 selected targets and four absent seeds from BASELINE_REPLAY_20261009.md. Recorded the method before calculating results. Used actual saved incoming events and saved target spikes; no ordinal matching, altered event histories, new simulation or new selection. Verified prior evidence, source/model connectivity provenance, saved spike hashes and reconstructed arrivals against previously verified arrays.

An incoming event is blocked if it occurs at or after a saved postsynaptic spike and before that spike plus 2.2 ms. The firing tick is blocked and the exact release tick is allowed. This reuses the previously tested scheduling rule. Arrival ticks include the 1.8-ms delay and are represented on the common 0.0001-ms grid. These are model-predicted acceptance states conditioned on saved spikes, not new direct state recordings.

There are 23,862 coarse and 23,813 fine incoming events across the selected prefixes. Exact source/time joining finds 366 common events. All 366 have the same acceptance state at both steps. The coverage fraction is 2×366/(23,862+23,813) = 1.5354%. Each event is specific to one selected target and seed; repeated source events across targets are not independent observations. Unmatched events were retained, not classified as lost or newly generated spikes.

The low exact-match coverage makes this join unsuitable for locating a first general refractory divergence. Changing a target's spike timing changes its refractory intervals, but the present result does not establish whether shifted arrivals fall on different sides of those intervals. No conclusion about absence of refractory amplification follows. A first target spike-time difference is retained in each record only as chronology, not as a threshold-voltage reconstruction or causal onset.

## Checks and decision

Three focused tests passed in 1.35 seconds: exact firing/release boundaries, shifted-event nonmatching, empty histories, and rejection of duplicate events, unsorted spikes and conflicting common-event weights. Separately checked all 47,675 arrival acceptance states using direct membership in saved refractory intervals instead of the producer's search operation. All matched, and the common-event count and zero changed statuses were reproduced.

Full results: results/pcdr/baseline_gating_20261010. [Compact evidence](evidence/2026-10-10/baseline_gating/snapshot.json) preserves protocol, all case summaries, empty changed-event table, provenance and verification, with hashes for full event tables retained locally. Reproduce with `.venv/Scripts/python.exe scripts/pcdr_baseline_gating.py --out <unused-directory>`; tests: `tests/test_pcdr_baseline_gating.py`.

Stop this exact-event join as a general mechanism finder. Do not relax event matching after this negative result to claim a positive mechanism. Further state tracing needs a separately justified design and may remain selected-case diagnosis. With the adviser meeting approaching, the priority is a decision on numerical requirements and the original eigencircuit question, rather than more branching diagnostics. All eighteen original convergence groups still fail; no full-network or CCR run was launched.

Code, analysis, documentation and checks used Codex assistance. Separate arithmetic checks are not independent human review.
