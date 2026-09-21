# TASK

## ID

`CG3D-IMB-001`

## Type

`modeling + implementation`

## Objective

Introduce an **independent direct-imbibition initialization/protocol** for `cg3d-graphite`.

The new scenario represents an initially gas-filled porous graphite structure contacted by electrolyte from one side, with a small pre-wetted zone inside the real structure to avoid placing the initial gas/liquid discontinuity directly at the rough geometry entrance.

Do **not** change the meaning or baseline behavior of the existing drainage → imbibition I-R workflow in `run_ir_cg3d.py`.

Read first:

- `AGENTS.md`
- `.agent/decisions/DIRECT_IMBIBITION_BASELINE.md`
- `docs/BC_IC_OUTPUT.md`
- `docs/ALGORITHM.md`
- relevant code in `cg3d/protocol.py`, `run_ir_cg3d.py`, and the solver only as needed

## Scope

### Allowed

- `cg3d/`
- a new direct-imbibition driver if needed
- tests required for this task
- documentation directly related to the new direct-imbibition mode
- small diagnostic/QA helpers needed to inspect the initial state
- `.agent_runtime/execution_report.md`

### Prefer

Reuse or minimally extend the existing shared protocol rather than duplicating the full solver or I-R infrastructure.

A separate driver such as `run_imbibition_cg3d.py` is acceptable if it keeps the physical meaning clear and avoids changing the existing I-R driver.

### Do not modify without stopping for review

- core Color Gradient collision/recoloring numerics
- surface-tension formulation
- wettability/contact-angle calibration
- convergence criteria
- existing I-R scientific meaning
- existing published/report result files
- existing baseline result directories

If implementation appears to require one of these changes, stop and report why.

## Requirements

### R1 — Independent direct-imbibition scenario

Implement a fresh-start direct-imbibition path that does not depend on a prior drainage checkpoint or drainage-generated residual-liquid state.

The existing drainage → imbibition I-R path must remain available and semantically unchanged.

### R2 — Phase orientation

For the new direct-imbibition setup:

#### Left / liquid-contact side

- reservoir phase = liquid / wetting phase, `psi = -1`
- inlet membrane passes liquid and blocks gas

#### Right / gas-exit side

- reservoir phase = gas / non-wetting phase, `psi = +1`
- outlet membrane passes gas and blocks liquid

Verify the actual `mem_r` / `mem_b` convention from the current implementation before coding.

### R3 — Preserve open-pore buffers

Retain the existing open-pore buffer separation between forced reservoir/membrane conditions and the rough real graphite geometry.

Do not solve the IC problem by moving the forced BC directly onto the real rough surface.

### R4 — Direct-imbibition initial state

For a fresh direct-imbibition initialization:

- left liquid reservoir: liquid;
- left open-pore buffer: liquid;
- first `N` pore layers of the **real graphite domain** adjacent to the liquid-contact side: liquid;
- all remaining real graphite pore cells: gas;
- right open-pore buffer: gas;
- right gas reservoir: gas;
- solid nodes remain treated according to the existing solver initialization.

No liquid distribution from a previous drainage state should be inherited.

Do not hard-code absolute x indices such as 14/214 if the current geometry/layout code already exposes the relevant boundaries programmatically.

### R5 — Explicit pre-wet parameter

Expose pre-wet thickness as an explicit configuration/CLI parameter, preferably:

`--prewet-layers N`

The value must not be hidden in solver internals.

If a default is introduced, document clearly that it is a provisional numerical baseline rather than a validated physical value.

### R6 — Zero-pressure-bias baseline

The new mode must support a baseline with:

`delta = 0`

and equal nominal reservoir densities, so spontaneous/capillary-driven imbibition can be studied without externally imposed pressure bias.

Do not add a pressure ladder unless it is needed for a clean implementation. Pressure-assisted imbibition can remain future work.

### R7 — Inspectable initial condition

Provide a deterministic way to inspect/verify the initial phase layout **without running a full expensive simulation**.

This can be a pure NumPy helper, an exposed initialization builder, a dedicated diagnostic, or another testable method.

The evidence must allow checking:

- reservoir phases;
- membrane orientation;
- buffer phases;
- pre-wet thickness;
- gas-filled bulk pore space;
- solid handling.

### R8 — Existing protocol regression

Existing drainage and drainage→imbibition initialization semantics must not change.

Add a regression check appropriate to the current code structure.

## Scientific / Modeling Assumptions

### Accepted

- This task represents **direct imbibition**, not I-R hysteresis.
- The electrode is idealized as initially gas-filled except for the pre-wetted entrance region.
- One side is initially in contact with electrolyte.
- The open-pore buffer remains necessary to separate strong BCs from the rough geometry.
- The initial pre-wet zone is partly a numerical initialization device and may also represent local physical pre-wetting.

### Unresolved

- The optimal/physical value of `N`.
- Whether a sharp pore-layer transition or a diffuse/tanh initial interface is ultimately preferable.
- The final physically preferred gas-outlet representation for all filling scenarios.
- Whether real electrodes require a more complex initial residual-liquid / adsorbed-film model.

These unresolved items must not be silently claimed as solved by this task.

## Validation Requested

Do **not** launch the full 200³/228³ long GPU production run for this task.

Run cheap/deterministic validation only unless a very short smoke test is necessary.

At minimum provide tests/evidence for:

### V1 — Initial-state layout

Verify on a small/synthetic or directly inspectable geometry that:

- left reservoir/buffer = liquid;
- first `N` real-domain pore layers = liquid;
- remaining real-domain pores = gas;
- right buffer/reservoir = gas;
- solids are not incorrectly assigned fluid phase.

Test at least two values of `N` if practical.

### V2 — Membrane orientation

Verify that the direct-imbibition mode uses the membrane orientation consistent with:

- liquid entering from the left;
- gas leaving to the right.

### V3 — Existing-mode regression

Verify that default/current drainage-oriented `OpenSystem` and `run_ir_cg3d.py` semantics are unchanged when direct-imbibition mode is not selected.

### V4 — Zero-bias construction

Verify that the direct-imbibition baseline can be constructed with `delta = 0` and equal nominal reservoir densities.

### Optional short smoke test

A very short CPU or bounded GPU smoke test is permitted only to demonstrate that initialization/first stepping does not immediately produce NaN or an obvious structural failure.

Do not treat such a smoke test as physical validation.

## Evidence Requested

Include in the execution report:

- changed files;
- design chosen (new driver vs protocol mode vs another minimal approach);
- exact initial-condition semantics;
- exact membrane semantics;
- exact validation commands;
- PASS / FAIL / NOT_RUN / INCONCLUSIVE for each validation;
- any small QA output useful for inspecting the phase layout;
- whether existing I-R behavior was touched;
- any existing evidence that may become stale;
- any shared/copy-paired file that may require later synchronization with the separate LBM tree.

## Git Policy

For this task:

- edits are allowed on the current task branch/worktree;
- commits are allowed;
- push is allowed;
- do not merge to `master`;
- do not force-push;
- do not rewrite shared history.

Do not create a final merge unless explicitly requested.

## Human Decisions Reserved

Stop and request a decision if the implementation requires:

- choosing a scientifically preferred `prewet-layers` value;
- changing contact angle/wettability calibration;
- changing convergence rules;
- changing core CG-LBM numerics;
- removing the open-pore buffer;
- redefining existing I-R results or their interpretation;
- introducing a nontrivial externally imposed pressure protocol beyond the zero-bias baseline.

## Suggested Implementation Principle

Prefer separating **layout/initial-condition construction** from solver stepping sufficiently that it can be tested deterministically.

Avoid duplicating the full `OpenSystem` implementation if a small explicit mode/orientation abstraction can preserve readability.

However, do not over-generalize the solver merely to satisfy this task.

## Required Executor Output

Write:

`.agent_runtime/execution_report.md`

using:

`.agent/templates/EXECUTION_REPORT.md`

The report must clearly distinguish implementation claims from actually run validation evidence.
