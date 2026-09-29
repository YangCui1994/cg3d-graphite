# Promotion, Rework, Escalation, and Checkpoint Contract

## Stage promotion

V0 PASS -> V1
V1 PASS -> V2
V2 PASS -> V3
V3 PASS -> CHECKPOINT_READY

No other automatic promotion is authorized.

## Rework loop

For each stage:

Attempt 1:
Executor E1 -> candidate C1 -> fresh Reviewer R1

If CHANGES_REQUESTED:
Executor E2 (resume E1 unless RESET_CONTEXT=YES) -> candidate C2 -> fresh Reviewer R2

If CHANGES_REQUESTED again:
Executor E3 -> candidate C3 -> fresh Reviewer R3

Any non-PASS after R3 -> HUMAN_REQUIRED.

## Required durable stage record

At PASS or HUMAN_REQUIRED publish:

- stage contract version/hash;
- execution base;
- accepted/rejected candidate SHA;
- EXECUTION_REPORT.md;
- REVIEW.md;
- validation command list;
- metric summary JSON/CSV where practical;
- plots needed to understand the result;
- artifact manifest;
- changed-files/diff summary;
- attempt history;
- session IDs for executor/reviewer provenance;
- unresolved diagnostics.

Raw multi-gigabyte simulation fields may remain local if the durable manifest records hashes and paths.

## Mandatory V3 checkpoint package

Create a compact entry document named CHECKPOINT.md containing:

1. Episode and source provenance.
2. V0 status and baseline environment.
3. V1:
   - geometry;
   - LW comparison;
   - fit window;
   - slope/prefactor error;
   - mass/stability diagnostics;
   - reviewer decision.
4. V2:
   - bilateral geometry;
   - symmetry metrics;
   - connectivity/isolation event;
   - mass diagnostics;
   - collision diagnostics;
   - reviewer decision.
5. V3:
   - buffer sweep;
   - normalized front-difference metrics;
   - wall/reflection diagnostics;
   - reviewer decision.
6. All provisional engineering thresholds used.
7. All diagnostics that intentionally lacked hard thresholds.
8. Scientific interpretation boundaries.
9. Deviations from the original Episode Contract.
10. Questions reserved for ChatGPT + user.
11. Recommended options for the next porous-media episode, without selecting one on the user's behalf.

## Human review questions after V3

The checkpoint should make it possible to answer:

- Is the dynamic wetting validation strong enough?
- Does bilateral symmetry hold before interaction?
- Does interface collision show a numerical artefact large enough to limit use?
- Does finite-buffer size materially influence invasion?
- Is closed-BB outer-boundary modelling still a useful baseline?
- Is unit-density trapped-phase behaviour acceptable for the intended topology/trapping questions?
- Which quantities from V2/V3 may become hard gates in the porous-media episode?
- Which must remain diagnostics only?

## Crash recovery

A crash is not PASS or FAIL.

Runner should preserve:
- last committed candidate;
- stage/attempt;
- executor session ID;
- last completed validation;
- local artifact manifest.

On restart, resume only when provenance is unambiguous. Otherwise stop HUMAN_REQUIRED.
