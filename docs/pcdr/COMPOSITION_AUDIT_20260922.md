# Baseline composition audit 22 September 2026

- This audit uses baseline features and frozen lesion IDs only. It describes differences that the original mean-balance rules did not constrain. No new simulations or p-values.
- Largest empirical cumulative-distribution gap: 0.275, for optimized_003, in_degree. A gap is a descriptive maximum difference in cumulative proportions, not a significance result.
- The motor label comes from available annotations. Missing annotations remain unavailable; non-motor here includes unavailable classifications and must not be interpreted as a verified biological identity.

| Sign | Recruited | Annotated motor | Needed | Available outside support and inputs |
|---|---|---|---:|---:|
| excitatory | False | False | 7 | 86275 |
| excitatory | False | True | 2 | 52 |
| excitatory | True | False | 9 | 161 |
| excitatory | True | True | 8 | 8 |
| inhibitory | False | False | 13 | 40250 |
| inhibitory | True | False | 9 | 185 |
| inhibitory | True | True | 3 | 4 |

- Every exact motor/sign/recruitment stratum has enough candidates: True. This does not establish simultaneous continuous-feature feasibility.
- Next design step is a separately declared joint matching feasibility check with motor counts added, preserving the original six feature limits. If capacity fails, report it rather than silently merging strata. MN9 membership cannot be exactly matched while the whole focal support is excluded; its secondary interpretation remains limited.
- Code created with Codex assistance: scripts/pcdr_composition_audit.py. ecdf_gap sorts both samples, evaluates cumulative fractions at every unique observed value and returns the largest absolute gap. Main writes a protocol before analysis, then saves all feature quantiles/variances and class counts.
- Evidence: results/pcdr/composition_audit_20260922/protocol.json, distributions.csv, composition.csv, motor_strata_capacity.csv and summary.json. Command: .venv/Scripts/python.exe scripts/pcdr_composition_audit.py. No new distributional acceptance cutoff was chosen from these results.

- The active excitatory motor stratum needs8cells and has exactly8eligible candidates: all8would be mandatory in every exact composition-matched set. Active inhibitory motor counts require3of4. This constrains diversity even though all individual capacities pass. The largest-gap example also has incoming-degree variance ratio4.092 on log1p values while SMD is0.042. Do not interpret passing mean balance as matching the entire distribution.

## Bounded joint feasibility check

- Ran .venv/Scripts/python.exe scripts/pcdr_motor_matching_witness.py after the capacity audit. Separate protocol was written before solving. It reuses the baseline-only binary optimizer, rebuilds nearest64neighbors within sign/recruitment/motor strata, and retains the conservative0.099sqrt(target variance/2) mean bounds. Seed631100; at most5solves,30seconds each.
- First solve returned infeasible, so the declared rule stopped subsequent solves. No candidate control sets or lesions resulted. This certifies infeasibility only of this restricted candidate pool with stricter sufficient mean bounds. It does not prove infeasibility under the original pooled-SMD<=0.1 criterion or the full pool.
- Next justified check: full-pool feasibility or direct original-SMD constraints, with method and budget fixed before execution. Do not infer that motor composition explains the effect, relax thresholds, or substitute a mode. Evidence: results/pcdr/composition_audit_20260922/motor_witness/protocol.json and summary.json. Code created with Codex assistance; simulation files unchanged.
