# A0 — Lightweight Episode Runner Bootstrap

## Objective

Create the smallest local orchestration layer required to run V0-V3 without ChatGPT participating in every executor/reviewer round.

Do not replace the existing V1 Controller. Reuse its proven subprocess/session/provenance patterns where useful, but keep this runner episode-oriented and local.

## Required capabilities

1. Read the Episode Contract and one Stage Contract.
2. Create or attach to the declared episode product branch.
3. Launch a fresh ZCode executor session for stage round 1.
4. Preserve the executor session ID for optional rework resume.
5. Require a candidate commit before review.
6. Freeze and record the candidate SHA.
7. Launch a fresh ZCode reviewer session with restricted context.
8. Validate that REVIEW.md binds to the frozen candidate SHA.
9. Interpret exactly three reviewer decisions:
   - PASS
   - CHANGES_REQUESTED
   - HUMAN_REQUIRED
10. On CHANGES_REQUESTED, pass REVIEW.md to the executor and start the next bounded attempt.
11. Enforce maximum 3 candidates per stage.
12. Auto-promote PASS from V0 to V1 to V2 to V3.
13. Stop after V3 PASS and publish CHECKPOINT_READY.
14. Stop immediately on HUMAN_REQUIRED.
15. Persist enough local state to resume after process interruption.

## Minimum local state

Suggested local runtime layout:

~~~text
.agent_runtime/episodes/BI-VALIDATION-001/
  episode_state.json
  V0/
    round-01/
      candidate.json
      execution_report.md
      review.md
      evidence/
  V1/
  V2/
  V3/
~~~

The exact filenames may change, but candidate SHA, session IDs, attempt count, decision, and artifact manifest must be machine-readable.

## Reviewer isolation test

Before scientific work, run one harmless smoke stage proving:

- executor session A writes a candidate marker;
- reviewer session B is a distinct fresh session;
- reviewer receives the candidate marker and contract;
- reviewer does not receive executor transcript;
- reviewer cannot modify product files;
- a deliberate review failure routes back to executor;
- a second candidate receives a new fresh reviewer session;
- PASS promotes cleanly.

A0 is not complete until this smoke passes.

## Writes

The runner may modify only agent infrastructure paths explicitly authorized in the bootstrap task.

Do not modify CG3D solver physics during A0.

## Review of A0

Because the autonomous reviewer loop is the thing being bootstrapped, A0 requires one external/manual review before V0 is authorized.

After A0 passes its smoke:
- push the runner branch/commit;
- publish the smoke evidence;
- stop for ChatGPT/user review.

This is the only mandatory pre-V0 human checkpoint.
