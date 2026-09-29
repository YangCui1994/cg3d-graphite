# 10 — Review readiness, recovered context and remaining gaps

Updated 2026-09-29. This supplement separates readiness to conduct an architecture review from readiness to select and implement a physical model.

## Readiness judgment

**INFERENCE:** the repository now supports an independent first review of development history, retained assets, scientific claims and harness failure hypotheses. It does **not** yet support a definitive modern SC-versus-CG ranking, a calibrated battery prediction, or a fully specified implementation plan. Finishing a file inventory is not completing the evidence base.

| Decision | Available now | Still needed |
|---|---|---|
| Reconstruct development and harness failures | pinned code/history, validation records, later critical reviews | distinguish measured causes from plausible governance explanations; runtime/session evidence only if operational claims require it |
| Retain/adapt existing assets | production and L17 operators, failure cases, branch boundaries | per-asset disposition and acceptance scope from independent reviewer |
| Choose battery-scale physical model | application objective, resolution constraint, candidate literature and code map | target observables, gas physics, material parameters, boundaries, acceptable error |
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

## Prioritized missing inputs

1. **Owner/application facts:** geometry preprocessing and whether reservoirs/buffers are included; measured usable GPU memory and acceptable elapsed time (the owner has now supplied a single-5080 target, desired 70 × 100 × 100 micrometre domain and capacity estimates); intended observables and tolerance; fluid properties; wetting/contact-angle information; inlet/outlet pressure protocol; vented versus sealed gas and whether compression/dissolution matters. The 0.25 micrometre constraint is already recorded and need not be rediscovered.
2. **Existing private assets:** exact R2/R5 PDFs already listed in the repository manifest; prior SC code with branch/commit, configurations and outcomes. Their absence from this clone does not prove they do not exist. Attachments and `_refs/` were not available through this inspection.
3. **Application-specific full texts:** battery electrolyte filling and homogenized multicomponent SC papers added to the [reference queue](references/REFERENCE_INDEX.md). Extract the actual model, binder representation, mapping, validation and limitations before importing conclusions.
4. **A fair comparison contract:** one named modern MCMP pseudopotential variant versus specified production/L17 variants, on matched geometry, dimensionless controls, wetting calibration, interface resolution and numerical cost. Single-component liquid-vapor improvements are not automatically noncondensable-air MCMP improvements.
5. **Author implementation provenance:** original L17 Palabos extension remains unrecovered. It would help equation-to-code adjudication, but is not a prerequisite to the first architecture review. See the [implementation map](references/IMPLEMENTATION_REFERENCE_MAP.md).

## Recommended reviewer boundary — proposal, not execution authorization

Proceed with the science/harness architecture review now, require conditional recommendations and an explicit missing-evidence table, and defer an irreversible solver switch. Ask the reviewer to separate retain/adapt/replace/defer decisions from experiments needed to decide them. Highest-value next acquisition is targeted full-text extraction and application constraints, not repeated generic code searches. No external code was copied, no simulations were run, and no author was contacted in preparing this supplement.


## Follow-up received: domain and memory budget

The owner supplied the desired domain, fallback domain and diagnostic-storage capacity estimates after this supplement was first published. See the [goal/constraint record](01_PROJECT_GOAL_AND_CONSTRAINTS.md). This closes the missing *planning target*, not the missing measurement/provenance. Do not ask the owner to rediscover these dimensions. Priority owner-held materials are existing R2/R5 PDFs, prior SC code/configurations/results, and the original memory calculation if available. Publicly accessible literature should be acquired directly when the separate extraction task proceeds; only inaccessible full text needs owner assistance. No new solver or allocation changes accompany this update.
