# REVIEW

## Binding

- **Task ID:** `CG3D-CONVERGENCE-DIAG-003`
- **Candidate / commit:** `3e49087e195ac98b41000bc647b115c685daa71b`
- **Execution report:** `.agent/tasks/CG3D-CONVERGENCE-DIAG-003/round-01/EXECUTION_REPORT.md`

## Review Mode

`DIFFERENT_MODEL` — ChatGPT reviews Z Code execution in the existing planner/reviewer session. This is not the later fresh-session repository audit.

## Coverage

Inspected:

- Round 1 TASK.md;
- candidate diff and changed-file list;
- `NumericalHealthTracker` and `termination_record` implementation;
- insertion points inside `cg3d.protocol.run_hold`;
- deterministic fake-system tests;
- controller process evidence;
- executor-published manifest, provenance, validation logs, schema examples, and stopping-equivalence evidence;
- regression evidence for Task 2 periodic connectivity.

Not independently rerun:

- the Python test commands on the Windows worker.

## Requirement Review

| Requirement | Review status | Evidence / reason |
|---|---|---|
| R1 preserve existing stopping rules and loop ordering | PASS | Candidate adds observation/reporting only. `health.observe()` is side-effect-free with respect to control state; termination flags are derived from the existing legacy reason after exit. Published A/B replay covers 16 cases with legacy fields/callbacks identical. |
| R2 small host-side helper set | PASS | `termination_record` and `NumericalHealthTracker` are localized reporting helpers, not a new state-machine framework. |
| R3 additive termination + numerical-health records | PASS | Existing `reason` and `convergence` remain present; new records are added alongside them. |
| R4 do not change `eval_convergence` math | PASS | Candidate leaves the accepted calculations intact; Task 2 code in the same file is retained. |
| R5 deterministic fake-system tests without LBM/GPU execution | PASS | New test drives real `run_hold` using a fake solver/system and does not execute an LBM kernel or GPU workload. |
| R6 required semantic cases | PASS | Published log shows PASS for quasi-steady, max-steps, finite umax-cap, non-finite reporting, independence of convergence/health, and legacy/new consistency. |
| R7 retain accepted periodic-connectivity fix | PASS | Published `periodic_connectivity.log` reports all 34 checks PASS, including the 252-combination oracle. |
| R8 no unauthorized simulation work | PASS | Execution report and process evidence show host-side tests only. |

## Validation Review

| Validation | Review status | Notes |
|---|---|---|
| `tests/test_termination_diagnostics.py` | PASS | Durable executor log reports 62 checks, 0 failures, ALL PASS. |
| `tests/test_postprocessing.py` | PASS | Durable executor log reports 20 checks, 0 failures, ALL PASS. |
| `tests/test_periodic_connectivity.py` | PASS | Durable executor log reports 34 checks, 0 failures and oracle agreement. |
| Stopping-equivalence replay | PASS | 16 scripted cases, 0 mismatches; legacy row fields and callbacks remain identical. |
| Candidate source / scope | PASS | Controller records only `cg3d/diagnostics.py`, `cg3d/protocol.py`, and `tests/test_termination_diagnostics.py` changed. |
| Process execution | PASS | Controller records exit code 0, no timeout, parsed envelope, and the expected candidate commit. |
| Executor evidence provenance | PASS | Controller-generated provenance binds six published files to task, round, candidate SHA, session ID, worker, capture time, file size, and SHA-256. |

## Findings

### Blocking

None.

### Non-blocking

1. The test process imports the Taichi Python package because `cg3d.__init__` imports `cg3d.runtime`; however, no `ti.init()`, kernel, GPU, or LBM step is executed. This does not violate the task's simulation/runtime guardrail, but it is worth distinguishing "Taichi package imported" from "Taichi runtime initialized".
2. Older ladder rows written before this task lack the new additive records. Current repository consumers do not require them, so backward compatibility is preserved; downstream consumers should continue treating the new fields as optional when reading historical results.
3. Broader convergence-policy redesign and any future policy that reacts to NaN/Inf remain explicitly deferred.

## Modeling / Scientific Review

The implementation keeps the four concepts separate:

- normal process return;
- configured quasi-steady convergence;
- step/safety termination;
- observed finite/non-finite diagnostics.

This separation is correct for the task. In particular, `termination.converged=true` can coexist with `numerical_health.finite=false` in `qs_mode="sat"`, because convergence is defined strictly by the existing configured stopping rule, while health is observational. No physical-equilibrium claim is introduced.

A finite `umax-cap` exit is correctly treated as a safety-limit termination, not a NaN/Inf failure. `max-steps` is correctly treated as "criterion not reached within budget", not as proof of numerical failure.

## Evidence-Publication Infrastructure Review

The updated Controller evidence protocol passed its first real task:

- `evidence/controller/` contains independently captured process/Git facts;
- `evidence/executor/` contains only manifest-declared executor artifacts;
- `manifest.json` is durable;
- `provenance.json` is Controller-generated, not executor-generated;
- every published artifact is bound to candidate `3e49087e...` with size and SHA-256;
- the reviewer can inspect decisive validation logs directly from GitHub.

This closes the specific evidence-publication gap observed in Tasks 1 and 2.

## Decision

PASS

## Decision Rationale

The candidate satisfies the requested diagnostics/reporting semantics without changing the existing stopping policy. Required deterministic tests pass, accepted Task 2 topology behavior is retained, and the A/B replay provides strong evidence that legacy run_hold behavior and callback sequencing are unchanged. No blocking issue justifies another execution round.

## Next Action

CLOSE `CG3D-CONVERGENCE-DIAG-003`. Retain the candidate branch and durable evidence; do not merge automatically. The next architecture follow-up should address cumulative accepted-candidate integration as a first-class Controller concept rather than relying on manually prepared integration bases.
