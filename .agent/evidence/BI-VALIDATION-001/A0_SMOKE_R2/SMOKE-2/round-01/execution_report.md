# SMOKE-2 Execution Report — Round 01, Attempt 1 (VALIDATION-ONLY)

> Executor claim, not proof. Git identity and command evidence may be captured independently by the controller/reviewer.
> This stage is a harmless orchestration rehearsal (validation-only path test). It contains no scientific work.

## Stage / Attempt

- Episode: BI-VALIDATION-001 (smoke mini-episode)
- Stage: SMOKE-2 (validation-only round)
- Round / attempt: round 01, attempt 1
- Status: COMPLETED — **VALIDATION-ONLY: no product change, no commit made by this round**
- Stage Contract snapshot: `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/contract_snapshot.md`
- Snapshot sha256: `81c50c7b39a10ff769c8b7fd24134c45807a4a57e6a86572eb8b4808ca5942b1` (recomputed this round; matches the declared value)

## Round task, as executed

The Stage Contract for this round requires exactly three things of the executor, all read-only:

1. make no commit and no product-file modification;
2. verify that `smoke/marker.md` at the current HEAD contains the required token `SMOKE-PASS-TOKEN-7f3a`;
3. write this execution report, stating that the round is validation-only and naming the unchanged HEAD SHA it is bound to.

All three were performed. Item 2 is **PASS** (evidence below). Items 1 and 3 are satisfied as stated.

## Git state

- Product branch: `agent-episode/BI-VALIDATION-001-smoke-r2` (unchanged; no branch created, renamed, switched, or deleted)
- Round base SHA: `7ab0094b9a5b4d5266a74fecb0a189b64f980621` (verified as this round's HEAD at session start, tree clean)
- Candidate SHA: **validation-only, unchanged `7ab0094b9a5b4d5266a74fecb0a189b64f980621`** — no commit was created by this round, so the candidate for review is the unchanged HEAD commit
- Candidate tree SHA: `56982c2a6d1392aac721828c8615e85305b7d764`
- Candidate commit subject: `smoke(SMOKE-1): add required acceptance token to marker (round 2)`
- Working tree after the round: clean (`git status --porcelain` empty) — verified again after this report was written; the report is written outside the product worktree, so it cannot appear in the product diff
- No merge, no push, no force-push, no history rewrite, no branch change performed. No `git add`, `git commit`, or any other state-changing git command was run this round.

## Changed files (base → candidate)

**None.** Base and candidate are the same commit by construction: `7ab0094b9a5b4d5266a74fecb0a189b64f980621` → `7ab0094b9a5b4d5266a74fecb0a189b64f980621`.

No file in the product tree was created, modified, staged, or deleted by this round. The only write
performed in the whole session is this report, at
`.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/round-01/execution_report.md`, which lives on the
control/evidence plane — a different directory tree from the product worktree
(`cg3d-episode-worktrees/BI-VALIDATION-001-smoke-r2`).

## Hard-gate result — required token present at the candidate

Gate (Stage Contract): `smoke/marker.md` at the current HEAD contains the required token `SMOKE-PASS-TOKEN-7f3a`.

**Result: PASS**, verified directly against the committed git object, not only against the working copy.

- `smoke/marker.md` is tracked at HEAD (`smoke/marker.md` is the only path under `smoke/` in `git ls-tree -r HEAD`).
- HEAD blob: `ed7f6217a10abdb8c964a74687b68972d78ae6f7`; content sha256 `e95dfbb6f48f8c81cb77d95ad72021977eac103894e87578aa939fea0c29d1f7`.
- Token as a whole line at the committed blob: exactly **1** match (`grep -cx "SMOKE-PASS-TOKEN-7f3a"`).
- Token as a fixed string at the committed blob: exactly **1** match (`grep -cF`).
- The working-tree file is byte-identical to the committed blob (`git diff HEAD -- smoke/marker.md` is empty; identical sha256 `e95dfbb6…`), so the verification is not an artefact of an uncommitted local edit.
- Both the committed blob and the working file are LF-only (0 CR bytes), consistent with the SMOKE-1 round-02 record.

The token appears in the file as its own line under an `## Acceptance token` heading. The exact
spelling required by the contract, `SMOKE-PASS-TOKEN-7f3a`, is the token present — no near-miss
variant appears anywhere in the file.

## Commands run and exit codes

All commands are read-only inspections. None writes to the repository or runs any solver, test, or GPU work.

| # | Command | Exit code | Result |
|---|---|---|---|
| 1 | `git rev-parse HEAD` / `git rev-parse --abbrev-ref HEAD` / `git status --porcelain` | 0 | HEAD `7ab0094b9a5b4d5266a74fecb0a189b64f980621` = declared round base; branch `agent-episode/BI-VALIDATION-001-smoke-r2`; `git status --porcelain` empty (tree clean at session start) |
| 2 | `git ls-tree -r --name-only HEAD \| grep -i "^smoke/"` | 0 | `smoke/marker.md` — the only tracked path under `smoke/` |
| 3 | `git rev-parse HEAD:smoke/marker.md` | 0 | blob `ed7f6217a10abdb8c964a74687b68972d78ae6f7` |
| 4 | `git show HEAD:smoke/marker.md` | 0 | 16-line marker file displayed; token line present |
| 5 | `git show HEAD:smoke/marker.md \| grep -c "SMOKE-PASS-TOKEN-7f3a"` | 0 | `1` — token present in the committed blob |
| 6 | `git show HEAD:smoke/marker.md \| grep -cx "SMOKE-PASS-TOKEN-7f3a"` | 0 | `1` — exactly one **whole-line** match |
| 7 | `git show HEAD:smoke/marker.md \| grep -cF "SMOKE-PASS-TOKEN-7f3a"` | 0 | `1` — one fixed-string match |
| 8 | `git diff HEAD -- smoke/marker.md \| head -20` | 0 | Empty output — working file identical to the HEAD blob |
| 9 | `git show HEAD:smoke/marker.md \| sha256sum` | 0 | `e95dfbb6f48f8c81cb77d95ad72021977eac103894e87578aa939fea0c29d1f7` |
| 10 | `sha256sum smoke/marker.md` | 0 | identical to command 9 — same content hash for blob and working file |
| 11 | `git show HEAD:smoke/marker.md \| tr -cd '\r' \| wc -c` | 0 | `0` — committed blob is LF-only |
| 12 | `tr -cd '\r' < smoke/marker.md \| wc -c` | 0 | `0` — working file is LF-only |
| 13 | `git rev-parse HEAD^{tree}` | 0 | `56982c2a6d1392aac721828c8615e85305b7d764` |
| 14 | `sha256sum .../SMOKE-2/contract_snapshot.md` | 0 | `81c50c7b39a10ff769c8b7fd24134c45807a4a57e6a86572eb8b4808ca5942b1` — matches the declared snapshot hash |
| 15 | `find .../smoke/` (runtime dirs) / `ls` (SMOKE-1 round record) | 0 | Confirmed SMOKE-2 had only the frozen contract snapshot before this round; used the SMOKE-1 round-02 report as the format reference |
| 16 | `git status --porcelain` (after this report was written) | 0 | Empty output — the product tree is still clean; this round left no product change |

No GPU, solver, or test-suite validation was required by this Stage Contract and none was run.
Nothing is reported as passed that was not actually executed.

## Reviewer decision rule, item by item

The Stage Contract's decision rule for this round, mapped to the state the reviewer will find:

- "HEAD at review time equals the frozen (unchanged) candidate SHA" — the frozen candidate SHA named
  here is `7ab0094b9a5b4d5266a74fecb0a189b64f980621`, which was HEAD at the start and end of this round.
  Confirming this at review time is the reviewer's action, not the executor's claim; the executor
  states only that it made no commit and no product modification that could move HEAD.
- "the report exists and states the validation-only result" — satisfied: this report, at
  `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/round-01/execution_report.md`, states it
  explicitly in its title, status line, and round-task section.
- "the marker at that SHA contains the token" — satisfied: hard-gate PASS above, verified against
  the committed git object.

## Artifacts

| Artifact | Path / reference | Purpose | Hash |
|---|---|---|---|
| Candidate marker (unchanged) | `smoke/marker.md` at `7ab0094b9a5b4d5266a74fecb0a189b64f980621` | Subject of the read-only verification | git blob `ed7f6217a10abdb8c964a74687b68972d78ae6f7`; content sha256 `e95dfbb6f48f8c81cb77d95ad72021977eac103894e87578aa939fea0c29d1f7` |
| Execution report | `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/round-01/execution_report.md` (this file) | Round record | — |
| Contract snapshot | `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/contract_snapshot.md` | Frozen stage contract | sha256 `81c50c7b39a10ff769c8b7fd24134c45807a4a57e6a86572eb8b4808ca5942b1` |

No new artifact was produced: this round generates no product content by design.

## Deviations

1. **No candidate commit exists for this round — deliberate, per the Stage Contract.** Episode Contract
   §4 states that every executor round must end at a git commit before review. This stage's contract
   explicitly overrides that for the validation-only path (it is the shape A0 finding B3 asked to test):
   the candidate for review is the unchanged HEAD. The executor therefore did not commit, and flags the
   tension here so the reviewer does not read the absence of a commit as an executor omission. This is
   the one place where the episode-level and stage-level contracts differ, and the stage contract governs.
2. **The marker file's own free-text metadata is stale relative to this stage.** `smoke/marker.md` is a
   SMOKE-1 artifact: its body says `Stage: SMOKE-1 (A0 runner isolation test)` and `Round: 1 of the
   stage's bounded rework cycle`. The SMOKE-2 contract requires only that the file contain the token
   `SMOKE-PASS-TOKEN-7f3a`; it does not require any metadata update, and editing the file would have
   violated this round's no-modification rule. Disclosed so the mismatch between the marker's prose and
   the current stage is not mistaken for an oversight — it has no bearing on the gate.
3. **Branch-name deviation reported in SMOKE-1 rounds does not recur here.** The SMOKE-2 contract
   snapshot does not name a branch, and the checked-out branch matches the round instruction
   (`agent-episode/BI-VALIDATION-001-smoke-r2`), so there is nothing to reconcile this round.

No other deviations. Scope was not broadened: nothing in the product tree was read-write touched, and
nothing outside this stage's declared verification was executed.

## Scientific / modeling impact

None. This round authorizes no solver, test, documentation, boundary-condition, wettability,
surface-tension, or convergence-rule change, and none was made. No physical assumption was changed or
challenged. No simulation was run and no existing result, validation, or benchmark is affected.

## Unresolved issues / human decisions

- None. The round's single requirement is a mechanical token check, it passed, and no acceptance
  threshold outside the Stage Contract was invoked. No physical BC interpretation was in play and no
  solver limitation is involved.

## Suggested next action

Bind a fresh reviewer session to candidate `7ab0094b9a5b4d5266a74fecb0a189b64f980621` and apply the
Stage Contract's decision rule to the two items the reviewer can check independently: that HEAD at
review time is still `7ab0094b9a5b4d5266a74fecb0a189b64f980621` with a clean product tree, and that
`smoke/marker.md` at that SHA contains the token `SMOKE-PASS-TOKEN-7f3a`. Per the Stage Contract's
episode terminal behaviour, a PASS here must stop the smoke mini-episode at CHECKPOINT_READY and must
not auto-promote further; the runner publishes the durable stage record.
