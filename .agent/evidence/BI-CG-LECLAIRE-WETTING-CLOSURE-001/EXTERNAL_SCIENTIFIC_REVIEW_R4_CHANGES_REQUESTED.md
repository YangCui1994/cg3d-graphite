# External Scientific Review R4 — BI-CG-LECLAIRE-WETTING-CLOSURE-001

## Binding

- Product branch: \`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001\`
- Frozen Pass-5 source candidate: \`b65bdce3758dd967df1a3f5559c7014f97fd960b\`
- Pass-5 evidence/package tip: \`ad07b18c548a06babf385f0b33f13e52433234a4\`
- External decision: **CHANGES_REQUESTED**

## Executive finding

Pass-5 materially improves the Leclaire reference line.

The canonical code path now uses the R1 wall-normal direction
\(+\nabla g\), the sessile-drop measurement uses the correct liquid-side
circle relation, the contact-angle benchmark passes quantitatively, and the
transverse slit capillary-pressure benchmark now has the correct sign and
magnitude.

However, the wetting-reference stage is **not yet scientifically closed** for
two independent reasons:

1. the Jurin case still does not represent a connected capillary-rise system;
2. the frozen harness/evidence writes the superseded \(-\nabla g\) convention
   into current machine-readable artifacts even though the executed solver uses
   \(+\nabla g\).

The first is a validation-physics defect; the second is a provenance/science
record defect.

The bulk Leclaire formulation must not be reopened.

---

# 1. Freeze discipline — ACCEPTED

The Pass-5 freeze invariant is materially better than Pass-4.

Comparison:

\`b65bdce3758dd967df1a3f5559c7014f97fd960b..ad07b18c548a06babf385f0b33f13e52433234a4\`

shows no post-freeze edits to:
- \`experimental/leclaire_cg/**\`;
- \`tests/leclaire_cg/pass05.py\`;
- measurement code;
- gates;
- artifact writer.

The evidence commit adds generated results/raw artifacts/reports and
documentation.

Therefore the solver/harness used by Pass-5 is genuinely frozen before the
evidence run.

This closes the Pass-4 source/evidence binding defect.

---

# 2. Raw artifact retention — ACCEPTED

The Pass-5 evidence tree contains tracked raw NPZ files.

Repository-tree audit:

- tracked Pass-5 NPZ files: **39**;
- render manifests: **11**;
- \`source_raw\` references across manifests: **36**;
- missing manifest targets: **0**.

The gitignore exception is present:

\`!results/leclaire_cg/pass-*/**/raw/*.npz\`

This closes the Pass-4 "figures without committed raw source" blocker.

Note: the evidence commit also backfills historical Pass-4 NPZ files. Those are
not used as Pass-5 source data and must remain clearly historical.

---

# 3. Canonical R1 wall-normal implementation — CODE PASS

The frozen solver now defaults to:

\[
\boxed{
n_w=+\nabla g/|\nabla g|
}
\]

with:

\`\`\`text
g = 1 solid
g = 0 fluid
n_w = fluid -> solid
\`\`\`

This matches R1 Eqs.(34)-(38) as transcribed in \`PAPER_FORMULATION.md\`.

The production \`psi_solid\` wall-colour model is not imported into L17_CORE.

The new analytic convention unit checks explicitly test:
- 30 deg;
- 60 deg;
- 90 deg;
- 120 deg;
- 150 deg;
- canonical +grad(g);
- rejection of -grad(g);
- the secant branch.

The unit-check package reports **88/88 PASS**.

The analytic cap construction is sufficiently independent of the measurement
formula: it constructs the cap from the contact-line tangent / inward normal
and separately checks the recovered liquid-side angle.

This is a real closure improvement over Pass-4.

---

# 4. Sessile contact angle — SCIENTIFIC PASS

The corrected measurement relation is:

\[
\boxed{
\cos\theta_{liquid}=-(z_c-z_w)/R
}
\]

Pass-5 reports:

| prescribed | measured liquid-side | abs. error |
|---:|---:|---:|
| 60 deg | 65.19 deg | 5.19 deg |
| 90 deg | 95.70 deg | 5.70 deg |
| 120 deg | 129.40 deg | 9.40 deg |

All are inside the predeclared 15-degree gate.

The fit-quality metrics are also well inside the geometric-RMS gate.

Therefore the R1 wetting operator now has credible quantitative sessile-drop
support under the fixed red/liquid phase convention.

This part of wetting closure is accepted.

---

# 5. Slit capillary pressure — SCIENTIFIC PASS

The transverse slit geometry introduced in Pass-4 remains the correct geometry:
- plates transverse to the meniscus;
- real contact lines;
- x ends sealed;
- no hidden longitudinal periodic second interface;
- z is only the extrusion direction.

Pass-5 results:

| theta | Pc measured | Pc theory | ratio |
|---:|---:|---:|---:|
| 60 deg | +2.0509e-3 | +2.0000e-3 | 1.025 |
| 90 deg | -4.2e-7 | ~0 | absolute near-zero |
| 120 deg | -2.1567e-3 | -2.0000e-3 | 1.078 |

The mandatory sign structure is now correct.

This is exactly the inverse of the Pass-4 sign error and is strong evidence that
the wall-normal convention correction is physically effective, not merely a
sessile-drop measurement relabeling.

The current slit-Pc benchmark is accepted.

A future refinement may measure the local slit contact angle directly rather
than compare only to the prescribed angle, but that is not required to accept
the present wetting closure evidence.

---

# 6. HARD BLOCKER — the Jurin geometry is still not a connected Jurin system

The current case-08 claims:

\`\`\`text
initial = liquid column continuous from reservoir into capillary
\`\`\`

but the actual initialization is:

\`\`\`python
psi[:, :, :z_res0] = +1
# z_res0 = 14

psi[:, wall:n_y-wall, neck:z_cap0] = +1
# neck = 18, z_cap0 = 20
\`\`\`

Therefore:

\`\`\`text
reservoir liquid       z < 14
gas gap                z = 14 ... 17
capillary liquid slug  z = 18 ... 19
\`\`\`

The liquid in the capillary is **not connected** to the reservoir at t=0.

This already invalidates the interpretation as Jurin rise.

There is a deeper geometry issue.

The capillary side walls begin only at:

\`z >= neck = 18\`

while the predicted reservoir free surface is:

\`z_res ~= 13.22\`

Thus the narrow capillary is not immersed below the reservoir free surface.
Between the reservoir surface and the capillary entrance is an open gas region.

Jurin's law assumes a connected liquid column in a tube/slit immersed in a
reservoir. The current precheck uses a connected-volume hydrostatic formula for
a geometry whose liquid phases are topologically disconnected.

So:

\[
\Delta h = \frac{2\sigma\cos\theta}{\rho g h}
\]

is not a valid prediction for the actual initialized topology.

The observed trace:

\`\`\`text
t=0    capillary level 19, reservoir 13
t=400  capillary level 18, reservoir 12
t>=800 capillary level NaN
\`\`\`

is fully compatible with disappearance/retraction of an isolated capillary
liquid slug. It is **not evidence of a Jurin solver failure**.

### Correct classification

Current Pass-5 case-08:

\`INVALID_CONFIGURATION / FAIL_TEST_GEOMETRY\`

not:

\`FAIL_SOLVER\`.

### Required redesign

Use a physically connected geometry, for example:

- a capillary/slit whose walls extend below the reservoir free surface, with
  an open immersed entrance; or
- a side-by-side reservoir and vertical capillary connected by a lower liquid
  channel.

The capillary liquid must be continuously connected to the reservoir before the
run, and the theoretical volume constraint must correspond to the actual
geometry.

This is the remaining load-bearing wetting-validation blocker.

---

# 7. HARD BLOCKER — machine-readable Pass-5 evidence states the wrong wall-normal convention

The executed solver uses \(+\nabla g\), but the frozen Pass-5 harness still
hard-codes the old Pass-4 text.

Examples in the frozen source:

\`\`\`python
wall_normal="n_w = -grad(g)/|grad(g)|  (solid->fluid)"
wall_normal_sign=-1
\`\`\`

and the Pass-5 summary writes:

\`\`\`text
convention = n_w=-grad(g)/|grad(g)| solid->fluid; theta through liquid/red
\`\`\`

Consequences in committed evidence:

- \`pass-05/SUMMARY.json\` states the wrong convention;
- \`case-04-contact-angle/metrics.json\` states the wrong wall normal;
- case-04 metadata/README carry the wrong sign;
- \`VALIDATION_REPORT.md\` repeats the wrong convention.

At the same time:
- \`solver.py\` actually uses +grad(g);
- \`PAPER_FORMULATION.md\` correctly states +grad(g);
- \`EXECUTION_REPORT.md\` correctly states +grad(g).

This is precisely the multiple-sources-of-truth failure the science-masterline
work is intended to eliminate.

The numerical wetting results are not invalidated by this text bug because the
runtime solver is correct, but the current evidence package cannot be called
scientifically closed while its machine-readable provenance names the opposite
model.

Because these wrong strings are emitted by the frozen harness itself, the
source candidate must be corrected and a new frozen validation pass produced.

---

# 8. Additional provenance defects

These are smaller than the two blockers above but should be fixed in the same
round.

## 8.1 operators.py docstring

\`wall_normals()\` still describes the superseded \(-\nabla g\) convention even
though the solver default is now +grad(g).

## 8.2 pass05.py header

The Pass-5 harness header still says it runs "pass-04 cases" into
\`results/leclaire_cg/pass-04/\` and references the Pass-4 validation contract.

The actual OUT_ROOT is Pass-5, but the scientific/provenance text is stale.

## 8.3 artifact render version

\`artifact.py\` writes:

\`script_version = "pass-04"\`

into Pass-5 render manifests.

## 8.4 validation report stage

The generated Pass-5 report says:

\`stage = BI-CG-LECLAIRE-PASS4-001\`

instead of the Pass-5 wetting-closure stage.

These do not change numerical results, but they prevent the current artifact
tree from being a clean durable scientific record.

---

# 9. Mechanical surface tension — strong result, but documentation is stale

Pass-5 case-11 reports:

\[
\sigma_{mech}=0.0199999067
\]

for:

\[
\sigma_{input}=0.0200000000
\]

so:

\[
\sigma_{mech}/\sigma_{input}=0.9999953.
\]

The committed stress profile itself sums over the stated integration window to:

\[
0.0199999067
\]

which independently reproduces the reported metric at the text-evidence level.

The case now also records:
- retained full \(N_i\) distribution;
- one isolated integration interface;
- discrete total variation ~2;
- a low-stress bulk window.

This is much stronger than Pass-4 and supports the conclusion that the
perturbation amplitude is not globally low by ~20%.

However, two hygiene issues remain:

1. the raw artifact stores arrays as f32 even though the solver is f64; this is
   probably sufficient for the diagnostic but should be stated explicitly in the
   raw schema;
2. \`MECHANICAL_SIGMA_DERIVATION.md\` still presents the superseded Pass-4
   result 0.01537 / 0.768 as its current measured outcome.

The derivation document must be updated to separate:
- Pass-4 failed diagnostic;
- Pass-5 corrected/recomputable diagnostic.

### Scientific consequence

If the Pass-5 mechanical result survives fresh binary-level recomputation, then:

\`\`\`text
mechanical sigma  ~1.000 sigma_input
Laplace local sigma ~1.02-1.06 sigma_input
free-intercept regression slope ~1.127 sigma_input
\`\`\`

This strongly shifts suspicion away from a global R1 perturbation-amplitude
factor and toward the Laplace measurement/regression/finite-radius treatment.

---

# 10. Laplace — keep FAIL, but the regression interpretation needs care

Pass-5:

| R_measured | local sigma / input |
|---:|---:|
| 5.87 | 1.056 |
| 6.87 | 1.042 |
| 7.91 | 1.032 |
| 8.89 | 1.018 |

The zero-intercept estimate is:

\[
\sigma_{0-int}/\sigma_{input}\approx1.041
\]

whereas the free-intercept regression gives:

\[
\sigma_{free}/\sigma_{input}\approx1.127
\]

with a negative intercept.

Therefore the statement "surface tension is 12.7% high" is too coarse.
The data show a finite-radius/intercept structure: the per-radius values are
only ~2-6% high and decrease with R.

The predeclared free-intercept gate still honestly FAILS and should remain a
FAIL, but the next sigma investigation should distinguish:

- slope/intercept coupling;
- finite-radius correction;
- pressure estimator;
- radius definition.

The field named \`sigma_extrapolated_large_R\` remains misleading: its value is
negative and is not a physically meaningful large-R sigma limit. Rename or
remove it in the next harness.

Do not retune \(A=(9/4)\omega\sigma\).

---

# 11. Asymmetric-wall case — global conservation remains closed

Pass-5 reproduces the important conservation result:

- max red excursion ~2.75e-13;
- max blue excursion ~2.74e-13;
- late rates ~2.5e-13/step.

The historical multi-percent global mass source remains eliminated.

The case still fails a wall-band redistribution gate (~-6.83%), but the artifact
explicitly refuses to attribute that change to wall mass transfer without a
stationary reference.

That attribution discipline is correct.

This case should not be used as a blocker for the wetting convention itself.

---

# 12. Durable science documents — incomplete cleanup

Several science documents are now correct:

- \`PAPER_FORMULATION.md\` states +grad(g);
- \`CURRENT_VS_LECLAIRE_MAP.md\` has the corrected non-shell-major ordering;
- \`REFERENCE_MANIFEST.md\` now retracts the false "local search" R5 claim.

But current checkout still contains stale contradictory material:

- \`results/leclaire_cg/PROVENANCE.md\` still says R5 came from local search;
- \`MECHANICAL_SIGMA_DERIVATION.md\` still headlines the Pass-4 0.768 result;
- Pass-5 machine-readable artifacts state -grad(g);
- some render manifests identify themselves as pass-04.

This confirms the need for the planned science-consolidation phase, but the
Pass-5-specific contradictions should be corrected before declaring wetting
closure.

---

# 13. What is accepted and should not be reopened

Preserve:

1. R1 D3Q19/MRT transcription;
2. corrected Eq.(4) \(u\cdot\nabla\rho\) term;
3. X_W one-dimensional gradient;
4. harmonic viscosity interpolation;
5. explicit beta recoloring;
6. unrelaxed perturbation ordering;
7. \(A=(9/4)\omega\sigma\);
8. +grad(g) canonical R1 wall-normal implementation;
9. liquid-side contact-angle measurement formula;
10. quantitative sessile-drop contact-angle result;
11. transverse slit-Pc geometry and Pass-5 Pc result;
12. f64 global conservation closure;
13. Pass-5 freeze discipline;
14. tracked raw artifact pipeline;
15. mechanical-sigma diagnostic design, subject to documentation cleanup.

---

# 14. Required next correction

Do not create another broad validation round.

Create a narrow **Jurin + provenance closure** stage.

## J1 — fix Jurin physics

- make the reservoir and capillary liquid topologically connected;
- ensure the capillary walls are immersed below the reservoir free surface or
  use an equivalent lower liquid connection;
- derive the closed-system volume/Jurin prediction for that exact geometry;
- precheck reachability using the actual connected geometry;
- retain initial/intermediate/final field renderings;
- rerun only after geometry/theory are consistent.

## J2 — fix current evidence metadata at source

Before freezing:
- replace every Pass-5 \(-\nabla g\) string with +grad(g);
- correct \`wall_normal_sign\`;
- correct Pass-5 stage ID;
- correct pass-05 paths/header;
- set render script version to pass-05/new stage;
- update operator docstring.

## J3 — update science documents

- update \`MECHANICAL_SIGMA_DERIVATION.md\` with Pass-5 result;
- correct stale R5 text in \`PROVENANCE.md\`;
- ensure current summary/report/atlas all state the same convention.

## J4 — freeze and rerun

Because the machine-readable harness changes and Jurin changes:
- make a new frozen source SHA;
- rerun the full matrix once;
- generate a new immutable pass;
- fresh independent review.

---

# External status

~~~text
freeze discipline                         PASS
raw NPZ retention                         PASS
R1 +grad(g) runtime implementation        PASS
independent convention tests              PASS

sessile contact angle                     PASS
slit Pc geometry                          PASS
slit Pc sign/magnitude                    PASS

Jurin theoretical topology                FAIL
Jurin current FAIL_SOLVER classification  WITHDRAWN
Jurin case                                INVALID_CONFIGURATION

mechanical sigma                          STRONG / ~1.000, doc cleanup needed
Laplace free-intercept gate               FAIL / unresolved
f64 conservation                          PASS

Pass-5 machine-readable convention        FAIL (stale -grad text)
Pass-5 stage/provenance labels            FAIL
science-document consistency              INCOMPLETE

NumPy/f64 wetting-reference closure        NOT YET
overall                                    CHANGES_REQUESTED
~~~
