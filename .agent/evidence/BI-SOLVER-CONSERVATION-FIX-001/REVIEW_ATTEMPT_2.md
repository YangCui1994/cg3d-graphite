stage: conservation-fix
attempt: 2
candidate: 8554ee78b6d3d6d28bdb4943dbe1768f27adaaf4
execution_report: results/conservation_fix/EXECUTION_REPORT.md

# REVIEW — BI-SOLVER-CONSERVATION-FIX-001 (attempt 2)

## Review mode and coverage

`FRESH_SESSION`, independent reviewer. Executor transcript not read. No GPU
work was started, no simulation was re-run; all recomputation is host-side on
committed evidence (SHA256 checks, git object comparison, CSV re-fits, PDF
text extraction). Nothing was modified except this file and
`REVIEW_SESSION.json`.

Inspected: `AGENTS.md`; the reviewer contract; the authorizing audit reviews
and the literature note; `START_CONSERVATION_FIX.md` §8; the solver-fix
contract §§16–19; the attempt-2 `REVIEW_REQUEST.md`; `REVIEW_ATTEMPT_1.md`;
the full revision diff `2d45b9e..8554ee7`; the worktree at
`cg3d-episode-worktrees/BI-SOLVER-CONSERVATION-FIX-001`; the revised
documents and all new artifacts; the raw F0/F1/F2/F3/F4 evidence; the
living technical document on the control branch.

## 1. Revision integrity and scope — verified

| Check | Result | Evidence |
|---|---|---|
| Candidate / branch / clean worktree | PASS | `git rev-parse HEAD` = `8554ee78…`; branch `agent-task/BI-SOLVER-CONSERVATION-FIX-001`; `git status --porcelain` empty |
| Descends from audit candidate `1f5ee76` | PASS | `1f5ee76` is an ancestor; chain `1f5ee76 → 503f474 → 9bd922d → 46be3f2 → e3d5a93 → 2d45b9e → 8554ee7` |
| `git diff 2d45b9e 8554ee7 --stat` lists only revision files | PASS | 15 files, **all** under `results/conservation_fix/`: 9 modified (4 docs, `MANIFEST.json`, `PROVENANCE.md`, figure generator, 3 SVGs), 5 added (`a2_isolation.json`, `a2_isolation_check.py`, corrected PDF, `logs/a2_isolation.log`, `logs/final_batch_exit_codes.log`), 1 deleted (the misattributed PDF) |
| Solver and tests byte-identical between attempts | PASS | `git diff 2d45b9e 8554ee7 -- lbm_solver_cg3d.py tests/` is empty; nothing outside `results/conservation_fix/` changed |
| No raw evidence file modified | PASS | enumerated all 536 files present in **both** commits: only the 9 documented docs/derived files differ; zero `f0_*`/`f1_*` CSVs, per-run `*_report.json`, logs, `levelc_v1c_fix/**`, `levelc_v2_fix/**` or frozen baseline file touched |
| Manifest integrity | PASS | `MANIFEST.json` = 198 entries, 0 missing, **198/198 SHA256 recomputed and matching** by me; contains the corrected PDF, excludes the deleted one; solver hash `d359fd03…` matches `sha256sum lbm_solver_cg3d.py` |
| Frozen baselines intact | PASS | `results/levelc_v1c/`, `results/levelc_v2/`, `results/conservation_audit/` untouched by the revision |
| No V3 / porous-media work | PASS | no V3 artifact; V3-hold statement retained (`EXECUTION_REPORT.md:199-203`) |

The revision is exactly what it claims to be: a documentation/derived-artifact
revision with no solver, test, gate or raw-data change.

## 2. Correction-by-correction verification

### (1) B1 — literature source (faithful, one leftover)

Independently extracted the replaced PDF: 30 pages, title page =
Lehmann, Krause, Amati, Sega, Harting, Gekle, "On the accuracy and performance
of the lattice Boltzmann method with 64-bit, 32-bit and novel 16-bit number
formats"; full-text count 47 × "lattice Boltzmann" (exactly the number the
report claims), 1 × `2112.08926`, **0 × `2202.05643`**. The old file is
deleted and absent from the manifest. `LITERATURE_AND_IMPLEMENTATION_SEARCH.md`
now cites arXiv:2112.08926 with the verified title (lines 57–67), carries an
explicit erratum for the revision-1 misattribution (68–73), and the access-log
row is corrected with the erratum (176).

**Leftover (blocking-class, one line):** `EXECUTION_REPORT.md:35` still reads
"Key sources downloaded to `literature/` (arXiv 2412.17426, **2202.05643**)"
— the stale wrong identifier persists in the primary required deliverable and
contradicts the corrected search report and the actual `literature/` contents.

### (2) B2 — momentum values (faithful, verified against the CSVs)

Read from `f0_*/f0_local_identities.csv` (C3 block, n = 1 152 000 = 28 800
nodes × 40 steps): selected T3+C1s `mom_x/y/z` means −3.25e-12 / −1.03e-12 /
−1.83e-12, max 1.3038e-8; T0+C0 max 2.7940e-8; T2+C0 max 2.7940e-8; T1+C1 max
4.2841e-8 with **`mom_x` mean −1.4833e-8 and `mom_y` mean −1.4830e-8**
(frac_pos 0.022/0.017 — a one-sided systematic bias). Both named locations
(`CANDIDATE_COMPARISON.md:49-62`, `EXECUTION_REPORT.md:68-80`) now carry these
values and disclose T1's x/y side-effect and its mechanical origin. The old
"≤ 2.2e-8 / all candidates equal" claim is gone.

### (3) B3 — colour channel (faithful; my own refit reproduces it)

I refit every `f1_*` series from the raw CSVs with my own OLS code using the
driver's own definition (`Mc` = (Mr+Mb)/M0, `Mff` = Σf/M0;
`tests/conservation_fix.py:266-281`): T0+C0 60k total +1.5525e-8 (R² 1.0000),
colour +6.7617e-9 (R² 0.9960); **T3+C1s 60k total +1.1944e-11 (R² 0.6246),
colour −6.4253e-10 (R² 0.9827)**; T1+C1 60k total +2.8667e-11, colour
−1.3035e-9. Improvement ≈ 1300× total, 10.5× colour — matches the documents.
One-sidedness reproduced: colour increments **299/300 negative** (298/300
checkpoint values negative) versus the baseline 0/300 negative (final
+4.208e-4, 0.2106e-3-scale); final fixed-run colour drift **−4.0454e-5**
(= the committed `f1_report.json` `drift_fits.Mc.final_rel` −4.04538e-5,
quoted as −4.05e-5). Cross-variant/backend spread reproduced from the
committed reports: Mc slopes span **−6.85e-11 … −1.59e-9** (T3C1s CPU 20k …
T2C1 20k), matching the stated 6.9e-11–1.6e-9. The "no monotone bias" claim
is removed in both documents and replaced by an explicit bounded one-sided
(negative) floor statement with sign, magnitude, spread and the ~90 % removal
decomposition (6.09e-9/node × 28 800 = 1.75e-4/step vs baseline
6.76e-9 × 28 800 = 1.95e-4/step).

### (4) B4 — F2 before/after (faithful in the report; two products left stale)

Verified directly: `logs/f2_laplace_T0.log` = 0.42 % rel (σ = 0.0610 vs 0.0607),
`logs/f2_contact_T0.log` = 34.0°; after-fix `logs/f2_laplace_T3C1s.log` =
0.35 %, `logs/f2_contact_T3C1s.log` = 27.3°. `EXECUTION_REPORT.md:115-132`
now uses exactly these committed-log values, states the run-to-run spread
(Laplace 0.26–0.42 %, contact 30.8–34.0°) and explicitly marks the pairs **not
fix-attributable**.

**Leftovers (B4 class):** `CANDIDATE_COMPARISON.md:178-179` still presents
"Laplace (0.26% -> 0.35% rel), contact angle (30.8 -> 27.3 deg)" — the
superseded values, with no spread/not-attributable note; and `summary.json`
(`f2_v0`) still carries `T0_sigma_rel = 0.0026`, `T0_theta = 30.8`, i.e. the
same untraceable before-values in the machine-readable §16 product.

### (5) B5 — §17 living document (record added; publication is controller-side)

`EXECUTION_REPORT.md:205-216` now carries an explicit route record: the living
document exists only on the control/integration branch, the product branch
cannot produce it (`git ls-files | grep -c docs/research` = 0, re-verified),
and the solver-fix section with the committed figures is to be published on the
control branch after this review accepts. I verified the precedent claim: the
living document on `agent-dev/bilateral-episode-v0.1` carries sections 20
(V1c), 21 (V2) and 24 (conservation audit) whose record heads name the product
branch and candidate commit for each stage — i.e. the controller does publish
and bind these sections. However, `START_CONSERVATION_FIX.md` §8 **mandates**
the update ("do not consider the task complete without the technical-document
update") and says nothing that authorizes deferral, and contract §19 makes
"living-document publication" part of the stop boundary. The record therefore
removes the attempt-1 defect of a *silently skipped* §17, but the alternate
route still needs the controller's confirmation and the actual publication;
that is a controller action, not something the executor can produce on this
branch, so it is carried forward as a process item rather than charged to the
revision.

### (6) Minor items

| Item | Status | Evidence |
|---|---|---|
| A2 isolation backed by committed evidence | **PASS** | `a2_isolation.json` (9 combos) + `a2_isolation_check.py` + `logs/a2_isolation.log`; values match the comparison table (T1C0/T2C0/T0+C1/T1+C1/T2+C1 4.4629e-6; T4C0 3.1032e-6; T0C0/T3C0/T3C1 0.0) and agree with the production-gate logs (`f2_levelA_T1C1.log` FAIL 4.46e-06; T0/T3C1s PASS 0.00e+00) |
| Figure T4 bar corrected | PASS | `cf_make_figs.py` `a2v[4]` 4.463e-6 → 3.103e-6, matching the json; SVG regenerated |
| Final-batch exit codes committed | PASS | `logs/final_batch_exit_codes.log`, 47 lines = 24 exit records + 23 start records, matching `run_final_batch.sh`; exactly one non-zero (`f3_collect exit=1`, explained in the report and PROVENANCE) |
| F3 L0/h baseline corrected | PASS | `EXECUTION_REPORT.md:143` = 3.05/4.32 vs baseline 3.0220/4.2489; frozen `results/levelc_v1c/summary.json` = 3.021996/4.248945; fix run `levelc_v1c_fix/summary.json` = 3.0530/4.3222 |
| Storage claim corrected | PARTIAL | Corrected in `EXECUTION_REPORT.md:103-113` (11 unconditional f64 probe fields, ~3 MB C3 / ~7 MB V2, writes compiled out when `dbg off`); **`CANDIDATE_COMPARISON.md:168` still says "no new per-node fields"** |
| Stale "selected" label on T1+C1 in the F1 table | **NOT FIXED** | Only the 20k row gained "(rejected by A2)" (`:73`); the 60k row still reads "**selected**: total 541x better" (`:76`), and the table still omits the selected candidate's F1 rows (`f1_T3C1s_60k` exists: +1.19e-11 / −6.43e-10). The file's own Selection section contradicts it. The revision request's claim that this label was replaced is not accurate for this row |

Additional non-blocking observations from the new artifact: the isolation table
labels T0+C1 / T1+C1 "(unscoped)" while the committed generator only exposes
the scoped `C1` switch (so the json rows are scoped runs — values are identical
to 4 digits, but the labels do not match the artifact); the isolation grid
(N = 24, 200 steps) differs from the production A2 gate (N = 32,
`tests/run_level_a.py:20`) and this is not stated in the table; the report's
"documented in `CANDIDATE_COMPARISON.md`" for the aborted first T1+C1 batch is
actually documented in `PROVENANCE.md:68-71`. The "299/300 checkpoints
negative" phrasing is exact for increments and off by one for point values
(298/300) — inherited from the attempt-1 review; the one-sided conclusion is
unaffected.

## 3. Scientific conclusions of attempt 1 — still standing

The raw evidence is byte-identical between the two attempts (verified over all
536 common files), so attempt-1's F0/F1/A2/F3/F4 recomputations apply
unchanged, and I re-checked the load-bearing numbers myself on the committed
files:

- **F0 (selected T3+C1s):** R_f −8.348e-12 (frac_pos 0.469), R_r +9.760e-11
  (0.513), R_b +1.955e-10 (0.489) — no one-sided local bias; T4 negative
  control R_f +1.494e-8 (0.940) with the same std as T3 (9.19e-9).
- **Momentum:** selected ~1e-12 mean / 1.3038e-8 max; T1's systematic
  −1.483e-8 x/y now disclosed.
- **F1:** total +1.1944e-11/step (~1300×), colour −6.4253e-10/step (10.5×,
  inside the ≤2e-9 target), bounded one-sided floor stated.
- **A2/F2/F3/F4:** A2 exact 0.0 for T0/T3+C1s and FAIL 4.46e-6 for the f32-path
  candidates; F2 before/after traceable to committed logs; a26 = 1.0389 /
  a40 = 1.0581 inside |a−1| ≤ 0.10 (baseline 1.0436/1.0699); V2 max eps_r
  7.487e-5, max eps_b 1.976e-4 (committed `report.json`, g6 now true), single
  trapped cluster, NOT_REACHED, V_bin change 0.2506 %, 60k steps.
- No gate weakened (A2 1e-6, A3 5e-6, V2 g6 5e-4 unchanged; solver and all
  `tests/` files untouched in this revision).

## 4. Answers to the contract's six final questions

1. **Original drift mechanism removed?** Yes, total channel — the 2⁻²⁶ stored
   inverse-matrix defect is removed (not compensated) by the f64 roundtrip.
2. **Total and colour closed?** Total yes; colour closed to a bounded,
   one-sided (negative), ordering-dependent floor — now stated with its sign
   and spread in the two report documents; the residual instances of the old
   framing (below) must still be corrected.
3. **Momentum preserved locally?** Yes — `sum_q w_q e_q = 0` exactly; residual
   at the f32 floor.
4. **V0/V1c/V2 physics preserved?** Yes at every unchanged gate; the
   Laplace/contact pairs are not fix-attributable and must not be read as such.
5. **Preferable to full f64?** Yes among the tested candidates (only T3+C1s
   passes F0/F1/A2); T3 *is* the f64 roundtrip; the 11 probe fields must be
   documented (now done in the report, not in the comparison) or later made
   lazy.
6. **V3 safe to reconsider?** No. V3 stays HOLD. This review authorizes neither
   V3 nor the fix's promotion; even PASS would return to external scientific
   review.

## 5. Decision rationale

The revision does what it claims in substance: the solver, tests and all raw
evidence are untouched; the corrected PDF is the right paper with the claimed
title and hit count; the momentum, colour-floor, F2-log, A2-isolation,
exit-code, L0/h and storage corrections are all verifiable against committed
data; the manifest fully re-verifies (198/198); and the scientific conclusions
of attempt 1 stand, re-checked independently. What prevents PASS is that the
same class of defect attempt 1 blocked on — statements contradicted by the
package's own committed evidence — survives in **required** products that this
revision did not sweep:

- `EXECUTION_REPORT.md:35` still names arXiv 2202.05643 as a downloaded key
  source (the deleted, misattributed identifier);
- `CANDIDATE_COMPARISON.md:76` still marks T1+C1 as "**selected**" and the F1
  table still omits the selected candidate's rows, contradicting the same
  file's Selection section — and the revision request states this item was
  fixed;
- `CANDIDATE_COMPARISON.md:178-179` and `summary.json` (`f2_v0`) still present
  the superseded F2 before-values (0.26 % / 30.8°) without the committed-log
  basis or the spread/not-attributable note;
- `CANDIDATE_COMPARISON.md:168` still asserts "no new per-node fields".

These are all one-to-three-line documentation/derived-artifact corrections; no
simulation, solver or physics work is required, and the fix itself does not
need to change.

Exact next action (documentation-only; then resubmit for fresh review, and
regenerate `MANIFEST.json` if any hashed evidence file changes):

1. `EXECUTION_REPORT.md:35` — replace `2202.05643` with `2112.08926` (or drop
   the identifier list).
2. `CANDIDATE_COMPARISON.md` F1 table — relabel the T1+C1 60k row "rejected by
   A2 (initial selection, kept for history)" and add the selected candidate's
   rows from `f1_T3C1s_60k` (total +1.19e-11, colour −6.43e-10) and
   `f1_T3C1s_20k_cpu`.
3. `CANDIDATE_COMPARISON.md:178-179` — use the committed-log pairs
   (0.42 % → 0.35 %; 34.0° → 27.3°) with the spread sentence and the
   not-fix-attributable marking, as already written in `EXECUTION_REPORT.md`.
4. `summary.json` `f2_v0` — regenerate the T0 before-values from the committed
   logs (or mark them explicitly as superseded first-batch values not present
   in the committed logs); update its manifest hash if the file changes.
5. `CANDIDATE_COMPARISON.md:168` — replace "no new per-node fields" with the
   disclosed probe-allocation wording.
6. A2 table — align the "(unscoped)" labels with the committed scoped
   generator rows (and state grid N = 24 / 200 steps vs the production N = 32
   gate logs).
7. Controller/owner (outside executor scope): confirm the §17 publication route
   and publish the solver-fix section with the committed figures on the control
   branch; contract §19 requires it before the stage closes.

Decision: CHANGES_REQUESTED — the revision is scientifically sound and unchanged (solver/tests byte-identical, 198/198 manifest hashes re-verified, raw evidence untouched, attempt-1's F0/F1/A2/F3/F4 conclusions independently re-confirmed), but corrections (1), (4) and (6) are only partially implemented: a wrong arXiv identifier, the superseded F2 before-values and the "no new per-node fields" claim, plus the stale "selected" label and the missing selected-candidate F1 rows, all survive in required products (`EXECUTION_REPORT.md`, `CANDIDATE_COMPARISON.md`, `summary.json`), one of them despite being explicitly claimed fixed; next action: apply the seven documentation-only items above (no solver, physics or simulation change needed; controller to confirm/publish §17), then resubmit for fresh review — no V3 authorization.
