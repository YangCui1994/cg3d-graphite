# A0-R3 Rework Evidence — BI-VALIDATION-001

Durable evidence for the focused A0 rework requested by
`../A0_SMOKE_R2/A0_EXTERNAL_REVIEW_R3.md` (CHANGES_REQUESTED, candidate
`f6a9fe0…`, findings B14–B16 only).  Rework implementation commit:
`83577f0` ("agent(A0-R3): rework runner per external review R3 —
B14/B15/B16 only").  The real-session smoke below ran on exactly that
commit (`runner_commit` in every stage_record.json in this directory).
**The A0 approval is bound to `83577f0d670958c7550227d6a0682ccce80a9852`.**

## Finding → resolution → evidence map

| Finding | Resolution | Evidence |
|---|---|---|
| B14 publication failure after PASS/promotion already persisted | two-phase promotion: a decided round persists `PUBLISH_PENDING` (decision in `st['pending']`) FIRST, publishes product + evidence, and applies PASS/promotion/rework/HUMAN only after publication succeeded (`_finish_round`); a publication failure leaves `ERROR` + `error_phase=publish_pending` with the next stage never exposed (`READY`/`current_stage` untouched, decision not appended); recovery — the `run` command or a crash-resume of `PUBLISH_PENDING` — re-validates the frozen review/candidate binding, re-publishes, and NEVER reruns an executor/reviewer session for a decided round; an ambiguous pending (missing/altered review) stops HUMAN_REQUIRED | offline S19a (product-push failure after PASS: no promotion, decision not applied, SMOKE-2 stays LOCKED), S19b (persisted restart stops deterministically, zero new sessions), S19c (retry re-publishes without sessions, then applies PASS + promotion), S19d (control-side publication failure, same guarantees), S19e (terminal-stage failure: episode NOT CHECKPOINT_READY); real: every round below went decision → publish → apply (stage records carry `pending` at publication; `decisions` lists APPLIED decisions) |
| B15 valid executor + dirty worktree can become an unreviewed retry base | the dirty check now runs BEFORE candidate freeze: a VALID executor session that leaves a dirty tree (with or without a commit) is the same terminal treatment as B12 — `HUMAN_REQUIRED` orphan (`kind=dirty-worktree-before-review`, head recorded), evidence-only publication (the unreviewed product state is never pushed), retry refused; the unambiguous head==base clean case (`no-candidate-where-commit-required`) remains a retryable ERROR | offline S20a (terminal orphan, no candidate frozen), S20b (evidence-only, `prod_pushes == []`), S20c (retry refused — the commit/dirty tree can never become the next base) |
| B16 A0 approves one runner implementation but the real episode does not enforce it | `approve-a0` freezes the APPROVED implementation: the git blob identity of `episode_runner.py` at the reviewed runner commit (`rev-parse <commit>:<path>`, EOL-safe; `hash-object` of the executing file for comparison — a CRLF checkout still matches its LF blob), stored as `state['approved_runner']` with provenance; every real entry point — `init-product`, `start-stage`, `run`, `run-episode` (including plain continuation and crash-restart, via both the command layer `_require_real_ready` and the engine loop) — verifies the EXECUTING runner is identical and refuses otherwise ("a changed runner requires a new A0 smoke + external review"); every real stage record carries `approved_runner`; evidence-only commits after approval are fine (only the runner FILE content matters) | offline S21a (approve freezes identity), S21b (unchanged runner → real loop allowed; record carries the identity), S21c (changed runner → refused); real live demo: approval bound to `83577f0…` froze blob `fae7912b69cf…` resolved from the COMMIT (`runner_blob_source=commit`), the executing file verified ALLOWED, a tampered identity REFUSED; the demo used an in-memory state copy, the persisted state remains `A0_REVIEW` |

## Offline generic-engine test suite

`python tests/test_episode_runner_generic.py` → **66/66 PASS, exit 0**
(56 carried over from R2 + 10 new: S19a–e, S20a–c, S21a–c; the old S7
dirty-worktree ERROR expectation was superseded by S20's terminal
semantics and replaced with a no-session-id clean-failure case).

## Real-session smoke through the generic engine (6 headless sessions)

Console log: `.agent_runtime/smoke_r3_run.log` (gitignored); verbatim
prompts in each `round-*/session_log.jsonl` (committed).  Total wall
time ≈ 8 min.  All sessions exit 0, none timed out; every round
published product + evidence BEFORE its decision was applied (B14).

| Stage | Rounds | Sessions | Outcome |
|---|---|---|---|
| SMOKE-1 (marker, planted defect) | att-1 `0e176e5d…` → CHANGES_REQUESTED; att-2 `aed0fdee…` → PASS | E1 `sess_8722d319…` fresh (47 s); R1 `sess_ad1a368b…` fresh (102 s); E2 = E1 resumed (58 s); R2 `sess_b707eac1…` NEW fresh (100 s) | PASS, auto-promoted |
| SMOKE-2 (validation-only, terminal) | att-1 candidate = unchanged `aed0fdee…` (validation_only=true) | E3 `sess_531f708f…` fresh (47 s); R3 `sess_d6327b69…` fresh (103 s) | PASS → episode CHECKPOINT_READY |

Control-branch evidence commits (auto-published by the engine, pushed):
`da57ffd` (SMOKE-1 att-1, CHANGES_REQUESTED), `d34bd24` (SMOKE-1 att-2,
PASS), `aabe7d7` (SMOKE-2, PASS).  Product branch
`agent-episode/BI-VALIDATION-001-smoke-r3` pushed and remote-verified
at exactly `aed0fdee…` (`git ls-remote`), with `product_push` recorded
in both stage records.

## Note on `decisions` vs `pending` in stage_record.json (B14 semantics)

At publication time `decisions` lists the decisions whose publication
ALREADY succeeded (applied decisions); the decision being published in
that very call is in `pending` (and, binding-wise, in the copied
`round-NN/review.md`).  This lag is the direct, honest consequence of
publish-before-apply.

## Files (this directory, committed)

- `SMOKE-1/`, `SMOKE-2/` — per-stage frozen `contract_snapshot.md`,
  `stage_record.json` (candidates/applied decisions/session provenance/
  contract sha256 + snapshot/runner commit/product push/pending/
  approved_runner) and per-round `execution_report.md`, `review.md`,
  `session_log.jsonl` (verbatim prompts), `diff_stat.txt`.
- `A0_R3_EVIDENCE.md` — this index.

## State after A0-R3

- `episode_status = A0_REVIEW`; V0–V3 remain LOCKED/READY-but-gated
  and **unstarted** (live demo: `start-stage V0` refused while
  A0_REVIEW; a PASS bound to the previous runner `f6a9fe0…` refused
  against the new smoke runner `83577f0…`).
- Approval path: an external PASS review whose `candidate:` binding is
  exactly `83577f0d670958c7550227d6a0682ccce80a9852`, then
  `episode_runner.py approve-a0 --review <path>` (freezes the approved
  runner blob `fae7912b…`) → `run-episode`.
- Deferred human decisions (unchanged): disposal of smoke
  worktrees/branches (`smoke`, `smoke-r1`, `smoke-r2`, `smoke-r3`;
  r2/r3 are pushed and hold the smoke provenance chains).
