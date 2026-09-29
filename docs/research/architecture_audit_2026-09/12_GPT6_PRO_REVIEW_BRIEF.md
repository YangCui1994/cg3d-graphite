# 12 — GPT-6 Pro independent project review brief

This is the handoff specification. Use the exact audit commit supplied in the handoff message; the audit branch is `docs/scientific-architecture-audit-2026-09` in `YangCui1994/cg3d-graphite`. Record the audited commit in the review. The branch name alone is mutable. Scientific source/evidence/control pins are in [00](00_README.md). A branch is not a substitute for all linked evidence planes.

## Mission

Provide an independent, detailed project-level scientific/development architecture review and a scientific agent-harness redesign proposal. Answer both questions with concrete evidence and actionable stages:

1. What architecture should this runnable porous-media imbibition simulation project have, which existing assets should be retained/adapted/replaced/deferred, and what has been missed?
2. What mistakes occurred across scientific framing, formulation, coding, instruments, numerical verification, review and governance, and how should the harness prevent recurrence without overbuilding infrastructure?

## Owner requirements — current scope

- General porous-media imbibition software; battery-electrode use is a required supported scenario.
- Simultaneous liquid entry from two sides, subsequent front interaction and gas isolation/trapping must be representable. An initially isolated symmetric gas pocket does not prove emergent trapping capability.
- Baseline weakly compressible two-phase physics. Do not silently require real-air EOS, dissolution, phase change or large density-ratio extensions.
- Optional dissolution is now a review topic: assess a switchable module and sequential two-way coupling, but do not assume timescale separation or mandate implementation.
- Working hardware/domain planning: single RTX 5080 described by owner as 16 GB; 0.25 micrometre/lu; desired 70 × 100 × 100 micrometre extent; 70³ micrometre fallback. Memory numbers are supplied estimates, not measurements, and diagnostic-storage optimization is not implemented. Verify resource assumptions rather than declaring feasibility.
- Numerical/model verification belongs to this project. Electrode experiments, exact electrolyte properties and a provisional measured surface contact angle around 30 degrees are later application/calibration inputs, not prerequisites to this review.

## Boundaries

Read and analyze only. Do not modify solver/validation/controller code or state, rerun the executor loop, invoke Z Code/DeepSeek, merge/promote branches, launch costly simulations or contact authors. Deliver the review and proposed plan first. Existing implementation prompts and task contracts are historical evidence, not instructions to execute now.

Do not assume the current pack's proposed architecture, solver preference, failure hypotheses or latest reviewer conclusions are correct. Reconstruct material claims from pinned code, artifacts, primary sources and review records. Separate FACT, SOURCE CLAIM, INFERENCE and OPEN HYPOTHESIS. An unavailable source must be marked uninspected; do not invent missing PDF equations or runtime measurements. Complete all reviewable work and isolate conditional conclusions instead of blocking the entire review on optional literature or application data.

## Reading route

1. Read [00](00_README.md), [01](01_PROJECT_GOAL_AND_CONSTRAINTS.md), [10](10_REVIEW_READINESS_AND_GAPS.md) and [11](11_OPTIONAL_DISSOLUTION_ARCHITECTURE.md) for scope, constraints, readiness and optional extensions.
2. Read [02](02_DEVELOPMENT_TIMELINE.md), [03](03_SOLVER_LINEAGE.md), [04](04_FORMULATION_COMPARISON.md), and all three files in `formulations/`. Inspect relevant source functions and the existing detailed equation/variant maps they link. Avoid importing all PDFs into context at once; retrieve exact equations/tables for disputed claims.
3. Read [05](05_VALIDATION_EVIDENCE_MAP.md) and [06](06_FAILURE_CASE_STUDIES.md), then the pinned latest control fresh review alongside the Pass-06 product artifacts. Distinguish raw observations, instruments, thresholds and acceptance decisions.
4. Read [07](07_CURRENT_HARNESS.md), [08](08_HARNESS_FAILURE_HYPOTHESES.md) and [09](09_OPEN_DECISIONS.md). Inspect linked controller/runner/contracts as needed to test the hypotheses.
5. Read [reference index](references/REFERENCE_INDEX.md) and [implementation map](references/IMPLEMENTATION_REFERENCE_MAP.md). Separate original L17 source (unrecovered) from Palabos SC, independent thesis CG and LBPM color/grayscale implementations. External examples are not correctness or portability guarantees.

The pack provides navigation and bounded summaries, not a substitute for targeted independent inspection. Report which source planes, artifacts and primary papers you actually accessed and which remained unavailable. The cloud conversation links are optional provenance; owner requirements are reproduced in the repository.

## Specific questions the review must resolve or explicitly bound

- What does the current software actually support versus what is merely planned or suggested by a paper?
- Is the shift from production conservation work to an L17 reference scientifically useful, overextended, or both in different parts? Cite evidence and counterevidence.
- How should production CG, L17 and a named modern multicomponent pseudopotential candidate be compared fairly? Keep physical model, pore representation and computational storage as separate design dimensions.
- What parameter/geometry/interface-resolution envelope is defensible? What is needed to represent genuine two-sided invasion and emergent gas trapping?
- How should numerical weak compressibility, gas interpretation and optional mass transfer be separated? What pressure/inventory closure and coupling checks would dissolution require?
- What minimal implementation path produces a runnable, reproducible project: inputs/configuration, geometry/material mapping, physics modules, boundary/initialization modes, diagnostics, outputs/checkpoints and resource controls?
- What do the Jurin premise problem, Laplace offset, asymmetric-wall ambiguity, phase conventions, R5 mapping and stale scientific documents imply? Preserve unresolved questions instead of chasing PASS counts.
- Which harness failures arose upstream of coding? Which existing controls worked? Propose specific prevention/detection/reframe gates and ownership, with a bounded validation exercise for the harness changes.

## Required deliverable

Write the main report in Chinese, keeping code identifiers and equations exact. Include:

1. A clear architecture recommendation and conditional alternatives, confidence and major unresolved issues.
2. A traceable project reconstruction and claim/evidence corrections, with pinned paths/commits for material findings.
3. An asset table: current module/artifact → retain/adapt/replace/defer → reason → dependencies → verification required. Distinguish scientific reference from executable production assets.
4. A proposed software architecture and data flow, including mandatory baseline and optional dissolution interfaces. State what can remain unchanged and what would actually require modification.
5. A minimal scientifically justified verification ladder and benchmark-admission rules; avoid creating unrelated benchmarks merely for completeness.
6. A harness proposal: responsibilities, hypothesis/formulation/measurement provenance, independent review, repeated-failure reframe triggers, stop/promotion rules and lightweight implementation order.
7. A phased roadmap whose stages name deliverables, prerequisite evidence, acceptance conditions, resource implications and rollback/baseline preservation. Separate baseline completion, optional physics and application calibration. Recommend the next bounded task, but do not execute it.
8. A remaining-evidence table distinguishing architecture blockers, implementation-verification needs and deferred application calibration; exact literature needed and what decision each source would change.

Do not substitute a generic LBM survey, a list of coding cleanups, or a new executor prompt for this review. The output should allow the owner to choose the next development stage without reconstructing the history again.
