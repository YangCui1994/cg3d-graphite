# Bilateral Imbibition Scientific Development Episode v0.1

Status: experimental planning package. This package defines the first long-running local ZCode executor/reviewer episode for cg3d-graphite.

## Purpose

The first episode deliberately stops before the real graphite + PCS production problem. It validates the autonomous development loop and the numerical regime using controlled synthetic geometries.

The sequence is:

A0. bootstrap a lightweight local Episode Runner;
V0. establish the existing CG3D regression baseline on the Windows GPU machine;
V1. validate single-front spontaneous capillary filling;
V2. validate symmetric bilateral spontaneous imbibition and opposing-front interaction in a simple resolved channel;
V3. test finite-liquid-buffer sensitivity and closed-wall artefacts;
mandatory human/scientific checkpoint.

Only after that checkpoint should a second porous-media episode introduce real graphite geometry, variable interface gap, separator bounce-back, optional PCS geometry, production simulations, post-processing, and visualization.

## Authoritative references

Planning/control branch base:
- agent-dev/step0-protocol at 9900845c0c480e8b5167adf6432ad49e3bf7457b

Initial product execution base:
- master at 9ede55c8ef7589b61606e11c033c84d9bcd1de94

Evidence package:
- agent-task/ADS-BILATERAL-EVIDENCE-001
- evidence commit bdbebb2a16b340deb79298f6230af4d50d9c6f5a

The evidence package is input to this contract, not a substitute for the stage-specific acceptance rules.

## Files

- EPISODE_PLAN.md — global scientific and orchestration contract.
- RUNNER_BOOTSTRAP.md — minimum runner required before autonomous execution.
- EXECUTOR_CONTRACT.md — executor role and output contract.
- REVIEWER_CONTRACT.md — fresh-context reviewer role and decision contract.
- STAGE_V0_BASELINE.md — existing regression baseline.
- STAGE_V1_DYNAMIC_WETTING.md — single-front Lucas-Washburn verification.
- STAGE_V2_BILATERAL.md — symmetric two-front verification.
- STAGE_V3_BUFFER_SENSITIVITY.md — finite-buffer sensitivity.
- CHECKPOINT_AND_PROMOTION.md — promotion, rework, escalation, and durable checkpoint rules.
- ARCHITECTURE.md / ARCHITECTURE.svg — human-readable system diagram.
- GPT6_AUDIT_PACKAGE.md — what to preserve for a later framework-level GPT-6 Pro audit.

## Non-goal

This package does not authorize the real porous-media/PCS production episode and does not authorize merging any scientific change to master.
