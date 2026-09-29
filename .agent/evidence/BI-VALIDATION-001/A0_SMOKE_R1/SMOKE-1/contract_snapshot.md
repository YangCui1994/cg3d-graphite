# SMOKE-1 Stage Contract — A0 Runner Isolation Test (BI-VALIDATION-001)

Harmless infrastructure stage of the smoke mini-episode. It contains no
scientific work and authorizes no changes to solver, tests, or product
documentation. Its purpose is to exercise the SAME generic orchestration
path (`run_round` / `run_episode`) that V0–V3 will use, with real
headless sessions.

## Round task (both rounds)

The candidate is the file `smoke/marker.md` on the smoke branch
`agent-episode/BI-VALIDATION-001-smoke-r1`. Each round MUST end with a
commit of this file (a validation-only outcome is not acceptable for
this stage).

## Acceptance rule (hard gate)

`smoke/marker.md` at the frozen candidate commit must contain the
single required line

```
SMOKE-PASS-TOKEN-7f3a
```

plus a short free-text description. Anything else in the file is
acceptable as long as that exact token line is present.

## Planted defect (round 1 ONLY — by design)

Round 1 deliberately writes the marker WITHOUT the required token.
This defect is intentional and documented here so that:

- the fresh reviewer is expected to return CHANGES_REQUESTED;
- the runner routes the review back to the executor (a NEW attempt
  number bound to the immediately preceding review);
- the executor (resumed session unless RESET_CONTEXT) produces a
  corrected second candidate;
- a NEW fresh reviewer session passes the second candidate;
- PASS auto-promotes to the next smoke stage without any manual
  `start-stage` invocation.

## Reviewer decision rule

- `smoke/marker.md` at the frozen candidate commit lacks the token
  line: **CHANGES_REQUESTED** (required correction: add the exact token
  line; validation to rerun: checking the file at the new candidate
  commit only).
- Token line present and the candidate is otherwise a clean single-file
  marker commit: **PASS**.
- The product tree does not match the frozen candidate SHA, or the
  candidate touches files beyond `smoke/marker.md`: **HUMAN_REQUIRED**.

## Write restrictions and their exact strength (v0.1)

Executor: may write only `smoke/marker.md` (committed) and its runtime
execution report (outside the product tree). Reviewer: may write only
the review file and reviewer evidence under its runtime directory; no
product files, no commits, no branches.

The runner enforces the reviewer restriction as: **persistent reviewer
product modifications are detected and rejected** (post-session HEAD
and `git status` check at the frozen candidate). No stronger sandbox
than that is claimed or implemented in v0.1.
