# EXECUTION REPORT — BI-CG-LECLAIRE-IMPLEMENTATION-001

## 0. CURRENT HEADLINE — pass-04 (this is the only current summary)

**Every section below section 0 is a historical record and is explicitly
`SUPERSEDED`.** Passes 1, 2 and 3 are retained because their errors are part
of the provenance; none of their claims is current. Read
`results/leclaire_cg/pass-04/VALIDATION_REPORT.md` for the current
machine-readable summary and `docs/research/leclaire_cg/VALIDATION_ATLAS.md`
for the current visual entry point.

| item | value |
|---|---|
| stage | `BI-CG-LECLAIRE-PASS4-001` |
| frozen source candidate | `0b3da4e954878dc22618330caed9f0da0782d449` |
| evidence tree | `results/leclaire_cg/pass-04/` |
| unit checks | 73/73 (`results/unit_checks.log`) |
| pass-04 verdicts | {'PASS': 7, 'FAIL_SOLVER': 2, 'INVALID_TEST': 1, 'INCONCLUSIVE': 1} |
| backend scope | NumPy/f64 reference only; **not** ported to Taichi/f32 |

| case | verdict |
|---|---|
| case-01 | **PASS** | `case-01-uniform-stationarity/README.md` |
| case-02 | **PASS** | `case-02-planar-interface/README.md` |
| case-03 | **FAIL_SOLVER** | `case-03-laplace-multi-radius/README.md` |
| case-04 | **PASS** | `case-04-contact-angle/README.md` |
| case-05 | **PASS** | `case-05-beta-width-validity/README.md` |
| case-06 | **PASS** | `case-06-axis-symmetry-isotropy/README.md` |
| case-07 | **INVALID_TEST** | `case-07-slit-capillary-pressure/README.md` |
| case-08 | **INCONCLUSIVE** | `case-08-jurin-equilibrium/README.md` |
| case-09 | **FAIL_SOLVER** | `case-09-asymmetric-wall/README.md` |
| case-10 | **PASS** | `case-10-conservation/README.md` |
| case-11 | **PASS** | `case-11-mechanical-sigma/README.md` |

Gates were declared in `tests/leclaire_cg/pass04.py::GATES` before the run and
were not edited afterwards, with one documented exception recorded in
case-04's README: the contact-angle fit-quality gate was switched from the
linearised residual (radius-squared units) to the geometric residual in
lattice units, because the former mixed dimensions and scales as R^2. Both
quantities are reported for every angle so the change is auditable.

`A = (9/4) omega_eff sigma` was **not** retuned anywhere in this round.

---

## 1. Summary (SUPERSEDED — pass-1/2/3)

Delivered: an isolated, paper-faithful Leclaire-2017 D3Q19
colour-gradient candidate (`L17_CORE`) in `experimental/leclaire_cg/`, an
equation-level formulation and current-vs-Leclaire map in
`docs/research/leclaire_cg/`, and a ten-test canonical validation matrix
with machine-readable evidence in `results/leclaire_cg/`.

Headline status:

| item | result |
|---|---|
| table / operator unit checks | **42 / 42 pass** (exact to f64 roundoff) |
| canonical matrix | **7 PASS, 3 FAIL** (see §5) |
| the paper's recolouring is mass-exact | **confirmed**; flat-interface component mass is **bit-frozen** (§7) |
| Laplace calibration | **RESOLVED** — σ_meas/σ_input = 1.108 / 1.058 / 1.024 at R = 5 / 7 / 9, converging to 1 (§6) |
| ready for external scientific review | **NOT YET** — recommend `CHANGES_REQUESTED`; §9 lists what remains |

The candidate is **not** proposed for promotion. Nothing in this branch
changes production.

**This report covers two validation passes.** Pass 1 (`51cc61a`) gave
6 PASS / 4 FAIL with the Laplace offset unexplained and attributed to the
then-unobtainable R5 stencil. Between the passes R5 was obtained, which
**ruled out** that hypothesis and thereby located the real cause: an
arithmetic error in the Eq. (18) constant. Pass 2 re-ran the whole matrix
on the corrected candidate. Both passes remain in the history; §4.5 and
§6 describe the correction, and §11 lists what pass 1 got wrong.

**The most important thing in this report is not the matrix.** It is §4:
five corrective commits, four of which fixed defects that produced
*silent* wrong answers rather than crashes. A reader who skims to the
results table will miss the part that matters most for trusting the
implementation at all.

---

## 2. What was built

```
experimental/leclaire_cg/lattice.py     R1 Tables IV/VI/VII/VIII/XI
experimental/leclaire_cg/operators.py   R1 Eqs. (4)-(20), (30)-(38)
experimental/leclaire_cg/solver.py      the seven-step update, R1's order
experimental/leclaire_cg/geometry.py    algorithm-independent geometries
tests/leclaire_cg/test_lattice_tables.py   41 table/operator checks
tests/leclaire_cg/run_canonical.py         the ten-test matrix
```

Design decisions worth naming:

- **The equilibrium is evaluated in distribution space** from R1 Eq. (4),
  including the `ψ_i (u·∇ρ)` and `ξ_i (G:c⊗c)` density-gradient terms, and
  the moment equilibrium is formed as `M · N^(e)`. No closed-form moment
  equilibrium is hand-derived. This makes the density-gradient terms
  structurally impossible to drop, and removes the transcription risk the
  production line documented having to verify separately.
- **R1's step domains are honoured literally.** Steps (2), (4) and (5)
  act on `x ∈ X_F` only. §4 explains why this is load-bearing.
- Later paper variants (R3's wetting) and the project-style conservation
  overlay exist only as **default-OFF switches**.
- R1's regularized open boundaries (Eqs. 21–29) are **not implemented**,
  and the constructor **raises** rather than falling back.

---

## 3. Fidelity — what is verified exactly

`tests/leclaire_cg/test_lattice_tables.py`, **42 checks, all passing at
f64 roundoff**:

| group | checks | worst residual |
|---|---|---|
| Table IV weights, `φ+ϕW₀ = W`, `ΣB_i = 1/3`, `ζ(1−W₀) = 1/3`, opposite-map involution | 6 | 5.6e-17 |
| Table XI row identification (rows 0/3/5/7/9/11/13/14/15), invertibility, **rows 1–2 shell-constant** | 11 | 8.9e-16 |
| shell counts and norms | 3 | 0.0 |
| gradient: linear exactness on all three axes, physical sign, tanh agreement, off-axis zero | 6 | 1.3e-15 (linear) |
| equilibrium reduction to `ρW_i` at `u=0` | 2 | 0.0 |
| perturbation: mass, momentum, **second moment against the closed-form derivation** `(2/9)A|F|(n̂⊗n̂ − δ)`, and **the Eq. (18) constant itself** (`A = 2.25 ω σ`, asserted against both 2.25 and 1.5) | 5 | 3.5e-18 |
| recolouring: `Σ N_r = ρ_r`, `Σ N_b = ρ_b`, `N_r+N_b = N` | 3 | 2.2e-16 |
| bounce-back involution and fluid pass-through | 3 | 0.0 |
| streaming shift and mass preservation | 3 | 7.1e-15 |

Two of these checks exist because the corresponding defect was actually
made: `rows_shell_constant` pins R1's Table IV ordering (§4.1), and
`perturbation.A_equals_9over4_omega_sigma` pins the Eq. (18) constant
(§4.5). Neither is a hypothetical test.

---

## 4. Corrective commits — what each caught, and why it matters

The task contract asks for explicit corrective commits rather than
rewrites. Four of these fixed defects that produced **plausible-looking
but wrong** output. They are the strongest evidence in this package that
the implementation is now trustworthy, and they are also a warning about
how the earlier numbers should be read.

### 4.1 `dbe47d3` — R1's Table IV ordering is not shell-major

The first formulation draft assumed indices 1–6 are the axis directions
and 7–18 the diagonals. They are not: indices 10, 11, 12 are the
*positive* axes. The error was caught by a table cross-check — Table XI
row 1 has the values −30 / −11 / 8, and those are constant within a shell
**only** under the correct grouping. The check is now permanent
(`rows_shell_constant`). All per-shell weight lookups depended on it.

### 4.2 `d2177e5` — two silent colour-gradient defects

**(a) Direction.** `_shift(arr, c)` implements the *streaming* convention
`out[x] = arr[x−c]`. The gradient stencil needs `arr[x+c]`, so the operator
computed `−∇ψ`. Consequence: the colour gradient pointed the wrong way, which
**inverted the recolouring's segregation direction**, so the diffuse
interface could never be held. The signature was a terminal state that was
*identical for every σ, ν and χ* — i.e. insensitive to precisely the
parameters it should have depended on. That insensitivity is what made it
findable.

**(b) Normalisation.** The partial-stencil renormalisation divided by
`Σᵢ 3Wᵢ = 2` rather than by the trace factor `Σᵢ Wᵢ|cᵢ|² = 1`, scaling every
gradient by 0.5. The recolouring is blind to this (it uses the orientation),
but R1 Eq. (16) uses `|F|`, so the perturbation was halved.

Effect on the physics, planar interface, σ = 0.02, ν = 1/6, identical at
t = 200/600/1500 (a converged steady state):

| β | width | \|ψ\|max |
|---|---|---|
| 0.5 | 1.84 | 0.997 |
| 0.7 | 1.47 | 1.000 |
| 1.0 | 1.12 | 1.000 |

### 4.3 `33b0a33` and `22fe2d3` — wall geometries

Two coupled defects in the presence of solid nodes:

1. The recolouring recomputed `N_r = (ρ_r/ρ)N` at *solid* nodes, where
   `ρ_r = 0`, overwriting the streamed colour populations with zero. The
   domain-wide red mass decayed monotonically — a **mass sink**, not a
   divergence.
2. The collision ran at solid nodes too, where `ρ` can sit near the f64
   floor, so `u = (Σ Nᵢcᵢ)/ρ` exploded and the bounce-back carried the
   garbage into the fluid. That is the divergence (`|ψ|` up to 5e34 in
   test 04).

Both are fixed by applying R1's step domains literally. After the fix, the
slit geometry runs 800 steps with `|ψ|max = 0.889` and zero non-finite
equilibrium entries.

### 4.4 `a3f1c1a`-series — the wall normal was identically zero

`n_w` was computed with the *fluid-only* sampling mask. The smoothed solid
image is defined on every site and is nearly constant across the fluid
nodes, so a fluid-only stencil returns **exactly zero**: `|n_w| = 0` at
all 1152 wall nodes, making the entire wetting condition a silent no-op.
The symptom was test 04 returning the *same* 79.5° for prescribed 60°, 90°
and 120°. Note this is the **opposite** of the phase-field gradient, where
fluid-only sampling is what R1 §II.E specifies — the two gradients have
different correct domains.

After the fix, `|n_w| = 1.0` everywhere and the contact angle responds:

| prescribed | measured |
|---|---|
| 60° | 70.5° |
| 90° | 96.4° |
| 120° | 160.0° |

The 120° case is outside R1's own stated good-accuracy band
(`θ_c ∈ [45°, 135°]`, error growing asymmetrically away from 90°) and is
measured here with a crude spherical-cap estimator; see §5.

### 4.5 pass 2 — the Eq. (18) constant was written `1.5` instead of `9/4`

Found only because R5 arrived and **ruled out** the gradient-stencil
hypothesis for the Laplace offset (§6). With the stencil eliminated, the
calibration constant itself was the remaining candidate — and the code had

```python
A = 1.5 * omega[ok] * sigma        # (9/4) * omega * sigma
```

R1 Eq. (18) is `A = (9/4) ω_eff σ`, and **9/4 = 2.25, not 1.5**. The comment
on the line was right and the expression was wrong. The implemented `A` was
therefore `1.5/2.25 = 2/3` of the paper's; since the delivered surface
tension is proportional to `A`, the model returned exactly `2/3 × σ_input`.
Pass-1 ratios were 0.682–0.738 — i.e. `2/3` plus a finite-radius correction.

After the fix: **1.108 / 1.058 / 1.024** at R = 5 / 7 / 9, converging to 1
as the droplet is better resolved. That convergence is the expected
finite-radius behaviour, not a residual systematic.

`test_lattice_tables.py` now asserts the constant directly
(`perturbation.A_equals_9over4_omega_sigma`), because this error is
invisible to every conservation, table, stationarity and stability check —
it moves only the amplitude of the delivered surface tension.

**Generalisable lesson.** This defect was silent *and had been
rationalised*: the pass-1 report attributed the offset to a plausible
physical cause and wrote a careful paragraph about it. Obtaining R5
converted a plausible story into a refuted one, and the refutation is what
located the real bug. The prior "the paper's constant is fine; my
transcription is wrong" should have been tested first. Of the six defects
found in this candidate, four were silent and this one was also
self-justifying.

---

## 5. Canonical matrix

Driver: `tests/leclaire_cg/run_canonical.py`. Pre-declared acceptance
statements are in the driver and are not edited after the fact.
Parameters: σ = 0.02, ν = 1/6, β = 0.7, χ = 1 (SRT limit), unit density
ratio. Machine-readable per-test output in `results/leclaire_cg/*.json`.

**Pass 2 (current candidate, commit after `51cc61a`).** All ten entries
below are from a single uninterrupted run of the committed driver.

| # | test | verdict | headline number |
|---|---|---|---|
| 1 | uniform single-phase stationarity | **PASS** | `max|v| = 8.8e-14`, `max|Δρ| = 7.5e-14` |
| 2 | planar interface stationarity | **PASS** | position drift 0.0057 lu over 1000 steps; amplitude ratio 0.99987 |
| 3 | Laplace droplet | **PASS** | σ_meas/σ_input = 1.108 / 1.058 / 1.024 at R = 5 / 7 / 9; radius-independence spread 8.4 % |
| 4 | static contact angle | **FAIL** | 60→54.5°, 90→106.6°, 120→unmeasurable |
| 5 | interface width vs β | **PASS** | monotone: 1.84 / 1.47 / 1.12 / 0.66 / 0.40 for β = 0.5 / 0.7 / 1.0 / 1.5 / 2.0 |
| 6 | dynamic isotropy | **PASS** | x-vs-y wave response agrees to **0.48 %** |
| 7 | static slit capillary pressure | **FAIL** (test design) | Δp = 0 to 1e-16 — flat meniscus at neutral wetting; test must be redesigned |
| 8 | simple capillary imbibition | **FAIL** | front *retreats* by 1 lu (z 5→4) instead of advancing |
| 9 | asymmetric killer test | **PASS** (with a caveat) | wall-band red changes 0.91 %; single component; fluid max\|v\| = 0.020 |
| 10 | conservation audit | **PASS** | `L17_CORE` **total and component drift bit-frozen at 0.0** over 1000 steps |

**Pass 1 (`51cc61a`) for comparison** — same driver, pre-fix candidate.
Pass 1 was 6 PASS / 4 FAIL; pass 2 is **7 PASS / 3 FAIL**.

| # | pass 1 | pass 2 |
|---|---|---|
| 3 | FAIL, ratios 0.682–0.738 | **PASS**, ratios 1.024–1.108 |
| 4 | FAIL, 60→70.5° | FAIL, 60→54.5° |
| 9 | PASS, wall-band 1.21 % | PASS, wall-band 0.91 % |
| 10 | PASS, 2.8e-13/step | PASS, bit-frozen 0.0 |
| 7, 8 | FAIL | FAIL |

Test 3 is the only verdict that changed. Tests 4, 7 and 8 fail for reasons
unrelated to §4.5. Pass-1 numbers are kept because the direction of change
is itself evidence about which physics the constant controls.

### What passed, and why it is credible

Test 5 is the cleanest positive result and directly tests R2's central
claim that the recolouring parameter alone controls the numerical
interface thickness: the width falls **monotonically** over a factor of 4.6
in β, with the bulk phases fully separated for β ∈ [0.5, 1.0]. R1's
refinement law `β = β*(Δx/Δx*)^η` is *not* tested — it needs two
resolutions, and the report says so rather than implying otherwise.

Test 6 shows the interface dynamics carry no resolvable lattice-direction
bias (0.46 % between an x-directed and a y-directed capillary wave).

Test 9's geometry is the one R2's warning demands: one-sided ledge, four
closed lateral faces, no imposed pressure difference, so a wall-directed
mass transfer cannot cancel by symmetry. Wall-band red mass moves 1.21 %
over 1500 steps and the domain stays a single component.

**Test 9 caveat, stated rather than buried.** The test only passed the two
criteria it declares. The measured wall-band change of 1.21 % is close to
its own 2 % gate rather than comfortably inside it, and the driver's
whole-domain `max|v|` was initially reported as 1.0, which looked like a
near-sonic spurious current. That number was a **solid-node artefact**:
measured on the same run, the fluid-only `max|v|` is 0.021. The driver's
velocity metric has since been corrected to report the fluid-only value,
because a solid node holds only what streaming delivered and `u = mom/ρ`
there is not a physical velocity. Also note that a 1.21 % wall-band drift
over 1.5k steps is not zero, and 1.5k steps is short.

### What failed

- **Test 7 (slit capillary pressure).** This test needed two corrections
  before it measured anything, and after both it returns a physically
  correct but uninformative answer.
  - The first version measured "top" and "bottom" regions of a *sealed*
    slit, which do not exist, and returned `None`.
  - The second version's sampling windows were wider than the slit, so
    they were empty again.
  - With a wide enough slit the test now measures cleanly
    (`max|v| = 0.0`) and returns **Δp = −9.3e-16, i.e. zero**, for both
    gaps 10 and 12.

  That zero is the *correct* static result for this setup: the test runs
  with `wetting="none"`, so the wall is neutral (θ ≈ 90°), the meniscus is
  **flat**, its curvature is zero and so is the capillary pressure. The
  failure is therefore in the test design, not in the solver — the gate
  assumes a curved meniscus that this configuration cannot produce. To
  probe `P_c = 2σcos θ/gap` the test needs a *prescribed* contact angle,
  which is exactly what test 4 exercises. Reported as `FAIL` against its
  declared gate and flagged as a test that must be redesigned.
- **Test 8 (imbibition).** The front does not merely stall, it *retreats*
  by 1 lu (front at z = 5 for 561 steps, then z = 4 for the remaining 935).
  With spontaneous imbibition absent, this is a genuine negative result
  for this candidate at these parameters, not a measurement artefact.
- **Test 4 (contact angle).** Responds monotonically and is close at
  60°/90°, but the measurement is a crude spherical-cap estimator
  (`θ = 2·arctan(apex/r_b)`) and the 120° case is unmeasurable (the cap
  does not reach the first fluid layer). A profile-normal fit at the
  contact line, as R3 uses, is the correct instrument.

---

## 5b. Validation pass 3  [SUPERSEDED by pass-04] — post-review correction candidate

Candidate **`5a3929fa1cefb7359893d6c19ed0ec8a7c80a91d`**, produced in response to external review
`EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md` (reviewed candidate
`738e76f`). Everything in sections 1-12 above describes **passes 1 and 2**
and is retained unchanged: the earlier candidates' behaviour, including its
errors, is part of the record.

Counts: **FAIL 3, INCONCLUSIVE 2, PASS 5**.

All ten entries are from a single uninterrupted run of the frozen driver at
candidate `5a3929fa1cefb7359893d6c19ed0ec8a7c80a91d`.

| # | verdict | headline |
|---|---|---|
| 01 | **PASS** |  |
| 02 | **PASS** |  |
| 03 | **FAIL** | sigma ratio 1.135, R^2 1, intercept -0.000531 |
| 04 | **INCONCLUSIVE** | 60->115, 90->82.8, 120->47.4 |
| 05 | **PASS** | widths [1.84, 1.47, 1.12], positivity violations at beta=[1.5, 2.0] |
| 06 | **PASS** | asymmetry 1.589e-13 |
| 07 | **FAIL** | pc ratios ['-4.81e-13', '-8.44e-13'] |
| 08 | **INCONCLUSIVE** | rise nan vs Jurin 5.95 ratio n/a |
| 09 | **FAIL** | max excursions red/blue 2.7e-13/2.7e-13, late rates -2.4e-13/-2.6e-13 |
| 10 | **PASS** | total/step ['2.8e-13', '2e-14'] |

### What the review changed, and whether it moved the numbers

| blocker | change | observable effect |
|---|---|---|
| B1 | Eq. (4) `psi_i(u.grad rho)` | A1-A4 now hold at non-zero `u`, `grad rho`; previously untested |
| B2 | R1 `X_W` 1D Cartesian gradient | wall-adjacent `F` and `grad rho` are no longer a renormalised truncated stencil |
| B3 | R3 Eqs. (2)-(4) complete | `wetting="akai"` is now R3; the partial form is renamed |
| B4 | test 08 replaced with a closed-system Jurin test | the old periodic two-interface setup is gone |
| B5 | test 07 prescribed contact angle | compared against `2 sigma cos(theta)/h`, not `2 sigma/h` |
| B6 | test 09 topology and mass gating | the box is verified closed; global mass is now gated on the time-history maximum and the late-window rate |
| B7 | test 06 equal wavelength + Fourier mode | the two arms are a genuine lattice-direction comparison |
| B8 | test 03 measured radius + regression | nominal radius replaced by the equivalent-sphere radius from the phase field |
| B9 | test 05 positivity gates | `|psi| > 1` is now a warning, not a valid interface |
| B10 | conservation scope | the bit-frozen claim is explicitly f64-reference-only |
| B11 | 科研通 provenance | R5 is recorded as a 科研通 delivery; the earlier "no tooling" claim is retracted |
| B12 | R5 mapping | marked `UNRESOLVED` with the exact mapping recorded |

### Reading pass 3 against pass 2

Pass 2's headline was 7 PASS / 3 FAIL. Pass 3 is
**5 PASS / 3 FAIL**
/ 2 INCONCLUSIVE.
The counts are **not directly comparable**: six of the ten tests were
rebuilt because the review found them invalid, so a verdict change is a
change of question as much as of answer. Where a verdict moved, the report
says which of the two it is.


## 6. The Laplace calibration  [SUPERSEDED by pass-04] — RESOLVED

**Outcome: the model now reproduces R1 Eq. (18)'s interfacial tension.** The
offset that dominated validation pass 1 was an arithmetic error in the
implementation, not a property of the model or of the source.

### 6.1 What pass 1 measured

With `A` implemented as `1.5·ω·σ`, the measured tension was 0.682–0.738 of
the input across R = 5/7/9, and a separate β sweep showed the ratio was
**independent of the interface resolution** (R/width from 10 to 83). That
resolution-independence was correct reasoning about the evidence and is
what made the offset look like a constant calibration factor rather than a
discretisation artefact.

### 6.2 What R5 changed

Pass 1's leading hypothesis was a constant stencil-normalisation
difference in `|F|`, since R5 was unobtainable. Obtaining R5
(`REFERENCE_MANIFEST.md`, `PAPER_FORMULATION.md` §4.2) **refuted** that:
R5's `(S,I) = (2,4)` 3D weights restricted to D3Q19 are `1/6` on the axes
and `1/12` on the face diagonals, which is exactly `3W_i` — the operator
this implementation already had, derived independently. With the stencil
eliminated, the calibration constant itself became the remaining
candidate, and it was wrong: `A = 1.5·ω·σ` where Eq. (18) says
`A = (9/4)·ω·σ = 2.25·ω·σ`. `1.5/2.25 = 2/3`, which is the measured
offset.

### 6.3 Pass-2 measurement

| R | Δp | σ_measured | σ_input | ratio | R/w |
|---|---|---|---|---|---|
| 5 | 8.86e-3 | 0.02216 | 0.02 | **1.108** | 39 |
| 7 | 6.04e-3 | 0.02116 | 0.02 | **1.058** | 20 |
| 9 | 4.55e-3 | 0.02048 | 0.02 | **1.024** | 10 |

- The droplet survives at every radius (`|ψ|peak` ratio = 1.000), so the
  pressure difference is a genuine Laplace measurement.
- The ratio **converges towards 1 as R grows**: the excess falls 10.8 % →
  5.8 % → 2.4 % across R = 5 → 9, i.e. roughly as `1/R`. That is the
  expected finite-radius behaviour (the tension surface does not coincide
  with the ψ = 0 surface when the interface has finite width), not a
  residual systematic. Extrapolating, the R → ∞ value is consistent with
  unity.
- Radius-independence of the implied σ is 8.4 % over R = 5–9 at fixed
  β = 0.7, so the Laplace law itself is demonstrated.

### 6.4 Claim discipline

The honest statement is: *at R = 9 the delivered tension is within 2.4 % of
the input, and the residual shrinks with radius in the manner a
finite-radius correction predicts.* The evidence does **not** include an
R → ∞ extrapolation with a fitted correction, so the report does not claim
"σ_measured = σ_input exactly". A convergence study in R, or a comparison
against an analytic profile, would settle that; it was not run.

### 6.5 The cross-check predicted in pass 1

`CURRENT_VS_LECLAIRE_MAP.md` §4 predicted that if a paper-faithful line and
the production `CapA` line were driven to the same measured σ, the ratio
`CapA/σ` should come out near the production line's independently measured
`1/1.012`. That prediction was made from the §A.8 derivation when the
implementation still had the wrong `A`. It is now the natural next check
and has **not** been run; it is listed in §9.

---

## 7. Conservation — a positive result worth stating clearly

The formulation derives, and the unit checks confirm, that R1's
recolouring satisfies `Σᵢ Ωᵢ^r = ρ_r` **exactly** (the rest population is
untouched and `Σᵢ Wᵢ cos ϑᵢ = 0`). Test 10 confirms it numerically for the
no-solid geometry:

Pass 2, planar interface, 1000 steps:

| arm | total drift / step | red / step | blue / step |
|---|---|---|---|
| `L17_CORE` (no overlay) | **0.0** | **0.0** | **0.0** |
| `L17_PLUS_OVERLAY` (`f64_arithmetic`) | **0.0** | **0.0** | **0.0** |

The component mass is **bit-frozen**: the sampled red mass is the identical
f64 value `799.999607...` at every one of the eleven checkpoints. That is a
stronger result than pass 1 reported (2.8e-13/step), and consistent with the
construction -- R1's recolouring is exactly mass-conserving, so once the
interface reaches its discrete fixed point there is nothing left to round.

Two things follow.

1. `L17_CORE` needs **no** conservation correction at all in this geometry.
   The overlay is redundant here, so the contract's rule that an overlay
   arm must never be labelled paper-faithful applies trivially.
2. This is *not* a claim that the candidate is conservative in every
   geometry. The wall-bounded case carries the solid-node reservoir
   (below), and pass 1 measured a small non-zero drift in this same planar
   geometry. Read the bit-frozen result as "this configuration is
   stationary", not as a general theorem.

**Wall storage.** In geometries with solid nodes the whole-domain mass is
not stationary early on, because R1's full-way bounce-back (step 6) fills
the solid-node reservoir. Measured on the slit, 1200 steps:

```
t =   0..400   +1.10e-08 / step
t = 400..800   -9.61e-14 / step
t = 800..1200  -8.24e-14 / step
```

The reservoir **saturates** and the asymptotic rate is f64 roundoff. This
is a property of R1 step (6), not a leak. Any future conservation
reporting on wall-bounded geometry must separate the reservoir transient
from the asymptotic rate, or it will read as a defect.

---

## 8. What this evidence supports, and what it does not

**Supports:**

- the D3Q19 tables, the MRT basis and its row identities, the perturbation's
  conservation laws and its second moment, the recolouring's exact component
  conservation, and the gradient's sign, linear exactness and isotropy -- all
  at f64 roundoff (42/42 checks);
- that the gradient operator matches R5's published `(2,4)` 3D stencil on the
  direction set D3Q19 possesses;
- that a stable diffuse interface exists, that beta controls its width
  monotonically, and that the interface dynamics are lattice-isotropic to
  0.5 %;
- that the delivered interfacial tension matches R1 Eq. (18) to within 2.4 %
  at the largest tested radius, with the residual shrinking as the interface
  is better resolved;
- that R1's recolouring needs no conservation correction, and that the
  planar-interface component mass is bit-frozen;
- that R1's wetting condition, once the wall normal is computed on the
  smoothed image, produces angles that respond to the prescribed value.

**Does not support:**

- a quantitative contact-angle claim. The instrument is a spherical-cap
  estimate whose error changed sign between passes; the wetting BC is the
  paper's headline contribution and it is not yet measured (section 9.1);
- spontaneous imbibition at these parameters (test 8 fails);
- slit capillary pressure against an analytic value (test 7 cannot produce
  a curved meniscus);
- an `R -> infinity` value of sigma. The trend is consistent with 1 but was
  not extrapolated (section 6.4);
- any claim about `eta` in R1's refinement law (needs two resolutions);
- anything about porous media, graphite, separator, PCS or gap: none was
  run, per the stop boundary;
- **any performance claim.** This candidate is NumPy, not Taichi; the
  production line's ~5.5 min JIT tax per instance motivated that choice and
  makes the two incomparable on speed.
## 9. Open items for the reviewer

Ordered by how much they change the interpretation.

1. **Test 4 (contact angle) is measured with the wrong instrument.** The
   reported angles come from a spherical-cap estimate
   `theta = 2*arctan(apex/r_b)`, valid only for a genuine spherical cap and
   sensitive to where the contact line is judged to be. Pass 1 gave
   60 -> 70.5 deg; pass 2 gives 60 -> 54.5 deg for the same prescribed
   angle. The *sign* of the error flipped between passes, which is what an
   unreliable estimator looks like. The 120 deg case yields `r_b = 0` (the
   cap does not reach the first fluid layer) in both passes. **A
   profile-normal fit at the contact line, as R3 uses, is required before
   any conclusion about the wetting BC can be drawn.** The FAIL verdict is
   not evidence that the BC is wrong, only that this test cannot yet say.
2. **Tests 7 and 8 fail, and they are not the same failure.** Test 7
   returns a *correct* zero (flat meniscus at neutral wetting, so
   `P_c = 0`) and needs redesign with a prescribed contact angle. Test 8's
   front *retreats* by 1 lu, a real negative result. Do not merge them into
   one phenomenon without evidence.
3. **The `CapA <-> sigma` cross-check predicted in pass 1 (section 6.5) has
   not been run.** `CURRENT_VS_LECLAIRE_MAP.md` section 4 predicts
   `CapA/sigma ~ 1.012`; driving both lines to a common measured sigma would
   test the section A.8 derivation end-to-end rather than only in algebra.
4. **The R3 wetting variant is wired but never ablated.** `wetting="akai"`
   exists and is default-off; no run compares it with `wetting="leclaire"`.
   R2 records that periodic closure can hide wetting defects, and tests 7
   and 8 are exactly the confined geometries where an alternative wall
   treatment should be compared. This is a gap in the package, not a result.
5. **Test duration.** 1000-2000 steps at beta = 0.7. Steady state was
   verified for tests 1, 2, 3 and 5 (and test 10 is bit-frozen); for 4, 7,
   8 and 9 it was assumed.
6. **The solid-node reservoir.** Whole-domain mass in wall-bounded geometry
   is not stationary early, because R1's full-way bounce-back fills the
   solid nodes. On the slit the rate falls from +1.10e-08/step (t<400) to
   -9.6e-14/step (t>800), i.e. it saturates. Any later conservation
   reporting must separate that transient from the asymptotic rate or it
   will read as a leak.
## 10. Scope exclusions actually honoured

- `lbm_solver_cg3d.py` **unmodified** (blob `1b7db4ac…`), verified.
- No production default, gate or threshold changed.
- No V3, graphite, separator, PCS, gap or porous-media production run.
- D3Q19 only.
- No Palabos source copied.
- R1 Eqs. (21)–(29) regularized open boundaries **not implemented**; the
  constructor raises rather than falling back.

## 11. What validation pass 1 got wrong

Recorded because the mechanism is more instructive than the outcome.

Pass 1's report stated, in a carefully argued section 6, that the Laplace
calibration carried "a quantified, resolution-independent 0.70 offset" and
that "the most plausible source is the discrete |F| scale". Every step of
that reasoning was sound *given its premise*: the resolution-independence
was correctly measured and correctly interpreted, and the stencil genuinely
was the one element without a sourced coefficient set.

The premise was still testable and was not tested. Obtaining R5 cost one
local file search and refuted it in a single comparison. Once refuted, the
remaining candidate was a constant sitting in plain sight on one line of
code.

Two things would have caught it earlier, and both are cheap:

- **Check the paper's constants against the code by value, not by
  comment.** The line read
  `A = 1.5 * omega * sigma  # (9/4) * omega * sigma`. Reading the comment
  confirms nothing; evaluating `9/4` does.
- **When an offset is a clean round number, look for a constant.** `2/3`
  is `1.5/2.25`. A measured 0.67 sitting next to a documented `9/4` in the
  source is a strong hint that should have been checked before writing a
  paragraph attributing it to physics.

## 12. Recommendation

**`CHANGES_REQUESTED`**, on a narrower basis than after pass 1.

What pass 2 improved: the Laplace law passes, with the calibration
converging to the paper's value; conservation is bit-frozen; 42/42 table
and operator checks are exact. The calibration item that dominated pass 1
is closed.

What still blocks: **three tests fail, and two of the three are about the
instrument rather than the solver.** Test 4's contact-angle estimator is
demonstrably unreliable -- the sign of its error changed between passes for
the same prescribed angle -- and test 7's design cannot produce a curved
meniscus. Until those two are rebuilt, the wetting half of this candidate
is effectively unmeasured, and the wetting BC is the paper's headline
contribution. Test 8's retreating front is an untouched real negative
result.

So: the *bulk* physics of this candidate is now in good shape; the
*wetting* physics is not yet measured. That distinction should drive the
next round.
