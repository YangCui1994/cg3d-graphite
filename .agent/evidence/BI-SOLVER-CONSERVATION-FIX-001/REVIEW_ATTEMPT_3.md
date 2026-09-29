stage: conservation-fix
attempt: 3
candidate: b75253e01efa8ee5a2ebd1ed61501274ebe902da
execution_report: results/conservation_fix/EXECUTION_REPORT.md

# REVIEW — BI-SOLVER-CONSERVATION-FIX-001 (attempt 3)

## Review mode and coverage

`FRESH_SESSION`, independent reviewer. Executor transcript not read. No GPU
work started, no simulation re-run; every check below is host-side on
committed evidence (git object comparison, independent SHA256 recomputation
of all 198 manifest entries, my own OLS re-fits of the raw F1 CSVs, direct
reads of the per-run JSON/CSV/log artifacts). Nothing was modified except
this file and `REVIEW_SESSION.json`.

Inspected: `AGENTS.md`; the reviewer contract; the attempt-3
`REVIEW_REQUEST.md`; `REVIEW_ATTEMPT_1.md` and `REVIEW_ATTEMPT_2.md`; the
full revision diff `8554ee7..b75253e`; the worktree at
`cg3d-episode-worktrees/BI-SOLVER-CONSERVATION-FIX-001`; the revised
documents; `MANIFEST.json` and every file it lists; the raw F0/F1/A2/F3/F4
evidence; the frozen `results/levelc_v1c/`, `results/levelc_v2/` baselines;
`tests/run_level_a.py`; and the candidate solver's probe/allocation and C1
scope code.

## 1. Revision integrity and scope — verified

| Check | Result | Evidence |
|---|---|---|
| Candidate / branch / clean worktree | PASS | `git rev-parse HEAD` = `b75253e01e…`; branch `agent-task/BI-SOLVER-CONSERVATION-FIX-001`; `git status --porcelain` empty |
| Descends from audit candidate `1f5ee76` | PASS | ancestor check true; chain `1f5ee76 → 503f474 → 9bd922d → 46be3f2 → e3d5a93 → 2d45b9e → 8554ee7 → b75253e` |
| `git diff 8554ee7 b75253e --stat` lists only revision files | PASS | exactly 4 files, **all** under `results/conservation_fix/`: `CANDIDATE_COMPARISON.md` (+21/−8), `EXECUTION_REPORT.md` (1 line), `MANIFEST.json` (3 hash lines), `summary.json` (2 F2 blocks). Nothing added, deleted or renamed |
| Solver and tests byte-identical between attempts | PASS | `git diff 8554ee7 b75253e -- lbm_solver_cg3d.py tests/` is empty (0 lines); no file outside `results/conservation_fix/` touched |
| Raw evidence untouched | PASS | 541 files present in **both** commits; only the 4 documented files differ; zero `f0_*`/`f1_*` CSVs, per-run `*_report.json`, `logs/**`, `levelc_v1c_fix/**`, `levelc_v2_fix/**` or frozen-baseline file changed |
| MANIFEST integrity | PASS | `MANIFEST.json` = **198 entries**; I recomputed all 198 SHA256 values: **198/198 match**, 0 missing, 0 mismatch; `solver` field `d359fd03…` equals `sha256sum lbm_solver_cg3d.py`; the three changed documents' hashes were updated in the same commit |
| Frozen baselines intact | PASS | `results/levelc_v1c/`, `results/levelc_v2/`, `results/conservation_audit/` untouched by this revision |
| No V3 / porous-media work | PASS | no V3 artifact; V3-hold statement retained (`EXECUTION_REPORT.md:199-203`) |

The revision is exactly what it claims: a documentation/derived-artifact
revision with no solver, test, gate or raw-data change.

## 2. Item-by-item verification of the attempt-2 finding set

### (1) EXECUTION_REPORT arXiv identifier — FIXED

`EXECUTION_REPORT.md:35` now reads "`literature/` (arXiv 2412.17426,
2112.08926)". Package-wide, the string `2202.05643` now occurs only twice,
both as the deliberate erratum records in
`LITERATURE_AND_IMPLEMENTATION_SEARCH.md:69` and `:176`, which is correct
and should stay. `2112.08926` appears 5×.

### (2) F1 table: selected rows and the T1+C1 rejection label — FIXED, one wrong number introduced

Both requested changes are present: the T1+C1 60k row is relabelled
"initial selection, **rejected by A2** (kept for history)" (`:76`), and the
selected candidate's rows were added (`:77` T3+C1s 60k, `:78` T3+C1s CPU
20k). I re-fit the raw CSVs myself with my own OLS code (301 checkpoints of
each 60k run, drift referenced to each run's own `M0`):

| row | document | committed `f1_report.json` | my own refit | verdict |
|---|---|---|---|---|
| T3+C1s 60k total | +1.19e-11 | +1.19441e-11 | +1.19441e-11 (R² 0.6246) | value correct |
| T3+C1s 60k total R² | **0.81** | **0.6246** | **0.6246** | **WRONG** |
| T3+C1s 60k colour | −6.43e-10 | −6.42529e-10 | −6.42529e-10 (R² 0.9827) | correct |
| T3+C1s CPU 20k total | −3.30e-11 (R² 0.85) | −3.30271e-11 (R² 0.8474) | −3.30271e-11 (R² 0.8474) | correct |
| T3+C1s CPU 20k colour | −6.85e-11 (R² 0.795) | −6.85289e-11 (R² 0.7951) | −6.85289e-11 (R² 0.7951) | correct |

**Defect (new, blocking-class, one character).** The newly added selected-
candidate row states a total-channel **R² of 0.81**. The committed
`f1_T3C1s_60k/f1_report.json` `drift_fits.Mff.r2` is **0.6246**, my
independent refit of `long_horizon_mass.csv` gives **0.6246**, and the
package's own `EXECUTION_REPORT.md:88` states "total **+1.19e-11/step**
(R2 0.62 — no trend…)". The 0.81 is the value of the row directly above it,
T1+C1 60k (`drift_fits.Mff.r2` = 0.8128) — i.e. the R² was copied from the
adjacent, rejected candidate's row. The consequence is not cosmetic: in the
comparator table the *selected* candidate now appears to fit its total
channel as tightly as the candidate A2 rejected (both "0.81"), whereas the
committed data make the selected candidate's total fit distinctly weaker
(0.62 vs 0.81); and `CANDIDATE_COMPARISON.md` now contradicts
`EXECUTION_REPORT.md` on the same quantity. The slope, the ~1300×
improvement and every gate conclusion are unaffected.

### (3) Committed-log F2 pairs with spread wording in both documents — FIXED

Committed logs verified directly: `logs/f2_laplace_T0.log` = `sigma=0.0610
(expect 0.0607, rel 0.42%)`; `logs/f2_contact_T0.log` = `theta_liq = 34.0
deg`; `logs/f2_laplace_T3C1s.log` = `rel 0.35%`;
`logs/f2_contact_T3C1s.log` = `theta_liq = 27.3 deg`.
`CANDIDATE_COMPARISON.md:184-188` now uses exactly those pairs, states the
T0 run-to-run spread (Laplace 0.26–0.42 %, contact 30.8–34.0 ° across the
two T0 batches) and marks both pairs "not fix-attributable";
`EXECUTION_REPORT.md:115-132` already carried the same. The superseded
"0.26 % / 30.8°" before-values survive only as the disclosed spread
endpoints, with the first-batch provenance stated.

### (4) `summary.json` `f2_v0` regenerated from the committed logs — FIXED

`f2_v0.laplace.T0_sigma_rel` = 0.0042 and `f2_v0.contact_angle.T0_theta` =
34.0 now match `logs/f2_laplace_T0.log` (0.42 %) and
`logs/f2_contact_T0.log` (34.0°); the after-fix entries 0.0035 / 27.3 match
their logs; both blocks gained a `note` recording the committed-log basis,
the spread and the not-fix-attributable marking. `MANIFEST.json` carries the
new `summary.json` hash (`6e04ba80…`), which my recomputation confirms.
`summary.json` carries no R² values at all, so the wrong R² below appears in
`CANDIDATE_COMPARISON.md` only.

### (5) "no new per-node fields" → probe-allocation wording — FIXED (one minor count issue, inherited)

The claim is gone from the package (`grep "no new per-node"` = 0 hits);
`CANDIDATE_COMPARISON.md:172-174` now reads "one 19x19 f64 table, plus the
11 unconditional per-node f64 probe fields (~3 MB on C3, ~7 MB on V2; writes
compiled out when dbg off)". I verified each element against the solver: the
table is `inv_M_f64 = ti.field(ti.f64, shape=(19,19))` (line 91), the
allocation is unconditional in the constructor (lines 371-381) while writes
sit behind `ti.static(self.dbg_local)` (lines 678, 742), and the "~3 MB /
~7 MB" magnitudes are right for the domain sizes (34 776 cells on C3,
82 152 on V2).

**Minor count issue (non-blocking, inherited from attempt 2's report
wording, now propagated into the comparison).** The constructor declares
**10** f64 probe field objects — `dbg_m0pre`, `dbg_sumpost`, `dbg_sumgr`,
`dbg_sumb`, `dbg_mom` (a `Vector.field(3, f64)`), `dbg_delta`, `dbg_dr`,
`dbg_db`, `dbg_sumgr_eq`, `dbg_sumb_eq` — i.e. 9 scalars + 1 three-component
vector = **12 f64 values per node** (10 × 8 B = 2.8 MB / 6.6 MB; 12 × 8 B =
3.3 MB / 7.9 MB over all cells). The stated "11" matches neither count; it
does match the number of distinct quantities reported in the F0 CSV
(`R_f, R_r, R_b, Req_r, Req_b, mom_x, mom_y, mom_z, delta_f, dr, db` = 11
quantities). The disclosure's substance is correct and the memory estimates
are of the right order, so this changes no conclusion — the phrase should
read "10 per-node f64 probe fields (12 f64 values per node)" or similar.

### (6) A2 table labels aligned with the committed artifact — FIXED

The three C1 rows now read "(scoped, committed)" and the table carries the
provenance note "(grid N=24, 200 steps; the production gate in
`run_level_a.py` uses its own N and the full suite; C1 rows in the committed
generator run under the CURRENT scoped code…)". Verified: the committed
generator `a2_isolation_check.py` runs `a2(fix, cf, N=24, steps=200)` over 9
combos and writes `a2_isolation.json` (`grid: 24`, `steps: 200`) — so the
json rows are scoped runs, exactly as the new labels say; the solver exposes
only the scoped C1 switch (`self.colour_fix in ('C0','C1')`, line 285;
scoped block at line 712). Table values match the json: T0+C0 0.0, T3+C0
0.0, T3+C1 0.0 (PASS); T1+C0 / T2+C0 / T0+C1 / T1+C1 4.463e-06 (json
4.462895503820619e-06), T2+C1 4.463e-06 (json 4.4628959585679695e-06),
T4+C0 3.103e-06 (json 3.1031652270030463e-06) — FAIL, all gates false in
the json.

Two non-blocking precision remarks: (a) the note says the production gate
"uses its own N" without naming it — the value is N = 32
(`tests/run_level_a.py:20`), and naming it would close the attempt-2 request
verbatim; (b) the parenthetical "the pre-scoping unscoped variants failed
identically, see `logs/f2_levelA_T1C1.log`" cites a log whose run is the
*scoped* final-batch run (`FAIL A2 uniform phase stationary max|v|=4.46e-06`,
committed at `e3d5a93`); the unscoped observation rests on the superseded
first batch, as recorded in the attempt-1/2 reviews, and is presented as
history rather than as committed evidence — which is honest, but the cross-
reference points at the scoped log.

### (7) §17 publication route — unchanged; controller action, not charged to this revision

The route record (`EXECUTION_REPORT.md:205-216`) is unchanged by this
revision: the living document exists only on the control/integration branch,
and the solver-fix section is to be published there after this review. Per
the controller-issued `START_CONSERVATION_FIX.md` §8 note in the review
request, this remains outside executor scope and executes after the review.
Carried forward as a process item (see §5).

## 3. Attempt-2 scientific conclusions — still standing

The raw evidence is byte-identical between attempts 2 and 3 (541 common
files, zero raw-evidence changes), so attempt-2's recomputations apply
unchanged; I re-checked the load-bearing numbers directly on the committed
artifacts:

- **F0 (selected T3+C1s, C3):** `R_f` −8.348e-12 (frac_pos 0.469), `R_r`
  +9.760e-11 (0.513), `R_b` +1.955e-10 (0.489), `delta_f` exactly 0 (the
  correction's momentum residual is identically zero), `mom` means
  −3.25e-12 / −1.03e-12 / −1.83e-12 with max 1.304e-8. Baseline T0: `R_f`
  +1.489e-8 (frac_pos 0.660). **T4 negative control:** `R_f` +1.494e-8
  (frac_pos 0.940) with the *same* std as T3 (9.190e-9 both) — f64
  accumulation with the unchanged f32 `inv_M` is insufficient, as the audit
  predicted.
- **F1:** total +1.1944e-11/step vs baseline +1.5525e-8 (~1300×); colour
  −6.4253e-10/step vs +6.7617e-9 (10.5×, inside the ≤2e-9 target); the
  bounded one-sided (negative) floor is stated with sign and spread, and the
  "no monotone bias" claim is gone.
- **A2:** T0 0.0 PASS, T1+C1 FAIL 4.46e-6, T3+C1s 0.0 PASS — unchanged gate
  (`max|v| < 1e-6`, `run_level_a.py:66`).
- **F3 (V1c):** static C = 0.790155 / 0.751291 / 0.807004 / 0.783381
  (baseline 0.790193 / 0.751095 / 0.806739 / 0.779494); differential a26 =
  1.038877, a40 = 1.058149, both gates true (baseline 1.043640 / 1.069897);
  L0/h 3.0530 / 4.3222 vs baseline 3.0220 / 4.2489.
- **F4 (V2):** max eps_r 7.487e-5, max eps_b 1.976e-4 (baseline 4.208e-4 /
  6.730e-4, i.e. inside the original 5e-4 g6 value); g6 true where the
  baseline's was false; mirror error 4.959e-4 (baseline 1.297e-3); single
  trapped cluster; V_bin change identical at 0.2506 %; 60 000 steps;
  `all_hard=false` only because g4/g10 are null by design, as in the
  accepted baseline.
- **Gates unchanged:** `git diff 1f5ee76 b75253e -- tests/` touches only the
  new `conservation_fix.py` and the one-line `OUTROOT` env hooks in the two
  levelc drivers; every V0 gate file is untouched and the A2/A3 thresholds
  (1e-6, 5e-6) are unmodified.

## 4. Answers to the reviewer contract's six final questions

1. **Original drift mechanism removed?** Yes, total channel: the 2⁻²⁶
   stored-inverse defect is removed (not compensated) by the f64 roundtrip,
   and the local identity `R_f` is unbiased for the selected candidate.
2. **Total and colour both closed?** Total yes (+1.19e-11/step, no trend).
   Colour closed to a bounded, one-sided (negative), ordering-dependent
   floor at −6.43e-10/step, inside the ≤2e-9 target; that sign is stated for
   external review rather than denied.
3. **Momentum preserved locally?** Yes — `delta_f` is exactly 0.0 in the
   committed F0 CSV (the correction weights satisfy `sum_q w_q e_q = 0`), and
   the full-collision residual is ~1e-12 mean / 1.30e-8 max per node, the f32
   floor and negligible against rho·u.
4. **V0/V1c/V2 physics preserved?** Yes at every unchanged gate. Surface
   tension 0.35 % and contact angle 27.3° are inside their historical bands,
   but the before/after pairs are **not** fix-attributable (T0 itself spans
   0.26–0.42 % and 30.8–34.0°); hydraulic slope (a26/a40) and trapped-pocket
   topology are unchanged.
5. **Is the production choice preferable to full f64?** Yes among the tested
   set: T3+C1s is the only candidate passing F0, F1 and A2 simultaneously;
   T3 *is* the f64 roundtrip (f64 matrix + f64 accumulator with f32 state),
   at no resolvable steady-state throughput cost. The residual cost to
   disclose is the unconditional probe allocation (see §2 item 5).
6. **Is V3 scientifically safe to reconsider?** Not by this review. V3 stays
   on HOLD; the conservation preconditions are substantively met but even a
   PASS here returns to external scientific review, which is the only route
   that can lift the hold.

## 5. Decision rationale

The revision does what it claims in substance and the fix itself is
scientifically unchanged and re-confirmed: the solver and tests are
byte-identical, all raw evidence is untouched, the manifest re-verifies
198/198, and the arXiv identifier, F2 committed-log pairs, `summary.json`
`f2_v0`, probe-allocation wording and A2 labels are all implemented and
checkable against committed artifacts. The attempt-2 F0/F1/A2/F3/F4
conclusions stand under my own recomputation.

What prevents PASS is one newly introduced number of exactly the class that
blocked attempts 1 and 2 — a figure in a required product that the package's
own committed evidence contradicts:

- `CANDIDATE_COMPARISON.md:77` gives the **selected** candidate's total-
  channel R² as **0.81**; the committed `f1_T3C1s_60k/f1_report.json` says
  0.6246, my independent refit says 0.6246, and `EXECUTION_REPORT.md:88` of
  the same package says 0.62. The 0.81 belongs to the adjacent, rejected
  T1+C1 row (0.8128). This makes the selected candidate's total-channel fit
  look as good as the rejected candidate's, and leaves the two required
  documents contradicting each other on the same quantity.

Two minor accuracy items worth sweeping in the same pass (non-blocking on
their own): the probe count "11" should be 10 per-node f64 fields / 12 f64
values per node, and the A2 note could name the production gate's N = 32.

Exact next action (documentation-only; then resubmit for fresh review):

1. `CANDIDATE_COMPARISON.md:77` — change the T3+C1s 60k total R² from **0.81
   to 0.62** (committed value 0.6246, consistent with `EXECUTION_REPORT.md:88`).
2. Regenerate `results/conservation_fix/MANIFEST.json` for the changed
   `CANDIDATE_COMPARISON.md` hash (the manifest is the only other file to
   touch; no raw-evidence file changes, so the 198-entry set is unchanged).
3. Optional, same pass: `CANDIDATE_COMPARISON.md:172-174` and
   `EXECUTION_REPORT.md:109` — state the probe allocation as 10 per-node f64
   fields (12 f64 values per node); `CANDIDATE_COMPARISON.md:120-124` — name
   the production A2 gate's N = 32 (`tests/run_level_a.py:20`).
4. Controller/owner (unchanged, outside executor scope): publish the §17
   solver-fix section on the control branch with the committed figures.
5. No solver, physics, gate or simulation work is required; V3 stays HOLD.

Process note for the owner: this is the third consecutive round whose only
blocking defect is a hand-typed number in a derived table that disagrees
with a committed machine-readable artifact. Generating the F1/F2 table rows
from `f1_report.json` / the committed logs (or adding a small doc-vs-evidence
checker to the batch) would stop this class from recurring.

Decision: CHANGES_REQUESTED — the attempt-3 revision is correctly scoped and the attempt-2 finding set is otherwise fully implemented (arXiv id fixed, F1 selected rows and the T1+C1 rejection label added, committed-log F2 pairs with spread wording in both documents, `summary.json` `f2_v0` regenerated from the committed logs, probe-allocation wording replacing "no new per-node fields", A2 labels aligned with the committed scoped generator), the solver and tests are byte-identical, raw evidence is untouched and MANIFEST re-verifies 198/198, and the attempt-2 F0/F1/A2/F3/F4 conclusions stand under independent recomputation — but the newly added selected-candidate row states a total-channel R² of 0.81 where the committed `f1_T3C1s_60k/f1_report.json`, my own CSV refit and the package's own EXECUTION_REPORT.md:88 all give 0.62 (0.6246), the 0.81 having been copied from the adjacent rejected T1+C1 row, so the comparator table overstates the selected candidate's total-channel fit and contradicts a sibling required deliverable; next action: correct that single value in `CANDIDATE_COMPARISON.md:77`, regenerate the `CANDIDATE_COMPARISON.md` hash in `MANIFEST.json`, optionally sweep the probe-count "11" → 10 fields / 12 values per node and name the production A2 gate's N = 32, then resubmit for fresh review — no solver, physics, gate or simulation change is needed, and this review authorizes neither V3 nor promotion of the fix.
