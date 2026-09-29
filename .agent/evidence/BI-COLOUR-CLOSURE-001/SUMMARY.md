# SUMMARY — BI-COLOUR-CLOSURE-001

- **Task:** BI-COLOUR-CLOSURE-001 (narrow colour-channel closure;
  entry `.agent/episodes/bilateral-imbibition-v0.1/START_COLOUR_CLOSURE.md`)
- **Base:** `e256b4857a6e51510b75358994d7c5bcc742781e` ·
  **Candidate:** `6c30260` · **Branch:** `agent-task/BI-COLOUR-CLOSURE-001`
  (pushed; evidence `results/colour_closure/`, 253-file SHA256 MANIFEST)
- **Decision:** fresh reviewer **PASS** (attempt 1, no self-review,
  no GPU, manifest 253/253 verified).  Even PASS authorizes neither
  V3 nor promotion; the package goes to external scientific review.

## What was established

1. Both external-review blockers reproduce from committed evidence
   (13/13 checks).
2. Diagnosis BEFORE code changes: two opposite-sign mechanisms
   partially cancel — the uncorrected equilibrium-construction leak
   at non-frozen `cc==0` pure nodes near interfaces (positive; the
   B2 class) and f32 scatter-accumulate rounding (negative; the C3
   60k drift; budget identity closes to 7.7e-12).  Every
   single-intervention candidate fails a frozen gate in the
   predicted direction; the reviewer-suggested rest-population
   closure (C1R) is absorbed by f32 storage (rejected on evidence).
3. Selected candidate **T3 + C1X + A2** (weighted closure with the
   natural guard `cc>0 or dr!=0`; f64 colour pipeline end to end;
   the only remaining rounding is the single `rho_r` store):
   - local closure at f64 epsilon for EVERY node class;
   - C3 60k colour +8.09e-12/step (R2 0.583; 120k R2 0.415,
     alternating quarters) — trendless; total channel inside the
     accepted T3 floor;
   - periodic C1: 13.8x improvement at 60k, decaying segments; at
     240k R2 0.28 (noise) while the base at 240k is still linear
     (R2 0.9986);
   - A2 stationarity exactly 0.0 (all 7 combos);
   - unchanged-gate regressions all green (a26 1.0618 / a40 1.0741;
     V2 eps_r 5.9e-6 / eps_b 5.2e-7 — 12.7x / 384x better than the
     accepted fix; single trapped cluster; symmetry intact);
     performance net-zero within noise.
4. Residual honesty: the remaining colour residual is small,
   horizon-decaying and sign-symmetric late, sourced at the single
   f32 `rho_r` store.  It is calibrated, NOT proven bounded; the
   frozen no-sign-bias clause requires an explicit owner decision
   (acceptance or re-scope) at the external scientific review.
   V3 remains HOLD.

## Files

- `REVIEW_REQUEST.md`, `REVIEW.md`, `REVIEW_SESSION.json`,
  `SUMMARY.md`/`summary.json` (this directory)
- Product evidence:
  `agent-task/BI-COLOUR-CLOSURE-001:results/colour_closure/`
- Living document: `docs/research/bilateral_imbibition/
  ALGORITHM_IMPLEMENTATION_EVOLUTION.md` §26 + figures
  `figures/fig_cc_diagnosis.svg`, `figures/fig_cc_candidates.svg`
