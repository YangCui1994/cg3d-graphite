# BI-CG-LECLAIRE-WETTING-CLOSURE-001 — Executor Contract

## Purpose

Close the remaining Leclaire-2017 wetting-reference ambiguity with a narrow
Pass-5 correction.

Known causal chain:

~~~text
Pass-4:
red = liquid
F = gas -> liquid
g = 1 solid
n_w = -grad(g)           wrong vs R1
circle-fit sign          returned complementary angle
    -> sessile-drop false PASS
    -> valid slit Pc with correct magnitude / reversed sign
    -> reachable Jurin tube empties
~~~

The correction is source-determined: use +grad(g) and measure theta through
liquid/red.

## Binding

Task: BI-CG-LECLAIRE-WETTING-CLOSURE-001

Control branch:
agent-dev/bilateral-episode-v0.1

Product branch:
agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001

Starting product tip:
ca10d6503857f2d6349ce313dd97561d9406fd9e

Pass-4 source/evidence are historical only. Pass-5 must have a new frozen source
SHA and a new evidence tip.

Read as binding:
1. docs/research/SCIENCE_MASTERLINE.md
2. docs/research/leclaire_cg/WETTING_PHASE_CONVENTION.md from control
3. this contract
4. .agent/evidence/BI-CG-LECLAIRE-PASS4-001/FRESH_REVIEW.md
5. .agent/evidence/BI-CG-LECLAIRE-PASS4-001/EXTERNAL_SCIENTIFIC_REVIEW_R3_CHANGES_REQUESTED.md
6. docs/research/leclaire_cg/VALIDATION_ARTIFACT_SPEC.md

## Hard scope boundary

Do not modify production lbm_solver_cg3d.py.
Do not port to Taichi/f32.
Do not tune R1 Eq.(18).
Do not introduce a new wetting model.
Do not redesign the now-valid slit-Pc geometry unless a new independent defect
is demonstrated.
Do not redesign the now-reachable Jurin geometry unless a new independent
defect is demonstrated.
Do not start V3/graphite/separator/PCS work.

## E1 — canonical convention

Implement and document:

~~~text
red = liquid/electrolyte/wetting
blue = gas/non-wetting
psi = (rho_red-rho_blue)/rho
F = grad(psi) = gas -> liquid
g = 1 solid, 0 fluid
n_w = +grad(g)/|grad(g)| = fluid -> solid
theta = through red/liquid
~~~

Update the L17 default wall-normal path.

A sign override may remain only as a labelled debug switch.

## E2 — contact-angle measurement

For a red/liquid sessile cap above a horizontal wall:

\[
\cos\theta_{\rm liquid}=-(z_c-z_w)/R.
\]

Fix implementation, docstring, metrics, rendering labels and stale docs.

Replace circular synthetic tests with independent geometric tests at
30/60/90/120/150 degrees.

The tests must fail if the circle-fit sign is reversed or if -grad(g) is used as
the canonical R1 normal.

## E3 — rerun existing wetting geometries

### Case 04 contact angle

Keep the current geometry unless a separate defect is proven.

Run 60/90/120 degrees and retain:
- raw initial/final fields;
- contour;
- fitted curve;
- liquid-side angle wedge;
- fit-quality metric;
- measured-vs-prescribed plot;
- error plot.

Predeclare gates before run and do not edit after results.

### Case 07 slit Pc

Keep the Pass-4 transverse-wall geometry.

It already has real contact lines, sealed longitudinal ends and no hidden second
interface.

Use:

\[
P_c=p_{gas}-p_{liquid}=\frac{2\sigma\cos\theta_{\rm liquid}}{h}.
\]

Run 60/90/120.

Required sanity:
- 60 -> Pc positive;
- 90 -> approximately zero;
- 120 -> Pc negative.

Wrong sign is FAIL_SOLVER / FAIL_CONVENTION, not INVALID_TEST.

### Case 08 Jurin

Keep the Pass-4 reachable geometry and precheck.

Recompute reachability before run. Under corrected convention verify connected
liquid, measurable reservoir level, measurable capillary level and

\[
\Delta h = \frac{2\sigma\cos\theta_{\rm liquid}}{\rho g h}.
\]

If precheck passes but the tube empties or no interface exists, report the
physical/numerical failure directly.

## E4 — raw artifacts must be tracked

The repo-wide *.npz ignore rule dropped Pass-4 raw evidence.

Add an explicit exception equivalent to:

~~~gitignore
!results/leclaire_cg/pass-*/**/raw/*.npz
~~~

Pass-5 must commit every raw snapshot referenced by a render manifest.

Before evidence commit verify with Git that every source_raw path exists, is
tracked and is reachable from the evidence commit.

Do not silently bind old local Pass-4 fields into Pass-5.

## E5 — freeze discipline

Before freeze:
- finish solver convention fix;
- finish measurement fix;
- finish harness/artifact fixes;
- run unit tests;
- run cheap smoke/dry paths for every case;
- verify report generation;
- verify raw NPZ tracking;
- verify no gate-key/broadcast/report-order bug.

Then freeze the complete source + harness and record a NEW candidate SHA.

After freeze, do not modify solver, measurement, harness, gates or artifact
writer.

Run the full Pass-5 matrix from that exact SHA.

If a harness defect appears after freeze: STOP, fix, create a new frozen SHA and
restart the Pass-5 run. Do not patch selected cases under the old SHA.

## E6 — immutable Pass-5 tree

Create:

~~~text
results/leclaire_cg/pass-05/
  VALIDATION_REPORT.md
  SUMMARY.json
  run_manifest.json
  UNIT_CHECKS.log
  case-01-.../
  ...
  case-11-.../
~~~

Do not overwrite Pass-4.

Every headline case must include README, metadata, metrics JSON/CSV, tracked raw
NPZ, figures, render manifest, reproduce script and case/full-run log binding.

## E7 — full regression

After freezing, run the full canonical matrix once.

Use verdict vocabulary:
- PASS
- FAIL_SOLVER
- FAIL_MEASUREMENT
- INVALID_TEST
- INCONCLUSIVE
- EXPLORATORY_UNGATED

Do not use INVALID_TEST for a solver sign failure.

## E8 — mechanical sigma is exploratory

Case 11 must not contribute a validating PASS unless:
- enough raw distributions/stress data are retained to recompute the observable;
- one-vs-two-interface contribution is explicit;
- bulk windows are clean;
- discrete total-variation/integral consistency is verified.

Otherwise label EXPLORATORY_UNGATED.

Do not retune A=(9/4) omega sigma.

## E9 — Laplace remains an open calibration question

Re-run only as part of the full regression. Do not redesign or retune it in this
stage.

Current science state:
- strong 1/R linearity;
- sigma scale roughly 12–13% high;
- unresolved.

## E10 — durable science/provenance cleanup

Current checkout must state one truth.

Correct as needed:
- R1 wall normal = +grad(g);
- theta = liquid/red;
- circle-fit sign;
- R5 mapping status;
- 科研通 provenance;
- stale "R5 local search" statements;
- superseded Pass-1/2/3/4 headlines;
- current Pass-5 headline.

Update the detailed formulation/map/manifest/atlas/execution-report/provenance
documents without rewriting Git history.

## Commit discipline

At minimum:
1. convention-fix
2. harness-fix
3. docs/provenance cleanup needed before freeze
4. validation-source — final frozen Pass-5 source
5. validation — immutable Pass-5 evidence
6. docs — final atlas/current headline if generated after evidence

The frozen source commit must contain the exact harness used for evidence.

## Success criteria

Wetting can close only if:
- R1 +grad(g) is implemented;
- liquid/red convention is unambiguous;
- independent analytic tests pass;
- contact angle 60/90/120 is measured through liquid and satisfies gate or
  honestly fails;
- slit Pc sign/magnitude are reported on the valid geometry;
- Jurin is reachable and measured;
- raw fields are tracked and regenerate figures;
- one frozen source SHA reproduces the full evidence tree.

A numerical wetting failure is acceptable evidence. A convention/provenance
ambiguity is not.

## Stop rule

After Pass-5 evidence and review request are committed: STOP.

Do not port to Taichi, promote modules, start production A/B, or start
V3/graphite.

Next action: fresh independent review.
