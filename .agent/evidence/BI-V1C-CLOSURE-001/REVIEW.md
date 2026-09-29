stage: V1C
attempt: 2
candidate: 2b82f9a5f448e756b5d5903b0df37f9a3b11d804
execution_report: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-V1C-CLOSURE-001/results/levelc_v1c/EXECUTION_REPORT.md

# REVIEW — BI-V1C-CLOSURE-001 (V1c closure rework, attempt 2)

## Review Mode

`FRESH_SESSION` — no prior context on this episode. The review is read-only: no
product file, commit, branch, or executor artifact was modified, and only this
file was written. The executor conversation transcript was not read or
requested. All findings below come from (a) the frozen candidate's committed
source and evidence, (b) `git` objects in the product worktree, and (c) my own
recomputation from those committed files (`python` via stdin, no files
written). No GPU rerun was performed and no conclusion depends on one.

## Binding

- **Task ID:** BI-V1C-CLOSURE-001, per
  `.agent/episodes/bilateral-imbibition-v0.1/V1C_CLOSURE_CONTRACT.md`, reviewer
  contract `.agent/episodes/bilateral-imbibition-v0.1/V1C_REVIEWER_CONTRACT.md`,
  binding `REVIEW_REQUEST.md` in this directory.
- **Product worktree (absolute):**
  `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-V1C-CLOSURE-001`.
- **Branch:** `agent-task/BI-V1C-CLOSURE-001`.
- **Base SHA:** `a9c6db87da2eeb3572607152391fe6863394ebee` (V1b candidate).
- **Candidate SHA (verified):** `2b82f9a5f448e756b5d5903b0df37f9a3b11d804` —
  `git rev-parse HEAD` returns exactly this value and the branch resolves to it.
- **Worktree state:** `git status --porcelain` empty (0 lines) — clean.
  `git merge-base --is-ancestor a9c6db8 HEAD` succeeds → descendant of the
  declared base. Parent chain:
  `032d273 → 5f18caa → cfff538 (attempt-1 candidate) → 17bdb1b → 4d4dcb3 →
  fbb60ac → 2b82f9a5` — the rework was committed **on top of** the attempt-1
  candidate; `cfff538` is still an ancestor and unmodified, i.e. no history
  rewrite, as the review request claims. (The review request's parenthetical
  calls `2b82f9a5` "parent of the attempt-1 candidate `cfff538`"; the
  relationship is the reverse. Cosmetic error in the binding document, not in
  the product.)
- **Change set:** 86 files vs base (81 from attempt 1 + 5 new), all inside the
  two locations the closure contract authorises (`tests/levelc_v1c.py`,
  `results/levelc_v1c/**`). Out-of-scope filter returns nothing; no
  `lbm_solver_cg3d.py`, `cg3d/**`, `levelc_v1b*` or `levelc_v1.py` path appears
  in the diff.
- **Rework delta vs attempt 1** (`git diff --name-status cfff538..HEAD`, 19
  files): `tests/levelc_v1c.py` (+215/−19, analysis + new `reanalyze` mode),
  the four `dyn_*/report.json`, `EXECUTION_REPORT.md`, `PROVENANCE.md`,
  `MANIFEST.json`, `differential_table.csv`, `gates.csv`, `summary.json`,
  `static_table.prov.json`, new `estimator_sensitivity.csv` (+ sidecar), new
  `logs/collect{2,3,4}.log`. **`front.csv` and `probes.csv` are absent from the
  diff in all four dynamic case directories, and every `static_h*/` artifact is
  untouched** — the simulation evidence really is unchanged, as claimed.
- **Evidence paths reviewed:** `results/levelc_v1c/{EXECUTION_REPORT.md,
  PROVENANCE.md, MANIFEST.json, summary.json, static_table.csv,
  differential_table.csv, estimator_sensitivity.csv, gates.csv}`, the four
  `static_h*/` and four `dyn_*/` directories (`report.json`,
  `static_series.csv`/`front.csv`/`probes.csv`, `axial_*.csv`, `.prov.json`
  sidecars), `logs/*.log|*.exit`, and `tests/levelc_v1c.py` (1042 lines; the
  docstring, `bulk_bands`, `run_static`, `run_dynamic`, `analyze_dynamic`,
  `reanalyze`, `collect` read directly).

## Gate table

Statuses are mine, recomputed from committed evidence (not copied from
`gates.csv`).

| Gate (source) | Requirement | Reviewer status | Evidence |
|---|---|---|---|
| Binding | HEAD = declared candidate, clean, descendant of `a9c6db8` | **PASS** | `git rev-parse/status/merge-base` |
| Scope | only V1c-authorised files; no solver change | **PASS** | 86-path diff, out-of-scope filter empty |
| Reanalysis provenance | runs unchanged; aggregation recomputed by the same production path; `prov_reanalysis` recorded | **PASS** | `front.csv`/`probes.csv` absent from the rework diff; per-run `prov_reanalysis` (`run_head 4d4dcb3`, `producer_sha256 bcf827a7…`, `exit_code 0`); `analyze_dynamic` byte-identical between `4d4dcb3` and HEAD |
| Contract A (static) | `C_static(h)` for h=26/40/60/80, θ, `1/h` table, candidate fits + residuals, stationarity recorded separately from spurious-current magnitude | **PASS** | `static_table.csv`, `summary.json.convergence_fits`, per-run `convergence` block; all values re-derived by me |
| Contract A (readiness) | reproducible, non-erratic trend; plateau or coherent trend identifiable | **PASS** | plateau `C = 0.78188 ± 0.0308` (resid_max 3.9 %), no monotonic component, `1/h` and `1/h²` fits not supported |
| Contract B (band rule) | full cross-section inspection, 95 % bulk columns, ≥2 mixed-column padding, ≥12 contiguous columns, **invalid if unavailable** | **PASS** | rule implemented as declared; explicit failure exercised (2 probes `dyn_h26_s`, 1 probe `dyn_h40_s` with `band_valid=0` and empty `Pc`) |
| Contract B (band diagnostics) | band counts and threshold sensitivity 0.85/0.90/0.95 | **PASS** | per-run `threshold_sensitivity`, `validity_variants.counts`; threshold effect ≤0.94 % (see NF1 — the report's "≤0.6 %" is wrong) |
| Contract C gate | `\|a_26−1\| ≤ 0.10` | **PASS** | my recomputation `a26 = 1.043640` |
| Contract C gate | `\|a_40−1\| ≤ 0.10` | **PASS** | my recomputation `a40 = 1.069897`; holds for every validity variant and both estimators inside the declared ladder |
| Contract D | no NaN/Inf | **PASS** | `nan_at = None`, all four reports |
| Contract D | no velocity-cap violation | **PASS** | `umax_break = None`; window peaks 0.0227–0.0267 ≤ 0.12 |
| Contract D | zero imposed reservoir pressure difference | **PASS (BC check only)** | `rho_res_*` deviations exactly 0; informative numbers are the recorded jumps |
| Contract D | monotonic post-transient front, declared fit window, `R² ≥ 0.995`, secondary/primary ≤ 2 % | **PASS** | `R² = 0.999975–1.000000`, front agreement 6.1e-5–1.2e-3, `monotonic_window = True`; window now applied to the `Pc` sample (B2) |
| Contract D | colour-mass closure reported | **PASS** | `closure_rel` 4.9e-4–6.8e-4, total drift 0.042–0.271 % (`mass_accounting`) |
| Contract E | provenance binding | **PASS (with gaps NF5/NF6)** | 60/60 MANIFEST hashes verified; sidecars; PROVENANCE.md chain reproduced |
| Contract F | mandatory technical-document update | **NOT_RUN** | correctly sequenced after the fresh review; content constraints below |

## Independent recalculations

### Static calibration `C_static(h) = P_c·h/(2σ)`, σ = 0.06072

Recomputed both from each `static_h*/report.json` `Pc_static` and, independently,
by re-deriving the band-mean pressure difference from the committed
`axial_static.csv` with the committed band definitions
(`bulk_bands_090.liq / .gas`):

| h | bands (liq / gas) | `Pc` from my re-derivation | reported `Pc_static` | Δ | `C_static` (mine = reported) | θ |
|---:|---|---:|---:|---:|---:|---:|
| 26 | [95,145) / [0,81) | 3.690824869e-3 | 3.690809011e-3 | 1.6e-8 | 0.790193 | 37.80° |
| 40 | [96,144) / [0,81) | 2.280299264e-3 | 2.280324697e-3 | 2.5e-8 | 0.751095 | 41.31° |
| 60 | [98,142) / [0,76) | 1.632890027e-3 | 1.632839441e-3 | 5.1e-8 | 0.806739 | 36.22° |
| 80 | [99,141) / [0,75) | 1.183257103e-3 | 1.183271408e-3 | 1.4e-8 | 0.779494 | 38.79° |

(The 1e-8 residuals are the precision of the committed axial profile.) Constant
fit `C = 0.78188` with `resid_max = 0.03079` (±3.9 %); `over_h` and `over_h2`
residuals 0.0305/0.0308 — no `1/h` law supported, as the report states. Static
threshold sensitivity: `Pc_thr095` vs 0.90 differs by 0.22/0.34/0.00/1.03 % at
h = 26/40/60/80 — the report's "1.03 % at h80" is correct. Stationarity is
recorded separately from the spurious-current magnitude
(`Pc_last10_rel_drift = −2.5e-4 < 1e-3`, `umax_final = 0.0253`,
`umax_floor_note`), satisfying contract A's separation requirement. The static
numbers are identical to attempt 1 (those artifacts are untouched), so attempt
1's static findings and caveats carry over unchanged — the rework does not
address them and does not claim to.

### Dynamic chain `L_eff = P_c,dyn·h²/(12μV)`, `a_h = ΔL_eff/ΔL`

I re-implemented the declared ladder from scratch against the committed
`front.csv` + `probes.csv` (V0 `band_valid` and t-window → V1 plus
`x_ic_exit ≤ x_m(t_probe) ≤ x_stop` with `x_m` interpolated from `front.csv` →
V2 plus both band widths ≥ 20 columns → V3 plus
`0.5 ≤ |dp/dx|/G ≤ 2.0` on both bands, `G = 12μV_meas/h²`). I did not call the
candidate's code.

`V_meas` re-fitted from `front.csv` over each report's declared window matches
the reported value to ≤1.7e-18 (4.973974e-3 / 3.000195e-3 / 5.588791e-3 /
3.791366e-3; `R²` 0.999975–1.000000). Ladder counts reproduce exactly
(35,33,27,26,22) / (55,55,43,43,43) / (25,24,20,18,13) / (49,49,38,38,38) and
every primary median/mean matches to machine precision:

| h | `L_eff` short→long | `Pc,dyn` short→long (primary) | `a_h` | `L_0` | `L_0/h` |
|---:|---|---|---:|---:|---:|
| 26 | 330.089 → 576.388 | 2.914534e-3 → 3.069721e-3 | **1.043640** | 78.57 | 3.02 |
| 40 | 427.803 → 680.299 | 1.793176e-3 → 1.934445e-3 | **1.069897** | 169.96 | 4.25 |

Both primary gates pass as declared. Two cross-checks that bind this attempt to
attempt 1:

- **Estimator table is complete and faithful.** All 20 cells of
  `estimator_sensitivity.csv` (5 variants × median/mean × 2 heights) reproduce
  from my own implementation to ≤1.3e-15. Nothing is hidden, including the
  cells that FAIL (`V0` mean 1.1206, `V1` mean 1.1302, `V2` mean 1.1016 at
  h=40) — those three reproduce **exactly** the numbers attempt 1 computed for
  the contaminated set, which is the strongest available evidence that the two
  attempts measured the same quantity and that the change in the reported
  number is caused only by the new validity rule.
- **Where the rules coincide, attempt 1 and attempt 2 agree.** My `V0` cell
  gives 1.045357 / 1.087966 = attempt 1's reported `a26`/`a40`; my `V1` cell
  gives 1.050059 / 1.095588 = attempt 1's E2 medians. Attempt 1's independent
  table and mine agree on every overlapping variant.

### Pressure-budget and mass cross-checks

- **Pressure-budget identity.** For every probe of the primary sets,
  `P_c,dyn = |g_l|(x_m−14) + |g_g|(buf0−1−x_m) + jump_in + jump_out` holds to a
  median relative residual of 3.2e-6 / 3.6e-6 / 4.5e-6 / 4.6e-6 (h26 short,
  h26 2L, h40 short, h40 2L). An apparent 25 % outlier at `dyn_h40_s` t=33000
  is my own sign assumption, not a data defect: that probe's **gas slope is
  positive** (`dpdx_gas = +6.68e-6`), so the identity holds in its proper
  signed form. This is the one substantive weakness of the V3 rule I found
  (see NF4).
- **Mass accounting.** Reconstructing `m0 = (m_r − inj_r + closure_r) +
  (m_b − inj_b + closure_b)` from the committed finals gives exactly the
  geometric fluid-node counts (40 248 / 77 064 / 61 920 / 118 560);
  `closure_rel` = 5.30e-4 / 5.95e-4 / 4.91e-4 / 6.82e-4 and total colour-mass
  drift = 0.271 / 0.042 / 0.194 / 0.105 %. Both match the execution report's
  corrected claims (4.9e-4–6.8e-4 and 0.04–0.27 %) and the `mass_accounting`
  block in `summary.json`.

## B1 resolution assessment (attempt-1 finding B1: contaminated aggregate)

**Resolved.** B1 said the aggregate was not restricted to bulk plateaus: gas
bands down to 12 columns with `r²_gas` 0.002 and gradients 0.03×/4.3× the
analytic Poiseuille value were flagged `band_valid=1` and entered the reported
median, making the h=40 verdict estimator-dependent. The rework introduces a
declared four-rung ladder whose top rung defines the primary aggregate, and I
verified each element against the committed per-probe evidence:

- Contaminated probes are **excluded explicitly and audibly**. V3 rejects 5
  probes at `dyn_h26_s` (t = 34 000…38 000; gas bands 15–35 columns,
  `|g_g|/G` 0.03–0.32, `r²_gas` 0.002–0.31, depressed `Pc` 2.74–2.81e-3) and 7
  at `dyn_h40_s` (t = 26 000…35 000; gas bands 62/46/40/34/29/18/12 columns,
  `|g_g|/G` 0.08–4.30, `r²_gas` 0.002–0.66). These are precisely the starved
  interface/exit-contaminated probes attempt 1 identified. Note the h40 probe
  at t = 26 000 has a **62-column** gas band that attempt 1's own "gas band
  ≥ 60 lu" variant (E3) would have kept — the gradient rung catches what the
  width rung cannot, which is a genuine improvement, not a re-labelling.
- Every variant × estimator is published (`estimator_sensitivity.csv`), and the
  attempt-1 FAIL cells are still shown as FAIL. Nothing is silently repaired.
- The primary PASS does not depend on the estimator: median **and** mean pass
  at both heights (1.0436/1.0459 and 1.0699/1.0888). The PASS does not depend
  on the filter either — with the gradient rung removed entirely (V2 only) the
  medians still pass (1.0491/1.0896), and tightening the gradient window to
  [0.9, 1.11] moves the answer to 1.0390/1.0300, i.e. the reported primary is
  not sitting at a tuned edge. The declared rule is therefore not circular: it
  tests `|dp/dx| ≈ G` in the bands (a factor-2 envelope) while the gate tests
  the full path-length budget, and the residual is far smaller than the
  envelope.
- The two declared deviations from attempt 1's illustrative thresholds are
  documented in the driver docstring **and** the execution report, and both
  survive checking:
  1. *20-column positional margin instead of 3h/4h.* The structural argument
     is arithmetically correct and I reproduced it: at h=40 short,
     `buf0 − 4h = 250 − 160 = 90 < x_ic_exit = 122`, so a 4h front-position
     margin empties the window; the entire usable post-IC window is
     `250 − 122 = 128 lu = 3.2h`. My sweep confirms the review's combined
     illustrative rule ("gas band ≥ 3h **and** `x_m ≤ buf0 − 4h`") selects 0
     probes at h40 short and 10 at h26 short. A fixed 20-column margin is a
     resolution-based substitute, and the V3 gradient rung covers the residual
     risk. Caveat recorded for the external review: at h=40 this margin is only
     ≈0.5h, so the h40-short primary rests on 13 probes inside a 3.2h-wide
     usable window. Defensible, but it is the weakest link in the candidate and
     should be named as such.
  2. *Rejecting a pure-`r²` primary (≥0.995 or ≥0.90).* Data-backed: in
     `dyn_h40_s` the gas-band fits sit at `r²_gas` 0.771–0.920 even for
     100–139-column bands, and the published `V3_r2_090` rung retains exactly
     **1** probe at h40 short. The claim in the docstring is accurate.
- The B2 half is resolved as well: the `Pc` sample now honours the declared
  window (`t ≥ t_tr` **and** `x_ic_exit ≤ x_m(t_probe) ≤ x_stop`, front
  position interpolated from committed `front.csv`). The window-x rung removes
  exactly 6 probes at `dyn_h26_s` and 4 at `dyn_h40_s` — the same counts
  attempt 1 reported as violating the window (6/35 and 4/25). The filter is a
  faithful per-probe implementation of the declared window.
- Attempt 1's other differential remark is now quantified in the candidate's
  own numbers and, in my decomposition, the residual is separable: with the
  boundary jumps removed, the equivalent lengths are 231.3 → 469.9 (h26) and
  220.3 → 465.2 (h40), i.e. a distributed residual of ≈1.1 % / ≈3.7 % against
  `ΔL = 236`, while the jump terms (`jump_in + jump_out` over `G`) grow from
  98.8 → 106.5 and 207.5 → 215.2 and contribute ≈3.3 percentage points to
  `a_h − 1` at both heights. The contract's framing ("distributed resistance
  after separating localized open-boundary resistance") is thus supported, and
  the `L_0/h` = 3.02 / 4.25 intercept is the same effect expressed as an
  intercept. (Approximate algebra — the jump anchors differ from the fit
  reference points — but it is arithmetic on committed per-probe numbers.)

**B1/B2 verdict: resolved.** The verdict of both primary gates no longer
depends on an undeclared aggregation choice, the contamination is isolated,
counted, published and reproducible, and the numbers I recomputed independently
agree with the frozen evidence to machine precision.

## Non-blocking findings

1. **The execution report's dynamic threshold-sensitivity claim is wrong.**
   "Pc_dynamic threshold sensitivity (0.85/0.90/0.95) of the PRIMARY aggregates
   ≤ 0.6 %" — recomputed maxima from the committed fields are 0.00 / 0.00 /
   0.00 / 0.06 % for `thr085` but **0.94 %** for `thr095` vs 0.90 at
   `dyn_h26_s` (2.941989e-3 vs 2.914534e-3). The correct statement is
   "≤ 0.94 %". This is the third instance of an overstated sensitivity claim in
   this task (attempt-1 NF2 was the static ≤0.7 % vs 1.0 %); it must be
   corrected before the contract-F document quotes it, otherwise the error
   propagates into the deliverable.
2. **The "≥ ~9 interface widths" justification for the 20-column margin is not
   supported by committed evidence.** The committed `n_mixed` (mixed-column
   envelope) is 7–8 columns at h26 and 8–9 at h40, so 20 columns is ≈2–3
   mixed-envelope widths, not 9 interface widths. The defensible phrasing is
   "≥ 2× the mixed-column envelope, after the 2-column padding exclusion" —
   which the committed `n_mixed` data does support. The same text appears in
   the driver docstring and the execution report.
3. **`g8_band_valid_frac` no longer certifies the primary measurement.**
   `analyze_dynamic` evaluates g8 on `band_valid_frac_base` (0.94–1.00) while
   the primary aggregate is the V3 set (0.52–0.78; 13/25 at h40 short). The
   candidate is transparent about this — both fractions are in every
   `report.json` and the execution report says "base-band fraction ≥ 0.94" —
   but `gates.csv` reading `g8_band_frac=True` invites the wrong inference.
   Recommend relabelling it "base-rule coverage" and adding a primary-coverage
   gate with a stated threshold (a count rule such as `n_primary ≥ 10` would
   pass at 13), rather than leaving the strong rule un-gated.
4. **V3 tests the gradient magnitude, not its sign — one primary probe is
   non-physical.** At `dyn_h40_s` t = 33 000 the retained gas band (23 columns)
   has a **positive** gas slope (`dpdx_gas = +6.68e-6`, i.e. pressure rising in
   the flow direction) and `r²_gas = 0.34`; it passes because
   `|dp/dx|/G = 1.59` is inside [0.5, 2.0]. Adding the physically required
   `dp/dx < 0` on both bands changes nothing measurable (h26 unchanged,
   `a40` stays 1.069897 with 12 probes), so this is not a gate flip — but it is
   a free hardening of the rule and should be added when the ladder is next
   touched.
5. **The attempt-2 `collect` step has no captured exit code.**
   `logs/collect.exit` is the attempt-1 artifact (mtime 10:11, unchanged in
   git), while the attempt-2 runs wrote `logs/collect2.log`, `collect3.log`,
   `collect4.log` (10:33–10:39) with no matching `.exit`; `collect2/3.log`
   contain tracebacks (`KeyError: 'V3_linearity'` — the intermediate naming
   state, honestly committed), and `PROVENANCE.md` asserts exit 0 for the
   attempt-2 collect without an artifact that binds it. The five headline
   tables therefore bind to their producer only through `.prov.json` sidecars
   that carry `exit_code: null`, plus `summary.json`'s embedded `prov`.
   Substantively fine — the console log is committed, the tables hash-verify,
   and I reproduced every number — but contract E's "shell exit code" is not
   satisfied for the step that produced the deliverable numbers. Add a MANIFEST
   entry for the collect run.
6. **Line-ending-dependent hashing inside one provenance set.** `prov()` hashes
   raw on-disk bytes; with `core.autocrlf=true` the same logical revision
   yields two SHA-256 values. `MANIFEST.json` mixes them: the per-run entries
   record `46a4b477…` (LF form of `tests/levelc_v1c.py` at `032d273`, i.e. the
   git blob form) while the top-level `producer_sha256` records `80550954…`
   (CRLF form of the same file at `fbb60ac`/HEAD, content identical —
   LF-normalized hash `cc6ec721…` = the HEAD blob). Readers must not interpret
   the two values as different revisions; state the convention in
   `PROVENANCE.md`.
7. **The superseded fit-region wording survives in the frozen evidence.** The
   source was corrected to `[12, buf0=14+L)` (line 231), but all four committed
   `dyn_*/report.json` still carry
   `"fit region [12,16+L) = open buffers + slit"` in `layout.note`, because
   `reanalyze` preserves the stored layout block. Attempt-1 NF6 is therefore
   half-fixed: the source is right, the evidence still asserts a
   two-columns-wider region. Harmless numerically (the code uses `psi[12:buf0]`),
   but the pending document must not quote it.
8. **A fully-invalid case would crash `collect` rather than fail explicitly.**
   `analyze_dynamic`'s empty-primary path is correct (explicit
   `window_fail_reason`, gates set to `None`, early return), but `collect`'s
   `drow()` reads `r['Pc_dynamic_median']` and `r['V_meas']` unconditionally, so
   such a report would raise `KeyError` instead of emitting a failure record.
   Loud, not silent, and untriggered by this candidate's evidence — worth
   hardening when the driver is next edited.

## Static coherence and interpretive cautions for the external review

No extrapolation model is forced here, per the reviewer contract. The sequence
is coherent: one producer revision (`032d273`), one measurement rule, four
points scattering ±3.9 % with no monotonic component, stationarity verified.
Carried forward unchanged from attempt 1 (the rework does not touch the static
side): the ±0.4–2.7 % band-extent sensitivity, the unexplained 18 % V1b↔V1c
spread at h=26 (now correctly attributed by the report to method **and**
protocol change, but not isolated), and the systematic ~10 % offset from
`cos 30° = 0.866` (θ_slit ≈ 38.6°) that must reach V2 as an open calibration
item rather than as a resolution artifact.

Two further cautions belong in the pending document, both visible in the
committed numbers:

- The h40-short primary's gas bands are not measured to better than ~±50 %:
  `|g_g|/G` spans 0.527–1.593 with median 0.815 across the 13 retained probes.
  `a40 − 1 = 7.0 %` therefore mixes physical excess resistance with a gas-side
  measurement limitation and must not be presented as pure physics. The h26
  case is much cleaner (`|g_g|/G` median 0.951, span 0.541–0.973).
- The h40 gate margin is real but thin: a probe-resampling bootstrap (10 000
  draws, primary sets) puts `a40` at 1.0613 / 1.0716 / 1.0928 (5 / 50 / 95 %)
  and `a26` at 1.0360 / 1.0437 / 1.0546. The gate holds in the upper tail, with
  ≈0.007 to spare at h40 — enough for a declared PASS on the contract's
  engineering gate, and exactly the kind of number the external scientific
  review needs.

## Technical-document deliverable (contract F)

`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md` in
the control checkout is still at "更新至 V1b external scientific review；V1c
尚未执行", and no V1c draft exists anywhere in the control checkout (the only
V1c-related control artifact is the untracked figure script). Per the closure
contract the update is sequenced *after* the fresh review, so NOT_RUN is
correct here — but the review must constrain the content, and this candidate is
now the right numeric base for it:

1. use the attempt-2 primary numbers (`C_static ≈ 0.782 ± 0.031`; `a26 =
   1.0436`, `a40 = 1.0699`), not attempt 1's contaminated `1.0454 / 1.0880`,
   and not the archived V1b two-point extrapolation (§11: `C_∞ ≈ 0.905`,
   `θ_∞ ≈ 25.2°`) which the four V1c points do not support;
2. report the estimator sensitivity honestly, including that `V3_r2_090` rests
   on 1 probe at h40 short and that the FAIL cells are the contaminated V0/V1
   (and V2-mean) aggregations;
3. state the 20-column margin's real justification (≥2× the mixed envelope;
   the 3h/4h margins are structurally impossible at h40 short) and drop the
   "9 interface widths" phrasing;
4. state the ~10 % registry offset and the 18 % h26 protocol spread as open
   items for V2, the `L_0/h` = 3.02/4.25 intercept, the 19–49 % jump share of
   `Pc,dyn`, and the h40 gas-side gradient spread;
5. correct the ≤0.6 % sensitivity claim to ≤0.94 % before quoting it, and do
   not quote the stale `[12,16+L)` fit region;
6. `figures/v1c_make_figs.py` (control checkout, untracked) still hardcodes
   `CAND = 'cfff538d…'` (the attempt-1 SHA) while reading the attempt-2
   evidence directory — it must be updated to `2b82f9a5…` before the SVGs are
   generated, and the SVGs must be regenerated from this candidate's committed
   tables with the SHA in the caption;
7. add the ten contract-F items (Task ID/base/candidate SHA, formulas, code
   excerpts, static table, static SVG, differential table, `L_eff` vs `L` SVG,
   before/after comparison, SOLVER/BC/VAL/DIAG/HARNESS statement, evidence
   paths and this decision).

## Blocking findings

None.

## Decision

Decision: PASS

## Rationale

The rework does what attempt 1 asked and does it verifiably. The two blocking
findings are resolved at the level of the measurement, not the wording: the
`Pc_dynamic` aggregate is now restricted to a declared, source-inspectable
per-probe validity rule and to the declared fit window; the contaminated
probes that attempt 1 identified are excluded explicitly and counted per
variant; every variant × estimator is published, including the cells that still
FAIL, and those FAIL cells reproduce attempt 1's numbers exactly. I reproduced
the candidate SHA/cleanliness/descent, the unchanged `front.csv`/`probes.csv`,
the reanalysis provenance binding, all 60 MANIFEST hashes, the static
`C_static(h)` chain (both from the reported values and from the committed axial
profiles), the front speeds, the whole validity ladder, and all 20
estimator-sensitivity cells from my own implementation — with the published
numbers agreeing to machine precision.

Both hard gates pass as declared (`a26 = 1.043640`, `a40 = 1.069897`), and the
PASS is robust: it survives median and mean within the primary rule, every
gradient-window width from [0.9, 1.11] to no filter at all, and every
positional margin I tested; the only failing configurations are the ones that
retain the contamination the candidate now declares as excluded. The declared
deviations from attempt 1's illustrative thresholds are transparently
documented, and the two substantive ones are evidence-backed (the 3h/4h margins
are structurally impossible at h40 short; the `r²` rungs are unusable there).
The physics reading is unchanged and now correctly decomposed: the distributed
resistance agrees with plane Poiseuille to ≈1 % / ≈4 % once the localized
boundary jumps are removed, and the remaining `a_h − 1` is dominated by those
jumps and by the documented intercept — consistent with the contract's framing
of the task.

This is not `HUMAN_REQUIRED`. None of the closure contract's human triggers is
met: no solver change is needed (the solver is untouched and V1b↔V1c front
speeds agree to ~1e-4); the static trend is coherent, reproducible and
non-erratic with a plateau identifiable; and the band method does identify
robust bulk regions (13–43 probes per case, all with gradients inside a factor
2 of the analytic value and, but for a single benign exception, the physically
required sign). The remaining findings are documentation accuracy, gate
labelling and provenance-completeness items. None of them changes a number, a
gate verdict, or the scientific reading, and all of them fall inside the
mandatory contract-F document update that is the next deliverable — where
finding NF1 in particular must be fixed before the numbers are quoted.

PASS means V1c is technically and scientifically ready for **external
scientific review**; it does not authorize V2. V2/V3 remain unauthorized. The
external review should be asked specifically about (i) the 20-column positional
margin at h=40 short, where only 3.2h of usable window exists and the primary
rests on 13 probes, (ii) whether `a40 − 1 = 7.0 %` may be read as physical
excess resistance given the gas-side gradient spread (0.53–1.59 × G), and
(iii) the `L_0/h` ≈ 3–4 intercept and the 19–49 % jump share of `Pc,dyn`.

## Exact next action

1. Write the contract-F update of
   `docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`
   on the control branch from **this** candidate's committed evidence, using the
   attempt-2 primary numbers (`a26 = 1.0436`, `a40 = 1.0699`,
   `C_static ≈ 0.782 ± 0.031`) and the ten required items; state the candidate
   SHA `2b82f9a5f448e756b5d5903b0df37f9a3b11d804` and this decision in it.
2. Before generating the figures, edit
   `docs/research/bilateral_imbibition/figures/v1c_make_figs.py`:
   `CAND = '2b82f9a5f448e756b5d5903b0df37f9a3b11d804'`, and make the gate
   annotations read the primary (`V3_gradient`) cells of
   `estimator_sensitivity.csv` rather than only `summary.json`, so a FAIL cell
   cannot be silently hidden; then regenerate both SVGs and confirm each
   caption states the candidate SHA.
3. In the same pass, correct the documentation/provenance defects the document
   would otherwise inherit: the dynamic threshold-sensitivity claim (≤0.94 %,
   not ≤0.6 %), the "9 interface widths" phrasing, the superseded `[12,16+L)`
   fit-region string, the `g8` labelling, a MANIFEST entry binding the collect
   step (command, timestamps, exit code), and a note in `PROVENANCE.md` on the
   LF/CRLF hashing convention. These are text/evidence-only edits on the
   control branch (or a follow-up product commit if the controller prefers the
   gate label to change in the driver); none requires a GPU run, and none
   changes a gate verdict, so no re-review is needed.
4. Hand the frozen candidate plus this review to external scientific review,
   with the three questions named in the Rationale explicitly in the cover
   note, and do not start V2/V3.
