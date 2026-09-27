# External Scientific Review — BI-CG-LECLAIRE-IMPLEMENTATION-001

## Binding

- Product branch: \`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001\`
- Exact base: \`6c30260dfe0c8b61ea9609e6bffa5c487312cf06\`
- Reviewed candidate: \`738e76f5d6bd3375c9c7ec7c2403c2a8e4e8eed9\`
- Production solver \`lbm_solver_cg3d.py\`: unchanged from base
- Review type: external scientific/code review, independent of executor summary

## Decision

**CHANGES_REQUESTED**

The branch isolation, source-manifest structure, table transcription discipline,
operator split, explicit beta recolouring, Eq. (18) correction, and commit
provenance are all useful progress.

However, the candidate is not yet a faithful executable reference for
Leclaire et al. 2017. One load-bearing Eq. (4) term is implemented incorrectly,
the wall-gradient treatment is not the one used by R1, the advertised Akai
variant is incomplete, and several canonical tests do not test the physical
claim named by the test.

Do not launch a fresh reviewer yet. First perform one bounded executor correction
round addressing the blockers below, then freeze a new candidate and launch the
fresh reviewer.

---

## B1 — HARD BLOCKER: R1 Eq. (4) is implemented incorrectly

R1 Eq. (4) contains

\[
\nu\left[\psi_i(\mathbf u\cdot\nabla\rho)
+\xi_i(\mathbf G:\mathbf c_i\mathbf c_i)\right],
\]

with

\[
\mathbf G=\mathbf u\otimes\nabla\rho+
(\mathbf u\otimes\nabla\rho)^T.
\]

The current implementation in
\`experimental/leclaire_cg/operators.py::equilibrium\` computes:

\`\`\`python
cu = c_i · u
cd = c_i · grad_rho

nu * (PSI_I * cd + XI_I * 2 * cu * cd)
\`\`\`

The first term is wrong.

It implements

\[
\psi_i(\mathbf c_i\cdot\nabla\rho)
\]

instead of

\[
\psi_i(\mathbf u\cdot\nabla\rho).
\]

This is not a notation issue and is not confined to a high-density-ratio
extension. It changes the equilibrium whenever both velocity and density
gradient are non-zero.

### Why the existing 42/42 checks miss it

The equilibrium check uses \(u=0\) and \(\nabla\rho=0\), where both the correct
and incorrect formulas collapse to the same value.

A paper-fidelity gate must include non-zero randomized \(u\) and
\(\nabla\rho\), and verify the moment identities corresponding to R1 Appendix
A1-A4 / Eq. (4), not only the zero state.

### Required correction

Compute once per node:

\[
u\_dot\_grad\rho=\mathbf u\cdot\nabla\rho,
\]

and use that scalar for every population:

\`\`\`python
ud = einsum("...a,...a->...", u, grad_rho)
PSI_I * ud[..., None]
\`\`\`

Retain the second term as

\[
2\xi_i(\mathbf c_i\cdot\mathbf u)
(\mathbf c_i\cdot\nabla\rho).
\]

After the fix, add direct invariant tests at non-zero \(u,\nabla\rho\).

This blocker invalidates interpretation of the existing moving-interface,
wall, and imbibition results until they are rerun.

---

## B2 — HARD BLOCKER: L17_CORE wall-adjacent gradient is not R1's numerical scheme

The candidate uses a fluid-neighbour-only D3Q19 gradient plus an invented scalar
renormalisation:

\`\`\`python
gradient_isotropic(field, fluid, renormalize=True)
\`\`\`

The code itself records that the renormalisation is not stated by R1.

R1's numerical setup explicitly distinguishes bulk and wall-adjacent sites:

- bulk: 3D fourth-order isotropic gradients;
- \(X_W\): standard one-dimensional forward / backward / centred finite
  differences.

Therefore a scalar-renormalised truncated D3Q19 stencil at \(X_W\) is not a
paper-faithful implementation.

It is also not generally equivalent: deleting solid-neighbour directions
changes a tensor stencil anisotropically; multiplying the remaining stencil by
one scalar cannot in general reconstruct all Cartesian derivative components.

### Required correction

Implement an explicit R1 wall-gradient path for \(X_W\):

- bulk sites: the sourced isotropic operator;
- wall-adjacent sites: the paper's forward/backward/centred Cartesian
  finite-difference rule according to available fluid neighbours.

Use the same distinction consistently for both the colour gradient and the
density gradient where R1 specifies it.

Do not call the current renormalised truncated-stencil mode \`L17_CORE\`.
It may be retained only as a separately labelled experimental variant.

---

## B3 — HARD BLOCKER: the Akai 2018 switch is only a partial implementation

\`FOLLOWUP_OPTIMIZATION_MAP.md\` states:

> Implemented now? YES (switch)

for R3 / Akai wetting.

But \`operators.wetting_akai(...)\` implements only the orientation-rotation
part. Its \`solid_extrap\` argument is unused.

R3's method requires, before the normal correction:

1. identify boundary-fluid and boundary-solid classes;
2. extrapolate the colour function onto \(C_{SB}\) from neighbouring
   \(C_{FB}\) nodes (R3 Eq. 2);
3. compute the interface normal from that extrapolated field (Eq. 3);
4. apply the closed-form contact-angle rotation (Eq. 4).

The current switch starts with the same already-computed \`F\` as L17_CORE and
therefore does not implement the R3 boundary-field construction.

### Required correction

Either:

- implement R3 Eqs. (2)-(4) completely, including the boundary-site colour
  extrapolation and recomputed gradient; or
- relabel the switch explicitly as a partial rotation experiment and mark R3 as
  \`NOT_IMPLEMENTED\`.

No scientific A/B claim between Leclaire and Akai is allowed before this is
resolved.

---

## B4 — VALIDATION BLOCKER: test 08 is not a capillary-imbibition test

\`test_08_imbibition\` runs with:

\`\`\`python
wetting="none"
\`\`\`

and no imposed pressure difference.

The z direction is still periodic under the generic streaming implementation,
so the initial liquid section creates a periodic two-interface topology. There
is no wetting boundary condition and no liquid reservoir / regularized inlet
providing the physical configuration used by R1's Washburn validation.

Requiring the front to advance by >2 lu therefore does not test spontaneous
wetting-driven imbibition. The observed -1 lu retreat must not be interpreted as
a negative result for the Leclaire wetting model.

### Required correction

Choose one:

1. implement the R1-compatible reservoir/open-boundary machinery needed for a
   genuine Washburn test; or
2. replace this item with a valid closed-system capillary test whose driving
   mechanism and analytic expectation are explicitly derived.

Until then test 08 is \`INCONCLUSIVE / INVALID_TEST\`, not a solver FAIL.

---

## B5 — VALIDATION BLOCKER: test 07 asks for capillary pressure while disabling wetting

\`test_07_slit_pc\` also uses:

\`\`\`python
wetting="none"
\`\`\`

but compares against

\[
P_c = \frac{2\sigma}{h},
\]

which corresponds to \(\cos\theta=1\), not neutral/no imposed wetting.

The observed approximately zero pressure difference is therefore not evidence
against the solver. It is consistent with a flat/neutral interface.

### Required correction

Run the slit with an explicitly prescribed, independently measured contact
angle and compare against

\[
P_c = \frac{2\sigma\cos\theta}{h}
\]

for the actual geometry/convention.

If the wetting angle is not yet validated, this test must wait rather than
supply a physics FAIL.

---

## B6 — VALIDATION BLOCKER: test 09 currently passes despite ~7% global mass creation

The asymmetric-killer result is labelled PASS because only two gates are used:

- final wall-band red-mass change <2%;
- one connected component.

But the same committed trace shows large global component growth over 1500
steps:

- red: approximately +92.5;
- blue: approximately +125.3;
- total: approximately +217.8, about 7% of the initial total mass.

That is incompatible with using this case as evidence of a clean wall treatment.

It is especially important because B1 provides a plausible mechanism for a
local collision mass source where \(u\cdot\nabla\rho\neq0\).

### Geometry claim also needs correction

\`asymmetric_ledge()\` says both x faces are closed, but the implementation
closes only one x face (left OR right). The other global x face remains linked
through the periodic \`np.roll\` streaming topology.

Thus the note

> "closed on all four lateral faces"

is false for the committed geometry.

### Required correction

After B1/B2 are fixed:

- make the intended non-cancelling topology explicit and verify it in code;
- gate global total and component mass;
- track the **maximum time-history excursion**, not only initial-to-final
  wall-band change;
- retain wall-band flux/contact-line/topology metrics;
- reject a case with multi-percent global mass creation even if its final
  wall-band value happens to return near the initial value.

The current test-09 PASS is withdrawn.

---

## B7 — VALIDATION BLOCKER: test 06 is not a controlled dynamic-isotropy comparison

The two capillary-wave arms use the same array \`(32,16,16)\` but set:

- wave along x: wavelength 32 lu;
- wave along y: wavelength 16 lu.

Those are different physical/numerical wavelengths, so their response cannot
be interpreted as a pure lattice-direction comparison.

The reported metric also averages over the tangential directions and compares
terminal \`max|psi|\`, rather than measuring interface-wave amplitude, phase or
frequency.

### Required correction

Use equal physical/lattice wavelength in the two rotated cases, e.g. by
rotating the domain dimensions with the wave, and track the interface-height
Fourier mode versus time.

Compare decay/frequency/amplitude for the same \(k\), not the mean phase-field
peak.

The current 0.48% number must not be described as validated dynamic isotropy.

---

## B8 — Laplace evidence is encouraging but the measurement should be hardened

The Eq. (18) correction

\[
A=(9/4)\omega_{\rm eff}\sigma
\]

is correct, and the current Laplace results are consistent with the intended
surface-tension scale.

However:

- the droplet radius used in \(\sigma=\Delta p R/2\) is the initial nominal
  radius, not a measured equilibrium radius;
- the interface-width helper fits a single tanh to a centreline that crosses a
  spherical droplet twice, producing radius-dependent widths that are not
  physically meaningful;
- no \(\Delta p\) versus \(1/R\) regression / intercept / \(R^2\) is reported.

Before calling the Laplace calibration "resolved" in publication-quality
language, use a measured equilibrium radius and a multi-radius linear
regression.

This is not the highest-priority blocker; B1/B2 must be fixed first.

---

## B9 — beta sweep must distinguish sharpening from nonphysical overshoot

Test 05 counts every case with \(|\psi|_{\max}>0.95\) as a physical interface,
including:

- beta=1.5: \(|\psi|_{\max}>1\);
- beta=2.0: \(|\psi|_{\max}>1.1\).

A colour/order parameter outside its component-fraction range is an
over-sharpening/positivity warning, not evidence of a healthy diffuse
interface.

### Required correction

- keep the beta range justified by the source/model stability envelope;
- report positivity / component-population violations;
- require \(|\psi|\le1+\epsilon\) (or explicitly justify another admissible
  bound) before counting a run as physically valid;
- separate "monotone width response" from "valid parameter range".

---

## B10 — the NumPy/f64 implementation is a useful reference, not yet the production candidate

The isolated NumPy/f64 implementation is acceptable as a first executable
scientific reference. It is useful precisely because it removes Taichi/f32
implementation noise while checking the equations.

But the previous project conservation defect was precision/backend-specific.
Therefore:

> "L17 recolouring needs no conservation correction"

is currently supported only for this f64 reference implementation / tested
states.

It must not be generalized to the eventual Taichi/f32 GPU implementation
without repeating the local/global conservation audit after the port.

No Taichi port is required in the immediate correction round; first make the
reference implementation scientifically correct.

---

## B11 — literature-acquisition contract was not followed

The control contract required the already-working ZCode **科研通** workflow by
DOI.

\`REFERENCE_MANIFEST.md\` explicitly states that the executor did not use
科研通 and substituted publisher/institutional sources.

The acquired sources appear legitimate and DOI-bound, so this does not by
itself invalidate the scientific content, but it is a contract/provenance
violation.

For the correction round:

- use 科研通 as requested when re-obtaining/checking the mandatory DOI set; or
- if the ZCode environment genuinely cannot access the existing workflow,
  stop and report that as a tooling failure instead of silently substituting a
  route.

Do not prescribe a local storage path; the user explicitly did not require one.

---

## B12 — R5 gradient-source claim needs one more source-level check

The current formulation claims that R5's 3D \((S,I)=(2,4)\) stencil contains
additional body-diagonal / higher-shell coefficients, then argues that
restricting it to D3Q19 yields exactly \(3W_i\).

Because the R5 table was acknowledged to be difficult to parse and the argument
mixes "full R5 stencil" with "D3Q19 restriction", this should be verified
directly against the rendered source table and its stated compact-stencil
construction.

Do not rely on text extraction alone. Record the exact row/column mapping used.
If ambiguity remains, mark the coefficient mapping \`UNRESOLVED\`; the bulk
D3Q19 \(3W_i\) isotropy derivation can remain as an independent implementation
choice.

---

## What is already good / should be preserved

Do not discard the whole branch. Preserve:

1. exact base / branch isolation;
2. production solver unchanged;
3. formulation -> implementation -> validation commit history;
4. explicit correction commits instead of history rewriting;
5. D3Q19 Table-IV / Table-XI consistency checks;
6. explicit \(beta\) recolouring structure;
7. paper perturbation as a separate, unrelaxed operator;
8. Eq. (18) factor \(9/4\);
9. Leclaire secant wetting as an isolated baseline concept;
10. three-pass wall-image smoothing;
11. explicit separation of follow-up variants and conservation overlay;
12. failure reporting instead of retuning gates to force PASS.

DeepSeek also correctly narrowed its own recommendation to
\`CHANGES_REQUESTED\`; that self-critique is useful. The external review simply
finds that the required correction scope is broader and more upstream than the
executor report states.

---

## Required next executor round

Order matters:

### C1 — formulation/code fidelity
1. Fix Eq. (4) \(u\cdot\nabla\rho\) term.
2. Add non-zero-\(u\), non-zero-\(\nabla\rho\) moment-identity tests.
3. Implement the R1 \(X_W\) gradient rule; remove the scalar-renormalized
   truncated stencil from \`L17_CORE\`.
4. Resolve R5 table mapping.

### C2 — wetting variant fidelity
5. Implement complete R3 Eq. (2)-(4) or mark Akai unimplemented.
6. Build a robust contact-angle instrument from interface normals / contour
   fitting; verify phase/sign convention.

### C3 — validation redesign
7. Redesign test 07 with prescribed wetting.
8. Redesign/defer test 08 as a real imbibition case.
9. Fix test-09 topology and gate global/time-resolved mass.
10. Replace test-06 with equal-wavelength Fourier-mode dynamic isotropy.
11. Harden Laplace radius/regression.
12. Add positivity gates to beta sweep.

### C4 — rerun
13. Rerun unit checks.
14. Rerun the corrected canonical matrix from one frozen candidate.
15. Update report/provenance without deleting prior-pass history.
16. Prepare a fresh-review request.

Then STOP and launch a **fresh DeepSeek reviewer** in a separate session.

There is currently no committed fresh-review artifact for this task, so this
candidate is not eligible for external PASS/promotion.

## External status

\`\`\`text
branch isolation                       PASS
paper/source structure                 PARTIAL PASS
L17 core equation fidelity             FAIL — Eq.(4) blocker
wall-gradient fidelity                 FAIL
Leclaire wetting implementation        PARTIAL / not yet quantitatively validated
Akai follow-up fidelity                FAIL / incomplete
bulk static evidence                   promising but must rerun after B1
canonical validation matrix            INVALID AS A 7/3 PASS-FAIL SUMMARY
fresh reviewer                         NOT RUN
production promotion                   NOT AUTHORIZED
\`\`\`
