stage: A0
attempt: 2
candidate: 08117fd92db86212d8a7185141fae71b0a353006
execution_report: .agent/evidence/BI-VALIDATION-001/A0_SMOKE_R1/A0_R1_EVIDENCE.md

# A0 External Review R2 — BI-VALIDATION-001

## Binding

- **Runner implementation reviewed:** `08117fd92db86212d8a7185141fae71b0a353006`
- **Evidence index:** `.agent/evidence/BI-VALIDATION-001/A0_SMOKE_R1/A0_R1_EVIDENCE.md`
- **Current evidence/control branch head inspected:** `b23a5e966d5e7c83433515dc469931276deeba25`
- **Review mode:** external planner-level review
- **Previous external review:** `A0_SMOKE/A0_EXTERNAL_REVIEW.md`

The later commits after `08117fd...` are evidence/publication commits; the generic smoke stage records themselves identify `08117fd...` as the runner commit that produced the run.

## Summary

The A0-R1 rework is materially better than the first implementation.

The following previous findings are substantially resolved:

- B1: rework attempts increment correctly in the generic engine;
- B2: smoke and V0–V3 now share `run_round()/run_episode()`;
- B3: validation-only unchanged-source candidates are supported;
- B4: an explicit A0 approval state/action now exists;
- B6: executor/reviewer receive their role contracts by control-plane path;
- B7: a real `run-episode` auto-promotion loop exists;
- H2: reviewer write isolation claim has been narrowed accurately.

The real-session generic smoke is useful evidence:
SMOKE-1 performs CHANGES_REQUESTED -> resumed executor -> fresh reviewer -> PASS, and SMOKE-2 reviews an unchanged-source validation-only candidate and terminates at CHECKPOINT_READY.

However, several remaining defects affect durable provenance and failure recovery. A0 is therefore not yet ready to authorize a long unattended V0–V3 run.

## Blocking findings

### B9 — Product candidate branch is not durably pushed

The Episode Contract requires durable publication of both stage evidence and the product/candidate history at stage boundaries.

Current `publish_round()` commits and pushes the **control/evidence branch only**:

- copies contract/report/review/session evidence;
- commits the evidence directory;
- pushes the current control branch.

It never pushes `cfg["branch"]` from the product worktree.

This is observable in GitHub now: no remote `agent-episode/*` branch exists, while evidence records refer to smoke candidate SHAs such as `6c1d5a89...` and `2db5d1a1...`.

If the Windows worktree/clone is lost, the durable GitHub evidence can point to candidate commits that are not reachable from any remote ref.

**Required correction**

At every durable publication boundary required by the Episode Contract (at minimum PASS, HUMAN_REQUIRED, crash/manual checkpoint, final checkpoint):

1. verify the product worktree is on the expected product branch and exact reviewed SHA;
2. push that product branch with a normal non-force push;
3. record the remote branch/ref and pushed SHA in `stage_record.json`;
4. fail safely if the push is rejected.

For validation-only stages the branch may remain at the same SHA, but the remote ref still must exist.

Add a deterministic test/stub assertion and, preferably, make the smoke product branch visible remotely or otherwise demonstrate the push path without leaving ambiguous local-only candidates.

### B10 — Contract provenance is hashed, but the stage contract is not actually frozen

At stage start, `start_stage()` records:

`contract_sha256 = sha256_file(current_contract_path)`

But executor and reviewer prompts still read the **moving control-plane contract path**.

At publication, `publish_round()` copies the contract from that moving path at publication time.

Therefore, if the contract file changes during a long stage:

- the stored SHA can describe version A;
- a later executor/reviewer can read version B;
- `contract_snapshot.md` can contain version B;
- the evidence can claim a frozen contract while not actually preserving what the first session used.

The prompts include the expected hash, but the runner itself does not verify that the file still matches that hash before each session/publication.

**Required correction**

Prefer one of:

1. create an immutable runtime contract snapshot at `start_stage()`, record its hash, and point all executor/reviewer prompts to that snapshot; or
2. verify the live contract hash equals the frozen hash before every executor session, reviewer session, and publication, stopping on mismatch.

Publication must copy the exact frozen bytes whose hash is recorded.

Add a test that mutates the control-plane contract after stage start and proves the runner refuses to continue or continues from the immutable snapshot.

### B11 — A0 approval can accept a PASS review with no candidate binding

`approve_a0_from_text()` currently does:

- parse a candidate if one is found;
- reject only when a candidate exists **and** differs from `runner_commit`.

If the external-review text says only:

`Decision: PASS`

and contains no parsable candidate, `cand=None` and the approval can still succeed.

That contradicts the requirement that approval be bound to the exact runner commit that produced the smoke.

**Required correction**

Require a full 40-character candidate/runner commit binding to be present and exactly equal to `state["smoke"]["runner_commit"]`.

Add a test for “PASS with missing candidate binding” and require rejection.

### B12 — Session failure can advance Git history without advancing state

`validate_session()` runs **after** the executor session.

An executor can:

1. create/commit a source change;
2. then exit non-zero, time out, fail to emit a valid session envelope, or fail to write the report.

The runner correctly records no candidate decision, but the product worktree HEAD may already have advanced.

The current failure tests assert state/candidate counts, but do not assert that HEAD remains at the pre-round base.

On a later retry, the new round base can silently become this unreviewed commit.

This breaks candidate provenance: source state can advance even though the state machine says the round did not.

**Required correction**

Record the pre-session round base SHA and, on any invalid executor session:

- if HEAD is still the base and tree clean: safe ERROR;
- if HEAD/tree changed: do **not** silently reuse it. Record the orphan/unreviewed source state and require explicit recovery (HUMAN_REQUIRED or a deterministic recovery policy that preserves/proves the change).

Never start a new executor retry treating an unreviewed failed-session commit as an accepted base.

Add a failure test where the stub executor commits a change and then returns non-zero/timeout, and assert that the runner cannot silently continue from it.

### B13 — Reviewer-session ERROR recovery restarts the executor rather than preserving the frozen candidate

When the reviewer session fails after a valid executor candidate exists:

- the candidate is already appended to `st["candidates"]`;
- status becomes ERROR;
- `error_phase` is set to the stage phase at entry (EXECUTING/REWORK).

On same-attempt retry, `run_round()` restores that phase and launches the executor again rather than simply retrying a fresh reviewer against the already-frozen candidate.

This can create another commit for the same attempt and weakens the candidate/review binding model.

**Required correction**

Persist a finer-grained round phase, for example:

EXECUTOR_PENDING
-> CANDIDATE_FROZEN
-> REVIEW_PENDING

If the reviewer process fails but candidate provenance is intact, retry a fresh reviewer on the **same frozen candidate** and same execution report; do not rerun the executor.

If the candidate/worktree is no longer intact, stop for explicit recovery.

Add a test: valid executor candidate + failed reviewer session -> retry -> no additional executor call/commit -> fresh reviewer reviews the identical candidate SHA.

## Hardening findings

### H4 — Existing worktree expected-HEAD checking is implemented but not used by top-level attach paths

`make_worktree(cfg, expected_head=...)` can verify HEAD, but both:

- `cmd_run_smoke()`
- `cmd_init_product()`

call `make_worktree(cfg)` without an expected SHA.

Thus an existing clean worktree on the correct branch but at an unexpected commit is accepted.

This does not fully satisfy previous H1 (“branch, cleanliness, expected head”).

**Required correction**

When attaching an existing worktree, derive the expected HEAD from persisted state:

- before first real stage: declared product base;
- during/resuming episode: latest frozen/accepted candidate implied by state;
- smoke reset/new smoke: declared smoke base unless state explicitly binds a later candidate.

Refuse a branch-correct, clean, but state-inconsistent worktree.

Add a test for this exact case.

### H5 — Reinvoking `run-episode` while a stage is in ERROR can spin indefinitely

The first `run_episode()` invocation correctly returns `ERROR` immediately when `run_round()` fails.

But on a subsequent invocation with the persisted stage status already `ERROR`, the loop handles only READY / EXECUTING / REWORK and has no ERROR branch. If episode_status remains RUNNING, the while-loop has no terminating transition.

**Required correction**

Make ERROR an explicit terminal return for `run_episode()`, or define and implement an explicit recovery command/state transition.

Do not allow a busy loop on a persisted ERROR state.

Add a test that calls `run_episode()` again after a persisted ERROR and proves deterministic termination.

## Publication/evidence assessment

The new control-plane evidence publication is useful:

- contract hash is recorded;
- reports/reviews/session prompts are durably copied;
- attempt histories are preserved;
- the evidence commits themselves are on GitHub.

But until B9 and B10 are fixed, the evidence is not fully self-contained:

- candidate SHAs can be local-only;
- the claimed contract snapshot can drift from the hashed version.

## Decision

Decision: CHANGES_REQUESTED

Do not approve A0 or start V0 yet.

## Required next action

Perform A0-R2 rework only.

A0 may return for the next external review when:

1. B9–B13 are fixed;
2. H4–H5 are fixed;
3. generic-engine tests explicitly cover each new failure/recovery case;
4. the real/generic smoke is rerun if the changed logic affects candidate publication, reviewer retry, or contract snapshot behaviour;
5. the resulting evidence package identifies the exact runner commit;
6. V0–V3 remain unstarted.

RESET_CONTEXT: NO
