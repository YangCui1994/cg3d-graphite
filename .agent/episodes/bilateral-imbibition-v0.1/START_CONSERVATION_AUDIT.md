# START — BI-CONSERVATION-AUDIT-001

This is the single execution entry point for the solver conservation audit.

## 1. Control checkout

Checkout/pull:

\`agent-dev/bilateral-episode-v0.1\`

fast-forward only.

Read in full:

1. \`.agent/evidence/BI-V2-BILATERAL-001/V2_EXTERNAL_SCIENTIFIC_REVIEW_PASS.md\`
2. \`.agent/episodes/bilateral-imbibition-v0.1/CONSERVATION_AUDIT_CONTRACT.md\`
3. \`.agent/episodes/bilateral-imbibition-v0.1/CONSERVATION_AUDIT_REVIEWER_CONTRACT.md\`
4. \`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`
5. \`AGENTS.md\`

## 2. Product branch

Create:

\`agent-task/BI-CONSERVATION-AUDIT-001\`

from exactly:

\`5e679d8d99d338f9ab28565c636f021a0f9211b2\`

Do not reuse or rewrite the V2 product branch.

## 3. Executor task

In the current ZCode session act as Executor.

Execute:

\`CONSERVATION_AUDIT_CONTRACT.md\`

exactly.

Important:

- do not modify \`lbm_solver_cg3d.py\`;
- do not change physics;
- use direct calls to existing public kernels to expose the production timestep checkpoints;
- commit/push only audit-specific source/evidence;
- do not start a solver fix even if the defect becomes obvious.

## 4. Freeze candidate

After audit execution:

- ensure product worktree clean;
- commit final audit candidate;
- push normally;
- write a review request containing exact candidate/base, changed files, commands, artifacts and producer hashes.

## 5. Fresh reviewer

Launch a fresh ZCode reviewer with no resume.

Reviewer must read:

\`.agent/episodes/bilateral-imbibition-v0.1/CONSERVATION_AUDIT_REVIEWER_CONTRACT.md\`

and the review request.

Reviewer writes only:

\`.agent_runtime/BI-CONSERVATION-AUDIT-001/REVIEW.md\`

plus session metadata.

Do not self-review.

## 6. Durable publication

Publish to:

\`.agent/evidence/BI-CONSERVATION-AUDIT-001/\`

at least:

- REVIEW_REQUEST.md
- REVIEW.md
- REVIEW_SESSION.json
- SUMMARY.md

Then update:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

and add source-backed SVG result figures under:

\`docs/research/bilateral_imbibition/figures/\`

The living technical document is mandatory.

## 7. Stop

Stop after review and technical-document publication.

Do not:

- modify solver;
- create solver-fix code;
- start V3;
- start porous-media work.

Final console response:

\`\`\`text
TASK: BI-CONSERVATION-AUDIT-001
STATUS: PASS_DIAGNOSIS_READY_FOR_FIX | PASS_BOUNDED_FLOOR | CHANGES_REQUESTED | HUMAN_REQUIRED | FAILED

PRODUCT_BRANCH: agent-task/BI-CONSERVATION-AUDIT-001
BASE: 5e679d8d99d338f9ab28565c636f021a0f9211b2
CANDIDATE: <sha>

REVIEWER_SESSION: <id>
REVIEW_DECISION: <decision>

MECHANISM_CLASS: A | B | C | D | E | U
FIRST_DIVERGENCE_CHECKPOINT: <checkpoint or NONE>

TECHNICAL_DOC_UPDATED: YES|NO
PRIMARY_EVIDENCE: <path>

NEXT_ACTION:
External scientific review required.
\`\`\`
