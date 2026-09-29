# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `<TASK-ID>`
- **Status:** `COMPLETED | PARTIAL | BLOCKED | FAILED`

## Summary

What was attempted and what was achieved.

## Executor Claims — Changes

- file / module:
  - change:
  - reason:

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| R1 | PASS / FAIL / PARTIAL | |

## Validation

For every requested validation:

### <validation name>

- **Command:** `<exact command>`
- **Status:** `PASS | FAIL | NOT_RUN | INCONCLUSIVE`
- **Exit code:** `<value or unknown>`
- **Key result:** ...
- **Output / artifact reference:** ...

For scientific runs, separately report:

- numerical stability;
- convergence status;
- termination reason;
- relevant physical metrics.

Do not equate process completion with convergence.

## Git / Source State

If known:

- base:
- head / commit:
- branch:
- dirty files remaining:

If not independently known, state `UNKNOWN`.

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| | | |

## Deviations

Anything performed differently from the Task.

## Assumption / Modeling Impact

Did the work change or challenge any scientific assumption, BC meaning, stopping rule, or interpretation?

If yes, describe it. Do not silently resolve it.

## Existing Evidence Potentially Affected

List previous tests/results/benchmarks that may need to be reconsidered because of this change.

## Unresolved Issues / Human Decisions

- ...

## Suggested Next Action

One finite next action only.
