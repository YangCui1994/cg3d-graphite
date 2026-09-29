# TASK

## ID

`<TASK-ID>`

## Execution Base

`<full 40-character lowercase commit SHA of the accepted cumulative product commit>`

Round 1 starts exactly from this revision. Later rounds continue from the
reviewed candidate, so this field stays unchanged for the lifetime of the parent
task. The value must also be present as `execution_base_commit` in
`.agent/state.json`; that state field, not this section, is what the Controller
enforces.

## Objective

Describe one finite outcome.

## Scope

### Allowed

- `path/or/module`

### Do not modify

- unrelated code
- scientific assumptions not explicitly authorized below

## Requirements

1. ...
2. ...

## Constraints

- Preserve ...
- Do not change ...

## Scientific / Modeling Assumptions

List only assumptions relevant to this task.

- **Accepted:** ...
- **Unresolved:** ...

If an unresolved assumption blocks implementation or interpretation, stop and request a decision rather than choosing silently.

## Validation Requested

List deterministic checks to run.

```text
<command>
```

For expensive GPU runs, state explicitly whether they are authorized.

## Evidence Requested

Examples:

- diff / changed files;
- test output;
- numerical metrics;
- artifact paths;
- convergence status.

## Git Policy

Choose or state explicitly:

- no commit / local changes only;
- commit allowed;
- push allowed;
- PR allowed.

Default if omitted: **do not merge to master**.

## Human Decisions Reserved

List decisions the executor must not make.

## Notes / References

Relevant docs, issue links, commits, figures, or prior decisions.
