# START — BI-COLOUR-CLOSURE-001

Single entry point for the narrow colour-channel follow-up.

## Control

Checkout/pull fast-forward only:
agent-dev/bilateral-episode-v0.1

Read:
1. .agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md
2. .agent/episodes/bilateral-imbibition-v0.1/COLOUR_CLOSURE_CONTRACT.md
3. .agent/episodes/bilateral-imbibition-v0.1/COLOUR_CLOSURE_REVIEWER_CONTRACT.md
4. docs/research/bilateral_imbibition/CONSERVATION_FIX_LITERATURE_NOTE.md
5. docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md
6. AGENTS.md

## Product branch

Create/verify:
agent-task/BI-COLOUR-CLOSURE-001

from exactly:
e256b4857a6e51510b75358994d7c5bcc742781e

Do not rewrite prior history.

## Execution order

1. Freeze T3 total path. Do not reopen T0-T4.
2. Reproduce current blocker from committed evidence.
3. Diagnose local colour residual classes before code changes.
4. Run periodic-C1 accumulation test.
5. Compare current scoped-C1 against at least one diagnosis-informed colour-only alternative.
6. Select the smallest candidate that satisfies the frozen gates.
7. Run required A2/V1c/V2/T3 non-regressions.
8. Commit/push the final candidate.

Do not weaken any gate. Do not start V3.

## Fresh review

Write .agent_runtime/BI-COLOUR-CLOSURE-001/REVIEW_REQUEST.md with exact base/candidate, changed files, diagnosis, candidate comparison, commands and evidence paths.

Launch a fresh headless reviewer with no resume using COLOUR_CLOSURE_REVIEWER_CONTRACT.md.

Write REVIEW.md and REVIEW_SESSION.json. No self-review.

## Durable publication

Publish on control branch under:
.agent/evidence/BI-COLOUR-CLOSURE-001/

At minimum:
- REVIEW_REQUEST.md
- REVIEW.md
- REVIEW_SESSION.json
- SUMMARY.md

Update:
docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md

Add evidence-derived figures under:
docs/research/bilateral_imbibition/figures/

Stop after PASS / CHANGES_REQUESTED / HUMAN_REQUIRED / failure.
Even PASS requires external scientific review before V3.

Final console:

TASK: BI-COLOUR-CLOSURE-001
STATUS: <status>
PRODUCT_BRANCH: agent-task/BI-COLOUR-CLOSURE-001
BASE: e256b4857a6e51510b75358994d7c5bcc742781e
CANDIDATE: <sha>
RESIDUAL_SOURCE_CLASS: <short>
SELECTED_COLOUR_FIX: <short>
C1_COLOUR_DRIFT: <value>
C3_COLOUR_DRIFT: <value>
C3_TOTAL_DRIFT: <value>
A2_UMAX: <value>
A26: <value>
A40: <value>
V2_MAX_EPS_B: <value>
REVIEWER_SESSION: <id>
REVIEW_DECISION: <decision>
TECHNICAL_DOC_UPDATED: YES|NO
NEXT_ACTION: External scientific review required; V3 remains HOLD.
