# REVIEW

## Binding

- **Task ID:** `<TASK-ID>`
- **Candidate / commit:** `<SHA or diff reference>`
- **Execution report:** `<reference>`

## Review Mode

`SELF | FRESH_SESSION | DIFFERENT_MODEL | DIFFERENT_VENDOR`

## Coverage

What was actually inspected:

- task;
- diff / files;
- validation evidence;
- relevant documentation;
- artifacts.

What was not inspected:

- ...

## Requirement Review

| Requirement | Review status | Evidence / reason |
|---|---|---|
| R1 | PASS / FAIL / INSUFFICIENT_EVIDENCE | |

## Validation Review

| Validation | Review status | Notes |
|---|---|---|
| | PASS / FAIL / NOT_RUN / INCONCLUSIVE | |

## Findings

### Blocking

- ...

### Non-blocking

- ...

## Modeling / Scientific Review

Use this section only when relevant.

- Are assumptions unchanged and explicit?
- Does the numerical setup still represent the intended physical problem?
- Is convergence established, not merely process completion?
- Are scientific claims bounded by the available evidence?
- Has any previous evidence become stale?

## Missing Evidence

- ...

## Decision

Choose exactly one:

`PASS | CHANGES_REQUESTED | HUMAN_REQUIRED`

## Decision Rationale

Concise explanation tied to requirements and evidence.

## Next Action

One finite next action.

If `HUMAN_REQUIRED`, state:

- exact question;
- available options;
- evidence;
- consequences;
- what remains blocked.
