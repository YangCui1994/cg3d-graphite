# REVIEW — BI-CG-LECLAIRE-IMPLEMENTATION-001

## Binding

- **Task ID:** `BI-CG-LECLAIRE-IMPLEMENTATION-001`
- **Product branch:** `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`
- **Base:** `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`
- **Source / validation candidate:** `5a3929fa1cefb7359893d6c19ed0ec8a7c80a91d`
- **Evidence / package tip:** `a12c14f553c5a03a815dbfc96d5aa09a6f33083e`
- **External review under correction:** `.agent/evidence/BI-CG-LECLAIRE-IMPLEMENTATION-001/EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md` (reviewed predecessor `738e76f`)
- **Execution report:** `results/leclaire_cg/EXECUTION_REPORT.md` (+ `PROVENANCE.md`, `summary.json`) — treated as a claim, reproduced below
- **Worktree:** `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-CG-LECLAIRE-IMPLEMENTATION-001`

## Review Mode

`FRESH_SESSION` — independent reviewer. Executor transcript not read, not requested.
The frozen candidate was not modified. All recomputation was done on a byte-identical
copy of the candidate's source staged under `.agent_runtime/BI-CG-LECLAIRE-IMPLEMENTATION-001/rerun/`.

## Decision

**CHANGES_REQUESTED**

Ten of the twelve external-review blockers (B1, B2, B3, B6, B7, B8, B9, B10, B11, B12)
are fixed, and I verified the two load-bearing ones (B1, B2) directly against the
published source. **B4 and B5 are not fixed**: the two redesigned tests are provably
incapable of measuring the quantity they are named after, and I reproduced that
failure independently. The evidence package also contains mutually contradictory
provenance statements that an external reviewer would rely on, and the
contact-angle phase convention the review asked to be verified (C2.6) is unresolved
in the evidence — with a decisive, cheap experiment that the candidate never ran.

## Coverage

Inspected:

- all five contract documents (reviewer contract, external review, reference set,
  Palabos code trace, `AGENTS.md`);
- the complete candidate diff `base..tip` (30 files, +7011 lines) and every commit
  message in the chain `245d6e6 … a12c14f`;
- `experimental/leclaire_cg/{lattice,operators,solver,geometry}.py` in full;
- `tests/leclaire_cg/{test_lattice_tables,run_canonical}.py` in full;
- `docs/research/leclaire_cg/*.md` (all five) and `results/leclaire_cg/*.md`;
- all ten committed per-test JSONs and `summary.json`;
- the five staged reference PDFs (SHA256 re-hashed) and the R1/R3 text layers.

Recomputed (not read):

- `tests/leclaire_cg/test_lattice_tables.py` rerun from the frozen source — 59/59;
- `tests/leclaire_cg/run_canonical.py` **rerun in full** from the frozen source on a
  staged copy, writing to a staging results directory so the candidate tree was never
  written to — all ten verdicts and all compared metrics identical to the committed run;
- the R1 Eq. (4) / (5) / (13) / (14) / (16) / (17) / (18) / (19) / (20) / (30)–(33) /
  (34)–(38) and Table IV / VI / VII / VIII / XI transcriptions against the PDF text;
- the R3 Eqs. (2)–(4) transcription against the Akai PDF text;
- the test-09 geometry closure and asymmetry directly from the mask;
- the test-08 reachability arithmetic and the test-07 meniscus behaviour by running
  both configurations myself;
- a `wetting_sign` sweep of the test-04 configuration (new experiment, see R-5).

Not inspected: the executor transcript (forbidden); the production Taichi solver's
behaviour (out of scope, no GPU work authorised); the R2/R4 PDFs' internals beyond
the statements quoted in the formulation; the contents of the 科研通 web session
(only its local record, see B11).

## Requirement Review

### Contract section A — binding and isolation — **PASS**

| check | result | evidence |
|---|---|---|
| product branch correct | PASS | worktree on `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001` at `a12c14f` |
| base ancestry | PASS | `git merge-base --is-ancestor 6c30260d… HEAD` → true; 17 commits `base..tip` |
| `lbm_solver_cg3d.py` unchanged | PASS | blob `1b7db4ac27448b5b982cead1ea86e719c59e6684` identical at base, candidate and tip; worktree sha256 `98c5331d1a958919eff98ff7b770cfc4e7f65c01f5cb31483aadd367cfd7dd8b` |
| production defaults / gates unchanged | PASS | `git diff --name-status base..tip` = 29 × `A` + `.gitignore` (1 × `M`, +3 lines, adds only the `_refs/` ignore). No production file touched |
| isolated from the production solver line | PASS | `experimental/leclaire_cg/` imports nothing from `lbm_solver_cg3d.py`; geometries are re-implemented because production ones carry `psi_solid` semantics |
| no V3 / graphite / separator / PCS / production porous-media work | PASS | changed-file set is exactly `{.gitignore, docs/research/leclaire_cg/**, experimental/leclaire_cg/**, results/leclaire_cg/**, results/leclaire_cg_run.log, results/unit_checks.log, tests/leclaire_cg/**}` |
| control branch not merged into product | PASS | `agent-dev/bilateral-episode-v0.1` fast-forwarded to `1c4f1a4`; product chain contains no merge commit |

### Contract section B — literature provenance — **PASS with documentation defect (see R-3)**

- The mandatory DOI set is used and each DOI is recorded with its role
  (`REFERENCE_MANIFEST.md`).
- R5 (`10.1007/s10915-013-9772-2`) is an additional paper with a DOI and an explicit
  reason (R1 defers the gradient coefficients to it).
- I re-hashed all five staged PDFs: every SHA256 matches the manifest exactly
  (R1 `435b4fa1…32c3`, R2 `91fc30f1…811c`, R3 `073a3431…efdd`, R4 `17aca930…2962`,
  R5 `f18e3bfd…7968`); R5 is 1,078,397 bytes / 29 pages as claimed.
- The 科研通 route for R5 is corroborated out-of-band, not merely self-reported: the
  skill's own log (`~/.zcode/skills/ablesci-paper-download/SKILL.md`, mtime
  `2026-09-27 09:58:20 +0800`) records the same DOI, the 09:54:56 post, the AI6.2
  upload at ~1,078,397 B and the 10-point deduction, matching the manifest.
- B11's two admissible replies were "use the workflow" or "report the tooling failure".
  The candidate did neither verbatim for R1–R4: it routed them by OA because the
  skill's own precondition forbids 科研通 where an OA copy exists, and it escalated
  that reading to the owner instead of deciding silently. That is a defensible
  documented deviation, not a silent substitution — but it is not the letter of the
  correction, and the file contradicts itself about it (R-3).

### Contract section C — equation-level fidelity — **PASS**

Every element I re-derived from the PDF is faithful. Verified against the rendered
source text (not against the formulation's transcription):

| element | source | source text | candidate |
|---|---|---|---|
| equilibrium Eq. (4) | R1 PDF p.6 | `N^e = ν[ψ_i(u · ∇ρ) + ξ_i(G : c_i ⊗ c_i)] + ρ(φ_i + ϕ_iα + W_i(…))` | `PSI_I*ud[...,None] + XI_I*2*cu*cd` with scalar `ud = u·∇ρ` |
| Eq. (5) | R1 p.6 | `G = (u⊗∇ρ) + (u⊗∇ρ)ᵀ` | `2 (c_i·u)(c_i·∇ρ)` |
| Eq. (13)/(14) | R1 p.6 | harmonic density-weighted `ν`; `ω_eff = 2/(6ν+1)` | `viscosity_harmonic`, `omega_eff` |
| Eq. (16)/(17) | R1 p.6 | `A|F|[W_i(F·c_i)²/|F|² − B_i]`; `F = ∇[(ρ_r−ρ_b)/(ρ_r+ρ_b)]` | `perturbation`, `gradient` |
| Eq. (18) | R1 p.6 | `A = 9/4 ω_eff σ` | `2.25 * omega * sigma` (asserted in the unit checks against both 2.25 and 1.5) |
| Eq. (19)/(20) | R1 p.7 | `(ρ_k/ρ)N_i ± β(ρ_rρ_b/ρ²)cos ϑ_i N_i^e(ρ,0)` | pairwise form over the nine opposite pairs, rest population untouched |
| Eq. (30)–(33) | R1 p.8–9 | `f(v_c) = v_c·n_w − |v_c|cos θ_c`; `v⁰ = n_c`; `v¹ = n_c − λ(n_c+n_w)`; secant; **λ = 1/2, always stop at n = 2** | `secant_contact_angle` with `lam=0.5`, one recurrence step |
| Eq. (34)–(38) | R1 p.9 | D3Q27-weighted 3×3×3 smoothing, `w = 8/27, 2/27, 1/54, 1/216`, **three iterations** | `smooth_solid`, `SMOOTH_W`, `SMOOTH_PASSES=3` |
| X_W gradient rule | R1 p.24, p.26, and §II.E | three separate statements: isotropic "on all lattice sites, except … X_W where a standard 1D forward, backward, and/or centered discrete gradient" (and the random-network variant "first-order forward, first-order backward, and/or second-order centered") | `gradient(..., variant="l17")` |
| Table IV | R1 p.26 | `W` 1/3,1/18,1/36; `φ` 0,1/12,1/24; `ϕ` 1,−1/12,−1/24; `ψ` −5/2,−1/6,1/24; `ξ` 0,1/4,1/8; `B` −2/9,1/54,1/27; and `c₁…c₁₈` in the non-shell-major order | `lattice.py` identical cell by cell |
| Table VI/VII/VIII | R1 p.26–27 | `ζ(D3Q19) = 1/2`; `p = {3,5,7}`; `υ = {9,11,13,14,15}` | identical |
| Appendix A4 | R1 | third moment `= (ρ/3)(u_mδ_no + …)` | asserted at non-zero `u`, `∇ρ` |
| seven-step ordering | R1 p.4 | steps (1)–(7) with the stated site domains | `solver.step()` in the same order, with (1) raising rather than stubbing |

No element was accepted as `MATHEMATICALLY_EQUIVALENT` without its derivation
(`CURRENT_VS_LECLAIRE_MAP.md` §A.1–A.10); the one the review singled out
(perturbation ↔ stress-moment injection) is correctly resolved as `DIFFERENT`.

### Contract section D — baseline / follow-up separation — **PASS**

- `L17_CORE` is identifiable by construction: all defaults are paper-faithful
  (`wetting="leclaire"`, `recolor_form="paper"`, `perturbation_coeff="paper"`,
  `gradient_variant="l17"`, `conservation_overlay=None`, `external_bc=None`), and
  `external_bc` raises instead of falling back.
- Later-paper variants are separately named and default-off: `wetting="akai"` /
  `"akai_rotation_only"`, `recolor_form="min_variant"`, `chi`, `conservation_overlay`.
- No undocumented hybrid default exists; the ablation matrix in
  `FOLLOWUP_OPTIMIZATION_MAP.md` names `L17_CORE`, `L17_PLUS_AKAI`,
  `L17_PLUS_OVERLAY`, `CURRENT_AMPLITUDE_ABLATION` (none of the latter three was run,
  and the map says so).
- The project conservation overlay is an explicit overlay, and test 10's acceptance
  states that the overlay arm is not paper-faithful. The overlay is *not* inherited
  from the production line.

## Validation Review

### Independent rerun — the committed evidence is real

I ran the committed driver, unmodified, from a byte-identical copy of the frozen
candidate source (`md5 e52c13daba74e4990def7fc2605eff2d` for the driver), writing to a
staging directory.

| test | committed | my rerun | key metric agreement |
|---|---|---|---|
| 01 uniform single-phase | PASS | PASS | — |
| 02 planar interface | PASS | PASS | — |
| 03 Laplace droplet | FAIL | FAIL | `sigma_ratio` `1.1353336064475887` identical |
| 04 static contact angle | INCONCLUSIVE | INCONCLUSIVE | measured 114.753171 / 82.843068 / 47.430225° identical |
| 05 width vs β | PASS | PASS | — |
| 06 dynamic isotropy | PASS | PASS | `amplitude_asymmetry` `1.589207e-13` identical |
| 07 slit capillary pressure | FAIL | FAIL | — |
| 08 simple imbibition | INCONCLUSIVE | INCONCLUSIVE | `rise = nan` identical |
| 09 asymmetric killer | FAIL | FAIL | wall-band `−6.830798e-02`, excursions `2.749154e-13` identical |
| 10 conservation audit | PASS | PASS | — |

All ten verdicts and every compared metric reproduce exactly. The unit-check log also
reproduces line for line (59/59). `EXECUTION_REPORT.md` / `summary.json` are therefore
**verified, not taken on trust** — with the one exception noted as R-3 (the report's
headline numbers are its own superseded pass-2 claims).

### Per-test assessment against the external review

| test | review status | assessment |
|---|---|---|
| 01, 02 | PASS | stationary to machine precision, interface survives (`amplitude_ratio` gate added — this is a genuine improvement over position-only) |
| 03 | FAIL (honest) | B8 fixed: measured equilibrium radius + multi-radius regression with intercept and R²=0.99997, and the run is reported FAIL at `sigma_ratio = 1.135`. I recomputed the least-squares slope by hand and reproduced it. The σ offset is unresolved, not hidden |
| 04 | INCONCLUSIVE | instrument replaced (circle fit, unit-validated on synthetic arcs), but the fit-quality gate fails on 2 of 3 angles and the phase convention is unresolved (R-5) |
| 05 | PASS | B9 fixed: positivity separated from monotonicity; β = 1.5, 2.0 excluded with recorded negative component minima (`red_min` −7.7e−3 / −5.7e−2); monotone over the three positives |
| 06 | PASS | B7 fixed: equal lattice wavelength (16 = 16), Fourier-mode observable. Caveat R-6 |
| 07 | FAIL — **invalid test** | B5 **not** fixed: R-1 below |
| 08 | INCONCLUSIVE | B4 **not** fixed: R-1 below |
| 09 | FAIL (honest) | B6 fixed: geometry verified closed in code, global/component mass gated on the maximum time-history excursion and the late-window rate; the ~7 % mass creation is gone (excursions now 2.7e−13). The withdrawn PASS is now a FAIL on the wall-band gate. Minor overclaim R-7 |
| 10 | PASS | B10 fixed: `scope_limitation` in the test JSON limits the conservation claim to the NumPy/f64 reference |

Prior production PASS results were not reused as proof: the plan states that production
numbers would be re-generated inside this task's own driver, and in the event no
production A/B was run at all — so no cross-line claim is made anywhere.

## Findings

### Blocking

**R-1 — B4 and B5 are not resolved: both redesigned tests are structurally incapable
of measuring their named quantity.**

*Test 08 (imbibition, B4).* The geometry is a wide reservoir (`z < neck = 16`, full
20 × 12 cross-section) below a narrow slit (`z ≥ 16`, width `h = 8`). The initial
condition puts the red surface at `z ≈ 7`. Jurin's expectation is
`Δz = 2σcos60°/(ρgh) = 5.95 lu`, but the meniscus must first be lifted 8–9 lu to
reach the slit mouth. I computed the two pressures directly:

```
max available capillary pressure  2σcos(θ)/h = 2.500e-03
hydrostatic cost to reach the slit ρgΔz      = 3.360e-03
=> capillary pressure cannot lift the meniscus into the slit
equilibrium meniscus height        = 7.5 + 5.95 = 13.95 < 16 = slit mouth
```

The measurement window (`z ≥ neck`) is therefore unreachable for the whole run, the
slit column never contains red fluid, `rise = nan`, and `rise_ratio = None`. The
committed trace confirms it: `slit_level = nan` at all eleven checkpoints while
`reservoir_level = 7.0` never moves. So the test neither tests Washburn nor Jurin; the
INCONCLUSIVE verdict is honest but the item still measures nothing. C3 item 8 required
a **valid** replacement (or an explicit deferral); neither was delivered, and the
report does not disclose the reachability failure.

*Test 07 (slit capillary pressure, B5).* The slit's two plates have normals ±z
(`solid[:, :, :2]` and `solid[:, :, 12:]`), while the initial condition lays the red
phase as a layer `psi[:, :, :7] = +1` — an interface **parallel** to both plates. An
interface parallel to the walls has no contact line and no curvature, so the setup
cannot produce a contact-angle-governed meniscus at all. I ran the two-angle
experiment the candidate never ran:

```
prescribed θ = 60°  : meniscus z = 6,  Δp = -9.252e-16, pc_expected = +2.000e-03
prescribed θ = 120° : meniscus z = 6,  Δp = -9.252e-16, pc_expected = -2.000e-03
in-plane psi spread at the interface = 0.00e+00  (exactly flat)
```

The centre-column ψ and ρ profiles are identical for the two prescribed angles. The
measured Δp = 0 is geometrically forced, so the FAIL is not a statement about the
wetting closure and the declared comparison against `2σcosθ/h` is never exercised.
The test's own docstring asserts the comparison is now valid; it is not. Using a
prescribed angle instead of `wetting="none"` removed the "neutral wall" objection but
not the structural one.

Because both items are the exact subjects of the review's two VALIDATION BLOCKERs,
and because they are counted in the matrix summary as ordinary FAIL/INCONCLUSIVE
results, the correction round's central validation claim is not met.

**R-2 — the phase / sign convention the review asked to be verified (C2.6) is
unresolved in the evidence, and it is decisive.**

`wetting_sign` exists and the code documents it as the switch that exists so the
validation can report which convention reproduces the prescribed angle. No test or
unit check ever varies it (the driver's `make()` leaves it at the default `+1.0`).
Consequently all pass-3 contact-angle numbers are one-convention numbers, and they
carry a clean signature that was not noticed:

| prescribed | measured (default sign) | error as measured | error of `180° − measured` |
|---|---|---|---|
| 60° | 114.75° | 54.75° | **5.25°** |
| 90° | 82.84° | 7.16° | 7.16° |
| 120° | 47.43° | 72.57° | **12.57°** |

I ran the missing experiment (same grid, IC, steps as test 04, only `wetting_sign`
changed):

| sign | prescribed | measured | error |
|---|---|---|---|
| +1 (default) | 60° | 114.75° | 54.75° |
| **−1** | 60° | **51.12°** | **8.88°** |
| +1 | 90° | 82.84° | 7.16° |
| −1 | 90° | 82.84° | 7.16° |
| +1 | 120° | 47.43° | 72.57° |
| **−1** | 120° | **112.78°** | **7.22°** |

With `wetting_sign = −1` the measured angle (through the psi > 0 phase, as the
instrument reports and as the test's own stated convention says) matches the
prescribed angle to 7–9° at every tested angle. So the wetting closure is very
probably working, and the candidate's default convention realises the prescribed θ_c
through the opposite phase from the one it prints. This is a one-switch experiment
that costs minutes; its absence means the package's conclusion that "the wetting half
is effectively unmeasured" is an artefact of an unswept convention, and the review's
C2.6 item is not discharged.

Note precisely: even with `sign = −1`, test 04 would still return INCONCLUSIVE,
because its own fit-quality gate fails on two arms (θ = 90° → rms 0.689 > 0.5;
θ = 120° → 5 contour points). The instrument needs work independently of the
convention. But the accuracy criterion (< 15°) would be met at all three angles.

**R-3 — the evidence package contradicts itself on provenance and on the R5 mapping.**

Five locations carry pre-correction text that the same file (or a sibling) retracts.
An external reviewer reading only these sentences would form the opposite conclusion:

1. `docs/research/leclaire_cg/PAPER_FORMULATION.md` §11 item 1 declares the R5
   gradient mapping **CLOSED** ("its `(2,4)` 3D stencil restricted to D3Q19 is exactly
   `3W_i`"), while §4.2 of the same file declares it **UNRESOLVED** and lists three
   reasons it cannot be settled. B12 required the UNRESOLVED marking; §11 retracts it.
2. `docs/research/leclaire_cg/REFERENCE_MANIFEST.md`, closing paragraph: "The
   acquisition note at the top of this file (that 科研通 tooling does not exist on this
   machine) still applies; R5 was obtained by local search rather than download." This
   directly contradicts the file's own corrected acquisition note and its R5 entry,
   and it contradicts the corroborating skill log. Keep the corrected text, delete this.
3. `results/leclaire_cg/PROVENANCE.md`, "Known weaknesses" #4: R5 "obtained … by local
   search rather than download" — same stale claim, contradicting the same file's
   "R5 provenance correction" paragraph 65 lines earlier.
4. `docs/research/leclaire_cg/CURRENT_VS_LECLAIRE_MAP.md` row 2 still describes R1's
   Table IV ordering as "shell-major: 1–6 axes, 7–18 diagonals" — the reading that
   `PAPER_FORMULATION.md` §0.1 explicitly corrects as wrong; and §A.7 still says R5
   "could not be obtained" and offers to degrade the row to `UNRESOLVED`, which §4.2
   has already done.
5. `results/leclaire_cg/EXECUTION_REPORT.md` §1 headline ("42 / 42 pass", "7 PASS,
   3 FAIL", "Laplace calibration **RESOLVED**"), §3 ("42 checks"), §6 ("The Laplace
   calibration — RESOLVED") and §8/§12 are un-annotated pass-2 claims that the pass-3
   evidence contradicts (59/59; 5 PASS / 3 FAIL / 2 INCONCLUSIVE; `sigma_ratio = 1.135`
   → FAIL). §5b states that "sections 1-12 above describe passes 1 and 2", but that
   sentence is attached to §5b, not to §1 or §6, and §6's "RESOLVED" is precisely the
   publication-quality language B8 asked to be withheld until a measured radius and a
   regression were used.

This matters for the task type, not just for tidiness: the deliverable *is* the
provenance record, and it currently requires the reader to know which of two
contradictory sentences was written last.

### Non-blocking

**R-4 — two gates are looser than the acceptance text they publish.**
`run_canonical.py`'s header states the acceptance statements are declared before the
run and authoritative, but test 04 admits `n_pts >= 6` while its acceptance says
">=8 contour points", and test 06 gates on the final amplitude only while its
acceptance says "agree to within 5% at every sampled time". For this run the data
happen to satisfy the stricter statements (the two isotropy traces are equal to
1.6e−13 at all five samples), so no verdict is wrong — but the gate would not detect a
mid-run divergence, and the declaration/implementation pair is inconsistent.

**R-5 — the newly written Akai path is never executed by any committed check.**
`wetting="akai"` is not used by any of the ten tests, and no unit check touches
`wetting_akai`, `extrapolate_to_solid_boundary` or `secant_contact_angle`. I exercised
it myself: all four wetting modes run 200 steps on the hemi-droplet geometry without
error, produce finite fields and `n_nonfinite_equilibrium = 0`; `wetting_akai` changes
the field materially (`max|Δψ|` = 1.016 versus the `wetting="none"` arm at t = 200);
and `extrapolate_to_solid_boundary` reproduces a hand-coded R3 Eq. (2) at a C_SB node
to 1e−14 with the D3Q19 weights. So the implementation is live, but B3's correction
ships as unexercised code, and the review's rule that no Leclaire-vs-Akai claim may be
made is respected only because no claim is made.

**R-6 — the test-06 evidence is close to tautological.** The two arms are
`(32,16,16)` with an x-wave and `(16,32,16)` with a y-wave: exact x↔y transposes of one
another. Identical results follow from the lattice's x↔y symmetry, so the observed
1.6e−13 asymmetry is a symmetry check, not an isotropy measurement — it cannot see
anisotropy along a diagonal direction. The design does satisfy what the review asked
for (equal wavelength, Fourier-mode observable) and it is strictly better than the old
max|ψ| comparison; a 45°-wave arm would give it evidential content.

**R-7 — test 09's docstring claims metrics it does not emit.** The docstring says the
"wall-band / contact-line / topology metrics are kept"; the JSON contains wall-band,
total/component mass, excursions, late rates, spurious velocity and component count,
but no contact-line metric.

**R-8 — minor dead code.** `geometry.contact_angle_from_profile` returns `nan`
(documentedly superseded) and `lattice.equilibrium` raises `NotImplementedError`
(documentedly a placeholder). Both are labelled, but they are shipped stubs.

## Modeling / Scientific Review

- **Assumptions explicit?** Yes. `α = W0` (unit density ratio), `χ = 1`, equal
  viscosities, `cos ϑ_0 ≡ 0`, and the deferred elements (R1 Eqs. 21–29, variable γ,
  R4's extra recoloring, η) are all named with their switches and their reasons.
- **Numerical setup represents the intended physics?** For tests 01, 02, 03, 05, 06 and
  10 yes. For tests 07 and 08 no — the geometry/IC cannot realise the named phenomenon
  (R-1). Test 09's geometry does represent the intended non-cancelling configuration:
  I verified all four lateral faces are fully solid (so the periodic wrap cannot carry
  fluid across) and that the mask is asymmetric in x and symmetric in y.
- **Convergence, not just completion?** Partly. Steady state was verified for 01, 02,
  03 and 05 (and 10 is at drift floor); for 04, 07, 08, 09 it is assumed — and test 07's
  result in particular is a transient snapshot whose zero I showed is geometric rather
  than converged.
- **Claims bounded by evidence?** Mostly, and better than most packages: the report's
  §8 "does not support" list and test 10's `scope_limitation` are good practice. The
  exceptions are R-3 (un-annotated superseded headlines) and the test 07/08 labels that
  present structurally inert configurations as ordinary FAIL/INCONCLUSIVE results.
- **Stale evidence?** Yes, in two senses: the report's §1/§6/§8/§12 claim set is stale
  relative to the pass-3 matrix (R-3), and the pass-2 block-interface numbers remain
  valid only for the pass-2 candidate. The candidate itself is internally consistent:
  the committed log, `summary.json` and prose all describe the same 5/3/2 split.

### Are any conservation corrections formulation-independent enough to retain?

Yes, but none is needed by `L17_CORE` in the tested states. R1's recolouring is
mass-conservative by construction (ΔN_i = −ΔN_opp(i)), the unit checks confirm
`Σ N_r = ρ_r` and `Σ N_b = ρ_b` exactly, and test 10 measures total drift
2.8e−13 per step without any overlay — so the `f64_arithmetic` overlay is redundant
here and is correctly reported as a non-paper-faithful arm. The transferable lesson is
not the overlay but the *diagnostic* discipline: the project's precision/backend
defect is a property of an equilibrium-based colour split and an f32 matrix roundtrip,
neither of which is present in this f64/reference construction — which is exactly why
B10's scope limit must travel with the result.

## Missing Evidence

1. A correct `wetting_sign` sweep (or an equivalent convention determination) and a
   re-run of test 04 under the determined convention (R-2).
2. A test 07 whose meniscus actually has contact lines on the walls — e.g. the phase
   interface perpendicular to the plates, spanning the gap (R-1).
3. A test 08 whose expected rise is reachable — reservoir surface at or above the slit
   mouth, or a slit mouth short enough that `2σcosθ/h > ρgΔz` (R-1).
4. Any execution evidence for `wetting="akai"` (R-5).
5. A contact-line metric in test 09, or removal of the docstring claim (R-7).
6. Resolution of the five contradictory text locations (R-3).
7. A steady-state justification for tests 04, 07, 08, 09 — the report says step counts
   were assumed, and test 07's zero is demonstrably not a converged meniscus.

## Answers to the reviewer contract's section F

1. **Is the implementation faithful to the cited formulation?** Yes, at the level I
   could verify. The lattice tables, the MRT basis and its row identities, the Eq. (4)
   density-gradient terms (including the B1 term, now correct), the perturbation with
   Eq. (18)'s 9/4, the recoloring pair structure, the secant wetting with λ = 1/2 and
   n = 2, the three-pass D3Q27 smoothing, the X_W 1D-Cartesian gradient, and the
   seven-step ordering with its site domains all match the sources I read directly.
   The two things I cannot certify are the R5 coefficient mapping (correctly marked
   UNRESOLVED in §4.2, wrongly marked CLOSED in §11) and the phase convention (R-2).
2. **Which current-vs-Leclaire differences are real rather than notation?** All of
   them. The map's `MATHEMATICALLY_EQUIVALENT` rows are the bookkeeping rows (A.1) and
   the polynomial equilibrium at `α = W0` (A.5); the gradient stencil (A.7) is the same
   operator once the R5 caveat is attached. Everything else is a real difference, and
   the derivation of the perturbation-vs-moment-injection row (A.8) is the strongest
   single piece of analysis in the package: it shows the *isotropic* part differs in
   sign and magnitude, which no Laplace test could ever detect.
3. **Which follow-up optimizations demonstrably change numerical behaviour?** Only two
   are demonstrable here, and neither is a follow-up in the paper sense: the explicit β
   amplitude law (test 05: width falls monotonically 1.84 → 1.12 over β = 0.5 → 1.0),
   and the unrelaxed post-collision perturbation (structural, per A.8). The Akai
   closure is implemented but unmeasured, so it has no demonstrated effect.
4. **Does complex-wall wetting improve, degrade, or remain unresolved?** It improves —
   and this is the finding of the review. Under the default convention the angles look
   wrong (errors 55–73°); under `wetting_sign = −1` the same code reproduces 60° → 51°,
   90° → 83°, 120° → 113°, i.e. 7–9° accurate. So the closure is likely correct and the
   *convention* is unresolved, which is a much more favourable state than the package
   currently reports.
5. **Are any conservation corrections formulation-independent enough to retain?** Not
   as code (test 10 needs none), but the `L17_CORE` vs `L17_PLUS_OVERLAY` two-arm
   reporting pattern and the solid-node-reservoir transient separation are worth
   keeping as practice. Any claim must stay scoped to the f64 reference until a
   Taichi/f32 port repeats the audit.
6. **Is the candidate ready for external scientific review?** No. Two of the ten
   canonical tests do not test what they are named after, the wetting convention is
   unresolved, and the provenance record contradicts itself. The fundamental work
   (equations, tables, ordering, isolation, conservation discipline) is in good shape
   and the fix list is short and cheap — but it is not yet a package an external
   reviewer can adjudicate.

## Declaration

- Reviewer session: fresh, independent; executor transcript not read or requested.
- Candidate not modified. All recomputation performed on a byte-identical staged copy
  under `.agent_runtime/BI-CG-LECLAIRE-IMPLEMENTATION-001/rerun/`.
- No GPU work, no production run, no Taichi execution.
- Files written by this review: `.agent_runtime/BI-CG-LECLAIRE-IMPLEMENTATION-001/REVIEW.md`
  and `.agent_runtime/BI-CG-LECLAIRE-IMPLEMENTATION-001/REVIEW_SESSION.json` only.
- PASS was not available on the evidence; HUMAN_REQUIRED was considered and not
  triggered, because the unresolved convention does not flip any current verdict
  (test 04 is INCONCLUSIVE on fit quality under either sign; test 07 fails under
  either sign). The owner is nonetheless asked to confirm the intended contact-angle
  phase convention before the re-run, since it determines the wording of every
  wetting result.
