# 01 — Project goal and constraints

## Established scope

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

## Owner decisions to expose

Define the physical gas treatment (compressible, effectively incompressible, dissolving, vented or sealed), density/viscosity ratios, wetting/hysteresis requirements, physical geometry and minimum resolved throat/interface ratio. Define acceptable uncertainty and whether comparative trends suffice. These are [open decisions](09_OPEN_DECISIONS.md), not defaults silently inherited from a benchmark.

This task only creates an audit input pack. Preserve production and reference lines, prior evidence, controller state, and all existing branch boundaries. The source [promotion rule](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/docs/research/leclaire_cg/BRANCH_BOUNDARY.md) requires explicit owner selection of modules; the audit does not satisfy that selection by itself.
