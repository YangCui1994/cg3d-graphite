# REVIEW — CG3D-IMB-001 / Review 002

## Binding

- Parent task: `CG3D-IMB-001`
- Rework task: `CG3D-IMB-001-R1`
- Reviewed source candidate: `3eef436b5d932c2faee6b124425c47d2e00caba6`
- Evidence commit: `042109cb8a3f6ddbd638ab993114a39ae2472eee`
- Branch: `agent-dev/direct-imbibition-step0`
- Review mode: independent static review

## Decision

`PASS`

This PASS accepts the Step-0 direct-imbibition implementation and its structural/numerical smoke evidence.

It does **not** constitute physical validation of a preferred `prewet_layers` value, full-scale imbibition dynamics, convergence on the production graphite geometry, or trapped-gas topology.

---

## Review 001 findings

### Finding 1 — explicit real-structure bounds

**RESOLVED.**

The implementation no longer infers the real electrode boundary from the first/last x-plane containing solid voxels.

The authoritative resolution is now:

1. explicit `real_bounds` argument;
2. structured geometry field `real_x=[lo, hi]`;
3. `None` for legacy drainage paths that do not require real bounds.

`make_geo_buffer.py` writes:

```text
real_x = [K, K + original_width]
```

which gives `[14,214)` for the current production buffered geometry.

Direct imbibition fails fast if explicit bounds are unavailable.

Legacy drainage does not require solid voxels and all-open synthetic drainage remains valid.

### Finding 2 — gas vs trapped-gas semantics

**RESOLVED.**

The direct-imbibition driver reports neutral metrics:

- `gas_saturation_dom`
- `gas_saturation_real`
- `gas_saturation_real_continuous`

It no longer reports all remaining gas as `s_nr` / residual / trapped gas.

The report explicitly records:

`trapped_gas_analysis = NOT_IMPLEMENTED`

Outlet-connectivity-based trapped-gas analysis remains deferred.

### Finding 3 — durable validation evidence

**RESOLVED for Step 0.**

The repository now contains:

`.agent/evidence/CG3D-IMB-001/validation_summary.md`

The summary binds the validation campaign to source candidate `3eef436`, records exact commands, status, exit codes, execution classes and interpretation, and explicitly lists NOT_RUN items.

The subsequent evidence commit contains only the summary and QA figures; no source files changed after the frozen candidate.

This is still executor-produced evidence rather than future controller-observed evidence, but it is sufficient for the current Step-0 protocol and no longer relies solely on a commit-message claim.

---

## Requirement disposition

| Requirement | Review |
|---|---|
| R1 independent direct imbibition | PASS |
| R2 phase / membrane orientation | PASS |
| R3 retain open-pore buffer | PASS |
| R4 direct IC | PASS |
| R5 explicit pre-wet parameter | PASS |
| R6 zero-bias baseline | PASS |
| R7 inspectable IC | PASS |
| R8 existing-mode regression | PASS |
| explicit real-domain bounds | PASS |
| neutral gas-output semantics | PASS |
| durable Step-0 evidence | PASS |
| initial-state QA visualization | PASS |
| full physical validation | NOT PART OF THIS ACCEPTANCE |
| trapped-gas topology | DEFERRED |

---

## Evidence reviewed

The durable validation summary reports PASS for:

- direct-imbibition layout suite;
- direct-imbibition runtime suite;
- post-processing regression;
- Level-A structural suite;
- checkpoint/resume drainage + I-R regression;
- direct-imbibition driver smoke using npz `real_x`;
- missing-bounds fail-fast path;
- `--real-bounds` override path;
- production geometry bound resolution to `[14,214)`;
- initial-state QA figure generation;
- deterministic figure sanity scan.

It explicitly marks as NOT_RUN:

- full production 200^3/228^3 direct-imbibition GPU campaign;
- unrelated Level-B solver-physics suites not touched by this rework;
- physical validation of any pre-wet thickness;
- trapped-gas outlet-connectivity analysis.

No physical-convergence claim is therefore accepted by this review.

---

## Initial-state visualization

The committed QA set contains:

- `initial_state_profile_prewet_2.png`
- `initial_state_profile_prewet_6.png`
- `initial_state_slice_prewet_2.png`
- `initial_state_slice_prewet_6.png`
- `initial_state_compare.png`

The plotting path consumes the same `build_layout` arrays used by `OpenSystem`; the layout test independently verifies the phase-fraction data used for plotting.

The examples N=2 and N=6 remain QA examples only and are not accepted as physically preferred values.

### Non-blocking visualization note

The current QA plotting helpers are primarily tuned to the baseline/default layout. Some annotations use default-layout assumptions (for example wall/reservoir presentation), and the x-profile visually emphasizes liquid/gas while solid is represented through the complementary fraction rather than a dedicated filled band.

This does not block the present baseline QA purpose, but should be revisited if the visualization becomes a general user-facing tool for arbitrary wall/reservoir configurations.

---

## Remaining scientific boundaries

The following remain deliberately unresolved:

1. physically preferred `prewet_layers`;
2. sharp vs diffuse initial liquid/gas transition;
3. production-scale direct-imbibition dynamics and convergence;
4. final gas-outlet representation for broader filling conditions;
5. outlet-connected versus trapped gas;
6. pressure-assisted direct imbibition.

These require later modeling/validation tasks and must not be inferred from this PASS.

---

## Final acceptance statement

The direct-imbibition Step-0 implementation is accepted as a structurally coherent baseline for subsequent scientific experiments.

The accepted baseline is:

```text
liquid reservoir
→ liquid-selective membrane
→ liquid open buffer
→ N pre-wet real-electrode layers
→ initially gas-filled real porous bulk
→ gas open buffer
→ gas-selective membrane
→ gas reservoir
```

with explicit real-domain bounds and zero imposed density difference as the baseline condition.

## Next action

Human selects whether to:

- integrate the accepted Step-0 implementation; or
- open the next modeling/validation task, most naturally a bounded production-geometry direct-imbibition pilot and pre-wet sensitivity study.
