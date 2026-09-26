# TASK

## ID

`ADS-EXECUTION-BASE-005`

## Objective

Make the cumulative execution base a first-class, machine-validated part of the V1 Controller protocol.

The fresh independent review of cumulative candidate `645479e00217b1b50f6cd4ae5d833eda1661e84c` found no blocking software defect, but identified one material infrastructure risk:

> New parent tasks do not currently declare or machine-verify the accepted cumulative product commit they are supposed to start from. Round 1 can therefore start from the wrong source state while still satisfying existing Controller checks.

Implement the smallest repair. Do **not** build a DAG, merge manager, auto-integration system, or generalized dependency graph.

## Bootstrap Note

This task itself is executed by the pre-repair Controller. Therefore its task branch has been manually pre-created from:

`dbecc71898131cc6545bf314dc2f7ba56d1df337`

and the queued state carries that SHA as both the current bootstrap `candidate_commit` and the new `execution_base_commit`.

After this task is accepted, future parent tasks should no longer require manual pre-creation merely to select their starting source revision.

## Scope

### Allowed

- `.agent/controller/controller.py`
- `.agent/controller/tests/test_controller.py`
- `.agent/README.md`
- `.agent/templates/TASK.md`

### Do not modify

- CG3D production/scientific code
- existing scientific tests
- `.agent/state.json` from the executor
- task/evidence records of earlier tasks
- Z Code runtime behavior unrelated to base selection
- merge policy
- max-round policy
- evidence trust semantics except adding base provenance

## Required State Semantics

Add a first-class state field:

`execution_base_commit`

Meaning:

- immutable starting source revision for the **parent task**;
- Round 1 must start exactly from this commit;
- Round 2/3 keep the same `execution_base_commit`;
- later rounds continue from the latest reviewed `candidate_commit`, not from the original execution base;
- it is provenance, not an instruction to reset subsequent rounds.

For active non-draft tasks, require a valid full 40-character lowercase hexadecimal Git SHA.

For DRAFT state, `execution_base_commit` may be `null`.

Do not overload `candidate_commit` with this meaning:

- `execution_base_commit` = original parent-task start revision;
- `candidate_commit` = latest candidate produced/reviewed on the task branch.

## Round-1 Worktree Rules

For a fresh Round 1:

1. If no task branch exists, create the task branch from `execution_base_commit`, **not** from control-branch `ready_sha`.
2. After preparing the worktree and before invoking the executor, assert:
   `before_head == execution_base_commit`.
3. If a pre-existing local/remote task branch exists for Round 1, it must resolve to the declared `execution_base_commit` before execution begins.
4. A mismatch must fail clearly before Z Code execution and publish/record an ERROR through the existing failure path.
5. Do not silently reset, rebase, force-update, or rewrite the task branch.

The control READY commit may differ from `execution_base_commit`; that is expected and must no longer affect the product-code starting revision.

## Later-Round Rules

For Round 2/3:

- preserve `execution_base_commit` unchanged;
- require/use the current reviewed `candidate_commit` as the continuation head, as V1 already does;
- do not reset the task branch to `execution_base_commit`;
- preserve existing Z Code session-resume behavior.

## Provenance / Evidence

Record the declared execution base in Controller-owned evidence.

At minimum:

1. add `execution_base_commit` to `process.json`;
2. add `execution_base_commit` to Controller-generated executor `provenance.json`;
3. ensure `before_head` remains recorded so a reviewer can compare:
   - Round 1: `before_head == execution_base_commit`;
   - later rounds: `before_head == prior candidate_commit`.

Optionally add a small dedicated Controller evidence text file if it materially improves clarity, but do not duplicate data unnecessarily.

The Controller still does not interpret validation PASS/FAIL.

## TASK Template / Documentation

Update `.agent/templates/TASK.md` so a planner records the execution base explicitly for new parent tasks.

A simple section is sufficient, e.g.:

```text
## Execution Base

<full commit SHA>
```

Update `.agent/README.md` state/protocol documentation to explain:

- the new state field;
- Round 1 base selection;
- later-round continuation;
- difference between control branch revision and execution/product base;
- provenance/evidence behavior.

Do not introduce a machine parser for the Markdown TASK section in this task. The state field is authoritative for the Controller.

## Requirements

1. Add and validate `execution_base_commit` in state handling.
2. Fresh Round 1 worktrees are created from that SHA, not `ready_sha`.
3. Round 1 branch/head mismatch is rejected before executor invocation.
4. Later rounds still resume from `candidate_commit`.
5. Preserve the same `execution_base_commit` across state transitions.
6. Add base SHA to Controller process evidence and executor-evidence provenance.
7. Keep existing evidence-publication constraints unchanged.
8. Keep existing allowed-path enforcement unchanged.
9. Keep existing max-round/session-resume/error behavior unchanged.
10. Update tests and protocol docs.

## Validation Requested

Run:

```text
python .agent/controller/tests/test_controller.py
```

Add deterministic tests covering at least:

1. active state missing `execution_base_commit` is rejected;
2. malformed active base SHA is rejected;
3. DRAFT may use null base;
4. Round 1 with no task branch starts from declared base even when control `ready_sha` is different;
5. Round 1 `before_head` equals declared base;
6. pre-existing Round 1 branch at the wrong SHA is rejected before executor execution;
7. Round 2 continues from Round 1 candidate rather than resetting to original base;
8. `execution_base_commit` remains unchanged across Round 1 → Round 2;
9. `process.json` contains both `before_head` and `execution_base_commit`;
10. executor `provenance.json` contains `execution_base_commit`;
11. existing evidence-publication success/failure tests still pass;
12. existing timeout, scope, candidate/session and max-round tests still pass.

A useful end-to-end fixture should deliberately make:

`control READY SHA != execution_base_commit`

and prove that the executor's Round-1 `before_head` is nevertheless the declared execution base.

## Durable Executor Evidence

Publish via `.agent_runtime/published_evidence/`:

- `controller_tests.log`
  - kind: `validation_log`
  - command: `python .agent/controller/tests/test_controller.py`
- `base_semantics_summary.json`
  - kind: `validation_summary`
  - include the tested Round-1 base, control READY SHA, observed `before_head`, Round-1 candidate, Round-2 `before_head`, and whether all relevant assertions passed.

Keep decisive results in `execution_report.md` as well.

## Evidence Requested

Report:

- starting/bootstrap SHA;
- candidate SHA;
- changed files;
- exact test command and exit code;
- number of tests run and result;
- one concrete end-to-end example proving control READY SHA can differ from execution base while Round 1 starts from the execution base;
- Round-2 continuation example proving it uses prior candidate;
- process/provenance snippets showing the new base field;
- confirmation that no CG3D product code changed.

## Git Policy

- commit/push allowed on the pre-created task branch;
- do not merge to `master`;
- do not modify the control branch directly from the executor;
- no force-push/history rewrite.

## Human Decisions Reserved

- whether/when to merge Controller changes;
- future integration-branch policy;
- any automatic merge/DAG/dependency design;
- scientific validation sequence after this infrastructure repair.

## Notes / References

Fresh independent review conclusion: `PASS WITH FOLLOW-UPS`.

The review classified missing cumulative-base enforcement as a genuine future correctness/reproducibility risk, while confirming the current V1 candidate itself is correctly based.

The desired V1 invariant after this task is:

```text
Round 1:
  actual before_head == state.execution_base_commit

Round N > 1:
  actual before_head == prior reviewed candidate_commit

state.execution_base_commit:
  unchanged for the lifetime of the parent task
```
