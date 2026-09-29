# SMOKE-1 Execution Report — Round 01, Attempt 1

> Executor claim, not proof. Git identity and command evidence may be captured independently by the controller/reviewer.
> This stage is a harmless orchestration rehearsal (A0 runner isolation test). It contains no scientific work.

## Stage / Attempt

- Episode: BI-VALIDATION-001 (smoke mini-episode)
- Stage: SMOKE-1 (A0 runner isolation test)
- Round / attempt: round 01, attempt 1
- Status: COMPLETED
- Stage Contract snapshot: `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-1/contract_snapshot.md`
- Snapshot sha256: `a87eba7f30c65460414f5f194f413bbe247706c405ef5b2a7a35761c3879adb6`

## Git state

- Product branch: `agent-episode/BI-VALIDATION-001-smoke-r2`
- Base SHA: `9ede55c8ef7589b61606e11c033c84d9bcd1de94`
- Candidate SHA: `c0c903cb5fbd8a8b1f5d72fb7851b391aca6700d`
- Candidate tree: `0ae12c649234c181cd3b9b8641dd1888565c7a50`
- Candidate commit subject: `smoke(SMOKE-1): add round-1 candidate marker file`
- Working tree after commit: clean (`git status --porcelain` empty)
- No merge, no push, no force-push, no history rewrite performed.

## Changed files (base → candidate)

| Status | Path | Notes |
|---|---|---|
| A | `smoke/marker.md` | New file, 12 lines. The only file in the candidate diff. |

`git diff --name-status 9ede55c8ef75 c0c903cb` reports exactly this one addition.

## Round task and hard gate

The round task was to write `smoke/marker.md` and commit it as the round candidate, and,
as documented in the Stage Contract, to **intentionally plant the round-1 defect**: a short
marker written **without** the required token line, so the reviewer can exercise the
failure path. The token was not to be added in this round.

- Required token line for the hard gate: `SMOKE-PASS-TOKEN-7f3a`
- Presence in the candidate: **ABSENT — intentional, per Stage Contract ("Planted defect (round 1 ONLY — by design)")**
- Verification command: `grep -c "SMOKE-PASS-TOKEN" smoke/marker.md` → output `0`, exit code `1` (no match), i.e. the token line is confirmed absent.

Consequently the stage's hard gate is **FAIL at this candidate by design**, and the expected
reviewer decision on this candidate is CHANGES_REQUESTED. This is not an executor error and
not a deviation from the round task; it is the documented round-1 behaviour of the stage.

## Commands run and exit codes

| # | Command | Exit code | Result |
|---|---|---|---|
| 1 | `git rev-parse --abbrev-ref HEAD` / `git rev-parse HEAD` / `git status --porcelain` | 0 | Branch `agent-episode/BI-VALIDATION-001-smoke-r2`, HEAD `9ede55c8ef75`, tree clean |
| 2 | `ls -la smoke` | 2 | `smoke/` did not exist before this round (no prior marker in the worktree) |
| 3 | `grep -c "SMOKE-PASS-TOKEN" smoke/marker.md` | 1 | `0` matches — token absent as required by the round-1 design |
| 4 | `git add smoke/marker.md && git commit -m "..."` | 0 | 1 file changed, 12 insertions |
| 5 | `git diff --name-status HEAD~1 HEAD` | 0 | `A smoke/marker.md` (single-file candidate) |
| 6 | `git status --porcelain` (post-commit) | 0 | Empty output — no residual modification in the product tree |
| 7 | `git ls-tree HEAD smoke/marker.md` | 0 | `100644 blob cdc0813ebed3b3fbe99d56bdd5a448f2eaa54ed9` |
| 8 | `git cat-file -p HEAD:smoke/marker.md \| sha256sum` | 0 | `5ca3b058134401743a46d7f7e667b1e4217d581416faefb3af879e0e724b6cb4` |

No validation beyond the marker check above was required by this Stage Contract; there are no
hard-gate commands other than the token-presence check. Nothing was reported as passed without
being run. No solver run, no test suite, and no GPU work was performed or needed.

## Artifacts

| Artifact | Path / reference | Purpose | Hash |
|---|---|---|---|
| Candidate marker | `smoke/marker.md` at commit `c0c903cb` | Round candidate under review | git blob `cdc0813ebed3b3fbe99d56bdd5a448f2eaa54ed9`; sha256 of content `5ca3b058134401743a46d7f7e667b1e4217d581416faefb3af879e0e724b6cb4` |
| Execution report | `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-1/round-01/execution_report.md` (this file) | Round record | — |
| Contract snapshot | `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-1/contract_snapshot.md` | Frozen stage contract | sha256 `a87eba7f30c65460414f5f194f413bbe247706c405ef5b2a7a35761c3879adb6` |

## Deviations

1. **Branch name differs from the Stage Contract snapshot text.** The snapshot's "Round task"
   section names the smoke branch `agent-episode/BI-VALIDATION-001-smoke-r1`, while the round
   instruction and the actual checked-out branch are `agent-episode/BI-VALIDATION-001-smoke-r2`.
   The round instruction was treated as authoritative for branch selection, and the declared
   round base (`9ede55c8ef75`) matched the actual HEAD at session start, so the candidate is
   correctly bound to the declared base. No branch was created, renamed, or checked out during
   this round; work was done only on the branch that was already checked out.
2. **`smoke/` did not exist in the working tree** before this round (`ls -la smoke` → exit code 2).
   The directory and the marker file were created as part of the round task. No pre-existing
   marker was overwritten.
3. Git emitted a benign line-ending notice on `git add` (`LF will be replaced by CRLF the next
   time Git touches it`) — informational only; the committed blob is the LF content hashed above.

No other deviations. Scope was not broadened: this round touched only `smoke/marker.md` in the
product tree.

## Scientific / modeling impact

None. This stage authorizes no solver, test, documentation, boundary-condition, wettability,
surface-tension, or convergence-rule change, and none was made. No physical assumption was
changed or challenged. No existing result, validation, or benchmark is affected.

## Unresolved issues / human decisions

- None requiring a human decision. The absent token is the documented round-1 planted defect and
  is expected to return CHANGES_REQUESTED; the correction (adding the exact token line in
  `smoke/marker.md`) stays inside the current stage scope and does not change any scientific
  assumption.

## Suggested next action

Bind a fresh reviewer session to candidate `c0c903cb5fbd8a8b1f5d72fb7851b391aca6700d` and apply
the Stage Contract's reviewer decision rule, which for this candidate yields CHANGES_REQUESTED
with the finite correction "add the exact token line"; the runner should then route round 02 back
to this executor session (unless REVIEW.md requests RESET_CONTEXT).
