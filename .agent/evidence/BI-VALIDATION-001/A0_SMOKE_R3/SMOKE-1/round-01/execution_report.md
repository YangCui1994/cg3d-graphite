# Execution Report — BI-VALIDATION-001 / SMOKE-1 / attempt 1

## 1. Identity

| Field | Value |
|---|---|
| Stage ID | SMOKE-1 (A0 runner isolation smoke test) |
| Episode | BI-VALIDATION-001 |
| Attempt | 1 (round 1 of 2 — planted-defect round) |
| Role | ZCode Executor |
| Product branch | `agent-episode/BI-VALIDATION-001-smoke-r3` |
| Round base SHA | `9ede55c8ef7589b61606e11c033c84d9bcd1de94` |
| **Candidate SHA** | **`0e176e5dafc7a64609f41f50f66711f863d771ce`** |
| Candidate parent | `9ede55c8ef7589b61606e11c033c84d9bcd1de94` (single-commit diff, no other commit in between) |
| Stage contract snapshot | `contract_snapshot.md`, sha256 `a87eba7f30c65460414f5f194f413bbe247706c405ef5b2a7a35761c3879adb6` |
| Commit author/date | Yang Cui `<yang@YangdeMacBook-Pro.local>`, Wed Sep 23 20:22:20 2026 +0800 |

## 2. Outcome

Candidate committed — **not** a validation-only round. The stage requires a
committed single-file marker, and this round produced one. The commit
intentionally omits the required hard-gate token, as the Stage Contract
instructs for round 1.

## 3. Changed files at the candidate

`git diff --name-status 9ede55c8ef75..0e176e5` →

```
A	smoke/marker.md
```

Exactly one file added, identical to the Stage Contract's "clean single-file
marker commit" requirement. No other path is touched by the diff; no
solver, test, or product documentation file is modified.

| Path | Status | Blob SHA-1 | sha256 |
|---|---|---|---|
| `smoke/marker.md` | added | `1abf3c44367f6a7cdda7240f40f67dd839f16e9e` | `18f0245b6841f8152afb6386daae8021b7533aee9847ade5c70cb579a5d34c96` |

## 4. Hard-gate result

Stage hard gate: `smoke/marker.md` at the frozen candidate commit must
contain the exact line `SMOKE-PASS-TOKEN-7f3a`.

**Result: FAIL (expected and intended for round 1.)**

The token line is absent by design — this is the documented planted defect
for this round. The gate failing here is the correct, contracted behaviour,
not an execution error. The fresh reviewer is expected to return
CHANGES_REQUESTED, and the runner should route round 2 back to this stage
with a corrective action of "add the exact token line".

## 5. Commands run and exit codes

| # | Command (working dir: repo root of the smoke worktree) | Exit code | Observed |
|---|---|---|---|
| 1 | `git status --short` | 0 | empty (clean tree at start) |
| 2 | `git rev-parse --abbrev-ref HEAD` | 0 | `agent-episode/BI-VALIDATION-001-smoke-r3` |
| 3 | `git rev-parse HEAD` | 0 | `9ede55c8ef7589b61606e11c033c84d9bcd1de94` (= declared round base) |
| 4 | `ls -la smoke/` | 2 | `No such file or directory` — `smoke/` did not exist; created by this round |
| 5 | `grep -c '^SMOKE-PASS-TOKEN-7f3a$' smoke/marker.md` | 1 | `0` matches — gate FAIL (pre-commit, working tree) |
| 6 | `git add smoke/marker.md && git commit -m "smoke(SMOKE-1 r1): add candidate marker file for runner isolation test"` | 0 | `1 file changed, 12 insertions(+)` → `0e176e5` |
| 7 | `git show --stat --oneline HEAD` | 0 | `smoke/marker.md \| 12 ++++++++++++` |
| 8 | `git diff --name-status 9ede55c8ef75..HEAD` | 0 | `A smoke/marker.md` (only file) |
| 9 | `git status --short` (post-commit) | 0 | empty (clean — no uncommitted residue) |
| 10 | `git rev-parse HEAD:smoke/marker.md` | 0 | `1abf3c44367f6a7cdda7240f40f67dd839f16e9e` |
| 11 | `git show HEAD:smoke/marker.md \| grep -c '^SMOKE-PASS-TOKEN-7f3a$'` | 1 | `0` matches — gate FAIL confirmed **at the candidate commit**, not merely in the working tree |
| 12 | `sha256sum smoke/marker.md` | 0 | `18f0245b6841f8152afb6386daae8021b7533aee9847ade5c70cb579a5d34c96` |
| 13 | `git log -1 --format=...` | 0 | candidate metadata as recorded in §1 |

Command 11 is the authoritative gate check: it reads the file out of the
frozen commit object rather than the working tree, so the FAIL verdict is
bound to the candidate SHA and not to transient local state.

## 6. Marker file content at the candidate

The committed file (`HEAD:smoke/marker.md`, 12 lines) contains a title, a
statement of purpose, and a short free-text description of the round. It
does **not** contain the required token line. No other token-like string is
present, so there is no near-miss or partial-token ambiguity for the
reviewer to interpret.

## 7. Diagnostics

- Numerical stability: not applicable — this stage performs no numerical
  work.
- Convergence/termination reason: not applicable — no solver run.
- Authorized-scope compliance: the only write inside the product tree was
  `smoke/marker.md`. No product code, test, or documentation file was
  modified. No branch was created, none merged, no push performed, no
  history rewritten, no force-push.
- Reviewer-facing line-ending note: Git reported `LF will be replaced by
  CRLF the next time Git touches it` for `smoke/marker.md` (Windows
  worktree). The committed blob retains LF, so the reviewer's byte-level
  view of the file at the candidate commit is the LF form. This is a
  cosmetic warning only and does not affect the gate.

## 8. Artifacts

| Artifact | Location | sha256 |
|---|---|---|
| Candidate file | `smoke/marker.md` @ `0e176e5` | `18f0245b6841f8152afb6386daae8021b7533aee9847ade5c70cb579a5d34c96` |
| This report | `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-1/round-01/execution_report.md` | (runtime plane, outside product tree) |

## 9. Deviations

**One deviation from what a neutral reader of the round task might assume,
recorded explicitly.** The Stage Contract frozen for this stage names the
smoke branch `agent-episode/BI-VALIDATION-001-smoke-r1`, whereas the round
task for this attempt names `agent-episode/BI-VALIDATION-001-smoke-r3`. The
candidate was committed on the branch named by the round task (`-r3`), which
is also the branch this worktree is checked out on and the branch the runner
created for this attempt. The stage ID, acceptance rule, planted defect, and
reviewer decision rule are identical in both; only the branch suffix differs,
and the `-r3` suffix is consistent with the declared round base
`9ede55c8ef75`, which is this branch's HEAD before the commit. Flagged so the
reviewer does not treat the branch-name mismatch as a provenance problem.

No other deviation. The planted defect is not a deviation — it is the
contracted behaviour for round 1.

## 10. Unresolved issues

None for this round. The single open item is the intended gate failure,
which round 2 is contracted to correct.

## 11. Suggested next action

Dispatch a fresh reviewer session bound to candidate
`0e176e5dafc7a64609f41f50f66711f863d771ce`, expecting
**CHANGES_REQUESTED** with the finite corrective action "add the exact token
line `SMOKE-PASS-TOKEN-7f3a` to `smoke/marker.md`", then route round 2 back
to this stage as a new attempt bound to that review.
