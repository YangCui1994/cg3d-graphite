# A0 External Review — BI-VALIDATION-001

## Binding

- **Review target branch:** `agent-dev/bilateral-episode-v0.1`
- **Reviewed candidate:** `281f1d98210a1f97382c4c271a784a6b859aeeb1`
- **Parent planning commit:** `784e5ef2bcd8fa3701fd5785fc02ad7a9adb4947`
- **Review mode:** external planner-level review
- **Scope:** A0 runner implementation + committed A0 smoke evidence only

## Coverage

Inspected:

- `.agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py`
- `.agent/episodes/bilateral-imbibition-v0.1/runner/SMOKE_CONTRACT.md`
- `.agent/episodes/bilateral-imbibition-v0.1/RUNNER_BOOTSTRAP.md`
- `.agent/episodes/bilateral-imbibition-v0.1/EPISODE_PLAN.md`
- committed A0 smoke report/evidence
- round-01 and round-02 smoke reviews
- product execution base availability of `AGENTS.md`

The smoke itself is credible for the code path it exercises:
E1 fresh -> C1 -> R1 fresh CHANGES_REQUESTED -> E2 resume -> C2 -> R2 fresh PASS.

However, the smoke uses a dedicated `cmd_run_smoke()` implementation rather than the generic real-stage `cmd_run()` path. Several defects therefore remain hidden by the smoke.

## Blocking findings

### B1 — Real-stage rework attempt bookkeeping is broken

In `cmd_run()`:

- `attempt = st["attempts"]`;
- on `CHANGES_REQUESTED`, status becomes `REWORK`;
- `st["attempts"]` is not incremented.

On the next `run`, the same attempt number is reused. The REWORK branch then looks for:

`stage_run_dir(stage, attempt - 1) / "review.md"`

For the first rework this points to `round-00/review.md`, while outputs also collide with the prior attempt directory.

The dedicated smoke path manually implements two rounds and therefore does not test this defect.

**Required correction:** real-stage rework must create a new attempt number and bind it to the immediately preceding review/candidate. Add a deterministic test that exercises the generic real-stage round engine through CHANGES_REQUESTED -> rework -> PASS.

### B2 — A0 smoke does not exercise the orchestration path used by V0–V3

`cmd_run_smoke()` duplicates candidate/reviewer/rework logic separately from `cmd_run()`.

This allowed A0 to PASS while the real rework path is defective.

**Required correction:** either:

1. refactor smoke and real stages to share the same round/review/promotion engine; or
2. add an explicit generic-loop test that runs the exact production orchestration functions with a harmless fake/smoke stage.

A0 must validate the path that V0–V3 will actually use.

### B3 — V0 cannot succeed when the correct result is “no product change”

`cmd_run()` rejects:

`csha == base`

with “executor produced no candidate commit”.

But V0 explicitly says “Prefer no product changes”; a healthy baseline may only execute tests and produce evidence.

**Required correction:** support validation-only stages bound to an unchanged source SHA, or explicitly design and authorize an evidence-only/empty candidate commit. Prefer binding the review to the unchanged source SHA rather than creating meaningless product commits.

### B4 — External A0 approval is not actually enforced

Current state after smoke is `episode_status = A0_REVIEW`.

But `cmd_start_stage()` explicitly accepts both `A0_REVIEW` and `RUNNING`. Therefore V0 can be started before this external review approves A0.

The committed evidence states that the runner “REFUSES to start V0 until the external A0 review flips it”; the implementation does not do that.

**Required correction:** introduce an explicit externally-authorized state/action, for example:

`A0_REVIEW -> A0_APPROVED -> RUNNING`

and require an external-review reference/commit or explicit approval command before product initialization / V0 start.

### B5 — Session failure handling is insufficient for unattended execution

The real loop does not require, before proceeding:

- executor exit code == 0;
- no timeout;
- non-null executor session ID;
- newly written execution report exists;
- clean candidate worktree before review;
- reviewer exit code == 0;
- no timeout;
- non-null fresh reviewer session ID;
- newly written review exists.

A failed/stale session could therefore flow into candidate/review logic.

**Required correction:** treat any missing/failed process envelope, timeout, missing session ID, missing fresh report/review, or dirty pre-review candidate as a controlled stop (ERROR or HUMAN_REQUIRED according to the episode semantics). Never parse stale files from a previous attempt.

### B6 — The role contracts are not actually delivered to the agents

The executor prompt tells ZCode to read only:

- `AGENTS.md` in the product worktree;
- the Stage Contract.

But the declared product base `9ede55c...` does **not** contain `AGENTS.md`; the smoke executor already reported this deviation.

The executor is also not instructed to read:

- `EPISODE_PLAN.md`;
- `EXECUTOR_CONTRACT.md`.

The reviewer reads Episode + Stage contracts, but is not instructed to read `REVIEWER_CONTRACT.md`.

**Required correction:** provide explicit absolute/read-only control-plane paths to:

Executor:
- AGENTS.md
- EPISODE_PLAN.md
- EXECUTOR_CONTRACT.md
- current Stage Contract
- previous review when applicable

Reviewer:
- AGENTS.md or review-relevant project guardrails
- EPISODE_PLAN.md
- REVIEWER_CONTRACT.md
- current Stage Contract
- frozen candidate/report/evidence

Do not rely on `AGENTS.md` being present in the product branch.

### B7 — V0→V3 is not currently autonomous

After PASS, `cmd_run()` marks the next stage `READY` and returns.

Calling `run` again fails because READY is not an executable state; a human must invoke `start-stage <next>` between every stage.

This contradicts the episode objective of unattended V0→V3 progression.

**Required correction:** add a production `run-episode` / loop command (or equivalent) that:

- starts V0 after explicit A0 approval;
- handles bounded rework automatically;
- promotes PASS to the next stage automatically;
- stops on HUMAN_REQUIRED;
- stops at V3 CHECKPOINT_READY;
- is crash-resumable.

### B8 — Required durable publication is not implemented in the real loop

The Episode Contract requires durable publication/push at:

- stage PASS;
- HUMAN_REQUIRED;
- crash-recovery checkpoint;
- final V3 checkpoint.

The current generic loop only writes local runtime state/reports and changes state. It contains no real-stage publication/push path.

**Required correction:** implement stage publication that records at minimum:

- stage contract snapshot/hash;
- source/candidate SHA;
- execution report;
- review;
- exact validation commands and exit codes;
- metric/artifact manifest;
- attempt/session provenance;
- changed-files/diff summary.

Push the episode product branch/checkpoint evidence according to the contract. Large raw fields may remain local with hashes/paths.

## Important hardening findings

### H1 — Existing worktrees are trusted without identity/cleanliness checks

`_make_worktree()` returns an existing path without verifying:

- expected branch;
- expected HEAD;
- cleanliness;
- state/candidate consistency.

Before unattended scientific work, validate existing worktree identity and refuse ambiguous reuse.

### H2 — Reviewer “cannot modify product files” is stronger than the current guarantee

The reviewer runs in the same writable product worktree with `--mode yolo`.

The runner verifies only that HEAD/dirty state is clean after the review. This proves that the reviewer did not leave a persistent product modification; it does not technically prevent transient edits/commit-reset behaviour.

For v0.1 either:

- change the claim to “persistent reviewer product modifications are detected and rejected”; or
- strengthen isolation with a dedicated detached reviewer worktree / other write isolation.

Do not claim a stronger guarantee than the harness enforces.

### H3 — Contract provenance should be frozen per stage

Prompts currently read contracts from the moving control checkout by path.

Persist a stage-contract snapshot or SHA/hash at stage start so executor and reviewer can be shown to have used the same contract version.

This is already required by `CHECKPOINT_AND_PROMOTION.md` and should be implemented before long autonomous runs.

## A0 smoke assessment

The committed smoke evidence is useful and internally consistent:

- distinct reviewer sessions are shown;
- executor rework resumes the original executor session;
- candidate SHA binding is demonstrated;
- the planted defect is correctly caught and corrected;
- the product tree was clean at reviewer completion.

The smoke is therefore **PASS for the dedicated smoke path**, but it is **not sufficient evidence that the production V0–V3 loop is ready**, because that loop follows different code.

## Decision

**CHANGES_REQUESTED**

Do not start V0 yet.

## Required A0 rework acceptance

A0 can return for external review when:

1. B1–B8 are addressed;
2. H1 and H3 are implemented;
3. H2 is either strengthened or the guarantee is accurately narrowed;
4. an updated smoke/test exercises the **same generic orchestration path used by real stages**;
5. that test demonstrates at least:
   - validation-only unchanged-source stage can be reviewed;
   - CHANGES_REQUESTED increments to a new attempt;
   - executor rework consumes the immediately prior review;
   - each review is a fresh session;
   - failed/timed-out sessions do not advance;
   - PASS auto-promotes without a human `start-stage`;
   - max attempts stops correctly;
   - HUMAN_REQUIRED stops correctly;
   - V3-style terminal stage stops at CHECKPOINT_READY;
   - durable publication is produced;
   - explicit A0 authorization is required before real execution.

After that, publish a new A0 evidence package bound to the updated runner commit and stop again for external review.
