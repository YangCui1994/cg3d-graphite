# START — BI-CG-LECLAIRE-IMPLEMENTATION-001 — DeepSeek Executor

You are the executor for the isolated Leclaire/Latt CG research branch.

## Sync

Read from control branch:
`agent-dev/bilateral-episode-v0.1`

Read in full, in this order:

1. `.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_REFERENCE_SET.md`
2. `.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_IMPLEMENTATION_CONTRACT.md`
3. `docs/research/bilateral_imbibition/PALABOS_LECLAIRE_CODE_TRACE.md`
4. `.agent/evidence/BI-COLOUR-CLOSURE-001/EXTERNAL_SCIENTIFIC_REVIEW_PASS.md`
5. `docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`
6. `AGENTS.md`

## Product branch

Use the already-created branch:

`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`

It is based exactly on:

`6c30260dfe0c8b61ea9609e6bffa5c487312cf06`

Do not merge the control branch into the product branch.

## Literature

Use the already-working **科研通** workflow and the DOI list in
`LECLAIRE_REFERENCE_SET.md`.

No local download path is prescribed by this task.

## Execution order

1. Complete paper formulation and equation mapping.
2. Commit them with a `formulation:` commit.
3. Only then implement the isolated candidate.
4. Commit implementation/tests with an `implementation:` commit.
5. Run the bounded canonical validation matrix.
6. Commit evidence with a `validation:` commit.
7. Prepare:
   `.agent_runtime/BI-CG-LECLAIRE-IMPLEMENTATION-001/REVIEW_REQUEST.md`
8. STOP.

Do not self-review.
Do not modify `lbm_solver_cg3d.py`.
Do not execute V3 or graphite/PCS work.

Final response must include:
TASK, STATUS, PRODUCT_BRANCH, BASE, CANDIDATE, formulation commit,
implementation commit, validation commit, output paths, and
NEXT_ACTION = fresh DeepSeek review.
