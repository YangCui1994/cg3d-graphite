# DeepSeek Transition Fresh Reviewer Contract

Task ID: BI-DEEPSEEK-TRANSITION-001

Use a fresh DeepSeek session. Do not read or request the executor transcript.
Do not modify the product candidate.

## Binding checks

Verify:
- exact base ancestry from 6c30260dfe0c8b61ea9609e6bffa5c487312cf06;
- exact candidate SHA;
- clean worktree;
- no solver modification;
- no V3 execution;
- no graphite/separator/gap/PCS work.

## Independent recomputation

Recompute from raw committed evidence, not from executor summaries:

1. periodic-C1 240k colour slope and R2;
2. four periodic-C1 60k slopes;
3. C3 120k colour slope and R2;
4. four C3 30k slopes;
5. V2 max blue relative mass drift;
6. V2 max mirror error;
7. V2 trapped-cluster status;
8. V2 interaction status.

Compare with:
results/model_transition/recomputed_metrics.json

## Scientific-state comprehension

Verify V3_READINESS_AND_PERIODIC_BC_AUDIT.md correctly states:
- T3 + C1X + A2 is frozen;
- V1c/V2/conservation are accepted;
- central gas is trapped from t=0;
- old isolation-time/pre-isolation V3 framing is obsolete;
- revised V3 is planning only;
- periodic-BC tests are proposed, not executed;
- graphite/separator/gap/PCS remain unauthorized.

## V3 design quality

Check the proposed design distinguishes:
- hard invariants;
- scientific diagnostics;
- buffer-size sensitivity;
- periodic-BC sanity checks;
- stop conditions.

Review scientific consistency and executability, not prose style.

## Reviewer outputs

Write only:
- .agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW.md
- .agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW_SESSION.json

Decision exactly:
PASS
CHANGES_REQUESTED
HUMAN_REQUIRED

PASS means DeepSeek is sufficiently calibrated for a staged revised-V3 task.
PASS does not itself start or execute V3.
Return the package to ChatGPT for external review.
