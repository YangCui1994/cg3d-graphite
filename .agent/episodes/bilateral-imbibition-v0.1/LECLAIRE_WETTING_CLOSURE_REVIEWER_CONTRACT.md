# BI-CG-LECLAIRE-WETTING-CLOSURE-001 — Fresh Reviewer Contract

Use a fresh independent session. Do not read the executor transcript and do not
modify the candidate.

Bind to the new Pass-5 frozen source SHA and evidence/package tip.

Verify:

## A. Freeze binding
- frozen source contains the exact harness used for the full Pass-5 run;
- no source/harness/gate change occurs between freeze and evidence;
- one command from the frozen source reproduces the complete matrix.

## B. Convention
Independently verify:
red=liquid, blue=gas, F=gas->liquid, g=1 solid,
n_w=+grad(g)=fluid->solid, theta through liquid/red.

Re-run independent 30/60/90/120/150 analytic tests. Reject circular tests.

## C. Contact angle
From tracked raw fields recompute contour, fitted geometry and liquid-side angle.
Regenerate the fitted-circle/angle-wedge figure.

## D. Slit Pc
Verify the valid transverse geometry, real contact lines and sealed ends.
Recompute p_gas-p_liquid and 2 sigma cos(theta)/h for 60/90/120.
A sign failure is solver/convention failure, not invalid-test.

## E. Jurin
Recompute reachability, reservoir/capillary levels, measured rise, theory and
ratio from raw fields.

## F. Raw artifacts
Verify every render_manifest source_raw exists in Git, is tracked, belongs to
the evidence commit and regenerates the figure.

## G. Full regression
Independently rerun unit checks, the full Pass-5 matrix and representative
figures.

## H. Preserved science
Ensure no regression/redefinition of Eq.(4), X_W gradient, beta, perturbation
ordering, A=(9/4) omega sigma or f64 conservation.

## I. Mechanical sigma
Treat as exploratory unless raw data and derivation premises are actually closed.

## J. Durable science docs
Verify one consistent current statement for R1 wall normal, liquid-side angle,
R5 mapping, 科研通 provenance, Pass-5 headline and superseded passes.

Decision exactly one:
PASS / CHANGES_REQUESTED / HUMAN_REQUIRED.

PASS closes only the NumPy/f64 wetting-reference stage.

Publish review artifacts under:
.agent/evidence/BI-CG-LECLAIRE-WETTING-CLOSURE-001/

on the control branch, then STOP.
