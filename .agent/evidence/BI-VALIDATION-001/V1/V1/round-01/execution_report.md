# EXECUTION REPORT — BI-VALIDATION-001 / V1, attempt 1

> This document is the executor's report. It is not, by itself, proof that the
> commands ran or that the reported source state is correct. A controller or
> reviewer may independently capture Git and process evidence.

- **Stage / attempt:** V1 (single-front dynamic wetting verification), attempt 1
- **Status:** `PARTIAL` — the requested validation driver and evidence exist and
  all required diagnostics were produced on the production solver path, but the
  stage's quantitative gates do **not** all pass, and one failure is an
  unexplained anomaly that I flag as a human decision rather than resolve.
- **Base SHA:** `280a46fed488` (`agent-episode/BI-VALIDATION-001` round base)
- **Candidate SHA:** `e9540bcadb86257c70b805afc98f2eec9626c64e`
- **Branch:** `agent-episode/BI-VALIDATION-001` (no merge, no force-push, no
  history rewrite; tree clean after the commit, the only remaining local files
  are the gitignored raw run outputs under `tests_output/`)

## 1. What was done

A dedicated V1 validation driver was added, plus three read-only diagnostics and
a small evidence bundle. **No solver, driver, or geometry file was touched**:
`lbm_solver_cg3d.py` and everything else in `src` are byte-identical to the base.

### Changed files

| File | Change |
|---|---|
| `tests/levelc_imbibition.py` | new — the V1 validation driver (geometry, membranes/reservoirs, IC, time series, declared relation, declared window rule, fits, gates, figure) |
| `tests/levelc_diag_front.py`, `tests/levelc_diag_axial.py`, `tests/levelc_diag_lscan.py` | new — diagnostics (thin wrappers that re-enter the driver's production `build()`/run/`extract_front()` path and add read-only field dumps) |
| `results/levelc_v1/` | new — evidence bundle: two reports, front/probe CSVs, two figures, one run log, three diagnostic profile CSVs, `PROVENANCE.md` (commands, environment, sha256 of every artifact) |

### Configuration (identical in all runs)

Straight slit in a slab that is **periodic in z** (6 layers, so the meniscus is
exactly two-dimensional and has no z-curvature and no side walls), solid
no-slip wetting walls in y at `psi_solid = -0.68` (`theta_liq = 30 deg`, the
repo's calibrated registry value), sealed elsewhere. Open system reusing the
repo's infrastructure: liquid reservoir pinned at `(psi=-1, rho=1)` behind an
inlet membrane that blocks gas; gas reservoir pinned at `(psi=+1, rho=1)`
behind an outlet membrane that blocks liquid. Both baths are therefore at the
**same nominal pressure — zero imposed pressure difference** — and the only
drive is the wetting meniscus. Initial condition: a wetting slug from the slit
entrance to `x0 = 40`, non-wetting phase ahead. `CapA = 0.06`
(`sigma = 1.012*CapA = 0.06072`), `nu_l = nu_g = 0.1` (matched viscosity, the
episode-level fixed assumption), unit density ratio.

### Declared reference relation (fixed before the runs, not fitted)

Because the two phases have matched viscosity and the two baths are at equal
pressure, the liquid and gas columns form a **series** resistance whose sum is
the full channel length, so the configuration-appropriate Lucas-Washburn
relation is the constant-velocity (generalized Washburn) law

    x(t) = x0 + V t ,        V = Pc * h_y^2 / (12 * mu * L_tot)
    Pc = sigma*cos(theta)/b ,  b = h_y/2 ,  mu = nu

and **not** the gas-negligible `x^2 = K t` form (`K = 2 Pc b^2/(3 mu)`), which
is reported only as a diagnostic. The derivation and the reason the naive form
cannot hold here are in the driver header and in §5 below. Declared window
rule: `t >= 5000` steps (declared a priori as ~3x the duct's viscous diffusion
time `h_y^2/(4 nu) ~ 1690`) and `x >= x0 + 5 h_y`, applied mechanically.

## 2. Commands, exit codes, artifacts

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `python tests/levelc_imbibition.py --tag v1_h26 --steps 40000` | 0 | primary case, `h_y = 26`, `L_tot = 246`, 40 000 steps (step cap), front 40.3 -> 192.0 lu |
| 2 | `python tests/levelc_imbibition.py --hy 40 --tag v1_h40 --steps 40000` | 0 | cross-resolution case (gate 8), `h_y = 40`, 40 000 steps, front 40.2 -> 186.9 lu |
| 3 | `DIAG_STEPS=8000 DIAG_EVERY=1000 python tests/levelc_diag_front.py` | 0 | near-front axial profiles of `psi, rho, v_x, v` |
| 4 | `DIAG_STEPS=20000 DIAG_EVERY=4000 python tests/levelc_diag_axial.py` | 0 | full-range axial profiles (liquid and gas gradients, meniscus pressure jump) |
| 5 | `DIAG_NX=508 DIAG_STEPS=16000 python tests/levelc_diag_lscan.py` | 0 | doubled channel length (`L_tot = 492`) — the fixed-vs-proportional resistance discriminator |

All runs on `LBM_ARCH=cuda` (RTX 5080), conda env `lbm`; the first instantiation
of a new grid shape costs ~6 min of Taichi JIT, cached afterwards (~110 steps/s
at 40k nodes, ~4.4 MLUPS).

Artifacts and their sha256 are listed in `results/levelc_v1/PROVENANCE.md`.

## 3. Hard-gate results (V1 stage contract)

| Gate | Result | Evidence |
|---|---|---|
| 1 — no NaN/Inf, no stability-cap violation | **PASS** | no non-finite sample in 40 000 steps; `u_max = 0.0236` (h26) / `0.0242` (h40), `u_rms = 0.0043`, both far below the drivers' 0.12 cap |
| 2 — correct zero imposed pressure difference | **PASS** | liquid and gas reservoir mean densities are exactly `1.000000` at every probe in both runs; nominal `Pc = delta/3 = 0` |
| 3 — monotonic capillary advance | **PASS** | `dx > 0` at every sample after the IC in both runs; no stall, no reversal |
| 4 — post-transient interval >= 40% of the usable trajectory | **PASS** | declared window = 100% of the declared trajectory, 76% of the wider `x >= x0+3b` trajectory |
| 5 — `x^2` vs `t` linear, `R^2 >= 0.98` | **PASS literally, FAIL in intent** | on the declared window `R^2 = 0.99975`; on the wider post-transient trajectory (front advance 79.7 -> 192.0 lu, ratio 2.41) `R^2 = 0.9882`. But the window is **not discriminating**: a constant-velocity front gives this `R^2` for any advance below ~3.5x, and the decisive form test is `x` vs `t`, whose `R^2 = 0.999998`. The measured speed history (a 1.6% drift while the L-W law would require a 2.4x decay) rejects the `x^2 ~ t` law. |
| 6 — measured slope vs the chosen analytic relation within 10% | **FAIL** | h26: `V = 3.842e-3` vs `V_pred = 9.263e-3` -> **-58.5%**; h40: `V = 3.773e-3` vs `V_pred = 14.251e-3` -> **-73.5%**. Against the naive `K` the deficit is -77% (h26). |
| 7 — colour-mass accounting closes, no drift trend | **PASS** | the f64 injection counters agree with the field mass change to 4.2e-4 (h26: residual -10.0 of 23 709 exchanged) and 4.5e-4 (h40); the residual does not trend with time |
| 8 — larger resolved channel does not change the conclusion; normalized slope reported | **RAN, FAILS qualitatively** | `V(h_y=40)/V(h_y=26) = 0.98`; the declared relation requires `1.54` (`V` proportional to `h_y`). The front speed is essentially **independent of the channel width**. |

## 4. Diagnostics (recorded, no threshold)

- **Front extraction robustness:** the primary (volumetric, swept-length)
  definition and the secondary (column-mean crossing) definition agree to
  1.4 lu on average over both runs; fitted slopes are insensitive to the
  choice. The liquid-side column mean is exactly `psi = -1.000` (no film).
- **Meniscus shape:** the wall-adjacent layer leads the centreline by ~4.5 lu
  (a concave, wetting meniscus), symmetric in y, and the interface stays
  ~2 lu wide. Implied apparent angle ~50 deg vs the 30 deg registry value —
  a *diagnostic*, not treated as proof of anything.
- **Axial pressure profiles** (diagnostic 4, at `x_f = 115`): the liquid's far
  field gradient is `dp/dx = -7.06e-6 /lu` and the gas's is `-6.89e-6 /lu`,
  both equal to the plane-Poiseuille value `12 nu V/h_y^2 = -6.85e-6` for the
  *observed* `V`. The measured pressure jump across the meniscus is
  `3.06e-3`, i.e. **0.76x** the Laplace value `sigma cos(theta)/b = 4.045e-3`.
- **Pressure balance:** the columns account for `1.71e-3` of viscous drop, so
  `~1.35e-3` of the meniscus jump is unaccounted for (`~80%` of the column
  drop) — this is the quantitative core of the gate-6 failure.
- **Spurious-current / interface jet:** the gas velocity near the meniscus
  reaches ~2x the developed Poiseuille value and decays over ~20-25 lu; the
  centreline-to-mean velocity ratio in the far field is 1.5 as expected.
- **Length scaling (diagnostic 5):** doubling `L_tot` (246 -> 492) changes `V`
  by `0.641x` where the declared relation requires `0.500x` and a purely fixed
  extra resistance would give `0.356x`. Fitting `V = Pc/(a L + R0)` gives
  `a = 2.38e-3` (1.34x the plane-Poiseuille `12 nu/h_y^2 = 1.78e-3`) **and**
  `R0 = 0.462`, equivalent to ~194 lu of channel at the fitted slope (or ~260 lu at the plane-Poiseuille slope). The anomaly therefore has
  both a proportional (~1.34x) and a large fixed component.

## 5. Numerical stability, convergence, termination

- **Numerical stability:** no NaN/Inf, no density collapse (reservoir densities
  pinned at exactly 1.000000 throughout, in-slit densities stayed within
  `1.000 +- 0.008`), `u_max` an order of magnitude below the operational cap.
- **Convergence:** the front reaches a *steady* constant speed early
  (3.7999 -> 3.8614 lu per 1000 steps, a 1.6% drift over 35 000 steps at h26),
  and the axial pressure gradients match plane Poiseuille with that speed —
  i.e. the flow is quasi-steady and fully developed. This is convergence of the
  *flow*, not of the front (which never stops); see the termination reason.
- **Termination reason:** both production runs ended at the **40 000-step cap**,
  not at the planned `x_stop = 240` (the front reached 192.0 / 186.9 lu),
  because the front is slower than predicted. The process exit code 0 is not
  presented as convergence of anything.

## 6. Deviations

1. **Non-wetting-phase escape path.** V1's first implementation used the
   documented alternative of a *lateral* vent (a liquid-blocking membrane along
   a z-face, backed by a pinned gas reservoir) so that the displaced phase's
   viscous load would be small. A smoke run (5 000 steps, data kept in
   `tests_output/levelc_imbibition/smoke/`) showed the liquid is repelled from
   the vent membrane: it leaves a ~4-layer gas film against it and the front
   becomes strongly z-tilted (a ceiling-corner flow), so the front position is
   ill-defined. That configuration was abandoned; the final evidence uses the
   plain open-slit layout of §1. This exploration cost ~15 min of GPU time and
   is recorded here so it is not repeated.
2. **Declared relation.** The reference relation is the matched-viscosity
   constant-velocity law rather than `x^2 ~ t` (derivation in the driver header
   and §1). This is a *choice of comparison equation for the chosen
   configuration*, made before the runs; it did not rescue the comparison, as
   §3 gate 6 shows.
3. **Window rule too aggressive.** The declared cut `x >= x0 + 5 h_y` leaves a
   narrow (ratio 1.12) window at h26. I therefore also report the wider
   post-transient trajectory (ratio 2.41) and the alternative form tests; the
   declared-window pass on gate 5 is flagged as non-discriminating.
4. **Gas reservoir thickness.** My gas reservoir is 2 lu thick, whereas the
   repo's drivers use 8-lu reservoirs behind a buffer. This is a deviation from
   the repo's convention and a candidate contributor to the fixed part of the
   anomaly; it cannot explain the proportional part (§4, diagnostic 5).
5. **Gate 5 reported in two readings.** The literal gate passes on the declared
   window; the same gate fails to establish what it intends. Both are reported
   rather than choosing the favourable one.

## 7. Assumption / modelling impact

- The V1 contract's reference behaviour (`x^2` vs `t`) is **not** the correct
  relation for the episode's fixed configuration (matched viscosity, equal
  bath pressures, defined escape path): the displacement is a constant-velocity
  series-resistance problem. This is derived, not assumed, and is confirmed by
  the measurement (`x` vs `t` `R^2 = 0.999998` with a 1.6% speed drift).
- The measurements additionally show a **quantitative anomaly** of the same
  order as the effect V1 was meant to measure: the front is 2.4-3.8x slower
  than the declared relation, the meniscus pressure jump is 0.76x the Laplace
  value, ~80% of the column pressure drop is unaccounted for, and the front
  speed is insensitive to the channel width. I did **not** resolve this and did
  not adjust any parameter or relation to make it disappear.
- If this anomaly is a property of the solver rather than of my configuration,
  it propagates to any timing-based interpretation in V2/V3, and gate 5/6-style
  acceptance for later stages cannot be designed on the `x^2 ~ t` form.

## 8. Existing evidence potentially affected

No solver file changed, so nothing already shipped is invalidated. Reusable
conclusions for the rest of the episode: do not plan V2/V3 acceptance on the
gas-negligible Lucas-Washburn form; treat any absolute front-speed prediction
from `sigma cos(theta)` as unvalidated until the anomaly below is resolved.

## 9. Unresolved issues / human decisions

1. **Cause of the capillary-rate anomaly** (the blocker). Candidates not yet
   separated: (a) an effective *dynamic* capillary pressure below
   `sigma cos(theta)/b` at a moving meniscus; (b) an extra *dynamic*
   resistance localised at the diffuse-interface/spurious-current region;
   (c) a boundary/entrance resistance at the reservoir-membrane transitions
   (my gas reservoir is thinner than the repo's convention). The proportional
   part of the anomaly (§4) argues against (c) alone.
2. **Whether the episode's matched-viscosity constraint should be revisited.**
   With matched viscosity the `x^2 ~ t` regime cannot exist in this geometry;
   a defensible V1-style dynamic-wetting gate needs either a viscosity contrast
   or the constant-velocity formulation. That is a scientific-assumption
   decision and is therefore escalated, not taken.
3. **Gate 5's status** — literal pass versus intended fail — is left explicitly
   to the reviewer.

## 10. Suggested next action (one)

Run a **static meniscus test in the same channel**: pin the liquid and gas
reservoirs at a small density difference, let the meniscus stall, and read the
stalled pressure jump directly. That single measurement separates "the
wall-colour meniscus pressure is lower than `sigma cos(theta)/b`" from "the
flow carries an extra dynamic resistance", which is the fork that decides
whether V1's dynamic-wetting question can be answered without a solver change.
