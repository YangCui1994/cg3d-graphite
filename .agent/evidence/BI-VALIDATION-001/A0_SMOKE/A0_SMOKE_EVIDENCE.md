# A0 Runner-Bootstrap Evidence — BI-VALIDATION-001

Durable evidence for the A0 isolation smoke required by
`RUNNER_BOOTSTRAP.md` ("A0 is not complete until this smoke passes").
Local runtime copy (gitignored): `.agent_runtime/episodes/
BI-VALIDATION-001/SMOKE/`. Raw session stdout tails are truncated in
the committed log; full logs remain local.

## What ran

- Runner implementation (this commit):
  `.agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py`
  + `.agent/episodes/bilateral-imbibition-v0.1/runner/SMOKE_CONTRACT.md`.
- Unit validation (pre-smoke): 12/12 `parse_review` cases PASS
  (binding header, candidate SHA binding, ambiguous/unknown decision
  rejection, RESET_CONTEXT parsing).
- Isolation smoke: four sequential headless ZCode sessions in the
  dedicated worktree `../cg3d-episode-worktrees/BI-VALIDATION-001-smoke`
  (branch `agent-episode/BI-VALIDATION-001-smoke`, created by the
  runner from the declared product execution base `9ede55c8…`).

## Result: SMOKE PASS — all 8 isolation checks true

| # | Bootstrap requirement | Check key | Result |
|---|---|---|---|
| 1 | executor session A writes a candidate marker | `executor_wrote_candidate_marker` | True (C1 `bbda7ff8…`, `smoke/marker.md` committed) |
| 2 | reviewer session B is a distinct fresh session | `reviewer_distinct_fresh_session` | True (`sess_620b35a3…` ≠ executor `sess_578fa632…`, no `--resume`) |
| 3 | reviewer receives candidate marker and contract | `reviewer_received_marker_and_contract` | True (prompt carries contract path + frozen SHA + report path; verbatim prompts in the log) |
| 4 | reviewer does not receive executor transcript | `reviewer_prompt_has_no_transcript` | True (prompt contains no transcript; structural: fresh session + prompt-only inputs) |
| 5 | reviewer cannot modify product files | `reviewer_did_not_modify_product` | True (post-session `git status` clean at frozen SHA, both rounds) |
| 6 | deliberate review failure routes back to executor | `round1 decision = CHANGES_REQUESTED` → rework | True (planted defect per SMOKE_CONTRACT; E2 resumed E1) |
| 7 | second candidate receives a new fresh reviewer session | `second_candidate_new_fresh_reviewer` | True (R2 `sess_de4dc1c1…` ≠ R1 ≠ E1, no `--resume`) |
| 8 | PASS promotes cleanly | `pass_promotes_cleanly` | True (smoke → PASS; episode state → `A0_REVIEW`, V0 stays READY-locked behind the external A0 review) |

Candidates: C1 `bbda7ff8e2fc53c501760daaf2e78d24e6338974`
(marker without token — planted defect) → C2
`ad828860d5528403ae8e77217f6b108745711b22` (token added, PASS).
Session elapsed times: E1 65.6 s, R1 59.7 s, E2 68.8 s (resumed),
R2 68.8 s; all exit 0, none timed out.

## Files

| File | Content |
|---|---|
| `smoke_report.md` | runner-written PASS report with the 8 checks |
| `session_isolation_log.json` | per-session command + FULL prompt (isolation proof) + timing + exit code + stdout tail |
| `round-01-execution_report.md` / `round-02-execution_report.md` | executor reports |
| `round-01-review.md` / `round-02-review.md` | reviewer decisions (binding headers frozen to C1/C2) |

## Scope compliance

- No CG3D solver/product code touched; the smoke branch contains only
  `smoke/marker.md` (two commits).
- The control checkout working tree was not used for sessions (dedicated
  worktree; user's untracked files untouched).
- Episode state machine now at `episode_status=A0_REVIEW` — the runner
  REFUSES to start V0 until the external A0 review flips it (per
  RUNNER_BOOTSTRAP "Review of A0": stop for ChatGPT/user review).
- Smoke branch left in place (no branch deletion); it can be discarded
  by a human after review.
