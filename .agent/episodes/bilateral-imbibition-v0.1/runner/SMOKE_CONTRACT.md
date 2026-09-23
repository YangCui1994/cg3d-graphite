# SMOKE Stage Contract — A0 Runner Isolation Test (BI-VALIDATION-001)

This is a HARMLESS infrastructure stage. It contains no scientific
work and authorizes no changes to solver, tests, or documentation of
the CG3D product. Its only purpose is to prove the runner's role
isolation, candidate binding, and rework loop before V0.

## Round task (both rounds)

The candidate is the file `smoke/marker.md` on the smoke branch
`agent-episode/BI-VALIDATION-001-smoke`.

## Acceptance rule (hard gate)

`smoke/marker.md` must contain the single required line

```
SMOKE-PASS-TOKEN-7f3a
```

plus a short free-text description. Anything else in the file is
acceptable as long as that exact token line is present.

## Planted defect (round 1 ONLY — by design)

Round 1 deliberately writes the marker WITHOUT the required token.
This defect is intentional and documented here so that:

- the fresh reviewer is expected to return CHANGES_REQUESTED;
- the runner routes the review back to the executor;
- the executor (resumed session) produces a corrected second candidate;
- a NEW fresh reviewer session passes the second candidate.

## Reviewer decision rule

- If `smoke/marker.md` at the frozen candidate commit lacks the token
  line: **CHANGES_REQUESTED** (required correction: add the exact token
  line; validation to rerun: none beyond checking the file at the new
  candidate commit).
- If the token line is present and the candidate is otherwise a clean
  single-file marker commit: **PASS**.
- If the product tree does not match the frozen candidate SHA or the
  candidate touches files outside `smoke/marker.md` and the runtime
  report path: **HUMAN_REQUIRED**.

## Write restrictions

Executor: may write only `smoke/marker.md` (committed) and its runtime
execution report (outside the product tree). Reviewer: may write only
the review file and reviewer evidence under its runtime directory; no
product files, no commits, no branches.
