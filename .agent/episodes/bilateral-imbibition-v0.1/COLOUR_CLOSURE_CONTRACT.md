# Colour Closure Follow-up Contract

Task ID: BI-COLOUR-CLOSURE-001

## Scope

Close only the remaining colour-channel conservation issue from the external review of BI-SOLVER-CONSERVATION-FIX-001.

Frozen:
- T3 total-distribution fix is accepted.
- T1/T2/T4 rejection is accepted.
- V0, V1c and V2 regression conclusions are accepted.
- Do not reopen total-channel design.
- V3 remains HOLD.

Base product candidate:
e256b4857a6e51510b75358994d7c5bcc742781e

Product branch:
agent-task/BI-COLOUR-CLOSURE-001

Read first:
- .agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md
- docs/research/bilateral_imbibition/CONSERVATION_FIX_LITERATURE_NOTE.md
- docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md
- AGENTS.md

## A. Reproduce the blocker

From committed evidence reproduce:
- C3 local R_r/R_b approximately unbiased (~1e-10, frac_pos ~0.5).
- periodic C1 local R_r ~ +3.9e-9, R_b ~ +3.1e-9, frac_pos ~0.76.
- C3 60k colour slope ~ -6.43e-10/step, R2 ~0.983.
- segmented C3 slopes: ~-9.56e-10, -5.77e-10, -5.22e-10 per step for successive 20k windows.

If not reproducible: HUMAN_REQUIRED.

## B. Diagnose before changing code

Using current T3 + scoped-C1, partition local colour residuals for:
- periodic C1 two-phase;
- C3 two-phase slit.

Record R_r, R_b, equilibrium-sum residual, recoloring increment, cc, rho_r, rho_b, psi, and wall adjacency.

Report statistics separately for:
- cc>0 / cc==0;
- pure-like / mixed;
- wall-adjacent / non-wall.

Use chi=min(rho_r,rho_b)/(rho_r+rho_b), primary mixed threshold chi>1e-6; report sensitivity at 1e-7 and 1e-5.

Output:
results/colour_closure/LOCAL_RESIDUAL_DIAGNOSIS.md
plus machine-readable tables.

The diagnosis must identify which node class causes the one-sided periodic-C1 residual and whether it accumulates globally.

## C. Periodic-C1 accumulation test

Run current T3 + scoped-C1 for at least 20k steps with <=200-step sampling.
Extend to 60k if a plateau/regime change is plausible.

Track red mass, blue mass, total colour mass, slopes, R2 and increment-sign fractions.

## D. Colour-only candidates

Freeze T3 total path.

Baseline = current scoped-C1.

After diagnosis, compare at least one defect-scoped alternative. Candidate families may include:
- rest-population exact component closure;
- zero-net-momentum opposite-pair closure;
- diagnosis-driven extension to mixed cc==0 nodes.

Do not accept a candidate from algebra alone: verify the correction survives f32 storage and measure momentum / second-moment effects.

Do not correct uniform pure frozen states without evidence.

## E. Hard gates

Selected candidate must:
1. remove persistent one-sided local bias in the node class responsible for accumulating drift;
2. keep C3 local closure no worse than current accepted T3+C1s;
3. demonstrate any remaining biased class is non-accumulating;
4. keep correction-induced momentum at representation floor;
5. introduce no material second-moment/pressure perturbation.

C3 GPU 60k:
- |r_colour| <= 2e-9/step;
- >=10x improvement vs pre-fix T0 remains;
- |r_total| <= 2e-9/step;
- no persistent one-sided late trend.

If a systematic colour trend remains, return HUMAN_REQUIRED unless enough new horizon/scaling evidence exists for an owner gate re-scope. Do not call a linear trend a bounded floor.

If periodic-C1 accumulates in the base, selected candidate must improve it >=10x and to <=2e-9/step.

## F. Regression chain if solver code changes

Keep all thresholds unchanged.

- V0: full Level A, Laplace, contact angle, Poiseuille. A2 max|v| <1e-6; prefer exact 0.
- V1c: rerun dynamic cases needed for a26/a40; require |a26-1|<=0.10 and |a40-1|<=0.10.
- V2: rerun h40/B80/G160 primary; preserve symmetry/topology/density gates and max(eps_r,eps_b)<=5e-4.
- T3 total channel must remain <=2e-9/step.

## G. Outputs

Use results/colour_closure/** and provide:
- LOCAL_RESIDUAL_DIAGNOSIS.md
- partition tables
- CANDIDATE_COMPARISON.md
- EXECUTION_REPORT.md
- PROVENANCE.md
- MANIFEST.json
- summary.json
- C1/C3 long-horizon series
- regression outputs
- logs/exit codes

Update docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md after fresh review with formulas, code excerpts, figures, before/after metrics and bindings.

## H. Decision / stop

Fresh reviewer decision exactly:
PASS / CHANGES_REQUESTED / HUMAN_REQUIRED

Even PASS returns to external scientific review.
Do not start V3.
