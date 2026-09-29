# Scientific architecture audit pack — September 2026

Prepared 2026-09-29 using ChatGPT reasoning and read-only repository inspection. This is **review input, not a replacement scientific source-of-truth, acceptance decision, or execution contract**. No solver, validation, controller, or existing evidence changes are part of this pack. No Z Code / DeepSeek invocation or executor-loop continuation was used.

## Questions for the architecture reviewer

1. Reconstruct the research/development architecture for battery-electrode imbibition and trapped gas. Identify assets to retain, claims to narrow, missing physics/measurements, and a staged research roadmap. Compare production CG, L17 CG, and a specifically identified modern pseudopotential candidate without presuming a winner.
2. Explain which historical failures arose from implementation, benchmark premises, instruments, evidence handling, or research governance. Propose a scientific-development harness with explicit decision ownership, falsification and reframe gates; distinguish proposed design from demonstrated causes.

The earlier control-branch [GPT6_AUDIT_PACKAGE](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/GPT6_AUDIT_PACKAGE.md) was narrower (framework audit after an episode). The current owner request explicitly expands the review to scientific architecture. That older document is historical input, not the scope of this audit.

## Frozen evidence boundary

| Plane | Inspected snapshot | Role |
|---|---|---|
| Production | `6c30260dfe0c8b61ea9609e6bffa5c487312cf06` | accepted colour-closure baseline in control records |
| L17 executable source | `9773a439f9f994225ce6515bd9f755815aa2c5af` | Pass-06 frozen solver + validation harness |
| L17 package | `5dca114bc40c40743029a9439101958b13eaf721` | Pass-06 evidence and science docs; parent is frozen source |
| Control / reviews | `dddac98d16bb4b792a371fe4d74276aba702038b` | bilateral episode contracts, harness, latest fresh review |
| Default branch observed | `9ede55c8ef7589b61606e11c033c84d9bcd1de94` | not the current L17 or control state |

The pack is based on the L17 package, on a separate documentation branch. Cross-plane links use full commit SHAs; opening only `master` or only the L17 branch loses material evidence. Local links within this pack are navigation; external GitHub links pin the source statements.

**Critical conflict:** the published Pass-06 matrix reports 8 PASS / 3 FAIL_SOLVER. The later [Pass-6 fresh review](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/evidence/BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001/FRESH_REVIEW.md) requests changes: classical Jurin theory is inappropriate for the unit-density, mixture-forced setup; case-09 attribution remains unresolved; document/provenance issues remain. Do not equate the matrix labels with the latest scientific acceptance decision.

## Reading order and file inventory

1. [01 — Goal and constraints](01_PROJECT_GOAL_AND_CONSTRAINTS.md), [02 — Timeline](02_DEVELOPMENT_TIMELINE.md), [03 — Solver lineage](03_SOLVER_LINEAGE.md).
2. [04 — Formulation comparison](04_FORMULATION_COMPARISON.md), then [production CG](formulations/PRODUCTION_CG.md), [L17 CG](formulations/L17_CG.md), and [Shan–Chen](formulations/SHAN_CHEN.md). Follow detailed equation sources only where needed.
3. [05 — Evidence map](05_VALIDATION_EVIDENCE_MAP.md) and [06 — Failure cases / inconsistencies](06_FAILURE_CASE_STUDIES.md). Read the latest control review alongside the product report.
4. [07 — Current harness](07_CURRENT_HARNESS.md), [08 — Harness hypotheses](08_HARNESS_FAILURE_HYPOTHESES.md), [09 — Open decisions](09_OPEN_DECISIONS.md).
5. [Reference index and acquisition queue](references/REFERENCE_INDEX.md). PDFs are verification sources; existing extractions are the first reading layer.

## Evidence vocabulary

- **FACT:** directly inspected code, Git relationship, file content, or stored number. A recorded PASS is a fact about a record, not universal physical validation.
- **SOURCE CLAIM:** an existing report/reviewer/paper attribution; link it and preserve its scope. This audit did not rerun its simulations or independently re-extract its PDFs.
- **INFERENCE:** reasoning from identified facts, with assumptions and limits stated.
- **OPEN HYPOTHESIS / PROPOSAL:** requires additional evidence or an owner decision; not an accepted change.

Prefer source papers for what a paper says, frozen code for what executes, raw artifacts for what was measured, and dated review records for acceptance. Do not resolve contradictions solely by a document's self-declared authority.

## Completion and limits

All 14 requested files are supplied. Inspection covers selected product/control documentation, solver operators, validation code and summaries, representative reviews, and Git ancestry/diffs. No simulation or benchmark rerun, no complete PDF audit, no exhaustive review of every historical branch, and no inspection of live Windows runtime state was performed. Literature discovery was bounded to identifying primary/review sources needed for the comparison, not claiming a systematic survey through 2026. Existing scientific evidence remains intact.

Static delivery checks: 14 requested Markdown files; 24 internal links and 60 distinct commit-pinned source-file links resolve; ancestry and empty production/source-harness diffs verified; only this audit directory is added. No benchmark was rerun for these checks.

Suggested review output: (a) claim/evidence corrections, (b) retain/adapt/replace/defer asset decisions, (c) alternative scientific routes with selection criteria, (d) proposed harness architecture and minimum implementation sequence, (e) unresolved owner decisions. Do not authorize a port or production promotion merely by finishing this review.
