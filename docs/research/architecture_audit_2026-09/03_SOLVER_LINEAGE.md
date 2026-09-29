# 03 — Solver lineage and reusable assets

## Distinct identities

| Line | Provenance | Present role |
|---|---|---|
| Historical / previous production CG | upstream taichi_LBM3D tables plus project 2D-to-3D rewrite; [history](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/ALGORITHM.md), [ADR](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/adr/001-hydrodynamic-equilibrium.md) | historical calibrated runs; older results retain their source state |
| Production CG after closure | [accepted product baseline](https://github.com/YangCui1994/cg3d-graphite/commit/6c30260dfe0c8b61ea9609e6bffa5c487312cf06), `lbm_solver_cg3d.py` | same production family with T3+C1X+A2 arithmetic corrections |
| L17 reference CG | [isolated NumPy/f64 solver](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/experimental/leclaire_cg/solver.py); Leclaire, Parmigiani, Malaspinas, Chopard & Latt (2017) | independent unit-density reference, not production replacement |
| L17 optional variants | [variant map](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/FOLLOWUP_OPTIMIZATION_MAP.md) | Akai wetting and explicit overlays; do not relabel these L17_CORE |
| SC / pseudopotential | mentions and external implementation archaeology only in inspected corpus | comparison candidate, no repository-local validated SC formulation established here |

“Latt CG” means the Leclaire et al. 2017 coauthored paper in this pack, not an assertion that all Palabos multiphase code implements it. [Code archaeology](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/docs/research/bilateral_imbibition/PALABOS_LECLAIRE_CODE_TRACE.md) distinguishes Palabos Shan–Chen code from the sought L17 implementation. This is a repository source claim, not a fresh upstream code survey.

## Retention proposals — review input, not promotion decisions

| Asset | Proposed disposition | Reason / condition |
|---|---|---|
| Production solver + arithmetic ablations | retain as frozen comparison baseline | extensive backend-specific conservation work would be lost by unconditional replacement |
| Geometry, topology and pressure diagnostics | retain interfaces; audit assumptions per model | periodic connectivity, phase labels and wall storage differ |
| L17 modular operators and lattice checks | retain as scientific reference | inspectable algebra and isolated variants; reference-stage closure remains contested |
| Existing graphite results | retain with exploratory banner and original phase convention | not quantitative proof for later closed-system battery filling |
| Evidence manifests / frozen raw fields | retain and strengthen | support recomputation independent of narrative |
| Current benchmark verdicts | preserve as historical records | reassess scientific interpretation separately; do not overwrite failures |
| Missing physical gas law or modern SC candidate | defer implementation | choose the physical question and primary formulation first |

**FACT:** legacy production documentation has red=gas, blue=liquid; the L17 masterline has red=liquid, blue=gas. Phase identity is a case/driver contract, not an intrinsic colour name. Any future A/B adapter must map physical phase, psi sign, contact-angle phase, pressure-jump sign and reservoir composition explicitly.

**OPEN:** the external paired `LBM/source_code/taichi_LBM3D/2phase/` tree and any historical SC implementation are not in this inspected checkout. Obtain their exact revision and reports before claiming historical SC-versus-CG superiority or synchronizing shared files.
