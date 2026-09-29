# START — BI-VALIDATION-001 V0→V3

This file is the **single execution entry point** for the first real bilateral-imbibition validation episode.

Do not redesign the workflow. Do not modify the runner. Do not start the porous-media/PCS episode.

## 1. Control branch

Use the control checkout on:

`agent-dev/bilateral-episode-v0.1`

Fetch/pull this branch with fast-forward only before execution.

The approved runner implementation is:

`83577f0d670958c7550227d6a0682ccce80a9852`

Later commits on the control branch are evidence/launch documents only. The runner file must remain blob-identical to the approved implementation.

## 2. Read before execution

Read these files in full:

1. `.agent/episodes/bilateral-imbibition-v0.1/EPISODE_PLAN.md`
2. `.agent/episodes/bilateral-imbibition-v0.1/EXECUTOR_CONTRACT.md`
3. `.agent/episodes/bilateral-imbibition-v0.1/REVIEWER_CONTRACT.md`
4. `.agent/episodes/bilateral-imbibition-v0.1/CHECKPOINT_AND_PROMOTION.md`
5. `.agent/evidence/BI-VALIDATION-001/A0_SMOKE_R3/A0_EXTERNAL_REVIEW_R4_PASS.md`

Stage contracts are frozen by the runner when each stage begins.

## 3. A0 approval

Run:

```powershell
python .agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py approve-a0 --review .agent/evidence/BI-VALIDATION-001/A0_SMOKE_R3/A0_EXTERNAL_REVIEW_R4_PASS.md
```

Then run:

```powershell
python .agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py status
```

Required state before real execution:

`episode_status = A0_APPROVED`

If approval is refused, stop. Do not bypass the gate and do not edit the runner.

## 4. Start the real episode

Run:

```powershell
python .agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py run-episode
```

The runner owns all stage transitions and ZCode Executor/Reviewer sessions.

Expected autonomous sequence:

```text
V0 existing baseline
  -> fresh reviewer
V1 single-front dynamic wetting
  -> fresh reviewer
V2 bilateral symmetric front interaction
  -> fresh reviewer
V3 finite-buffer sensitivity
  -> fresh reviewer
CHECKPOINT_READY
```

Do not manually start V1/V2/V3 after a PASS. Promotion is runner-owned.

## 5. Stop conditions

If the runner ends with any of the following, stop and do not improvise:

- `ERROR`
- `HUMAN_REQUIRED`
- `CHECKPOINT_READY`

For `ERROR` or `HUMAN_REQUIRED`, do not change scientific assumptions, boundary conditions, acceptance thresholds, or runner logic unless a later external instruction explicitly authorizes it.

For `CHECKPOINT_READY`, do not start graphite / gap / separator / PCS work.

## 6. Git rules

- Never merge to `master`.
- Never force-push.
- Never rewrite history.
- Do not manually create an alternate episode branch.
- Let the runner create/manage `agent-episode/BI-VALIDATION-001`.
- Preserve all runner-published evidence and candidate refs.
- Do not modify `episode_runner.py` during this episode.

## 7. Scientific scope

This execution is validation only.

Authorized stages:
- V0 baseline regressions
- V1 resolved single-front spontaneous capillary filling
- V2 resolved symmetric bilateral imbibition
- V3 finite-buffer sensitivity

Not authorized:
- real graphite porous-media production run
- configurable 5/10/20 µm interface-gap production matrix
- separator/PCS production geometry
- final battery-process interpretation

## 8. Final console response

When the runner stops, respond only with:

```text
EPISODE: BI-VALIDATION-001
STATUS: ERROR | HUMAN_REQUIRED | CHECKPOINT_READY
CURRENT_STAGE: <stage>
PRODUCT_BRANCH: <branch>
PRODUCT_HEAD: <sha>

STAGE_STATUS:
- V0: <status>
- V1: <status>
- V2: <status>
- V3: <status>

PRIMARY_EVIDENCE:
<path to the most relevant published stage/checkpoint evidence>

NEXT_ACTION:
External review required.
```

Do not reproduce long logs or scientific results in the console response. GitHub evidence is authoritative.

## 9. Controller note

Do **not** modify the legacy `.agent/controller/` during this episode.

After the V0→V3 episode produces real execution history, controller integration will be handled as a separate architecture task. The intended future direction is to reuse the proven episode invariants rather than merge the old Controller and Episode Runner ad hoc.
