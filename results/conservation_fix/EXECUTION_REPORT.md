# EXECUTION REPORT — BI-SOLVER-CONSERVATION-FIX-001

> Executor report, not sole proof. Git identity, logs, CSV/JSON evidence
> under `results/conservation_fix/` may be independently captured by the
> controller/reviewer.

## Task

- **Task ID:** BI-SOLVER-CONSERVATION-FIX-001
- **Status:** COMPLETED — selected fix **T3 + C1(scoped)** passes F0–F4
- **Contract:** `.agent/episodes/bilateral-imbibition-v0.1/SOLVER_CONSERVATION_FIX_CONTRACT.md`
- **Base:** `1f5ee76fa183b42dd0ffcb291f389c3f1974a147` (audit candidate)
- **Branch:** `agent-task/BI-SOLVER-CONSERVATION-FIX-001`
- **Authorization:** conservation external review PASS §6–7 + independent
  confirmation (solver-fix mandatory before V3)

## Frozen diagnosis reproduced (contract section 4)

On the task branch before any code change:
`sum_s inv_M[s,0] - 1 = +1.49011611938476562e-08` (= 2^-26);
C3 total drift 1.487e-8/step (R2 = 1.0000), colour 1.097e-8/step
(4000-step rerun; `logs/diag_C3_gpu.log`, `results/conservation_audit/`
holds the full C0/C2-clean + CPU/GPU-sign evidence on the same base).
First accumulating imbalance in collision: audit identities J1/J7.

## Search (contract section 3) — done BEFORE code changes

`LITERATURE_AND_IMPLEMENTATION_SEARCH.md`: two passes executed; **no
source directly documents the f32 inv_M column-sum defect** (consistent
with the control memo); new implementation finding: the **2D canonical
solver (D2Q9) carries the same defect class** (`colsum[0]-1 = +7.45e-9`
= 2^-27); Dubois/Philippi projection papers are name-similar but
mechanistically unrelated (0 precision/conservation content); C2
(search-derived candidate) = none, justified. Key sources downloaded to
`literature/` (arXiv 2412.17426, 2202.05643); paywalled DOIs recorded.

## Candidates and comparison (contract sections 5–7, 15)

Implemented behind constructor switches `total_fix` (T0–T4) /
`colour_fix` (C0–C1) with env overrides; full matrix in
`CANDIDATE_COMPARISON.md` (mechanisms, F0 per-node identities, F1
slopes, F10 performance, A2 stationarity table, rejection evidence).
Highlights:

- **T4 negative control confirmed** (F0: R_f +1.494e-8, frac_pos 0.94 —
  f64 accumulator + f32 matrix keeps the bias) → eliminated at F0.
- **T2 fails the F1 >=10x gate** (global -2.76e-9/step monotone despite
  unbiased local closure) — evidence that local identities alone do not
  suffice.
- **T1 matched T3 drift quality at zero cost** and was initially
  selected (`46be3f2`), but the **unchanged V0 A2 stationarity gate
  eliminates every f32-path table/correction change**: under T0 the
  uniform single-phase state is a bit-exact frozen fixed point
  (max|v| = 0.0); T1/T2/unscoped-C1 all break it and migrate to a common
  attractor max|v| = 4.46e-6 > 1e-6 (psi stays exactly uniform — a
  f32-floor effect, but the gate may not be weakened).
- **Only T3 (full-f64 moment roundtrip) preserves the frozen point
  exactly** (A2 max|v| = 0.0) while closing both channels. C1 was
  scoped to interface nodes (`cc > 0`), where the audit measured the
  colour leak (bulk J7 = 0 exactly) — bulk corrections were unnecessary
  and stationarity-breaking. Final selection commit `e3d5a93`.

## F0 — local identities (selected: T3 + scoped C1)

C3 geometry, device arithmetic, window after 1500 steps:
R_f mean −8.35e-12 (frac_pos 0.47), R_r +9.8e-11 (0.51), R_b +2.0e-10
(0.49) — no one-sided bias, at the representation floor.
Momentum (full-collision change `sum_q e_q (f_post - F_pre)`, from the
committed F0 CSVs): selected T3+C1s mean ~1e-12, max 1.30e-8 per node
(f32 floor, negligible vs rho*u); T0/T2+C0 max 2.79e-8; T1+C1 max
4.28e-8 — and **T1 additionally carries a systematic per-axis momentum
mean of −1.5e-8 in x/y** (attempt-1 review's independent reproduction:
with the projected table `sum_q e_q delta_f_q = (−1.49e-8, −1.49e-8, ~0)`
per node, i.e. T1 trades the zeroth-moment table defect for a local
momentum defect of the same magnitude — a further reason it cannot be
selected; the selected candidate is unaffected).
Colour three-stage split: equilibrium-sum residual dominates
(+6.45e-9 mean), recoloring ~2 orders smaller (−1.1e-10), post-C1
~1e-10. Correction-specific momentum residual exactly zero
(`sum_q w_q e_q = 0` verified host-side f64, attempt-1 review).
Full table: `f0_T3C1s/f0_local_identities.csv` (+ all other candidates).
Revision-2 note: F0 records per-node statistics (mean/std/frac_pos/max
over fluid nodes x 40 steps) rather than literal per-node before/after
rows; the probe fields hold the raw per-node values in-run.

## F1 — long-horizon conservation (selected)

C3, 60k steps, GPU: total **+1.19e-11/step** (R2 0.62 — no trend,
52.7% positive increments; baseline T0 +1.552e-8, R2 1.0000 → **~1300x**,
60k total drift 9.3e-4 → ~7e-7). Colour **−6.43e-10/step** (R2 0.98;
baseline +6.76e-9 → **10.5x**, meets both the >=10x gate and the <=2e-9
target) — restated per attempt-1 review B3: the colour residual is a
**bounded, one-sided (negative) floor**, 299/300 checkpoints negative,
−4.05e-5 over 60k (sign-flipped vs the baseline's +4.2e-4, 100%
positive); the scoped-C1 correction removes ~90% of the pre-fix absolute
colour leak (6.09e-9/node x 28800 = 1.75e-4/step vs baseline 1.95e-4/step,
reviewer-derived), and the leftover varies 6.9e-11–1.6e-9 across C1
variants and backends (ordering-dependent, floor-consistent). CPU 20k:
total −3.3e-11, colour −6.9e-11 (backend-consistent; CPU colour at
noise). No abrupt jumps (max |delta drift| 1.89e-7 vs baseline 3.17e-6).
Raw series: `f1_T3C1s_60k/long_horizon_mass.csv` etc.

## F10 — performance

C3 steady: T3+C1s **2479 steps/s (71.4 MLUPS)** vs T0 2465 (71.0) —
net zero cost after C1 scoping (unscoped T3+C1: 2347; T3+C0: 2355-2423).
JIT one-time ~300 s per new kernel variant (cache-warm 6.8 s); one
19x19 f64 table added (2.9 KB). Storage correction (attempt-1 review):
the constructor also allocates **11 per-node f64 probe fields
unconditionally** (~3 MB on C3, ~7 MB on V2); their writes are
statically compiled out when `dbg_local` is off, so the timing claims
stand, but they are a real allocation (candidates for a later
lazy-allocation cleanup, out of this task's scope).

## F2 — V0 regression suite (before/after, thresholds unchanged)

Before-values are from the **committed** final-batch T0 logs
(`logs/f2_*_T0.log`). The first (superseded) T0 batch measured Laplace
0.26% and contact 30.8° on identical code — i.e. the T0 metrics carry a
run-to-run spread (Laplace 0.26–0.42%, contact 30.8–34.0°) **larger
than the reported before/after differences**; the Laplace/contact pairs
below therefore must not be read as fix-attributable changes — both
sides sit inside the historical bands and the suite gates.

| suite | T0 (committed before) | T3+C1s (after) |
|---|---|---|
| Level A | ALL PASS | **ALL PASS** (A2 max\|v\| = 0.00 exact) |
| Compute_C bulk suppression | PASS | PASS |
| Poiseuille | eff = 0.9933 PASS | eff = 1.0010 PASS |
| Laplace sigma | 0.42% rel PASS | 0.35% rel PASS |
| Contact angle theta(-0.68) | 34.0° PASS | 27.3° PASS (band 30±6) |
| Postprocessing | ALL PASS | ALL PASS |

## F3 — V1c scientific regressions (selected fix)

- Static slit (full h26/40/60/80 set; collect requires all):
  C = 0.7902 / 0.7513 / 0.8070 / 0.7834 vs V1c baseline 0.7902 / 0.7511
  / 0.8067 / 0.7795 — plateau preserved (mean 0.7830 vs 0.782,
  spread unchanged).
- Differential hydraulics (4 dynamic runs rerun, 60k, production
  driver): **a26 = 1.0389, a40 = 1.0581** — gates |a−1| ≤ 0.10 both
  **PASS** (baseline 1.0436 / 1.0699; deltas 0.005 / 0.012).
  L0/h = 3.05 / 4.32 (baseline 3.0220 / 4.2489). Outputs:
  `levelc_v1c_fix/` (incl. `collect` report with per-case gates
  all_hard = true).
- No pressure bands or geometry tuned.

## F4 — V2 bilateral regression (selected fix)

Full 60k primary rerun on the fixed solver (`levelc_v2_fix/v2_primary/`):

- no NaN/Inf; same geometry; single trapped cluster throughout; no
  fragmentation; interaction NOT_REACHED (baseline outcome);
- front mirror error max **4.96e-4 lu** (baseline 1.297e-3 — 2.6x
  better); RMS 1.84e-4;
- bulk-density guardrail unchanged: [0.9350, 1.0074] (baseline pocket
  [0.935, 1.008]); umax post-equil 2.55e-2;
- mass drift: max eps_r 7.49e-5, max eps_b **1.98e-4** — 3.4x better
  than baseline (4.21e-4 / 6.73e-4) and **inside the original V2 g6
  gate value of 5e-4** that the audit proved was below the old
  implementation's floor;
- qualitative V2 physics unchanged (meniscus shaping / stall, trapped
  from t=0) — no topology change → no HUMAN_REQUIRED trigger.

## Solver change scope (contract section 14)

`lbm_solver_cg3d.py` only, all inside the fix task:

1. module tables: `inv_M_f64` (f64 inverse, T3) + `project_inv_m_colsums()`
   (T1, kept for reproducibility of the comparison) +
   `_inv_m_colsums_f64()` helper;
2. constructor: `total_fix`/`colour_fix` switches (env-overridable,
   production default T3/C1 since `e3d5a93`) + `dbg_local` F0 probe
   fields;
3. `collision()`: static branches for T2/T3/T4 total-channel paths, the
   scoped C1 projection block, and the dbg capture block;
4. docstring updated.

Plus task-local drivers/notes: `tests/conservation_fix.py`,
`results/conservation_fix/**`, and `LBM_OUTROOT` env hooks in
`tests/levelc_v1c.py` / `tests/levelc_v2_bilateral.py` (defaults
unchanged; lets prior-stage drivers rerun without touching frozen
evidence). No physical parameter changed; no gate weakened; unrelated
code untouched. Candidate history: `503f474` (implementation),
`9bd922d` (F0 + hooks), `46be3f2` (first selection), `e3d5a93`
(final selection).

## Validation commands

- batches: `results/conservation_fix/run_f1_batch.sh`,
  `run_f1_60k_batch.sh`, `run_final_batch.sh`, `run_collect_finish.sh`
  (exit codes in `logs/`); F0 driver invocations in
  `LITERATURE...`-adjacent logs;
- every run exit 0 except the deliberately superseded first
  `f3_collect` (missing static_h26 — resolved by completing the static
  set) and the aborted first T1+C1 regression batch (documented in
  `CANDIDATE_COMPARISON.md`).

## V3 boundary

Per the authorizing reviews: this fix **does not** authorize V3. V3
remains HOLD pending external scientific review of this task and the
V3 contract rewrite (old isolation-time gates obsolete).

## Living technical document (contract section 17 — route record)

`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`
lives on the **control/integration branch** (`agent-dev/bilateral-episode-v0.1`),
not on this product branch (it does not exist in this branch's tree).
Per the controller-issued `START_CONSERVATION_FIX.md` section 8 and the
episode's established flow (V1c §20, V2 §21/§24 precedents), the
mandatory solver-fix document section (with the committed figures from
`results/conservation_fix/figures/`) is published on the control branch
immediately after this fresh review accepts the candidate. This record
resolves the attempt-1 review's B5 explicitly rather than silently
skipping section 17.
