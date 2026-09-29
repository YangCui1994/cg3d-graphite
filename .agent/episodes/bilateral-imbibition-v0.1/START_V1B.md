# START — BI-V1B-DIAGNOSTIC-001

This is the single execution entry point for the V1b scientific diagnostic.

Do not modify the approved Episode Runner.
Do not resume the old V1 stage.
Do not start V2/V3.

## 1. Control checkout

Use branch:

`agent-dev/bilateral-episode-v0.1`

Fetch and fast-forward only.

Read in full:

1. `.agent/evidence/BI-VALIDATION-001/V1/V1/V1_EXTERNAL_SCIENTIFIC_REVIEW.md`
2. `.agent/episodes/bilateral-imbibition-v0.1/V1B_DIAGNOSTIC_CONTRACT.md`
3. `.agent/episodes/bilateral-imbibition-v0.1/V1B_REVIEWER_CONTRACT.md`
4. `AGENTS.md`

## 2. Product branch

Create a dedicated product branch/worktree from exactly:

`e9540bcadb86257c70b805afc98f2eec9626c64e`

Branch name:

`agent-task/BI-V1B-DIAGNOSTIC-001`

Do not reuse `agent-episode/BI-VALIDATION-001` for new commits.

If the branch/worktree already exists, verify its base/provenance and cleanliness before using it. Do not reset or overwrite ambiguous work.

## 3. Executor work

In the current ZCode session, act as the Executor.

Execute `V1B_DIAGNOSTIC_CONTRACT.md` exactly.

Important:

- no solver modification;
- create V1b-specific driver/results rather than rewriting V1 history;
- run the static h26/h40 calibration;
- run corrected dynamic h26/h40;
- run one approximately 2x-length h26 case;
- preserve exact logs, exit codes, raw/reduced numerical evidence;
- do not tune model parameters to pass;
- create `results/levelc_v1b/EXECUTION_REPORT.md`;
- create `results/levelc_v1b/PROVENANCE.md`;
- create `results/levelc_v1b/MANIFEST.json`;
- commit the final candidate;
- push `agent-task/BI-V1B-DIAGNOSTIC-001` normally, never force-push.

After the final candidate commit, ensure any committed derived artifact is actually bound to the final producer revision. If this cannot be guaranteed, omit the derived artifact and preserve numerical data instead.

## 4. Create the review request

Write:

`.agent_runtime/BI-V1B-DIAGNOSTIC-001/REVIEW_REQUEST.md`

It must contain:

- task ID;
- product branch;
- exact candidate SHA;
- base SHA;
- absolute product worktree path;
- execution report path;
- provenance path;
- manifest path;
- exact changed-file list;
- exact primary run commands;
- statement that the product worktree is clean.

## 5. Launch a fresh ZCode reviewer

Do **not** review in the executor session.

Launch a new headless ZCode session with no `--resume`.

Use the installed ZCode CLI:

`C:/Program Files/ZCode/resources/glm/zcode.cjs`

The fresh reviewer prompt must tell it to:

- read `.agent/episodes/bilateral-imbibition-v0.1/V1B_REVIEWER_CONTRACT.md`;
- read `.agent_runtime/BI-V1B-DIAGNOSTIC-001/REVIEW_REQUEST.md`;
- inspect the frozen candidate in the product worktree;
- write its review only to:
  `.agent_runtime/BI-V1B-DIAGNOSTIC-001/REVIEW.md`;
- never modify product files;
- never use the executor transcript.

Record the reviewer session ID and exit code in:

`.agent_runtime/BI-V1B-DIAGNOSTIC-001/REVIEW_SESSION.json`.

If the fresh reviewer fails to produce a valid review, stop. Do not self-review.

## 6. Durable publication

After the reviewer completes:

1. verify the product branch still points to the reviewed candidate and is clean;
2. verify the remote product branch resolves to the same candidate SHA;
3. copy the following into:
   `.agent/evidence/BI-V1B-DIAGNOSTIC-001/`

   - `REVIEW_REQUEST.md`
   - `REVIEW.md`
   - `REVIEW_SESSION.json`

4. also write `SUMMARY.md` containing:
   - candidate SHA;
   - reviewer decision;
   - static h26/h40 `Pc_static` and `C_static`;
   - dynamic h26/h40 `V_meas`, `Pc_dynamic`, `V_hyd`, mismatch;
   - length-scan `L_eq/L1`;
   - maximum five unresolved scientific issues.

Commit and push these control-plane evidence files on:

`agent-dev/bilateral-episode-v0.1`

Do not modify `episode_runner.py`.

## 7. Stop conditions

Stop immediately if:

- solver modification appears necessary;
- executor leaves ambiguous/uncommitted source state;
- any primary run has unexplained NaN/Inf;
- fresh reviewer returns `HUMAN_REQUIRED`;
- fresh reviewer returns `CHANGES_REQUESTED`;
- reviewer session fails;
- evidence cannot be bound to the final candidate.

Even if reviewer returns `PASS`, stop for external scientific review.

## 8. Final console response

Return only:

```text
TASK: BI-V1B-DIAGNOSTIC-001
STATUS: PASS | CHANGES_REQUESTED | HUMAN_REQUIRED | FAILED

PRODUCT_BRANCH: agent-task/BI-V1B-DIAGNOSTIC-001
BASE: e9540bcadb86257c70b805afc98f2eec9626c64e
CANDIDATE: <sha>

REVIEWER_SESSION: <session id>
REVIEW_DECISION: <decision>

PRIMARY_PRODUCT_EVIDENCE:
results/levelc_v1b/EXECUTION_REPORT.md

PRIMARY_CONTROL_EVIDENCE:
.agent/evidence/BI-V1B-DIAGNOSTIC-001/SUMMARY.md

NEXT_ACTION:
External scientific review required.
```

Do not start V2/V3.
