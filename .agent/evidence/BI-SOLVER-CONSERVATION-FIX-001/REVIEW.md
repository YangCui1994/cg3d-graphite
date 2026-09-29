stage: conservation-fix
attempt: 4
candidate: e256b4857a6e51510b75358994d7c5bcc742781e
execution_report: results/conservation_fix/EXECUTION_REPORT.md

# REVIEW — BI-SOLVER-CONSERVATION-FIX-001 (attempt 4)

## Review mode and coverage

`FRESH_SESSION`, independent reviewer. Executor transcript not read. No GPU
work started, no simulation re-run; every check below is host-side on
committed evidence (git object comparison, independent SHA256 recomputation
of all 198 manifest entries, my own OLS re-fits of the raw F1 series with the
driver's exact definition, direct reads of the per-run JSON/CSV/log
artifacts). Nothing was modified except this file and `REVIEW_SESSION.json`.

Inspected: `AGENTS.md`; the reviewer contract
`SOLVER_CONSERVATION_FIX_REVIEWER_CONTRACT.md`; the attempt-4
`REVIEW_REQUEST.md`; `REVIEW_ATTEMPT_1.md`, `REVIEW_ATTEMPT_2.md` and
`REVIEW_ATTEMPT_3.md`; the full revision diff `b75253e..e256b48` and the
per-revision breakdown of the whole chain `1f5ee76..e256b48`; the worktree at
`cg3d-episode-worktrees/BI-SOLVER-CONSERVATION-FIX-001`; the revised
documents; `MANIFEST.json` and every file it lists; the raw F0/F1/A2/F3/F4
evidence; the frozen `results/levelc_v1c/` and `results/levelc_v2/`
baselines; `tests/run_level_a.py`; and the candidate solver's probe,
allocation, switch and C1-scope code.

Not inspected: the executor transcript (excluded by the review request); the
raw per-node F0 probe arrays, which by design are not in the archive — the F0
artifacts record per-node *statistics* over fluid nodes x 40 steps
(1 152 000 samples per quantity), so the literal per-node recomputation the
contract's section 5 asks for is only reproducible in-run; recomputing it
would require a `dbg_local=True` GPU rerun, which is outside a host-side
review and not authorized.

## 1. Revision integrity and scope — verified

| Check | Result | Evidence |
|---|---|---|
| Candidate / branch / clean worktree | PASS | `git rev-parse HEAD` = `e256b4857a6e51510b75358994d7c5bcc742781e`; branch `agent-task/BI-SOLVER-CONSERVATION-FIX-001`; `git status --porcelain` empty |
| Descends from audit candidate `1f5ee76` | PASS | `git merge-base --is-ancestor 1f5ee76 HEAD` true; chain `1f5ee76 -> 503f474 -> 9bd922d -> 46be3f2 -> e3d5a93 -> 2d45b9e -> 8554ee7 -> b75253e -> e256b48` |
| `git diff b75253e e256b48` lists only revision files | PASS | exactly 3 files, all under `results/conservation_fix/`: `CANDIDATE_COMPARISON.md` (5+/5−), `EXECUTION_REPORT.md` (2+/2−), `MANIFEST.json` (2+/2−) — 9 insertions / 9 deletions total; 0 files added, deleted or renamed; no REVIEW-side file touched |
| Solver and tests byte-identical between attempts | PASS | `git diff b75253e e256b48 -- lbm_solver_cg3d.py tests/` is empty (0 lines); solver blob hash `38bf419e…` identical at `2d45b9e`, `8554ee7`, `b75253e`, `e256b48` |
| Raw evidence untouched | PASS | 0 files changed outside `results/conservation_fix/`; 0 changes among `f0_*`, `f1_*`, `logs/**`, `levelc_v1c_fix/**`, `levelc_v2_fix/**` or any `*_report.json`; the 21 F0/F1 CSVs are present in both commits; across the full chain `2d45b9e..e256b48` the only changes outside the four documentation/derived files are the attempt-2 revision's already-accepted items (arXiv-corrected PDF swap, `a2_isolation*`, `logs/*.log`, `figures/*`, `LITERATURE_…`, `PROVENANCE.md`, `summary.json`) |
| MANIFEST integrity | PASS | `MANIFEST.json` = **198 entries**; I recomputed all 198 SHA256 values: **198/198 match**, 0 missing, 0 mismatch; `solver` field `d359fd036085096fbc47e275098b2cba2af8c15b3c42c2b35c84d4ec152b7fe2` equals `sha256sum lbm_solver_cg3d.py`; the entry key set is unchanged from attempt 3 and only the two revised documents' hashes were updated in the same commit |
| Frozen baselines intact | PASS | `results/levelc_v1c/`, `results/levelc_v2/`, `results/conservation_audit/` untouched by this revision |
| No V3 / porous-media work | PASS | 0 V3/porous artifacts in `results/`; V3-hold statement retained (`EXECUTION_REPORT.md:199-203`) |

The revision is exactly what it claims: a documentation-only correction with no
solver, test, gate or raw-data change.

## 2. Attempt-3 blocking item and optional sweeps — all implemented

### (1) Selected-candidate total-channel R² 0.81 -> 0.62 — FIXED and correct

`CANDIDATE_COMPARISON.md:77` now reads total slope `+1.19e-11`, **R² `0.62`**;
`EXECUTION_REPORT.md:88` reads "total **+1.19e-11/step** (R2 0.62 — no trend,
52.7% positive increments…)". Both agree with the committed artifact and with
my own recomputation:

| quantity | document | committed `f1_T3C1s_60k/f1_report.json` | my own refit |
|---|---|---|---|
| total slope | +1.19e-11 | +1.1944050796498566e-11 | +1.194405e-11 |
| total R² | **0.62** (both documents) | **0.6246387026270235** | **0.6246** |
| total final_rel | (not stated) | +1.1646096782502724e-06 | +1.1646e-06 |
| colour slope | −6.43e-10 | −6.425291352758677e-10 | −6.425291e-10 |
| colour R² | 0.983 | 0.9827035645829738 | 0.9827 |

My refit replicated the driver's definition exactly (`tests/conservation_fix.py:266-281`:
`drift = value/M0 - 1` with the committed `M0 = 28800.000429153442`, OLS of
`drift` on `step` over the 301 committed checkpoints of
`long_horizon_mass.csv`); agreement is 1.3e-19 on the slope and 6.5e-9 on R².
The `0.81` that the attempt-3 review blocked is gone from the selected row and
correctly remains on the adjacent rejected `T1+C1 60k` row, whose committed
value is 0.8127776117623615 -> 0.81.

I also machine-checked the whole F1 comparator table cell by cell against the
committed `f1_report.json` of every run it cites (10 rows x {total slope, total
R², colour slope, colour R²}): all cells agree at their displayed precision,
with one inherited exception recorded in §5(a).

### (2) MANIFEST regenerated for the changed hash — FIXED

The diff updates exactly `CANDIDATE_COMPARISON.md` (`e36771c6…` -> `7b2f6863…`)
and `EXECUTION_REPORT.md` (`fc0fbc5e…` -> `92a09433…`); the 198-entry key set is
unchanged, and my independent recomputation of all 198 hashes on the e256b48
tree gives 198/198 matches.

### (3) Probe-allocation sweep (10 fields / 12 values) — FIXED

`CANDIDATE_COMPARISON.md:172-174` now reads "…plus the **10** unconditional
per-node f64 probe fields (**12** f64 values per node incl. the 3-component
momentum; ~3 MB on C3, ~7 MB on V2; writes compiled out when dbg off)"; the
attempt-1 "11" is gone (`EXECUTION_REPORT.md:109` carries the same correction).
Verified against the solver constructor (lines 372-381): the declared probe
objects are `dbg_m0pre`, `dbg_sumpost`, `dbg_sumgr`, `dbg_sumb`, `dbg_delta`,
`dbg_dr`, `dbg_db`, `dbg_sumgr_eq`, `dbg_sumb_eq` (9 x `ti.field(ti.f64)`) plus
`dbg_mom` = `ti.Vector.field(3, ti.f64)` — i.e. **10 field objects / 12 f64
values per node**. The stated magnitudes match the domain sizes (~2.8 MB on C3's
34 776 cells, ~6.6 MB on V2's 82 152 cells), and the writes remain behind
`ti.static(self.dbg_local)`.

### (4) Production A2 gate N = 32 named — FIXED

`CANDIDATE_COMPARISON.md:121` now reads "the production gate in
`run_level_a.py` uses **N=32** and the full suite". `tests/run_level_a.py:20` is
`N = 32`, and that file is byte-identical to the base commit
(`git diff 1f5ee76 e256b48 -- tests/run_level_a.py` empty), so the named value is
the unmodified production gate.

### (5) Controller-side §17 publication — unchanged, correctly outside executor scope

The route record (`EXECUTION_REPORT.md:205-216`) is unchanged by this revision;
the solver-fix section is to be published on the control branch after this
review, per the controller-issued `START_CONSERVATION_FIX.md` §8 note. Carried
as a process item, not charged to this revision.

## 3. Attempt-3 scientific conclusions — still standing

The measurement evidence is byte-identical from attempt 1 through attempt 4
(§1), so the earlier recomputations apply unchanged. I re-derived the
load-bearing numbers directly from the committed artifacts:

- **F0 (selected T3+C1s, C3, 1 152 000 samples/quantity):** `R_f`
  −8.3479e-12 (frac_pos 0.4688, std 9.1902e-9, max 2.608e-8), `R_r`
  +9.7602e-11 (0.513), `R_b` +1.9554e-10 (0.489), `Req_r` +6.4533e-9,
  `Req_b` +5.0109e-9, `delta_f` **exactly 0.0**, momentum means
  −3.25e-12 / −1.03e-12 / −1.83e-12 with max 1.304e-8. Baseline T0: `R_f`
  +1.4889e-8 (frac_pos 0.660).
- **T4 negative control:** `R_f` +1.4940e-8 (frac_pos 0.940) with the *same*
  per-node std as T3 (9.1895e-9 vs 9.1902e-9), `dr`/`db` exactly 0 — f64
  accumulation with the unchanged f32 `inv_M` is insufficient, as the audit
  predicted.
- **F1:** total +1.1944e-11/step (R² 0.6246) vs baseline +1.5525e-8 (R² 1.0000)
  -> **1300x**; colour −6.4253e-10/step (R² 0.9827) vs +6.7617e-9 -> **10.5x**,
  inside the <=2e-9 target; my count of increments reproduces the documented
  52.7% positive (158/300). CPU 20k: total −3.303e-11 (R² 0.847), colour
  −6.853e-11 (R² 0.795) — backend-consistent and inside the disclosed
  ordering-dependent floor band (6.9e-11—1.6e-9); GPU 20k total +1.586e-11,
  colour −8.942e-10. The one-sided (negative) colour floor is stated with sign
  and spread, not denied.
- **A2:** committed `a2_isolation.json` reproduces exactly — T0+C0 0.0 PASS,
  T3+C0 0.0 PASS, T1+C0 / T2+C0 / T0+C1 / T1+C1 4.463e-06 FAIL, T4+C0
  3.103e-06 FAIL, T3+C1 0.0 PASS; the committed suite logs show
  `PASS A2 … max|v|=0.00e+00` for T0 and T3+C1s and `FAIL … 4.46e-06` for
  T1+C1. The gate (`max|v| < 1e-6`) is unmodified.
- **F3 (V1c):** static C = 0.790155 / 0.751291 / 0.807004 / 0.783381 (baseline
  0.790193 / 0.751095 / 0.806739 / 0.779494); differential a26 = 1.038877,
  a40 = 1.058149 (baseline 1.043640 / 1.069897), both inside |a−1| <= 0.10 and
  moved slightly toward 1; the four dynamic runs are `all_hard = true`; L0/h
  3.0530 / 4.3222 (baseline 3.0220 / 4.2489).
- **F4 (V2):** max |eps_r| 7.487e-5, max |eps_b| 1.976e-4 (baseline 4.207e-4 /
  6.730e-4 — 3.4x better on `eps_b`, inside the original 5e-4 gate value); front
  mirror error max 4.9591e-4 (baseline 1.2970e-3 — 2.6x better); a single
  trapped cluster throughout, no fragmentation, `INTERACTION_ONSET =
  NOT_REACHED`, `g6_mass_drift = true` where the baseline's was false; over
  60 000 steps; `all_hard = false` only because g4/g10 are null by design, as in
  the accepted baseline.
- **F2 committed-log pairs:** Laplace T0 `sigma=0.0610, rel 0.42%`, fix
  `sigma=0.0609, rel 0.35%`; contact T0 `34.0 deg`, fix `27.3 deg` — exactly the
  pairs both documents quote, with the run-to-run spread and the
  "not fix-attributable" marking retained.
- **Gates unchanged:** `git diff 1f5ee76 e256b48 -- tests/` is the new
  `tests/conservation_fix.py` plus one-line `LBM_OUTROOT` hooks in the two
  levelc drivers; every V0 gate file is untouched (the A2 threshold 1e-6 and the
  suite's other thresholds are unmodified).
- **Solver change scope:** 8 hunks — the T2/T3/T4 total-channel branches, the
  C1 block scoped to `cc > 0` with `sum_q w_q e_q = 0` weights, the static probe
  capture block, the constructor switches and the docstring. Production defaults
  are `T3`/`C1`, env-overridable (`lbm_solver_cg3d.py:280-285`); no physical
  parameter (CapA, psi_solid, contact angle, density, viscosity, geometry) is
  touched.
- **Performance:** the F10 claims use the same C3 grid and horizon and separate
  JIT from steady state: 60k T3+C1s 2479 steps/s (71.4 MLUPS) vs T0 ranges
  2352—2465 (67.7—71.0) and T3+C0 2355—2423; JIT one-time 296—348 s cold vs
  6.8 s cache-warm, matching the disclosed "~300 s / 6.8 s". Performance is
  reported as non-compensating for gates in both documents.

## 4. Answers to the reviewer contract's six final questions

1. **Is the original deterministic mass drift mechanism removed?** Yes, total
   channel. The 2^-26 stored-inverse representation defect is removed rather
   than compensated by the f64 roundtrip, and the local identity `R_f` is
   unbiased for the selected candidate (mean −8.3e-12, frac_pos 0.469 —
   sign-symmetric). The T4 control isolates the mechanism: same standard
   deviation, mean shifted to +1.494e-8 with 94% positive when the f32 `inv_M`
   is retained.
2. **Are total and colour channels both closed?** Total yes (+1.19e-11/step,
   R² 0.62, 52.7% positive increments, 1300x better than baseline). Colour is
   closed to a bounded, one-sided (negative), ordering-dependent floor at
   −6.43e-10/step — 10.5x better and inside the <=2e-9 target — with the sign
   stated for external review rather than denied.
3. **Does the selected fix preserve momentum locally?** Yes — `delta_f` is
   exactly 0.0 across all 1 152 000 F0 samples (the correction weights satisfy
   sum_q w_q e_q = 0), and the full-collision residual is ~1e-12 mean /
   1.30e-8 max per node, the f32 floor and negligible against rho·u.
4. **Does it preserve V0/V1c/V2 physics?** Yes at every unchanged gate: A2 exact
   (max|v| = 0.0), Laplace/contact inside their historical bands **and not
   fix-attributable** (T0 itself spans 0.26—0.42 % and 30.8—34.0°), hydraulic
   a26/a40 inside |a−1| <= 0.10 and slightly closer to 1, V2 mass drift 3.4x
   better and inside the original 5e-4 gate value, mirror error 2.6x better,
   trapped-pocket topology unchanged (single cluster, no fragmentation).
5. **Is the production choice preferable to full f64 on correctness /
   complexity / performance grounds?** Yes among the tested set: T3 *is* the
   f64 roundtrip (f64 matrix + f64 accumulator with f32 state on the GPU), and
   it is the only candidate passing F0, F1 and A2 simultaneously — T1 and T2 are
   eliminated by the A2 frozen-fixed-point failure (4.46e-06), T4 by F0. The
   measured steady-state cost is not resolvable (2479 vs 2352—2465 steps/s, i.e.
   within the run-to-run range). The residual cost to disclose is the
   unconditional probe allocation (~3 MB on C3, ~7 MB on V2), now stated
   correctly.
6. **Is V3 scientifically safe to reconsider?** Not by this review. V3 stays on
   HOLD; the conservation preconditions are substantively met, but even a PASS
   here returns to external scientific review, which is the only route that can
   lift the hold.

## 5. Minor observations carried forward (non-blocking)

**(a) One inherited display-rounding artifact.** `CANDIDATE_COMPARISON.md:71`
shows the T3+C0 20k total slope as `-6.40e-11`; the committed value is
−6.39478e-11, whose 3-significant-figure rounding is `-6.39e-11`. This is a
one-unit-in-the-last-displayed-place artifact (0.08% of the mantissa) on a
non-selected "reference floor" row. The line is byte-identical from attempt 1
through attempt 4 and no revision in the chain touched it; no gate, threshold or
conclusion depends on it. Worth sweeping in a future documentation pass, not a
reason to withhold acceptance.

**(b) One inherited basis ambiguity.** `EXECUTION_REPORT.md:87-88` states "60k
total drift 9.3e-4 -> ~7e-7". Both figures are the slope x 60 000 basis
(baseline 1.5525e-8 x 60 000 = 9.32e-4; selected 1.1944e-11 x 60 000 = 7.17e-7);
read that way the pair is self-consistent and is what yields the 1300x ratio.
The selected run's actual end-of-series `final_rel` is 1.1646e-6 (797x on that
basis). Both bases pass the >=10x gate by orders of magnitude, and the text is
unchanged since attempt 2 and was not part of the attempt-3 next action; stating
the basis explicitly would remove the ambiguity.

**(c) A2 parenthetical cross-reference (carried from attempt 3, unchanged).**
`CANDIDATE_COMPARISON.md:135` attributes the T1+C1 failure's "unscoped variant
failed identically" to the F2 suite log, whose committed run is the *scoped*
final-batch run; the unscoped observation rests on the superseded first batch and
is presented as history. The substance is unchanged and the labels are honest;
the cross-reference is imprecise.

**(d) Manifest self-exclusion (structural, inherited).** The evidence tree holds
200 files while the manifest lists 198: the two unlisted files are
`MANIFEST.json` and `levelc_v1c_fix/MANIFEST.json` themselves. This is a normal
self-exclusion and the same structure was present and accepted at attempt 3; no
unlisted measurement artifact exists.

## 6. Decision rationale

The attempt-3 exact next action is fully implemented and independently verified.
The blocking number is corrected to 0.62 in both required documents and matches
the committed `f1_T3C1s_60k/f1_report.json` (0.6246) exactly, including under my
own re-fit of the raw series using the driver's definition; the entire F1
comparator table now agrees with the committed machine-readable evidence at
displayed precision. The manifest was regenerated for the two changed document
hashes and re-verifies 198/198. Both optional sweeps were applied correctly —
the probe allocation is now stated as 10 per-node f64 fields / 12 f64 values per
node, which I confirmed against the constructor, and the production A2 gate's
N = 32 is named, which I confirmed against the untouched
`tests/run_level_a.py:20`. The revision is correctly scoped to documentation: the
solver and tests are byte-identical, no raw evidence or frozen baseline changed,
and no V3 or porous-media work exists. All attempt-3 scientific conclusions stand
under my own recomputation on evidence that is byte-identical since attempt 1,
and the three minor items in §5 are inherited cosmetic documentation artifacts
that affect no gate, threshold or conclusion.

Exact next action:

1. Owner/controller: hand this package to the external scientific review — the
   only route that can lift the V3 HOLD. This review authorizes neither V3 nor
   promotion of the fix.
2. Controller/owner: publish the §17 solver-fix section on the
   control/integration branch with the committed figures (as already recorded in
   `EXECUTION_REPORT.md:205-216`).
3. Optional, next documentation pass (not required for acceptance): sweep the two
   inherited cosmetic items — `CANDIDATE_COMPARISON.md:71` total slope
   `-6.40e-11` -> `-6.39e-11`, and state the "60k total drift" basis in
   `EXECUTION_REPORT.md:87-88`; and, if convenient, generate the F1/F2 table rows
   from `f1_report.json` / the committed logs to retire this defect class
   permanently.
4. No solver, physics, gate or simulation change is required; V3 stays HOLD.

Decision: PASS — the attempt-4 revision implements the attempt-3 exact next action with no new defect: `git diff b75253e e256b48` is exactly three files, all under `results/conservation_fix/` (CANDIDATE_COMPARISON.md, EXECUTION_REPORT.md, MANIFEST.json; 9 insertions / 9 deletions), the solver and tests are byte-identical (solver blob `38bf419e…` unchanged across all four attempts), zero raw-evidence or frozen-baseline files changed, and MANIFEST re-verifies 198/198 with the solver hash `d359fd03…` matching `sha256sum lbm_solver_cg3d.py`; the selected-candidate total-channel R² now reads 0.62 in both CANDIDATE_COMPARISON.md:77 and EXECUTION_REPORT.md:88, matching the committed `f1_T3C1s_60k/f1_report.json` (0.6246387026270235 -> 0.62) and my own independent re-fit of the raw 301-checkpoint series with the driver's exact definition (+1.194405e-11/step, R² 0.6246, final_rel 1.1646e-06 — agreement 1.3e-19 on the slope), with the `0.81` correctly confined to the rejected T1+C1 60k row (committed 0.8128) and every other F1 table cell matching its committed report; the two optional sweeps are correctly applied and verified in code (10 per-node f64 probe fields = 12 f64 values per node, confirmed at `lbm_solver_cg3d.py:372-381`; production A2 gate N = 32 named, confirmed at `tests/run_level_a.py:20` on a file byte-identical to base); the attempt-3 scientific conclusions stand on evidence byte-identical since attempt 1 — F0 selected `R_f` −8.3479e-12 (frac_pos 0.4688) with `delta_f` exactly 0.0 and momentum residual ~1e-12 mean / 1.30e-8 max, T4 negative control `R_f` +1.4940e-8 (0.940) at identical std proving f64 accumulation with f32 `inv_M` insufficient, F1 total 1300x (baseline 1.5525e-8 -> 1.1944e-11) with 52.7% positive increments reproduced exactly and colour 10.5x inside the <=2e-9 target with the one-sided floor disclosed, A2 exact stationarity for T3+C1 (0.0 PASS) with T1+T2 eliminated at 4.46e-06 against an unmodified 1e-6 gate, F3 a26 1.038877 / a40 1.058149 inside the unchanged |a−1| <= 0.10 gates and L0/h 3.0530 / 4.3222, and F4 max|eps_b| 1.976e-4 (3.4x better, inside the original 5e-4 value) with mirror error 4.9591e-4 (2.6x), a single trapped cluster and no fragmentation; the only remaining findings are three inherited cosmetic documentation artifacts (a 0.08% display-rounding difference on the non-selected T3+C0 20k slope, the unstated slope basis behind "60k total drift ~7e-7", and an imprecise A2 log cross-reference) that affect no gate, threshold or conclusion — next action: owner/controller hands the package to the external scientific review, which is the only route that can lift the V3 HOLD, and publishes the §17 solver-fix section on the control branch; the two cosmetic items and generating the F1/F2 tables from `f1_report.json` are optional future documentation work; no solver, physics, gate or simulation change is required, V3 stays HOLD, and this review authorizes neither V3 nor promotion of the fix.
