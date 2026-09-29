# START — BI-V2-BILATERAL-001

This is the single execution entry point for the revised V2 bilateral
verification.

Do not use the superseded old V2 contract.
Do not start V3.

## 1. Control checkout

Checkout/pull with fast-forward only:

\`agent-dev/bilateral-episode-v0.1\`

Read in full:

1. \`.agent/evidence/BI-V1C-CLOSURE-001/V1C_EXTERNAL_SCIENTIFIC_REVIEW_PASS.md\`
2. \`.agent/episodes/bilateral-imbibition-v0.1/V2_BILATERAL_CONTRACT.md\`
3. \`.agent/episodes/bilateral-imbibition-v0.1/V2_REVIEWER_CONTRACT.md\`
4. \`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`
5. \`AGENTS.md\`

## 2. Product branch

Create/verify a dedicated product worktree:

\`agent-task/BI-V2-BILATERAL-001\`

from exactly:

\`2b82f9a5f448e756b5d5903b0df37f9a3b11d804\`

Do not rewrite or modify V1c history.

If an existing worktree/branch is ambiguous, stop rather than resetting it.

## 3. Executor work

Act as Executor in the current ZCode session.

Execute \`V2_BILATERAL_CONTRACT.md\` exactly.

Important:

- h=40 primary;
- B=80, initial central gas gap G0=160;
- central gas is trapped from t=0;
- no reservoirs/membranes/pressure forcing;
- no absolute 30-degree front-speed gate;
- no \`x^2~t\` acceptance gate;
- collision/interaction is **not required**;
- no solver modification;
- do not tune physical/numerical parameters to pass.

Create the final V2 candidate, commit it, and push
\`agent-task/BI-V2-BILATERAL-001\` normally.

## 4. Review request

Write:

\`.agent_runtime/BI-V2-BILATERAL-001/REVIEW_REQUEST.md\`

including:

- task ID;
- exact base;
- exact candidate;
- product branch/worktree;
- changed-file list;
- primary run commands;
- execution-report path;
- provenance/manifest paths;
- clean-worktree statement.

## 5. Fresh reviewer

Launch a new headless ZCode session with no resume.

Reviewer reads:

\`.agent/episodes/bilateral-imbibition-v0.1/V2_REVIEWER_CONTRACT.md\`

and the review request.

It inspects the frozen candidate and writes only:

\`.agent_runtime/BI-V2-BILATERAL-001/REVIEW.md\`

Record reviewer session + exit code in:

\`.agent_runtime/BI-V2-BILATERAL-001/REVIEW_SESSION.json\`

Do not self-review.

## 6. Durable publication

Verify:

- product branch remains at reviewed candidate;
- product worktree clean;
- remote product ref resolves to the same SHA.

Publish on control branch under:

\`.agent/evidence/BI-V2-BILATERAL-001/\`

at minimum:

- \`REVIEW_REQUEST.md\`;
- \`REVIEW.md\`;
- \`REVIEW_SESSION.json\`;
- \`SUMMARY.md\`.

\`SUMMARY.md\` should contain:

- candidate SHA;
- reviewer decision;
- max/RMS front mirror error;
- one-sided displacement;
- colour-mass drift;
- rho min/max;
- gas volume change;
- gas mean rho/p change;
- initial/final cluster count;
- interaction onset or NOT_REACHED;
- maximum five unresolved issues.

## 7. Mandatory technical document

Update:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

and add V2 figures under:

\`docs/research/bilateral_imbibition/figures/\`

as required by the V2 contract.

The technical document must include formulas, key code excerpts, result
figures and candidate/evidence bindings.

Do not consider V2 complete without this update.

## 8. Stop conditions

Stop immediately on:

- solver-change requirement;
- NaN/Inf;
- density leaving the operational range in a scientifically consequential way;
- unexplained gas fragmentation/disappearance;
- reviewer session failure;
- \`CHANGES_REQUESTED\`;
- \`HUMAN_REQUIRED\`;
- \`PASS\`.

Even PASS stops for external scientific review.

Do not start V3.

## 9. Final console response

Return only:

\`\`\`text
TASK: BI-V2-BILATERAL-001
STATUS: PASS | CHANGES_REQUESTED | HUMAN_REQUIRED | FAILED

PRODUCT_BRANCH: agent-task/BI-V2-BILATERAL-001
BASE: 2b82f9a5f448e756b5d5903b0df37f9a3b11d804
CANDIDATE: <sha>

REVIEWER_SESSION: <session id>
REVIEW_DECISION: <decision>
TECHNICAL_DOC_UPDATED: YES|NO

PRIMARY_PRODUCT_EVIDENCE:
results/levelc_v2/EXECUTION_REPORT.md

PRIMARY_CONTROL_EVIDENCE:
.agent/evidence/BI-V2-BILATERAL-001/SUMMARY.md

NEXT_ACTION:
External scientific review required.
\`\`\`
