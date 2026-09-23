# REVIEW

## Binding

- **Task ID:** `CG3D-PERIODIC-CONN-002`
- **Candidate / commit:** `62219270d5d3c29dc522103e262718c77332b233`
- **Execution report:** `.agent/tasks/CG3D-PERIODIC-CONN-002/round-01/EXECUTION_REPORT.md`

## Review Mode

`DIFFERENT_MODEL` — ChatGPT reviews Z Code execution in the existing planner/reviewer session. This is not the later fresh-session repository audit.

## Coverage

Inspected:

- Round 1 TASK.md;
- candidate commit and full changed-file set;
- `cg3d.diagnostics.label_periodic` implementation after the fix;
- the new focused periodic-connectivity test file;
- the added primary post-processing regression cases;
- production call sites through `run_common.py` and `run_ir_cg3d.py`;
- controller process evidence and candidate continuity;
- pre-change reproducer results and post-change result summaries reproduced directly in the execution report.

Not independently rerun:

- the Python test commands on the Windows worker;
- executor-local custom raw validation logs, which the current Controller still does not publish.

## Requirement Review

| Requirement | Review status | Evidence / reason |
|---|---|---|
| R1 correct 6/18/26 torus topology | PASS | New implementation enumerates valid structure offsets and applies wrapping on every periodic axis participating in the offset. Explicit edge/corner cases match the intended connectivity. |
| R2 arbitrary subsets of periodic axes | PASS | Implementation normalizes any provided subset; focused tests cover all non-empty subsets plus empty periodic axes. |
| R3 return semantics preserved | PASS | Relabel + descending size calculation is unchanged in meaning; tests verify exact size sums after wrapped merges. |
| R4 preserve non-periodic SciPy semantics | PASS | Base labeling still uses `scipy.ndimage.label`; `periodic_axes=()` is tested against SciPy directly. |
| R5 required deterministic cases | PASS | Required single-seam, multi-seam, wrapped edge, wrapped corner, missing-axis negative controls, size exactness, and separate-cluster controls are all present. |
| R6 pure NumPy/SciPy host-side | PASS | Changed implementation/tests do not introduce Taichi or solver dependencies; executor reports isolation check with neither imported. |
| R7 no semantics change beyond topology fix | PASS | Default `periodic_axes=(1,2)`, connectivity numbers, and trapped-gas meaning are unchanged. |
| R8 small/general topology fix | PASS | One general wrapped-offset union replaces per-seam special handling; no test-specific branches observed. |
| R9 only change if bug reproducible | PASS | Pre-change reproducer shows the stated y+z edge and xyz corner failures. |

## Validation Review

| Validation | Review status | Notes |
|---|---|---|
| `python tests/test_postprocessing.py` | PASS WITH EVIDENCE CAVEAT | Execution report reproduces 20 PASS / 0 FAIL and the decisive new case lines; raw executor-local log is not controller-published. |
| `python tests/test_periodic_connectivity.py` | PASS WITH EVIDENCE CAVEAT | Execution report reproduces 34 PASS / 0 FAIL including 252 oracle combinations; raw executor-local log is not controller-published. |
| Pre-change key reproducer | PASS | Report shows old code returns 2 singleton clusters for y+z edge at conn=18 and xyz corner at conn=26, proving the defect. |
| Production default `conn=6,(1,2)` equivalence | PASS WITH EVIDENCE CAVEAT | Executor reports partition-identical results on the real 200^3 pore mask; this is also structurally consistent because conn=6 has only face offsets and cannot require simultaneous in-plane wrapping. |
| Candidate source/scope | PASS | Controller evidence shows only `cg3d/diagnostics.py`, `tests/test_periodic_connectivity.py`, and `tests/test_postprocessing.py` changed. |
| Process execution | PASS | Controller records exit code 0, no timeout, parsed envelope, and candidate commit `62219270...`. |

## Findings

### Blocking

None.

### Non-blocking

1. **Documentation implementation wording is stale.** `docs/BC_IC_OUTPUT.md` and a changelog line still describe the older per-seam plane union implementation. The documented topology intent remains correct, but the implementation description should be refreshed in a separate docs-scoped task.
2. **tests/README.md is stale.** The listed post-processing check count and file list do not reflect the new focused test. This is documentation/test-index cleanup, not a correctness issue.
3. **Controller custom-evidence publication gap remains.** Raw executor-local validation logs are still not copied to the durable control-branch evidence bundle. The execution report mitigates this by reproducing the decisive results inline, but the infrastructure should be improved separately.

## Modeling / Scientific Review

The candidate changes topology/post-processing only. No LBM solver, BC/IC, convergence rule, pressure protocol, saturation definition, or trapped-gas physical interpretation was changed.

For the production default `conn=6`, the topology is unchanged because the neighbourhood contains face offsets only; no two-axis or three-axis wrapped offset exists at that connectivity. For `conn=18/26`, the intended effect is monotone coarsening relative to the buggy implementation: previously split components may merge, but existing connected relations are not removed.

This review does not infer whether a connected gas component is physically trapped; that remains a separate boundary/reservoir semantics problem.

## Missing Evidence

- Controller-captured raw stdout/stderr for the individual Python validation commands.
- No simulation evidence is required for this host-side topology task.

## Decision

PASS

## Decision Rationale

The stated multi-axis periodic-connectivity defect is reproducible, the implementation addresses the root cause with a general torus-neighbour union strategy, the required positive and negative cases are covered, and no out-of-scope solver or physical semantics were changed. No blocking issue justifies another execution round.

## Next Action

CLOSE `CG3D-PERIODIC-CONN-002`. Retain candidate branch and evidence; do not merge automatically. Track documentation cleanup and Controller custom-evidence publication as separate follow-up work.
