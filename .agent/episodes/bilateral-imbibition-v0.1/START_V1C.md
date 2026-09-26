# START — BI-V1C-CLOSURE-001

This is the single execution entry point for V1c.

## 1. Control checkout

Use:

\`agent-dev/bilateral-episode-v0.1\`

Read:

1. \`.agent/episodes/bilateral-imbibition-v0.1/V1C_CLOSURE_CONTRACT.md\`
2. \`.agent/episodes/bilateral-imbibition-v0.1/V1C_REVIEWER_CONTRACT.md\`
3. \`.agent/evidence/BI-V1B-DIAGNOSTIC-001/V1B_EXTERNAL_SCIENTIFIC_REVIEW.md\`
4. \`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`
5. \`AGENTS.md\`

## 2. Product branch

Create/verify:

\`agent-task/BI-V1C-CLOSURE-001\`

from exactly:

\`a9c6db87da2eeb3572607152391fe6863394ebee\`

Do not modify V1b history.

## 3. Execute

Act as Executor in the current session.

Execute \`V1C_CLOSURE_CONTRACT.md\`.

Freeze, commit and push the final product candidate.

## 4. Fresh review

Create a review request under:

\`.agent_runtime/BI-V1C-CLOSURE-001/\`

Launch a fresh ZCode reviewer with no resume.

Reviewer reads \`V1C_REVIEWER_CONTRACT.md\` and the frozen candidate.

Write:

- \`REVIEW.md\`
- \`REVIEW_SESSION.json\`

Do not self-review.

## 5. Durable control publication

Copy review request/review/session summary under:

\`.agent/evidence/BI-V1C-CLOSURE-001/\`

Then update:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

and add derived SVG result figures under:

\`docs/research/bilateral_imbibition/figures/\`

The document update must use only committed V1c product evidence.

Commit/push control evidence + technical document on:

\`agent-dev/bilateral-episode-v0.1\`

Do not modify \`episode_runner.py\`.

## 6. Stop

Stop on PASS, CHANGES_REQUESTED, HUMAN_REQUIRED, or failure.

Even PASS does not authorize V2.

Final console:

\`\`\`text
TASK: BI-V1C-CLOSURE-001
STATUS: <status>
PRODUCT_BRANCH: agent-task/BI-V1C-CLOSURE-001
CANDIDATE: <sha>
REVIEWER_SESSION: <id>
REVIEW_DECISION: <decision>
TECHNICAL_DOC_UPDATED: YES|NO
PRIMARY_EVIDENCE: <path>
NEXT_ACTION: External scientific review required.
\`\`\`
