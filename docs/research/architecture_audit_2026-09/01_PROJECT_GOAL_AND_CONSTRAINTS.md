# 01 — Project goal and constraints

## Established scope

**FACT / owner clarification, 2026-09-29:** the intended application is **imbibition in porous media**, specifically the previously discussed battery-electrode problem. This is an established objective, not a new open choice between generic filling, drainage and imbibition. The cloud conversation [整理渐变色及Chen对比](chatgpt-conversation://6ab67912-ffb8-83ed-91ad-7d4d01ec0aa5), owner turn `6c3fe2c7-2f61-455b-8454-e42ac04c5feb`, explicitly asks about SC versus CG at the scale of lithium-battery imbibition.

**FACT / historical plan:** the linked episode contract below specifies closed bilateral **spontaneous** imbibition, no externally imposed pressure difference in V2/V3, finite liquid buffers and closed outer ends. Its post-checkpoint roadmap names real graphite, interface gap, Cu/separator representation, optional PCS, and trapped-gas/topology analysis. These are the documented research direction and staged design, not evidence that the real porous-media stage has run. Synthetic capillaries, bilateral channels and Jurin tests are supporting validation instruments; they are not the final scientific objective. The earlier pressure-driven graphite results are historical assets with different boundary conditions.

**Reviewer obligation:** assess each retained model, benchmark and harness gate by its relevance to porous-media imbibition, including complex-wall wetting, pore connectivity, interface/throat resolution, invasion and gas isolation. Carry the existing bilateral/finite-buffer design into review as context; do not ask the owner to define the application from scratch. The exact real-domain boundary realization, material parameters and required accuracy may still need decisions, and synthetic V2/V3 assumptions must not silently become a validated real-gas model.

**FACT / source statement:** [Repository README](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/README.md) targets pore-scale drainage, imbibition, electrolyte filling and trapped gas in Li-ion graphite microstructure. The [episode plan](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/.agent/episodes/bilateral-imbibition-v0.1/EPISODE_PLAN.md) deliberately starts with synthetic single-front, bilateral and finite-buffer tests before real graphite / separator / gap / PCS work.

The review must decide what model can answer the intended battery question; it should not merely make the next existing gate pass.

| Question | Evidence available | Limit that must travel with it |
|---|---|---|
| Pressure-driven invasion / resaturation | historical graphite ladder in [RESULTS](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/RESULTS.md) | open reservoirs/membranes; not spontaneous closed filling |
| Single-front capillary dynamics | V1/V1b/V1c reports; [evidence map](05_VALIDATION_EVIDENCE_MAP.md) | matched-viscosity resistance and boundary losses matter |
| Bilateral trapped gas | V2 closed symmetric synthetic case | gas trapped at initialization; fronts did not collide |
| Real electrolyte / air trapping | application objective | current unit-density weak-compressibility model is not a calibrated real-air compression law |
| Buffer / porous-media progression | revised V3 planning on control/transition lines | planning or authorization does not establish completed validation |

## Numerical and physical constraints

**FACT / source claim:** the README reports a 200³ graphite subcrop, 0.128 micrometre voxels, median throat 1.73 lattice units, and production interface width about 2.2 lattice units. It calls those graphite results exploratory. Refining a voxelized image is not automatically recovery of missing pore geometry.

**FACT:** production uses unit-density CG; the L17 implementation is a unit-density specialization even though its source paper includes broader machinery. Backend evidence is distinct: production Taichi/f32 storage with selected f64 paths versus L17 NumPy/f64 computation. Saved L17 snapshots use a separately documented f32 raw schema.

**INFERENCE:** required observables should be chosen before selecting the solver: filling rate, pressure balance, final saturation, connected gas volume, dissolution versus compression, or comparative geometry trends can demand different physics. No unique physical time/density/viscosity mapping for the future battery study is established by this pack.

**FACT / recovered owner constraint:** future application work is memory-limited to approximately **0.25 micrometre/lu**, as stated in the cloud discussion. This differs from the historical 0.128 micrometre image voxel. See [recovered context and readiness](10_REVIEW_READINESS_AND_GAPS.md) for provenance, limits and missing hardware/domain inputs.

## Owner decisions to expose

Define the physical gas treatment (compressible, effectively incompressible, dissolving, vented or sealed), density/viscosity ratios, wetting/hysteresis requirements, physical geometry and minimum resolved throat/interface ratio. Define acceptable uncertainty and whether comparative trends suffice. These are [open decisions](09_OPEN_DECISIONS.md), not defaults silently inherited from a benchmark.

This task only creates an audit input pack. Preserve production and reference lines, prior evidence, controller state, and all existing branch boundaries. The source [promotion rule](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/docs/research/leclaire_cg/BRANCH_BOUNDARY.md) requires explicit owner selection of modules; the audit does not satisfy that selection by itself.


## Owner-supplied domain and capacity estimates — 2026-09-29

**FACT / owner-supplied planning input:** target hardware is a single RTX 5080, described as 16 GB; desired physical extent is **70 × 100 × 100 micrometres** at **0.25 micrometre/lu**. A smaller **70 × 70 × 70 micrometre** domain is a fallback candidate, not an accepted scientific or hardware upper limit. Hardware availability and peak usable device memory have not been measured in this audit.

| Scenario | Grid / cell count (arithmetic checked) | State-array estimate supplied by owner | With approximately 25% allowance, supplied by owner |
|---|---|---|---|
| Smaller domain, resident diagnostic arrays included | 280³ = 21,952,000 | 13.0 GiB | 16.3 GiB |
| Smaller domain, resident diagnostic arrays removed | same | 4.3 GiB | 5.4 GiB |
| Desired domain, resident diagnostic arrays removed | 280 × 400 × 400 = 44,800,000 | not separately supplied | 11.1 GiB |

**SOURCE CLAIM, not measured capacity:** these memory numbers were supplied in the current conversation as prior estimates. They have not been independently reconstructed from an exact code/configuration snapshot or confirmed by peak-memory/runtime measurements. The diagnostic-array optimization is explicitly **not implemented**. “Current code” in that estimate has no attached commit or allocation inventory; do not assume it applies to every production/reference/debug configuration. Decimal GB and binary GiB must be normalized when making an actual capacity decision.

**INFERENCE / planning consequence:** treat optional diagnostic storage as a candidate architecture improvement before reducing the scientific domain solely on memory grounds. This is not authorization to modify it in this documentation task. Reservoirs, gas buffers, boundary padding and other allocations can enlarge the final domain; whether the supplied dimensions include them remains unspecified. Resampling from historical image voxels to 0.25 micrometre/lu also needs a geometry/connectivity validation rule. A capacity estimate does not establish physical resolution adequacy or acceptable execution time.

For reproducible follow-up, retain the original allocation calculation if available: code SHA, field names/shapes/dtypes, diagnostic switches, extra domains, overhead convention and device/runtime environment. It is useful evidence but not a blocker to the architecture review.
