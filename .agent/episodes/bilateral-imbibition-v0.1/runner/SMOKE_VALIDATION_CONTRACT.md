# SMOKE-2 Stage Contract — Validation-Only Round (BI-VALIDATION-001)

Harmless infrastructure stage of the smoke mini-episode. Its purpose is
to prove the generic engine's validation-only path: a stage round whose
correct outcome is NO product change must be reviewable while bound to
the unchanged source SHA (A0 review finding B3; this is the shape V0
"prefer no product changes" is expected to take).

## Round task

The executor makes **no commit and no product-file modification**. It
performs a read-only verification that `smoke/marker.md` at the current
HEAD contains the required token `SMOKE-PASS-TOKEN-7f3a`, and writes
its execution report. The candidate for review is the UNCHANGED current
HEAD commit.

## Executor report requirement

The report must state that the round is validation-only and name the
unchanged HEAD SHA it is bound to.

## Reviewer decision rule

- HEAD at review time equals the frozen (unchanged) candidate SHA, the
  report exists and states the validation-only result, and the marker
  at that SHA contains the token: **PASS**.
- HEAD differs from the frozen SHA, the product tree was modified, or
  the executor failed to perform/report the verification:
  **CHANGES_REQUESTED**.
- Ambiguous provenance (report/SHA mismatch): **HUMAN_REQUIRED**.

## Write restrictions

Same as SMOKE-1; the reviewer restriction strength claimed in v0.1 is
"persistent product modifications are detected and rejected" (post-
session HEAD + `git status` check).

## Episode terminal behaviour

This is the LAST stage of the smoke mini-episode: its PASS must stop
the episode at CHECKPOINT_READY (never auto-promote further), and the
runner must publish the durable stage record.
