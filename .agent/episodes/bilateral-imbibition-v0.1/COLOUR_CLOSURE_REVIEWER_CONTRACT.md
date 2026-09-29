# Colour Closure Follow-up — Fresh Reviewer Contract

Task ID: BI-COLOUR-CLOSURE-001

Read:
1. AGENTS.md
2. .agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md
3. .agent/episodes/bilateral-imbibition-v0.1/COLOUR_CLOSURE_CONTRACT.md
4. executor REVIEW_REQUEST.md
5. frozen candidate/evidence

Verify exact candidate, clean worktree, descendant of e256b4857a6e51510b75358994d7c5bcc742781e, T3 total path frozen, no V3/BC/physical-parameter changes.

## Required independent checks

### Residual localization
Recompute C1 and C3 local colour statistics by:
- cc>0 / cc==0
- pure-like / mixed
- wall-adjacent / non-wall

Verify equilibrium residual, recoloring increment and post-fix residual separately.
Check mixed/pure threshold sensitivity.

State exactly which node class causes the base one-sided residual.

### Periodic-C1 accumulation
Recompute red/blue/total colour drift slopes, R2 and sign fractions.
State whether the local bias accumulates, plateaus or is non-accumulating.

### Candidate mechanism
Verify the selected correction is representable in stored arithmetic, preserves momentum to the numerical floor, and does not introduce a material second-moment/pressure change.
If a rest-population correction is used, explicitly verify the tiny residual survives f32 storage.

### Long-horizon
Independently fit C3 colour and total drift over:
- full 60k
- 0-20k
- 20-40k
- 40-60k

Do not label a high-R2 one-sided trend as bounded.
If a systematic residual remains where the contract forbids it, return HUMAN_REQUIRED.

### Regressions
Verify unchanged:
- production Level A / A2
- V1c a26/a40
- V2 symmetry/topology/mass
- T3 total-channel conservation

No gate may be weakened.

### Evidence
Verify MANIFEST, provenance, commands and exit codes.
Prefer derived tables generated from committed machine-readable evidence.

Review the required update to docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md.

Decision exactly:
PASS / CHANGES_REQUESTED / HUMAN_REQUIRED

Even PASS returns to external scientific review.
Do not authorize V3.
