# 10 — Review readiness, recovered context and remaining gaps

Updated 2026-09-29. This supplement separates readiness to conduct an architecture review from readiness to select and implement a physical model.

## Scope update: simulation project first

**Owner clarification, 2026-09-29:** the immediate product is runnable porous-media imbibition software using weakly compressible two-phase physics and capturing simultaneous liquid entry from two sides, including battery-electrode use. The material/experiment gaps below concern later application calibration, not admission to architecture review. Do not repeatedly request the owner to supply them now. Retain numerical verification and validity limits as current code-project requirements; see [01](01_PROJECT_GOAL_AND_CONSTRAINTS.md).

## Readiness judgment

**INFERENCE:** the repository now supports an independent first review of development history, retained assets, scientific claims and harness failure hypotheses. It does **not** yet support a definitive modern SC-versus-CG ranking, a calibrated battery prediction, or a fully specified implementation plan. Finishing a file inventory is not completing the evidence base.

| Decision | Available now | Still needed |
|---|---|---|
| Reconstruct development and harness failures | pinned code/history, validation records, later critical reviews | distinguish measured causes from plausible governance explanations; runtime/session evidence only if operational claims require it |
| Retain/adapt existing assets | production and L17 operators, failure cases, branch boundaries | per-asset disposition and acceptance scope from independent reviewer |
| Design the current simulation project | porous imbibition, weakly compressible scope, two-sided invasion, hardware/domain target and candidate code/literature | supported parameter/boundary envelope and numerical acceptance criteria; application calibration deferred |
| Compare modern pseudopotential and CG | CG extracts and historical benchmarks; SC source queue | exact MCMP candidate, verified forcing/wetting/EOS assumptions, matched comparison protocol |
| Choose feasible implementation | production storage layout, external architecture examples | measured memory budget, domain size, precision policy, runtime target; no family-wide performance ranking yet |
| Design research harness | contracts, evidence/review workflow, observed scientific premise failures | reviewer proposal with falsification/reframe gates, then an explicitly scoped implementation decision |

## Recovered cloud context and its authority

The bounded cloud records returned for [Review进展](chatgpt-conversation://6abb6746-2bf8-83ed-88e3-a4f17532f31b), [整理渐变色及Chen对比](chatgpt-conversation://6ab67912-ffb8-83ed-91ad-7d4d01ec0aa5), [LBM双侧渗吸设计](chatgpt-conversation://6ab34c37-9a00-83eb-b6f9-9c403013fd89), and [继续讨论V1架构](chatgpt-conversation://6ab22e7f-72e8-83ed-8119-83a378d54143) were inspected. Retrieval exposed recent text, not a guaranteed complete archive; referenced attachments were not supplied. These links may require the owner's ChatGPT access. Material constraints are restated below so the reviewer does not depend on that access.

**FACT / owner statement:** in 整理渐变色及Chen对比, user turn `6c3fe2c7-2f61-455b-8454-e42ac04c5feb` says “当前大概最多能做到0.25um per lu” because GPU memory limits resolution. Treat approximately **0.25 micrometre per lattice unit** as the stated working resolution constraint for the intended study. It is not the historical README's **0.128 micrometre image voxel size**, and does not specify a universal fixed grid or an approved coarsening procedure.

**Arithmetic, not a resolution-validity claim:** at 0.25 micrometre/lu, a 0.5/1/2 micrometre throat spans 2/4/8 lu. The reviewer must assess interface width, wall discretization, segmentation uncertainty and unresolved porosity together. Numerical subdivision cannot restore unmeasured structure.

**FACT / conversation content:** earlier assistant advice discussed keeping CG while using SC as a comparison, battery multicomponent SC literature, grayscale/homogenized binder, and memory estimates. Those are proposals, not owner-approved model selection or measured performance. In particular, rough bytes-per-node estimates must not substitute for allocation measurements with precision, buffers, diagnostics and runtime overhead included.

**INFERENCE:** the relevant architecture has at least three independently selectable layers: physical model, representation of resolved/unresolved pores, and numerical/storage implementation. Grayscale modeling is not exclusive to SC: the inspected LBPM documentation also describes a grayscale CG route. Choosing a family name alone does not resolve the application.

**FACT / conversation content:** prior planning and review also prescribed the Jurin benchmark. The failed premise should therefore be audited across planning, implementation and review; assigning it solely to an executor or model is unsupported. Owner interest in visible execution sessions is an operational usability requirement, distinct from scientific validity.

## Remaining inputs by decision stage

**Current handoff:** no owner-supplied experimental dataset is required to start the architecture review. The required scope, weakly compressible baseline, simultaneous two-sided invasion and resource-planning targets are already recorded. The reviewer should proceed, marking evidence-dependent conclusions as conditional.

| Stage | Remaining evidence | How to handle now |
|---|---|---|
| Architecture review | exact R2/R5 PDF verification, modern SC candidate extraction, historical SC implementation if it exists | use available source maps and code; identify precise unresolved claims, do not claim complete ranking |
| Architecture review, optional dissolution | full texts and pressure/inventory/coupling derivation in [11](11_OPTIONAL_DISSOLUTION_ARCHITECTURE.md) | assess interfaces and alternatives; do not assume decoupling or implement now |
| Implementation verification | measured GPU allocation/runtime, supported parameter envelope, two-sided invasion/trapping checks, geometry/interface convergence | propose bounded tasks and acceptance criteria; supplied memory estimates remain unmeasured |
| Later application calibration | exact electrode geometry/extent including buffers, electrolyte properties, contact-angle measurement interpretation, experimental observables and error targets | deferred; no need for owner to collect these before review |
| Optional provenance recovery | original L17 Palabos extension, private `_refs/`, prior SC code/configuration/results | missing from inspected clone, not proven nonexistent; original author code is helpful but not a prerequisite |

Publicly accessible literature should be retrieved by the reviewer when needed. Request owner assistance only for exact private files or inaccessible full text that changes a concrete decision. The fair comparison must identify a modern MCMP variant and match physical/numerical controls; single-component liquid-vapor improvements cannot automatically be transferred to noncondensable-gas MCMP.

## Recommended reviewer boundary — proposal, not execution authorization

Proceed with the science/harness architecture review now, require conditional recommendations and an explicit missing-evidence table, and defer an irreversible solver switch. Ask the reviewer to separate retain/adapt/replace/defer decisions from experiments needed to decide them. Highest-value next acquisition is targeted full-text verification and any available prior implementation provenance. Application calibration is deferred; do not repeat generic code searches without a specific new lead. No external code was copied, no simulations were run, and no author was contacted in preparing this supplement.


## Follow-up received: domain and memory budget

The owner supplied the desired domain, fallback domain and diagnostic-storage capacity estimates after this supplement was first published. See the [goal/constraint record](01_PROJECT_GOAL_AND_CONSTRAINTS.md). This closes the missing *planning target*, not the missing measurement/provenance. Do not ask the owner to rediscover these dimensions. Priority owner-held materials are existing R2/R5 PDFs, prior SC code/configurations/results, and the original memory calculation if available. Publicly accessible literature should be acquired directly when the separate extraction task proceeds; only inaccessible full text needs owner assistance. No new solver or allocation changes accompany this update.


## Scope clarification: porous-media imbibition is already established

The owner's subsequent clarification and the retrieved cloud user statement explicitly identify porous-media/battery imbibition. The existing episode contract supplies the closed bilateral spontaneous-imbibition validation design and the later graphite/gap/PCS roadmap. See [01 — established scope](01_PROJECT_GOAL_AND_CONSTRAINTS.md). Read the remaining input list as requests for quantitative realization and evidence, not uncertainty about whether imbibition is the research objective. Generic electrolyte-filling papers remain supporting literature whose forcing and boundary assumptions must be compared with this target.
