# External Scientific Review R2 — BI-CG-LECLAIRE-IMPLEMENTATION-001

## Binding

- Product branch: \`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001\`
- Exact base: \`6c30260dfe0c8b61ea9609e6bffa5c487312cf06\`
- Frozen source / validation candidate: \`5a3929fa1cefb7359893d6c19ed0ec8a7c80a91d\`
- Evidence package tip: \`a12c14f553c5a03a815dbfc96d5aa09a6f33083e\`
- Fresh reviewer package commit on control: \`55a883ed2338ff3ff3c1622fb52bbbd327a359d0\`
- Fresh reviewer decision: \`CHANGES_REQUESTED\`

## External decision

**CHANGES_REQUESTED**

The correction round made substantial progress. The previously identified
load-bearing formulation defects B1/B2 are fixed, the Akai path is now a real
R3-style implementation rather than only a rotation formula, and the previous
~7% moving/wall-state mass creation disappears after the Eq.(4) correction.

The branch is now useful as a serious f64 executable reference. It is not yet
closed as a validated Leclaire/Latt wetting reference because two canonical
tests remain geometrically incapable of exercising the phenomenon they claim to
test, the contact-angle phase/normal convention is not frozen, and the durable
documentation contradicts the pass-3 evidence in several places.

Do not port this branch to Taichi/f32 yet. Close the remaining reference-model
ambiguities first.

---

## 1. Fresh-review independence and reproduction — ACCEPTED

The fresh reviewer bound to the requested candidate/evidence pair and reports:

- 59/59 unit checks independently rerun;
- full ten-test canonical driver independently rerun;
- all ten verdicts reproduced;
- key numerical metrics reproduced;
- R1/R3 equations checked against the staged source PDFs;
- product candidate not modified.

This is sufficient to treat the fresh review as independent evidence rather
than an executor restatement.

The fresh review itself remains \`CHANGES_REQUESTED\`, which is the correct
decision.

---

## 2. B1 Eq.(4) correction — ACCEPTED and causally important

The corrected equilibrium now implements

\[
\nu\,\psi_i(\mathbf u\cdot\nabla\rho)
\]

with a node-scalar \(\mathbf u\cdot\nabla\rho\), rather than the incorrect

\[
\nu\,\psi_i(\mathbf c_i\cdot\nabla\rho).
\]

The non-zero-\(u\), non-zero-\(\nabla\rho\) moment checks close the gap that the
old zero-state unit tests could not detect.

### Strong causal evidence

Before B1, the asymmetric wall case created about 7% total mass over the run.
After B1/B2, the independently rerun test-09 reports component-mass excursions
at approximately \(2.7\times10^{-13}\) and late-window rates at f64 roundoff.

The most economical interpretation is:

\`\`\`text
wrong Eq.(4) term
    -> m0_eq != rho when u.grad(rho) != 0
    -> collision source in moving/interface-wall states
    -> large apparent component/total mass creation

correct Eq.(4)
    -> equilibrium moment identity restored
    -> global mass creation disappears
\`\`\`

This is a valuable diagnosis and should remain explicit in the algorithm
evolution record.

Do not generalize the resulting conservation claim beyond the current NumPy/f64
reference. A future Taichi/f32 port still requires its own arithmetic audit.

---

## 3. B2 X_W wall-gradient correction — ACCEPTED

The source now separates:

- bulk sites: isotropic D3Q19 gradient;
- wall-adjacent \(X_W\): one-dimensional Cartesian centered / forward /
  backward differences according to available fluid neighbours.

This matches the numerical setup stated in R1 and removes the previous
scalar-renormalized truncated stencil from \`L17_CORE\`.

The old mode is retained only as a labelled experimental variant, which is the
right provenance boundary.

---

## 4. B3 Akai path — implementation accepted, validation still pending

The source now contains the R3 sequence:

1. classify boundary-fluid / boundary-solid sites;
2. extrapolate the colour function to boundary-solid sites;
3. recompute the interface normal from the extrapolated field;
4. apply the closed-form contact-angle rotation.

Therefore the previous B3 implementation blocker is closed.

However, no committed validation arm exercises \`wetting="akai"\`. The fresh
reviewer only performed a local probe.

Status:

\`\`\`text
Akai source fidelity       ACCEPTED
Akai numerical validation  NOT YET DONE
Akai vs Leclaire A/B       NOT YET SUPPORTED
\`\`\`

This is nonblocking for closing \`L17_CORE\`, but must be completed before making
a claim about the later wetting improvement.

---

## 5. BLOCKER R1 — test 07 geometry still cannot test capillary pressure

The correction changed test 07 from neutral wetting to a prescribed contact
angle, but the geometry remains wrong.

The two solid plates are normal to z, while the initialized fluid-fluid
interface is also an xy plane at fixed z. The interface is therefore parallel
to the plates and does not form a contact line with them.

The fresh reviewer independently ran theta=60 and theta=120 and obtained the
same flat meniscus and essentially zero pressure difference in both cases.

Thus:

\[
\Delta p \approx 0
\]

is imposed by the geometry; the test never exercises

\[
P_c=\frac{2\sigma\cos\theta}{h}.
\]

### Required redesign

For a slit capillary-pressure benchmark, orient the plates across one transverse
coordinate, e.g. y, and let the meniscus advance/curve along x or z so that the
fluid-fluid interface intersects both walls.

Only after the contact-angle convention is frozen should this test compare
measured \(\Delta p\) with \(2\sigma\cos\theta/h\).

Current test-07 verdict is **INVALID TEST**, not a physical solver FAIL.

---

## 6. BLOCKER R1 — test 08 Jurin configuration is unreachable

The new closed-system Jurin geometry contains a reservoir below a slit, but the
initial meniscus sits too far below the slit mouth.

The fresh reviewer independently evaluates:

- expected Jurin rise: about 5.95 lu;
- lift needed to reach the slit mouth: about 8 lu;
- available capillary pressure: \(2.5\times10^{-3}\);
- hydrostatic cost to reach the slit: \(3.36\times10^{-3}\).

Therefore the equilibrium surface remains below the capillary entrance. The
committed trace confirms the slit level is never measurable.

### Required redesign

Use a geometry/initial condition in which the meniscus is already inside the
capillary, or choose neck/gravity/contact-angle parameters such that the
expected equilibrium level necessarily lies inside the measurement region.

Prefer reproducing the structure of R1's Jurin validation more closely:
measure the inside-versus-outside differential height after capillary
equilibration, rather than asking a reservoir surface to first jump an
unreachable entrance.

Current test-08 is **INCONCLUSIVE / INVALID CONFIGURATION** and cannot be counted
toward wetting validation.

---

## 7. BLOCKER R2 — contact-angle wall-normal / phase convention must be frozen

This is the most informative result in the fresh review.

The committed test uses the default \`wetting_sign=+1\` while declaring that
contact angle is measured through the \(\psi>0\) red phase.

The fresh reviewer ran the missing sign experiment:

\`\`\`text
default sign +1:
60  -> 114.75 deg
90  ->  82.84 deg
120 ->  47.43 deg

sign -1:
60  ->  51.12 deg
90  ->  82.84 deg
120 -> 112.78 deg
\`\`\`

Under sign -1 the absolute error is only about 7–9 degrees for all three
angles, inside the intended 15-degree accuracy gate. The default sign produces
approximately the complementary-angle behavior for 60/120 degrees.

This strongly suggests that the wetting solver itself is substantially more
correct than the pass-3 headline implies; the unresolved item is the mapping
between:

- binary-solid image convention;
- direction of \(\mathbf n_w\);
- colour-gradient direction (blue -> red);
- which phase the reported contact angle is measured through.

### Required correction

Do not keep an arbitrary sign switch inside a mode called \`L17_CORE\`.

Choose and document one canonical convention, then derive the required sign from
the definitions. For example:

\`\`\`text
g = 1 in solid / 0 in fluid
n_w = ? (define: solid->fluid OR fluid->solid)
F = grad[(rho_r-rho_b)/rho] = blue->red
theta_c = measured through ? phase
\`\`\`

Then make the implementation and measurement use that convention consistently.

The paper validates the wetting treatment with Jurin and Washburn-type
capillary configurations, so the sign convention should also be checked against
one of those source-defined geometries, not only a sessile droplet.

After the convention is frozen, rerun the contact-angle sweep. The current
circle-fit instrument may still need more contour resolution, but the gross
60/120 discrepancy is no longer evidence of a failed wetting closure.

---

## 8. BLOCKER R3 — durable provenance is internally contradictory

The fresh reviewer identified multiple stale statements, and spot checks confirm
them.

Examples include:

- \`PAPER_FORMULATION.md\` §4.2 marks the R5 mapping \`UNRESOLVED\`, while §11
  still marks it \`CLOSED\`;
- \`REFERENCE_MANIFEST.md\` still says 科研通 does not exist and R5 came from
  local search, contradicting its corrected R5 acquisition record;
- \`CURRENT_VS_LECLAIRE_MAP.md\` retains the old shell-major ordering statement
  and an obsolete "R5 could not be obtained" caveat;
- \`EXECUTION_REPORT.md\` still presents pass-2 headline claims (42/42, 7 PASS /
  3 FAIL, "Laplace calibration RESOLVED") before the later pass-3 section that
  contradicts them.

For a research-reference branch, this is blocking because these documents are
part of the scientific artifact, not disposable narration.

### Required correction

Do not delete history, but make the current documents internally consistent:

- old claims should be explicitly labelled \`SUPERSEDED PASS-1/PASS-2\`;
- current headline must be pass 3 only;
- R5 mapping must have one current status;
- acquisition route must have one current provenance statement;
- the corrected non-shell-major Table-IV ordering must appear everywhere.

After the clean-up, a reader should be able to read only the latest version of
each file and recover the current truth without reconstructing Git history.

---

## 9. Laplace result — honest FAIL; do not call resolved

The pass-3 redesign is materially better:

- equilibrium radius is measured from the final phase field;
- \(\Delta p\) is regressed against \(2/R\);
- intercept and \(R^2\) are reported.

The regression gives approximately:

\[
\sigma_{\rm fit}/\sigma_{\rm input}=1.135,
\qquad R^2\approx0.99997.
\]

This is an excellent linear relation but misses the predeclared 10% calibration
band.

Therefore the current scientific status is:

\`\`\`text
Laplace-law linearity          STRONG
surface-tension calibration    FAIL / unresolved +13.5%
Eq.(18) 9/4 transcription      CORRECT
\`\`\`

Do not restore the old "RESOLVED" wording.

Before changing any coefficient, first determine whether the offset comes from
finite-radius/interface-location effects, the unresolved R5 mapping, the
pressure estimator, or another discretization detail. A larger-radius /
multi-resolution study is preferable to retuning \(A\).

---

## 10. Test 09 — mass-source blocker closed; wall-band behavior remains diagnostic

The corrected asymmetric geometry is actually closed against periodic wrap, and
the large global mass drift has disappeared.

That closes the original catastrophic defect.

The case still fails its wall-band gate by about -6.8%. This is not by itself
proof of nonphysical wall transfer because the initial interface can physically
redistribute while satisfying global conservation.

To turn this into a wetting-artifact test, define a stationary/no-driving
reference state or subtract a physically expected redistribution. Track a
contact-line observable as originally promised.

Current interpretation:

\`\`\`text
global mass integrity       PASS
closed topology             PASS
wall-band no-transfer gate  FAIL
cause of wall-band change   UNRESOLVED
\`\`\`

Do not call the 6.8% change a wall-mass-transfer defect without an attribution
test.

---

## 11. Test 06 — acceptable axis-isotropy regression, limited scope

The corrected test compares equal wavelengths and a Fourier-mode interface
amplitude. This fixes the original B7 error.

Because the two cases are exact x/y transposes of a cubic lattice, the
near-machine-zero difference is mostly an axis-symmetry regression.

It is still useful as a regression but does not establish general rotational
isotropy. A diagonal-wave or rotated-interface case would provide stronger
evidence later.

No blocker for the immediate round.

---

## 12. What is now accepted

Preserve these results:

1. isolated branch / production solver unchanged;
2. Leclaire D3Q19 table transcription and MRT structure;
3. corrected Eq.(4) equilibrium and nonzero-gradient moment checks;
4. R1 X_W wall-gradient path;
5. explicit beta recoloring;
6. separate unrelaxed perturbation operator with \(A=(9/4)\omega\sigma\);
7. three-pass wall-normal smoothing;
8. full Leclaire secant wetting implementation;
9. full Akai Eq.(2)-(4) implementation as a separate default-off variant;
10. f64 reference conservation closure after B1;
11. beta positivity/validity separation;
12. measured-radius Laplace regression instrumentation;
13. equal-wavelength Fourier axis-isotropy regression;
14. independent fresh-review reproducibility.

---

## 13. Required final reference-model correction round

Keep this round small. No new physics family.

### D1 — freeze wetting convention
1. Define the canonical \(g\), \(n_w\), \(F\), and phase/contact-angle convention.
2. Choose the corresponding wall-normal sign in \`L17_CORE\`; remove the
   arbitrary default ambiguity.
3. Rerun contact-angle 60/90/120 with enough resolution/contour points to pass
   or honestly fail the existing fit-quality gate.

### D2 — replace invalid capillary tests
4. Rebuild test 07 with walls transverse to the meniscus so a real contact line
   exists.
5. Rebuild test 08 so the expected Jurin equilibrium lies inside the capillary
   measurement region, preferably following R1's inside/outside height logic.

### D3 — clean the durable scientific record
6. Remove/annotate stale pass-1/pass-2 statements.
7. Make R5 status, 科研通 provenance and Table-IV ordering internally consistent.
8. Make pass-3 (or the new pass-4) the only current headline.

### D4 — rerun
9. Rerun unit checks.
10. Rerun only the affected wetting/capillary tests plus the full matrix once
    from the frozen candidate.
11. Preserve the Laplace +13.5% result as unresolved unless new evidence changes
    it; do not retune \(A\) to make the gate pass.
12. Prepare another fresh-review package.

Then STOP.

---

## External status

\`\`\`text
branch / isolation                       PASS
fresh-review independence                PASS
R1 equation fidelity                     PASS
B1 Eq.(4) correction                     PASS
B2 X_W gradient correction               PASS
B3 Akai source implementation            PASS (unvalidated numerically)

catastrophic wall-state mass source      CLOSED
f64 reference global conservation        PASS in tested corrected cases

contact-angle convention                 UNRESOLVED — likely sign/convention issue
test 07 capillary-pressure geometry       INVALID
test 08 Jurin geometry                    INVALID / unreachable
test 09 wall-band attribution             UNRESOLVED

Laplace-law linearity                     PASS
sigma calibration                         FAIL (+13.5%, unresolved)

durable provenance consistency            FAIL
production promotion                      NOT AUTHORIZED
Taichi/f32 port                            NOT YET AUTHORIZED

overall                                    CHANGES_REQUESTED
\`\`\`
