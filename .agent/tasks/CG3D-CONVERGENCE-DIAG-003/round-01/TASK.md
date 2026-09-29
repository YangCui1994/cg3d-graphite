# TASK

## ID

`CG3D-CONVERGENCE-DIAG-003`

## Objective

Make convergence / termination reporting explicit and machine-readable without changing the existing solver physics, convergence criteria, or stopping behaviour.

The current `run_hold` already distinguishes three exit reasons:

- `quasi-steady`
- `max-steps`
- `umax-cap`

and already records a `convergence` dictionary. However, process completion, convergence, safety-limit exit, and observed numerical health are still partly conflated in downstream interpretation.

This task must add an **additive diagnostics layer** that keeps the existing stopping rules intact while exposing those concepts separately.

## Starting Base

This task branch was pre-created from the cumulative accepted integration base:

`0ca191c7cd6f8970fc8af7e20261f4d7f246fda0`

That base includes the accepted results of:

- `CG3D-TAICHI-INIT-001`
- `CG3D-PERIODIC-CONN-002`

Do not regress either accepted task.

## Scope

### Allowed

- `cg3d/diagnostics.py`
- `cg3d/protocol.py`
- `tests/test_postprocessing.py`
- `tests/test_termination_diagnostics.py`

### Do not modify

- `lbm_solver_cg3d.py`
- `cg3d/runtime.py`
- `run_ir_cg3d.py`
- `run_pcs_cg3d.py`
- pressure-ladder definitions
- existing convergence thresholds or their defaults
- the meaning of `qs_mode`
- BC/IC, solver kernels, physical parameters, contact angle/wettability semantics
- controller / agent infrastructure

## Required Semantics

Preserve the existing top-level compatibility fields:

- `row["reason"]`
- `row["convergence"]`

Add two explicit additive records to each normal `run_hold` return:

### 1. `row["termination"]`

At minimum:

```json
{
  "process_completed": true,
  "reason": "quasi-steady | max-steps | umax-cap",
  "converged": true,
  "step_limit_reached": false,
  "safety_limit_triggered": false,
  "qs_mode": "sat | multi"
}
```

Rules:

- `process_completed` is `true` only because `run_hold` returned normally.
- `converged` is `true` **iff** the existing stopping logic exited with `reason == "quasi-steady"`.
- `max-steps` must report `converged=false` and `step_limit_reached=true`.
- `umax-cap` must report `converged=false` and `safety_limit_triggered=true`.
- Do not rename or remove the legacy top-level `reason`.
- Do not invent `USER_STOPPED`, exception, or interrupt semantics in this task; abnormal process exits do not produce a normal `run_hold` return and remain outside this record.

### 2. `row["numerical_health"]`

Track only **observed finite/non-finite diagnostic values**. Do not invent new physical acceptance bounds.

At minimum:

```json
{
  "finite": true,
  "nonfinite_fields": [],
  "first_nonfinite_step": null,
  "sample_count": 10
}
```

Requirements:

- Inspect sampled diagnostic scalar values already produced by `OpenSystem.measure()`.
- Accumulate any scalar field names observed as NaN or Inf.
- Record the first sampled step where any non-finite value was observed.
- `finite=true` only when no sampled diagnostic scalar was non-finite.
- `None` / unavailable values may be ignored rather than treated as non-finite.
- A large but finite `umax` that triggers `umax-cap` is a **safety-limit exit**, not a non-finite numerical-health failure.
- This task must **not** add a new stop condition for non-finite observations. Report them; do not change trajectory or stopping logic.

The separation is intentional. For example, in `qs_mode="sat"`, saturation may satisfy the configured quasi-steady criterion while another sampled diagnostic is non-finite. The record may therefore truthfully show:

- `termination.converged = true`
- `numerical_health.finite = false`

Do not silently collapse these dimensions into one status.

## Requirements

1. Preserve the existing quasi-steady algorithm, thresholds, minimum-step rules, window rules, `qs_mode` selection, `umax_cap` check, and loop ordering.
2. Add a small, testable host-side helper or helpers in `cg3d.diagnostics` if useful; do not create a general state-machine framework.
3. Add the additive `termination` and `numerical_health` records to `run_hold` output while preserving existing fields and compatibility.
4. Do not change `eval_convergence` mathematical definitions unless a strictly additive field is required for reporting. If no change is needed, leave its calculations untouched.
5. Add deterministic pure-Python tests using a fake/minimal system rather than a real LBM simulation. The tests must exercise `run_hold` behaviour without Taichi/GPU.
6. Test at minimum:
   - quasi-steady exit -> `converged=true`, no step/safety limit;
   - max-step exit -> `converged=false`, `step_limit_reached=true`;
   - `umax-cap` exit with finite metrics -> `converged=false`, `safety_limit_triggered=true`, `numerical_health.finite=true`;
   - non-finite sampled diagnostic is reported with field name and first step;
   - selected convergence and numerical health remain independent;
   - legacy `row["reason"]` and existing `convergence["exit"]` remain consistent with the new record.
7. Because this task modifies `cg3d/diagnostics.py`, rerun the accepted periodic-connectivity tests from Task 2 to ensure that fix is retained.
8. Do not launch an LBM simulation, GPU work, Level B validation, full geometry run, or pressure ladder.

## Constraints

- This is diagnostics/reporting modularization, not convergence-policy redesign.
- Do not introduce new threshold values.
- Do not classify `max-steps` as a numerical failure; it means the configured convergence criterion was not reached within the step budget.
- Do not classify a finite `umax-cap` event as NaN/Inf numerical failure.
- Do not infer physical validity from `converged=true`.
- Keep the output JSON-serializable.
- Prefer additive compatibility over renaming existing report fields.

## Scientific / Modeling Assumptions

- **Accepted:** Existing `qs_mode="sat"` and `qs_mode="multi"` criteria remain authoritative for the current configured quasi-steady stopping decision.
- **Accepted:** `quasi-steady` means the configured numerical stopping criteria were satisfied; it does not prove physical equilibrium or model validity.
- **Accepted:** `max-steps` means the criterion was not reached within the step budget, not that the system could never converge.
- **Accepted:** Numerical health in this task means finite/non-finite observed diagnostics only; no new density, velocity, pressure, mass-balance, or physical plausibility bounds are authorized.
- **Unresolved:** Broader convergence-policy redesign is explicitly deferred.

## Validation Requested

Run all of the following:

```text
python tests/test_termination_diagnostics.py
python tests/test_postprocessing.py
python tests/test_periodic_connectivity.py
```

No GPU / Taichi solver run is authorized.

The new termination test should include clear PASS/FAIL output for each semantic case.

## Durable Executor Evidence

Use the new bounded evidence-publication protocol.

Create:

`.agent_runtime/published_evidence/manifest.json`

and publish at least:

1. `termination_diagnostics.log`
   - kind: `validation_log`
   - command: `python tests/test_termination_diagnostics.py`
2. `postprocessing.log`
   - kind: `validation_log`
   - command: `python tests/test_postprocessing.py`
3. `periodic_connectivity.log`
   - kind: `validation_log`
   - command: `python tests/test_periodic_connectivity.py`
4. `termination_examples.json`
   - kind: `schema_example`
   - description: deterministic example records for quasi-steady, max-steps, umax-cap, and non-finite-observation cases

All files must comply with the Controller's published-evidence constraints.

The decisive results must also be summarized directly in `execution_report.md`.

## Evidence Requested

Include in `execution_report.md`:

- candidate commit SHA;
- changed-file list;
- exact validation commands and exit codes;
- concise PASS/FAIL results for every required semantic case;
- one representative JSON record each for:
  - quasi-steady;
  - max-steps;
  - umax-cap;
  - non-finite observation;
- explicit statement that existing stopping criteria and thresholds were not changed;
- explicit confirmation that Task 2 periodic-connectivity tests still pass;
- confirmation that `published_evidence` was created and handed to the Controller.

## Git Policy

- commit allowed on the pre-created task branch;
- push allowed;
- do not merge to `master`;
- do not modify the control branch directly from the executor.

## Human Decisions Reserved

- Any new convergence criterion or threshold.
- Any physical-equilibrium interpretation.
- Any new non-finite stopping policy.
- Any change to `qs_mode` meaning.
- Any solver/BC/IC modification.
- Any automatic merge decision.

## Notes / References

- Existing convergence metrics: `cg3d.diagnostics.eval_convergence`.
- Existing rung stopping logic: `cg3d.protocol.run_hold`.
- Accepted Task 2 topology regression: `tests/test_periodic_connectivity.py`.
- This task intentionally tests the new Controller `published_evidence` + provenance path.
