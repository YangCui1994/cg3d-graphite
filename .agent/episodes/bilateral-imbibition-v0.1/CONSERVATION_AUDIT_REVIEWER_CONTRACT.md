# Conservation Audit Fresh Reviewer Contract

Task: \`BI-CONSERVATION-AUDIT-001\`

You are the independent fresh reviewer.

## Binding

Verify:

- candidate SHA;
- clean product worktree;
- candidate descends from V2 candidate
  \`5e679d8d99d338f9ab28565c636f021a0f9211b2\`;
- no solver source changed;
- only audit-specific files changed;
- artifact hashes and producer revision are valid.

Do not read or receive the executor transcript.

## Scientific review

Independently verify from committed evidence:

1. C0/C1/C2/C3 definitions;
2. production kernel ordering;
3. per-substep mass identities;
4. first checkpoint where:
   - \`M_f-M_c\`;
   - \`M_f-M_rho\`;
   - \`M_c-M_rho\`
   become materially nonzero;
5. whether any apparent mismatch is only a transitional storage representation;
6. long-horizon drift rates;
7. spatial mass budget;
8. backend/precision comparison;
9. scaling with timestep / domain / interface or wall area.

## Required caution

Do not call something "floating-point noise" merely because the absolute number is small.

A \`PASS_BOUNDED_FLOOR\` requires positive evidence of bounded precision scaling.

Do not call recoloring or bounce-back the cause merely from spatial correlation.

Mechanism attribution requires sub-step localization.

## Decision classes

Choose exactly one:

- \`PASS_DIAGNOSIS_READY_FOR_FIX\`
- \`PASS_BOUNDED_FLOOR\`
- \`CHANGES_REQUESTED\`
- \`HUMAN_REQUIRED\`

### PASS_DIAGNOSIS_READY_FOR_FIX

Requires:

- specific kernel/sub-step localization;
- reproducible conservation identity failure;
- credible minimal fix scope;
- regression list.

### PASS_BOUNDED_FLOOR

Requires:

- no discrete imbalance;
- quantitative scaling consistent with accumulation precision;
- operational bound supported by multiple cases/backends/scales.

### CHANGES_REQUESTED

Only for bounded audit implementation/evidence defects.

### HUMAN_REQUIRED

When evidence conflicts or diagnosis remains underdetermined.

## Technical-document review

Verify that the living document update:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

matches the frozen candidate evidence and includes:

- formulas;
- code excerpts;
- result figures;
- mechanism classification;
- evidence links.

Even PASS does not authorize a solver fix or V3.

Stop after review.
