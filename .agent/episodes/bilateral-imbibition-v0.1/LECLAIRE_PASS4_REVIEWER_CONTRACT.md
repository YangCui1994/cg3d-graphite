# BI-CG-LECLAIRE-PASS4-001 — Fresh Reviewer Contract

Use a fresh independent session. Do not read the executor transcript and do not
modify the candidate.

Bind explicitly to the frozen Pass-4 source candidate and evidence/package tip
named in the executor's review request.

## A. Convention

Verify from definitions, not from calibration:
- red = liquid/electrolyte/wetting;
- blue = gas/non-wetting;
- psi = (rho_red-rho_blue)/rho;
- F = gas -> liquid;
- g = 1 solid / 0 fluid;
- n_w = solid -> fluid;
- theta measured through red/liquid.

Re-run the analytic 60/90/120 convention tests.

## B. Contact-angle case

Inspect raw fields and renderings.
Recompute the contour/normal fit and the angle errors.
Verify the visualization actually corresponds to the retained raw data.

## C. Slit Pc

Verify the meniscus intersects both walls.
Verify 60/90/120 produce the expected sign structure.
Recompute Pc and both theory comparisons:
- nominal input sigma/theta;
- independently measured sigma/theta.

Reject the case if the geometry has no contact line or a hidden periodic second
interface invalidates the interpretation.

## D. Jurin

Verify the reachability precheck before accepting the run.
Recompute reservoir/capillary heights and Jurin prediction.
Inspect the raw field to verify both levels are genuinely present.

## E. Laplace

Recompute equilibrium radius, pressure jump and all regressions.
Verify no coefficient was retuned after prior failure.
Inspect residuals and large-R stability.

## F. Mechanical sigma

Audit the derivation first.
If the macroscopic prefactor is not source-closed, ensure the result is labelled
exploratory/ungated.
Recompute the stress integral from retained raw data.

## G. Complex wall

Verify global mass closure, wall-band metric and interface/contact-line
diagnostic.
Do not accept an attribution claim that the evidence does not separate.

## H. Artifact/visualization integrity

For every headline case:
- raw snapshots exist;
- render manifest binds figures to raw files;
- theory/actual/error are all present;
- figures regenerate;
- axes/scales/convention are consistent;
- invalid/inconclusive results are still rendered and retained.

## I. Durable-record consistency

Search current docs for stale contradictory claims:
- pass counts;
- R5 mapping status;
- acquisition route;
- Table-IV ordering;
- Laplace status;
- current candidate/evidence SHA.

Latest files must contain one current truth; history remains in Git.

## Decision

Exactly one:
- PASS
- CHANGES_REQUESTED
- HUMAN_REQUIRED

PASS closes only the NumPy/f64 reference-model validation stage. It does not
authorize Taichi/f32 port or production promotion.

Write the review artifacts under the task's normal review path, publish them to
the control branch evidence directory, then STOP.
