stage: A0
attempt: 4
candidate: 83577f0d670958c7550227d6a0682ccce80a9852
execution_report: .agent/evidence/BI-VALIDATION-001/A0_SMOKE_R3/A0_R3_EVIDENCE.md

# A0 External Review R4 — PASS

## Binding

- **Approved runner implementation:** `83577f0d670958c7550227d6a0682ccce80a9852`
- **Evidence index:** `.agent/evidence/BI-VALIDATION-001/A0_SMOKE_R3/A0_R3_EVIDENCE.md`
- **Evidence/control branch head inspected:** `872b2c3103cd919615e19fb455dfdaf31b5eddfd`
- **Remote smoke product branch:** `agent-episode/BI-VALIDATION-001-smoke-r3`
- **Remote smoke product HEAD verified:** `aed0fdeeb00563a49c036b286a27f28a48c721d9`
- **Review mode:** external planner-level review
- **Prior external reviews:** R1, R2, R3 under the corresponding A0 evidence directories

The control/evidence commits after `83577f0...` do not modify
`.agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py`.
The runner file therefore remains byte-identical, by Git blob identity,
to the implementation exercised by the R3 live smoke.

## Review scope

This review intentionally does not reopen framework-hardening topics that
were explicitly made non-blocking in R3. It checks only whether the A0
runner is safe enough to authorize the first V0->V3 scientific validation
episode under the current v0.1 contract.

## Closure of R3 blocking findings

### B14 — publication-safe promotion

**Resolved.**

The generic engine now uses a two-phase round completion protocol:

1. reviewer decision is parsed and persisted as `PUBLISH_PENDING`;
2. product branch + durable evidence are published;
3. only after publication succeeds is the decision appended/applied and
   PASS/rework/HUMAN_REQUIRED promotion performed.

If publication fails, the stage becomes `ERROR/publish_pending` and the
next stage is not exposed. Recovery re-validates the frozen candidate +
review binding and retries publication without rerunning executor or
reviewer sessions.

Offline S19a-e covers product-push failure, control-side publication
failure, persisted restart, publication-only recovery, and terminal-stage
failure. The live R3 smoke shows normal decision->publish->apply ordering.

### B15 — valid executor with dirty pre-review state

**Resolved.**

A valid executor session that leaves the product worktree dirty is now
treated as a terminal pre-review provenance ambiguity:

- HUMAN_REQUIRED;
- orphan state recorded;
- no candidate accepted;
- evidence-only publication;
- ambiguous/unreviewed product state is not pushed;
- retry cannot silently adopt the dirty/unreviewed HEAD as a new base.

Offline S20a-c directly covers this path.

### B16 — approved harness identity

**Resolved.**

A0 approval now freezes the Git blob identity of the reviewed
`episode_runner.py` implementation. Real entry points and real loop
continuation verify that the executing runner file matches the approved
blob.

The identity is persisted in `approved_runner` and is included in real
stage records. A changed runner requires a new A0 smoke + external review.

Offline S21a-c covers approval, allowed unchanged execution, and refusal of
a changed runner implementation.

## Cross-checks

### Generic-path equivalence

The R3 live smoke uses the same generic `start_stage / run_round /
run_episode / publish_round` engine intended for V0-V3.

### Reviewer isolation

Each review session is fresh. Executor rework may resume the stage executor
session. Candidate SHA binding and persistent reviewer-product-modification
detection remain intact.

### Product provenance

The R3 product branch exists remotely and resolves to the final reviewed
smoke candidate:

`agent-episode/BI-VALIDATION-001-smoke-r3 -> aed0fdeeb00563a49c036b286a27f28a48c721d9`

Thus durable evidence no longer points only to local-only candidate SHAs.

### Contract provenance

Stage contracts are frozen into runtime snapshots and hashed at stage
start. Executor/reviewer sessions consume the frozen snapshot; publication
copies those same frozen bytes. Control-plane drift is recorded rather
than followed.

### Failure behaviour

The current generic tests and live history cover the main unattended-run
failure classes required before V0:

- executor/reviewer process failure;
- timeout/missing artifact;
- stale artifact;
- failed executor leaving an orphan commit;
- valid executor leaving a dirty tree;
- failed reviewer with frozen candidate retry;
- publication/push failure;
- max-attempt escalation;
- HUMAN_REQUIRED stop;
- persisted ERROR stop;
- worktree HEAD mismatch;
- approved-runner mismatch.

## Non-blocking items retained for later framework hardening

These remain useful improvements, but do not block V0:

- freeze/hash the complete global contract bundle, not only the Stage Contract;
- stronger reviewer filesystem sandbox beyond post-session detection;
- path-isolated control-plane evidence commits;
- stage-specific configurable long-run timeout;
- automatic final compact `CHECKPOINT.md` generation before the V3 human review;
- formal `SYSTEM_INVARIANTS.md` / guarantee classification
  (ENFORCED / DETECTED / CONVENTION / DIAGNOSTIC).

These can be incorporated into the later framework-level cleanup without
reopening A0 unless they change the runner implementation.

## Authorization boundary

This PASS authorizes the runner infrastructure for the already-defined
validation episode only:

`V0 -> V1 -> V2 -> V3 -> mandatory CHECKPOINT_READY`

It does **not** authorize automatic promotion into the real graphite /
interface-gap / PCS porous-media episode.

The scientific Stage Contracts and their reviewers remain authoritative for
whether each V-stage passes.

## Decision

Decision: PASS

## Next action

Use this review as the explicit A0 approval input.

Then:

1. run `approve-a0 --review <this file>`;
2. verify status reports `A0_APPROVED`;
3. start the real episode with `run-episode`;
4. allow the runner to execute/review/promote V0->V3 autonomously;
5. stop on ERROR, HUMAN_REQUIRED, or V3 CHECKPOINT_READY;
6. do not start the porous-media/PCS episode before the V3 external scientific review.

No further A0 rework is required for v0.1.
