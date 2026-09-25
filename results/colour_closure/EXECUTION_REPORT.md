# EXECUTION REPORT — BI-COLOUR-CLOSURE-001

> Executor's report; not by itself proof.  Git state, logs and
> machine-readable artifacts under `results/colour_closure/` (SHA256
> in `MANIFEST.json`) may be captured independently.

## Task

- **Task ID:** `BI-COLOUR-CLOSURE-001`
- **Status:** `COMPLETED` (awaiting fresh review; V3 remains HOLD)

## Summary

The external solver-fix review accepted the T3 total-channel fix but
returned CHANGES_REQUESTED on the colour channel: (B1) the C3 60k
colour series was a persistent one-sided drift, not a bounded floor;
(B2) the periodic-C1 geometry kept a materially one-sided local
residual.  This task reproduced both blockers from the committed
evidence (13/13 checks), localized the residual by node class BEFORE
any code change, ran the periodic-C1 accumulation test, and compared
diagnosis-informed colour-only alternatives against the accepted
scoped-C1 baseline.

Diagnosis: two mechanisms of OPPOSITE sign partially cancel —
(a) the uncorrected equilibrium-construction leak at non-frozen
cc==0 nodes (positive; the B2 class is PURE nodes adjacent to the
diffuse interface, chi ~ 1e-12, NOT mixed), and (b) f32
scatter-accumulate rounding at non-frozen cc>0 nodes (negative; the
C3 60k drift is dominated by it — budget identity closes to 7.7e-12).
Consequently every single-intervention candidate FAILS a frozen gate
in a predicted direction, and only the combined candidate passes:

**Selected: T3 (frozen) + C1X (weighted closure, natural guard
`cc>0 or dr!=0`) + A2 (f64 colour pipeline end to end)** —
every node class closes to f64 epsilon (~1e-16); C3 60k colour
+8.1e-12/step (R2 0.58; 120k R2 0.41 — trendless; 79x vs base);
periodic C1 −6.4e-11/step at 60k (13.8x), decaying to R2 0.28 noise
by 240k while the BASE at 240k is still +1.05e-9 (R2 0.9986);
A2 stationarity exactly 0.0 for all 7 combos; the whole unchanged
V0/V1c/V2 gate chain passes; V2 mass stability improves 12.7x/384x
(eps_r/eps_b).  Production default flipped to C1X/A2 with env
override; the reviewer-suggested rest-population candidate (C1R) was
tested and rejected on f32-storage absorption evidence.

## Executor Claims — Changes

- `lbm_solver_cg3d.py` (SOLVER; total channel T3 path byte-frozen):
  - dbg-only probes (post-recolor stage sums, per-node `cc`,
    post-correction populations; written only when `dbg_local`);
  - `colour_fix` choices extended: `C1R` (rest-population closure),
    `C1X` (weighted closure with natural guard);
  - `acc_fix` switch: `A0` (original f32), `A1` (f64 accumulate),
    `A2` (f64 colour pipeline end to end);
  - production default: `T3 + C1X + A2` (env-overridable; `C1`/`A0`
    reproduce the interim accepted scoped closure).
  - BC: none.  Physical parameters: none.  Gates: none.
- `tests/colour_closure.py` (new task-local VAL/DIAG driver:
  reproduce / diagnose / accum / budget subcommands, production
  kernels in production step order);
- `tests/conservation_fix.py`: `make_solver` gains an optional
  `acc` passthrough (default `'A0'` preserves the historical replay
  semantics of the prior driver);
- `results/colour_closure/**`: full evidence package (see Artifacts).

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| A. Reproduce blockers from committed evidence | PASS | 13/13 checks, `A_reproduce/reproduce_report.json` |
| B. Diagnose by node class before code changes | PASS | `dx_*` class_stats + x_profiles + npz snapshots; biased class = non-frozen cc==0 (pure) nodes |
| C. Periodic-C1 accumulation test | PASS | base accumulates +8.85e-10/step (20k, R2 0.93); extended horizons 60k/240k for the candidate |
| D. Compare >=1 diagnosis-informed alternative | PASS | 6 arms + rest-population C1R, all with attribution |
| E. Hard gates | PASS | see checklist in CANDIDATE_COMPARISON.md |
| F. Regression chain (solver changed) | PASS | F2/F3/F4 all unchanged-threshold gates |
| Stop conditions | HELD | fresh review next; V3 HOLD; no gate weakened |

## Validation

All runs GPU (RTX 5080), taichi 1.7.4, lbm env; production kernels.
Batch drivers + per-run stdout: `run_*.sh` + `logs/` (exit codes in
the batch stdout captured by the executor session log).

### Contract A — reproduce

- **Command:** `python tests/colour_closure.py reproduce`
- **Status/exit:** PASS / 0
- 13/13 checks vs the external-review numbers (C1 R_r +3.8836e-9
  frac_pos 0.7578; C3 ~1e-10 unbiased; 60k slope −6.4253e-10 R2
  0.9827; segments −9.562/−5.771/−5.221e-10; total +1.1944e-11).

### Contract B — local partition (T3+C1/A0, pre 1500 / probe 40)

- **Commands:** `diagnose --geom C1|C3 --tag dx_*` → PASS / 0
- C1: `cc==0` (82%): R_r +4.66e-9 frac_pos 0.785 == Req_r (leak
  uncorrected); `cc>0`: −7.9e-12 unbiased.  x-profile: far bulk
  bit-frozen (~1e-19); biased band = non-frozen PURE cc==0 nodes
  (x~34-40, Req_r = R_r ~ +1e-8).
- C3: `cc>0` unbiased ±2e-10; `cc==0` wall class +5.1e-9(r)/+1.2e-8(b).

### Contract C — periodic-C1 accumulation (base)

- `accum --geom C1 --steps 20000`: Mc +8.845e-10/step (R2 0.927,
  frac_pos 0.778; second half +8.08e-10 R2 0.965) — ACCUMULATES,
  one-sided; the selected candidate must improve >=10x.

### Budget identity (C3, t=20k, 200 probed steps)

- dMr = −1.2825e-5/step = sumR (+6.99e-6) + sumdacc (−1.982e-5);
  residual 7.7e-12 (f64 noise) — mechanism attribution exact.
- Per-class: `cc>0` sum_dacc_r −7.18e-10/node (frac_pos 0.494);
  `cc==0` sum_R_r +4.64e-9/node.

### Candidate comparison (contract D/E)

See CANDIDATE_COMPARISON.md (all tables script-generated by
`make_report_tables.py candidates` from the committed CSV/JSON).
Headline (Mc slopes per step):

| arm | periodic C1 20k | C3 60k | verdict |
|---|---:|---:|---|
| C1/A0 (base) | +8.85e-10 | −6.55e-10 (rerun; committed −6.43e-10) | blockers B1/B2 |
| C1X/A0 | −3.54e-9 | −1.70e-9 | FAIL (exposes accumulate term) |
| C1/A1 | +2.45e-9 | +3.18e-10 | FAIL (>2e-9 on C1) |
| C1X/A1 | −9.22e-10 | +1.27e-10 | FAIL (f32 closure residue persists) |
| C1R/A0 | F0: absorbed by f32 storage | — | FAIL (storage survival) |
| C1/A2 | +9.46e-10 | — | FAIL (scope still needed) |
| **C1X/A2** | **−1.08e-10 (20k) / −6.40e-11 (60k) / +1.81e-11 R2=0.28 (240k)** | **+8.09e-12 R2=0.58 (60k) / +2.69e-12 R2=0.41 (120k)** | **SELECTED** |

### F2 — V0 suite (unchanged gates; T0 before / candidate after)

| mode | Level A | sigma | sigma rel | theta | Poiseuille eff | Compute_C | postproc |
|---|---|---:|---:|---:|---:|---|---|
| T0 | PASS | 0.0609 | 0.31% | 32.1 | 0.9933 | PASS | PASS |
| CAND | PASS | 0.0610 | 0.42% | 31.2 | 1.0010 | PASS | PASS |

Laplace/contact deltas are inside the documented run-to-run spread
(0.26–0.42% / 30.8–34.0°); NOT fix-attributable (same conclusion as
the solver-fix package).  A2 stationarity: `a2_candidates.json` —
max|v| EXACTLY 0.0 and psi_dev exactly 0.0 for all 7 combos
(incl. T3+C1X/A2 and the T3+C1/A0 reference).

### F3 — V1c (thresholds unchanged)

- static C = 0.7904 / 0.7516 / 0.8068 / 0.7715 (h26/40/60/80;
  V1c baseline 0.7902/0.7511/0.8067/0.7795 — plateau preserved);
- differential **a26 = 1.0618, a40 = 1.0741** (|a−1| ≤ 0.10 PASS);
- dynamic gates all_hard = True ×4 (g1–g8);
- non-gated diagnostic L0/h = 2.644 / 4.142 (V1c baseline 3.022 /
  4.249; solver-fix 3.053 / 4.322) — disclosed: the h26 effective
  front length shifts −12%; the gated hydraulic ratios are unaffected.

### F4 — V2 primary (60k, unchanged gates)

- gates: g1/g2/g3/g5/g6/g7/g8/g9 True; g4/g10 null by design (as in
  the accepted baseline); all_hard=False only due to the nulls;
- max_eps_r = 5.87e-6, max_eps_b = 5.16e-7 (accepted fix values
  7.49e-5 / 1.98e-4 → 12.7x / 384x better; gate ≤5e-4);
- mirror error max_e_x = 7.40e-4 lu (accepted 4.96e-4; gate PASS);
- single trapped gas cluster (1/1), no fragmentation, interaction
  NOT_REACHED, bulk ρ ∈ [0.9351, 1.0074] (unchanged).

### F10 — performance (same grid/horizon, JIT excluded)

| run | steps/s | MLUPS |
|---|---:|---:|
| C3 C1/A0 | 2833 | 81.6 |
| C3 C1X/A2 | 2853 | 82.2 |
| C1 C1/A0 | 2838 | 104.6 |
| C1 C1X/A2 | 2809 | 103.5 |

Net-zero cost within noise (−1.0% to +0.7%).

## Git / Source State

- base: `e256b4857a6e51510b75358994d7c5bcc742781e`
- head: see REVIEW_REQUEST.md (final candidate commit)
- branch: `agent-task/BI-COLOUR-CLOSURE-001`
- dirty files remaining: none at the candidate commit
- default-flip verification: constructor defaults read
  T3/C1X/A2 with env unset; f64 fields confirmed; short default-path
  run reproduces the candidate class behaviour (residual run-to-run
  differences are the documented GPU f32-atomic-ordering band of the
  total channel, inherited through v).

## Artifacts

| Artifact | Path | Purpose |
|---|---|---|
| reproduce report | `A_reproduce/reproduce_report.json` | contract A, 13/13 |
| diagnosis | `dx_C1_T3C1s/`, `dx_C3_T3C1s/` (+ candidate/arms variants) | class stats, x-profiles, one-step npz snapshots |
| accumulation series | `ac_*/mass_series.csv` + `accum_report.json` | contracts C/D/E |
| budget | `bg_*/budget_steps.csv`, `budget_class.csv` | identity + attribution |
| A2 isolation | `a2_candidates.json` | stationarity gate |
| regressions | `levelc_v1c_fix/`, `levelc_v2_fix/`, `logs/f2_*` | F2/F3/F4 |
| tables | `make_report_tables.py`, `make_regression_tables.py` | script-generated docs |
| figures | `figures/fig_cc_*.svg` (+ `figures/cc_make_figs.py`) | diagnosis + comparison |
| manifest | `MANIFEST.json` (`make_manifest.py`), `summary.json` | integrity + headline |

## Deviations

1. One solver edit was made while a candidate batch was still
   running, invalidating 8 arms (exit 1) — all re-run cleanly;
   the completed arms were produced by arithmetic-identical code
   paths (verified: same-code double-run difference is the GPU
   ordering band, not a code change).  Full record in PROVENANCE.md.
2. First C3 host gather used stream-OR-bounce instead of
   stream-PLUS-bounce for wall receivers; caught by a standalone
   Taichi scatter replay before conclusions were drawn; C1
   (no solids) unaffected; C3 re-run.
3. `f3_collect` initially failed (missing static_h26/h80 inputs to
   the V1c collect step) — the two static runs were added and
   collect re-run (exit 0).

## Assumption / Modeling Impact

No physics, BC, IC, threshold or interpretation change.  The colour
bookkeeping precision (f64 locals + accumulate + exact closure)
alters psi/rho_r at the f32-ulp scale only; the f/F moment path
(T3) is byte-identical.  The V0/V1c/V2 gate chain confirms
physics-neutrality at the accepted thresholds.

## Existing Evidence Potentially Affected

- Any future colour-mass sentinel values (e.g. `color_masses()` in
  production drivers) will show the improved (essentially exact)
  bookkeeping; earlier reported colour drifts (−6.4e-10/step band)
  correspond to the interim C1/A0 default and remain reproducible
  via `LBM_COLOUR_FIX=C1 LBM_ACC_FIX=A0`.
- 2D sibling (D2Q9) same-family defect remains out of scope (frozen
  line, per the solver-fix task).

## Unresolved Issues / Human Decisions

- The periodic-C1 candidate residual at 60k (−6.4e-11/step,
  R2 0.95) is a DECAYING transient (quarter slopes at 240k:
  +1.9e-10 → −5.0e-12 → +1.2e-11 → −4.7e-13; full-240k R2 0.28)
  while the base at 240k is still linear (R2 0.9986).  We do NOT
  label any residual a "bounded floor"; the horizon/scaling evidence
  (60k/120k/240k + mechanism attribution) is provided for the owner
  to accept the wording, per contract E.
- Non-gated V1c diagnostic L0/h(h26) shifts 3.02 → 2.64; gated
  hydraulic ratios unaffected (see F3).

## Suggested Next Action

Fresh headless review per
`.agent/episodes/bilateral-imbibition-v0.1/COLOUR_CLOSURE_REVIEWER_CONTRACT.md`;
even PASS returns to external scientific review; V3 stays HOLD.
