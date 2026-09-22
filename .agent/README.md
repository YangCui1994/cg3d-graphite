# Agent Interaction Protocol — Step 0 + V1 Controller

This directory defines the **minimal repo-native interaction protocol** for coding agents working on `cg3d-graphite`.

Step 0 intentionally did **not** implement the final JSON contracts, state
machine, controller, or automatic reviewer routing. V1 now adds only the
smallest executable infrastructure needed to move the existing Markdown
contracts through GitHub and a Windows Z Code executor.

Its purpose is to make today's manual workflow compatible with the future architecture.

## Current workflow

```text
Task
  ↓
Executor (Z Code / Codex / other)
  ↓
Execution Report + deterministic evidence
  ↓
Reviewer (Chat / Codex / other)
  ↓
PASS / CHANGES_REQUESTED / HUMAN_REQUIRED
```

The same protocol can later be driven by a Python controller without changing the project-level behavior rules.

## Files

- `../AGENTS.md` — project-level behavioral constraints.
- `templates/TASK.md` — task handoff template.
- `templates/EXECUTION_REPORT.md` — executor output template.
- `templates/REVIEW.md` — reviewer output template.
- `templates/HANDOFF.md` — compact cross-session handoff template.

## Runtime files

Temporary runtime material should go under:

```text
.agent_runtime/
```

This directory is ignored by Git.

Suggested layout:

```text
.agent_runtime/
  TASK.md
  execution_report.md
  review.md
  runs/
```

The controller still uses `.agent_runtime/` only as ignored worktree scratch.
Durable task, report, and evidence files are stored under `.agent/tasks/` on
the control branch.

## Z Code Step-0 invocation

A headless Z Code executor can be invoked conceptually as:

```powershell
node "C:\Program Files\ZCode\resources\glm\zcode.cjs" `
  --cwd <task-worktree> `
  --mode yolo `
  --json `
  -p "Read AGENTS.md and .agent_runtime/TASK.md. Execute only that task. Run only the requested validations. Write .agent_runtime/execution_report.md using .agent/templates/EXECUTION_REPORT.md. Do not merge to master."
```

The external runner/reviewer should independently capture observable facts such as:

- Git diff;
- changed files;
- commit SHA if one exists;
- validation exit codes;
- stdout/stderr;
- artifact locations.

Do not treat the agent's own execution report as proof that those events occurred.

## Design boundary

Step 0 deliberately avoids:

- final JSON Schema design;
- automatic merge;
- automatic repeated rework;
- multi-executor scheduling;
- an LLM manager;
- MCP-based orchestration;
- a general-purpose evidence graph.

Those can be added after several real tasks reveal what information is actually needed.

## V1 state protocol

The only machine state is `.agent/state.json`. It deliberately does not encode
requirements, validation meaning, PASS, or closure semantics. Those remain in
the Markdown task and review records.

Required fields:

| Field | Meaning |
|---|---|
| `schema_version` | `v1-alpha` |
| `task_id` | Parent task identity; safe path/ref characters only |
| `round` | Current execution round; Round 1 starts at `1` |
| `max_rounds` | Parent-task cap; V1 rejects values above `3` |
| `revision` | Monotonic state-update counter |
| `status` | One of the states below |
| `zcode_session_id` | Saved after Round 1 and reused with `--resume` |
| `candidate_commit` | Latest task-branch candidate, if available |
| `worker` | Claiming controller while `RUNNING`, otherwise `null` |
| `updated_at` | UTC timestamp of the last transition |
| `last_error` | Short controller error, otherwise `null` |

State flow:

```text
DRAFT
  -> READY_FOR_EXECUTION       planner/reviewer commits a finite round
  -> RUNNING                   controller claims with a Git push
  -> AWAITING_REVIEW           process/evidence/candidate were published
     -> READY_FOR_EXECUTION    reviewer starts the next round
     -> CLOSED                 reviewer closes the parent task
     -> HUMAN_REQUIRED

RUNNING -> ERROR               executor/controller failure was published
READY round > max_rounds -> STOPPED_MAX_ROUNDS
```

`PASS` belongs in `REVIEW.md` and means only that the current round's stated
requirements are satisfied. It does not close the parent task automatically.
Fresh-session review and merge remain manual.

Every active round uses this derived layout:

```text
.agent/tasks/<task_id>/round-<NN>/
  TASK.md
  EXECUTION_REPORT.md
  REVIEW.md                    # written later by the reviewer
  evidence/
    controller/                # independently observed Git/process evidence
      process.json
      zcode.stdout.json
      zcode.stderr.txt
      git-before.txt
      git-status.txt
      changed-files.txt
      git-diff-stat.txt
      git-diff.patch
      candidate-show.txt
      candidate-commit.txt
    executor/                  # optional executor-published evidence
      manifest.json
      provenance.json
      <manifest-listed files>
```

An executor may request durable publication of additional reviewer evidence by
placing a `manifest.json` and its listed files under
`.agent_runtime/published_evidence/`. The Controller validates this bundle,
copies the original manifest and files, and generates `provenance.json` bound
to the candidate commit and Z Code session. It does not interpret whether the
evidence proves PASS or FAIL.

V1 accepts at most 20 files, 1 MiB per file, and 5 MiB total (including the
manifest). Allowed extensions are `.txt`, `.log`, `.json`, `.csv`, `.md`,
`.patch`, and `.diff`. Invalid paths, symlinks, unlisted/missing files, and
limit violations put the round in `ERROR`; a candidate already committed and
pushed remains recorded in state.

## Windows Controller

The controller is the only watcher. Z Code does not monitor GitHub. It polls
the Git remote with `git fetch`, claims a READY round by committing/pushing
`RUNNING`, and only then invokes Z Code.

Prerequisites on Windows:

- Python 3.10 or newer;
- Git with push access to this repository;
- Node.js;
- Z Code installed and logged in;
- a dedicated clean clone with `agent-dev/step0-protocol` checked out.

Initial setup in PowerShell:

```powershell
git clone --branch agent-dev/step0-protocol `
  https://github.com/YangCui1994/cg3d-graphite.git `
  C:\dev\cg3d-graphite-controller
cd C:\dev\cg3d-graphite-controller

Copy-Item .agent\controller\config.example.json `
  .agent\controller\config.json
notepad .agent\controller\config.json
```

Normally only `worktree_root`, `worker_id`, and the Z Code script path need to
be checked. Use forward slashes in JSON paths. `config.json` is ignored so
machine-local paths are not committed.

Smoke one poll and exit:

```powershell
python .agent\controller\controller.py `
  --config .agent\controller\config.json `
  --once
```

Run the watcher in the foreground:

```powershell
python .agent\controller\controller.py `
  --config .agent\controller\config.json
```

Stop it with `Ctrl+C`. A Scheduled Task/service wrapper is intentionally not
part of V1.

### Operational boundaries

- Setting state to `READY_FOR_EXECUTION` authorizes controller commits and
  pushes only to the configured control branch and derived task branch.
- `TASK.md` must list machine-checkable backtick paths under `### Allowed`.
  The controller refuses to commit a candidate containing other paths. A
  listed directory covers its descendants; simple `*`, `?`, and `[]` glob
  patterns are also accepted.
- The controller never merges, force-pushes, deletes a branch/worktree, or
  decides PASS.
- A push rejection or dirty controller/task worktree stops the operation
  instead of overwriting concurrent/user work.
- A crash after claim can leave state at `RUNNING`; V1 requires manual
  inspection and recovery rather than guessing that a run is stale.
- Executor timeout, non-zero exit, missing JSON envelope, or missing execution
  report/session ID is published as `ERROR` with available evidence.
- Invalid executor evidence publication is also `ERROR`; the Controller never
  silently truncates or skips requested evidence.
- A later round must retain both the reviewed `candidate_commit` and
  `zcode_session_id`; the controller verifies the remote task branch before
  using `--resume`.

The two-round harmless test fixture is documented in
`.agent/examples/dummy/README.md`.
