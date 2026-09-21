# TASK — CG3D-IMB-001-R1

## Parent

- Parent task: `CG3D-IMB-001`
- Review: `.agent/reviews/CG3D-IMB-001_REVIEW_001.md`
- Reviewed candidate: `931792449c8559a4009288769200ec2556932396`

## Objective

Resolve the three review findings without widening the scientific scope of the direct-imbibition baseline.

This is a bounded rework task.

Do not redesign the solver.

---

## Required reading

Read in this order:

1. `AGENTS.md`
2. `.agent/decisions/DIRECT_IMBIBITION_BASELINE.md`
3. `.agent/tasks/CG3D-IMB-001_DIRECT_IMBIBITION.md`
4. `.agent/reviews/CG3D-IMB-001_REVIEW_001.md`
5. current implementation on `agent-dev/direct-imbibition-step0`

---

## R1 — Replace solid-occupancy-derived real-domain bounds

Current direct-imbibition code infers real geometry extent from the first/last x-plane containing any solid.

Replace this with an explicit/deterministic geometry-extent definition.

Requirements:

- `prewet_layers` must count from the true real-geometry entrance, not the first plane containing solid;
- current buffered production geometry must resolve to the documented real region `[14, 214)`;
- synthetic tests must not rely on "first plane with any solid" to define the real extent;
- legacy drainage layout must not require the geometry to contain solid voxels;
- preserve the existing open-pore buffer semantics.

Preferred direction:

- encode or expose real-domain x bounds explicitly;
- keep the logic testable without running Taichi.

Do not parse free-form metadata strings as the sole authoritative source unless there is no cleaner repo-native option.

If geometry metadata/schema must be extended, keep backward compatibility where practical and document the fallback behavior.

---

## R2 — Correct gas-output semantics

For direct imbibition, distinguish remaining gas from trapped gas.

Required minimum:

- use a neutral real-region gas saturation field such as `gas_saturation_real` or `s_g_real`;
- do not call all remaining gas `trapped`, `residual`, or `S_nr`;
- remove or clearly deprecate misleading direct-imbibition report keys/plot labels;
- document that outlet-connectivity-based trapped-gas analysis is not implemented yet.

A full trapped-gas connectivity analysis is optional and should not be added if it meaningfully widens the task.

If old temporary direct-imbibition report names must be retained for compatibility, they must be explicitly marked as deprecated aliases and must not claim trapped-gas meaning.

---

## R3 — Commit durable validation evidence summary

After implementing R1/R2, run the appropriate cheap validations.

Do not run a full production-scale GPU simulation.

Create:

```text
.agent/evidence/CG3D-IMB-001/validation_summary.md
```

The summary must include, for every validation actually run:

| Field | Required |
|---|---|
| candidate commit | yes |
| exact command | yes |
| result | PASS / FAIL / NOT_RUN / INCONCLUSIVE |
| exit code | when observed |
| execution class | NumPy / CPU solver / GPU smoke / static |
| key result | when relevant |
| interpretation | smoke / regression / structural / scientific |
| local artifact/log reference | when available |

At minimum re-run:

- direct-imbibition layout tests;
- direct-imbibition runtime tests;
- relevant existing drainage/I-R regression checks affected by `cg3d/protocol.py`;
- any cheap test added for explicit real-domain bounds.

If some historical validation is too expensive, mark it `NOT_RUN`; do not imply it passed.

---

## R4 — Tests

Add or modify tests so that at least the following are covered:

1. real-domain extent can begin with an all-pore plane and is still identified correctly from explicit geometry extent;
2. direct pre-wet starts from the explicit real-domain entrance;
3. legacy drainage layout works on an all-open synthetic geometry when otherwise valid;
4. direct driver/report uses neutral gas-saturation semantics;
5. direct driver does not claim trapped gas without connectivity analysis.

---

## Constraints

Do not change:

- core LBM numerical kernels;
- phase convention;
- membrane physical semantics;
- contact-angle calibration;
- open-pore buffer requirement;
- existing I-R physical interpretation;
- convergence criteria;
- pressure-assisted direct-imbibition model.

Do not merge to `master`.

Do not force-push.

---

## Git / execution policy

Continue on:

`agent-dev/direct-imbibition-step0`

Commit and push the bounded rework.

Use the existing Z Code session if its context is still bound to this task/branch and has not been contaminated by unrelated work.

---

## Required executor output

Update:

`.agent_runtime/execution_report.md`

and commit:

`.agent/evidence/CG3D-IMB-001/validation_summary.md`

The execution report must explicitly state:

- how real-domain bounds are now represented;
- backward-compatibility behavior;
- renamed gas metrics;
- whether any trapped-gas analysis remains;
- exact validation commands and outcomes;
- final commit SHA;
- whether existing I-R semantics changed;
- whether any old evidence became stale.

## Finish

Push the candidate and finish with:

**Independent review of CG3D-IMB-001-R1.**
