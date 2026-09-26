# BI-CG-LECLAIRE-IMPLEMENTATION-001 — Executor Contract

## 0. Task identity

Task ID: `BI-CG-LECLAIRE-IMPLEMENTATION-001`

Control branch:
`agent-dev/bilateral-episode-v0.1`

Product branch:
`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`

Exact product base:
`6c30260dfe0c8b61ea9609e6bffa5c487312cf06`

This task creates a **parallel research implementation line**. It is not a V3
subtask and it does not replace the accepted production CG solver.

## 1. Architectural boundary

The two solver lines are intentionally near-isolated.

### Frozen production line

The accepted solver at the base contains the current project production path,
including the accepted conservation work.

Do NOT modify:
- `lbm_solver_cg3d.py`;
- production defaults;
- accepted V0/V1c/V2 result files;
- accepted gates or thresholds;
- existing bilateral/V3 scientific interpretation.

### New Leclaire/Latt research line

Implement the Leclaire/Latt color-gradient family independently in new files.

The new line may reuse:
- algorithm-independent lattice constants/utilities when their equivalence is
  explicitly documented;
- validation definitions and metric formulas;
- test geometry generators when they do not encode current-CG-specific physics;
- conservation diagnostic methodology.

The new line must NOT inherit:
- current CG calibration constants as truth;
- current surface-tension/contact-angle/interface-width results;
- current recoloring semantics;
- current wetting semantics;
- T3/C1X/A2 corrections automatically.

If the same finite-precision defects appear, diagnose them first and add
conservation corrections as an explicit overlay, not as part of the paper-faithful
baseline.

## 2. Literature acquisition

Read:
`.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_REFERENCE_SET.md`

Use **科研通** with the listed DOI identifiers to obtain the papers and any
needed supplementary material.

This contract intentionally does not prescribe a local download path or a
specific command line. Use the already-working ZCode 科研通 workflow.

The mandatory DOI set is:
- `10.1103/PhysRevE.95.033306`
- `10.1142/S0129183117500851`
- `10.1016/j.advwatres.2018.03.014`
- `10.1155/2019/5176410`

Background if needed:
- `10.1016/j.compfluid.2011.04.001`

## 3. Phase A — paper formulation FIRST

Before changing implementation code, create and commit:

`docs/research/leclaire_cg/PAPER_FORMULATION.md`

This is an executable scientific specification, not a prose paper summary.

For every algorithmic element record:
- source DOI;
- exact paper equation / appendix / table identifier;
- D3Q19 specialization;
- all lattice weights and constants;
- operator ordering;
- variable definitions;
- parameter ranges / assumptions;
- wetting/solid-node handling;
- boundary-condition assumptions;
- whether the statement is explicit in the paper or inferred.

At minimum cover:
1. component densities and color/order parameter;
2. color-blind total distribution;
3. D3Q19 MRT collision;
4. viscosity interpolation;
5. color-gradient stencil / isotropic weights;
6. perturbation / interfacial-tension operator;
7. sigma-to-parameter relation;
8. Latva-Kokko recoloring;
9. explicit `beta` semantics and interface-width control;
10. wetting/contact-angle treatment;
11. solid bounce-back ordering;
12. any regularized/open boundary formulation relevant to the paper.

If an equation or implementation detail is unresolved, label it
`UNRESOLVED`. Do not fill gaps by intuition.

## 4. Phase B — equation-level mapping to current code

Create and commit:

`docs/research/leclaire_cg/CURRENT_VS_LECLAIRE_MAP.md`

Use one row per algorithmic element with exactly one status:

- `SAME`
- `MATHEMATICALLY_EQUIVALENT`
- `DIFFERENT`
- `MISSING`
- `UNRESOLVED`

`MATHEMATICALLY_EQUIVALENT` requires an explicit derivation.

In particular, if the current MRT stress-moment surface-tension formulation is
claimed equivalent to the paper perturbation operator, derive the mapping from
distribution-space perturbation to the moment basis. A successful Laplace test
alone is not proof of equivalence.

Also create:

`docs/research/leclaire_cg/FOLLOWUP_OPTIMIZATION_MAP.md`

For every later-paper change, state:
- baseline Leclaire-2017 behavior;
- follow-up source DOI;
- exact change;
- motivation;
- expected effect;
- whether it will be implemented now;
- a dedicated switch/ablation plan.

Do not collapse the papers into one undocumented "best" model.

## 5. Phase C — implementation plan gate

Create:

`docs/research/leclaire_cg/IMPLEMENTATION_PLAN.md`

The plan must separate at least:

### L17_CORE
Paper-faithful Leclaire-2017 D3Q19 implementation.

### Follow-up variants
Only directly justified improvements, each individually switchable.

At minimum consider:
- explicit-beta recoloring;
- later wetting treatment;
- later porous-media operator-ordering/handling if materially different.

### Conservation overlay
A distinct optional layer. Do not call an implementation paper-faithful if it
depends on project-specific conservation corrections not present in the source.

Only after these three formulation artifacts are committed may implementation
code be written.

## 6. Phase D — isolated implementation

Prefer new paths such as:

- `experimental/leclaire_cg/**`
- `tests/leclaire_cg/**`
- `results/leclaire_cg/**`
- `docs/research/leclaire_cg/**`

Do not modify `lbm_solver_cg3d.py`.

If a shared validation helper must be changed, first demonstrate that the
change is algorithm-independent and does not alter existing production results.

Implementation requirements:
- D3Q19 only in this task;
- one explicit mode for `L17_CORE`;
- later optimizations behind explicit switches;
- no silent production fallback;
- source DOI and equation references in code comments for nontrivial operators;
- no copied Palabos source.

## 7. Phase E — validation

Validation methodology may be shared with the current solver line, but the new
candidate must generate its own evidence.

### Required canonical tests

At minimum:
1. uniform single-phase stationarity;
2. planar interface stationarity;
3. Laplace droplet;
4. static contact angle;
5. interface-width measurement versus beta;
6. moving droplet or capillary-wave dynamic-isotropy test;
7. static slit capillary pressure;
8. simple capillary imbibition;
9. asymmetric complex-wall wetting killer test;
10. local/global total and component conservation audit.

### Complex-wall killer test

At least one wetting test must be asymmetric/non-cancelling so that artificial
wall-directed mass transfer cannot disappear through periodic symmetry.

Track:
- component mass near the wall;
- total component mass;
- contact-line/interface motion with no imposed pressure difference;
- spurious velocity;
- topology.

### Shared-validation rule

You may reuse:
- metric definitions;
- scripts after algorithm-independent verification;
- geometry generators;
- reporting format.

You may NOT reuse a prior PASS as evidence for this solver.

## 8. A/B structure

Where practical, report:

`CURRENT_PRODUCTION` vs `L17_CORE` vs each follow-up variant.

The goal is attribution, not forcing Leclaire to win.

Do not change existing production gates to make the new implementation pass.

## 9. Required outputs

### Research/specification
- `docs/research/leclaire_cg/PAPER_FORMULATION.md`
- `docs/research/leclaire_cg/CURRENT_VS_LECLAIRE_MAP.md`
- `docs/research/leclaire_cg/FOLLOWUP_OPTIMIZATION_MAP.md`
- `docs/research/leclaire_cg/IMPLEMENTATION_PLAN.md`
- `docs/research/leclaire_cg/REFERENCE_MANIFEST.md`

### Implementation
- isolated source under `experimental/leclaire_cg/**`
- isolated tests under `tests/leclaire_cg/**`

### Evidence
- `results/leclaire_cg/EXECUTION_REPORT.md`
- `results/leclaire_cg/PROVENANCE.md`
- `results/leclaire_cg/summary.json`
- machine-readable per-test outputs;
- machine-readable exit code for every executed test;
- committed scripts generating all reported headline metrics.

## 10. Commit discipline

Use at least three logical commits:

1. `formulation:` paper formulation + equation maps only;
2. `implementation:` isolated L17/follow-up candidate code + tests;
3. `validation:` committed evidence + report.

Do not rewrite the first formulation commit after seeing the simulation result
except through explicit corrective commits. This preserves provenance.

## 11. Stop boundary

This task does NOT authorize:
- merge/promotion into the production solver;
- revised V3 execution;
- graphite geometry;
- separator;
- PCS/gap;
- full porous-media production runs;
- replacing current CG defaults.

After evidence is committed, prepare a fresh-review request and STOP.
