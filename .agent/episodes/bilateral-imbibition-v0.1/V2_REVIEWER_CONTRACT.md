# V2 Fresh Reviewer Contract

Task ID: BI-V2-BILATERAL-001

You are the independent reviewer of the frozen V2 bilateral candidate.

## Inputs

Read in this order:

1. \`AGENTS.md\`;
2. \`.agent/evidence/BI-V1C-CLOSURE-001/V1C_EXTERNAL_SCIENTIFIC_REVIEW_PASS.md\`;
3. \`.agent/episodes/bilateral-imbibition-v0.1/V2_BILATERAL_CONTRACT.md\`;
4. executor \`REVIEW_REQUEST.md\`;
5. frozen product candidate source + committed evidence.

Do not read the executor conversation transcript.

## Binding

Verify:

- exact candidate SHA;
- clean product worktree;
- candidate descends from
  \`2b82f9a5f448e756b5d5903b0df37f9a3b11d804\`;
- no solver / cg3d / prior-stage source changes;
- only V2-authorized files changed.

## Scientific review requirements

### A. Geometry / symmetry

Independently verify the masks/arrays are exact mirror images.

Check:

- h=40;
- B=80;
- G0=160;
- equal left/right buffers;
- no reservoirs;
- no membranes;
- no force;
- solid outer x walls;
- z periodic only for fluid topology.

Recompute the initial symmetry tests rather than accepting executor claims.

### B. Front symmetry

From committed front time series recompute:

- left/right positions;
- mirrored-right coordinate;
- max/RMS mirror error;
- one-sided displacement;
- conditional left/right fitted-rate comparison.

Do not use \`x^2(t)\` as a physical acceptance relation.

Do not require a specific absolute front speed.

### C. Trapped-pocket topology

Verify at t=0 that the central gas is already trapped.

Do **not** search for a nonexistent later vent-loss event.

Recompute / inspect:

- initial gas cluster count;
- connectivity convention: 6-neighbour, periodic z only;
- gas volume / continuous saturation;
- gas mass proxy;
- mean gas rho/p;
- buffer gas occupancy;
- cluster count and largest cluster through time.

Treat unexplained fragmentation/disappearance before declared interface
interaction as blocking.

### D. Interaction event

Verify the declared bulk/mixed-column rule.

If \`INTERACTION_ONSET\` is reached, recompute it from committed fields or
reduced column data.

If it is not reached, \`NOT_REACHED\` is an acceptable outcome and is not a
failure.

### E. Conservation / stability

Recompute:

- red/blue colour-mass drift;
- \`u_max\`;
- \`rho_min/rho_max\`;
- NaN/Inf status.

Check the project gates in the contract.

### F. Interpretation

Explicitly answer:

1. Is bilateral symmetry preserved?
2. Does the central trapped gas remain numerically coherent?
3. Is any gas-volume reduction explainable within the weakly compressible
   numerical model without leaving the operational density range?
4. Did interface overlap occur? If yes, was it resolved reproducibly?
5. Is there any evidence requiring a solver change before V3?

Do not interpret pocket pressure as validated real-air compression.

## Evidence/provenance

Check candidate/producer binding and MANIFEST hashes.

A GPU rerun is optional unless the committed evidence is internally
inconsistent.

## Living technical document

Review the proposed V2 update to:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

for consistency with the candidate.

The document is part of the deliverable.

## Decision

Choose exactly one:

\`PASS\`
\`CHANGES_REQUESTED\`
\`HUMAN_REQUIRED\`

Even \`PASS\` returns to external scientific review and does not authorize V3.

## Output

Write \`REVIEW.md\` containing:

- candidate binding;
- requirement/gate table;
- independent symmetry recomputation;
- topology review;
- interaction-event review;
- conservation/stability review;
- interpretation boundary;
- provenance assessment;
- blocking findings;
- non-blocking findings;
- decision;
- rationale;
- exact next action.
