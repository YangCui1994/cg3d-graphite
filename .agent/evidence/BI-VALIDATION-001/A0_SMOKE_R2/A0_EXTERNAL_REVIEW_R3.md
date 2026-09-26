stage: A0
attempt: 3
candidate: f6a9fe079dfa9e1ca55de9c61561227f844fba71
execution_report: .agent/evidence/BI-VALIDATION-001/A0_SMOKE_R2/A0_R2_EVIDENCE.md

# A0 External Review R3 — BI-VALIDATION-001

## Binding

- **Runner implementation reviewed:** `f6a9fe079dfa9e1ca55de9c61561227f844fba71`
- **Evidence index:** `.agent/evidence/BI-VALIDATION-001/A0_SMOKE_R2/A0_R2_EVIDENCE.md`
- **Evidence/control branch head inspected:** `5e16c17bd65350b17dc410061bb586047045553b`
- **Remote smoke product branch verified:** `agent-episode/BI-VALIDATION-001-smoke-r2` at `7ab0094b9a5b4d5266a74fecb0a189b64f980621`
- **Review mode:** external planner-level review
- **Previous review:** `A0_SMOKE_R1/A0_EXTERNAL_REVIEW_R2.md`

The commits after `f6a9fe...` contain the successful smoke evidence/publication only; the runner source itself is unchanged after the reviewed implementation commit.

## Summary

A0-R2 closes the major findings from the previous two reviews.

Verified as substantially resolved:

- rework attempt numbering and immediate-prior-review binding;
- one generic engine for smoke and V0–V3;
- validation-only unchanged-source review;
- explicit A0 approval gate;
- session exit/timeout/artifact validation;
- role-contract delivery;
- V0→V3 autonomous promotion;
- durable control-plane evidence publication;
- durable product-branch push and remote-ref verification;
- frozen stage-contract snapshots;
- strict A0 candidate binding;
- orphan protection for failed executor sessions that changed source;
- reviewer retry against the same frozen candidate;
- existing-worktree identity checks;
- persisted ERROR termination.

The live R2 smoke is strong evidence: it also accidentally exercised the B12 orphan path, which correctly stopped rather than adopting an unreviewed executor commit.

This review does **not** reopen those items.

Three remaining issues are blocking because they can still make a long unattended episode advance from an unreviewed or non-durable state.

## Blocking findings

### B14 — Publication failure occurs after PASS/promotion state is already persisted

In `run_round()`, after a valid review decision:

1. stage status is changed to PASS / REWORK / HUMAN_REQUIRED;
2. for PASS, `current_stage` may already advance to the next stage;
3. state is persisted with `save(state)`;
4. only then is `publisher(...)` called.

If either:

- product-branch push fails;
- remote-ref verification fails;
- evidence commit fails;
- control-branch push is rejected;

the process raises after the state machine has already recorded successful promotion.

On restart, the persisted state can therefore say the previous stage passed and the next stage is READY even though its durable publication boundary failed.

That violates the Episode Contract's rule that PASS/promotion evidence be durably published before autonomous progression.

**Required correction**

Make promotion publication-safe.

Acceptable designs include:

1. two-phase transition:
   - REVIEW_DECIDED / PUBLISH_PENDING;
   - publish product + evidence;
   - only after successful publication persist PASS/promotion;

or

2. if publication fails after provisional state mutation:
   - catch the failure;
   - persist an explicit ERROR/PUBLISH_FAILED state;
   - do not expose/promote the next stage as executable until recovery proves publication.

A subsequent `run-episode` must not silently continue to the next stage after a failed publication.

Add deterministic tests for:
- product push failure after PASS;
- control/evidence push failure after PASS;
- persisted restart after either failure.

### B15 — “valid executor + dirty worktree before review” can still become an unreviewed retry base

After a successful executor session, the runner checks:

`if worktree_dirty(cfg["worktree"]): ... status = ERROR ... publisher(...)`

This path differs from the failed-session orphan path:

- it does not record a `base_guard`;
- it does not freeze/record the candidate;
- it does not restore the tree;
- publication is not marked evidence-only;
- `publish_round()` may push the current HEAD even though no candidate was reviewed.

On explicit retry, ERROR restores the executor-pending phase. Because no guard is present, the current HEAD can become the new round base while uncommitted dirty files also remain.

Thus a valid executor session that committed code but left extra dirty changes can cause the next attempt to start from an unreviewed commit/state.

The existing S7 test checks ERROR classification, but does not verify that the next retry cannot adopt the unreviewed HEAD/dirty tree.

**Required correction**

Treat any pre-review source-state ambiguity the same way as B12:

- if executor completion leaves HEAD/tree different from the exact intended frozen candidate state, do not silently retry from it;
- either classify it as terminal HUMAN_REQUIRED/orphan, or define a deterministic recovery that restores the exact pinned round base/candidate and records the discarded state.

Do not push an unreviewed ambiguous product state as if it were a durable candidate.

Add a test:
- executor commits candidate + leaves dirty extra file;
- pre-review check fails;
- retry is attempted;
- runner proves it cannot silently adopt the commit/dirty tree as the next base.

### B16 — A0 approves one runner implementation, but the real episode does not enforce that implementation

The smoke records the approved runner implementation in:

`state["smoke"]["runner_commit"] = f6a9fe...`

and `approve-a0` correctly binds the external review to that SHA.

However, after approval:

- the real state does not freeze an approved runner source hash/commit as an execution invariant;
- `_require_real_ready()` checks only `episode_status == A0_APPROVED`;
- V0–V3 may therefore run if `episode_runner.py` is later modified on the control branch without rerunning A0.

Also, real-stage `stage_record.json` reads `state.get("runner_commit")`; the main real state is not clearly populated with the smoke-approved runner commit, so real provenance may record `null` even though A0 approved `f6a9fe...`.

This breaks the central meaning of A0: the harness that was smoke-tested and externally approved must be the harness that runs V0–V3.

**Required correction**

On successful `approve-a0`:

- persist the approved runner commit and preferably the SHA256/blob identity of `episode_runner.py`;
- before every real entry point / stage start / run-episode continuation, verify the executing runner file is identical to the approved implementation (evidence-only commits after it are fine);
- record that approved runner identity in every real stage record.

If runner code changes, refuse real execution and require a new A0 smoke/review.

Add tests:
- approved runner unchanged → real loop allowed;
- runner source changed after approval → real loop refused.

## Required before PASS

Only B14–B16 are blocking in this review.

The next A0 rework does **not** need another broad redesign.

Required evidence:

1. generic tests covering B14–B16;
2. runner source update;
3. a focused smoke is required only if the changed code affects the live round/publish path materially — which B14/B15 do, so rerun at least the generic live smoke path once;
4. resulting evidence binds to the exact new runner implementation;
5. V0–V3 remain unstarted.

## Non-blocking items for later framework hardening

These do not block V0 in the next review unless the rework makes them relevant:

- The global Episode / Executor / Reviewer contracts and AGENTS.md remain live control-plane files while only the Stage Contract is frozen. For v0.1 this is acceptable if those files are not edited during the episode; a later framework version should freeze/hash the full contract bundle.
- `publish_round()` should eventually defend against unrelated staged changes in the control checkout (or use path-limited commit semantics).
- Reviewer isolation remains “persistent modifications detected”, not a true read-only sandbox; this is already documented accurately.
- The 7200-second ZCode session timeout may be too short for some future scientific stages. Before a stage expected to exceed two hours, make timeout configurable rather than silently killing a valid GPU run.
- The final compact `CHECKPOINT.md` required by `CHECKPOINT_AND_PROMOTION.md` is not yet generated by the runner. This may be implemented during/before V3; it must exist before the V3 human scientific review, but it does not need to block starting V0.

## Decision

Decision: CHANGES_REQUESTED

Do not approve A0 or start V0 yet.

## Next action

Perform one focused A0-R3 rework addressing B14–B16 only.

After the new generic/live evidence is published, stop again for external review.

RESET_CONTEXT: NO
