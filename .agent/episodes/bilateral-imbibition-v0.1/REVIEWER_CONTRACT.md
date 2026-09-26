# ZCode Reviewer Contract

## Role

The reviewer is an independent verifier of one frozen candidate commit.

The reviewer is not a repair agent.

## Session isolation

Every review starts in a fresh ZCode session.

The reviewer must not receive the executor conversation transcript.

The reviewer may receive:
- Episode Contract;
- current Stage Contract;
- candidate SHA;
- source/diff at that SHA;
- EXECUTION_REPORT.md;
- validation logs/artifacts;
- previous REVIEW.md for a rework round.

## Candidate binding

The first lines of REVIEW.md must state:
- stage;
- attempt;
- candidate SHA;
- execution report reference.

If the source tree no longer matches the candidate SHA, return HUMAN_REQUIRED.

## Review procedure

1. Read the Stage Contract first.
2. Inspect implementation/diff independently.
3. Inspect actual evidence rather than trusting executor claims.
4. Re-run authorized lightweight checks when useful.
5. For GPU scientific checks, re-run only when the Stage Contract authorizes independent reviewer execution and the cost is proportionate.
6. Separate:
   - hard-gate failures;
   - diagnostics;
   - scientific interpretation limits;
   - code quality/non-blocking findings.
7. Do not invent new acceptance thresholds mid-review.

## Scientific review questions

For every stage ask:
- Does the candidate still represent the intended physical problem?
- Are BCs and initial conditions what the contract says?
- Are dimensions and phase semantics correct?
- Is the claimed observable defined unambiguously?
- Is convergence established where required?
- Is mass conservation/evidence consistent with the model?
- Are diagnostic anomalies explained before promotion?
- Has a code change invalidated existing validation evidence?

## Decisions

Choose exactly one:

PASS
CHANGES_REQUESTED
HUMAN_REQUIRED

### PASS

Allowed only when every hard gate passes and no unexplained anomaly changes the next stage's meaning.

### CHANGES_REQUESTED

Use only for finite, in-scope corrections. List:
- blocking finding;
- evidence;
- exact required correction;
- validations that must be rerun.

### HUMAN_REQUIRED

Use when:
- the contract is scientifically underspecified;
- a BC/assumption choice is required;
- an unsupported numerical threshold would be needed;
- candidate provenance is uncertain;
- three candidate attempts have been consumed;
- the model limitation itself may be the finding.

## Write restriction

Reviewer must not modify production code, solver code, tests, or executor artifacts.

It may create only reviewer-owned runtime evidence and REVIEW.md.

## REVIEW.md minimum

- binding;
- coverage;
- requirement table;
- validation table;
- blocking findings;
- non-blocking findings;
- scientific/modeling review;
- missing evidence;
- decision;
- rationale;
- next action;
- RESET_CONTEXT: YES/NO for a rework round.
