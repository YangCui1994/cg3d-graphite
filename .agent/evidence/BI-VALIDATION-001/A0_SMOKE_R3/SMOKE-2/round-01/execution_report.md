# Execution Report — SMOKE-2, Round 1 (attempt 1)

**Episode:** BI-VALIDATION-001 (SMOKE mini-episode, infrastructure rehearsal)
**Stage:** SMOKE-2 — validation-only round
**Attempt:** 1
**Role:** ZCode Executor
**Date:** 2026-09-23

## Round classification

**This round is validation-only. No commit was made and no product file was modified.**

The candidate for review is the **unchanged current HEAD commit**
`aed0fdeeb00563a49c036b286a27f28a48c721d9`, which is also the declared round base
(`aed0fdeeb005`). Because validation-only means the source state does not advance, the base
SHA and the candidate SHA are the same commit; this report is bound to that single SHA.

The only file this round wrote is this execution report, which lives on the control/evidence
plane at `cg3d-graphite/.agent_runtime/...`, outside the product worktree. It is not part of
the product diff.

## Binding

| Item | Value |
| --- | --- |
| Product branch | `agent-episode/BI-VALIDATION-001-smoke-r3` |
| Round base SHA (declared) | `aed0fdeeb005` |
| Round base SHA (resolved) | `aed0fdeeb00563a49c036b286a27f28a48c721d9` |
| Candidate SHA | validation-only, unchanged `aed0fdeeb00563a49c036b286a27f28a48c721d9` |
| Commits created this round | 0 |
| Changed files (product) | none |
| Stage contract snapshot | `SMOKE-2/contract_snapshot.md` |
| Snapshot sha256 (declared) | `81c50c7b39a10ff769c8b7fd24134c45807a4a57e6a86572eb8b4808ca5942b1` |
| Snapshot sha256 (recomputed) | `81c50c7b39a10ff769c8b7fd24134c45807a4a57e6a86572eb8b4808ca5942b1` — **matches** |

## Round task as specified

Per the SMOKE-2 Stage Contract, the executor makes no commit and no product-file
modification, performs a read-only verification that `smoke/marker.md` at the current HEAD
contains the required token `SMOKE-PASS-TOKEN-7f3a`, and writes this report.

## Commands run and results

All commands were read-only inspections. Working directory for C1–C6 and C7 was the product
worktree `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-VALIDATION-001-smoke-r3`.

| # | Command | Exit code | Purpose / observed result |
| --- | --- | --- | --- |
| C1 | `git rev-parse --abbrev-ref HEAD` | 0 | Branch is `agent-episode/BI-VALIDATION-001-smoke-r3` — correct branch, no other branch was touched. |
| C2 | `git rev-parse HEAD` | 0 | `aed0fdeeb00563a49c036b286a27f28a48c721d9`. |
| C3 | `git status --porcelain` | 0 | Empty output: working tree clean, no untracked files. No product modification. |
| C4 | `git show HEAD:smoke/marker.md` | 0 | File content retrieved from the HEAD tree (not from the worktree), so the check is bound to the commit rather than to local files. |
| C5 | `git show HEAD:smoke/marker.md \| grep -c '^SMOKE-PASS-TOKEN-7f3a$'` | 0 | **1** exact-token line. Token present. |
| C6 | `git ls-tree HEAD smoke/marker.md` | 0 | `100644 blob 91fc24e4c31f96a278f73a1382a2b5104c39e3fa smoke/marker.md` — file is tracked at HEAD, not an untracked local artifact. |
| C7 | `git rev-list --count aed0fdeeb005..HEAD` | 0 | **0** — no commits were created after the round base. |
| C8 | `git diff --stat aed0fdeeb005 HEAD` | 0 | Empty: no product diff between base and HEAD. |
| C9 | `git diff HEAD --stat` | 0 | Empty: worktree is byte-identical to HEAD. |
| C10 | `git merge-base --is-ancestor aed0fdeeb005 HEAD` | 0 | Base is an ancestor of HEAD, consistent with an unchanged HEAD. |
| C11 | `sha256sum .../SMOKE-2/contract_snapshot.md` | 0 | Hash equals the declared snapshot SHA (see Binding table). |

No GPU work was performed. No solver code was executed. No files were deleted or moved.

## Required verification result

**PASS.** The required token `SMOKE-PASS-TOKEN-7f3a` is present in `smoke/marker.md` at HEAD
`aed0fdeeb00563a49c036b286a27f28a48c721d9`, as a standalone line (C5). The file is a tracked
blob at that commit (C6), so the token is part of the committed source state and not a
worktree-only artifact.

Marker evidence for the reviewer — the token line as committed:

```
SMOKE-PASS-TOKEN-7f3a
```

## Hard gates and diagnostics

The SMOKE-2 contract defines one verification (token present at the unchanged HEAD) and one
provenance requirement (report states validation-only and names the bound SHA). Both are
satisfied.

- Token present at HEAD: **PASS** (C5, C6).
- No product commit and no product modification: **PASS** (C3, C7, C8, C9).
- Report states validation-only and names the bound SHA: **PASS** (this document).
- Numerical stability / convergence: **NOT_RUN** — not applicable to a validation-only round;
  no solver or simulation was invoked, so there is no trajectory, no termination reason, and
  no convergence claim to make. None is asserted here.

## Artifacts

| Artifact | Location | Hash |
| --- | --- | --- |
| This execution report | `cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/round-01/execution_report.md` (control plane) | see note below |
| Marker file (candidate) | `smoke/marker.md` at `aed0fdeeb00563a49c036b286a27f28a48c721d9` (product tree) | blob `91fc24e4c31f96a278f73a1382a2b5104c39e3fa` |
| Stage contract snapshot | `cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/contract_snapshot.md` | sha256 `81c50c7b39a10ff769c8b7fd24134c45807a4a57e6a86572eb8b4808ca5942b1` |

Note: this report's own hash is deliberately not self-embedded, since writing it would change
the hash it recorded. The reviewer can recompute it from the path above.

## Deviations

None from the round task.

Two points worth recording for the runner, neither a deviation from the contract:

1. The report directory `SMOKE-2/round-01/` did not exist and was created before writing this
   report. It was created on the control plane, outside the product worktree, so the product
   tree remains unmodified (C3, C9 confirm cleanliness after the write).
2. The base SHA and the candidate SHA are identical by design — that is the defining property
   of a validation-only round, not a missing commit. Readers expecting distinct base/candidate
   SHAs should treat this equality as the expected outcome here.

## Unresolved issues

None. No scientific assumption, boundary-condition meaning, or interpretation boundary was
touched; no such decision was required by this round.

## Suggested next action

Await the fresh-context reviewer for SMOKE-2. The reviewer should confirm that HEAD at review
time still equals `aed0fdeeb00563a49c036b286a27f28a48c721d9`, that the product tree is
unmodified, and that `smoke/marker.md` at that SHA contains `SMOKE-PASS-TOKEN-7f3a`. Per the
contract's decision rule, that combination is **PASS**, and because SMOKE-2 is the last stage
of the smoke mini-episode its PASS must stop the episode at CHECKPOINT_READY without further
auto-promotion, with the runner publishing the durable stage record.
