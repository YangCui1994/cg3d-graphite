# A0-R1 Rework Evidence — BI-VALIDATION-001

Durable evidence for the A0 rework requested by
`A0_SMOKE/A0_EXTERNAL_REVIEW.md` (CHANGES_REQUESTED, candidate
`281f1d98…`).  Rework implementation commit: `08117fd`
("agent(A0-R1): rework runner per external review — one generic
engine").  The real-session smoke below ran on exactly that commit
(`runner_commit` recorded in every stage_record.json), through the
SAME generic engine (`start_stage` / `run_round` / `run_episode` /
`publish_round`) that V0–V3 will use.

## Finding → resolution → evidence map

| Finding | Resolution | Evidence |
|---|---|---|
| B1 rework attempt bookkeeping | `run_round` increments `attempts` on CHANGES_REQUESTED and binds rework to `round-(n-1)/review.md`; same-attempt retry after ERROR restores the recorded phase and clears stale artifacts | offline S1b/S1c; real: SMOKE-1 candidates [att-1 `6c1d5a89`, att-2 `2db5d1a1`], `next_attempt=2` in console log |
| B2 smoke ≠ production path | single generic engine for smoke AND real stages; `cmd_run_smoke` is thin glue over `run_episode(smoke_config())` | `episode_runner.py` (one `run_round`/`run_episode`); the whole A0_SMOKE_R1 tree below was produced by that engine |
| B3 validation-only stages | unchanged-source round → validation-only candidate bound to the unchanged SHA (no meaningless commit); reviewer told the candidate is intentionally diff-less | offline S1f/S1g; real: SMOKE-2 candidate `validation_only=true`, sha == SMOKE-1 att-2 sha `2db5d1a1…`, review binds that sha |
| B4 A0 approval not enforced | explicit `A0_REVIEW → approve-a0 → A0_APPROVED → RUNNING`; `approve-a0` requires a PASS review bound to the runner commit; all real-execution commands gated | offline S2a–S2e; real: `start-stage V0` refused while A0_REVIEW (message in `smoke_r1_console` capture; reproduced after completion) |
| B5 session failure handling | every session validated (exit 0, no timeout, non-null session id, artifact freshly written — pre-checked absent); dirty pre-review worktree or reviewer failure → ERROR without advancing; stale files never parsed | offline S3–S8 (exit≠0 / timeout / missing report / stale artifact / dirty worktree / reviewer failure) |
| B6 role contracts not delivered | executor/reviewer prompts carry absolute control-plane paths: AGENTS.md, EPISODE_PLAN.md, EXECUTOR_CONTRACT / REVIEWER_CONTRACT, Stage Contract (+ sha256) | offline S1k; verbatim prompts in each `round-*/session_log.jsonl` below |
| B7 not autonomous | `run-episode` auto-starts READY stages, auto-promotes PASS, bounded rework, stops on HUMAN_REQUIRED / ERROR / terminal CHECKPOINT_READY; crash-resumable state | offline S1h/S9/S10; real: SMOKE-1 PASS auto-promoted to SMOKE-2 with no `start-stage` call (console log `promote stage=SMOKE-1 next_stage=SMOKE-2`) |
| B8 no durable publication | `publish_round` per finished round: contract snapshot + sha256, execution report, review, session log, diff stat (code candidates), stage_record.json; auto-commit + push of the control branch | the three auto-commits `65e79de`, `6d6a7d7`, `3b0c72e` on `agent-dev/bilateral-episode-v0.1` (pushed); tree below |
| H1 worktree trust | `make_worktree` identity checks: branch, cleanliness, expected head; ambiguous reuse refused | `episode_runner.py::make_worktree`; offline harness path |
| H2 over-strong reviewer claim | claim narrowed everywhere to "persistent reviewer product modifications are detected and rejected" (post-session HEAD + git-status check); no stronger sandbox claimed | `SMOKE_CONTRACT.md` / `SMOKE_VALIDATION_CONTRACT.md` wording; `product_at()` after every reviewer session (all rounds ran clean) |
| H3 contract provenance | stage contract frozen at stage start: sha256 in state, quoted in executor AND reviewer prompts, snapshot copied to publication | offline S1j; real: `contract_snapshot.md` + `contract_sha256` in both stage_record.json files (a87eba7f… / 81c50c7b…) |

## Offline generic-engine test suite (deterministic, stubbed sessions)

`python tests/test_episode_runner_generic.py` → **36/36 PASS, exit 0**
(log: `tests_output/episode_runner_generic_test.log`, gitignored).
Covers every item of the review's "Required A0 rework acceptance" list
including the failure modes that cannot be produced deterministically
with live sessions (timeouts, missing artifacts, stale files, dirty
worktree, max-attempts, HUMAN_REQUIRED).

## Real-session smoke through the generic engine (6 headless sessions)

Console log: `.agent_runtime/episodes/BI-VALIDATION-001/smoke_r1_console.log`
(gitignored).  Session/elapsed data lives in the stage records below.

| Stage | Rounds | Sessions | Outcome |
|---|---|---|---|
| SMOKE-1 (marker, planted defect) | att-1 `6c1d5a89…` → CHANGES_REQUESTED; att-2 `2db5d1a1…` → PASS | E1 `sess_878cbeba…` fresh; R1 `sess_25af8f0c…` fresh; E2 = E1 resumed (`--resume`); R2 `sess_9a45baab…` NEW fresh | PASS, auto-promoted |
| SMOKE-2 (validation-only, terminal) | att-1 candidate = unchanged `2db5d1a1…` (validation_only=true) | E3 `sess_ece47a11…` fresh; R3 `sess_7dfcb8e7…` fresh | PASS → episode CHECKPOINT_READY |

All sessions exit 0, none timed out; every round validated the
executor/reviewer artifacts as freshly written; product tree verified
clean at the frozen SHA after every reviewer session.

## Files (this directory, committed)

- `SMOKE-1/`, `SMOKE-2/` — per-stage `contract_snapshot.md`,
  `stage_record.json` (candidates/decisions/session provenance/
  contract sha256/runner commit) and per-round
  `execution_report.md`, `review.md`, `session_log.jsonl`
  (verbatim prompts), `diff_stat.txt` (code candidates only).
- `A0_R1_EVIDENCE.md` — this index.

## State after A0-R1

Main episode state: `episode_status=A0_REVIEW` (smoke PASS recorded,
`runner_commit=08117fd…`).  The runner refuses any real execution
until `approve-a0` is fed a PASS external review bound to that commit.
V0–V3 were NOT started.  Stopped again for external review, as
required.
