# V1b Fresh Reviewer Contract

You are the independent reviewer for `BI-V1B-DIAGNOSTIC-001`.

## Inputs

Read in this order:

1. `AGENTS.md` from the control checkout.
2. `.agent/evidence/BI-VALIDATION-001/V1/V1/V1_EXTERNAL_SCIENTIFIC_REVIEW.md`.
3. `.agent/episodes/bilateral-imbibition-v0.1/V1B_DIAGNOSTIC_CONTRACT.md`.
4. the executor's `REVIEW_REQUEST.md`.
5. the frozen product candidate source and committed evidence.

Do not read or receive the executor conversation transcript.

## Binding

The review must bind to one exact candidate SHA.

Verify:

- HEAD equals candidate SHA;
- worktree is clean;
- candidate descends from `e9540bcadb86257c70b805afc98f2eec9626c64e`;
- no solver source changed;
- only V1b-authorized files changed.

## Independent checks

Do not trust summary JSON alone.

Recompute from committed CSV/JSON where practical:

- static `Pc_static` and `C_static`;
- h26/h40 static scaling;
- dynamic `V_meas`;
- `R2[x,t]`;
- `Pc_dynamic` from the documented far-field method;
- `V_hyd`;
- `V_meas/V_hyd`;
- plane-Poiseuille gradient consistency;
- length-scan `L_eq`;
- mass-closure metrics.

Inspect the exact boundary masks/indices and verify no reservoir/membrane overlap.

Check that every committed numerical artifact is source-bound by candidate/producer provenance.

A GPU rerun is optional unless committed evidence is internally inconsistent.

## Scientific questions

Explicitly answer:

1. Has the old ~190-lu fixed boundary-resistance signature been materially reduced?
2. Does same-slit static `Pc h/(2 sigma)` transfer consistently from h26 to h40?
3. Can the observed dynamic front speed be explained by independently measured `Pc_dynamic` plus slit hydraulic resistance?
4. What remains different between static and dynamic capillary pressure?
5. Is any remaining discrepancy a blocking numerical inconsistency, or a declared moving-contact-line/model characteristic?

## Decision

Choose exactly one:

`PASS`
`CHANGES_REQUESTED`
`HUMAN_REQUIRED`

Do not authorize V2. Even PASS returns to external scientific review.

## Output

Write `REVIEW.md` with:

- candidate binding;
- changed-file scope;
- gate table;
- independent recalculations;
- boundary-resistance assessment;
- static/dynamic wetting assessment;
- provenance assessment;
- blocking findings;
- non-blocking findings;
- decision;
- rationale;
- exact next action.
