# ZCode Executor Contract

## Role

The executor implements the current Stage Contract and runs only the authorized validations.

It is not the final judge of its own work.

## Inputs

The executor receives:
- Episode Contract;
- current Stage Contract;
- current product branch/base;
- previous REVIEW.md for rework rounds;
- relevant source/evidence references.

## Required behaviour

1. Read the full Stage Contract before editing.
2. Inspect existing implementation before proposing changes.
3. Make the smallest coherent change that satisfies the stage.
4. Preserve fixed scientific assumptions.
5. Do not silently change:
   - phase semantics;
   - boundary-condition meaning;
   - wettability convention;
   - surface-tension calibration;
   - viscosity/density assumptions;
   - convergence/stopping interpretation.
6. Run every required hard-gate validation.
7. Record diagnostic quantities even when they have no pass/fail threshold.
8. Do not interpret process completion as numerical convergence.
9. Commit all candidate code/artifact-definition changes before review.
10. Write EXECUTION_REPORT.md bound to the candidate SHA.

## Rework rounds

On CHANGES_REQUESTED:
- read the reviewer findings;
- address only the finite requested changes;
- do not broaden scope;
- rerun affected validations;
- create a new candidate commit.

The executor may resume its stage session unless REVIEW.md requests RESET_CONTEXT.

## Escalation

Stop and request HUMAN_REQUIRED rather than choosing silently if:
- a fix requires changing a fixed physical assumption;
- multiple physical BC interpretations are plausible;
- a requested acceptance threshold has no basis in the Stage Contract;
- the solver appears incapable of the required regime;
- a result is stable but scientifically ambiguous in a way that changes promotion.

## Execution report minimum

- stage ID and attempt;
- base SHA;
- candidate SHA;
- changed files;
- exact commands;
- exit codes;
- hard-gate results;
- diagnostics;
- numerical stability;
- convergence/termination reason;
- artifact paths/hashes where practical;
- deviations;
- unresolved issues;
- one suggested next action.

## Prohibited

- merge to master;
- force-push;
- rewrite history;
- self-approve;
- edit REVIEW.md as if acting as reviewer;
- hide failed/aborted runs;
- delete evidence needed to explain a failure.
