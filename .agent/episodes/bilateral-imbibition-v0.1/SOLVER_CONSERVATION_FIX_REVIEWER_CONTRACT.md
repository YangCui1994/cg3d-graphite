# Solver Conservation Fix — Fresh Reviewer Contract

Task ID: BI-SOLVER-CONSERVATION-FIX-001

## 1. Read order

1. `AGENTS.md`
2. `.agent/evidence/BI-CONSERVATION-AUDIT-001/CONSERVATION_EXTERNAL_REVIEW_PASS.md`
3. `.agent/evidence/BI-CONSERVATION-AUDIT-001/INDEPENDENT_EXTERNAL_REVIEW_CONFIRMATION.md`
4. `docs/research/bilateral_imbibition/CONSERVATION_FIX_LITERATURE_NOTE.md`
5. `.agent/episodes/bilateral-imbibition-v0.1/SOLVER_CONSERVATION_FIX_CONTRACT.md`
6. executor `REVIEW_REQUEST.md`
7. frozen candidate + evidence

Do not read executor transcript.

## 2. Binding / scope

Verify:

- exact candidate and clean worktree;
- descends from audit candidate
  `1f5ee76fa183b42dd0ffcb291f389c3f1974a147`;
- solver changes are limited to conservation fix/instrumentation;
- no V3 or porous-media work.

## 3. Search review

Check that the executor performed both search passes.

Distinguish:

- literature-supported model constraints;
- implementation-specific repository findings;
- speculative analogies.

Reject any statement claiming the exact f32 inv_M bug is literature-known
unless a source directly demonstrates that mechanism.

## 4. Candidate comparison review

Independently verify that at least T0/T1/T2/T3/T4 and the colour baseline/C1
logic were tested as required, subject to early elimination by failed F0.

Confirm T4 demonstrates that f64 accumulation with unchanged f32 inv_M is
insufficient.

## 5. F0 local invariants

Independently recompute representative:

```text
R_f
R_r
R_b
momentum correction residual
```

The final selected fix must remove persistent one-sided local closure bias.

Do not accept only a global-mass improvement.

## 6. F1 long-horizon drift

Recompute slopes from raw committed series.

Compare against baseline:

```text
~1.56e-8 / step total
~8e-9 / step colour
```

Require >=10x improvement and target <=2e-9/step unless an explicitly justified
floor is established.

Check CPU/GPU consistency.

## 7. Performance

Verify performance numbers use comparable grids/horizons and separate JIT from
steady-state cost.

Performance cannot compensate for failed conservation or physics.

## 8. F2/F3/F4 physics regressions

Independently inspect/recompute:

- V0 baseline metrics;
- V1c static calibration and a26/a40;
- V2 symmetry/topology and mass drift.

No threshold may be weakened.

Explicitly answer whether the fix changes:

- surface tension;
- contact angle;
- hydraulic slope;
- trapped-pocket topology.

## 9. Final questions

Answer:

1. Is the original deterministic mass drift mechanism removed?
2. Are total and colour channels both closed?
3. Does the selected fix preserve momentum locally?
4. Does it preserve V0/V1c/V2 physics?
5. Is the production choice preferable to full-f64 on correctness/complexity/
   performance grounds?
6. Is V3 scientifically safe to reconsider after external review?

## 10. Decision

Exactly one:

`PASS`
`CHANGES_REQUESTED`
`HUMAN_REQUIRED`

Even PASS returns to external scientific review.

Do not authorize V3 yourself.
