# A0-R2 Rework Evidence — BI-VALIDATION-001

Durable evidence for the A0 rework requested by
`../A0_SMOKE_R1/A0_EXTERNAL_REVIEW_R2.md` (CHANGES_REQUESTED, candidate
`08117fd9…`).  Rework implementation commits:

- `6e5610d` — B9–B13 + H4–H5 engine rework (runner + offline tests);
- `f6a9fe0` — follow-up fix found by the first live smoke attempt
  (`--reset` must also archive the smoke runtime directory).

The real-session smoke below ran on exactly `f6a9fe0` — the
`runner_commit` recorded in every stage_record.json in this directory —
through the SAME generic engine (`start_stage` / `run_round` /
`run_episode` / `publish_round`) that V0–V3 will use.  **The A0
approval is bound to `f6a9fe079dfa9e1ca55de9c61561227f844fba71`.**

## Finding → resolution → evidence map

| Finding | Resolution | Evidence |
|---|---|---|
| B9 product branch not durably pushed | `publish_round` now calls `push_product_branch` at EVERY publication boundary (PASS, CHANGES_REQUESTED, HUMAN_REQUIRED, crash/ERROR checkpoints): verifies the worktree is on the product branch at the exact reviewed SHA, normal non-force push, `ls-remote` confirmation, result recorded in `stage_record.json`; validation-only rounds push the unchanged ref so the remote ref exists; orphan rounds are evidence-only (product branch never pushed from an ambiguous tree) | offline S12a/S12b + S8b (frozen candidate published at a reviewer-failure checkpoint); real: remote branch `agent-episode/BI-VALIDATION-001-smoke-r2` at exactly `7ab0094b…` (`git ls-remote`), `product_push` (branch/remote_ref/pushed_sha/verified_at) in both stage records below |
| B10 contract hashed but not frozen | `start_stage` copies the contract into an immutable runtime snapshot (`…/smoke/<STAGE>/contract_snapshot.md`) and records its sha256; executor AND reviewer prompts point at the snapshot; `_verify_contract` re-checks the hash before every session and at publication; publication copies the frozen bytes; live control-plane drift is recorded (`contract_drift`) but never followed | offline S13a (live contract mutated after freeze → run inert, frozen bytes published, drift recorded) and S13b (snapshot tampered → runner refuses before any session); real: both stage records carry `contract_snapshot` + `contract_sha256` (`a87eba7f…`/`81c50c7b…`), snapshots committed alongside |
| B11 approval without candidate binding | `approve_a0_from_text` requires a full 40-hex `candidate:` binding exactly equal to the smoke `runner_commit` in state; missing binding, short binding, wrong binding, or missing state runner_commit are all rejected without flipping status | offline S14 (4 rejection cases) + S2b–S2d; real: `approve-a0` with the R2 review refused (non-PASS decision), and a PASS text bound to the previous runner `08117fd9…` refused against `f6a9fe0…` — status remained `A0_REVIEW` |
| B12 failed session can advance Git history silently | the round base is pinned and persisted BEFORE each executor session; an invalid executor session that advanced HEAD or left a dirty tree is a terminal `HUMAN_REQUIRED` ORPHAN: recorded in state (`orphan`), published evidence-only, and a retry can never adopt the unreviewed commit as base (`base_guard` demands the tree be exactly back at the pinned base) | offline S15a–S15c; **real live demonstration**: the FIRST R2 smoke attempt aborted exactly this way (see `SMOKE-1-aborted-attempt-1/ABORTED.md`, evidence commit `bf6851d`) — a runner reset defect invalidated a committed executor session, and the engine refused to reuse the orphan commit, went terminal, published evidence-only, never pushed the product branch |
| B13 reviewer failure restarts the executor | round phase is explicit and persisted: `EXECUTING`/`REWORK` (executor pending) → `CANDIDATE_READY` (candidate frozen, review pending); a failed REVIEWER session with an intact candidate sets `ERROR` + `error_phase=review_pending`, and the retry (the `run` command, or crash-resume of a persisted `CANDIDATE_READY`) launches ONLY a fresh reviewer against the SAME frozen candidate/report; a non-intact candidate or a persistent reviewer modification of the product tree stops `HUMAN_REQUIRED` | offline S16a/S16b (no additional executor call, identical candidate sha, fresh reviewer, PASS) and S8b; `episode_runner.py::run_round` review-pending branch |
| H4 expected-HEAD check not used at attach | `run-smoke` attaches the smoke worktree with `expected_head = declared base`; `init-product` derives the expected HEAD from persisted state (`_expected_product_head`: base advanced by every started stage's latest candidate); a branch-correct, clean, but state-inconsistent worktree is refused with an explicit recovery hint | offline S17a–S17d; real: fresh `smoke-r2` worktree created at declared base `9ede55c…` |
| H5 persisted ERROR can spin `run-episode` | `run_episode` treats a persisted ERROR stage as an explicit terminal return (deterministic stop, no busy loop); the documented same-attempt recovery is the `run` command | offline S18 (second invocation returns ERROR immediately, zero extra sessions) |

## Offline generic-engine test suite (deterministic, stubbed sessions)

`python tests/test_episode_runner_generic.py` → **56/56 PASS, exit 0**
(36 carried over from R1 + 20 new checks; S12–S18 cover every new
failure/recovery case from the R2 review, S3/S4/S6 were tightened to
fail cleanly so the orphan path is tested separately in S15).

## Real-session smoke through the generic engine (6 headless sessions)

Console log: `.agent_runtime/smoke_r2_run2.log` (gitignored); verbatim
prompts in each `round-*/session_log.jsonl` (committed).  Total wall
time ≈ 9 min.

| Stage | Rounds | Sessions | Outcome |
|---|---|---|---|
| SMOKE-1 (marker, planted defect) | att-1 `c0c903cb…` → CHANGES_REQUESTED; att-2 `7ab0094b…` → PASS | E1 `sess_00db1a26…` fresh (45 s); R1 `sess_8d341a0e…` fresh (107 s); E2 = E1 resumed (75 s); R2 `sess_2fb32a94…` NEW fresh (112 s) | PASS, auto-promoted |
| SMOKE-2 (validation-only, terminal) | att-1 candidate = unchanged `7ab0094b…` (validation_only=true) | E3 `sess_53575433…` fresh (59 s); R3 `sess_35c82201…` fresh (134 s) | PASS → episode CHECKPOINT_READY |

All sessions exit 0, none timed out; every round validated the
executor/reviewer artifacts as freshly written; the product tree was
verified clean at the frozen SHA after every reviewer session; the
product branch was pushed and remote-verified at every publication
(`verified_at` timestamps in the stage records).

Control-branch evidence commits (auto-published by the engine, pushed):
`670cba4` (SMOKE-1 att-1, CHANGES_REQUESTED), `a957b79` (SMOKE-1 att-2,
PASS), `3867846` (SMOKE-2, PASS).  The aborted first attempt's
evidence-only orphan record is `bf6851d`.

## Files (this directory, committed)

- `SMOKE-1/`, `SMOKE-2/` — per-stage frozen `contract_snapshot.md`,
  `stage_record.json` (candidates/decisions/session provenance/contract
  sha256 + snapshot path/runner commit/product push) and per-round
  `execution_report.md`, `review.md`, `session_log.jsonl` (verbatim
  prompts), `diff_stat.txt` (code candidates only).
- `SMOKE-1-aborted-attempt-1/` — preserved engine record of the first
  R2 attempt that terminated as a B12 orphan (see `ABORTED.md`).
- `A0_R2_EVIDENCE.md` — this index.

## State after A0-R2

- `episode_status = A0_REVIEW`; V0–V3 remain LOCKED/READY-but-gated and
  **unstarted** (live demo: `start-stage V0` refused while A0_REVIEW).
- Approval path: an external PASS review whose `candidate:` binding is
  exactly `f6a9fe079dfa9e1ca55de9c61561227f844fba71`, then
  `episode_runner.py approve-a0 --review <path>` → `run-episode`.
- Deferred human decisions (unchanged): disposal of smoke
  worktrees/branches (`BI-VALIDATION-001-smoke{,-r1,-r2}`; r2 is pushed
  and holds the smoke provenance chain).
