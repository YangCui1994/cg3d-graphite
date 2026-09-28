# External Scientific Review R3 — BI-CG-LECLAIRE-PASS4-001

## Binding

- Frozen Pass-4 source candidate: \`0b3da4e954878dc22618330caed9f0da0782d449\`
- Pass-4 evidence/package tip: \`ca10d6503857f2d6349ce313dd97561d9406fd9e\`
- Fresh-review publication commit: \`99fe6a53538fbf1602673f50eeb2814a41824c7d\`
- Fresh-review decision: \`CHANGES_REQUESTED\`

## External decision

**CHANGES_REQUESTED**

The fresh review is accepted. Its central finding is independently supported by
the current repository state: Pass-4 froze the wrong wall-normal direction for
the already-fixed liquid/red contact-angle convention, and the contact-angle
instrument used the complementary spherical-cap formula while labelling its
output as the liquid-side angle.

This invalidates the Pass-4 wetting PASS, but it does **not** reopen the bulk
Leclaire formulation work. Eq.(4), the X_W gradient path, recoloring, the
unrelaxed perturbation operator, beta/positivity work and the corrected f64 mass
closure should be preserved.

---

## R3-1 — HARD BLOCKER: the normative wall-normal convention is wrong

The project convention correctly freezes:

\`\`\`text
red  = liquid/electrolyte/wetting
blue = gas/non-wetting
psi  = (rho_red-rho_blue)/rho
F    = grad(psi) = gas -> liquid
theta = measured through liquid/red
g    = 1 solid, 0 fluid
\`\`\`

The incorrect part is:

\`\`\`text
n_w = -grad(g)/|grad(g)| = solid -> fluid
\`\`\`

The paper formulation already transcribes R1 §II.E / Eqs.(34)-(38) as

\[
\mathbf n_w=\nabla g^{(3)}.
\]

With \(g=1\) in solid and \(g=0\) in fluid, this points **fluid -> solid**.

The frozen source candidate implements the negation by default.

### Required correction

For the canonical \`L17_CORE\` convention:

\[
\boxed{
\mathbf n_w=+\frac{\nabla g}{|\nabla g|}
}
\]

and retain:

\[
\boxed{
\theta=\theta_{\rm liquid/red}
}
\]

Do not keep the sign as a physical calibration knob. A debug override may remain
only as an explicitly non-canonical regression switch.

The normative document and the paper-formulation document must be made
consistent.

---

## R3-2 — HARD BLOCKER: the contact-angle measurement formula returns the complementary angle

The current circle-fit instrument uses

\[
\cos\theta=\frac{z_c-z_{wall}}{R}
\]

while calling the result "theta measured through the psi>0 red phase".

For a sessile red/liquid drop occupying the +z side of the wall, the liquid-side
spherical-cap relation is

\[
\boxed{
\cos\theta_{\rm liquid}
=
-\frac{z_c-z_{wall}}{R}.
}
\]

Therefore the current instrument returns \(180^\circ-\theta_{\rm liquid}\).

This is independently visible in the committed case-04 fit:

- prescribed 60 deg: reported 53.7 deg, correct liquid-side value ~126 deg;
- prescribed 90 deg: reported 84.3 deg, liquid-side ~96 deg;
- prescribed 120 deg: reported 112.7 deg, liquid-side ~67 deg.

The existing synthetic unit tests are circular because they construct the
reference cap with the same sign convention as the defective instrument.

### Required correction

1. fix the analytic spherical-cap convention first;
2. replace the synthetic unit tests with geometrically independent constructions;
3. verify 30/60/90/120/150 deg;
4. then rerun the LBM 60/90/120 cases under the corrected R1 wall normal;
5. render the fitted circle, wall and angle wedge so the reported phase-side
   angle is visually inspectable.

The existing Pass-4 case-04 PASS is withdrawn.

---

## R3-3 — Important positive result: case-07 geometry is now valid

The previous external review required a real wall-intersecting meniscus. Pass-4
does provide one:

- slit plates transverse to the meniscus;
- two real wall contact lines;
- x ends sealed;
- z-invariant extrusion;
- no hidden periodic second interface.

So case-07 is **not an invalid test anymore**.

Its result is more informative than the executor headline suggests:

\[
P_c^{meas}
\approx
- P_c^{theory}
\]

with nearly the correct magnitude:

- 60 deg: ratio ~ -1.023;
- 90 deg: approximately zero;
- 120 deg: ratio ~ -1.081.

This is exactly the signature expected from the complementary-angle convention.

### Required interpretation

Current Pass-4 case-07 should be classified as:

\`FAIL_SOLVER / FAIL_CONVENTION\`

not \`INVALID_TEST\`.

After R3-1/R3-2 are fixed, this same geometry is a strong candidate for the
clean capillary-pressure validation and should be rerun without redesigning it
again.

---

## R3-4 — Jurin configuration is now reachable; the convention empties the tube

The Pass-4 reachability precheck is valid: the predicted equilibrium height lies
inside the capillary measurement region.

The fresh review reports that the capillary liquid is expelled rather than
raised while red mass remains conserved. This is consistent with the same
complementary wetting convention.

Therefore the current \`INCONCLUSIVE\` status should not be read as a geometric
failure.

After the wetting convention is corrected, rerun the existing reachable Jurin
configuration before redesigning it again.

---

## R3-5 — HARD ARTIFACT BLOCKER: the raw fields were never committed

The new visualization workflow generated figures and render manifests that
reference raw NPZ files, but the repository-wide

\`\`\`text
*.npz
\`\`\`

ignore rule silently excluded them.

Examples referenced by manifests but absent from the evidence tree:

- \`case-04-contact-angle/raw/theta120_final.npz\`
- \`case-07-slit-capillary-pressure/raw/theta60_final.npz\`
- \`case-11-mechanical-sigma/raw/t_final.npz\`

Thus the repository currently contains rendered outputs without the raw fields
needed to regenerate them.

This directly violates \`VALIDATION_ARTIFACT_SPEC.md\`.

### Required correction

Add an explicit exception, e.g. equivalent to:

\`\`\`gitignore
!results/leclaire_cg/pass-*/**/raw/*.npz
\`\`\`

and commit the existing Pass-4 raw snapshots if they still exist and their
hashes match the manifests.

If any raw snapshot is gone, rerun that case from the corrected frozen candidate
and create a new immutable pass instead of fabricating/reconstructing the field
from metrics.

No publication-facing validation artifact is complete without the bound raw
field.

---

## R3-6 — HARD PROVENANCE BLOCKER: frozen source and evidence-producing harness differ

The frozen source SHA \`0b3da4e...\` contains a Pass-4 harness that cannot
produce all of the committed evidence:

- case-04 references an unrenamed gate key;
- case-07 contains a broadcasting defect;
- report generation is ordered after \`sys.exit(main())\`.

The evidence tip fixes the harness and reruns cases 04/07.

The solver physics source is byte-identical, so this does not invalidate the
physics calculations by itself. It does invalidate the current claim that one
frozen source candidate plus one command reproduces the complete evidence tree.

### Required correction

Create a new frozen source candidate **after** all harness fixes, before the next
full validation run.

The next evidence package must be generated from that exact source SHA without
case-specific post-freeze harness edits.

If a harness defect is discovered after freeze:
- create a new source candidate;
- rerun the full affected validation pass;
- do not retain the old candidate SHA as the run binding.

---

## R3-7 — mechanical sigma remains exploratory

The derivation itself is useful, but the current case does not cleanly satisfy
its stated premises:

- the periodic planar domain contains two interfaces;
- the selected bulk-reference window is not demonstrably independent of the
  interface shoulder;
- the raw distribution/tensor data needed to independently recompute the stress
  observable is not retained in the repository.

Therefore the current

\[
\sigma_{mech}/\sigma_{input}\approx0.768
\]

must be labelled \`EXPLORATORY / UNGATED\`, not a validating PASS.

The combination

\[
\sigma_{Laplace}\approx1.13\,\sigma_{input}
\]

versus

\[
\sigma_{mech}\approx0.77\,\sigma_{input}
\]

still usefully rules out a simplistic "multiply one global calibration factor"
story, but it is not yet a closed quantitative diagnosis.

### Required correction

Use a geometry and raw-output schema that permit the mechanical observable to be
recomputed directly:
- retain the required \(N_i\) / momentum-flux tensor or an equivalently complete
  sourced quantity;
- isolate one interface or explicitly account for both interfaces;
- define bulk windows away from all interfaces;
- report the total-variation/integral consistency check.

---

## R3-8 — Laplace status remains unchanged

Preserve the Pass-4 Laplace result:

- strong \(1/R\) linearity;
- R1 \(A=(9/4)\omega\sigma\) not retuned;
- sigma calibration outside the gate (~+12-13%);
- no stable large-R extrapolation currently established.

Do not use the mechanical-sigma result to retune \(A\).

---

## R3-9 — durable-record cleanup is still incomplete

Two stale R5 provenance statements remain, including "local search rather than
download", conflicting with the corrected 科研通 record.

Additional old pass-3 top-level artifacts remain without an in-file
\`SUPERSEDED\` banner.

Clean these in the next correction round. The latest checked-out documents must
state one current truth without requiring Git archaeology.

---

## Preserve without reopening

Do not disturb:

1. branch isolation / production solver unchanged;
2. corrected R1 Eq.(4) term;
3. D3Q19 tables and MRT structure;
4. R1 X_W one-dimensional gradient;
5. explicit beta recoloring and positivity window;
6. separate unrelaxed perturbation operator;
7. \(A=(9/4)\omega\sigma\);
8. corrected global f64 mass closure;
9. equal-wavelength x/y Fourier regression and its limited axis-symmetry label;
10. corrected case-07 geometry;
11. complex-wall global conservation result;
12. artifact directory/render-manifest machinery itself.

---

## Required correction round

Keep the next round narrow.

### E1 — correct convention and instrument
1. change canonical R1 wall normal to \(+\nabla g/|\nabla g|\);
2. keep theta measured through liquid/red;
3. fix the circle-fit sign;
4. replace circular convention tests with independent analytic geometry tests;
5. rerun contact angle 60/90/120.

### E2 — rerun wetting validations
6. rerun the existing valid case-07 slit geometry;
7. rerun the existing reachable Jurin geometry;
8. expect geometry to remain unchanged unless the corrected convention reveals
   a separate failure.

### E3 — artifact/provenance closure
9. commit raw NPZ snapshots under an explicit gitignore exception;
10. freeze the source only after harness fixes;
11. generate the entire evidence pass from that exact source SHA;
12. fix R5/科研通 stale provenance statements;
13. mark superseded top-level legacy files explicitly.

### E4 — diagnostic hygiene
14. demote current mechanical sigma to exploratory;
15. if rerun, retain recomputable stress/distribution data and correct the
    geometry/reference window;
16. preserve the Laplace FAIL without coefficient retuning.

Then run a fresh independent review.

## External status

\`\`\`text
branch isolation                         PASS
R1 bulk formulation                     PASS
Eq.(4) / X_W corrections                PASS
global f64 mass closure                 PASS

wetting phase identity                   PASS
R1 wall-normal sign                     FAIL
contact-angle measurement convention     FAIL
case-04 wetting PASS                     WITHDRAWN

case-07 geometry                         PASS
case-07 current result                   FAIL_CONVENTION (magnitude ~correct, sign inverted)
case-08 reachability                     PASS
case-08 current result                   FAIL/INCONCLUSIVE due convention

raw-field artifact retention             FAIL
frozen-source/evidence harness binding   FAIL
mechanical-sigma validation              EXPLORATORY ONLY
Laplace sigma calibration                FAIL / unresolved

production promotion                     NOT AUTHORIZED
Taichi/f32 port                          HOLD
overall                                  CHANGES_REQUESTED
\`\`\`
