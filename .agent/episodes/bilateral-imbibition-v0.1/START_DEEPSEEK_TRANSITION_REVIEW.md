# START — BI-DEEPSEEK-TRANSITION-001 — Fresh Reviewer

You are the fresh independent DeepSeek reviewer.

## 1. Sync

Checkout/pull with fast-forward only:

agent-dev/bilateral-episode-v0.1

Read:
1. .agent/episodes/bilateral-imbibition-v0.1/DEEPSEEK_TRANSITION_REVIEWER_CONTRACT.md
2. .agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW_REQUEST.md
3. .agent/evidence/BI-COLOUR-CLOSURE-001/EXTERNAL_SCIENTIFIC_REVIEW_PASS.md
4. AGENTS.md

Do not read or request the executor transcript.

## 2. Review

Inspect the frozen candidate on:

agent-task/BI-DEEPSEEK-TRANSITION-001

Follow DEEPSEEK_TRANSITION_REVIEWER_CONTRACT.md exactly.

Independently recompute the required metrics from raw committed evidence.
Do not trust recomputed_metrics.json until you reproduce it.

Do not modify the candidate.
Do not run V3.

## 3. Outputs

Write only:
- .agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW.md
- .agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW_SESSION.json

Decision exactly:
PASS / CHANGES_REQUESTED / HUMAN_REQUIRED

Then STOP and return a compact review status.
