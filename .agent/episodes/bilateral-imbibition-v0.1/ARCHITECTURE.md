# Episode v0.1 Architecture

## Human-readable flow

~~~mermaid
flowchart TD
    H[You + ChatGPT<br/>Scientific planner] --> P[Episode Plan + Stage Contracts<br/>agent-dev/bilateral-episode-v0.1]
    P --> A0[A0: Lightweight Episode Runner bootstrap]
    A0 --> HC0[One external harness checkpoint]
    HC0 --> R[Windows Episode Runner]

    R --> V0[V0 Existing baseline]
    V0 --> E[ZCode Executor<br/>stage session]
    E --> C[Candidate commit<br/>frozen SHA]
    C --> RV[Fresh ZCode Reviewer<br/>no executor transcript]
    RV --> D{Decision}

    D -->|CHANGES_REQUESTED| E2[Executor rework<br/>resume or fresh]
    E2 --> C
    D -->|HUMAN_REQUIRED| STOP[Stop + publish checkpoint]
    D -->|PASS| NEXT{Next stage?}

    NEXT -->|after V0| V1[V1 Dynamic wetting / Lucas-Washburn]
    NEXT -->|after V1| V2[V2 Bilateral simple channel]
    NEXT -->|after V2| V3[V3 Finite-buffer sensitivity]
    NEXT -->|after V3| CP[Mandatory CHECKPOINT_READY]

    V1 --> E
    V2 --> E
    V3 --> E

    CP --> H2[You + ChatGPT<br/>Scientific milestone review]
    H2 --> F[Future Porous-Media Episode<br/>Graphite + Gap + Separator BB + optional PCS]

    CP -. preserved run evidence .-> G6[Later GPT-6 Pro framework audit]
    P -. framework docs .-> G6
~~~

## Context isolation

Executor and reviewer can be the same underlying GLM model, but they are not the same session.

Reviewer gets:
- contract;
- frozen candidate SHA;
- diff/source;
- execution report;
- evidence;
- prior review for rework only.

Reviewer does not get executor transcript.

## Where GitHub fits

GitHub is the durable control/evidence plane, not the high-frequency inner loop.

High-frequency:
- local executor;
- local reviewer;
- local rework.

Durable publication:
- stage PASS;
- HUMAN_REQUIRED;
- crash checkpoint;
- final V3 checkpoint.

## Why the first episode stops at V3

The first episode must separate:
- orchestration failures;
- dynamic-wetting failures;
- bilateral-interface failures;
- closed-buffer artefacts;

from:
- real graphite under-resolution;
- interface-gap geometry;
- PCS morphology;
- real porous topology.

Only after the controlled stages are understood should the large porous-media episode start.
