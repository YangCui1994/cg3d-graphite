# Future GPT-6 Pro Framework Audit Package

Do not request this audit before the first real Episode v0.1 run exists.

The purpose of the later audit is not to re-review LBM physics from scratch. It is to decide which orchestration/contract patterns should become a reusable scientific-computing agent framework.

## Provide these framework documents

- EPISODE_PLAN.md
- RUNNER_BOOTSTRAP.md
- EXECUTOR_CONTRACT.md
- REVIEWER_CONTRACT.md
- CHECKPOINT_AND_PROMOTION.md
- one representative Stage Contract, preferably V2
- ARCHITECTURE.md

## Provide these real-run artifacts

- final V3 CHECKPOINT.md;
- one successful stage history;
- one rework history if any occurred;
- one reviewer report that found a nontrivial issue;
- runner state/provenance summary;
- total attempts and wall-clock execution profile;
- any HUMAN_REQUIRED event;
- concise user/ChatGPT postmortem.

## Ask GPT-6 Pro to audit

1. Role isolation:
   - Does fresh reviewer context meaningfully reduce self-confirmation?
   - Where can same-model blind spots remain?

2. Contract design:
   - Which constraints are useful?
   - Which are over-specified?
   - Which scientific decisions are incorrectly delegated?

3. Evidence/provenance:
   - Is candidate binding sufficient?
   - Can a later reviewer reconstruct what actually ran?

4. Promotion logic:
   - Are PASS / CHANGES_REQUESTED / HUMAN_REQUIRED boundaries clear?
   - Are maximum attempts and checkpoints placed well?

5. Generalizability:
   - Which parts should be reusable for CFD/DEM/other scientific simulation?
   - Which are LBM-specific and should stay in stage contracts?

6. Token/latency efficiency:
   - What context can be removed from executor/reviewer prompts?
   - What evidence should be summarized versus retained raw?

7. Failure modes:
   - loops;
   - self-confirmation;
   - threshold gaming;
   - stale evidence;
   - overfitting validation cases;
   - silent scientific-scope drift.

## Explicitly out of scope for the framework audit

- selecting the user's scientific objective;
- deciding the real battery PCS geometry;
- re-deriving the entire CG-LBM method;
- ranking models/vendors;
- redesigning the project from zero unless a demonstrated failure requires it.
