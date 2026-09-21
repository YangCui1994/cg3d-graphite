# REVIEW — CG3D-IMB-001 / Review 001

## Binding

- Task: `CG3D-IMB-001`
- Candidate commit: `931792449c8559a4009288769200ec2556932396`
- Branch: `agent-dev/direct-imbibition-step0`
- Review mode: independent static review

## Decision

`CHANGES_REQUESTED`

## Summary

The implementation direction is accepted:

- independent direct-imbibition driver added;
- existing drainage → imbibition I-R driver semantics are not directly modified;
- phase/reservoir orientation is reversed consistently for direct imbibition;
- `--prewet-layers` is explicit;
- zero-bias `delta=0` baseline is supported;
- open-pore buffers are retained;
- direct IC construction is inspectable and testable.

However, three issues must be resolved before this task can pass.

---

## Finding 1 — Blocking: real-structure bounds are inferred from first/last solid plane

Current implementation derives:

```text
x_real_lo / x_real_hi
```

from the first and last x-plane containing any solid voxel.

That is not equivalent to the real geometry extent.

A real electrode crop may begin with one or more all-pore x-planes. In that case:

```text
first x-plane containing solid
!=
first x-plane belonging to the real electrode geometry
```

This can shift the pre-wet region and make `--prewet-layers N` refer to the wrong physical extent.

The current buffered geometry generator already knows the true real-geometry extent:

```text
real graphite = [K, K + original_width)
```

For the current production geometry this is documented as `[14, 214)`.

### Required change

Do not use "first/last plane containing solid" as the authoritative real-domain definition.

Use explicit geometry extent information instead.

Acceptable approaches include:

- store explicit `real_x_start / real_x_stop` metadata in buffered geometry;
- or expose explicit real-domain bounds through the geometry/protocol interface;
- or another deterministic representation with the same semantics.

Synthetic tests may pass bounds explicitly.

The design must not depend on solid occupancy to define the real electrode extent.

### Regression requirement

The extraction of direct-imbibition layout logic must not add a new requirement that legacy drainage geometries contain solid voxels.

Existing drainage semantics for all-open/synthetic cases should remain valid unless a separate task explicitly changes them.

---

## Finding 2 — Blocking: remaining gas is currently labelled as trapped/residual gas

The new direct-imbibition driver currently calculates all remaining gas in the domain / real region and reports it with `s_nr` / residual/trapped-gas semantics.

In an open direct-imbibition system, gas may still be connected to the gas outlet.

Therefore:

```text
all remaining gas
!=
trapped gas
```

At minimum distinguish:

```text
gas_saturation_real
```

from:

```text
trapped_gas_saturation
```

### Required change for this rework

For this task, do not claim that all remaining gas is trapped.

The simplest acceptable implementation is:

- report real-region gas saturation with a neutral name such as `gas_saturation_real` or `s_g_real`;
- remove or deprecate misleading `s_nr` / trapped-gas wording for this direct-imbibition driver;
- explicitly state that outlet-connectivity-based trapped-gas analysis is not yet implemented.

A full outlet-connected vs disconnected gas-topology algorithm is **not required** in this rework unless it can be added cleanly without widening the task.

If implemented, it must be separately validated.

---

## Finding 3 — Evidence gap: validation results are only executor claims

The candidate commit message claims that multiple validation commands passed.

No durable execution evidence is currently available to the reviewer through GitHub checks/artifacts, and `.agent_runtime/` is ignored by Git.

Therefore the reviewer can confirm that the tests exist and appear relevant, but cannot independently confirm that the reported commands actually ran on the reviewed candidate.

### Required change

Keep `.agent_runtime/` ignored.

In addition, write a durable review-evidence summary under:

```text
.agent/evidence/CG3D-IMB-001/
```

For this rework, create at least:

```text
.agent/evidence/CG3D-IMB-001/validation_summary.md
```

It must record:

- candidate commit being tested;
- exact validation command;
- PASS / FAIL / NOT_RUN / INCONCLUSIVE;
- process exit code when observed;
- key numeric / structural result where relevant;
- whether the validation is CPU, GPU, NumPy-only, or static;
- whether the result is a smoke test or a scientific validation;
- any output/log path that remains available locally.

Do not commit large generated simulation outputs.

The summary is a durable record of the execution evidence; it is still subject to later controller-side independent capture.

---

## Requirement disposition

| Requirement | Review |
|---|---|
| R1 independent direct imbibition | PASS |
| R2 phase / membrane orientation | PASS |
| R3 retain open buffer | PASS |
| R4 direct IC | CHANGES_REQUESTED — real-domain bound definition |
| R5 explicit pre-wet parameter | PASS |
| R6 zero-bias baseline | PASS |
| R7 inspectable IC | PASS |
| R8 existing-mode regression | CHANGES_REQUESTED — all-open legacy semantics |
| gas/trapped output semantics | CHANGES_REQUESTED |
| durable validation evidence | INSUFFICIENT_EVIDENCE |

## Scope guard

Do not use this rework to change:

- core CG collision/recoloring numerics;
- surface tension;
- wettability calibration;
- convergence rules;
- existing I-R meaning;
- open-pore buffer strategy;
- pressure-assisted imbibition physics.

## Next action

Execute `CG3D-IMB-001-R1` and return the updated candidate for independent review.
