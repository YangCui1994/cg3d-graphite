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

## Optional durable executor evidence

Only when a reviewer needs to inspect additional validation logs, comparisons,
metrics, or small text artifacts from GitHub, place them under:

`.agent_runtime/published_evidence/`

That directory must contain `manifest.json` with schema version `v1`. Every
file in the directory other than the manifest must be listed exactly once.
Each entry requires non-empty `path`, `kind`, and `description` strings;
`command` is optional. Example:

```json
{
  "schema_version": "v1",
  "files": [
    {
      "path": "level_a.log",
      "kind": "validation_log",
      "description": "CPU Level A regression",
      "command": "LBM_ARCH=cpu python tests/run_level_a.py"
    }
  ]
}
```

Limits: at most 20 files, at most 1 MiB per file, and at most 5 MiB total.
Allowed extensions are `.txt`, `.log`, `.json`, `.csv`, `.md`, `.patch`, and
`.diff`. Use relative paths only. Do not use symlinks. Do not place large
simulation outputs, binary arrays, figures, or checkpoints in this directory.
The Controller validates and hashes the bundle and creates `provenance.json`;
do not create that file yourself.

If no extra evidence needs durable reviewer inspection, do not create
`published_evidence/`. In all cases, summarize decisive validation results in
`.agent_runtime/execution_report.md`; published files supplement that report.

Finish with one finite suggested next action.
