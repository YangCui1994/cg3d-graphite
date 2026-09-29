# DeepSeek Transition Calibration Contract

Task ID: BI-DEEPSEEK-TRANSITION-001

## Purpose

Use one real, low-risk task to calibrate DeepSeek as the next executor model
while producing a useful readiness artifact for the revised V3 stage.

This is NOT a V3 execution task.

## Frozen scientific state

Accepted product candidate:

6c30260dfe0c8b61ea9609e6bffa5c487312cf06

Accepted production numerical path:

total_fix  = T3
colour_fix = C1X
acc_fix    = A2

Accepted and frozen:
- V1c single-front validation;
- V2 bilateral trapped-pocket validation;
- total-channel conservation fix;
- colour-channel conservation fix.

Do not redesign or modify any accepted solver path.

## Product branch

agent-task/BI-DEEPSEEK-TRANSITION-001

Base exactly:

6c30260dfe0c8b61ea9609e6bffa5c487312cf06

## Part A — independent evidence recomputation

Do not use headline values from SUMMARY.md as calculation inputs.

### A1 periodic C1

Source:
results/colour_closure/ac_C1_T3C1X_A2_240k/mass_series.csv

Recompute:
- full 240k colour slope;
- full R2;
- four 60k colour slopes;
- increment-sign fractions.

### A2 C3

Source:
results/colour_closure/ac_C3_T3C1X_A2_120k/mass_series.csv

Recompute:
- full 120k colour slope;
- full R2;
- four 30k colour slopes;
- increment-sign fractions.

### A3 V2

Source:
results/colour_closure/levelc_v2_fix/v2_primary/

Independently derive or extract from raw committed evidence:
- maximum blue relative mass drift;
- maximum front mirror error;
- trapped-cluster count/history;
- interaction status.

Write:
- results/model_transition/recompute_metrics.py
- results/model_transition/recomputed_metrics.json

The script must read committed raw evidence directly.

## Part B — useful new artifact: revised V3 readiness design

Create:

results/model_transition/V3_READINESS_AND_PERIODIC_BC_AUDIT.md

It must contain:

1. accepted/frozen scientific state;
2. why the old V3 isolation-time/pre-isolation framing is obsolete;
3. revised V3 question: finite liquid-buffer sensitivity in the closed
   bilateral trapped-pocket system;
4. proposed buffer-size test matrix;
5. hard invariants versus scientific diagnostics;
6. whether a periodic-BC sanity suite should precede V3;
7. if useful, proposed P0-P3 periodic tests:
   - fully periodic single phase;
   - fully periodic two-phase slab;
   - z-periodic with x/y solid walls;
   - solid geometry crossing the z-periodic seam;
8. expected evidence/artifact structure;
9. explicit stop boundary.

The document may propose experiments, but must not execute V3 or the periodic
test suite.

## Scope restrictions

Do not:
- modify lbm_solver_cg3d.py;
- modify accepted physics or gates;
- run V3;
- begin graphite, separator, gap or PCS work;
- revive the superseded old V3 isolation-time framing.

## Required outputs

results/model_transition/
- recompute_metrics.py
- recomputed_metrics.json
- V3_READINESS_AND_PERIODIC_BC_AUDIT.md
- EXECUTION_REPORT.md
- PROVENANCE.md

Also write:
.agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW_REQUEST.md

The review request must bind exact base/candidate SHAs, changed files, commands
and evidence paths.

## Stop

Commit and push the product candidate, prepare REVIEW_REQUEST.md, then STOP.

Do not launch or simulate V3.
Do not self-review.
