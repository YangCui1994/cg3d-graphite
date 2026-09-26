# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `BI-DEEPSEEK-TRANSITION-001`
- **Status:** `COMPLETED`

## Summary

Two things were produced, both non-executing.

**Part A — independent evidence recomputation.** A new script
(`results/model_transition/recompute_metrics.py`) re-derives, directly from the
committed raw evidence of the accepted candidate `6c30260`, the quantities the
transition contract names: the periodic-C1 240k colour drift (full slope, R^2,
four 60k window slopes, increment-sign fractions), the C3 120k colour drift
(same, four 30k windows), and the V2 bilateral trapped-pocket metrics (maximum
blue relative mass drift, maximum front mirror error, trapped-cluster count
history, interaction status). No headline/summary value was used as a
calculation input; committed headline values are consulted only afterwards as a
cross-check and every cross-check is recorded with an explicit match verdict.
All cross-checks reproduce the committed producer reports within the declared
13-significant-digit text-precision tolerance.

**Part B — revised-V3 readiness and periodic-BC audit.** A design document
(`results/model_transition/V3_READINESS_AND_PERIODIC_BC_AUDIT.md`) covering the
nine items the contract requires: the accepted/frozen scientific state; why the
old isolation-time / pre-isolation V3 framing is obsolete (with a gate-by-gate
disposition); the revised V3 question and the closed-system balance that makes
it well posed; a buffer-size test matrix; the separation of hard invariants from
scientific diagnostics; whether a periodic-BC sanity suite should precede V3;
the proposed P0-P3 periodic tests; the expected evidence structure; and an
explicit stop boundary.

The audit's one substantive new result is quantitative: the closed-system
compressibility balance `d rho_gas = 3 Pc V_liquid/(V_gas+V_liquid)` reproduces
the measured V2 pocket compression (observed `+3.444e-3` at t = 1000 versus
`+3.421e-3` predicted from the V1c same-slit static capillary pressure, 0.7%
apart). The same balance predicts a 1.333x difference in pocket compression
between 1 B and 2 B, which means the old "1 B and 2 B must agree within 5%"
promotion gate would reject correct closed-system physics by a factor of 6.7.
That is the concrete reason the old gate cannot be carried forward.

A read-only probe of the committed V2 fields
(`results/model_transition/periodic_seam_probe.py`) additionally established
that the z direction is not inert: a `~5e-4` z-structure in `psi` develops from
an exactly z-uniform initial condition, saturates, and is spatially persistent
(`r = 0.996` between the mid and final snapshots). This is reported as a bounded
characterisation, and it is the basis for recommending that V3 be *not* gated on
a periodic-BC suite.

No simulation was run. The solver was not modified.

## Executor Claims — Changes

- `results/model_transition/recompute_metrics.py` (new):
  - change: independent recomputation of A1/A2/A3 from committed CSV/JSON.
  - reason: contract Part A; the transition needs evidence recomputed from raw
    artifacts rather than quoted from summaries.
- `results/model_transition/recomputed_metrics.json` (new):
  - change: machine-readable output of the above, with declared conventions, a
    convention-sensitivity block, and cross-check verdicts.
  - reason: contract Part A required output.
- `results/model_transition/periodic_seam_probe.py` (new, beyond the required
  list):
  - change: read-only z-seam / mirror probe over the committed V2 field
    archives.
  - reason: item 6 of Part B ("should a periodic-BC sanity suite precede V3?")
    cannot be answered factually without knowing how much z-structure the
    accepted run carries. Kept as a separate script and a separate JSON so that
    the contracted Part A output stays exactly as specified and no number in
    the audit document is hand-copied.
- `results/model_transition/periodic_seam_probe.json` (new, beyond the required
  list): output of the probe.
- `results/model_transition/V3_READINESS_AND_PERIODIC_BC_AUDIT.md` (new):
  - change: the nine required sections plus scope, commands and a term table.
  - reason: contract Part B required output.
- `results/model_transition/PROVENANCE.md`, `EXECUTION_REPORT.md` (new):
  - change: provenance and this report.
  - reason: contract required outputs.
- No production file changed. `lbm_solver_cg3d.py` and everything under
  `tests/` are byte-identical to the base commit.

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| A1 periodic C1 recomputation from raw evidence | PASS | full slope/R^2, four 60k slopes, sign fractions |
| A2 C3 recomputation from raw evidence | PASS | full slope/R^2, four 30k slopes, sign fractions |
| A3 V2 derivation from raw evidence | PASS | max blue drift, max mirror error, cluster history, interaction status |
| no headline/summary value as calculation input | PASS | headline values used only in a post-hoc `cross_check` block |
| script reads committed raw evidence directly | PASS | paths resolved from the script location; no network, no simulation |
| Part B items 1-9 present | PASS | section-to-item mapping in `V3_READINESS_AND_PERIODIC_BC_AUDIT.md` §1-§9 |
| no solver modification | PASS | see Git/Source State |
| no V3 execution | PASS | no V3 run exists; no simulation invoked |
| no periodic-BC test execution | PASS | the seam probe is read-only analysis of committed artifacts |
| no graphite / separator / gap / PCS work | PASS | no such files touched |
| product branch from exactly `6c30260` | PASS | see Git/Source State |
| commit and push the product candidate | PASS | see Git/Source State |

## Validation

### Part A recomputation

- **Command:** `C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/recompute_metrics.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** all three cross-checks reproduce the committed producer
  reports inside the declared text-precision tolerance.
- **Output / artifact reference:** `results/model_transition/recomputed_metrics.json`

| recomputed quantity | value | committed headline | verdict |
|---|---:|---:|---|
| periodic C1 240k colour slope | `+1.8046e-11 /step` | `+1.8046e-11` | reproduces |
| periodic C1 240k R^2 | 0.2797 | 0.2797 | reproduces |
| periodic C1 60k window slopes | `+1.93e-10`, `-5.04e-12`, `+1.24e-11`, `-4.66e-13` | same | reproduces |
| periodic C1 increment-sign fraction | 0.5492 full; 0.523 / 0.487 / 0.687 / 0.500 per window | 0.5492 | reproduces |
| C3 120k colour slope | `+2.6929e-12 /step` | `+2.6929e-12` | reproduces |
| C3 120k R^2 | 0.4146 | 0.4146 | reproduces |
| C3 30k window slopes | `+2.23e-11`, `-4.11e-12`, `+3.70e-12`, `+3.85e-12` | same | reproduces |
| C3 increment-sign fraction | 0.5585 full; 0.676 / 0.467 / 0.560 / 0.533 per window | 0.5585 | reproduces |
| V2 max blue relative drift | `5.1584e-07` | `5.1584e-07` | reproduces |
| V2 max front mirror error | `7.4500e-04 lu` derived from the position columns; `7.4005e-04 lu` from the committed `e_x` column | `7.4005e-04` | reproduces (difference is the 8-significant-digit text quantum of the position columns) |
| V2 trapped-cluster count | `{1}` at all 60 samples; t=0 single 38400-node cluster | 1 / 1 | reproduces |
| V2 interaction status | `NOT_REACHED`; `G_bulk` constant 146 | `NOT_REACHED` | reproduces |

Numerical stability / convergence / termination for the recomputation: not
applicable — the script performs deterministic post-processing of committed
text artifacts and contains no iterative solver; it is bit-reproducible.

### Periodic-seam probe

- **Command:** `C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/periodic_seam_probe.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** z-spread of `psi` is exactly 0 in the initial condition and
  saturates at `5.07e-04` in the final field (`rho` `1.32e-05`); the spatial
  pattern of the z-spread is persistent at `r = 0.996` between the mid and final
  snapshots; the field-based `E_psi` mean at the final snapshot is `8.57e-05`.
- **Output / artifact reference:** `results/model_transition/periodic_seam_probe.json`

### Not-run validations

- revised V3 buffer sweep: `NOT_RUN` (not authorized by this contract).
- periodic-BC suite P0-P3: `NOT_RUN` (not authorized by this contract; proposed
  in the audit document).

## Git / Source State

- base: `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`
- head / commit: recorded in `REVIEW_REQUEST.md`
- branch: `agent-task/BI-DEEPSEEK-TRANSITION-001`
- dirty files remaining: none in the product package (`.agent_runtime/` is
  git-ignored scratch and holds the review request)

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| recomputation script | `results/model_transition/recompute_metrics.py` | Part A, reproducible |
| recomputed metrics | `results/model_transition/recomputed_metrics.json` | Part A output |
| seam probe script | `results/model_transition/periodic_seam_probe.py` | read-only z-seam characterisation |
| seam probe output | `results/model_transition/periodic_seam_probe.json` | probe result |
| readiness audit | `results/model_transition/V3_READINESS_AND_PERIODIC_BC_AUDIT.md` | Part B |
| provenance | `results/model_transition/PROVENANCE.md` | binding, commands, incidents |
| review request | `.agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW_REQUEST.md` | reviewer binding |

## Deviations

1. Two files beyond the contract's required output list were added
   (`periodic_seam_probe.py`, `periodic_seam_probe.json`). Reason: the item-6
   question cannot be answered factually without a measurement of how much
   z-structure the accepted run carries, and the project's standing practice
   (§25.9 lesson) forbids hand-copied numbers in report tables. Scope was held
   to read-only analysis of already-committed artifacts, with no simulation.
2. The contract's A3 wording allows the V2 mirror error to be "derived or
   extracted". Both are reported rather than one, because they differ at the
   1.0e-5 lu level purely from the position columns' text quantisation; the
   difference is disclosed in the JSON rather than silently resolved.

## Assumption / Modeling Impact

The audit document proposes a new acceptance criterion for the revised V3
(comparison against the closed-system compressibility balance rather than
equality between buffer sizes) and proposes new hard invariants N1-N4. These
are **proposals**. They are marked in the document as requiring contract-owner
approval and are not adopted anywhere. No accepted gate, boundary condition,
initial condition, convergence rule or physical parameter was changed, and no
existing result was invalidated.

One previously accepted observable is recommended for retirement as a
*primary* observable (`psi`-threshold trapped volume); the recommendation is
documented with the evidence that motivates it and remains an owner decision.

## Existing Evidence Potentially Affected

None. The work is additive documentation and post-processing. All accepted
results (V0, V1c, V2, conservation audit, fix, colour closure) stand as
recorded, and the recomputation in this task independently reproduces their
committed headline values.

## Unresolved Issues / Human Decisions

- The acceptance tolerance for departure from the closed-system balance (§3.2
  of the audit) is not chosen here.
- The V3 comparison horizon is proposed (150k as a first choice) but not fixed.
- Whether the conditional 4 B case is included in the sweep.
- Whether the recommended retirement of `psi`-threshold trapped volume as a
  primary observable is accepted.
- The V2 review's non-blocking finding N1-N9 (including the `d(t)` identity
  defect) remains unfixed on the accepted candidate; it touches the
  interface-position observable that the revised V3 would use, and the audit
  document flags it.

## Suggested Next Action

Fresh DeepSeek review of this package against
`.agent/episodes/bilateral-imbibition-v0.1/DEEPSEEK_TRANSITION_REVIEWER_CONTRACT.md`,
then return the package to the external reviewer.
