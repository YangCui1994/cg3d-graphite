# FRESH REVIEW — BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001 (Pass-6)

## Binding

- **Task ID:** `BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001`
- **Product branch:** `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`
- **Base:** `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`
- **Frozen Pass-6 source candidate:** `9773a439f9f994225ce6515bd9f755815aa2c5af`
- **Pass-6 evidence / package tip:** `5dca114bc40c40743029a9439101958b13eaf721`
- **Control branch read (fast-forward):** `agent-dev/bilateral-episode-v0.1` @ `6c51469`
- **Predecessor reviews:** `BI-CG-LECLAIRE-WETTING-CLOSURE-001/EXTERNAL_SCIENTIFIC_REVIEW_R4_CHANGES_REQUESTED.md`, `BI-CG-LECLAIRE-PASS4-001/EXTERNAL_SCIENTIFIC_REVIEW_R3_CHANGES_REQUESTED.md`, `BI-CG-LECLAIRE-WETTING-CLOSURE-001/FRESH_REVIEW.md`
- **Staging:** `D:/2026_agent_work/01_GLM_LBM3D_porous_media/.review_runtime/BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001/` (outside every git worktree)
- **Review mode:** `FRESH_SESSION` — executor transcript not read and not requested; neither the candidate nor the evidence tree was modified.

## Decision

**CHANGES_REQUESTED**

Pass-6 does everything the R4 correction round asked of it, and I verified the wetting
physics end-to-end. The freeze now holds strictly, the whole matrix reproduces from one
frozen SHA, the corrected convention reaches every machine-readable artifact, and the
contact-angle, slit-Pc, mechanical-sigma and Laplace results all reproduce from raw data.

The stage still cannot close, because the one benchmark this round was created to fix is
scientifically misfiled, and because the current provenance is not yet internally
consistent:

1. **Classical Jurin's law does not apply to this model.** `L17_CORE` runs at unit
   density ratio: I measured the bulk total density of *both* phases at
   `1.000000000`, the body force is applied to the total mixture density, and the
   measured hydrostatic gradients are `-2.383e-4` (liquid) and `-2.349e-4` (gas) —
   i.e. both phases are hydrostatic with the same `rho g = 2.5e-4`. The classical
   relation `dh = 2 sigma cos(theta)/(rho g h)` is the *weightless-gas* form whose
   restoring term `(rho_liquid - rho_gas) g dh` vanishes identically here. There is no
   finite classical Jurin equilibrium to validate, so `case-08 = FAIL_SOLVER` mislabels
   the outcome, and the masterline/atlas statements that the case "fails on a geometry
   where Jurin's law finally applies" are wrong as written.
2. **Current provenance is not internally consistent yet.** The atlas carries *two*
   sections both headed "— CURRENT" (Pass-5 and Pass-06); the masterline header still
   says "Updated through: Pass-4 fresh review + external review R3" and its
   one-sentence truth still lists the Pass-4 convention/artifact defects as the
   remaining blockers, contradicting its own Pass-6 status table; and the gravity
   control that the freeze commit leans on has no committed artifact.

Everything else in the Pass-6 package verified clean; see "What should be preserved".

## Coverage

Inspected: the six required documents; the complete `9773a43..5dca114` diff and the
`ad07b18..9773a43` source diff; `tests/leclaire_cg/pass06.py` (Jurin section in full,
the summary/report emitters, the case list), `artifact.py`, `verify_manifest_paths.py`;
all eleven Pass-6 case `metrics.json` / `metadata.json` / `README.md` /
`render_manifest.json`; `SUMMARY.json`, `run_manifest.json`, `VALIDATION_REPORT.md`,
`EXECUTION_REPORT.md`, `VALIDATION_ATLAS.md`, `SCIENCE_MASTERLINE.md`,
`WETTING_PHASE_CONVENTION.md`, `MECHANICAL_SIGMA_DERIVATION.md`, `PAPER_FORMULATION.md`,
`REFERENCE_MANIFEST.md`, `PROVENANCE.md`.

Recomputed (never from `metrics.json` as a source):

- unit checks, manifest verification and the **complete Pass-6 matrix** from a
  byte-exact staging copy of `9773a43` with the committed harness;
- the Jurin topology by independent flood fill on the raw `t0000` field, and the
  section areas / volume balance;
- phase densities, hydrostatic gradients, gas-pocket volumes/densities/masses, the
  local Laplace balance at both interfaces with thin windows, the meniscus sag and the
  realised contact angle, node-threshold vs sub-grid interface levels;
- a **new gravity-scaling control** (`g` and `4g`) in reviewer staging, since no
  committed artifact exists;
- contact angle (own contour extraction, own least-squares circle fit, an independent
  `2 atan(h/a)` estimator), slit `Pc` (own meniscus contour and bulk windows),
  mechanical sigma (from the retained `Ndist`), Laplace (own radii, pressure jumps and
  both regressions), case-09 (mass and closure from raw), and the Pass-5 vs Pass-6
  regression comparison;
- pixel-level regeneration of five `fig1_field` figures, the three contact-angle wedge
  figures and the mechanical-sigma observable figure.

Not inspected: the executor transcript (forbidden); the production Taichi solver; the
R1/R2 PDFs beyond the statements already verified in the previous rounds.

---

## 1. Freeze / evidence invariant — PASS

| check | result | evidence |
|---|---|---|
| evidence commit is a pure child of the freeze | PASS | `5dca114^ == 9773a43`; the only commits between are the evidence commit itself |
| no change to `experimental/leclaire_cg/**` | PASS | `git diff --name-status 9773a43 5dca114 -- experimental/` is empty |
| no change to `tests/leclaire_cg/pass06.py` | PASS | `git diff --name-status 9773a43 5dca114 -- tests/` is empty |
| no change to geometry, measurement code, gates, artifact writer, raw schema | PASS | all of those live under the two paths above; the only modified files in the evidence commit are `VALIDATION_ATLAS.md`, `EXECUTION_REPORT.md` and `results/pass06_run.log` |
| the frozen SHA contains the harness that produced the evidence | PASS | the harness at `9773a43` is byte-identical to the harness at `5dca114` (EOL-normalised), and my rerun from a staged copy of `9773a43` reproduces the whole tree |
| one command reproduces the complete matrix | PASS | `python tests/leclaire_cg/pass06.py` from the staged frozen copy → **320/320 `metrics.json` fields bit-identical, 11/11 verdicts identical, 39/39 raw `.npz` byte-identical** |
| no case-specific post-freeze patch or selective rerun | PASS | single command, single run, all eleven cases; the harness is unchanged across the freeze |
| isolation | PASS | `lbm_solver_cg3d.py` blob `1b7db4ac…` identical at base, freeze and tip; the only non-added file `base..tip` is `.gitignore` |

One provenance wrinkle, recorded rather than counted: `results/pass06_run.log` already
exists in the freeze commit (an earlier run of a pre-freeze tree) and is overwritten by
the evidence commit with the actual evidence run. The evidence-tip log matches the
committed `SUMMARY.json` wall times case by case (`case-03 340.4 s`, `case-04 529.0 s`,
…), so the log shipped with the evidence is the run that produced it; the earlier entry
is harmless but a reader cannot tell the two apart without checking the timings.

## 2. Already-closed wetting findings — regression confirmed, not reopened

**Pass-5 → Pass-6 regression.** Every `metrics.json` numeric field for cases 01, 02, 03,
05, 06, 07, 09, 10, 11 is bit-identical between the two passes, and every raw `.npz` for
those cases is array-for-array identical (the only byte difference is the storage string
`schema_version`, `l17c_core_raw_v1` → `l17c_core_raw_f32_v2`). The single metric change
in case-04 is the corrected `wall_normal` string. The only source change in
`experimental/leclaire_cg/` between the two freezes is a docstring in
`operators.wall_normals` (R4 §8.1). No bulk physics moved.

**Contact angle (case-04).** Recomputed from the committed raw fields with my own
contour walk and my own least-squares circle fit:

| prescribed | my liquid-side angle | my `2 atan(h/a)` | reported | complement (what Pass-4 reported) | psi at the fitted centre |
|---:|---:|---:|---:|---:|---|
| 60° | 64.85 | 63.29 | 65.19 | 115.15 | −1.00 (gas side) |
| 90° | 96.29 | 91.19 | 95.70 | 83.71 | +1.00 (liquid side) |
| 120° | 128.99 | 112.48 | 129.40 | 51.01 | +0.999 (liquid side) |

The liquid-side relation `cos(theta_liquid) = -(z_c - z_w)/R` is what the fields
satisfy; the complementary values are exactly the ones Pass-4 published, so the Pass-5
correction is confirmed rather than re-litigated. The 60° cap has its centre of curvature
below the wall (a spreading film), the 90°/120° caps above it. `metrics.json` now states
`n_w = +grad(g)/|grad(g)| = fluid -> solid` and `theta measured through psi>0 liquid/red`.

**Slit capillary pressure (case-07).** My recomputation from raw: `Pc` = **+2.032e-3 /
≈0 (0.0) / −2.141e-3** against theory ±2.0e-3 (ratios +1.016 and +1.071), reported
+2.0509e-3 / −4.22e-7 / −2.1567e-3. Geometry re-verified from the mask and field: plates
transverse to the meniscus, `x` ends sealed, `z`-invariance exactly `0.0`, and the
meniscus advances at the walls for 60° (edge 13.765 vs centre 13.096) and recedes for
120° (13.223 vs 13.932).

## 3. Main review target — the Jurin benchmark

### 3A. Geometry and topology — PASS (independently verified)

`jurin_geometry` builds floor + ceiling, a barrier at `x = x_w = 10` above
`z_channel = 8`, slit walls at `y < 3` / `y >= 13` above the channel, and seals both `x`
faces. On the committed `t0000` field my own 6-connectivity flood fill over `psi > 0`
returns **one component of 5632 cells** touching the reservoir band, the lower channel
and the capillary interior. The initial condition fills everything below `z_fill = 20`,
so the three regions are connected by construction. Section areas from my own masks
match the harness: channel 352, reservoir 144, capillary 120 (the barrier column and the
slit walls occupy the rest). Liquid mass is conserved over the run to 4e-9. The
`connected_at_t0 = true` metadata claim is therefore true in fact, not merely asserted.
The reservoir free surface sits at `z ≈ 19.3`, well above the channel top, so the
capillary entrance is genuinely submerged. **The R4 §6 topology blocker is fixed.**

One structural fact the harness never records: the *gas* forms **two sealed pockets**
(3312 cells reservoir-side, 2760 capillary-side at `t0`), because the barrier separates
them above the channel. Any pressure-balance argument for this geometry has to treat the
two pocket pressures as independent variables — the classical treatment uses one gas
pressure.

### 3B. Is classical Jurin applicable to this model? — NO

Measured from the committed raw fields and read from the frozen source:

| question | answer |
|---|---|
| bulk total density of the liquid (red) phase | **1.000000000** |
| bulk total density of the gas (blue) phase | **1.000000000** |
| does `L17_CORE` implement a density contrast? | **No** — unit density ratio is the declared scope; `rho_r + rho_b = 1` in both phases |
| what does the body force act on? | the **total mixture density**: `solver.step()` does `m[..., idx] += rho * self.force[a]` with `rho` from `op.macroscopic(N)`; identical weight per unit volume in both phases |
| hydrostatic gradients in the two phases | liquid `-2.383e-4`, gas `-2.349e-4` per lu (t_final); both ≈ `-rho g` with `rho = 1`, `g = 2.5e-4`; they agree to 1.4 % |

So `Delta rho = rho_liquid - rho_gas = 0`. The classical capillary-rise balance

```
(rho_liquid - rho_gas) g dh = sigma (kappa_capillary - kappa_reservoir)
```

has no gravity restoring term at all, and the harness's prediction
`dh = 2 sigma cos(theta)/(rho g h) = 8.00 lu` is the *single-phase / weightless-gas*
form of that balance. Its premise is refuted by measurement: if the gas were weightless,
`dp/dz` in the gas would be ≈ 0, whereas the gas column is hydrostatic with essentially
the liquid's gradient (a factor ~70 difference, not a subtle one).

Consequence: **a finite classical Jurin equilibrium height does not exist for
`L17_CORE` as frozen.** The case cannot fail "Jurin's law" because the law's premises are
not satisfied by the model; `FAIL_SOLVER` is a misclassification and the atlas's
"fails on a geometry where Jurin's law finally applies" is wrong as written.

What would be required to make a true Jurin test, in the order I would try them:
(i) a non-unit density ratio (`gamma != 1`, `PAPER_FORMULATION` §§ 0.4/2.7 machinery
already specified but out of scope) so that `rho_liquid != rho_gas`; or (ii) a
phase-selective body force (not present — the forcing is on the mixture); or (iii) an
open/pressure-controlled gas boundary, which addresses only the closed-box complication
and still leaves `Delta rho = 0`.

### 3C. Reservoir curvature — negligible, and not the issue

The reservoir free surface is flat to `sigma / R_res ≈ 6.8e-6` (surface height variance
1.05e-5 lu²), so the classical simplification that drops the reservoir curvature term is
justified *in the classical balance*. It does not rescue that balance, because the
failing term is the density contrast, not the reservoir term. For completeness the
meniscus itself is strongly curved in the right direction: edges at `z = 20.43`,
centre at `z = 19.34`, a sag of 1.09 lu, corresponding to a circular arc of radius
≈ 12.0 lu, i.e. `sigma/R = 1.67e-3` and a realised liquid-side angle of ≈ 65° for a
prescribed 60° — the same ~ +5° systematic the sessile-drop case shows.

### 3D. Interface-level measurement — the reported "1 lu" is a probe convention, not a quantisation artefact

| measurement | t=0 | t_final (g = 2.5e-4) | rise |
|---|---:|---:|---:|
| node threshold (harness: highest `psi > 0` node) | 19 / 19 | 20 / 19 | **1.000 lu** |
| sub-grid `psi = 0` crossing, probe columns | 19.500 / 19.500 | 20.203 / 19.342 | **0.861 lu** |
| sub-grid, region means over both interiors | 19.500 / 19.500 | 20.070 / 19.500 | **0.570 lu** |

So the harness's "~1.0 lu" overstates the physical rise by ~15 % relative to the same
probe columns measured sub-grid, and by ~75 % relative to region means. It is *not*,
however, a pure quantisation artefact: the sub-grid rise is still ≈ 0.86 lu, i.e. about
11 % of the 8.0 lu prediction, so the "does not reach theory" conclusion survives the
correction. The case should state which convention it reports.

### 3E. Equilibration — the state is stalled, not demonstrated to be at equilibrium

The committed trace freezes from `t = 400` onward: levels constant to 0.001–0.003 lu
over 3600 steps. My own control reproduces that freeze exactly (`cap_sub` 20.206 → 20.203
between t=1000 and t=4000). But the state is not static in the strict sense:

- `max|u|` over the fluid stays at `9.97e-4` (mean `1.62e-4`) — a persistent current, not
  round-off;
- at the slit meniscus the local Laplace balance closes well (measured `p_gas - p_liq`
  = 1.53–1.67e-3 across thin windows adjacent to the interface, against `sigma/R_arc` =
  1.67e-3 from the sag) — so the meniscus itself is locally consistent;
- at the reservoir surface the same thin-window measurement gives `p_gas - p_liq` =
  +7.3e-4 against a curvature pressure of ≈ 0 — a residual imbalance of the same order
  as half the capillary drive;
- the two gas pockets sit at different pressures (`p_gas,slit - p_gas,res ≈ 7.7e-4` after
  removing the hydrostatic difference), and my pocket accounting shows the solid nodes
  absorb ≈ 302 units (5 %) of the blue component over the run, so the "sealed pocket"
  picture is itself only approximate in this solver (the known full-way bounce-back
  solid-node reservoir).

The honest classification is therefore "stalled / lattice-pinned interface with a
residual parasitic current", not "equilibrium reached, theory contradicted". The case
should say so, and the review cannot use it as an equilibrium verdict either way.

### 3F. Gravity-scaling control — no committed artifact; the claim reproduces, the inference does not follow

The freeze commit message asserts `g = 2.5e-4 → rise ~1.0 lu` and
`g = 1.0e-3 → rise ~1.0 lu`, but **no committed artifact records the 4g run**:
`case-08/metadata.json` carries `gravity: 0.00025` only, `CASES` has a single case-08,
and no file under `results/leclaire_cg/pass-06/` mentions the control. Per the review
contract I ran it myself in reviewer staging from the frozen source, geometry and
initial condition otherwise identical:

| arm | theory (`dh`) | node rise | sub-grid rise | region-mean rise | final `cap_sub` / `res_sub` |
|---|---:|---:|---:|---:|---|
| `g = 2.5e-4` | 8.00 lu | 1.00 | 0.861 | 0.570 | 20.203 / 19.342 |
| `g = 1.0e-3` (4×) | 2.00 lu | 1.00 | 0.867 | 0.567 | 19.664 / 18.797 |

The numbers in the commit message are **confirmed**: the relative rise is unchanged at 4×
gravity, whereas the classical prediction would move from 8.00 to 2.00 lu and a properly
scaling system would rise four times less. But the inference drawn from it — "the rise
does not scale with 1/g, so this is a genuine FAIL_SOLVER" — does not follow: with
`Delta rho = 0` there is no hydrostatic restoring force, so *1/g scaling is not expected
in this model in the first place*. The control is good evidence that the meniscus
response is not gravity-driven; it is not evidence about Jurin.

## 4. Mechanical surface tension (case-11) — reproduced, immaterial f32 cast

Recomputed from the retained `Ndist` (the raw schema stores arrays as f32 while the solver
runs f64): `sigma_mech = 0.019999960`, ratio **0.999998**, against the reported
`0.019999907` / 0.999995. The disagreement between my f32-based recomputation and the
driver's f64 evaluation is `5.29e-8`, i.e. **2.6e-6 relative** — the storage cast does not
materially change the diagnostic. Premises verified independently: exactly one interface
in the integration window `[15, 47)`, a bulk window `[44, 51)` clear of both interfaces,
discrete total variation over the window `2.000000` against the continuum value 2, and
`A = 2.25` untuned.

Implication, stated carefully: this argues **against** a global perturbation-amplitude
error (`A` is not low by ~20 %), and together with the Laplace data (local ratios
1.018–1.056, zero-intercept 1.041, free-intercept 1.127 with a negative intercept) it
shifts suspicion to the Laplace measurement/regression/finite-radius treatment. It does
not by itself diagnose the Laplace offset.

## 5. Laplace (case-03) — reproduced; the "12.7 % high" summary is too coarse

| `R_nominal` | `R_measured` | `dp` | `sigma_local / sigma_input` |
|---:|---:|---:|---:|
| 6 | 5.869461618 | 7.1960365e-3 | 1.0559 |
| 7 | 6.868001997 | 6.0667292e-3 | 1.0417 |
| 8 | 7.909886120 | 5.2197262e-3 | 1.0322 |
| 9 | 8.891988587 | 4.5799514e-3 | 1.0181 |

My free-intercept fit: slope `0.022538347` (**1.1269×** input), intercept `-4.872e-4`,
`R² = 0.9999557`; zero-intercept: `0.020824273` (**1.0412×**). Reported values agree to
~1e-8. The data therefore show a finite-radius/intercept structure: the per-radius
values are only 2–6 % high and fall monotonically with `R`, while the free-intercept
slope is 13 % high because of the negative intercept coupling. The predeclared gate
honestly fails and the FAIL_SOLVER verdict stands; `A = (9/4) omega sigma` is not
retuned. The formerly misleading `sigma_extrapolated_large_R` field is **renamed**
`sigma_1overR_fit_unstable` with `r2_vs_invR = 0.9925` reported alongside, which
addresses the Pass-5/R4 labelling defect.

## 6. Asymmetric wall (case-09) — conservation closed; the verdict label is still questionable

From the committed raw arrays: the box is sealed on all four lateral faces; red/blue
masses are `1320.000000000 / 1400.000000000` at `t0` and
`1320.000000321 / 1400.000000460` at `t_final`, i.e. drift ~3–5e-10 (the reported values
3.63e-10 / 3.84e-10 are the same quantity measured against the driver's f64 initial
sums). No multi-percent mass creation — the historical ~7 % source stays eliminated. The
wall-band change is still −6.83 %, reported with the explicit non-attribution note.

`FAIL_SOLVER` remains defensible as a gate failure but sits oddly on a number the
artifact itself declines to attribute: a gate whose cause is explicitly "not attributed
to wall mass transfer; no stationary reference case was run" is an unresolved
diagnostic, and `INCONCLUSIVE` would be the more honest label until a stationary
reference exists. This mirrors the Pass-5 review's non-blocking point; it is not a
blocker here either, but the current label is not the best available one.

## 7. Raw artifact and rendering integrity — PASS

- 39 raw `.npz` files are tracked at the evidence tip; every `render_manifest.json`
  `source_raw` reference (36 across 11 manifests) resolves to a committed file;
  `verify_manifest_paths.py` reports 36 referenced / 36 trackable / 0 missing / 0
  ignored.
- All eleven manifests carry `candidate_sha = 9773a43…`, `script =
  tests/leclaire_cg/pass06.py` and `script_version = "pass-06"` — the Pass-5 stale
  `pass-04` version string is fixed.
- Raw schema `l17c_core_raw_f32_v2`, with `solid, psi, rho_r, rho_b, rho, vel, speed,
  Ndist(where applicable), schema_version`.
- Figure regeneration from the tracked raw: **5/5 `fig1_field` PNGs pixel-identical**
  (Laplace, contact angle, slit Pc, Jurin geometry, mechanical sigma);
  `fig_cap_theta{90,120}` pixel-identical and `fig_cap_theta60` `max|d| = 1`; the
  mechanical-sigma observable `fig2` regenerated from my own recomputed `P_N - P_T`
  profile matches at `max|d| = 1`.
- **`reproduce.py` is still broken in all eleven cases.** Each script inserts
  `os.path.join(dirname(__file__), '..', '..', '..', 'tests', 'leclaire_cg')` — three
  levels up lands on `<repo>/results/tests/leclaire_cg`, which does not exist; the
  correct depth is four. Running the committed `case-04-contact-angle/reproduce.py`
  fails with `ModuleNotFoundError: No module named 'pass06'` from both the repository
  root and the case directory. `VALIDATION_ARTIFACT_SPEC.md` §5.1/§8/§11 require a
  working regeneration path, and the root cause is in `artifact.Case.write_reproduce`,
  so it must be fixed at source before the next freeze.

## 8. Provenance / science-document closure — mostly fixed, three inconsistencies remain

Fixed and verified in the current checkout:

- the canonical convention `n_w = +grad(g)/|grad(g)| = fluid -> solid` and
  `theta = through liquid/red` now appear in `pass-06/SUMMARY.json`,
  `VALIDATION_REPORT.md`, the per-case `metrics.json`/`metadata.json`/READMEs, and the
  report headline; no current artifact states `-grad(g)`;
- the Pass-6 stage id is used in `SUMMARY.json`, `run_manifest.json` and
  `VALIDATION_REPORT.md` (the Pass-5 `PASS4-001` mix-up is gone);
- render script versions are `pass-06` everywhere;
- R5 acquisition is consistently 科研通: `REFERENCE_MANIFEST.md` is clean and
  `PROVENANCE.md` now reads "obtained via the 科研通 (ablesci-paper-download) workflow
  by DOI on 2026-09-27; any earlier statement that it came from a local search is
  retracted";
- the R5 coefficient mapping remains `UNRESOLVED` in the masterline, `PAPER_FORMULATION`
  §4.2/§11 and `CURRENT_VS_LECLAIRE_MAP.md` — not silently closed;
- Passes 1–5 are banner-marked superseded in `EXECUTION_REPORT.md` §0 and the atlas; the
  Pass-4 complementary-angle result is presented as history and its `-grad(g)` mentions
  are explicitly labelled superseded;
- `MECHANICAL_SIGMA_DERIVATION.md` §6 now separates "Pass-4 — failed diagnostic
  (superseded), 0.768" from "Pass-5 — corrected and recomputable, 1.000".

Still inconsistent:

1. **`VALIDATION_ATLAS.md` has two sections headed "— CURRENT"** — line 340
   "Pass-5 — CURRENT (`BI-CG-LECLAIRE-WETTING-CLOSURE-001`)" and line 393
   "Pass-06 — CURRENT (`BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001`)". Each claims that
   "every earlier section in this file is historical and SUPERSEDED", so the Pass-5
   section supersedes itself. The Pass-5 section must be demoted.
2. **`SCIENCE_MASTERLINE.md` contradicts itself.** Its header still reads
   "Updated through: Pass-4 fresh review + external review R3", and §17's
   one-sentence truth still says the remaining blockers are "the Pass-4 wetting
   convention/instrument error, reproducible raw-artifact binding, and an unresolved
   ~12–13 % Laplace sigma-scale offset" — while §12 (rewritten for pass-06) marks the
   convention and the raw-artifact binding `PASS` and names the Jurin benchmark as the
   blocker. The file has two current truths.
3. **`MECHANICAL_SIGMA_DERIVATION.md`** still says the diagnostic "is implemented as
   `case-11-mechanical-sigma` in the pass-04 artifact tree" (it is Pass-6), and the
   top-level `results/leclaire_cg/PROVENANCE.md` still describes the Pass-3 run with no
   superseded banner (my Pass-5 non-blocking point; R4 did not require it).

And the substantive version of the same problem: the masterline §12 row and the atlas
both present the Jurin outcome as a solver failure on a geometry "where Jurin's law
finally applies". Section 3B shows that statement is wrong; the current science
document therefore records an incorrect interpretation of the one open benchmark.

## 9. Preserved bulk formulation — PASS

`git diff ad07b18 9773a43 -- experimental/leclaire_cg/` touches only a docstring in
`operators.wall_normals`. `lattice.py`, `solver.py`, `geometry.py` and
`test_lattice_tables.py` are untouched between Pass-5 and Pass-6, so the D3Q19 tables,
the MRT structure, the corrected R1 Eq. (4) `psi_i (u · grad rho)` term, the `X_W`
one-dimensional gradient, the harmonic viscosity interpolation, the explicit-beta
recolouring, the post-collision unrelaxed perturbation and `A = (9/4) omega_eff sigma`
are all preserved; the unit checks (88/88, identical log) and the bit-identical
Pass-5→Pass-6 metrics confirm it numerically. f64 conservation is unchanged (case-10
identical; case-09 excursions ~1e-10).

---

## Answers to the required questions

1. **Is the freeze/evidence binding valid?** Yes. `5dca114^ == 9773a43`, no source,
   harness, gate, geometry or schema change in the evidence commit, and the frozen SHA
   runs the whole matrix: 320/320 metric fields, 11/11 verdicts, 39/39 raw snapshots.
2. **Are raw/render artifacts fully reproducible?** Yes for data and figures (39 tracked
   `.npz`, 36/36 manifest paths committed, 5/5 field figures pixel-identical, wedges and
   the mechanical-sigma observable reproduced). No for the per-case `reproduce.py`
   scripts, which all fail on a wrong `sys.path` depth.
3. **Is the R1 wetting convention closed?** Yes — `+grad(g)` in code and in every
   machine-readable artifact, `theta_liquid` everywhere, and the analytic lock is
   non-circular (unchanged from Pass-5, re-verified at 88/88).
4. **Does the sessile contact angle validate it?** Yes, within the predeclared 15° gate:
   64.85 / 96.29 / 128.99° (my recomputation) and 65.19 / 95.70 / 129.40° (driver) for
   60 / 90 / 120°, with the correct phase identity at the fitted centre.
5. **Does slit Pc validate it?** Yes: my recomputation gives +2.032e-3 / ≈0 / −2.141e-3
   for 60 / 90 / 120°, correct signs, magnitudes within 2–7 %, transverse geometry with
   real contact lines and sealed ends.
6. **Is the new Jurin geometry topologically valid?** Yes — one connected liquid
   component spanning reservoir, channel and capillary; entrance submerged; areas and
   volume balance as declared.
7. **Is classical Jurin equilibrium physically applicable to the current unit-density
   `L17_CORE`?** **No.** `rho_liquid = rho_gas = 1.000000000`, the body force acts on the
   mixture, and both phases are hydrostatic with the same gradient, so
   `(rho_liquid - rho_gas) g dh = 0` and the classical restoring force does not exist.
8. **What density difference and body-force coupling enter the balance?** `Delta rho = 0`
   and the body force is `rho_total * f_z` (equal in both phases); the realised balance is
   `rho_liquid g dh = (p_gas,res - p_gas,slit) + sigma (kappa_c - kappa_r)` — i.e. the
   rise would be set by the gas-pocket pressure difference and the curvature difference,
   not by a density contrast.
9. **Does reservoir curvature change the prediction?** Not materially: the reservoir
   surface is flat to `sigma/R ≈ 6.8e-6`, so the classical practice of neglecting it is
   justified; the failing premise is the density contrast, not the reservoir term.
10. **Does sub-grid measurement change the ~1 lu rise?** It changes it by ~15 %: node
    threshold 1.000 lu, sub-grid at the same probe columns 0.861 lu, region means
    0.570 lu. It is a probe/definition effect, not a quantisation artefact — the rise
    remains ≈ 0.86 lu, far from 8.00 lu.
11. **Is the case equilibrated?** No demonstrable equilibrium: the levels freeze after
    ~400 steps but `max|u|` stays ≈ 1e-3, the reservoir interface carries a residual
    ~7.3e-4 imbalance against ≈ zero curvature, the two gas pockets differ in pressure,
    and the solid-node reservoir absorbs ~5 % of the gas component. Classify it as
    stalled/pinned with a residual current, not as an equilibrium result.
12. **What does the gravity-scaling test demonstrate?** That the relative rise is
    gravity-independent (1.00 node / 0.861 sub-grid at `g`; 1.00 / 0.867 at `4g`, where
    theory would ask 8.00 → 2.00 lu) — consistent with the absence of a hydrostatic
    restoring term. It does **not** demonstrate a Jurin solver failure, and it has no
    committed artifact.
13. **Is case-08 correctly classified as `FAIL_SOLVER`?** No. With the classical law out
    of scope and the state not equilibrated, the correct classification is
    `INVALID_TEST` / out-of-scope theory (or the case must be re-derived as a
    closed-system pressure-balance diagnostic), with the `FAIL_SOLVER` label withdrawn.
14. **Is mechanical sigma ≈ sigma_input reproducible?** Yes: 0.019999960 (ratio 0.999998)
    from the retained f32 `Ndist`, against the reported 0.999995; the f32 cast contributes
    2.6e-6 relative, immaterial.
15. **What does mechanical ≈ 1.0 together with the Laplace data imply?** It rules out a
    global perturbation-amplitude calibration error and points at the Laplace
    measurement/regression/finite-radius treatment (per-radius 1.02–1.06, zero-intercept
    1.04, free-intercept 1.13 with a negative intercept).
16. **Is case-09 a solver failure or an unresolved diagnostic?** An unresolved
    wall-band diagnostic: conservation is closed to round-off, and the failing gate is
    explicitly not attributed. `FAIL_SOLVER` is defensible as a gate result but
    `INCONCLUSIVE` would be more honest until a stationary reference exists.
17. **Are the current science/provenance documents internally consistent?** Not yet:
    two "CURRENT" atlas sections, a masterline whose header and §17 contradict its §12,
    a stale pass-04 path in the mechanical-sigma derivation, an un-bannered top-level
    `PROVENANCE.md`, and the incorrect Jurin interpretation in the masterline and atlas.
18. **Is the NumPy/f64 reference line ready for closure?** Not as published, but it is
    close: the wetting formulation, convention, instrument and two of the three wetting
    benchmarks are verified closed; what remains is (a) correctly scoping and
    documenting the Jurin benchmark, (b) committing the gravity control, (c) fixing
    `reproduce.py`, and (d) the three document-consistency items above. `PASS` closes
    only the NumPy/f64 reference stage and authorises neither a Taichi/f32 port nor any
    production promotion.

## Findings

### Blocking

**B-1 — the Jurin benchmark is scientifically misfiled: classical Jurin's law is out of
scope for the unit-density model.**

Measured `Delta rho = 0` (both phases at total density 1.000000000), body force on the
mixture, and equal hydrostatic gradients in both phases (`-2.383e-4` vs `-2.349e-4`
against `rho g = 2.5e-4`). The harness's `dh = 2 sigma cos(theta)/(rho g h) = 8.00 lu`
and its 0.5–1.5 rise-ratio gate therefore test a relation whose restoring term vanishes
identically; `FAIL_SOLVER` (and the masterline/atlas statement that the case fails "on a
geometry where Jurin's law finally applies") misrepresents the physics. The signal is
unambiguous and cheap to confirm — the gas column is hydrostatic with the liquid's
gradient, whereas the weightless-gas premise requires it to be flat. Required: withdraw
the `FAIL_SOLVER` label, classify the case as an out-of-scope/invalid theory test (or
re-derive the closed-system pressure balance and report that instead), and state
explicitly what a true Jurin test would need (density-ratio support, phase-selective
forcing, or an open gas boundary).

**B-2 — the gravity-scaling evidence is not durable, and its inference does not follow.**

The freeze commit message rests on a 4× gravity control for which no artifact exists in
the evidence tree. My staging run confirms the numbers (1.00 node / 0.861 sub-grid at
`g`; 1.00 / 0.867 at `4g`) but also shows the intended inference is invalid: with
`Delta rho = 0`, gravity-independence is expected, so "no 1/g scaling" cannot be read as
a solver failure. Required: commit the control (a second case or a documented arm with
its own raw fields, figures and metrics), and rebuild the classification on the correct
hydrostatic law.

**B-3 — current provenance contradicts itself.**

`VALIDATION_ATLAS.md` carries two sections both headed "— CURRENT" (Pass-5 and Pass-06);
`SCIENCE_MASTERLINE.md`'s header and §17 still describe Pass-4-era blockers that its own
§12 marks as PASS. The review contract's PASS condition — "current provenance is
internally consistent" — is not met.

### Non-blocking

**N-1 — every per-case `reproduce.py` is broken** by an off-by-one `sys.path` depth
(three levels up instead of four), so `import pass06` fails from any cwd; the cause is
`artifact.Case.write_reproduce`, hence a source fix plus regeneration. Violates
`VALIDATION_ARTIFACT_SPEC` §5.1/§8/§11. (This is my Pass-5 W-3 recurring in a new form:
the module name was updated, the path depth never was.)

**N-2 — the rise convention is undocumented.** The reported "≈1.0 lu" is the node
threshold; the same probe measured sub-grid is 0.861 lu and the region mean is 0.570 lu.
The case should state which convention the verdict uses.

**N-3 — the state is not equilibrated**, and neither the README nor the report says so:
`max|u| ≈ 1e-3` persists, the reservoir interface carries a `7.3e-4` residual against
zero curvature, the two sealed gas pockets sit at different pressures, and the solid-node
reservoir absorbs ≈ 5 % of the gas component over the run.

**N-4 — case-09's `FAIL_SOLVER`** is a gate result whose cause the artifact explicitly
declines to attribute; `INCONCLUSIVE` would be more honest until a stationary reference
exists.

**N-5 — small durable-record leftovers:** `MECHANICAL_SIGMA_DERIVATION.md` still names
the pass-04 tree as the diagnostic's home; the top-level `results/leclaire_cg/PROVENANCE.md`
still describes the Pass-3 run with no superseded banner; and the freeze commit's
`results/pass06_run.log` (a pre-freeze run) is indistinguishable from the evidence run
without comparing timings.

## What should be preserved

1. the freeze discipline and single-command reproducibility (320/320 fields, 39/39 raw,
   88/88 unit checks);
2. the canonical `+grad(g)` convention in code and in every artifact, with the
   non-circular analytic lock;
3. the liquid-side circle-fit relation and the sessile contact-angle result;
4. the transverse slit-Pc geometry and its correct sign/magnitude;
5. the connected Jurin geometry itself — it is a genuine improvement and a valid
   wetting/redistribution configuration even though it cannot test Jurin's law;
6. the retained raw distributions and the premise-gated mechanical-sigma diagnostic;
7. `A = (9/4) omega_eff sigma` untuned, with the Laplace FAIL preserved and the
   renamed `sigma_1overR_fit_unstable` field;
8. the f64 conservation closure and its explicit backend scope limit;
9. the artifact/render-manifest machinery and the per-case README structure.

## Declaration

- Fresh, independent reviewer session; the executor transcript was not read or requested.
- Neither the frozen candidate nor the evidence tree was modified. All recomputation ran
  on a byte-exact staging copy of `9773a43` under
  `.review_runtime/BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001/`, outside every git
  worktree.
- No GPU work, no Taichi execution, no production run.
- Files written by this review: this file and `FRESH_REVIEW_SESSION.json`, published to
  `.agent/evidence/BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001/` on
  `agent-dev/bilateral-episode-v0.1`.
- `PASS` was not available: the remaining benchmark is misclassified against the model's
  own physics (B-1) and current provenance is not yet self-consistent (B-2, B-3).
  `HUMAN_REQUIRED` was considered and is not triggered — every correction is determined
  — but the owner should settle one scope question: whether the reference line will
  support a true capillary-rise test at all (density-ratio or phase-selective forcing,
  a scope extension beyond the frozen unit-density contract), or whether the Jurin
  benchmark is retired from the closure claim and the stage closes on the two wetting
  benchmarks that are now verified.
