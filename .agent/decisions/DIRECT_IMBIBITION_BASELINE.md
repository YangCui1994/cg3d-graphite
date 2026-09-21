# Direct Imbibition Baseline — Modeling Decision

## Status

Accepted baseline for the first independent direct-imbibition implementation task.

This document records the modeling assumptions that have already been agreed so the coding agent does not silently reinterpret them.

## Scientific objective

Add an **independent direct imbibition scenario** representing a porous electrode that is initially gas-filled and then contacted by electrolyte from one side.

This scenario is separate from the existing drainage → imbibition I-R hysteresis protocol.

The existing I-R behavior must remain unchanged.

## Physical interpretation

The intended baseline is:

```text
LEFT
liquid reservoir
    ↓
liquid-selective inlet membrane
    ↓
open-pore buffer, initially liquid
    ↓
first N pore layers of the real graphite structure, initially liquid
    ↓
remaining real graphite pore space, initially gas
    ↓
open-pore buffer, initially gas
    ↓
gas-selective outlet membrane
    ↓
gas reservoir
RIGHT
```

This represents one-side electrolyte contact / pre-wetting of the electrode face.

## Phase convention

Use the existing project convention:

- liquid / wetting phase: `psi = -1`
- gas / non-wetting phase: `psi = +1`
- solid: phase field remains zero / non-fluid as required by the existing initialization path.

## Boundary semantics

For direct imbibition, reverse the phase roles of the current drainage-oriented open system.

### Left side

- reservoir phase: liquid, `psi = -1`
- membrane must pass liquid and block gas

### Right side

- reservoir phase: gas, `psi = +1`
- membrane must pass gas and block liquid

Do not infer this only from variable names. Verify the current `mem_r` / `mem_b` semantics in the implementation before changing them.

## Open-pore buffer

Keep the existing open-pore buffer strategy.

The buffer solves a different problem from pre-wetting:

- buffer: isolates forced reservoir/membrane boundary conditions from the rough real geometry;
- pre-wet zone: removes the initial phase discontinuity exactly at the real-geometry entrance.

Do not remove or bypass the buffer as part of this task.

## Initial condition in the real porous structure

At `t = 0`:

- the first `N` pore layers of the real graphite structure adjacent to the liquid-contact side are liquid;
- the remaining real-structure pore space is gas;
- no residual liquid from a previous drainage path is inherited.

Therefore this is an **independent initially gas-filled direct-imbibition baseline**, not a continuation of drainage.

## Pre-wet thickness

Expose the pre-wet thickness as an explicit parameter, tentatively named:

`--prewet-layers N`

Do not bury the value inside the solver.

The exact physically/numerically preferred value is **not yet validated**.

For development/smoke testing, a small value such as 4 lu may be used only as a provisional numerical baseline if a concrete value is required, but it must not be presented as a validated physical parameter.

## Baseline driving condition

The first baseline should support **spontaneous / capillary-driven imbibition at zero imposed density difference**:

```text
delta = 0
rho_left ≈ rho_right
```

so that the principal intended driving mechanisms are wetting and capillarity rather than an externally imposed pressure bias.

Pressure-assisted imbibition may be added later; it is not required to define the initial baseline.

## Correctness boundaries

This task should establish:

1. boundary-phase orientation is internally consistent;
2. the initial phase field is continuous from the liquid reservoir/buffer into the pre-wetted real structure;
3. the bulk real pore space is initially gas;
4. the existing drainage and I-R protocols remain unchanged.

This task does **not** establish:

- the physically optimal pre-wet thickness;
- a final gas-outlet model for all real electrode conditions;
- full physical validation of direct imbibition;
- equivalence to a specific industrial filling process.

Those remain later modeling/validation questions.
