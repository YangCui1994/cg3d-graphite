# Execution Report — BI-VALIDATION-001-SMOKE / SMOKE-2 / round 1 (attempt 1)

- **Stage / attempt:** SMOKE-2 / attempt 1
- **Round type:** VALIDATION-ONLY — correctness is the *absence* of a product change; no commit was made
- **Round status:** COMPLETED (validation-only; no candidate commit created)
- **Hard-gate status:** MET (required token present in `smoke/marker.md` at the unchanged HEAD)
- **Base SHA (declared round base):** `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df`
- **Candidate SHA:** **validation-only, unchanged `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df`**
- **Branch:** `agent-episode/BI-VALIDATION-001-smoke-r1`
- **Worktree:** `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-VALIDATION-001-smoke-r1`
- **Report location note:** this report is written to the evidence plane
  (`.agent_runtime/…` inside the `cg3d-graphite` control tree), which is **outside** the product
  worktree. Writing it cannot and did not alter the frozen product SHA.

## Summary

This round is **validation-only**. The product tree was not modified and no commit was created. I
performed a read-only verification that `smoke/marker.md` at the current HEAD contains the required
token line `SMOKE-PASS-TOKEN-7f3a`, and confirmed that HEAD at the end of the round is byte-for-byte
the same commit object the round started from:

- HEAD before verification: `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df`
- HEAD after verification and after writing this report: `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df`

The declared round base is itself the HEAD commit, so the reviewed candidate is the unchanged base
rather than a newly minted commit. That is the intended outcome for SMOKE-2: the stage exists to
prove the orchestration engine can freeze, bind, and review a round whose correct result is "no
product change" (A0 review finding B3).

All three parts of the verification passed: the marker exists at HEAD, it contains the required
token exactly once as an anchored whole-line match, and the working tree is clean with no untracked
or dirty files, so the worktree state equals the frozen commit. No GPU work, no simulation, no
solver code, test, or product documentation was touched.

## Product change — none (validation-only)

| Item | Value |
|---|---|
| Changed files | **none** — `git status --porcelain --untracked-files=all` empty; `git diff HEAD --stat` empty |
| Commits created | **none** — HEAD unchanged at `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` |
| Files written | Only this report, outside the product worktree |

No `git add`, `git commit`, `git checkout`, `git reset`, or any other state-changing git command was
run in the product worktree. Every command executed there was a read-only inspection (`rev-parse`,
`status`, `diff`, `show`, `ls-tree`, `cat-file`, `log`, `config`), plus `sha256sum` / `grep` on file
content.

## Verification of the required token

The token was checked against the **commit object** (`git show HEAD:smoke/marker.md`), not merely
against the working file, so the result is bound to the frozen SHA rather than to a possibly-edited
worktree. The worktree file and the frozen blob hash identically, which closes that gap.

Recorded content of `smoke/marker.md` at `2db5d1a1`:

```
# SMOKE marker

SMOKE-PASS-TOKEN-7f3a

Round candidate marker for the BI-VALIDATION-001-SMOKE infrastructure rehearsal,
stage SMOKE-1, round 1, on branch `agent-episode/BI-VALIDATION-001-smoke-r1`.

This file exists only to give the orchestration path a real single-file commit to
freeze, review, and promote. It contains no scientific content and no
solver-relevant information, and it must not be read as a result of any kind.
```

The token occupies its own bare line (line 3), with no decoration, bullet marker, backticks, or
surrounding text, and it is an exact match under anchored whole-line matching.

## Commands run and exit codes

All commands ran in the product worktree
`D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-VALIDATION-001-smoke-r1`.

Exit-code semantics note: `grep` returns `1` when a pattern selects no lines. For the two *negative*
checks (CR scan, non-ASCII scan) exit `1` is the **desired, clean** outcome — it means nothing
undesirable was found — and is not a failed verification. Every positive token check exits `0`.

| # | Command | Exit code | Key output |
|---|---|---|---|
| 1 | `git rev-parse --abbrev-ref HEAD` | 0 | `agent-episode/BI-VALIDATION-001-smoke-r1` |
| 2 | `git rev-parse HEAD` | 0 | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` |
| 3 | `git rev-parse --short=12 HEAD` | 0 | `2db5d1a1cb2f` |
| 4 | `git log -1 --format='%H%n%an <%ae>%n%ad%n%s'` | 0 | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` / `Yang Cui` / `Wed Sep 23 16:55:41 2026 +0800` / `smoke(SMOKE-1 r2): add required token line to smoke/marker.md` |
| 5 | `git status --porcelain --untracked-files=all` | 0 | empty — no dirty, staged, or untracked product files |
| 6 | `git diff HEAD --stat` | 0 | empty — worktree identical to HEAD |
| 7 | `git cat-file -e HEAD:smoke/marker.md` | 0 | blob exists at HEAD (no error printed) |
| 8 | `git ls-tree -r --name-only HEAD smoke/` | 0 | `smoke/marker.md` — the only file under `smoke/` at HEAD |
| 9 | `git show HEAD:smoke/marker.md` | 0 | full content shown above |
| 10 | `git show HEAD:smoke/marker.md \| grep -nx 'SMOKE-PASS-TOKEN-7f3a'` | 0 | `3:SMOKE-PASS-TOKEN-7f3a` — anchored whole-line match in the **commit object** |
| 11 | `git show HEAD:smoke/marker.md \| grep -c 'SMOKE-PASS-TOKEN-7f3a'` | 0 | `1` — present exactly once |
| 12 | `grep -Fx 'SMOKE-PASS-TOKEN-7f3a' smoke/marker.md` | 0 | `SMOKE-PASS-TOKEN-7f3a` — worktree file matches too |
| 13 | `git show HEAD:smoke/marker.md \| sha256sum` | 0 | `08d51e3c5f535ed80582cd70ab9fd1a2671bbf417f26908bc2a96bd52bae0f16` |
| 14 | `sha256sum smoke/marker.md` | 0 | `08d51e3c5f535ed80582cd70ab9fd1a2671bbf417f26908bc2a96bd52bae0f16` — identical to the frozen blob hash |
| 15 | `git config --get core.autocrlf` | 0 | `true` — explains the repository's LF/CRLF warning behaviour |
| 16 | `git show HEAD:smoke/marker.md \| grep -c $'\r'` | 1 | `0` — frozen blob is pure LF; no CR attached to the token line |
| 17 | `git show HEAD:smoke/marker.md \| grep -nP '[^\x00-\x7F]'` | 1 | no match — frozen blob is ASCII only, so the token is not visually disguised by zero-width or homoglyph characters |
| 18 | `git rev-parse HEAD` (re-check after writing this report) | 0 | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` — unchanged |
| 19 | `git status --porcelain` (re-check after writing this report) | 0 | empty — still clean |

Commands 18–19 were run after this report was written, to support the claim that writing the report
did not perturb the product tree.

## Hard-gate results

Gate mapping follows the SMOKE-2 Stage Contract's round task and reviewer decision rule.

| Gate (from Stage Contract) | Result | Evidence |
|---|---|---|
| No commit and no product-file modification | **PASS** | commands 5, 6 (clean tree, empty diff), 18–19 (HEAD and status unchanged after the round); no state-changing git command was run |
| `smoke/marker.md` at the current HEAD contains the required token `SMOKE-PASS-TOKEN-7f3a` | **PASS** | commands 10–11: anchored whole-line match at line 3 of the commit object; exactly 1 occurrence |
| Report states the round is validation-only and names the unchanged HEAD SHA it is bound to | **PASS** | header block and Summary of this report name `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` as the frozen candidate |
| Worktree matches the frozen candidate (reviewer will re-check HEAD + `git status`) | **PASS** | commands 5–6, 13–14 (identical sha256), 18–19 |
| Token is an exact, undecorated, non-disguised line match | PASS | commands 10, 16, 17: anchored `-x` match; LF-only; ASCII-only |

## Numerical / scientific diagnostics

Not applicable. No simulation, no solver execution, no GPU work, and no scientific measurement
occurred. There is no trajectory, so there is no numerical stability, convergence state, termination
reason, or physical metric to report. Process exit code `0` on the read-only git and text commands is
**not** reported as any kind of scientific result or convergence evidence.

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| Frozen candidate (unchanged HEAD) | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` on branch `agent-episode/BI-VALIDATION-001-smoke-r1` | the SHA the SMOKE-2 review must bind to |
| Marker (frozen blob) | `smoke/marker.md` @ `2db5d1a1`, sha256 `08d51e3c5f535ed80582cd70ab9fd1a2671bbf417f26908bc2a96bd52bae0f16` | verified to contain the token line |
| Prior-stage candidate | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` (same commit; SMOKE-1 attempt-2 candidate) | promoted from SMOKE-1 PASS and reused unchanged as the SMOKE-2 candidate |
| Episode state record | `.agent_runtime/episodes/BI-VALIDATION-001/smoke_state.json` (read-only inspection) | confirms `current_stage: SMOKE-2` and the SMOKE-1 attempt-2 candidate SHA |
| This report | `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/round-01/execution_report.md` | round evidence, outside the product tree |

No new artifact was produced inside the product tree, by design.

## Deviations

- **None from the Task or the Stage Contract.** The round did exactly what the task prescribed:
  read-only verification of the token, and a report naming the unchanged SHA.
- Scope discipline note: the only file written anywhere was this report, in the evidence plane
  (outside the product worktree). Nothing under the product path
  `cg3d-episode-worktrees/BI-VALIDATION-001-smoke-r1` was added, edited, or deleted.
- Minor, non-behavioural: the repository has `core.autocrlf=true` (command 15), which is why git may
  print `LF will be replaced by CRLF` warnings for working-tree files. This did not affect the round:
  no working-tree file was written, and the frozen blob was confirmed LF-only (command 16).
- The candidate was **not pushed**. Per the Episode Contract, the runner publishes the product branch
  at PASS / HUMAN_REQUIRED / checkpoint boundaries, not the executor.
- The marker's retained description text still says "stage SMOKE-1, round 1" (the stage in which the
  file was created). This is historical provenance text inherited from the reused SMOKE-1 candidate,
  not a claim about this round; the product file was deliberately **not** edited, because SMOKE-2
  authorizes no product change at all. The binding SHA, not that sentence, is authoritative.

## Assumption / modeling impact

None. No scientific assumption, boundary-condition meaning, initial-condition meaning, wettability
convention, surface-tension calibration, viscosity/density assumption, or convergence/stopping
criterion is touched. This stage contains no scientific content.

## Existing evidence potentially affected

None. No product byte changed, so every prior artifact and result — including SMOKE-1 round-1 and
round-2 evidence and the SMOKE-1 candidate identity — remains valid and unaffected.

## Unresolved issues / human decisions

None. No unresolved scientific assumption, boundary interpretation, acceptance-criterion question, or
provenance ambiguity arose. Provenance is unambiguous: the base SHA named in the task, the HEAD
observed at the start of the round, the HEAD observed at the end of the round, and the candidate SHA
in this report are all the same commit object.

## Suggested next action

Dispatch a fresh reviewer session bound to candidate `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df`. The
Stage Contract's decision rule maps this round to **PASS** if, at review time, HEAD still equals that
SHA, the product tree is unmodified, and this report states the validation-only result with the
marker containing the token — all of which are satisfied as of this report. Because SMOKE-2 is the
last stage of the smoke mini-episode, its PASS must stop at CHECKPOINT_READY and must not
auto-promote further; the runner should then publish the durable stage record.
