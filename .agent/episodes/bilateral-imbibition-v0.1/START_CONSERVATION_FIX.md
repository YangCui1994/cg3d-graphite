# START — BI-SOLVER-CONSERVATION-FIX-001

This is the single execution entry point for the authorized conservation fix.

## 1. Control checkout

Checkout/pull with fast-forward only:

`agent-dev/bilateral-episode-v0.1`

Read in full:

1. `.agent/evidence/BI-CONSERVATION-AUDIT-001/CONSERVATION_EXTERNAL_REVIEW_PASS.md`
2. `.agent/evidence/BI-CONSERVATION-AUDIT-001/INDEPENDENT_EXTERNAL_REVIEW_CONFIRMATION.md`
3. `docs/research/bilateral_imbibition/CONSERVATION_FIX_LITERATURE_NOTE.md`
4. `.agent/episodes/bilateral-imbibition-v0.1/SOLVER_CONSERVATION_FIX_CONTRACT.md`
5. `.agent/episodes/bilateral-imbibition-v0.1/SOLVER_CONSERVATION_FIX_REVIEWER_CONTRACT.md`
6. `docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`
7. `AGENTS.md`

## 2. Product branch

Create/verify:

`agent-task/BI-SOLVER-CONSERVATION-FIX-001`

from exactly:

`1f5ee76fa183b42dd0ffcb291f389c3f1974a147`

Do not rewrite audit/V2 history.

## 3. Search first

Before modifying solver code, execute the two-pass literature / implementation
search required by the contract and write:

`results/conservation_fix/LITERATURE_AND_IMPLEMENTATION_SEARCH.md`

If internet/search access is unavailable, record that limitation and use the
control-branch literature memo as the minimum baseline; do not fabricate
sources.

Search results may add candidates, but do not skip T0-T4/C0-C1 without an
explicit F0-based elimination.

## 4. Candidate comparison and implementation

Execute the contract.

Do not immediately promote the first working fix.

Compare candidates, preserve failed alternatives in evidence, then select the
smallest passing production fix.

Solver changes are authorized only inside this task.

Do not change physical parameters or weaken physics gates.

## 5. Freeze candidate

Commit/push the final selected solver fix and all product evidence to:

`agent-task/BI-SOLVER-CONSERVATION-FIX-001`

Write:

`.agent_runtime/BI-SOLVER-CONSERVATION-FIX-001/REVIEW_REQUEST.md`

with exact candidate/base, changed files, candidate comparison, commands,
evidence paths and clean-worktree statement.

## 6. Fresh review

Launch a new headless ZCode reviewer with no resume.

Reviewer reads:

`.agent/episodes/bilateral-imbibition-v0.1/SOLVER_CONSERVATION_FIX_REVIEWER_CONTRACT.md`

and the review request.

Reviewer writes only:

- `REVIEW.md`
- `REVIEW_SESSION.json`

under:

`.agent_runtime/BI-SOLVER-CONSERVATION-FIX-001/`

No self-review.

## 7. Durable publication

After review, publish on control branch:

`.agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/`

including:

- `REVIEW_REQUEST.md`
- `REVIEW.md`
- `REVIEW_SESSION.json`
- `SUMMARY.md`

## 8. Mandatory technical document

Update:

`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`

and add fix figures under:

`docs/research/bilateral_imbibition/figures/`

as required by the contract.

Do not consider the task complete without the technical-document update.

## 9. Stop

Stop on PASS, CHANGES_REQUESTED, HUMAN_REQUIRED or failure.

Even PASS requires external scientific review before V3 can be reconsidered.

Do not start V3.

## 10. Final console response

Return only:

```text
TASK: BI-SOLVER-CONSERVATION-FIX-001
STATUS: PASS | CHANGES_REQUESTED | HUMAN_REQUIRED | FAILED

PRODUCT_BRANCH: agent-task/BI-SOLVER-CONSERVATION-FIX-001
BASE: 1f5ee76fa183b42dd0ffcb291f389c3f1974a147
CANDIDATE: <sha>

SELECTED_FIX: <short description>
TOTAL_DRIFT_RATE: <value>
COLOUR_DRIFT_RATE: <value>
PERFORMANCE_DELTA: <value>

REVIEWER_SESSION: <id>
REVIEW_DECISION: <decision>
TECHNICAL_DOC_UPDATED: YES|NO

PRIMARY_PRODUCT_EVIDENCE:
results/conservation_fix/EXECUTION_REPORT.md

PRIMARY_CONTROL_EVIDENCE:
.agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/SUMMARY.md

NEXT_ACTION:
External scientific review required; V3 remains HOLD.
```
