stage: V1C
attempt: 1
candidate: cfff538d0549982769482b34e8528b251df1b585
execution_report: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-V1C-CLOSURE-001/results/levelc_v1c/EXECUTION_REPORT.md

# REVIEW — BI-V1C-CLOSURE-001 (V1c closure)

## Review Mode

`FRESH_SESSION` — no prior context on this episode. The review is read-only: no
product file, commit, branch, or executor artifact was modified, and only this
file was written. The executor conversation transcript was not read or requested.
All checks below are from (a) the frozen candidate's committed source and
evidence, (b) `git` objects in the product worktree, and (c) recomputation from
those committed files with `python -c` one-liners. No GPU rerun was performed
(optional in the review request); no conclusion below depends on one.

## Binding

- **Task ID:** BI-V1C-CLOSURE-001, per
  `.agent/episodes/bilateral-imbibition-v0.1/V1C_CLOSURE_CONTRACT.md`, reviewer
  contract `.agent/episodes/bilateral-imbibition-v0.1/V1C_REVIEWER_CONTRACT.md`,
  binding `REVIEW_REQUEST.md` in this directory.
- **Product worktree (absolute):**
  `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-V1C-CLOSURE-001`.
- **Branch:** `agent-task/BI-V1C-CLOSURE-001`.
- **Base SHA:** `a9c6db87da2eeb3572607152391fe6863394ebee` (V1b candidate).
- **Candidate SHA (verified):**
  `cfff538d0549982769482b34e8528b251df1b585` — `git rev-parse HEAD` returns
  exactly this value and the branch resolves to it.
- **Worktree state:** `git status --porcelain` empty (0 lines) — clean.
  `git merge-base --is-ancestor a9c6db8 HEAD` succeeds → the candidate is a
  descendant of the declared base.
- **Change set:** 81 files (1 source + 80 evidence files), see next section.
- **Evidence paths reviewed:** `results/levelc_v1c/{EXECUTION_REPORT.md,
  PROVENANCE.md, MANIFEST.json, summary.json, static_table.csv,
  differential_table.csv, gates.csv}`, the four `static_h*/` and four
  `dyn_*/` directories (`report.json`, `static_series.csv`, `front.csv`,
  `probes.csv`, `axial_*.csv`, `.prov.json` sidecars), `logs/*.log|*.exit`,
  and `tests/levelc_v1c.py` (846 lines, read in full).

## Changed-file scope

`git diff --name-only a9c6db8..cfff538` returns exactly 81 paths, all inside
the two locations the closure contract authorises:

| Area | Files | Status |
|---|---|---|
| `tests/levelc_v1c.py` | 1 (new, +846 lines) | authorised (contract "Implementation": V1c-specific driver) |
| `results/levelc_v1c/**` | 80 (new: per-run reports/CSVs/logs/exit codes, `static_table.csv`, `differential_table.csv`, `gates.csv`, `summary.json`, `MANIFEST.json`, `EXECUTION_REPORT.md`, `PROVENANCE.md`, `.prov.json` sidecars) | authorised (contract "Implementation": `results/levelc_v1c/**`) |

Out-of-scope filter (`grep -v '^results/levelc_v1c/\|^tests/levelc_v1c\.py$'`)
returns nothing.

- **Solver untouched:** zero diff lines for `lbm_solver_cg3d.py` and `cg3d/**`.
- **V1 / V1b history untouched:** no `results/levelc_v1*/**`, `results/levelc_v1b/**`
  or `tests/levelc_v1b.py` path in the diff.
- **Physics constants match the contract's "Fixed physics" list** (verified in
  source, `tests/levelc_v1c.py:70-92`): `CapA=0.06`, `sigma=1.012·CapA`,
  `nu_l=nu_g=0.1`, `rho0=1`, `psi_solid=-0.68`, z-periodic slit, pinned
  equal-pressure reservoirs, `UMAX_CAP=0.12`.
- **V1b boundary topology unchanged:** V1c's `WALL_T, RES_T, MEM_T, BUF_T = 3,
  8, 1, 2`, `X_RES0, X_RES1 = 3, 11`, `X_MEM_IN=11`, `X_IN=14` and the whole
  `layout()` body are byte-identical to `levelc_v1b.py` at the base revision
  (only the `note` string differs), and `L_hyd = L+5` reproduces V1b's 241/477.

## Gate table

Statuses are mine, recomputed from committed evidence (not copied from
`gates.csv`).

| Gate (source) | Requirement | Reviewer status | Evidence |
|---|---|---|---|
| Binding | HEAD = declared candidate, clean, descendant of `a9c6db8` | **PASS** | `git rev-parse/status/merge-base` |
| Scope | only V1c-authorised files; no solver change | **PASS** | 81-path diff, out-of-scope filter empty |
| Contract A (static) | `C_static(h)` for h=26/40/60/80, `theta`, `1/h` table, candidate fits + residuals, stationarity recorded separately from spurious-current magnitude | **PASS** | `static_table.csv`, per-run `report.json`; stationarity and `umax` floor both recorded |
| Contract A (readiness) | reproducible, non-erratic trend; plateau or coherent trend identifiable | **PASS (with caveats)** | one producer/one rule for all four points; no `1/h` law supported; see "Static coherence assessment" for the ±4 % scatter, ±0.4–2.7 % band-extent sensitivity, 18 % V1b↔V1c protocol spread at h=26 and the ~10 % offset to the droplet registry |
| Contract B (band rule) | full cross-section inspection, 95 % bulk columns, ≥2 mixed-column padding, ≥12 contiguous columns, **invalid if unavailable** | **FAIL (partial)** | rule implemented as declared and `None`-returns correctly, but 12 columns is insufficient to reject demonstrably non-bulk gas bands; 9 such probes per short case are still flagged `band_valid=1` and enter the reported `Pc_dynamic_median` (see "Bulk-band assessment") |
| Contract B (band diagnostics) | report band counts and threshold sensitivity 0.85/0.90/0.95 | **PASS (incomplete)** | threshold sensitivity reported per probe and aggregated (≤0.54 % dynamic, ≤1.0 % static); band **extent** sensitivity — the dominant effect — is not reported |
| Contract C gate | `\|a_26−1\| ≤ 0.10` | **PASS** | recomputed `a26 = 1.04536` |
| Contract C gate | `\|a_40−1\| ≤ 0.10` | **PASS (fragile)** | recomputed `a40 = 1.08797`; margin is 0.012, and two defensible re-aggregations give 1.0956 / 1.1206 (the latter outside the gate) |
| Contract D | no NaN/Inf | **PASS** | `nan_at = None` in all four reports (checked over the whole run, not only the window) |
| Contract D | no velocity-cap violation | **PASS** | `umax_break = None`; window peaks 0.0233–0.0268 ≤ 0.12 |
| Contract D | zero imposed reservoir pressure difference | **PASS (by construction)** | both reservoirs are pinned to `rho=1` every step (`lbm_solver_cg3d.py:766-777`); `g3` is therefore a tautology — it verifies BC application, not a dynamical equality |
| Contract D | monotonic post-transient front, declared fit window, `R² ≥ 0.995`, secondary/primary ≤ 2 % | **PASS** | `R² ≥ 0.99997`; secondary agreement ≤ 0.12 %; front refit from `front.csv` reproduces `V_meas` to machine precision |
| Contract D | colour-mass closure reported | **PASS (reported, not gated)** | `closure_{r,b}` 2.8e-4–1.2e-3 relative (exec report says "~1e-4"); unreported total colour-mass drift 0.04–0.27 % (non-blocking) |
| Contract E | provenance binding | **PASS (with minor gaps)** | see "Provenance assessment" |
| Contract F | mandatory technical-document update | **NOT_RUN** | not yet produced; correct per the contract's own ordering (after the fresh reviewer), but it is part of the deliverable and its required content must be constrained (see below) |

## Independent recalculations

### Static calibration `C_static(h) = P_c·h/(2σ)`, σ = 0.06072

Recomputed from each `static_h*/report.json` `Pc_static`, and cross-checked by
re-deriving the band-mean pressure difference from the committed
`axial_static.csv` (h26: 3.690825e-3 vs reported 3.690809e-3, a 1.6e-8
rounding difference → the band means and the reported `P_c` are mutually
consistent).

| h | `Pc_static` | `C_static` (reviewer) | `C_static` (reported) | θ (reviewer) | stationarity | `umax` floor |
|---:|---:|---:|---:|---:|---|---:|
| 26 | 3.690809e-3 | 0.790193 | 0.7902 | 37.80° | stationary at 19 750 | 0.0252 |
| 40 | 2.280325e-3 | 0.751095 | 0.7511 | 41.31° | stationary at 12 500 | 0.0254 |
| 60 | 1.632839e-3 | 0.806739 | 0.8067 | 36.22° | stationary at 12 000 | 0.0258 |
| 80 | 1.183271e-3 | 0.779494 | 0.7795 | 38.79° | stationary at 13 000 | 0.0253 |

Fits over the four points (my least-squares, matching `summary.json`):
constant `C = 0.78188` with `resid_max = 0.03079` (±3.94 % of the mean);
`over_h` R² = 0.0066; `over_h2` R² = 0.0001 — i.e. no `1/h`-type law is
supported, exactly as the execution report states.

### Dynamic chain `L_eff = P_c,dyn·h²/(12μV)`, `a_h = ΔL_eff/ΔL`

`V_meas` was re-fit independently from the committed `front.csv` using the
window declared in each report (`t ≥ T_TRANS`, `x_ic_exit ≤ x ≤ x_stop`): the
recomputed slopes agree with the reported values to machine precision
(4.9739739e-3 / 3.0001945e-3 / 5.5887907e-3 / 3.7913658e-3), and are stable to
the window choice (mid-60 % refit differs by ≤ 7e-4 relative). Per-probe
`Pc_dynamic` medians were re-derived from `probes.csv`; `L_eff`, `a_h`, `L_0`
and `L_0/h` follow from those two inputs (μ = 0.1, ΔL = 477−241 = 236):

| h | L_hyd short→long | V (short→long) | Pc,dyn (short→long) | `L_eff` (short→long) | `a_h` | `L_0` | `L_0/h` |
|---:|---|---|---|---|---:|---:|---:|
| 26 | 241 → 477 | 4.973974e-3 → 3.000195e-3 | 2.909850e-3 → 3.069054e-3 | 329.56 → 576.26 | **1.04536** | 77.6 | 2.99 |
| 40 | 241 → 477 | 5.588791e-3 → 3.791366e-3 | 1.778214e-3 → 1.936421e-3 | 424.23 → 680.99 | **1.08797** | 162.0 | 4.05 |

Both primary gates pass as declared. Two independent cross-checks of the
derived quantities:

- **Pressure-budget identity.** Using the recorded per-probe slopes and jumps,
  `P_c,dyn = |g_l|(x_m−14) + |g_g|(buf0−1−x_m) + jump_in + jump_out` holds to a
  median relative residual of ~1e-6 on every case (the +1e-6 residuals are the
  pinned-reservoir pressure equality); large residuals appear only on the
  starved-band probes, where the fitted gas slope changes sign. The same
  numbers show the **membrane/buffer jumps carry a median 30 % / 19 % / 49 % /
  32 % of the measured `P_c,dyn`** (h26 short / h26 2L / h40 short / h40 2L) —
  i.e. roughly a third of the "capillary pressure" that feeds `L_eff` is a
  localized open-boundary loss, which is consistent with the documented
  `L_0 ≫ 0` intercept and reinforces the external review's interpretation.
- **Mass accounting.** Reconstructing the initial colour masses from
  `closure_*_final` and `inj_*_final` gives exactly the geometric values
  (m0_red = 6084, m0_blue = 34164/9360; totals 40 248 / 77 064 / 61 920 /
  118 560 = fluid-node counts), and injection bookkeeping closes to
  2.8e-4–1.2e-3 relative. The **unreported** total colour mass
  (`m_r + m_b`) falls by 109 / 32.2 / 120.4 / 124.1 units over the four runs
  (0.271 %, 0.042 %, 0.194 %, 0.105 %) — a small, smooth diffuse-interface
  drift, not an order-one leak, but it is not part of the candidate's stated
  mass accounting.

## Bulk-band assessment (the material finding)

The rule is implemented as documented: per-probe full cross-section
classification, ≥95 % of nodes, mixed columns excluded plus 2 columns each side,
longest contiguous run, `None` (→ `band_valid=0`, no `Pc` written) when either
band is shorter than 12 columns. I confirmed the explicit-failure path exists in
source (`bulk_bands` returns `None`; `run_dynamic` then writes `band_valid=0`
with no `Pc`; `analyze_dynamic` excludes those probes and hard-fails the window
if none are valid), and that it is **exercised** in the committed evidence: the
last two probes of `dyn_h26_s` (t = 39 000, 40 000) and the last probe of
`dyn_h40_s` (t = 36 000) are `band_valid=0` with empty `Pc_dynamic` fields.

The defect is the *threshold*, not the mechanism. In the two short cases the gas
band is bounded below by the meniscus and above by the slit exit, so it shrinks
as the front advances; 12 columns is enough to satisfy the rule and far too few
to satisfy "bulk":

| Case | Probes with gas band < 60 lu | gas band at the last valid probe | `r²_gas` range on those probes | `\|dp/dx\|_gas / G` |
|---|---:|---:|---|---|
| `dyn_h26_s` | 9 of 38 (t ≥ 30 000) | 15 lu | 0.004 – 0.80 | 0.03 – 0.84 |
| `dyn_h40_s` | 9 of 35 (t ≥ 27 000) | 12 lu | 0.002 – 0.66 | 0.03 – 4.30 |
| `dyn_h26_2L` | 0 of 60 | 259 lu | 0.93 – 1.00 | 0.97 – 1.02 |
| `dyn_h40_2L` | 0 of 60 | 216 lu | 0.87 – 1.00 | 0.96 – 1.03 |

`r2_gas` and both fitted gradients are computed and committed per probe but are
not used as validity criteria, so a gas band whose linear fit has
`r² = 0.002` and whose slope is 4.3× the analytic Poiseuille value is published
as a valid bulk measurement. Their `P_c_dynamic` is systematically depressed
(e.g. `dyn_h40_s`: 1.47–1.79e-3 on the starved tail vs 1.79–1.86e-3 in the
developed regime), and they enter the reported median — the reported
`P_c_dynamic_median` is not a bulk-plateau average.

A second, independent contract-compliance issue in the same aggregation:
`analyze_dynamic` takes the `Pc` sample as `t_tr ≤ t ≤ t[i_hi]` and ignores the
`x ≥ x_ic_exit` condition that defines the candidate's own declared fit window.
Consequently 6 of 35 probes in `dyn_h26_s` (front at x = 69.0…93.6 <
x_ic_exit = 94) and 4 of 25 in `dyn_h40_s` (x = 102.6…119.2 < 122) are inside
the `Pc` aggregate while being outside the declared window; contract D requires
the pressure measurement to live in a "valid declared fit window".

**Estimator sensitivity of the primary gates** (all recomputed by me from
`probes.csv` + `front.csv`; "E1 mean/median" = the candidate's declared probe
set with mean/median; E2 = restricted to the declared window; E3/E4 = E2 plus a
gas-band width cut):

| Aggregation | `a26` | verdict | `a40` | verdict |
|---|---:|---|---:|---|
| E1 median (reported) | 1.0454 | PASS | 1.0880 | PASS |
| E1 mean | 1.0529 | PASS | **1.1206** | **FAIL** |
| E2 median (declared window) | 1.0501 | PASS | 1.0956 | PASS |
| E2 mean | 1.0588 | PASS | 1.1302 | FAIL |
| E3 median (gas band ≥ 60 lu) | 1.0397 | PASS | 1.0699 | PASS |
| E3 mean | 1.0404 | PASS | 1.0721 | PASS |
| E4 median (gas band ≥ 80 lu) | 1.0374 | PASS | 1.0647 | PASS |
| E4 mean | 1.0360 | PASS | 1.0592 | PASS |

Reading: the physics conclusion survives — every median-based variant passes,
and once the starved probes are excluded the mean and median agree (1.040 vs
1.040 at h26; 1.072 vs 1.070 at h40), i.e. the residual uncertainty is the
contamination, not the physics. But **the reported h=40 verdict is not robust
to a defensible estimator choice**: the declared margin (0.088 against a 0.10
gate) is smaller than the spread produced by the aggregation choice (0.065 →
0.096 across median variants, 0.121–0.130 under the mean). The reported 8.8 %
deviation also overstates the physical residual by ~2 percentage points
(band-quality-restricted: 6.5–7.0 %); contamination pushes the slope *away* from
1, so the candidate's headline number is pessimistic rather than optimistically
biased. A gate whose PASS depends on the estimator is not yet a closure result,
and the contract's own guard ("mark that probe invalid rather than silently
falling back") is what fails here.

Note on correction cost: every per-probe input needed for a corrected
aggregation (band ranges, `r2_gas`, slopes, `Pc`) is committed in `probes.csv`,
and shortening the window changes `V_meas` by ≤ 0.07 % — so this can be fixed in
the producer's aggregation path (`collect`, or the probe-validity rule in
`run_dynamic`) and re-collected **without any new GPU run**.

## Static coherence assessment

No extrapolation model is forced here, per the reviewer contract.

- **Sequence coherence (intra-candidate): GOOD.** All four heights come from one
  producer revision and one measurement rule; the values scatter within
  ±3.94 % around 0.7819 with no monotonic component (h26 0.7902, h40 0.7511,
  h60 0.8067, h80 0.7795). Constant, `1/h` and `1/h²` fits are statistically
  indistinguishable (`resid_max` 0.0308 / 0.0305 / 0.0308), so the contract's
  instruction not to force a law is correctly followed. The operational reading
  "no resolvable resolution trend for 26 ≤ h ≤ 80; plateau ≈ 0.78" is supported.
  The trend can therefore not be called erratic, and this promotion criterion is
  met as written.
- **Sensitivity is larger than the candidate states.** The reported diagnostic
  varies only the `|psi|` threshold (≤ 0.7 %). Re-deriving the same static `Pc`
  from `axial_static.csv` with different but equally defensible band extents
  moves it by ±0.4 % (h26), ±0.95 % (h40, h60) and ±2.7 % (h80) — the same order
  as the ±3.9 % inter-height scatter. The sequence is therefore
  *measurement-limited*: the four points do not resolve a physical trend finer
  than the method's band sensitivity.
- **Unresolved protocol spread (new, unstated in the candidate).** V1b's static
  measurement was a different protocol (nx=160, slab [60,100), fixed cores
  [68,92)/[110,150) with node masks, 60 000 steps) and V1c's is nx=240, slab
  [90,150), bulk-column bands, 12 000–19 750 steps. The overlap heights behave
  very differently: h=40 agrees to 0.18 % (0.75248 vs 0.75110), h=26 does not
  (0.67048 vs 0.79019, +17.9 % in `P_c`). I could not reduce this to a single
  cause from committed evidence (it is not the integration time — V1b's `P_c`
  plateau was already flat at 15 250 steps, while V1c's runs stop with a small
  residual creep of ±0.06 %/1000 steps at h26/h40 versus the flat V1b runs). The
  execution report's claim that "the V1b value was band-placement-biased"
  attributes the whole 18 % shift to the band rule without isolating it; the
  frozen candidate cannot support that attribution. This is a documented
  measurement-uncertainty item, not a failed gate.
- **The 30° droplet registry is not approached.** `C = 0.782` corresponds to
  θ_slit ≈ 38.6° ± 1.8°, i.e. ~10 % below `cos 30° = 0.866`. Within
  26 ≤ h ≤ 80 there is no trend toward the registry. The contract explicitly
  does not require equality, but the offset is systematic and must be carried
  forward explicitly as an unresolved calibration question for V2 (V2 is the
  first consumer of the slit calibration), not presented as a resolution
  artifact.
- **Convergence semantics.** Static runs declare stationarity from `P_c` drift
  (< 1e-3 relative over the last 10 blocks) while the spurious-current floor
  (umax ≈ 0.0252–0.0258, essentially h-independent) is recorded and not gated,
  as the closure contract requires. I verified the `P_c` series really is
  stationary at the stated level (last-10-block standard deviation 1e-6–5e-6,
  0.03–0.3 %). "Process completion ≠ convergence" is respected.

## Differential hydraulic assessment

- The metric is the right one and the prediction is unambiguous: with matched
  viscosities the total liquid+gas path length is fixed by the two pinned
  reservoirs, so an added slit length must add exactly one unit of equivalent
  length → `a_h = 1` is the exact ideal value. The measured 4.5 % (h26) and
  8.8 % (h40) deviations are the metric's signal, not a modelling artifact.
- Both primary gates pass as declared, and my cleanest re-aggregation (E3/E4)
  *strengthens* the result: `a26 ≈ 1.037–1.040`, `a40 ≈ 1.065–1.070`. The
  residual positive deviation is consistent with the documented localized
  open-boundary loss (median jumps are 19–49 % of `P_c,dyn`, `L_0/h` = 2.99 vs
  4.05 — same order, weakly supporting the external review's `L_eq ∝ h`
  entrance-loss reading, as the contract's optional diagnostic asked).
- I checked the robustness of the pass against the two measurement degrees of
  freedom available in the committed data: the aggregation statistic and the
  window/band validity cut. Medians always pass; the mean over the contaminated
  set fails at h=40 (1.121–1.130). The conclusion I can defend is therefore
  "distributed resistance matches plane Poiseuille to ≈4 % (h26) and ≈6–7 %
  (h40), inside the 10 % engineering gate", **not** the candidate's
  "4.5 % / 8.8 %" headline. The needed correction is a validity rule, not a
  physics change.
- The reported `Pc,dyn` increase from short to long (+5.5 % at h26, +8.9 % at
  h40, while Ca falls from 0.0082→0.0049 and 0.0092→0.0062) has the sign and
  rough magnitude expected from a dynamic contact angle (Tanner-type) effect,
  so the long-case value is not obviously an artifact — but it is exactly the
  term that decides the h=40 gate, which is why the aggregation must be made
  defensible rather than left estimator-dependent.
- Front/stability evidence is sound and, importantly, deterministic across
  protocols: `V_meas` reproduces V1b to 7e-5 / 5e-6 / 1.8e-4 relative for
  h26 short / h26 2L / h40 short, while the band-rule change moved `Pc,dyn` by
  only ~1 % (2.884→2.910e-3, 3.039→3.069e-3, 1.797→1.778e-3).

## Provenance assessment

- **Two-revision producer chain — verified.** `git diff 032d273..5f18caa`
  touches `tests/levelc_v1c.py` in exactly one hunk, one line, inside
  `collect()` (line 696, the constant-fit design matrix), which is a
  collect-only change; nothing in `run_static`/`run_dynamic`/`analyze_dynamic`.
  The file's SHA-256 is `46a4b477…` at `032d273` (the hash recorded in every
  primary run's `prov.producer_sha256`), `5b4eea59…` at `5f18caa`, and
  `5b4eea59…` in the candidate — so the candidate's driver is byte-identical to
  the last producer revision, and the run artifacts bind to the revision that
  actually produced them. The `PROVENANCE.md` account is accurate.
- **Artifact binding — verified.** All 8 `MANIFEST.json` run entries carry
  `shell_exit_code = 0`, `run_head = 032d273…`, the collect outputs carry
  `5f18caa…`; `logs/*.exit` are all `0` (9 files); and I re-hashed every
  MANIFEST-listed artifact against the files on disk: **60 hash checks, 0
  mismatches, 0 missing**.
- **Minor gaps (non-blocking).** (i) The per-artifact `.prov.json` sidecars and
  the per-run `report.json` embed `exit_code: null` / `finished_at: null`
  because they are written before `prov_finish`; the exit code is bound at
  MANIFEST/log level instead, so contract E's per-artifact list is only
  partially satisfied inside each artifact. (ii) Artifacts record the *producer*
  revision, not the candidate SHA; the mapping is documented and verifiable, but
  the literal wording of contract E ("candidate SHA") is met only via
  `PROVENANCE.md`. (iii) The 8 `fields_final.npz` files listed and hashed in
  `MANIFEST.json` are matched by the repository's `.gitignore` (`*.npz`, line 9)
  and are therefore present on this disk but absent from the committed
  candidate — consistent with V1b practice (0 npz among V1b's 53 committed
  evidence files), but it means raw final fields are not independently
  checkable from the branch. Everything else needed for the checks above is
  committed.
- **Documentation inconsistency in the frozen evidence.** Both the module
  docstring (`tests/levelc_v1c.py:24-27`) and the `layout.note` string that is
  written into every dynamic `report.json` state the fit region as
  `[12, 16+L)`; the code actually uses `psi[12:buf0]` with `buf0 = 14+L`, i.e.
  `[12, 14+L)` (in-buffer + slit; the out-buffer is excluded). The quoted region
  is two columns wider than the one used. Harmless numerically, but the frozen
  evidence asserts a region the code does not use, and the pending document
  update would quote it.

## Technical-document deliverable (contract F)

`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md` in the
control checkout is still at "更新至 V1b external scientific review；V1c 尚未执行"
(unchanged; the only V1c-related control-branch artifact is an untracked
`figures/v1c_make_figs.py`). Per the closure contract the update is sequenced
*after* the fresh review, so this is not a deviation — but the review must
constrain its content, and the present candidate is not yet the right numeric
base for it. When it is written it must:

1. state the four-point plateau `C_static ≈ 0.782 ± 0.031` (statistical) with the
   method sensitivity (±0.4–2.7 % band extent) and the 18 % V1b↔V1c h=26
   protocol spread, instead of repeating the archived V1b two-point
   extrapolation (§11: "h26 → h40 明显向 droplet registry 靠近", `C_∞ ≈ 0.905`,
   `θ_∞ ≈ 25.2°`), which the four V1c points do not support;
2. state the ~10 % offset from `cos 30° = 0.866` (θ_slit ≈ 38.6°) as an
   unresolved slit-vs-droplet calibration item for V2, not as a resolution
   artifact;
3. use the *corrected* differential numbers, not the contaminated
   `a26 = 1.0454 / a40 = 1.0880` (the untracked figure script reads
   `summary.json`/`static_table.csv` and labels the gates "PASS" from those
   values, so it must be regenerated after the re-collect, with the candidate
   SHA in the captions as it already does);
4. add the contract-F items 1–10 (SHA/base, formulas, code excerpts, tables, two
   SVGs, before/after table, SOLVER/BC/VAL/DIAG/HARNESS statement, evidence
   paths and this decision).

## Blocking findings

1. **B1 — The reported `Pc_dynamic` aggregate is not restricted to bulk
   plateaus.** Gas bands down to 12 columns with `r²_gas` as low as 0.002 and
   `|dp/dx|` 4.3× (or 0.03×) the analytic Poiseuille value are flagged
   `band_valid=1` and enter the reported median (9 probes in each short case).
   Consequence: `a40` is reported as 1.0880 when the band-quality-restricted
   value is 1.065–1.070, and under a defensible mean estimator the same
   contaminated set yields 1.121–1.130 → **FAIL**. The contract's requirement
   that insufficient bands fail explicitly (reviewer contract: "Confirm that
   invalid/insufficient bulk bands fail explicitly") is not met at
   `BULK_MINCOLS = 12`; the candidate's own committed diagnostics (`r2_gas`,
   `dpdx_gas`) show it.
2. **B2 — The `Pc` sample contradicts the candidate's own declared fit window.**
   `analyze_dynamic` filters probes by `t_tr ≤ t ≤ t[i_hi]` only, ignoring
   `x ≥ x_ic_exit`; 6/35 (h26 short) and 4/25 (h40 short) probes with the front
   inside the initial-condition transient region contribute to the reported
   `Pc_dynamic_median`. Contract D requires a "valid declared fit window" for
   the measurement; either the window declaration or the filter must change, and
   the change must be explicit.

B1 and B2 are both fixable in the producer's aggregation/validity logic from the
already-committed per-probe evidence, with no solver change and no GPU rerun.
They matter because this candidate's numbers are the intended numeric base for
the mandatory technical document and for the V2 decision.

## Non-blocking findings

1. **Static plateau level is method- and protocol-conditional.** Report the
   plateau with its method band (±0.4–2.7 %) and the unexplained 18 % V1b↔V1c
   spread at h=26; the current execution report presents the 5.1 % intra-V1c
   h26/h40 difference as if the band rule alone explained the change from V1b's
   11.5 %.
2. **Static threshold sensitivity is up to 1.0 %, not ≤ 0.7 %.** The ≤ 0.7 %
   claim holds for `Pc_dynamic` (max 0.54 %) but not for the static table, where
   `Pc_thr095` differs from `Pc_thr090` by +1.03 % at h=80.
3. **Mass accounting is under-stated.** `closure_{r,b}` relative values are
   2.8e-4–1.2e-3 (the execution report says "~1e-4"), and the total colour mass
   `m_r + m_b` — which is exactly reconstructible from the committed
   `closure`/`inj` fields — drifts down by 0.04–0.27 % over the runs and is not
   reported. `g9_mass_closure` is `None` (reporting only, as the contract
   allows), so this is a completeness item, not a gate failure.
4. **`g3_zero_dp` has no diagnostic power.** Both reservoirs are pinned to
   `rho = 1` each step, so `rho_res_*_dev_max = 0.0` exactly. The intended
   condition (equal imposed pressure) does hold — I verified the pinning in
   `lbm_solver_cg3d.py:766-777` — but the gate verifies BC application, not a
   dynamical pressure equality; the informative numbers are the recorded
   `jump_in`/`jump_out` (19–49 % of `Pc,dyn`).
5. **Before/after table mixes sensitivity definitions.** "V1b 8–9 % → V1c
   ≤ 0.7 %" compares V1b's band-*placement* sensitivity with V1c's threshold
   sensitivity. V1c's threshold sensitivity is indeed ≤ 0.54 % for
   `Pc_dynamic`, but replacing the bands moved `Pc_dynamic` by only ~1 %, and
   band *extent* remains the dominant sensitivity (finding B1).
6. **Documented fit region ≠ coded fit region** (`[12, 16+L)` vs `[12, 14+L)`),
   see "Provenance assessment".
7. **Per-artifact provenance gaps:** `exit_code`/`finished_at` are `null` inside
   each `report.json` and `.prov.json`; the binding lives in `MANIFEST.json` and
   `logs/*.exit`. The 8 `fields_final.npz` referenced in `MANIFEST.json` are
   gitignored and not committed.
8. **Optional low-cost diagnostic worth adding:** `L_0/h` = 2.99 (h26) vs 4.05
   (h40) supports a localized entrance/membrane loss of the same order; with
   B1/B2 corrected, report the same `L_0/h` under the corrected aggregation.

## Decision

Decision: CHANGES_REQUESTED

## Rationale

The candidate is honest, well-provenanced, and its physics conclusion is very
probably right: I reproduced the candidate SHA/cleanliness/descent, the
collect-only producer chain, 60/60 artifact hashes, the static `C_static(h)`
chain, both front speeds from raw `front.csv`, `L_eff`, `a26 = 1.04536`,
`a40 = 1.08797`, and every D-layer stability gate — and both primary gates pass
as declared. But the *measurement* behind the differential result is not yet
acceptable as frozen V1c closure evidence: the bulk-band rule accepts probes
whose gas-band fits are demonstrably non-bulk (`r²_gas` 0.002, slope 4.3×
Poiseuille), those probes enter the reported `Pc_dynamic_median`, and the `Pc`
sample also violates the candidate's own declared fit window. The consequence is
not a cosmetic one: the reported `a40 = 1.0880` overstates the physical residual
(clean estimate 1.065–1.070) and sits 0.012 from the gate while a defensible
estimator on the same contaminated set gives 1.121–1.130 (FAIL). A closure gate
whose verdict depends on an undeclared aggregation choice cannot be carried into
the mandatory technical document or the V2 decision.

This is not `HUMAN_REQUIRED`: none of the closure contract's human triggers are
met. No solver change is needed (solver untouched and reproducible across V1b↔
V1c to 1e-4 in `V_meas`); the static sequence is not erratic (one producer, one
rule, no `1/h` law supported, stationarity verified at the stated level), and
its open items — the ~10 % registry offset and the 18 % h=26 protocol spread —
are documentation/uncertainty items, not decisions the reviewer must escalate;
and a finite measurement correction for the differential gate exists, is
computable from committed evidence, and restores a comfortable pass. No GPU run
is required to close this. The static calibration caveats and the fit-region and
mass-accounting remarks above are non-blocking and should be recorded as part of
the same revision.

Victory condition for the re-review: both differential slopes recomputed with a
declared, verifiable band-validity rule and the declared fit window, with the
estimator-variant table (median/mean × validity cut) published — the reviewer's
expectation is `a26 ≈ 1.04`, `a40 ≈ 1.065–1.070`, both PASS. External scientific
review remains mandatory before V2 regardless of this outcome; V2/V3 stay
unauthorised.

## Exact next action

In the product worktree on `agent-task/BI-V1C-CLOSURE-001`, amend
`tests/levelc_v1c.py` so that per-probe bulk measurement is validated before it
can enter any aggregate: (i) fail a probe explicitly when its gas (or liquid)
band does not clear the meniscus/distortion envelope **and** the slit exit by a
declared positional margin — e.g. reject when `gas band < 3h` or
`x_m > buf0 − 4h`, in addition to the existing 12-column rule; (ii) additionally
require a declared linearity check on the fitted band (the already-computed
`r2_gas`/`r2_liq`, e.g. ≥ 0.995); (iii) restrict the `Pc` aggregate to the
declared fit window (`t ≥ t_tr`, `x_ic_exit ≤ x ≤ x_stop`); (iv) publish an
estimator-sensitivity table (median and mean under each validity variant) as a
first-class diagnostic; then re-run only `python tests/levelc_v1c.py collect`
(no new GPU simulation), commit the re-collected `static_table.csv`,
`differential_table.csv`, `gates.csv`, `summary.json`, `MANIFEST.json` and
corrected `EXECUTION_REPORT.md`, fix the `[12, 14+L)` fit-region wording, and
request a fresh review (attempt 2) against the new candidate SHA. Regenerate
`figures/v1c_make_figs.py`/the two SVGs from the corrected candidate and only
then write the contract-F document update.
