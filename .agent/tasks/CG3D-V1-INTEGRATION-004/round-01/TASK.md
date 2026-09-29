# TASK

## ID

`CG3D-V1-INTEGRATION-004`

## Objective

Create and run a thin cumulative V1 integration validation on the accepted combined code from Tasks 1–3.

This is a validation task, not a production-code development task.

The purpose is to answer one question:

> Do the accepted runtime-lifecycle, periodic-connectivity, and termination-diagnostics changes still work correctly when combined on one cumulative codebase, including checkpoint/resume compatibility?

## Starting Base

The task branch was pre-created from:

`3e49087e195ac98b41000bc647b115c685daa71b`

This is the accepted cumulative integration base containing:

- `CG3D-TAICHI-INIT-001`
- `CG3D-PERIODIC-CONN-002`
- `CG3D-CONVERGENCE-DIAG-003`

Do not remove, rewrite, or bypass any accepted behavior from those tasks.

## Scope

### Allowed

- `tests/test_v1_integration.py`

### Do not modify

- `lbm_solver_cg3d.py`
- `cg3d/`
- existing test files
- drivers
- controller / agent infrastructure
- documentation
- any production code

If an existing regression test fails because of a production-code integration defect, report the failure and stop. Do not fix production code inside this validation task.

## New Validation File

Create:

`tests/test_v1_integration.py`

It must be a thin integration test, not a copy of the existing Task 1–3 test suites.

It should validate representative cross-module behavior in one process / small subprocesses, at minimum:

### A. Runtime-lifecycle integration

- Set `LBM_ARCH=cpu` before any explicit runtime initialization.
- Import `cg3d` and `lbm_solver_cg3d`.
- Confirm plain import does not itself initialize the project Taichi runtime.
- Explicitly initialize through the accepted project runtime boundary.
- Confirm the shared lattice tables can then be materialized.
- Confirm a small `ColorGradientSolver3D` instance can be constructed through the accepted lifecycle.
- Do not run a long solver trajectory.

### B. Periodic-topology integration

Use the accepted public `label_periodic` path and assert one representative multi-axis case, for example:

- y+z wrapped edge pair;
- `conn=18`;
- `periodic_axes=(1,2)`;
- expected one component of size 2.

Also include one negative control showing the same geometric pair stays separate when one required axis is non-periodic.

Do not duplicate the full Task 2 oracle matrix.

### C. Termination-diagnostics integration

Exercise the real `cg3d.protocol.run_hold` using a very small fake system, not the LBM solver, and assert:

- legacy `reason` is still present;
- legacy `convergence["exit"]` is still present;
- `termination` is present and consistent with the legacy reason;
- `numerical_health` is present;
- the returned row remains JSON-serializable for an all-finite representative case.

One representative quasi-steady or max-steps case is enough here; do not reproduce the full Task 3 semantic suite.

### D. Combined-import / API sanity

In the same validation, confirm the cumulative public paths used by the three accepted tasks coexist without circular-import/runtime-order failure:

- `cg3d.init_runtime`
- `cg3d.label_periodic`
- `cg3d.protocol.run_hold`
- `lbm_solver_cg3d.ColorGradientSolver3D`

## Requirements

1. Add only `tests/test_v1_integration.py`.
2. Keep it small and representative. Existing dedicated tests remain the source of deep coverage.
3. Do not modify production code to make this task pass.
4. Run the full cumulative validation command set below.
5. Use the existing project `lbm` Python environment. If the shell's default `python` is not that environment, invoke the project interpreter explicitly rather than changing code or dependencies.
6. No GPU work is authorized.
7. No Level B Laplace/contact-angle validation.
8. No full real-geometry pressure ladder.
9. Do not reinterpret scientific results.
10. If any existing accepted regression fails, capture the failure as durable evidence and report `PARTIAL` or `FAILED`; do not hide it by narrowing the command set.

## Validation Requested

Run all of the following on the frozen cumulative candidate:

```text
python tests/test_v1_integration.py
python tests/test_import_no_taichi_init.py
LBM_ARCH=cpu python tests/run_level_a.py
python tests/test_postprocessing.py
python tests/test_periodic_connectivity.py
python tests/test_termination_diagnostics.py
LBM_ARCH=cpu python tests/test_checkpoint_resume.py
```

Use the project `lbm` interpreter/environment for all commands.

The checkpoint/resume test is intentionally included because it crosses runtime initialization, `OpenSystem`, drivers, and persisted state.

## Durable Executor Evidence

Use the bounded `published_evidence` protocol.

Publish at least:

1. `v1_integration.log`
   - kind: `validation_log`
   - command: `python tests/test_v1_integration.py`
2. `import_lifecycle.log`
   - kind: `validation_log`
3. `level_a.log`
   - kind: `validation_log`
4. `postprocessing.log`
   - kind: `validation_log`
5. `periodic_connectivity.log`
   - kind: `validation_log`
6. `termination_diagnostics.log`
   - kind: `validation_log`
7. `checkpoint_resume.log`
   - kind: `validation_log`
8. `integration_summary.json`
   - kind: `validation_summary`
   - include command, exit code, elapsed time if available, and concise PASS/FAIL status for each validation

All files must comply with Controller evidence limits and manifest rules.

If a log would exceed the single-file publication limit, publish a concise deterministic summary instead and state that constraint in the execution report. Do not silently truncate evidence.

## Evidence Requested

In `execution_report.md`, include:

- starting base SHA;
- final candidate SHA;
- changed-file list;
- exact interpreter/environment used;
- exact command + exit code for all seven validations;
- concise result for each;
- explicit confirmation that only `tests/test_v1_integration.py` changed;
- explicit statement whether the cumulative Task 1–3 integration passed as a whole;
- any failure must identify which accepted task/interface it appears to affect;
- confirmation that the published evidence bundle was created.

## Git Policy

- commit/push allowed on the pre-created task branch;
- do not merge to `master`;
- do not modify the control branch directly from the executor;
- do not alter the integration branch directly from the executor.

## Human Decisions Reserved

- Any production-code fix arising from this validation.
- Any decision to merge accepted code to master.
- Any change to convergence policy, physics, BC/IC, or scientific interpretation.
- Any decision to expand from regression validation into expensive simulation validation.

## Notes / References

This task is intentionally narrower than the sum of the three prior tasks:

- deep runtime validation already exists in Task 1;
- deep periodic-topology validation already exists in Task 2;
- deep termination-diagnostics validation already exists in Task 3.

`test_v1_integration.py` should validate that these accepted interfaces coexist correctly, while the existing tests provide regression depth.
