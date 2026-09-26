# BI-CG-LECLAIRE-IMPLEMENTATION-001 — Fresh Reviewer Contract

Use a fresh DeepSeek session. Do not read the executor transcript and do not
modify the frozen candidate.

## A. Binding / isolation

Verify:
- product branch = `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`;
- base ancestry = `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`;
- `lbm_solver_cg3d.py` is unchanged;
- production defaults/gates are unchanged;
- implementation is isolated from the production solver line;
- no V3, graphite, separator, PCS or production porous-media work occurred.

## B. Literature provenance

Verify the mandatory DOI set was actually used:
- `10.1103/PhysRevE.95.033306`
- `10.1142/S0129183117500851`
- `10.1016/j.advwatres.2018.03.014`
- `10.1155/2019/5176410`

Check every nontrivial algorithm statement in PAPER_FORMULATION against the
cited equation/table/appendix in the source.

Any additional paper must have a DOI and an explicit reason for inclusion.

## C. Equation-level fidelity

Independently review:
- D3Q19 lattice and weights;
- MRT basis/relaxation mapping;
- color/order parameter;
- gradient stencil;
- perturbation operator;
- surface-tension relation;
- explicit-beta recoloring;
- viscosity interpolation;
- wetting/contact-angle handling;
- operator ordering.

Do not accept `MATHEMATICALLY_EQUIVALENT` without derivation.

## D. Baseline versus follow-up separation

Verify:
- `L17_CORE` is identifiable and paper-faithful;
- later improvements are separable switches;
- no undocumented hybrid default exists;
- project-specific conservation fixes, if any, are an explicit overlay.

## E. Validation

Independently inspect/recompute the canonical-test metrics.

Required coverage:
- uniform single-phase;
- planar interface;
- Laplace;
- contact angle;
- beta/interface-width relation;
- dynamic-isotropy test;
- slit capillary pressure;
- simple imbibition;
- asymmetric wall-transfer killer test;
- total/component conservation.

Check that prior production PASS results were not reused as proof.

## F. Interpretation

Answer separately:
1. Is the implementation faithful to the cited formulation?
2. Which current-vs-Leclaire differences are real rather than notation?
3. Which follow-up optimizations demonstrably change numerical behavior?
4. Does complex-wall wetting improve, degrade or remain unresolved?
5. Are any conservation corrections formulation-independent enough to retain?
6. Is the candidate ready for external scientific review?

## Decision

Exactly one:
- `PASS`
- `CHANGES_REQUESTED`
- `HUMAN_REQUIRED`

PASS does not authorize promotion to production.

Write only:
- `.agent_runtime/BI-CG-LECLAIRE-IMPLEMENTATION-001/REVIEW.md`
- `.agent_runtime/BI-CG-LECLAIRE-IMPLEMENTATION-001/REVIEW_SESSION.json`

Then STOP.
