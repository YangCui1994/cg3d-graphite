stage: SMOKE-2
attempt: 1
candidate: 2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df
execution_report: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/smoke/SMOKE-2/round-01/execution_report.md

# Review — BI-VALIDATION-001-SMOKE / SMOKE-2 / attempt 1

## binding

| Item | Value |
|---|---|
| Stage / attempt | SMOKE-2 / attempt 1 (fresh reviewer session) |
| Candidate SHA (frozen) | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` |
| HEAD observed at review time | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` — identical to the frozen candidate |
| Branch | `agent-episode/BI-VALIDATION-001-smoke-r1` |
| Product worktree | `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-VALIDATION-001-smoke-r1` |
| Round type | VALIDATION-ONLY — no product change; the reviewed candidate is the unchanged HEAD |
| Stage Contract snapshot | `…/runner/SMOKE_VALIDATION_CONTRACT.md`, sha256 `81c50c7b39a10ff769c8b7fd24134c45807a4a57e6a86572eb8b4808ca5942b1` — recomputed by the reviewer and matching the declared value |
| Registered candidate in runner state | `smoke_state.json`: SMOKE-2 `CANDIDATE_READY`, attempts 1, `validation_only: true`, sha and base both `2db5d1a1…`, `contract_sha256` matching the snapshot above |
| Reviewer evidence | `…/SMOKE-2/round-01/reviewer_evidence/candidate_verification.md` |
| Write restriction honoured | Reviewer modified no product file, commit, branch, test, or executor artifact; only this review and the reviewer-owned evidence directory were written |

Candidate binding is unambiguous. The reviewed SHA, the review-time HEAD, the declared round base in the execution report, and the
registered candidate in the runner state are one and the same commit object, so the Episode Contract's
"candidate/evidence mismatch" stop condition does not apply. The promotion chain is also traceable: SMOKE-1 attempt 2 PASSed on
this same SHA (`SMOKE-1/round-02/review.md`, candidate `2db5d1a1…`), and an unchanged reuse of a promoted candidate is exactly
what the SMOKE-2 Stage Contract prescribes.

## coverage

Contract requirement table (Stage Contract "Round task", "Executor report requirement", "Write restrictions"):

| # | Requirement | Status | Basis |
|---|---|---|---|
| R1 | Executor makes no commit | MET | HEAD at review time equals the declared base; `git log` shows no commit after `2db5d1a`; reflog shows no commit action after it |
| R2 | Executor makes no product-file modification | MET | `git status --porcelain` empty; re-checked with `--untracked-files=all --ignored` → 0 entries; `git diff HEAD --stat` empty |
| R3 | Read-only verification that `smoke/marker.md` at HEAD contains `SMOKE-PASS-TOKEN-7f3a` | MET | Anchored whole-line match against the commit object: `3:SMOKE-PASS-TOKEN-7f3a`; exactly 1 occurrence; token unique across the whole frozen tree |
| R4 | Report states the round is validation-only and names the unchanged HEAD SHA | MET | Report header and Summary name `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` and state "validation-only … no commit was made" |
| R5 | Marker verified at the frozen SHA, not merely in the worktree | MET | Reviewer verified `git show HEAD:smoke/marker.md`; worktree and blob digests are identical (`08d51e3c…`) |
| R6 | Reviewer write restriction respected | MET | Only `review.md` and `reviewer_evidence/` written, both outside the product tree |

Validation table — every load-bearing executor claim was re-run independently by the reviewer:

| Check | Executor claim | Reviewer re-run (result) | Agrees |
|---|---|---|---|
| HEAD SHA | `2db5d1a1…` (cmd 2, 18) | `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df` | yes |
| Working tree clean | empty `status`, empty diff (cmd 5, 6, 19) | empty; plus 0 entries under `--ignored` | yes |
| Marker exists at HEAD | `git cat-file -e` OK, only file under `smoke/` (cmd 7, 8) | blob `07e48920…`; `ls-tree` lists `smoke/marker.md` only | yes |
| Token anchored whole-line match | `3:SMOKE-PASS-TOKEN-7f3a` (cmd 10) | identical match at line 3 of the commit object | yes |
| Token occurs once | count `1` (cmd 11) | count `1` | yes |
| Blob digest | `08d51e3c5f535ed80582cd70ab9fd1a2671bbf417f26908bc2a96bd52bae0f16` (cmd 13) | identical digest | yes |
| Blob == worktree bytes | identical digests (cmd 14) | identical digests | yes |
| LF-only, no CR on token line | `grep -c $'\r'` → 0 (cmd 16) | `cat -A` shows `$` line ends with no `^M` | yes |
| `core.autocrlf` | `true` (cmd 15) | `true` | yes |
| Token not disguised / not duplicated | ASCII-only, single line (cmd 17) | `git grep` across `HEAD` finds exactly one hit, in `smoke/marker.md` | yes |

Not covered by this review, deliberately:

- The executor's own command-by-command execution record is not independently observable from the repository — only its outcome is.
  The reviewer therefore re-ran the outcome-bearing subset (all rows above) rather than trusting the transcript. The executor's
  session log was **not** read, per the Episode Contract's reviewer-isolation rule (no executor transcript or chain-of-thought).
- Whether the round wrote anything outside the product worktree and outside the evidence plane is a runner-side concern; the
  reviewer's write-restriction check covers the product worktree (R2/R6).
- No scientific, numerical, or convergence evidence is expected or required in this round; its absence is correct, not missing.

## findings

### Blocking findings

None.

### Non-blocking findings

1. **Stale provenance sentence inside the marker (already declared by the executor).** `smoke/marker.md` retains the line
   "stage SMOKE-1, round 1, on branch `agent-episode/BI-VALIDATION-001-smoke-r1`" while it is now the SMOKE-2 candidate. The
   execution report discloses this under Deviations and explains, correctly, that SMOKE-2 authorizes no product change, so the
   text was deliberately left alone. Leaving it untouched is the right call: editing it would have created a product commit and
   broken the validation-only premise of this very stage. The binding SHA, not that sentence, is authoritative. No action.
2. **The "no state-changing git command was run" claim is unfalsifiable from the repository.** The report asserts it under
   "Product change — none"; only its consequence is verifiable (unchanged HEAD, clean tree, unchanged reflog tail). This does not
   weaken the gates, which are stated in terms of observable state, not command history. No action.
3. **`core.autocrlf=true` in this checkout.** Confirmed by the reviewer. It is a standing hazard for future stages with
   content-bearing files (silent LF→CRLF rewriting on checkout could contaminate byte-level digests), but it did not affect this
   round: the marker blob and the checked-out file hash identically and both are LF-only. Worth remembering, not a defect here.
4. **Report length and redundant self-verification.** The report runs to 19 numbered commands for a three-part read-only check.
   Harmless, and the extra negative checks (CR scan, non-ASCII scan) are genuinely useful, but future validation-only rounds could
   state the outcome-bearing subset and note the rest as supporting detail.

### Scientific / modeling review

Not applicable, and the report says so explicitly rather than inflating exit code 0 into a result. No solver code, physics,
boundary- or initial-condition meaning, wettability convention, surface-tension calibration, viscosity/density assumption, or
convergence criterion is touched by this round; `smoke/marker.md` is a token-bearing placeholder that declares itself as containing
no scientific content, and no simulation or GPU work occurred. The Episode Contract's scientific stop conditions (NaN/Inf,
density collapse, unexplained left/right asymmetry, trapped-phase interpretation overflow) are all inapplicable at this stage, and
nothing in this round invalidates any prior validation evidence, because no product byte changed.

## decision

Decision: PASS

## rationale

The Stage Contract's reviewer rule has three conjunctive parts, and all three are satisfied by direct reviewer observation rather
than by executor assertion:

- **HEAD at review time equals the frozen (unchanged) candidate SHA.** Independently confirmed: `git rev-parse HEAD` returns
  `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df`, the same SHA named in my instructions, in the execution report, and in the runner
  state record as the SMOKE-2 candidate.
- **The report exists and states the validation-only result.** The report at the named path declares the round VALIDATION-ONLY,
  states that no commit and no product-file modification occurred, and names the unchanged HEAD SHA it is bound to.
- **The marker at that SHA contains the token.** Verified against the commit object, not the worktree: anchored whole-line match
  `SMOKE-PASS-TOKEN-7f3a` at line 3, exactly one occurrence, token unique across the entire frozen tree, blob digest
  `08d51e3c…` identical to the checked-out file.

The two conditions that would have forced CHANGES_REQUESTED — HEAD differing from the frozen SHA, or a modified product tree —
are both refuted, and refuted under a stricter test than the contract requires (untracked *and* ignored files included). The
HUMAN_REQUIRED condition (ambiguous provenance) is also refuted: base, HEAD, registered candidate, and report SHA are all the same
commit object, and the SMOKE-1 → SMOKE-2 promotion chain is documented in both the state record and the prior stage review.

Beyond the three-part rule, nothing in the Stage Contract's PASS semantics is left open: the required evidence exists and is bound
to the reviewed candidate, no blocking finding remains, and there is no diagnostic anomaly that could change the meaning of
anything downstream — the round has no diagnostics at all, by construction. On the wider review questions the Reviewer Contract
asks, this candidate cannot misrepresent the intended physical problem: it is unchanged source, and the only artifact added by the
episode is a marker file that carries no scientific claim.

Because SMOKE-2 is the last stage of the smoke mini-episode, this PASS must not be read as promotion authority beyond it.

## next action

1. Runner records the SMOKE-2 attempt-1 PASS and the reviewed candidate `2db5d1a1cb2fc60fe9862aa1af8018ac71fce4df`, and appends the
   review decision to `smoke_state.json`.
2. Runner stops the episode at CHECKPOINT_READY — per the Stage Contract's terminal-behaviour clause, the SMOKE-2 PASS must **not**
   auto-promote to any further stage, and the runner must not enter porous-media/V-stage work. This smoke mini-episode's purpose
   (proving the validation-only path with an unchanged SHA, per A0 finding B3) is complete once the PASS is recorded.
3. Runner publishes the durable stage record to the control/evidence plane and pushes the product branch at this boundary, per
   Episode Contract §7. No push was made by the executor, correctly.
4. No executor rework round is required, and no rework context instruction applies.
