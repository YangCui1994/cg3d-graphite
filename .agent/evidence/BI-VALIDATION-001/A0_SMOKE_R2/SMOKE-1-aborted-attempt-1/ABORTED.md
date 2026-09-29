# Why this record exists — aborted first R2 smoke attempt (2026-09-23)

This is the engine-published record of the FIRST R2 smoke attempt,
which aborted at SMOKE-1 attempt 1 and is preserved here unchanged as
the first LIVE demonstration of the B12 orphan protection.

## What happened

The first `run-smoke --reset` on the R2 runner archived the smoke
state but the runner did NOT yet clear the smoke runtime directory
(`.agent_runtime/episodes/BI-VALIDATION-001/smoke/`), which still held
round artifacts from the R1 smoke. The new executor session ran
correctly (exit 0, 101.5 s, committed its marker candidate
`80a8f6fb…` on top of base `9ede55c8…`), but `validate_session`
flagged the R1-leftover `execution_report.md` as a stale artifact
("pre-checked NOT to exist" defense) and declared the session invalid.

## How the engine responded (the point of keeping this record)

Exactly as specified by R2 finding B12 for a failed session whose tree
advanced:

- stage + episode went terminal `HUMAN_REQUIRED`;
- the orphan was recorded (`orphan-after-failed-executor-session`,
  base `9ede55c8ef75`, head `80a8f6fb8339`) — see `stage_record.json`;
- publication was EVIDENCE-ONLY (`product_push` skipped: the product
  branch was NOT pushed from the ambiguous tree);
- no candidate, no decision, no review was ever produced from the
  orphan commit, and the retry path refused to proceed (no silent
  reuse as a round base).

## Root cause and fix

The abort was a RUNNER defect (incomplete `--reset` semantics), not an
executor defect: stale runtime artifacts from the previous smoke made
every fresh executor session look invalid. Fixed immediately after in
`cmd_run_smoke` — a fresh smoke now archives the previous smoke
runtime directory alongside the previous smoke state (commit
"fix(A0-R2): run-smoke --reset must also archive the smoke runtime
dir"). The orphan commit `80a8f6fb…` and the disposable smoke branch
were then removed locally (never pushed anywhere).

The clean re-run that follows lives in `../SMOKE-1/`.
