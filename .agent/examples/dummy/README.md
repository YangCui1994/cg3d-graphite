# Two-round dummy flow

This fixture exercises infrastructure only. It must not touch LBM code, data,
results, physics, or GPU execution.

## Round 1 dispatch

The planner copies `ROUND_1_TASK.md` to:

```text
.agent/tasks/ADS-DUMMY-001/round-01/TASK.md
```

It then sets `.agent/state.json` to `READY_FOR_EXECUTION`, with `task_id` set
to `ADS-DUMMY-001` and `round` set to `1`, commits, and pushes the control
branch. That READY transition authorizes the controller to commit and push the
candidate task branch; it never authorizes a merge.

The controller must finish at `AWAITING_REVIEW`. The reviewer checks the task,
candidate diff, executor report, and independently captured evidence.

## Round 2 dispatch

If Round 1 is `PASS + CONTINUE`, the planner:

1. writes `REVIEW.md` in the Round 1 directory;
2. copies `ROUND_2_TASK.md` to
   `.agent/tasks/ADS-DUMMY-001/round-02/TASK.md`;
3. increments `round` and `revision`, retains `candidate_commit` and
   `zcode_session_id`, and changes state to `READY_FOR_EXECUTION`;
4. commits and pushes the control branch.

Round 2 must run with `--resume <round-1-session-id>`. A second `PASS` means
only that Round 2 requirements passed. The planner separately chooses whether
to set the parent task to `CLOSED`.
