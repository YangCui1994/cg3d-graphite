# Execution Report — BI-VALIDATION-001-SMOKE / SMOKE-1 / round 1

- **Stage / attempt:** SMOKE-1 / attempt 1 (round 1)
- **Round status:** COMPLETED (candidate committed as instructed)
- **Hard gate status:** UNMET — intentionally, by design (see "Planted defect" below)
- **Base SHA (round base):** `9ede55c8ef7589b61606e11c033c84d9bcd1de94`
- **Candidate SHA:** `6c1d5a8960de448d498f50242318c7bb4b5445c8`
- **Branch:** `agent-episode/BI-VALIDATION-001-smoke-r1`
- **Worktree:** `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-VALIDATION-001-smoke-r1`

## Summary

Wrote a short free-text marker file `smoke/marker.md` and committed it as the single-file round
candidate on the product branch. No solver code, no tests, and no product documentation were
touched; nothing was run on the GPU.

Per the Stage Contract section "Planted defect (round 1 ONLY — by design)", the round-1 marker
deliberately omits the required token line so the fresh reviewer exercises the
CHANGES_REQUESTED path. The token line was therefore **not** written and must not be added in
this round.

## Changed files

| File | Change | Lines |
|---|---|---|
| `smoke/marker.md` | added (new file) | +8 |

`git diff 9ede55c8ef75..HEAD --name-only` returns exactly `smoke/marker.md` — no other path is
touched by the candidate, so the reviewer's "candidate touches files beyond smoke/marker.md →
HUMAN_REQUIRED" condition does not apply.

## Commands run and exit codes

| # | Command | Exit code | Key output |
|---|---|---|---|
| 1 | `git branch --show-current` | 0 | `agent-episode/BI-VALIDATION-001-smoke-r1` |
| 2 | `git rev-parse HEAD` (before) | 0 | `9ede55c8ef7589b61606e11c033c84d9bcd1de94` |
| 3 | `git status --short` (before) | 0 | empty — tree clean at round base |
| 4 | `git check-ignore -v smoke/marker.md` | 1 | no output — path not ignored, committable |
| 5 | `mkdir -p smoke` (+ runtime report dir) | 0 | `smoke/` and round-01 report dir created |
| 6 | `grep -n "SMOKE-PASS-TOKEN" smoke/marker.md` | 1 | no match — token absent (intended) |
| 7 | `git add smoke/marker.md` | 0 | staged `A smoke/marker.md`; benign LF→CRLF warning |
| 8 | `git diff --cached --stat` | 0 | 1 file changed, 8 insertions |
| 9 | `git commit -m "smoke(SMOKE-1 r1): add smoke/marker.md round candidate"` | 0 | `6c1d5a8` created |
| 10 | `git status --short` (after) | 0 | empty — no dirty or untracked product files left |
| 11 | `git diff 9ede55c8ef75..HEAD --name-only` | 0 | `smoke/marker.md` (only) |
| 12 | `git show HEAD:smoke/marker.md \| sha256sum` | 0 | `60d9a0e77a7b385f3027a8eee3fee5c91923422ebb2c5d4bc6080c3358a4240a` |
| 13 | `git show HEAD:smoke/marker.md \| grep -c "SMOKE-PASS-TOKEN"` | 1 | count `0` — token absent at the frozen candidate |

## Hard-gate results

| Gate (from Stage Contract) | Result | Evidence |
|---|---|---|
| `smoke/marker.md` at the frozen candidate contains the exact token line `SMOKE-PASS-TOKEN-7f3a` | **FAIL — intentional, by design** (round 1) | command 13: 0 matches at `6c1d5a8` |
| Each round ends with a commit of `smoke/marker.md` | PASS | commands 9–11: single-file commit `6c1d5a8` |
| Executor writes only `smoke/marker.md` in the product tree | PASS | command 11: diff range contains only that path |

This round is expected to receive **CHANGES_REQUESTED**. The required correction is to add the
exact token line; the validation to rerun is checking the file at the new candidate commit only.

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| Round candidate commit | `6c1d5a8960de448d498f50242318c7bb4b5445c8` | candidate frozen for review |
| Marker (frozen blob) | `smoke/marker.md` @ `6c1d5a8`, sha256 `60d9a0e7…a4240a` | frozen single-file candidate |
| This report | `.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-1/round-01/execution_report.md` | round evidence (outside product tree) |

## Numerical / scientific diagnostics

Not applicable. This stage contains no simulation, no solver change, and no scientific
measurement; no convergence, stability, or physical metric exists for it. Process exit code 0
on the commit commands is not reported as any kind of scientific result.

## Deviations

- **None functional.** The omitted token is not a deviation — it is the behaviour the Stage
  Contract explicitly mandates for round 1 ("Planted defect"), and the round task instructed the
  same.
- Minor, non-behavioural: `git add` printed a `LF will be replaced by CRLF` warning (Windows
  `autocrlf`). The blob is stored with LF and the file content is unaffected.
- The candidate was not pushed. Per the Episode Contract, the runner publishes the branch at
  PASS / HUMAN_REQUIRED / checkpoint boundaries, not the executor mid-round.

## Assumption / modeling impact

None. No scientific assumption, boundary-condition meaning, wettability convention, calibration,
viscosity/density assumption, or stopping criterion is touched by this change.

## Existing evidence potentially affected

None. The change adds one new infrastructure file and modifies no existing path.

## Unresolved issues / human decisions

None. The unmet hard gate is the intended round-1 state, not an unresolved issue.

## Suggested next action

Dispatch a fresh reviewer session against candidate `6c1d5a8960de448d498f50242318c7bb4b5445c8`;
it is expected to return CHANGES_REQUESTED for the missing required token line, which routes
back to this stage for the bounded round-2 correction.
