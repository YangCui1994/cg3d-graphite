# FRESH REVIEW — BI-CG-LECLAIRE-PASS4-001

## Binding

- **Task ID:** `BI-CG-LECLAIRE-PASS4-001`
- **Product branch:** `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`
- **Base:** `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`
- **Frozen Pass-4 source candidate:** `0b3da4e954878dc22618330caed9f0da0782d449`
- **Pass-4 evidence / package tip:** `ca10d6503857f2d6349ce313dd97561d9406fd9e`
- **Control branch read (fast-forward):** `agent-dev/bilateral-episode-v0.1` @ `c6dfab31b975823df09839cd9ed68422e111f64a`
- **Reviewer contract:** `.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_PASS4_REVIEWER_CONTRACT.md`
- **Worktree:** `cg3d-episode-worktrees/REVIEW-BI-CG-LECLAIRE-PASS4-001` (detached at `ca10d65`, read-only)
- **Staging:** `.review_runtime/BI-CG-LECLAIRE-PASS4-001/` (outside every git worktree)

## Review mode

`FRESH_SESSION` — independent reviewer. The executor transcript was not read and
not requested. The frozen candidate was not modified; every run wrote into a
staging tree. `EXECUTION_REPORT.md`, `SUMMARY.json`, the atlas and the rendered
figures were treated as claims and checked against raw artifacts, which were
first re-derived from the frozen source.

## Decision

**CHANGES_REQUESTED**

The Pass-4 core claim is falsified. `case-04-contact-angle` passes only because
the measurement instrument reports the angle through the *gas* side while
documenting it, and labelling it in `metrics.json`, as "theta measured through
psi>0 liquid/red". Measured correctly through the liquid, the same runs give
126.0 / 96.0 / 67.2 deg for prescribed 60 / 90 / 120 — the **complement** of the
prescribed angle at every point. That single sign fault explains, and unifies,
all three wetting outcomes in this pass: the contact-angle PASS, the slit
capillary-pressure "INVALID_TEST", and the Jurin "INCONCLUSIVE".

Two further defects are independently blocking: the raw fields that the whole
artifact specification is built on were never committed (a repo-wide `*.npz`
ignore rule silently dropped them), and the named frozen candidate `0b3da4e`
cannot execute the harness that produced its own evidence tree.

## Coverage

Inspected:

- the five required documents (reviewer contract, wetting convention, artifact
  spec, atlas, previous fresh review, external review R2) and `AGENTS.md`;
- the complete `base..tip` diff (33 files) and every commit message in
  `245d6e6 … ca10d65`;
- `experimental/leclaire_cg/{lattice,operators,solver,geometry}.py`,
  `tests/leclaire_cg/{artifact,pass04,pass04_rerun}.py`,
  `tests/leclaire_cg/test_lattice_tables.py`;
- all eleven committed case directories, their README/metadata/metrics/render
  manifests, and the pass-04 `SUMMARY.json`, `run_manifest.json`,
  `VALIDATION_REPORT.md`;
- `docs/research/leclaire_cg/*.md` (all eight) and `results/leclaire_cg/*.md`;
- the R1 source PDF text layer (PRE 95, 033306) for the `n_w` definition.

Recomputed (not read):

- `experimental/leclaire_cg/*` and `tests/leclaire_cg/artifact.py` hashes at
  `0b3da4e` and `ca10d65` — byte-identical, so the differing file is the harness
  only;
- the whole pass-04 matrix from a byte-exact copy of the frozen candidate, into
  a staging results tree (see §13);
- `test_lattice_tables.py` unit checks from the frozen candidate;
- contact-angle geometry from the retained raw fields, independently of the
  driver's contour fit (section §3 below);
- an exact synthetic spherical-cap test of `contact_angle_circle_fit`;
- the slit meniscus shape, the `angle(F, n_w)` invariant at both contact lines,
  and the slit pressure difference from bulk density means;
- the Jurin reachability arithmetic and the raw initial/intermediate/final
  fields;
- the Laplace equilibrium radii, `Delta p`, free/zero-intercept regressions,
  per-radius `sigma_i` and residuals from the retained raw droplets;
- the mechanical-sigma derivation algebra by hand, and the case-11 raw psi
  profile;
- pixel-level regeneration of three committed field figures from the retained
  raw npz;
- the render-manifest bindings and per-case artifact completeness.

Not inspected: the executor transcript (forbidden); the production Taichi
solver (out of scope, no GPU work authorised); the R2/R4/R5 PDFs beyond the R1
quotations needed here; the contents of the 科研通 web session (only the local
record and the local PDF bytes).

---

## 1. Binding and isolation — PASS, with one binding defect

| check | result | evidence |
|---|---|---|
| source candidate is exactly `0b3da4e…` | PASS | commit exists on the product branch, message "convention+validation-fix+diagnostic+visualization: pass-04 frozen source" |
| evidence tip is exactly `ca10d65…` | PASS | tree read at `ca10d65` in a detached worktree |
| ancestry from base `6c30260…` | PASS | `git merge-base --is-ancestor 6c30260d 0b3da4e` true; `0b3da4e` is an ancestor of `ca10d65`; both on `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001` |
| `lbm_solver_cg3d.py` unchanged | PASS | blob `1b7db4ac27448b5b982cead1ea86e719c59e6684` identical at `6c30260d`, `0b3da4e`, `ca10d65` |
| no production defaults changed | PASS | the only non-added file in `base..tip` is `.gitignore` (+3 lines, adds `docs/research/leclaire_cg/_refs/`) |
| no Taichi / f32 port | PASS | no `taichi` import anywhere in `experimental/leclaire_cg/` or `tests/leclaire_cg/`; the only hits are comments and `artifact.py` storing f32 *snapshots* of an f64 solver |
| no V3 / graphite / separator / PCS work | PASS | changed top-level paths are exactly `.gitignore`, `docs/research/leclaire_cg/**`, `experimental/leclaire_cg/**`, `results/leclaire_cg/**`, `results/{pass04_run,pass04_rerun,unit_checks}.log`, `tests/leclaire_cg/**` |
| pass-04 lives under the immutable `results/leclaire_cg/pass-04/` tree | PASS | 136 committed files under that path; created only at `ca10d65` |
| earlier passes not overwritten **by Pass-4** | PASS | `ca10d65` touches top-level `results/leclaire_cg/EXECUTION_REPORT.md` only; `01_*.json` … `10_*.json`, `summary.json`, `PROVENANCE.md`, `UNIT_CHECKS.log` are untouched |
| **frozen candidate can produce the evidence** | **FAIL** | see below |

### 1.1 The named frozen candidate cannot run the harness that produced cases 04 and 07

`tests/leclaire_cg/pass04.py` was created at `0b3da4e` and modified at
`ca10d65`. Running the candidate's own driver aborts:

```text
File "…/pass04.py", line 355, in case_04
    and r["fit_rms_geom"] < g["max_fit_rms_geom"]]
KeyError: 'max_fit_rms_geom'
[           NOT_RUN] case-04  (558.5 s, exit 1)
File "…/pass04.py", line 601, in case_07
    xx = np.arange(n[0])[None, :, None] * np.ones(n)
ValueError: operands could not be broadcast together with shapes (1,28,1) (28,14,10)
[           NOT_RUN] case-07  (18.5 s, exit 1)
NameError: name 'write_validation_report' is not defined      # after the case loop
```

These are transcribed from the committed `results/pass04_run.log`. Cases 04 and
07 in the evidence tree therefore come from the *later* harness state:
`pass04_rerun.py` re-ran exactly those two after "an unrenamed gate key and a
broadcasting error" were fixed, and rebuilt `SUMMARY.json`,
`run_manifest.json` and `VALIDATION_REPORT.md`. `run_manifest.json` still
records `"command": "python tests/leclaire_cg/pass04.py"` for the whole tree,
which is not what produced cases 04 and 07.

Two mitigating facts, both verified rather than asserted:

- `experimental/leclaire_cg/*.py` and `tests/leclaire_cg/artifact.py` are
  **byte-identical** between `0b3da4e` and `ca10d65`, so the physics source for
  all cases is the frozen candidate's;
- the re-run is disclosed in `SUMMARY.json`/`run_manifest.json` under
  `rerun_note`, and in `results/pass04_rerun.log`.

What is not disclosed is that the case-04 **acceptance gate changed** in the
same step: `GATES["04_contact_angle"]` went from
`max_fit_rms=0.5` to `max_fit_rms_geom=0.30`. The new metric is dimensionally
correct and the new threshold is stricter, so this is not a loosening — but
`pass04.py`'s own module docstring still says "Gates … are NOT edited after
results are seen", and that sentence is now false. `EXECUTION_REPORT.md` §0
says the change is "recorded in case-04's README"; the case-04 README contains
no mention of it (grep for `rms|gate|dimension|linearised|switched` returns
nothing). The justification survives only as a code comment in the tip's
`pass04.py` and in the `metrics.json` pair `fit_rms` / `fit_rms_geom`.

`SUMMARY.json` and `run_manifest.json` report `candidate_sha = 0b3da4e…`, but
that string is read from an untracked `.cand` file at run time (there is no
`__cand__` in `pass04.py`), so the SHA in the machine-readable summary is a
claim, not a derivable fact. It does match the requested candidate.

**Binding verdict:** the candidate binding holds for the solver source, not for
the harness. A reviewer cannot regenerate cases 04 and 07 from `0b3da4e`.

---

## 2. Wetting / phase convention — the normative convention is implemented as its negation

Definitions, checked in the source rather than in the prose:

| element | required by the contract | as implemented | verdict |
|---|---|---|---|
| red = electrolyte / liquid / wetting | yes | `psi = (rho_r - rho_b)/rho`; `+1` is red | AGREE |
| blue = gas / non-wetting | yes | `-1` is blue | AGREE |
| `psi = (rho_red-rho_blue)/rho` | yes | `Solver.psi()` | AGREE |
| `F = grad(psi)` points gas -> liquid | yes | `op.gradient(psi, …)` is the D3Q19 isotropic gradient, unit-checked as an exact gradient | AGREE |
| `g = 1` in solid, `0` in fluid | yes | `smooth_solid()` returns the smoothed binary solid mask | AGREE |
| `n_w = -grad(g)/|grad(g)|` points solid -> fluid | as frozen | `wall_normals(solid, sign=-1.0)`, `self.nw_sign = -1.0` by default | AGREE with the frozen text |
| contact angle always measured through red/liquid | yes | **the instrument returns the angle through the gas side** | **VIOLATED** |

### 2.1 The source defines the opposite wall normal

R1, *Phys. Rev. E* **95**, 033306 (2017), p. 9, text layer:

> "Then the normal nw to the solid matrix at the fluid lattice sites near the
> boundary are estimated as the gradient of the smoothed image, i.e.,
> nw(α,β,γ) = ∇g(α,β,γ)(3)."

with `g` the fluid-solid binary matrix (1 in solid). So in the cited source
`n_w = +∇g/|∇g|`, i.e. **pointing from fluid into the solid**. The project's
`WETTING_PHASE_CONVENTION.md` §3 freezes the negation
(`n_w = -∇g/|∇g|`, solid -> fluid), and `solver.py` implements exactly that
negation. The formulation document is faithful to the paper here
(`PAPER_FORMULATION.md` §7.3: "`n_w = ∇g⁽³⁾`"), so the two internal documents
disagree about the sign, and the normative one chose the negation.

### 2.2 The implementation really does impose `angle(F, n_w) = theta_c`, and that yields the complementary physical angle

From the retained final fields I recomputed `F = op.gradient(psi, fluid, wall,
variant="l17")` and `n_w = op.wall_normals(solid, sign=-1.0)` and evaluated the
angle between them at the sites where the interface meets the wall:

| case | prescribed `theta_c` | `angle(F, n_w)` at the contact line |
|---|---:|---:|
| case-04 droplet | 60 / 90 / 120 | 64.9 / 94.2 / 122.0 deg |
| case-07 slit, low-y wall | 60 | 62.7 deg |
| case-07 slit, high-y wall | 60 | 62.7 deg |
| case-07 slit, both walls | 120 | 118.6 deg |

So the driver's own claim — the closure imposes `angle(F, n_w) = theta_c` — is
correct. The defect is in what that angle *means*.

I established the meaning three independent ways.

**(a) An exact synthetic cap.** A drop resting on the wall `z = 0` with contact
angle `theta` measured through the drop phase is a spherical cap whose sphere
centre sits at `z_c = -R cos(theta)` (hemisphere at 90 deg, one-point touch at
180 deg, vanishing film at 0 deg). Feeding exactly that cap to the frozen
instrument:

| true theta (through the drop) | sphere centre used | instrument returns |
|---:|---:|---:|
| 30 | -6.928 | **150.0** |
| 60 | -4.000 | **120.0** |
| 90 | 0.000 | 90.0 |
| 120 | +4.000 | **60.0** |
| 150 | +6.928 | **30.0** |

The instrument returns `180 - theta`. Its own unit checks build the reference cap
with `z_c = +R cos(ang)` — the opposite side — so
`instrument.circle_fit_recovers_60deg` passes by construction and cannot detect
the fault. The check is circular.

**(b) The raw droplet geometry.** From the retained `theta{60,90,120}_final.npz`
I recomputed the contour and the circle fit. For prescribed 60 deg the fit gives
`R = 6.68`, `z_c = 4.95` with the wall at `z = 1`, and `psi()` at
`(cx, cy, z = z_c)` is **+0.997** — the centre of curvature lies *inside* the
red phase, so the drop is a bead. The standard cap relation
`cos(theta_liquid) = -(z_c - z_wall)/R` then gives:

| prescribed | driver's instrument | theta through psi>0 (correct) | 180 - instrument |
|---:|---:|---:|---:|
| 60 | 53.71 | **125.96** | 125.96 |
| 90 | 84.30 | **95.95** | 95.95 |
| 120 | 112.71 | **67.18** | 67.18 |

Equivalently, the prescribed-60 droplet has cap height / contact radius
`h/a = 1.79`, i.e. `tan(theta/2) = 1.79`, i.e. `theta ~ 121 deg`. It is a
bead, not a wetting film.

**(c) The slit and the Jurin box.** Both are consistent with (a) and (b); see
§4 and §5.

### 2.3 Consequence for the unit-check suite

`test_lattice_tables.py` contains the check block
`convention.secant_fixed_point_{60,90,120}_from_*`, whose comment states:

> "the specified analytic branch: F = (-sin t, 0, cos t) with n_w = +z gives
> angle(F, n_w) = t, **which is the angle through the liquid**"

That asserted equivalence is precisely what the raw fields refute: with
`n_w = solid -> fluid`, `angle(F, n_w) = 180 - theta_liquid`. The check verifies
that the secant converges to the requested branch — true and useful — but it
also asserts the physical meaning of that branch, and it asserts it backwards.
`convention.flipped_nw_is_complementary` tests the same relation with a 25 deg
tolerance on a mean, which cannot resolve a 180 - theta mapping either.

So the answer to the contract's section A is: the sign is no longer *arbitrary*
— it is now derived and documented — but it is derived on the wrong side, and
the whole wetting section of the validation matrix inherits that.

---

## 3. Contact-angle case (case-04) — the PASS is an artifact of the instrument

Numbers, from the retained raw fields, independent of the driver's fit:

| quantity | value |
|---|---|
| contour points | 10 / 8 / 6 for 60 / 90 / 120 (my re-extraction; driver: 20 / 16 / 12 with sub-grid sampling) |
| fitted `R`, `z_c` (60 deg) | 6.676, 4.973 |
| `psi()` at the fitted centre (60 deg) | **+0.997** (inside the red phase) |
| driver's reported angle | 53.71 / 84.30 / 112.71 |
| angle through psi>0 | **125.96 / 95.95 / 67.18** |
| absolute error through psi>0 | **66.0 / 5.9 / 52.8 deg** |

Against the case's own gate (`max_angle_err_deg = 15`), the errors through the
liquid fail by a wide margin at 60 and 120 deg and barely pass at 90 deg. The
verdict should not be PASS.

Two related artifact facts:

- the "expected" column in the case-04 README is `within 15 deg`, and the
  `fit_rms` / `fit_rms_geom` values that the (changed) fit-quality gate uses are
  **not shown in the README at all** — they exist only in `metrics.json`;
- the case-04 README's `Standard / reference result` block prints the prose
  before the governing relation, and the relation appears below the prose in a
  code block. The gate that the case actually applied is nowhere stated.

The figure set is honest about what it draws: `fig1_field` overlays the solid
mask and the `psi = 0` contour, `fig2_observable` plots measured vs prescribed,
`fig3_residual` plots the absolute error. There is **no fitted-circle overlay
and no angle wedge**, so the rendering does not let a reader see the reading
that decides the verdict. `VALIDATION_ARTIFACT_SPEC.md` §6.B asks for a
"measured vs prescribed theta **+ interface contour overlay**"; the contour is
there, the fitted circle is not.

On the gate question the contract asks: the acceptance gate for this case was
**changed after the first run had already reached the gate-evaluation line**
(`max_fit_rms = 0.5` -> `max_fit_rms_geom = 0.30`). The change is defensible on
dimensional grounds and moves in the strict direction, both metrics are
retained for every angle, and both pass anyway (`fit_rms_geom` =
0.071 / 0.050 / 0.038). I do not treat this as gerrymandering. I do treat the
undisclosed `NOT edited afterwards` docstring and the false "recorded in
case-04's README" claim as a provenance defect.

---

## 4. Slit capillary-pressure case (case-07) — geometry now valid; the verdict is misclassified

**Geometry, checked first, from the raw solid mask and phase field.**

`case_07` builds `slit_transverse(28,14,10,wall=2)`: solid at `y < 2` and
`y >= 12`, plus `x < 2` and `x >= 26` sealed, `z` periodic. The interface is a
`yz` plane at mid-`x`. Therefore:

- the plates are **transverse** to the meniscus (their normals are `±y`, the
  meniscus normal is `x`) — the pass-3 geometry defect is genuinely fixed;
- the interface **does** intersect both plates; the wetting condition is active
  there (I measured `angle(F, n_w) = 62.7 deg` at both contact lines for
  prescribed 60 deg);
- there is **no hidden periodic second interface**: `x` is sealed at both ends
  and the field is `z`-invariant. I verified `z`-invariance directly — the
  contour is bit-identical at `z = 3, 5, 7`.

So the R2 blocker's required redesign was delivered. This is a real improvement
over pass 3.

**Recomputed quantities.**

| prescribed | `Pc = p_gas - p_liquid` (my recompute) | `2 sigma cos(theta)/h` | ratio |
|---:|---:|---:|---:|
| 60 | **-2.0463e-03** | +2.0000e-03 | -1.023 |
| 90 | -4.2170e-07 | ~0 | (null, 0.02 % of scale) |
| 120 | **+2.1620e-03** | -2.0000e-03 | -1.081 |

These reproduce the committed `metrics.json` exactly.

**Required sanity structure.**

| requirement | observed | verdict |
|---|---|---|
| 60 deg -> sign consistent with positive `cos(theta)` | negative | **FAIL** |
| 90 deg -> `Pc` approximately zero | `4.2e-07` against a `2e-03` scale = 0.02 % | PASS |
| 120 deg -> sign reversal | positive (reversed the right amount, wrong direction) | **FAIL** |

**What the meniscus actually does.** Contour `x(y)` at the mid-`z` slice,
independently extracted:

| prescribed | near-wall `x` (y = 2..4) | centre `x` (y = 6..8) | difference |
|---:|---:|---:|---:|
| 60 | 13.235 | 13.904 | **-0.669** |
| 90 | 13.500 | 13.500 | 0.000 |
| 120 | 13.777 | 13.068 | **+0.708** |

For a wetting liquid the meniscus advances along the wall; for prescribed 60 deg
it recedes instead, and the 120 deg arm advances. Fitting the arcs gives
`|theta| ~ 66` and `~64 deg` respectively — the **magnitude** is right at both
angles and the **side** is swapped, exactly the complement signature. The
measured `Pc` sign follows: `Pc_meas = -Pc_theory(theta_prescribed) =
+Pc_theory(180 - theta_prescribed)`.

**Verdict classification.** The geometry is valid — no contact-line absence, no
periodic second interface, a genuinely curved contact-line-governed meniscus of
the right magnitude. Per the contract ("If the geometry is still incapable …,
classify it as `INVALID_TEST`, not a solver failure"), this case must **not** be
`INVALID_TEST`. The driver emits `INVALID_TEST` precisely when the sign test
fails (`verd = "PASS" if ok else ("FAIL_SOLVER" if sign_ok else "INVALID_TEST")`),
so its verdict logic maps the solver outcome onto the test-design label. The
correct label here is `FAIL_SOLVER`, caused by the convention.

Two secondary artifact problems in this case:

- the README's "Actual result" rows print `ok` for 60 deg and 120 deg even
  though the row label says the criterion includes `Pc sign of cos(theta)` —
  the row-level test uses `abs(pc_ratio)` and drops the sign;
- `|ratio|` inside the markdown table row breaks the table into spurious extra
  columns in the rendered README.

**Answer to the contract's section C:** the slit test is now physically valid
and must be kept; it currently fails, and the failure is the convention, not the
geometry. This case is the strongest single piece of evidence in the pass — it
is the measurement that *shows* the sign fault, and it was read as an invalid
test instead.

---

## 5. Jurin equilibrium case (case-08) — reachable configuration, wrong verdict reason

**Reachability precheck, recomputed independently** from
`case_08(n=(20,16,48), wall=4, neck=18, theta=60, g=3e-4, z_res0=14, z_cap0=20)`:

```text
gap h                    = 16 - 2*4                     = 8
dh_theory = 2*sigma*cos(theta)/(rho*g*h)
          = 2*0.02*0.5/(1*3e-4*8)                       = 8.3333 lu
A_res = 20*16 = 320 ; A_cap = 20*8 = 160
vol   = 320*14 + 160*(20-18)                            = 4800
M     = (vol - A_cap*(dh - neck))/(A_res + A_cap) = (4800 + 1546.67)/480 = 13.222
L     = M + dh                                          = 21.556
predicted capillary level inside [18, 46] ?              YES  (21.56)
predicted reservoir level inside [1, 18] ?               YES  (13.22)
```

The precheck is correct and passes, and the initial condition deliberately
places a **connected** liquid column already inside the capillary
(`psi[:, wall:n1-wall, neck:z_cap0] = +1`). So the previous pass's unreachable
entrance is genuinely fixed.

**Raw fields, initial / intermediate / final (centre column `(10, 8, z)`):**

| time | `psi` at `z = 18..24` | capillary level | reservoir level | rise |
|---|---|---:|---:|---:|
| `t0000` | `[+1.00, +1.00, -1, -1, -1, -1, -1]` | 19.0 | 13.0 | 6.0 |
| `t_mid` | `[-0.97, -0.99, -1, -1, -1, -1, -1]` | NaN | 14.0 | NaN |
| `t_final` | `[-0.97, -0.99, -1, -1, -1, -1, -1]` | NaN | 14.0 | NaN |

The liquid is **expelled** from the capillary and returns to the reservoir
(which rises 13 -> 14). Total red mass is exactly conserved
(`rho_r.sum() = 4480.0000` at every snapshot). A prescribed *wetting* angle of
60 deg driving the liquid *out* of a capillary is the direct macroscopic
signature of the inverted convention; the same closure that makes the droplet a
bead makes the capillary non-wetting.

`rise = NaN` is produced by a genuine absent-interface branch
(`wi = np.where(fcap & (cap > 0))`, `nan` when empty), not by a fallback, so the
observable itself is honestly reported. What is misattributed is the *cause*:
the `INCONCLUSIVE` verdict and the atlas's "the capillary level is still not
measurable" present this as a measurement/reachability limit, when the raw field
shows the configuration works and the solver empties the tube.

**Answer to the contract's section D:** the configuration is valid and
reachable; the observable is absent for a physics reason. This should be
`FAIL_SOLVER` (or `INCONCLUSIVE` with the cause named), not an unreachability
finding.

---

## 6. Laplace validation (case-03) — executor's claim CONFIRMED, with one mislabelled output

Independent recomputation from the retained raw droplets
(`equivalent_radius` on `psi > 0`, `Delta p = (rho_in - rho_out)/3` with the
same `R ± 3.5` masks):

| `R_nominal` | `R_measured` | `2/R` | `Delta p` | `sigma_local` |
|---:|---:|---:|---:|---:|
| 6 | 5.869461618 | 0.340746755 | 7.196036513e-03 | 0.021118430 |
| 7 | 6.868001997 | 0.291205506 | 6.066728998e-03 | 0.020833153 |
| 8 | 7.909886120 | 0.252848141 | 5.219724768e-03 | 0.020643714 |
| 9 | 8.891988587 | 0.224921566 | 4.579951123e-03 | 0.020362437 |

Every digit matches the committed `metrics.json`. Regressions:

```text
free intercept   sigma = 0.02253835   ratio to sigma_input = 1.1269   intercept = -4.872e-04
zero intercept   sigma = 0.02082427   ratio                 = 1.0412
R^2 (free fit)                                          = 0.999956
residuals (dp - fit) = [+3.38e-06, -9.35e-06, +8.16e-06, -2.20e-06]
gate (0.90..1.10, R^2>0.95, |intercept|<0.25*mean dp)  -> FAIL
```

So the executor's summary of this case is **correct and I confirm it**:
Laplace linearity is very strong, the scale is +12.7 % relative to the input,
and the case honestly FAILS its predeclared calibration gate.

Also confirmed: `A = (9/4) omega_eff sigma` is **not** retuned. The code has
`A = 2.25 * omega * sigma` with `coeff_mode="paper"` and a comment recording the
earlier `1.5` slip; the commit that fixed it (`7159cf5`) predates every pass and
nothing on the path has changed since.

One output is mislabelled. `sigma_extrapolated_large_R = -2.4287e-04` is
reported in `metrics.json`, the README and `VALIDATION_REPORT.md` as the
`1/R -> 0` limit. It is not: the code fits `sigma_local` against
**`R_measured`** (`A2 = [1/sx, 1]` where `sx = 1/R_measured`, so `1/sx = R`) and
stores the **slope**. The slope of `sigma_local` against `R` has units of
sigma/length and is not a surface tension. The actual large-`R` behaviour is the
opposite of stable: `sigma_local` falls monotonically (0.02112 -> 0.02036) with
no levelling, and the intercept-based extrapolation lands on ~0.0226, i.e. the
offset does not disappear at large `R`. So no stable infinite-radius
extrapolation exists to accept, and the pass-3 ambition of "a larger-radius /
multi-resolution study is preferable to retuning `A`" has now been attempted
and does not close the offset.

---

## 7. Mechanical-sigma diagnostic (case-11) — derivation closes, measurement does not, and it cannot be recomputed

**Derivation audit (`MECHANICAL_SIGMA_DERIVATION.md`).** I re-derived the
prefactor by hand from R1 Eqs. (16) and (18) with the D3Q19 weights:

```text
sum_i dN_i c_a c_b = A|F| [ (1/9)(delta_ab + 2 n_a n_b) - delta_ab/3 ]
                   = (2/9) A|F| (n_a n_b - delta_ab)                    (star)
n = z  ->  dPi_zz = 0 ,  dPi_xx = -(2/9)A|F|  ->  P_N - P_T = (2/9)A|F|
int |F| dz over one monotone -1 -> +1 profile = 2
sigma_mech = (4/9) A = (4/9)(9/4) omega_eff sigma = omega_eff sigma
```

The algebra is right, the sign is right (`P_N - P_T > 0` for a stable
interface), the unrelaxed post-collision perturbation is verifiable in
`solver.step()` (step 4 adds `dN` to `N` directly, and the recolouring is
colour-blind so it contributes nothing to the total second moment), and the
`omega_eff = 1` at `nu = 1/6` is correct. Nothing is fitted. I accept the
prefactor as source-closed.

**But the measured number does not sit on those premises.** The case is
`n = (6,6,64)`, `psi = -tanh((z-32)/2.5)`, periodic in `z`. From the retained
`t_final.npz`:

```text
psi at z = 0 is +0.2623 and at z = 63 is -0.2623
total variation of psi over the PERIODIC centreline = 4.000
continuum value for ONE monotone interface          = 2.000
=> the periodic box contains TWO full interfaces, not one
the declared bulk window slice(2,8) has psi = 0.889 … 0.9998
the |psi| > 0.999 plateau starts at z = 6
=> the "bulk" reference window sits on the shoulder of the wrap interface
```

The derivation integrates over a window assumed to hold one interface with two
clean bulk regions; the implemented geometry holds two interfaces and a
reference window that is not in the bulk. A `sum` over all 64 nodes with a
non-zero baseline anisotropy offset accumulates 64 times that offset, which is
the right order to explain a 23 % miss.

I could **not** recompute the `P_N - P_T` profile, the cumulative integral or
the final `sigma_mech` from the committed artifact, because
`artifact.snapshot()` stores `solid, psi, rho_r, rho_b, rho, vel, speed` and
**not the distributions `N_r`, `N_b`**, and the momentum-flux tensor
`Pi_ab = sum_i N_i c_ia c_ib` is not a function of those fields. The
`render_manifest` for case-11 points `fig2_observable` and `fig3_residual` at
`raw/t_final.npz`, but that file cannot regenerate them. Reconstructing `Pi`
from the equilibrium would assume the answer.

**Verdict.** Because the measurement does not satisfy the derivation's premise
and cannot be independently recomputed, the PASS is not supportable as stated.
The doc's own §8 already records the 23 % gap and lists untested candidate
causes; the honest label for the number as produced is `EXPLORATORY / UNGATED`
until the geometry matches the derivation.

**The executor's cross-check claim is nevertheless CONFIRMED as a discrepancy.**
`sigma_laplace ~ 1.13 sigma_input` and `sigma_mech ~ 0.77 sigma_input` differ by
about 1.47, and I verified both numbers from raw data independently. The
derivation does **not** support a single calibration prefactor: the mechanical
route has no free parameter at all, and the Laplace route has no plausible
uniform rescaling that would move one up and the other down. So the pair of
measurements genuinely rules out a uniform prefactor change on the perturbation
— as a constraint that is a real result. It does **not** yet locate the cause.

---

## 8. Beta / positivity (case-05) — PASS, confirmed

From the committed `metrics.json`, independently consistent with the raw
`beta*_final.npz` snapshots:

| beta | width [lu] | `|psi|`max | `rho_r`min | `rho_b`min | valid |
|---:|---:|---:|---:|---:|---|
| 0.0 | 20.0 | 0.0573 | 0.5026 | 0.4713 | excluded (dissolution) |
| 0.5 | 1.838715 | 0.9970 | 0.00229 | 0.00150 | valid |
| 0.7 | 1.469026 | 0.99987 | 1.26e-04 | 6.7e-05 | valid |
| 1.0 | 1.123045 | 1.0000 | 0.0 | 0.0 | valid |
| 1.5 | 0.664671 | **1.01684** | **-7.673e-03** | **-8.419e-03** | excluded (positivity) |
| 2.0 | 0.404773 | **1.11409** | **-5.705e-02** | **-5.461e-02** | excluded (positivity) |

Width falls monotonically across the valid subset, β = 1.5 and 2.0 are excluded
on both the order-parameter bound and negative component populations rather than
being counted as "sharp interfaces", and β = 0.0 is separately excluded for
dissolution. Negative component minima are reported, so no clipping hides the
violation. This is exactly what the contract's section D-adjacent requirement
asks for. **PASS.**

---

## 9. Dynamic axis symmetry (case-06) — correctly labelled

- arms `(32,16,16)` wave along `x` and `(16,32,16)` wave along `y`, mode 2, both
  with lattice wavelength `32/2 = 16` — equal, and `equal_wavelength: true`;
- the tracked observable is `fourier_mode_amplitude` (mode 2 of the
  interface-height field), not an averaged maximum;
- `amplitude_asymmetry = 1.589207e-13`;
- `metrics.json` carries `scope: "axis symmetry on a cubic lattice, not general
  rotational isotropy"` and the README repeats it.

The two arms remain exact `x <-> y` transposes, so the tiny asymmetry is best
read as an x/y axis-symmetry regression rather than evidence about arbitrary
orientations — which is precisely how the artifact labels it. **PASS with the
stated scope.** A 45 deg arm would give the case real isotropy content.

---

## 10. Complex-wall case (case-09) — global conservatism confirmed; attribution correctly withheld

- **box closure:** `assert_closed_box` reports `x_minus/x_plus/y_minus/y_plus`
  all `true`; the mask closes all four lateral faces, so the periodic wrap
  cannot carry fluid across.
- **global mass history:** `max_red_excursion = 2.749e-13`,
  `max_blue_excursion = 2.745e-13`, late-window rates `-2.42e-13` and
  `-2.56e-13` per step, final drifts `3.63e-10` / `3.84e-10`. **The old
  catastrophic ~7 % global mass source is gone.** That is a large, real
  improvement and it survives into this pass.
- **wall-band mass history:** `wall_band_red_relative = -0.068308` (-6.83 %),
  which fails the predeclared 2 % gate.
- **attribution:** `metrics.json` records "wall-band change is NOT attributed to
  wall mass transfer; no stationary reference case was run", and the README says
  the same. I did not find any statement anywhere in the pass-4 artifacts that
  calls the wall-band redistribution nonphysical. **The contract's prohibition
  is respected.**
- **contact-line / interface-position metric:** still absent. The R2 review
  asked for one "as originally promised"; the pass-4 README does not claim one
  (so the previous review's R-7 overclaim is fixed), but the promised observable
  is also not delivered. The final state is a single connected component
  (`n_components_final = 1`, size 1100), which is reported.

So both halves of the contract's section G hold: global closure is good and the
attribution claim is properly withheld. The `FAIL_SOLVER` label on the wall-band
gate is defensible but sits uneasily with the same document's statement that the
change is not attributable — a failure of an unattributed gate is not yet a
solver failure. `INCONCLUSIVE` would be more honest for this row.

---

## 11. Visualization / artifact integrity — the binding is real, the data is not published

**What is good, and verified rather than assumed.** I regenerated three
committed field figures from the retained raw arrays using the production
plotting helper (`artifact.Case.fig_field_slice`), with the manifest's own
`plane`/`slice_index`:

| figure | result |
|---|---|
| `case-07/figures/fig1_field.png` | **pixel-identical**, `max|Δ| = 0` |
| `case-04/figures/fig1_field.png` | **pixel-identical**, `max|Δ| = 0` |
| `case-08/figures/fig1_field.png` | 99.82 % of pixels identical, `max|Δ| = 72` (a few contour-line pixels, from f32-vs-f64 contour crossing) |

So the figures genuinely come from the raw fields they name, the manifest
bindings are real, and `RdBu_r` with `vmin/vmax = ±1` does encode
`+psi = red = liquid`. Every case has three figures (field, observable,
residual), all eleven READMEs carry the five required blocks, and every case has
`metadata.json`, `metrics.json`, `metrics.csv`, `render_manifest.json` and
`reproduce.py`. Invalid and inconclusive cases (07, 08) are rendered rather than
hidden.

**The blocking defect: the raw fields were never committed.** `git ls-files`
returns nothing under any `raw/` directory and `find` finds zero `.npz` in the
committed pass-04 tree. The cause is `.gitignore` line 9, `*.npz`, which is
repo-wide; the Pass-4 work added a narrow negation for a previous task
(`!results/colour_closure/**/*.npz`) but none for
`results/leclaire_cg/pass-04/**/raw/*.npz`. `git check-ignore -v` confirms:
`results/leclaire_cg/pass-04/case-07-…/raw/theta120_final.npz` matches
`.gitignore:9:*.npz`. The files do exist, untracked, in the executor worktree:
39 files, 3.9 MB, most of it in case-03 (2.2 MB) and case-04 (1.4 MB). All
**33** `render_manifest.source_raw` references resolve against that untracked
tree and **none** resolve against the repository.

Consequences:

1. `docs/research/leclaire_cg/VALIDATION_ATLAS.md` claims "This is the first
   pass that retains raw fields and renders figures for every case, per
   `VALIDATION_ARTIFACT_SPEC.md`". For the delivered artifact this is **false**.
2. `VALIDATION_ARTIFACT_SPEC.md` §5.2, §6 and §8 are unmet: no publication-facing
   figure is reproducible from the repository, and §12's promotion gate ("every
   headline field claim has retained raw data and rendering") cannot be signed.
3. This is the *same* trap as the previous colour-closure task, which needed the
   same kind of negation. `.gitignore` was edited in this very branch (to add the
   `_refs/` rule) without noticing that it was also eating the evidence.

**Secondary artifact gaps.**

- no per-case `logs/` (the layout requires `logs/` and §5.1 requires a run log
  per run); only the aggregate `results/pass04_run.log` and
  `results/pass04_rerun.log` are retained;
- `run_manifest.json` records a single `command` for a tree that was produced by
  two different commands (see §1.1);
- case-11's `fig2`/`fig3` name a raw file that cannot regenerate them (§7);
- the contact-angle case has no fitted-circle overlay or angle wedge (§3).

**Answer to the contract's section H:** partly. The figure-to-raw provenance is
real and verified; the repository does not contain the raw provenance. A visually
plausible figure with a manifest that points at an uncommitted file is not
durable evidence.

---

## 12. Durable-document consistency — mostly fixed; two required corrections are still missing

Corrected since the previous pass, verified in the current files:

| item | status |
|---|---|
| pass-1/2/3 claims marked superseded | **FIXED** — `EXECUTION_REPORT.md` §0 states "Every section below section 0 is a historical record and is explicitly `SUPERSEDED`"; §1 is headed "(SUPERSEDED — pass-1/2/3)"; §5b and §6 carry "[SUPERSEDED by pass-04]"; `VALIDATION_REPORT.md` and the atlas say the same |
| pass-4 is the current headline | **FIXED** — §0 of the report, the atlas's "Pass-04 — CURRENT" section, and `pass-04/VALIDATION_REPORT.md` |
| Table-IV ordering consistently non-shell-major | **FIXED** — `CURRENT_VS_LECLAIRE_MAP.md` row 2 and §78, `PAPER_FORMULATION.md` §0.1, `lattice.py` all state the non-shell-major reading |
| R5 mapping one current status | **FIXED** — `PAPER_FORMULATION.md` §4.2 and §11 and `CURRENT_VS_LECLAIRE_MAP.md` all carry `UNRESOLVED`; the old §11 `CLOSED` is gone. `REFERENCE_MANIFEST.md`'s "CLOSED, no URL" is the OA-status column, not the mapping |
| "Laplace RESOLVED" not presented as current | **FIXED at section level** — the surviving `RESOLVED` row sits inside §1, which is banner-marked superseded. A row-level marker would be better, but the banner is unambiguous |
| atlas and machine-readable SUMMARY agree | **AGREE** — both give `PASS 7, FAIL_SOLVER 2, INVALID_TEST 1, INCONCLUSIVE 1` and the same per-case verdicts |
| candidate / evidence SHAs current | **PARTLY** — `EXECUTION_REPORT.md` §0 and `pass-04/VALIDATION_REPORT.md` carry `0b3da4e`. `RESULTS/leclaire_cg/PROVENANCE.md` still reports "control tip read `1c4f1a4`", "unit checks 59/59", "matrix FAIL 3, INCONCLUSIVE 2, PASS 5" — pass-3 numbers with no superseded banner in the file, and `results/leclaire_cg/summary.json` and `UNIT_CHECKS.log` are likewise pass-3 |

**The two required corrections that were not applied.** Both were listed as
R-3 items in the previous fresh review and repeated in external review R2 §8,
which required: "acquisition route must have one current provenance statement".

1. `docs/research/leclaire_cg/REFERENCE_MANIFEST.md`, closing paragraph:

   > "The acquisition note at the top of this file (that 科研通 tooling does not
   > exist on this machine) still applies; R5 was obtained by local search
   > rather than by download."

   This is the exact sentence R2 §8 required removed. It is in the present
   tense, it is not marked retracted, and it directly contradicts the same
   file's corrected note 150 lines earlier and its own R5 row
   (`route used: 科研通`).

2. `results/leclaire_cg/PROVENANCE.md`, "Known weaknesses" item 4:

   > "R5 in particular was obtained **late**, after the first validation pass,
   > by local search rather than download"

   The same file, 65 lines earlier, says: "The earlier claim that 科研通 could
   not be driven from this session was wrong and is retracted. R5 was obtained
   via the `ablesci-paper-download` skill by DOI on 2026-09-27". Two
   contradictory statements live in one file.

A reader who opens only `REFERENCE_MANIFEST.md` or only `PROVENANCE.md` still
cannot recover the current truth, which is the test R2 §8 set.

---

## 13. Independent rerun

**Unit checks.** `tests/leclaire_cg/test_lattice_tables.py` reruns to
73/73 from the frozen candidate (pass 3 was 59/59), and my log is
**byte-identical** to the committed
`results/leclaire_cg/pass-04/UNIT_CHECKS.log`:

```text
$ diff my_unit_run.log <committed pass-04 UNIT_CHECKS.log>   ->  (empty)
73/73 checks passed
```

**Pass-4 matrix.** I ran `pass04.CASES[idx]` in the driver's own order, with the
driver's own `write_validation_report`, from a byte-exact `git archive` copy of
`0b3da4e` (`out_frozen/`) and, for the two cases the candidate cannot execute,
from a byte-exact copy of `ca10d65` (`out_tip/`). The frozen candidate tree was
never written to.

| case | committed verdict | my rerun | metric fields compared | bit-exact |
|---|---|---|---:|---:|
| case-01 | PASS | PASS | 5 | 5 |
| case-02 | PASS | PASS | 6 | 6 |
| case-03 | FAIL_SOLVER | FAIL_SOLVER | 46 | 46 |
| case-04 | PASS | PASS (tip harness) | 30 | 30 |
| case-05 | PASS | PASS | 47 | 47 |
| case-06 | PASS | PASS | 40 | 40 |
| case-07 | INVALID_TEST | INVALID_TEST (tip harness) | 31 | 31 |
| case-08 | INCONCLUSIVE | INCONCLUSIVE | 18 | 18 |
| case-09 | FAIL_SOLVER | FAIL_SOLVER | 17 | 17 |
| case-10 | PASS | PASS | 14 | 14 |
| case-11 | PASS | PASS | 8 | 8 |
| **total** | | | **262** | **262** |

Every float in every `metrics.json` reproduces with `a == b` exact equality —
not "close", identical. Verdicts reproduce exactly. The committed evidence is
therefore a faithful record of what the frozen solver produced; the defects in
this review are in the design and the documentation, not in the recording.

The three harness defects in §1.1 I also reproduced from the frozen candidate
directly, rather than relying on the committed log:

```text
GATES['04_contact_angle'] at 0b3da4e = {min_contour_pts: 6, max_fit_rms: 0.5,
                                        max_angle_err_deg: 15.0, min_snapshots: 3}
case_04(...) -> KeyError: 'max_fit_rms_geom'
case_07(...) -> ValueError: operands could not be broadcast together with
                            shapes (1,28,1) (28,14,10)
pass04.py: `if __name__ == '__main__':` at line 1130,
           `def write_validation_report` at line 1134  -> NameError at exit
```

**Figure pipeline.** Three committed field figures were regenerated from the
retained raw arrays and matched to `max|Δ| = 0` (case-07), `0` (case-04) and
99.8 % (case-08); see §11.

---

## 14. Answers to the required review questions

**1. Is `L17_CORE` now faithful to the cited Leclaire-2017 formulation in the
implemented D3Q19 / unit-density scope?**

Everything except the wetting-condition sign. The lattice tables, the MRT basis
and its row identities, Eq. (4) with the corrected `u·grad(rho)` term, the
`X_W` 1-D Cartesian gradient path, Eq. (16) with `A = (9/4) omega_eff sigma`,
the recolouring pair structure with the rest population untouched, the
`lambda = 1/2`, `n = 2` secant, the three-pass D3Q27 smoothing and the
seven-step ordering all check out against the source I read directly. The
outstanding item is that the R1 wall normal `n_w = grad(g)` (textbook p. 9) is
implemented as its negation, and the wetting condition built on it therefore
realises the complementary angle. So: faithful in every element I could verify
individually, and wrong in exactly one place — the one this pass claimed to
have frozen.

**2. Is the wetting phase / contact-angle convention now unambiguous and
internally consistent?**

Unambiguous, yes: `WETTING_PHASE_CONVENTION.md` is explicit, and the code's
default is derived rather than arbitrary. Internally consistent, **no**. Three
documents and one instrument disagree:

- R1 defines `n_w = +grad(g)` (fluid -> solid);
- the convention document and `solver.py` use `n_w = -grad(g)/|grad(g)|`
  (solid -> fluid);
- the measurement instrument returns `180 - theta_liquid` while documenting
  itself, and being labelled in `metrics.json`, as "theta measured through
  psi>0 liquid/red";
- the unit tests assert that `angle(F, n_w) = t` *is* the angle through the
  liquid, which the raw fields refute.

**3. Do the contact-angle results quantitatively validate the Leclaire wetting
condition?**

**No, and the reported result is inverted.** Measured through the liquid, the
prescribed 60 / 90 / 120 deg arms give 126.0 / 96.0 / 67.2 deg — errors of
66.0 / 5.9 / 52.8 deg against a 15 deg gate. What the pass actually
demonstrates is that the closure realises `180 - theta_c` with good
repeatability (the closure is active, the magnitude is close, only the side is
wrong). The underlying wetting machinery is probably sound; the convention it
is fed is not.

**4. Is the slit Pc test now a valid physical test, and does it pass?**

Valid — **yes**, verified from the mask and the field: walls are transverse to
the meniscus, the interface intersects both plates, the wetting condition is
active at both contact lines, the field is `z`-invariant so there is no hidden
periodic second interface, and the meniscus is genuinely curved with `|theta| ~
65 deg`. It does not pass: the sign is inverted at 60 deg and at 120 deg, while
the 90 deg null is excellent (`4.2e-07` against a `2e-03` scale) and the
magnitudes are right to 2-8 %. The correct verdict is `FAIL_SOLVER` caused by
the convention, **not** `INVALID_TEST`.

**5. Is the Jurin test now valid / reachable, and does it pass?**

The configuration is now valid and reachable — I recomputed the precheck by
hand (`dh = 8.333`, `L = 21.56` inside `[18,46]`, `M = 13.22` inside `[1,18]`)
and the initial condition really does place a connected liquid column inside
the capillary. It does not pass, and the reason is not the configuration: the
prescribed wetting 60 deg arm **expels** the liquid from the tube
(`psi` in the capillary goes from `+1` to `~-1`, the reservoir rises, total red
mass is exactly conserved). The `INCONCLUSIVE` verdict is honest about the
missing observable but misattributes the cause.

**6. What does the Laplace + mechanical-sigma combination actually imply about
the remaining sigma-scale error?**

It rules out a single global prefactor, and I confirm both estimators
independently from raw data: Laplace gives `sigma_fit/sigma_input = 1.1269`
with `R^2 = 0.999956`, and the mechanical integral gives `0.768`. The mechanical
route has no free parameter (the moment algebra closes and `A` is not retuned),
so a uniform rescaling of the perturbation cannot move the two in opposite
directions. That is a genuine constraint and the most valuable thing this pass
produced. It does **not** yet identify the cause, and the mechanical number
itself is not trustworthy as a measurement: its geometry contains two
interfaces instead of one, its "bulk" reference window sits on the interface
shoulder, and it cannot be recomputed from the artifact at all (the
distributions are not stored). So the honest current state is: the Laplace
offset is real, unexplained, not a uniform prefactor, and the diagnostic that
would localise it is still uncalibrated.

**7. Is the complex-wall case globally conservative, and is the wall-band
behaviour attributable?**

Globally conservative: **yes**, and much better than before — component
excursions are `2.7e-13` and late rates `~2.5e-13` per step, so the old ~7 %
global mass source stays eliminated. Attributable: **no**, and the artifacts say
so explicitly — "wall-band change is NOT attributed to wall mass transfer; no
stationary reference case was run". No document claims otherwise. The
`-6.83 %` wall-band change therefore remains an unexplained gate failure rather
than a diagnosed defect, and given the Pc and Jurin evidence in this pass, a
convention-driven interface reorganisation is now a live candidate explanation
that was not available before.

**8. Are the Pass-4 raw-data / rendering artifacts sufficient for durable,
publication-facing validation?**

**No.** The rendering side is in good shape — figure-to-raw binding is verified
pixel-exact, every case has the five required README blocks, primary and
residual plots, and invalid cases are rendered rather than hidden. The raw-data
side fails: not one `.npz` is committed, so all 33 manifest bindings point at
files that exist only on the executor's disk, and the atlas's claim that this is
the first pass to retain raw fields is false for the delivered package. Two
further gaps: no per-case run logs, and the mechanical-sigma observable is not
a function of anything that was retained.

**9. Are there any stale contradictory scientific claims left?**

Yes, two, both of them previously flagged and both about the 科研通 route for
R5: the closing paragraph of `REFERENCE_MANIFEST.md` and item 4 of
`PROVENANCE.md`'s "Known weaknesses". Both still say R5 came from "local search
rather than download" while the same files' corrected text says it came from
科研通 by DOI, with the byte count matched to the delivery record. Separately,
`PROVENANCE.md`, `summary.json` and `UNIT_CHECKS.log` still carry pass-3 numbers
(59/59, 5/3/2) with no in-file superseded banner, and the case-04 gate change is
not disclosed where the report says it is. The big structural clean-up R2 asked
for was done well; these are the leftovers.

**10. Is the NumPy/f64 reference-model validation stage ready to close?**

**No.** Closing the stage would certify that the wetting behaviour is validated
in the reference model. On the evidence: the contact-angle PASS is an instrument
artifact (three independent demonstrations), the slit Pc sign is inverted while
the geometry is now correct, and the Jurin tube is emptied by a prescribed
wetting angle. The wetting closure is probably correct and the convention it is
driven by is not — which is a much cheaper fix than it looks, but it is not
done, and the currently published headline says the opposite. The parts of the
stage that are genuinely close — isolation, R1 equation fidelity, the beta
positivity window, the axis-symmetry regression, the f64 conservation result
and the honest Laplace FAIL — should be preserved as they stand.

---

## Findings

### Blocking

**P4-1 — the wetting convention is the negation of the source's, so the closure
realises `180 - theta_c`, and every wetting result in this pass inherits it.**

R1 defines `n_w = grad(g)` with `g` the fluid-solid binary matrix
(PRE 95, 033306, p. 9), i.e. fluid -> solid. `WETTING_PHASE_CONVENTION.md` §3
and `solver.py` (`self.nw_sign = -1.0`) use the negation, and the implementation
imposes `angle(F, n_w) = theta_c`, verified at 64.9 / 94.2 / 122.0 deg for
prescribed 60 / 90 / 120 on the retained droplet fields. The physical result is
the complement, shown three ways: an exact synthetic cap returns
`180 - theta` (60 -> 120); the prescribed-60 droplet's fitted circle has its
centre inside `psi > 0` at `z_c = +4.95` above the wall, i.e. it is a bead, and
`cos(theta_liquid) = -(z_c - z_wall)/R` gives 126.0 / 96.0 / 67.2 deg; and the
slit and Jurin cases follow the same rule. Consequences: case-04's PASS is
invalid, case-07 is misclassified, case-08's cause is misattributed.
*Fix direction is determined*: with `g = 1` in solid and the already-frozen
"theta through liquid/red", the canonical normal must be `+grad(g)/|grad(g)|`
(the historical `wetting_sign = +1` arm), or equivalently the convention text
must define `n_w` as fluid -> solid; either way the realised liquid-side angle
must equal `theta_c`.

**P4-2 — `contact_angle_circle_fit` returns the gas-side angle and documents it
as the liquid-side angle, and its unit check is circular.**

`cos_t = (z_c - z_wall)/R` has the wrong sign for a drop resting on the `+z`
side of the wall; the correct relation is `cos(theta_liquid) =
-(z_c - z_wall)/R`. The docstring, the case-04 README, the `metrics.json` field
`phase_convention` and the pass-04 header all assert the wrong reading. The
synthetic unit checks build their reference cap with `z_c = +R cos(theta)` — the
same sign — so `instrument.circle_fit_recovers_{30,60,90,120,150}deg` passes by
construction. `convention.secant_fixed_point_*` additionally asserts that
`angle(F, n_w) = t` "is the angle through the liquid", which the raw fields
refute.

**P4-3 — the raw fields were never committed.**

`.gitignore` line 9 (`*.npz`, repo-wide) silently excluded all 39 snapshots;
the Pass-4 work added no negation for `results/leclaire_cg/pass-04/**/raw/`.
Zero `.npz` in the committed tree, 33 of 33 `render_manifest.source_raw`
references unresolvable from the repository, and the atlas's "first pass that
retains raw fields" claim false for the delivered artifact. Also the same
mistake the previous colour-closure task had to fix.

**P4-4 — the named frozen candidate cannot produce the evidence tree.**

`0b3da4e`'s `pass04.py` raises `KeyError: 'max_fit_rms_geom'` (case-04),
`ValueError` (case-07 broadcasting) and `NameError: write_validation_report`.
Cases 04 and 07 come from the later tip harness, with a renamed and tightened
case-04 gate. Disclosed in a `rerun_note`, but the module docstring still says
gates are never edited after results, `run_manifest.command` is wrong for two of
eleven cases, and `EXECUTION_REPORT.md` §0 says the gate change is "recorded in
case-04's README" when the README does not mention it.

**P4-5 — two required provenance corrections are still missing.**

`REFERENCE_MANIFEST.md` closing paragraph and `PROVENANCE.md` "Known weaknesses"
item 4 both still assert that R5 came from "local search rather than download",
contradicting their own corrected 科研通 records. Both were R-3 items in the
previous fresh review and were repeated in external review R2 §8.

### Non-blocking

**P4-6 — case-07's verdict logic maps the solver outcome onto the test label.**
`INVALID_TEST` is emitted exactly when the sign test fails, and `FAIL_SOLVER`
when the sign is right but the magnitude is off — the reverse of the contract's
semantics. The README's per-row status also prints `ok` for the 60 and 120 deg
rows whose stated criterion includes the `Pc` sign, and `|ratio|` inside the
table breaks the markdown.

**P4-7 — case-11's diagnostic does not sit on its derivation's premises and
cannot be recomputed.** The periodic box holds two interfaces (total variation
4.0), the `slice(2,8)` bulk window is on the wrap interface's shoulder, and
`N_r`/`N_b` are not retained, so `Pi_ab` — and therefore `fig2` and `fig3` —
cannot be regenerated. The PASS should be `EXPLORATORY_UNGATED` until the
geometry matches the derivation; the cross-check conclusion (no uniform
prefactor) survives regardless.

**P4-8 — `sigma_extrapolated_large_R` is mislabelled.** It is the slope of
`sigma_local` against `R_measured` (units sigma/length), not a `1/R -> 0`
limit. No stable infinite-radius extrapolation exists: `sigma_local` falls
monotonically without levelling.

**P4-9 — case-06 remains an x/y transpose regression.** Correctly labelled as
such, and strictly better than the old `max|psi|` comparison, but a 45 deg arm
would give it isotropy content.

**P4-10 — case-09 has no contact-line or interface-position observable.**
The previous docstring overclaim is gone (good), but the R2 request for the
promised observable is still unmet, and a gate whose behaviour the document
itself declines to attribute sits oddly under a `FAIL_SOLVER` label.

**P4-11 — small durable-record leftovers.** `PROVENANCE.md`, `summary.json` and
`UNIT_CHECKS.log` at the top level still carry pass-3 numbers with no in-file
superseded banner; `PROVENANCE.md` reports "control tip read `1c4f1a4`". The
case-04 README prints its `prose` before its `relation` and omits both the
fit-quality gate and its measured values; the pass-04 `VALIDATION_REPORT.md`
drops case-04's numbers entirely because `write_validation_report` keeps only
scalar metrics. No per-case `logs/` is retained although the layout and §5.1
require one.

---

## What should be preserved

These results are sound and should not be disturbed by the correction round:

1. isolation: production solver untouched, no Taichi/f32 port, no V3 /
   graphite / separator / PCS work, earlier passes not overwritten by Pass-4;
2. the R1 equation-level transcription and the D3Q19 tables, including the
   corrected Eq. (4) term and the `X_W` 1-D gradient path;
3. `A = (9/4) omega_eff sigma`, never retuned;
4. the honest Laplace FAIL with its measured radius, free- and zero-intercept
   fits, residuals and `R^2`;
5. the beta positivity window and the `beta = 1.5 / 2.0` exclusions;
6. the equal-wavelength Fourier axis-symmetry regression and its stated scope;
7. the f64 conservation closure and its explicit scope limitation;
8. the complex-wall global closure result (excursions `2.7e-13`) and the
   refusal to attribute the wall-band change;
9. the artifact machinery — README structure, render manifests, valid
   figure-to-raw bindings — once the raw files are actually committed;
10. the case-07 geometry redesign, which is a genuine fix.

---

## Declaration

- Reviewer session: fresh and independent. Executor transcript not read and not
  requested.
- The frozen candidate was not modified. All recomputation ran on byte-exact
  `git archive` copies staged under
  `.review_runtime/BI-CG-LECLAIRE-PASS4-001/`, outside every git worktree; the
  product branch was never written to.
- No GPU work, no production run, no Taichi execution.
- Files written by this review: this file and `FRESH_REVIEW_SESSION.json`, both
  published to `.agent/evidence/BI-CG-LECLAIRE-PASS4-001/` on
  `agent-dev/bilateral-episode-v0.1`.
- `PASS` was not available on this evidence. `HUMAN_REQUIRED` was considered and
  is not triggered: the defect is identified, the fix direction follows from the
  already-frozen phase convention plus the source's own `n_w` definition, and no
  new modelling decision is needed. The owner may wish to confirm in one line
  whether `WETTING_PHASE_CONVENTION.md` should be rewritten to state
  `n_w = +grad(g)/|grad(g)|` (fluid -> solid, matching R1) or keep the
  solid -> fluid wording and correspondingly flip the implemented sign; either
  outcome yields the same physics and the same realised `theta_liquid`.
