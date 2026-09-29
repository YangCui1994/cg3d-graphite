# SUMMARY — BI-V2-BILATERAL-001

- **Candidate SHA:** `5e679d8d99d338f9ab28565c636f021a0f9211b2`
  (branch `agent-task/BI-V2-BILATERAL-001`, base `2b82f9a…`; remote
  verified; product worktree clean)
- **Reviewer decision:** **HUMAN_REQUIRED** (fresh session
  `sess_cb89ddea-76ab-46f2-a66a-e8c43fc03262`, exit 0; see `REVIEW.md`)

## Headline numbers (reviewer-corrected baselines)

| Quantity | Value |
|---|---|
| max front mirror error `e_x` | **0.0013 lu** (RMS 0.0010; gate ≤ max(2, 0.02d)) |
| full-field symmetry `max E_psi` | 8.3e-5 |
| one-sided displacement | −0.84 lu (static-meniscus shaping; rate comparison NOT_DISCRIMINATING at 0.09 lu window displacement) |
| colour-mass drift | max ε_r 4.2e-4; **max ε_b 6.73e-4 > 5e-4 gate (monotone; population channel +9.2e-4)** |
| rho min/max | bulk [0.935, 1.008]; all-fluid min 0.8851→0.8909 (interface structure, decaying) |
| gas volume | binary 38 400 (t=0) → 38 304 (t=1000 dip) → 38 400 (recovered); continuous 38 288→38 373 over samples |
| gas mean rho / p | 1.0000 (IC) → 1.0041 (**+0.42% from IC**), p 1/3→0.33470 |
| cluster count | 1 (initial = final; no fragmentation) |
| INTERACTION_ONSET | **NOT_REACHED** (G_bulk 160 at t=0 → 146 from t=1000) |
| buffer gas occupancy | 288/side, equal in 59/60 samples (one 12-node flicker at t=32 000) |

## Reviewer blocking findings (the human decision)

- **B1 (decision driver) — g6 colour-mass gate exceeded monotonically**
  and the drift is solver-level (systematic; two independent
  measurement channels disagree by 3.7e-4 about its size).  Resolution
  requires either (a) contract-owner re-scoping of the §10 gate
  (calibrated per-step rate ~1–1.5e-8/step and/or total-normalised
  bound; **the externally accepted V1c baseline also exceeds the gate
  as written**: 5.95e-4 / 6.82e-4 over 60k steps), or (b) an authorized
  solver-level conservation work item before V3.  Neither is within
  executor/reviewer authority.
- **B2 — the executor-declared bulk-node (|ψ|>0.9) scope of hard gate
  g3 needs contract-owner ratification**; the reviewer's independent
  audit supports the narrowing (dips are interface-localized, deeper
  dips exist in accepted V1c runs incl. dyn_h26_s 0.880460 / dyn_h40_s
  0.887740 / static_h40 0.888573 / static_h26 0.893018, pocket stays
  in range, excursion decays) but a hard gate's scope is the owner's
  to set.

All scientific gates (g1–g5, g7–g10, conditional rate diagnostic,
interaction handling) PASS — several by 3–4 orders of magnitude; the
V2 physics conclusions (symmetry, topology, trapping, NOT_REACHED,
stability) are independently confirmed by the reviewer.

## Unresolved issues (max five)

1. Contract-owner decision on g6: gate re-scope (option a) vs solver
   conservation work item (option b).
2. Ratification of the g3 bulk-node semantics (B2).
3. Solver non-conservation localization: Σ_fluid ρ vs Σ(ρ_r+ρ_b)
   differ by 28.7 at t=60k; interface bands −74.5 / pocket +161 /
   interior +71.8 budget points to wall bounce-back/Guo and recoloring
   bookkeeping (only if option b is chosen).
4. Driver `d(t)` identity defect (N1: mirrored-initial mixing; offset
   −80 in the committed column; gate unaffected here) + the N2–N9
   evidence corrections — to fix when the candidate is next touched.
5. V2 technical-document section delivered now with the
   reviewer-corrected numbers; final wording depends on the B1/B2
   outcomes.

V3 NOT started. No solver modification made. Product branch frozen at
the reviewed candidate.
