# Agent Interaction Protocol — Step 0

This directory defines the **minimal repo-native interaction protocol** for coding agents working on `cg3d-graphite`.

Step 0 intentionally does **not** implement the final JSON contracts, state machine, controller, or automatic reviewer routing.

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

These names are conventions only in Step 0. A later controller may replace them with validated JSON records.

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
