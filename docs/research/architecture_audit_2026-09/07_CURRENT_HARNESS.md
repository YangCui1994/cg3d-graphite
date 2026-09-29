# 07 — Current harness: observed architecture

This is an inventory at control snapshot `dddac98`, not a claim about a currently running Windows process. No controller or runner was launched; no live state was changed.

## Two orchestration layers, not one uniform loop

| Layer | Source | Observed contract / code responsibilities |
|---|---|---|
| Generic V1 controller | [protocol](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/README.md), [controller](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/controller/controller.py) | explicit execution base; Git claim/push; bounded rounds; changed-path checks; process/evidence capture; PASS meaning left to review |
| Scientific episode runner | [episode plan](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/EPISODE_PLAN.md), [runner](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/runner/episode_runner.py) | fresh review sessions; frozen candidate; contract snapshots; bounded rework; publication checkpoints; stop after V3 |
| Human / ChatGPT scientific governance | [architecture](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/ARCHITECTURE.md), [promotion contract](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/CHECKPOINT_AND_PROMOTION.md) | scientific stage definitions, external reviews, modeling decisions and promotion boundaries |
| Later task-specific work | [L17 contract](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_IMPLEMENTATION_CONTRACT.md), [wetting closure contract](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_WETTING_CLOSURE_CONTRACT.md) | isolated product branch, source fidelity and progressively stronger validation/evidence rules |

Generic controller states include DRAFT, READY_FOR_EXECUTION, RUNNING, AWAITING_REVIEW, CLOSED, HUMAN_REQUIRED and ERROR. Episode states and PASS promotion are specified separately. Do not interpret an old `.agent/state.json` as a full record of all subsequent scientific work.

## Existing strengths worth preserving

**FACT / documented design:** fresh reviewer context excludes executor transcript; reviews bind to candidate SHA; later source changes invalidate prior acceptance; contracts distinguish code, numerical and physical correctness; no automatic master merge; explicit owner boundary before real porous-media work; changed-file and provenance checks; finite attempt budgets.

**SOURCE CLAIM:** stored smoke/review records exercise role isolation and publication; this audit has not rerun the harness tests. The latest Pass-6 review reports exact frozen-source reproducibility. Independent review demonstrably found physics-premise and measurement problems that earlier pass counts had not settled.

## Important boundaries and limits

The generic V1 publication bundle is documented as at most 20 files, 1 MiB/file and 5 MiB total with restricted extensions; later raw NPZ case artifacts use a different publication path. These are different mechanisms, not evidence that NPZ must fit the earlier controller envelope.

The original episode allowed at most three candidate attempts per stage. Later task/review sequences exist, including multiple separately named L17 passes. **OPEN:** whether overall research effort was effectively bounded across renamed stages requires a stage-to-question ledger; commit count alone does not prove a limit was bypassed.

[DeepSeek transition planning](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/DEEPSEEK_TRANSITION_CONTRACT.md) exists historically and is explicitly not a V3 execution contract. Its existence is not authorization to use that model or continue the loop now.

## What the present audit cannot establish

No live controller configuration, running-process inventory, full latency/token/cost ledger, or complete external working-tree synchronization was inspected. No causal ranking of model vendors follows from this history. The narrower concern is whether contracts and review instruments asked the right scientific question early enough; [08](08_HARNESS_FAILURE_HYPOTHESES.md) makes that falsifiable.
