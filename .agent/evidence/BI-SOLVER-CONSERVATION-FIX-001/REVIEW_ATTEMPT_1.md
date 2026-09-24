stage: conservation-fix
attempt: 1
candidate: 2d45b9e5468dd28e953115824bfc836f43317247
execution_report: results/conservation_fix/EXECUTION_REPORT.md

# REVIEW — BI-SOLVER-CONSERVATION-FIX-001 (attempt 1)

## Review mode and coverage

`FRESH_SESSION`, independent reviewer. Executor transcript not read. Nothing
was modified except this file and `REVIEW_SESSION.json`. No simulation was
re-run and no GPU work was started; all recomputation is host-side on
committed evidence (F0/F1/A2 samples plus a CPU-only import of the base and
candidate solver tables to recompute the moment-matrix arithmetic).

Inspected: the review request, both contracts, the two authorizing audit
reviews, the literature note; worktree
`cg3d-episode-worktrees/BI-SOLVER-CONSERVATION-FIX-001` (HEAD, cleanliness,
full diff vs base, commit chain, driver/gate diffs); the full evidence tree
`results/conservation_fix/**` (search report, candidate comparison,
execution report, provenance, manifest, summary, all `f0_*`/`f1_*` CSVs and
reports, `levelc_v1c_fix/`, `levelc_v2_fix/v2_primary/`, `logs/`, figures +
generator); frozen baselines `results/levelc_v1c/`,
`results/levelc_v2/v2_primary/` and `results/conservation_audit/` from the
base commit; candidate solver `lbm_solver_cg3d.py` (collision path).

## 1. Binding and scope — verified

| Check | Result | Evidence |
|---|---|---|
| Candidate / branch / clean worktree | PASS | `git rev-parse HEAD` = 2d45b9e…; branch `agent-task/BI-SOLVER-CONSERVATION-FIX-001`; `git status --porcelain` empty |
| Descends from audit candidate | PASS | `1f5ee76` is an ancestor; chain 1f5ee76 → 503f474 → 9bd922d → 46be3f2 → e3d5a93 → 2d45b9e |
| Solver diff limited to fix + instrumentation | PASS | `lbm_solver_cg3d.py` 184+/8−: docstring, `inv_M_f64`, `project_inv_m_colsums()`, constructor switches + probe fields, `collision()` static branches (T2/T3/T4), scoped C1 block, dbg capture. No other physics touched |
| Drivers gained only an env hook | PASS | `tests/levelc_v1c.py` and `tests/levelc_v2_bilateral.py`: exactly one line each, `OUTROOT = os.environ.get('LBM_OUTROOT', <unchanged default>)` |
| No gate weakened | PASS | all six V0 test files untouched; A2 threshold `max\|v\| < 1e-6` (`tests/run_level_a.py:65-66`) and A3 `5e-6` unchanged; V1c gate set identical to frozen `gates.csv`, `a26_gate`/`a40_gate` present and True |
| No V3 / porous-media work | PASS | no V3 artifacts or runs; only a V3-hold statement (`EXECUTION_REPORT.md:166-170`) |
| Frozen baseline evidence intact | PASS | `results/levelc_v1c/`, `results/levelc_v2/` byte-identical to base; `results/conservation_audit/` gained only 7 **new** files in `diag_C3_gpu/` (no frozen file modified) |
| Code frozen for acceptance runs | PASS | `git diff e3d5a93 2d45b9e -- lbm_solver_cg3d.py tests/ ` is empty; final batch (02:29–03:55) ran after commit e3d5a93 (02:17) |

## 2. Search review (contract §3)

Both passes were performed before code changes and are documented with exact
queries, source links, "supports / does NOT support" statements, and an
explicit **no precedence claimed** verdict
(`LITERATURE_AND_IMPLEMENTATION_SEARCH.md` §§Verdict/Pass A/Pass B/C2).
C2 = not implemented, justified by absence of a mechanistically distinct
applicable candidate. `literature/dubois2024_mrt_projection_arxiv2412.17426.pdf`
is genuine (title page: Dubois & Philippi, "Multiresolution relaxation times
lattice Boltzmann schemes with projection"), and the report's claim that it
contains 0 occurrences of precision/FP32/single-precision/mass conservation
matches my own full-text scan (0 hits).

**Defect B1 (blocking, verified false statement).**
`literature/lehmann2022_f32_lb_arxiv2202.05643.pdf` is **not** Lehmann et al.
Its extracted first page is "Numerical-relativity validation of
effective-one-body waveforms in the intermediate-mass-ratio regime"
(Nagar et al.); 0 occurrences of "lattice Boltzmann" in the text. arXiv
2202.05643 is that gravitational-wave paper; the correct identifier for
Lehmann et al. 2022 (PRE 106, 015308) is **arXiv:2112.08926**. The search
report nevertheless lists "Lehmann et al. 2022 (PRE 106, 015308;
arXiv:2202.05643) … Downloaded: literature/lehmann2022_…pdf" and the access
log records "downloaded, %PDF-1.5 verified". This is a wrong-source
attribution inside a required deliverable (§16), and the accompanying
"supports" statement cannot come from the committed file (it comes from the
control memo's correct DOI citation, which is fine but is not the download).

## 3. Candidate comparison (contract §§4–7, 15)

F0 exists for T0/T1/T2/T3/T4+C0, T1+C1, T2+C1 and T3+C1s; F1 for 13 runs
including baseline, numerical reference and final candidate at 60k plus CPU
variants; A2 for the decisive triples. The T4 negative control is
independently persuasive: its R_f distribution has the **same std as T3
(9.19e-9) with the mean shifted by exactly the matrix defect**
(+1.494e-8 vs −3.6e-12, frac_pos 0.94) — i.e. f64 accumulation with the f32
matrix keeps the bias, as the audit predicted.

I independently recomputed the matrix arithmetic by importing the base and
candidate tables in a CPU process:

- base stored f32 `inv_M`: `colsum[0]−1 = +1.4901161193847656e-08` (= 2⁻²⁶),
  `max|colsum[l>0]| = 1.49e-08` → root cause reproduced;
- candidate table unchanged by default; `project_inv_m_colsums()` (T1) gives
  `colsum[0]−1 = 0` exactly, `max|colsum[l>0]| = 6.2e-17`, 20 entries changed,
  max |Δ| 1.49e-8 → matches the documented T1 projection;
- `inv_M_f64` is the exact f64 inverse (max deviation 0 vs `numpy.linalg.inv`).

A2 reselection is evidenced by committed logs: T0 PASS (`max|v| = 0.0`),
T1+C1 **FAIL 4.46e-6**, T3+C1s PASS (exact 0.0)
(`logs/f2_levelA_{T0,T1C1,T3C1s}.log`). The C1 `cc > 0` scoping is supported
by the measured locality: the scoped correction's mean per-node magnitude is
95.5 % of the unscoped one (dr mean −6.088e-9 in `f0_T3C1s` vs −6.376e-9 in
`f0_T1C1`, different total-fix runs, so order-of-magnitude), and the selected
candidate's R_r/R_b frac_pos ≈ 0.5 shows no residual local bias.

**Defect B2 (blocking, claim contradicted by the package's own CSV).**
`CANDIDATE_COMPARISON.md:49-52` and `EXECUTION_REPORT.md:68` state the
collision momentum residual is "≤ 2.2e-8 per node (f32 floor; all candidates
equal)". The committed F0 CSVs say otherwise: max|mom| reaches 4.28e-8 (T1C1,
C3) and 2.79e-8 (T0/T2, C3), and T1's per-axis **means** are −1.5e-8 in x and
y versus ~1e-12 for T0/T2/T3/T4. I reproduced the mechanism: with the
projected table, `sum_q e_q Δf_q = (−1.49e-8, −1.49e-8, ~0)` per node, i.e.
T1 trades the zeroth-moment table defect for a systematic local momentum
error of the same magnitude. T1 is rejected anyway, but this undisclosed
side-effect and the wrong "f32 floor / all equal" attribution must be
corrected in the comparison. The selected candidate is unaffected (mean
~1e-12, max 1.30e-8 = representation floor).

**Minor.** The A2 isolation table has 8 rows but only 3 committed runs; the
rows for T1+C0, T2+C0, T0+C1(unscoped) and T2+C1(scoped) have no retained
evidence. The F1 table still labels T1+C1 "selected" and omits the final
T3+C1s rows (stale, contradicts the same file's Selection section).

## 4. Independent recomputation of F0/F1/A2/F3/F4

**F0 (selected T3+C1s, `f0_T3C1s/f0_local_identities.csv`).**
R_f −8.348e-12 (frac_pos 0.469), R_r +9.760e-11 (0.513), R_b +1.955e-10
(0.489) — no one-sided bias, at the representation floor. Baseline T0:
+1.489e-8 (0.660); T4: +1.494e-8 (0.940). Colour three-stage split checks
out: equilibrium-sum residual (+6.45e-9) dominates, recoloring contributes
≈ −1.1e-10 (from dr vs Req reconciliation), post-C1 ≈ 1e-10. Correction
momentum residual is exactly zero: `sum_q w_q e_q = 0` verified host-side
(f64). Contract §5 requirement ("remove persistent one-sided local closure
bias, not just global mass") is met.

**F1 (refit by me from the raw CSVs, own OLS code; all reported values
reproduce to 4 significant digits):**

| run | total /step | R² | colour /step | R² |
|---|---|---|---|---|
| T0+C0 60k (baseline) | +1.5525e-8 | 1.0000 | +6.7617e-9 | 0.996 |
| T3+C0 60k (reference) | +1.1684e-11 | 0.35 | +6.7710e-9 | 0.996 |
| **T3+C1s 60k (selected)** | **+1.1944e-11** | **0.62** | **−6.4253e-10** | **0.983** |
| T2+C0 20k (rejected) | −2.7598e-9 | 0.9998 | +8.3709e-9 | 0.994 |
| T3+C1s 20k CPU | −3.3027e-11 | 0.85 | −6.8529e-11 | 0.795 |

Improvement: total ~1300×, colour 10.52× (both within the §9 gates: ≥10× and
≤2e-9). The baseline reproduces the frozen audit (my fit of the frozen
`results/conservation_audit/C3_gpu` CSV gives 1.5556e-8 / 8.3088e-9 at 20k;
the executor's 4 000-step rerun at base gives 1.4873e-8 / 1.0975e-8, which is
exactly what the frozen CSV's own 4 000-step window yields, 1.4888e-8 /
1.1013e-8 — the diagnosis reproduction is faithful at the same horizon).
No abrupt jumps (max |Δdrift| 1.89e-7 vs 3.17e-6 baseline); total-channel
increments 52.7 % positive (no monotone bias).

**Defect B3 (blocking, claim contradicted by the committed series).**
The colour channel after the fix is **one-sided**: 299 of 300 checkpoints
negative, relative drift −4.05e-5 over 60k, against a baseline that was
+4.2e-4 and 100 % positive. `EXECUTION_REPORT.md:80` states "No abrupt jumps;
no monotone bias from the correction itself", which is true for the total
channel and false for the colour channel. The magnitude does meet the gate
(10.5×, ≤2e-9), and the executor's "arithmetic floor" reading is plausible —
my own check shows the residual varies 6.9e-11 … 1.6e-9 across C1 variants and
backends (ordering-dependent, like a floor) — but the mechanism is not
demonstrated, and the surviving sign-flipped monotone drift must be stated
as such for external review rather than denied.

**F2.** A2 verified above. All other suites' committed "after" logs match the
report (Poiseuille eff 1.0010; Laplace 0.35 %; contact 27.3°; Level A,
Compute_C, postprocessing ALL PASS).

**Defect B4 (blocking, F2 before/after not traceable).** The documented
"before" values Laplace 0.26 % and contact 30.8° do **not** appear in the
committed T0 logs, which now read 0.42 % and 34.0°; they are from the
superseded first-batch T0 runs whose logs the final batch overwrote. More
importantly, the T0 contact metric itself spans 30.8°–34.0° between runs of
identical code — a spread larger than the reported before/after difference
(30.8 → 27.3). The before/after pairs for Laplace and contact must therefore
be regenerated from (or replaced by) the committed logs, with the metric's
run-to-run spread stated; they cannot be read as fix-attributable changes.

**F3.** All 8 runs (static 26/40/60/80, dynamic 26/40 × s/2L) carry
`run_head = e3d5a93`, producer hashes matching the committed drivers
(`57155f48…`, `c08c383d…`) and matching artifact hashes. Static
C = 0.790155 / 0.751291 / 0.807004 / 0.783381 vs frozen 0.790193 / 0.751095 /
0.806739 / 0.779494 (plateau 0.782 ± 0.031). Collect: a26 = 1.038877,
a40 = 1.058149, both |a−1| ≤ 0.10 PASS (baseline 1.043640 / 1.069897); all
four dynamic cases `all_hard = true`. No band or geometry tuned. One doc
error: "baseline L0/h 3.00/3.94" contradicts the frozen table (3.0220 /
4.2489).

**F4.** `levelc_v2_fix/v2_primary/report.json`: max mirror error 4.959e-4 lu
(baseline 1.297e-3), max eps_r/eps_b 7.487e-5 / 1.976e-4 (baseline 4.208e-4 /
6.730e-4, i.e. inside the original g6 value 5e-4); baseline g6 was **false**,
now **true**. Single trapped cluster (max = final = 1); NOT_REACHED; bulk rho
[0.93502, 1.00737] vs baseline [0.93529, 1.00807]; V_bin change identical to
baseline (0.2506 %); same 326×42×6 geometry and 60k steps. `all_hard=false`
only because g4/g10 are null by design, exactly as in the accepted baseline —
no gate weakened.

**Performance (§10).** All F1 runs share the C3 grid (126×46×6, 28 800 fluid
nodes); JIT is separated (`jit_first_step_s` vs `steady_wall_s`); matched
horizon comparison available: T0 60k 2352 steps/s vs T3+C0 2423 vs T3+C1s
2479. So the fix costs nothing resolvable above the ±5 % run-to-run spread —
but "no new per-node fields" is inaccurate: 11 per-node f64 probe fields are
allocated unconditionally in the constructor (~3 MB on C3, ~7 MB on V2);
writes are statically disabled when `dbg_local` is off, so the timing claim
holds while the storage claim (and §10's "additional fields / f64 storage"
row) does not.

## 5. Required product outputs (contract §§16–17)

Present: search report, candidate comparison, execution report, provenance,
`MANIFEST.json` (194 entries — all SHA256 verified by me, plus the solver
hash d359fd03… which matches the committed file), machine-readable
`summary.json`, local-identity and drift CSVs, performance table, V0/V1c/V2
regression outputs, logs, figures with a generator that reads only committed
evidence (verified).

**Defect B5 (blocking, mandatory output missing).** §17's "mandatory living
technical document update" is absent: the branch contains **no**
`docs/research/**` at all (`git ls-files | grep -c docs/research` = 0; the
living document exists only on the integration branch), and nothing in the
package reports this gap or the intended publication route. Either the
solver-fix section (with the committed figures) is published through the
controller/integration branch, or the executor records explicitly why §17
cannot be produced from this branch and an owner/controller confirms the
alternate route. It cannot be silently skipped, since §19 names
"living-document publication" as part of this stage.

Remaining minor gaps: final-batch shell exit codes are not committed although
`PROVENANCE.md` claims "all logs + exit codes in logs/" (only the superseded
first batch has a master log); F0 records per-node **statistics** (mean/std/
frac_pos/max over all fluid nodes × 40 steps) rather than per-node before/
after values as §8 literally asks; the 2D canonical-solver finding
(`colsum[0]−1 = +7.45e-9`) has no committed artifact and I could not verify
it; the diagnosis re-run writes into `results/conservation_audit/diag_C3_gpu/`
(additive only, disclosed — acceptable but a task-local directory would be
cleaner).

## 6. Answers to the reviewer contract's six final questions

1. **Is the original deterministic mass drift mechanism removed?** Yes, for
   the total channel. The stored-matrix zeroth-moment defect
   (+1.4901161193847656e-08 = 2⁻²⁶, independently recomputed from both base
   and candidate tables) is removed rather than compensated: T3 uses the exact
   f64 inverse with a f64 accumulator. Locally R_f is unbiased (frac_pos 0.47),
   globally the total drift falls ~1300× to +1.19e-11/step with no trend.
2. **Are total and colour channels both closed?** Total: yes. Colour: closed
   to a measured, bounded floor, not bias-free — locally R_r/R_b are unbiased
   at the f32 floor and the equilibrium-sum leak that dominated pre-fix is
   removed — the summed scoped C1 correction (6.088e-9 per node × 28 800
   nodes = 1.75e-4/step) accounts for 90 % of the pre-fix absolute colour
   leak (6.7617e-9 × 28 800 = 1.95e-4/step), so the 10.5× factor is the
   leftover ~10 % — and globally the colour drift improves 10.5× to −6.43e-10/step,
   inside the ≤2e-9 target — but the residual is still monotone one-sided
   (negative). "Closed to a defensible arithmetic floor, sign stated" is the
   accurate claim; the report's "no monotone bias" phrasing is not.
3. **Does the selected fix preserve momentum locally?** Yes. The correction
   weights satisfy `sum_q w_q e_q = 0` exactly (verified), so the
   correction-specific momentum residual is zero; the selected candidate's
   full-collision momentum change is ~1e-12 mean / 1.30e-8 max per node, the
   f32 floor, negligible against rho·u.
4. **Does it preserve V0/V1c/V2 physics?** Yes at every unchanged gate: A2
   exactly 0.0 (the gate that eliminated T1/T2/unscoped-C1), Level A,
   Compute_C, Poiseuille, Laplace, postprocessing all PASS; V1c static C on
   the plateau and a26 = 1.0389 / a40 = 1.0581 inside |a−1| ≤ 0.10; V2 mirror
   error 2.6× better, single trapped cluster, NOT_REACHED, bulk guardrail and
   V_bin change unchanged. Concretely: surface tension 0.26–0.42 % → 0.35 %
   (all inside the historical spread), contact angle 27.3° (band 30 ± 6;
   note the T0 metric itself spans 30.8–34.0°), hydraulic slope and
   trapped-pocket topology unchanged. The one physics caveat is the
   sign-flipped colour bookkeeping residual in Q2.
5. **Is the production choice preferable to full-f64 on correctness/
   complexity/performance grounds?** Among the tested set, yes: T3+C1s is the
   only candidate passing F0, F1 and A2 simultaneously; T1 (cheaper, same
   drift) is eliminated by the unchanged A2 gate and additionally carries a
   systematic 1.5e-8 local momentum bias (B2); T2 fails the F1 gate; T4 is the
   negative control. Note the question is slightly mis-framed: T3 already
   *is* the f64 roundtrip (f64 matrix + f64 accumulator, f32 storage of
   results); a full-f64 state representation was never a candidate and is not
   needed — T3/T4 vs T0 show the remaining bias came only from the matrix,
   not from f32 population storage. Residual cost: ~0 % measurable steady
   throughput, one 19×19 f64 table, plus the 11 unconditional probe fields
   that should be documented (or made optional).
6. **Is V3 scientifically safe to reconsider after external review?** Not by
   this review, and not yet: V3 stays on HOLD. The conservation preconditions
   are substantively met for the total channel and within the contract's
   numeric targets for colour, but (a) B1–B5 must be corrected in the evidence
   package, and (b) external scientific review must explicitly accept the
   bounded one-sided colour drift (Q2). This review authorizes neither V3 nor
   the fix's promotion.

## 7. Decision rationale

The scientific core of this candidate survives independent scrutiny: root
cause reproduced from first principles, negative control behaving exactly as
predicted, F0 local identities unbiased for the selected candidate, F1 slopes
reproduced to four digits with a genuine >10³× total-channel improvement and a
>10× colour improvement inside the target, A2/F3/F4 verified against frozen
baselines with thresholds untouched, and manifest/hash/provenance chains
intact. What prevents PASS is that the package's **required outputs contain
statements its own evidence contradicts** (B1 wrong source file + wrong arXiv
ID asserted as downloaded/verified; B2 momentum claim vs CSV; B3 "no monotone
bias" vs a 99.7 % one-sided colour series; B4 F2 before-values absent from the
committed logs), and one **mandatory deliverable is entirely missing** (§17
living-document section). None of these requires new physics work: B1–B4 are
corrections of documentation against committed data (B3 may add a short
isolating measurement or an explicit statement for external review), and B5
needs an owner/controller decision because the living document does not exist
on this branch.

Exact next action: (1) replace or delete
`results/conservation_fix/literature/lehmann2022_f32_lb_arxiv2202.05643.pdf`
(the correct source is arXiv:2112.08926) and correct the Pass-A entry and
access-log row; (2) rewrite the F0 momentum paragraph
(`CANDIDATE_COMPARISON.md:49-52`, `EXECUTION_REPORT.md:68`) with the CSV
values and disclose T1's −1.5e-8 x/y momentum side-effect; (3) restate the F1
colour result as a bounded one-sided residual floor with its sign and the
cross-candidate/backend spread, or add the isolating measurement; (4)
regenerate the F2 before/after table from the committed logs (or re-run the
T0 suite once) and state the contact-angle spread; (5) resolve §17 with the
controller/owner — publish the solver-fix section with the committed figures
on the integration branch, or record why it cannot be produced here and get
owner confirmation; (6) fix the minor items (A2 isolation rows without
evidence, stale "selected" label in the F1 table, missing final-batch exit
codes, "no new per-node fields", F3 L0/h baseline numbers). Then resubmit for
fresh review; the fix itself does not need to change.

Decision: CHANGES_REQUESTED — the fix is scientifically sound and independently reproduced (F0 unbiased, F1 total ~1300x / colour 10.5x within target, A2/F3/F4 gates pass with unchanged thresholds), but B1–B5 are blocking evidence-package defects (a misattributed literature file asserted as verified, a momentum claim and a "no monotone bias" claim contradicted by the committed data, F2 before-values absent from the committed logs, and the mandatory §17 living-document section missing); next action: apply corrections (1)–(6) above — no solver or physics change needed, no V3 authorization — and resubmit for fresh review.
