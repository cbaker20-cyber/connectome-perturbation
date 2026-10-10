# Connectome research update — 10 October 2026

## Research question
Does concentrated eigenvector support predict localized responses to outgoing-connection lesions beyond connectivity strength and recruitment? The selected support contains 51 cells. The original hypothesis remains unresolved.

| Evidence | Result | Numerical convergence / limitation |
|---|---|---|
| Selected support at the finest completed tested step | A = 22.508 Hz; F = 22.977% | Descriptive result; full agreement failed. Most absolute response remains outside the support. |
| Completed fine-step study | All 18 full agreement groups failed | Convergence is not established. Similar means do not establish agreement of detailed responses. |
| Selected-support final halving | Joint agreement in 1/30 seeds; rule requires 29/30 plus mean checks and both final halvings | Original criteria remain unchanged. |
| Local replay diagnostics | 112 native target prefixes reproduce saved spike ticks | Validates selected replay cases, not full-network convergence or the initiating cause. |
| Current smaller-step CCR pilot | 27 software tests passed; a mode reference worker at 0.0001 ms is active on cpn-d02-23 in supplied terminal output | Reference agreement and new scientific trial completion are not yet confirmed. |
| Prepared finer-step panel | Three original seeds, baseline/mode, 0.00005 and 0.000025 ms; twelve one-second trials | Starts only if reference and capacity gates pass. A three-seed panel cannot satisfy the original thirty-seed criterion. |

## Terms
**Convergence:** the specified results agree within declared tolerances when the simulation timestep is reduced. Passing software tests, repeating a run at the same timestep, and obtaining similar group averages are different checks.

**Timestep:** the interval used by the clocked simulation. Smaller intervals cost more computation and do not guarantee that this model will meet its agreement criteria.

**A:** average absolute paired mean rate response per cell inside the selected support, in Hz. **F:** the fraction of the network's absolute paired mean rate response inside that support. Signed responses are averaged across seeds before taking absolute values.

**Reference/capacity probes:** short 10 ms runs used to compare saved reference events and measure computational requirements. They are not the one-second scientific trials and cannot establish their convergence.

## Current decision
The bounded CCR work ends at 12:30 p.m. Eastern on 10 October. No new convergence result is claimed. Discuss whether the existing individual-response convergence target is necessary for the intended scientific claim, and what evidence would justify further compute. Any separately designed ensemble question must retain the original failed criteria and avoid presenting reused data as fresh confirmation.

Fixed comparison groups overlap and are imperfect controls. Selected local mechanisms are diagnostic, not proof of eigenvector-specific effects or biological function.

Prepared with Codex assistance; terminal status is user-supplied and awaits independent result retrieval. Detailed results and provenance: [meeting results table](MEETING_RESULTS_TABLE_20261010.md), [meeting brief](MEETING_BRIEF_20261010.md), [pilot protocol](SMALLER_STEP_PILOT_20261010.md).
