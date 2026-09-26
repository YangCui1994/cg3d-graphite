# Solver Conservation Fix Contract

Task ID: BI-SOLVER-CONSERVATION-FIX-001

## 1. Objective

Repair the two collision-channel zeroth-moment closure defects identified by
`BI-CONSERVATION-AUDIT-001`, while preserving the validated V0/V1c/V2 physics.

This task is explicitly authorized by:

- `.agent/evidence/BI-CONSERVATION-AUDIT-001/CONSERVATION_EXTERNAL_REVIEW_PASS.md`
- `.agent/evidence/BI-CONSERVATION-AUDIT-001/INDEPENDENT_EXTERNAL_REVIEW_CONFIRMATION.md`

V3 remains on HOLD.

## 2. Product base and branch

Base:

`1f5ee76fa183b42dd0ffcb291f389c3f1974a147`

Branch:

`agent-task/BI-SOLVER-CONSERVATION-FIX-001`

The base contains the accepted conservation audit and the same production
solver as V2.

## 3. Mandatory literature / implementation search BEFORE coding

Before changing solver code, produce:

`results/conservation_fix/LITERATURE_AND_IMPLEMENTATION_SEARCH.md`

### Pass A — academic search

Search for:

- MRT LBM conserved moments / collision invariants;
- floating-point / single-precision / round-off effects in LBM;
- color-gradient / Latva-Kokko recoloring mass conservation;
- component-mass conservation in recoloring;
- zeroth-moment projection or conservative correction of LBM populations.

At minimum inspect the sources listed in:

`docs/research/bilateral_imbibition/CONSERVATION_FIX_LITERATURE_NOTE.md`

### Pass B — targeted implementation search

If Pass A does not identify a direct analogue of the exact repository defect,
perform a second search including:

- open-source LBM implementations;
- GitHub issues/discussions;
- MRT inverse-transform implementation details;
- precision / matrix storage choices;
- local mass-projection techniques.

Record:

- exact query/search terms;
- relevant source links;
- what each source supports;
- what it does NOT support;
- whether any source directly reproduces the
  `float32 inv_M column-sum -> linear drift` mechanism.

Do not claim literature precedence if none is found.

The search may refine the candidate list, but any new candidate must be
mechanistically justified and included in the comparison matrix below.

## 4. Frozen diagnosis to reproduce before modifying code

Reproduce on the task branch:

```text
sum_s inv_M[s,0] - 1 ~= +1.490116119e-8
current C3 total drift ~= 1.56e-8 / step
current C3 colour drift ~= 8.3e-9 / step
```

Also reproduce that:

- C0/C2 do not show accumulating long-horizon drift after their short transient;
- CPU/GPU C3 share the same sign and comparable total-channel rate;
- first accumulating imbalance appears in collision.

If these cannot be reproduced, stop with HUMAN_REQUIRED.

## 5. Candidate design matrix

Do not jump directly to one fix.

Implement candidates behind explicit task-local/solver switches or separate
candidate commits so that all can be compared from the same base.

### T0 — current implementation

Required baseline.

### T1 — stored-matrix conservation projection

Modify the stored inverse transform or its construction so the zeroth-moment
column constraints are satisfied as closely as representable:

```text
1^T inv_M = [1, 0, ..., 0]
```

Document:

- projection formula;
- which matrix entries change;
- maximum element perturbation;
- effect on all 19 column sums;
- whether runtime inverse-transform accumulation order can reintroduce bias.

Do not assume the host-side projected sum guarantees device-side local closure;
measure it.

### T2 — local post-reconstruction total-mass projection

After reconstructing `f_q`, compute:

```text
delta_f = m0_pre - sum_q f_q
```

and apply a correction that preserves momentum exactly.

A rest-population correction is allowed as one candidate because e0=0, but its
effect on pressure/isotropic stress must be measured, not assumed harmless.

Report local changes to:

- density;
- momentum;
- relevant second moments/stress.

### T3 — full-f64 moment roundtrip reference

Use f64 matrix + f64 accumulator for the moment inverse transform as a
reference implementation.

This is primarily a numerical reference unless its performance and physics
results justify production use.

### T4 — negative control

Test:

```text
f64 accumulator + unchanged f32 inverse matrix
```

The audit predicts this is insufficient.

It must be measured explicitly and should fail the root matrix-bias test.

## 6. Colour-channel candidates

### C0 — current implementation

Required baseline.

### C1 — per-colour local zeroth-moment projection

After equilibrium + recoloring and before colour streaming, enforce separately:

```text
sum_q g_r,q = rho_r_pre
sum_q g_b,q = rho_b_pre
```

The correction must preserve the combined momentum to the expected arithmetic
floor.

A rest-population correction may be tested.

Measure separately:

- equilibrium-sum residual before recoloring;
- recoloring contribution to the residual;
- final per-colour residual after correction.

### C2 — search-derived candidate

If the mandatory search finds a materially different conservative scheme that
is applicable to this **binary immiscible** model, implement it as an additional
candidate.

Do not import a ternary/miscible algorithm without demonstrating equivalence of
its conservation logic to this binary model.

## 7. Candidate-combination strategy

Evaluate at least:

```text
T0+C0  baseline
T1+C0
T2+C0
T3+C0  reference
T4+C0  negative control
best-total + C1
```

If C2 exists, evaluate it against the best total-channel candidate as well.

Do not combine every candidate blindly if an earlier local invariant test
proves a candidate ineffective.

## 8. F0 — local conservation identities

This is the first hard gate.

For representative C0-C3 nodes/steps, record per-node before/after values.

Total:

```text
R_f = sum_q f_q(post-collision) - m0(pre-collision)
```

Colour:

```text
R_r = sum_q g_r,q(post) - rho_r(pre)
R_b = sum_q g_b,q(post) - rho_b(pre)
```

Also verify momentum:

```text
sum_q e_q delta_f_q ~= 0
sum_q e_q (delta_g_r_q + delta_g_b_q) ~= 0
```

Hard requirements for the selected production candidate:

- no persistent one-sided bias in R_f/R_r/R_b;
- local residuals at the measured f32 representation/accumulation floor;
- momentum correction residual negligible relative to pre-correction momentum.

If a fix improves global drift while leaving a systematic local closure bias,
it cannot be selected.

## 9. F1 — long-horizon closed-system conservation

Use the audited C3 minimal analogue.

Run at least:

- 20k steps for all viable candidates;
- 60k steps for baseline, numerical reference, and final selected candidate.

Current total-channel rate:

```text
~1.56e-8 / step
```

Selected production candidate must improve the persistent total and colour
drift rates by at least one order of magnitude.

Engineering target:

```text
|r_M,total| <= 2e-9 / step
|r_M,colour| <= 2e-9 / step
```

unless a lower/higher defensible arithmetic floor is measured and independently
reviewed.

Also require:

- no abrupt mass jumps;
- no monotone sign bias attributable to the correction itself;
- CPU/GPU comparison for the selected candidate.

## 10. Performance comparison

For every viable candidate report:

- first-compile/JIT time separately;
- steady steps/s or MLUPS;
- GPU memory impact if measurable;
- additional fields / f64 storage;
- kernel complexity / code-path complexity.

Performance is not allowed to override failed conservation/physics gates.

If multiple candidates pass all gates, prefer the candidate with:

1. smaller solver change;
2. simpler invariant;
3. lower GPU cost;
4. lower precision/storage overhead.

## 11. F2 — existing V0 regression suite

For the selected production candidate run unchanged:

- Level A;
- Compute_C;
- Poiseuille;
- Laplace;
- contact angle;
- postprocessing.

No acceptance threshold/reference may be weakened.

Record before/after metrics, not just PASS.

## 12. F3 — V1c scientific regressions

Re-run/reproduce on the fixed solver:

### Static slit

At minimum h=40 and one additional resolution from h=26/60/80.

Report:

```text
Pc_static
C_static = Pc h/(2 sigma)
theta_static
```

Compare against V1c plateau:

```text
C_static ~= 0.782 +/- 0.031
```

### Differential hydraulics

Re-run the minimum needed to recover:

```text
a26
a40
```

or an explicitly justified reduced chain if identical raw evidence can be
re-used only for analysis-independent portions.

Preferred requirement: rerun the dynamic cases because collision arithmetic has
changed.

Existing project gates remain:

```text
|a26 - 1| <= 0.10
|a40 - 1| <= 0.10
```

Do not tune pressure bands or geometry to pass.

## 13. F4 — V2 bilateral regression

Re-run the V2 primary bilateral case on the selected solver fix.

Require:

- no NaN/Inf;
- same h=40 / B=80 / G0=160 geometry;
- front mirror error gate unchanged;
- one trapped gas cluster throughout unless interaction legitimately changes
  topology;
- no unexplained fragmentation/disappearance;
- bulk-density guardrail unchanged;
- mass drift improved consistently with F1.

The qualitative V2 physics should remain the same:

- trapped from t=0;
- symmetric meniscus shaping / stall;
- interaction may remain NOT_REACHED.

A conservation fix that materially changes V2 qualitative topology requires
HUMAN_REQUIRED.

## 14. Solver source scope

Solver changes are authorized only for the minimum conservation fix and
instrumentation needed to compare candidates.

Do not refactor unrelated solver code.

Do not modify physical parameters to compensate for a candidate.

Keep every candidate change inspectable in git history.

## 15. Selection decision

The executor must produce a candidate comparison table covering:

- mechanism;
- local R_f/R_r/R_b;
- C3 total/colour drift rate;
- CPU/GPU;
- performance;
- V0;
- V1c;
- V2;
- implementation complexity.

The executor may recommend one candidate but must not hide failed alternatives.

If no candidate passes F0-F4, return HUMAN_REQUIRED.

## 16. Required product outputs

Use:

`results/conservation_fix/**`

Required:

- `LITERATURE_AND_IMPLEMENTATION_SEARCH.md`;
- `CANDIDATE_COMPARISON.md`;
- `EXECUTION_REPORT.md`;
- `PROVENANCE.md`;
- `MANIFEST.json`;
- machine-readable `summary.json`;
- local identity CSV/JSON;
- long-horizon drift CSV;
- performance table;
- V0/V1c/V2 regression outputs;
- logs + shell exit codes.

## 17. Mandatory living technical document update

Update:

`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`

Add a solver-fix section containing:

- literature/search findings and what was not found;
- exact root-cause formulas;
- candidate implementations with code excerpts;
- local invariant plots/tables;
- long-horizon drift comparison figure;
- performance comparison;
- V0/V1c/V2 before-after tables;
- final selected solver code;
- SOLVER classification explicitly marked;
- candidate/reviewer/evidence bindings.

All figures must derive from committed evidence.

## 18. Fresh reviewer decisions

Exactly one:

`PASS`
`CHANGES_REQUESTED`
`HUMAN_REQUIRED`

PASS requires:

- literature/search requirement satisfied;
- candidate alternatives honestly compared;
- selected fix passes F0-F4;
- no physics gates weakened;
- provenance auditable.

PASS returns to external scientific review.

It does **not** authorize V3 automatically.

## 19. Stop boundary

Stop after fresh review + living-document publication.

Do not start V3.
