# Full pool refinement 22 September 2026

## Result and meaning

The full eligible pool contains 126,935 cells. The integer solve returned no result before it was stopped externally. This is an unresolved attempt, not evidence of infeasibility. Separate coordinatewise bounds did not rule out any of the six original matching features. These bounds do not establish simultaneous feasibility.

The earlier restricted-pool infeasibility result remains valid for its narrower program. No lesion was run, no comparison set was accepted, and no eigen-support, recruitment cutoff or SMD limit was changed. The prior seed replication remains conditional on its original optimized sets.

## Notes on the method and stopping decision

- User requested continued testing for methodical refinement. Selected a baseline-only full-pool test because the previous nearest-64 candidate restriction could itself cause failure. This tests candidate coverage while retaining the earlier conservative sufficient mean bounds and exact sign, recruitment and annotated motor counts.
- Created scripts/pcdr_fullpool_motor_witness.py with Codex assistance. It replaces nearest-neighbor selection with all eligible cells in the target strata. It excludes the focal support and sugar inputs, uses binary variables, and sends a sparse constraint matrix to HiGHS. Seed 631101; one solve; requested 60-second solver limit and one thread. No automatic lesion stage follows.
- Wrote protocol.json before loading the features or solving. It hashes the code, baseline feature table and fixed mode selection. The inputs match the earlier frozen evidence.
- SciPy warned that threads is not a recognized wrapper option and passed it to HiGHS verbatim. This warning was not a scientific failure. Environment thread counts were also set to one.
- The solver did not return within the requested time limit. The inspected worker had used 145.44 CPU seconds and about 442 MB of working memory at 12:36:23 EDT; it was still active. Its exact command line was checked before stopping that worker. The parent exited with code 1. No solver result or candidate membership file existed.
- Saved terminal_stop.json rather than inventing a solver status. The cause of the time-limit overrun was not diagnosed. Do not assert that presolve caused it. Before another large solve, use a separate wall-clock watchdog that can stop the specific process tree and preserve an explicit incomplete record.

## Separate code guide for the bounds check

- Created scripts/pcdr_fullpool_bounds.py after the stopped attempt. Its protocol was saved before the new calculation. The purpose is to check necessary conditions cheaply, without another optimizer.
- For each nonnegative log1p feature, mean_bounds sorts values within each required stratum. Selecting the required number of smallest values gives the minimum possible mean L; selecting the largest gives maximum U. These are exact for one feature at a time.
- The same calculation on squared values gives an upper bound Q on the second moment. Since the mean is at least L and values are nonnegative, variance is at most Q minus L squared. Different sets can attain these extrema, so combining them gives a conservative upper bound.
- smd_lower_bounds computes the distance of the target mean from the interval [L, U], then divides it by the largest permitted pooled standard deviation under that variance bound. A value above 0.1 would rule out the original matching criterion for that feature. Zero means this bound cannot rule it out.
- Worked example: if every candidate mean is between 2 and 4 and the target mean is 3, the distance is zero. A mean constraint alone cannot reject matching. If the target mean is 5, the minimum distance is 1; the variance bound is then needed to assess the SMD lower bound.
- All six bounds below are zero. The target mean lies inside every single-feature interval. This does not mean one set attains all six intervals together, nor does it remove the forced motor membership limitation.

| Feature | Target log1p mean | Minimum mean | Maximum mean | SMD lower bound |
|---|---:|---:|---:|---:|
| in_degree | 5.500135 | 2.772925 | 6.960353 | 0.0 |
| out_degree | 4.870043 | 2.358120 | 6.695355 | 0.0 |
| in_strength | 8.282067 | 3.901476 | 9.172261 | 0.0 |
| out_strength | 6.755267 | 2.834045 | 8.287805 | 0.0 |
| baseline_hz | 2.152397 | 0.725098 | 2.258768 | 0.0 |
| strong_out_mass | 3.523870 | 0.137598 | 6.712169 | 0.0 |

## Tests and evidence

- Commands from C:/Users/Baker/Drosophila_Data: .venv/Scripts/python.exe scripts/pcdr_fullpool_motor_witness.py; .venv/Scripts/python.exe scripts/pcdr_fullpool_bounds.py; .venv/Scripts/python.exe scripts/pcdr_verify_fullpool.py.
- Test command: .venv/Scripts/python.exe -m pytest tests/test_pcdr_fullpool_bounds.py tests/test_pcdr_matching_audit.py tests/test_pcdr_composition.py tests/test_pcdr_backend_input_check.py -q --disable-warnings. Six tests passed in 0.77 seconds.
- New tests exhaustively enumerate a small stratified pool and verify that every candidate variance and SMD respects the derived bounds. Constant-feature tests cover both a zero difference and a nonzero difference with zero variance. These tests validate the bound calculation, not full-pool feasibility.
- pcdr_verify_fullpool.py independently verifies frozen input/code hashes and recomputes the eligible pool count. It recognizes the saved external stop and does not mistake a missing solver summary for success. Its witness-validation branch was not exercised because no witness exists; do not claim that branch was validated by this run.
- Evidence directory: results/pcdr/fullpool_motor_20260922. Files: protocol.json, terminal_stop.json, bounds_protocol.json, bounds.json and verification.json. Raw bounds include variance upper bounds; the table above is rounded. Export source hashes identify the exact evidence.

## What remains and why

- Do not run new lesions using nonexistent motor-matched sets. The full-pool conservative program and the original pooled-SMD feasible region remain unresolved.
- Next numerical step: implement and test an external timeout, then consider a bounded relaxation or a better-conditioned feasibility formulation before another full integer solve. Freeze that method and budget before execution. A fractional relaxation solution would not be a valid neuron set.
- No simulator suite, fresh eigen-search or CCR benchmark was run: none is needed to validate this baseline-only calculation, and CCR configuration remains pending. Existing simulated results and all earlier editions are preserved.
- This chapter records the failed numerical attempt as well as the completed diagnostic. Code and documentation were created with Codex assistance; no student discovery history is invented.
