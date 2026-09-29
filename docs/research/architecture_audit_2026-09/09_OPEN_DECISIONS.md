# 09 — Open decisions for the scientific architecture review

| Decision | Alternatives / unresolved issue | Required evidence | Decision owner / blocker |
|---|---|---|---|
| D1: code-project capability contract | porous-media imbibition, weakly compressible phases and simultaneous two-sided invasion are established; supported configuration/diagnostics and numerical criteria need design | existing evidence, model assumptions and controlled numerical verification | architecture reviewer proposes; experimental electrode data does not block this review |
| D2: retain/improve production vs port L17 vs modern SC | all remain viable research routes within evidence limits | [comparison contract](04_FORMULATION_COMPARISON.md), source extractions, scoped validation | owner after architecture review; no port authorized |
| D3: fate of Jurin benchmark | retire classical prediction for present model; derive closed-system diagnostic; or add physically consistent density/forcing/boundaries | explicit hydrostatic derivation including gas pressure and body-force law | modeling choice; geometry repair alone is insufficient |
| D4: Laplace offset | estimator/intercept/finite-radius/discretization hypotheses; not automatically wrong A | convergence with multiple radii/resolutions and pressure-window sensitivity; stress/pressure consistency | research design; preserve untuned coefficient |
| D5: asymmetric wall diagnostic | redistribution versus defect | stationary reference and wall-band transport budget including solid-node storage | numerical/scientific review; global conservation alone does not decide |
| D6: supported parameter envelope | document current unit/matched-ratio limits within weakly compressible scope; broader ratios/real-gas/dissolution are optional extensions | parameter validity, numerical verification and primary sources | reviewer recommends envelope; no scope expansion inferred from paper generality |
| D7: future geometry | resolved synthetic → actual graphite/separator/gap/PCS | mesh/interface convergence, image-resolution limits, material wetting conventions | owner after controlled validation; V3 completion not assumed |
| D8: modern SC comparison | single-component liquid-vapour vs multicomponent immiscible/noncondensable gas | [literature queue](references/REFERENCE_INDEX.md), exact previous SC code and tests | owner selects comparator after formulation audit |
| D9: harness evolution | minimal admission ledger vs separate lanes vs full evidence graph | one bounded trial with effort/failure accounting | owner; this pack implements none |
| D11: optional dissolution architecture | separate modules and sequential feedback vs reduced gas-pocket law vs integrated thermodynamic model | [11](11_OPTIONAL_DISSOLUTION_ARCHITECTURE.md): pressure mapping, conservative transfer, timescale and splitting checks | reviewer assesses; optional extension, not a baseline blocker |
| D10: science-document repair | reconcile current status and phase semantics across branches | inconsistency register and pinned review/source IDs | later docs-only task; preserve historical evidence |

## Minimum additional material requested

- Existing R1–R5 PDF copies identified by the repository manifest, particularly **R5** for visual table mapping. They are not tracked in the public clone; this is an availability gap here, not proof that the project never obtained them.
- The named SC primary/review papers in the reference index. Most have identified open author/preprint routes, so “missing” means not yet acquired/extracted into the evidence corpus, not necessarily paywalled.
- Any previous SC solver implementation/configuration, exact commit, and representative raw calibration or failed runs. Without these, “previous SC” cannot be reconstructed fairly from CG advocacy prose.
- No experimental battery parameter package is required for this architecture review. Specific physical values and experimental error targets belong to later application calibration. Runtime/allocation records help assess implementation feasibility, but the supplied hardware/domain estimates already establish planning context.

## Requested output from the next reviewer

Return a staged roadmap with a retain/adapt/replace/defer decision for each major asset, competing model routes with evidence requirements, and a scientific harness design with entry/exit/reframe conditions. For each recommendation identify source facts, inference, and what could falsify it. Resolve the Jurin premise before proposing more solver repair. Preserve uncertainty rather than filling literature gaps from memory.

## Follow-up inputs before a final architecture choice

Use [10 — readiness and gaps](10_REVIEW_READINESS_AND_GAPS.md) to distinguish questions that the existing pack can answer from unresolved application facts, literature extractions and code provenance. Preserve the owner-stated approximate 0.25 micrometre/lu constraint. Evaluate unresolved porosity on both CG and SC routes; require measured resource envelopes before claiming an implementation is feasible. Original L17 author source would help adjudication but is not a prerequisite for conducting the first architecture review.
