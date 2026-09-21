# TASK — CG3D-IMB-002 Production-Geometry Direct-Imbibition Pilot

## Parent / accepted baseline

- Accepted baseline task: `CG3D-IMB-001`
- Accepted review: `.agent/reviews/CG3D-IMB-001_REVIEW_002.md`
- Accepted Step-0 branch head: `af0a607dee563768424866d7c6259323092a7503`
- This task starts from the accepted direct-imbibition implementation and does not reopen that review.

## Type

`validation + modeling experiment`

## Objective

Run a **bounded production-geometry pilot** of the accepted direct-imbibition setup on the real buffered graphite geometry and compare the early-time behavior for:

- `prewet_layers = 2`
- `prewet_layers = 4`
- `prewet_layers = 6`

The purpose is to answer two limited questions:

1. Does the accepted direct-imbibition boundary/initial-condition setup remain numerically stable on the real 228^3 buffered graphite geometry?
2. How strongly does the early-time infiltration trajectory depend on the provisional pre-wet thickness over N = 2 / 4 / 6?

This task is **not** a full physical validation and must not claim convergence or a physically preferred `prewet_layers` value.

---

## Required reading

Read before execution:

1. `AGENTS.md`
2. `.agent/decisions/DIRECT_IMBIBITION_BASELINE.md`
3. `.agent/reviews/CG3D-IMB-001_REVIEW_002.md`
4. `.agent/evidence/CG3D-IMB-001/validation_summary.md`
5. `docs/BC_IC_OUTPUT.md`
6. current `run_imbibition_cg3d.py`
7. `make_geo_buffer.py`

Do not modify the accepted baseline physics unless this task explicitly requires it.

---

## Scientific baseline

Use:

- geometry: `geo_graphite_228b14.npz`
- real-domain bounds: structured `real_x=[14,214)`
- `psi_solid = -0.68`
- `capa = 0.06`
- `delta = 0.0`
- left side = liquid source
- right side = gas outlet
- open-pore buffers retained
- initially gas-filled real pore space except for the first N pre-wet layers
- no inherited drainage state

The pre-wet values 2 / 4 / 6 are **QA/sensitivity values only**, not physically validated values.

---

## Geometry gate

Before any GPU run:

1. verify `geo_graphite_228b14.npz` exists;
2. verify it contains structured `real_x`;
3. verify `real_x == [14,214]`;
4. verify the `solid` array shape is the expected buffered production geometry;
5. if the local geometry is missing or lacks `real_x`, regenerate it using the current `make_geo_buffer.py`;
6. do not silently infer real bounds from solid occupancy.

Record the geometry check in the durable evidence summary.

---

## Pilot execution plan

Run the cases **sequentially**, never in parallel on the same GPU.

Run the middle case first:

1. N = 4
2. N = 2
3. N = 6

If N = 4 shows an immediate structural failure, NaN, uncontrolled instability, or an unexpected boundary-direction failure, stop before launching N = 2 / 6 and report the failure.

### Fixed pilot horizon

Use a fixed 10,000-step horizon for each executed case.

The pilot is deliberately time-bounded. Do not interpret the end state as converged.

Recommended driver settings:

```text
--delta 0
--prewet-layers <N>
--psi-solid -0.68
--capa 0.06
--min-steps 10000
--max-steps 10000
--every 500
--dump-every 1000
--ckpt-every 0
```

Keep other accepted defaults unless a documented technical reason requires otherwise.

Use tags:

- `imb_pilot_n4`
- `imb_pilot_n2`
- `imb_pilot_n6`

Do not reuse or overwrite existing production result directories.

If one of these tags already exists, create a new non-destructive tag rather than deleting prior data.

---

## Runtime safety

Before launching each case:

- confirm no conflicting CG3D GPU simulation is already running;
- do not run PyVista rendering concurrently on the same GPU;
- do not edit imported solver/protocol Python files while the run is active.

If a case terminates by NaN, runtime error, or `umax-cap`, preserve the available frames/log/report and mark the case accordingly.

Do not automatically rerun a failed physical case until it passes.

---

## Required raw outputs

Keep raw pilot results under the normal gitignored result directories.

Do not commit:

- full frame series;
- checkpoints;
- large npz simulation outputs.

Preserve locally:

- initial IC artifacts;
- frames at the configured interval;
- final state;
- report/report_partial;
- console log if captured.

---

## Required comparison analysis

After the executed pilot runs, generate a **small durable comparison package** under:

```text
.agent/evidence/CG3D-IMB-002/
```

### A. Validation summary

Create:

```text
.agent/evidence/CG3D-IMB-002/validation_summary.md
```

For each N, record:

- exact command;
- source commit;
- result status:
  - PASS
  - FAIL
  - INCONCLUSIVE
  - NOT_RUN
- exit code;
- termination reason;
- whether rho / psi remained finite;
- max / representative `umax`;
- final `gas_saturation_real`;
- final `gas_saturation_dom`;
- whether the run reached exactly 10,000 steps;
- any observed boundary anomaly;
- local result directory;
- wall time if available.

Explicitly state:

> 10,000 steps is a bounded pilot horizon, not a convergence criterion.

### B. Time-history comparison

From the saved frames / reports, generate a comparison plot showing early-time gas saturation in the **real graphite region** versus step for N = 2 / 4 / 6.

Preferred filename:

```text
figures/gas_saturation_real_vs_step.png
```

If the current frame format does not directly store real-region gas saturation, compute it deterministically from the saved phase field, solid map and explicit `real_x` bounds.

Document whether the plotted metric is binary or continuous.

### C. Same-time central-slice comparison

Generate a compact comparison using the same physical time/step across cases.

At minimum compare:

- t = 0
- step = 1,000
- step = 5,000
- step = 10,000

for each executed N.

A grid/strip figure is preferred.

Suggested filename:

```text
figures/imbibition_slices_compare.png
```

The figure should clearly distinguish:

- solid;
- liquid;
- gas;
- real-domain bounds;
- flow direction.

### D. Final x-direction phase profile

For each N, generate an x-direction profile at the pilot endpoint showing the real-domain distribution of:

- liquid pore fraction;
- gas pore fraction;
- solid fraction.

Preferred combined filename:

```text
figures/final_phase_profile_compare.png
```

### E. Initial-state reference

Reuse or regenerate the accepted initial-state visualization for N = 2 / 4 / 6 so the initial differences are visible alongside the evolution results.

Do not claim any N is better from the initial-state plot alone.

---

## Optional implementation helper

If useful, add a small deterministic post-processing helper for this pilot.

Requirements:

- read existing saved outputs;
- use explicit `real_x`;
- do not duplicate solver physics;
- do not change the accepted direct-imbibition model;
- keep it reusable for later sensitivity runs if practical.

Do not build a general visualization framework in this task.

---

## Comparison questions to answer

The execution report should describe, without over-interpreting:

1. Did all executed cases remain numerically finite through 10,000 steps?
2. Did liquid advance into the real pore space in the intended +x direction?
3. Did gas remain able to leave toward the right-side gas outlet without an obvious phase-orientation contradiction?
4. How different are the N = 2 / 4 / 6 early-time gas-saturation trajectories?
5. Does the difference appear limited to an initial offset, or does it persist/grow over the 10,000-step pilot?
6. Are there qualitative differences in invasion pattern visible in the same-time slices?
7. Did any case show an immediate recurrence of the earlier rough-boundary instability?

Do **not** answer:

- which N is physically correct;
- whether the system is fully converged;
- whether the final remaining gas is trapped;
- whether the pilot reproduces industrial electrolyte filling quantitatively.

Those are outside this task.

---

## Source-change policy

Prefer running and analyzing the accepted baseline without changing source code.

Source changes are allowed only for:

- a small post-processing helper;
- a clearly necessary non-physics instrumentation fix.

If a change would affect:

- direct-imbibition physics;
- BC semantics;
- IC semantics;
- convergence rules;
- solver kernels;
- wettability;
- output scientific meaning;

stop and request a new review before proceeding.

---

## Git / branch policy

Work on:

`agent-dev/direct-imbibition-pilot`

You may commit:

- this task's small analysis helper if created;
- durable evidence summary;
- small comparison figures;
- relevant lightweight documentation.

Do not commit:

- full raw simulation outputs;
- large frame series;
- checkpoints.

Do not:

- merge to `master`;
- force-push;
- rewrite history;
- delete prior result directories.

---

## Required executor report

Write local:

`.agent_runtime/execution_report.md`

using the existing template.

It must include:

- source commit used for all runs;
- exact commands;
- actual run order;
- which cases executed / were skipped;
- numerical stability observations;
- final metrics;
- comparison-figure paths;
- any source changes made for post-processing;
- whether any result should be considered only smoke/pilot evidence;
- unresolved scientific questions;
- exact next action.

---

## Acceptance for this task

This task can PASS if:

- the production geometry gate is satisfied;
- the bounded pilot executes as specified, or failures are honestly captured;
- no result is mislabelled as converged physical validation;
- comparison evidence is durable and inspectable;
- no accepted Step-0 semantics are silently changed.

A pilot can still be scientifically useful even if one N fails; failure must remain visible in the evidence rather than being retried away.

## Finish

Push the durable evidence and any small analysis helper to:

`origin/agent-dev/direct-imbibition-pilot`

Do not merge.

Finish with:

**Independent review of CG3D-IMB-002 production-geometry pilot.**
