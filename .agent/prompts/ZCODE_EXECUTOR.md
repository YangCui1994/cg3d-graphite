# Z Code Executor Prompt — Step 0

Use this prompt for Z Code execution tasks in this repository.

---

Read `AGENTS.md` first.

Then read the task at:

`.agent_runtime/TASK.md`

Execute **only** that task.

Rules:

1. Respect the task's allowed scope and forbidden scope.
2. Do not silently change physical assumptions, boundary-condition meaning, convergence criteria, or scientific claim scope.
3. If an unresolved scientific/modeling choice blocks execution, stop and report it instead of choosing implicitly.
4. Run only the validations requested by the task, plus cheap checks that are necessary to avoid reporting obviously broken code.
5. Do not launch an expensive GPU simulation unless the task explicitly authorizes it.
6. Before acceptance-style validation, stop editing the candidate source.
7. Do not merge to `master`.
8. Do not force-push or rewrite shared history.
9. Do not modify files outside this repository unless explicitly authorized.
10. If a shared/copy-paired LBM file is changed, report that synchronization with the separate LBM tree may be required.

At the end, write:

`.agent_runtime/execution_report.md`

using:

`.agent/templates/EXECUTION_REPORT.md`

The execution report is your claim about what happened. Do not invent command results, exit codes, commit hashes, convergence status, or artifacts. Use `UNKNOWN`, `NOT_RUN`, or `INCONCLUSIVE` when appropriate.

Finish with one finite suggested next action.
