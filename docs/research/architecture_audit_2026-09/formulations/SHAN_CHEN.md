# Shan–Chen / pseudopotential — supported scope and missing formulation

**Status: comparison candidate, not a reconstructed or validated repository solver.** No SC-specific implementation/calibration package was identified in the inspected product/control files or filename-history search. This does not prove absence from the separate LBM tree or every historical branch.

## What can be supported now

**FACT about repository records:** [Palabos archaeology](https://github.com/YangCui1994/cg3d-graphite/blob/dddac98d16bb4b792a371fe4d74276aba702038b/docs/research/bilateral_imbibition/PALABOS_LECLAIRE_CODE_TRACE.md) identifies Shan–Chen code and distinguishes it from L17; [R2 manifest](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/REFERENCE_MANIFEST.md) identifies a 2017 CG-versus-pseudopotential benchmark. Neither gives a complete modern SC candidate for this project's battery question.

**PRIMARY-SOURCE ABSTRACT CLAIM:** Shan & Chen's original model introduces interparticle potentials for multiple phases/components and nonideal behaviour; it is not the same formulation as colour-gradient recolouring. Source: [Shan & Chen (1993)](https://doi.org/10.1103/PhysRevE.47.1815).

**PRIMARY-SOURCE ABSTRACT CLAIM:** Li & Luo propose independent surface-tension control through an additional source term in a pseudopotential model. Therefore the old repository generalization that SC surface tension is necessarily inseparable from other model properties is inadequate for a modern comparison. This does not establish independence of every physical/numerical parameter or validate an arbitrary multicomponent implementation. Source: [Li & Luo, tunable surface tension](https://arxiv.org/abs/1306.6445).

**PRIMARY-SOURCE ABSTRACT CLAIM:** modern multicomponent wetting work addresses non-axis-aligned/curved walls; it supplies candidates to examine rather than evidence that the repository's rough graphite geometry is solved. Sources: [Coelho et al.](https://arxiv.org/abs/2009.12584), [Wang et al. (2023)](https://doi.org/10.1103/PhysRevE.107.035301).

These are bounded literature-discovery statements. No SC force equation, coexistence curve, EOS parameter set or wetting formula is transcribed here from memory.

## Necessary split before selecting equations

- **Single-component multiphase:** liquid–vapour coexistence / phase change may be relevant to some problems, but does not automatically represent electrolyte plus noncondensable air.
- **Multicomponent immiscible:** component conservation, mutual solubility/diffusion, density ratio and gas treatment must be specified. Do not transfer single-component high-density-ratio claims without checking their applicability.
- **Previous local SC:** exact source/revision, force scheme, pseudopotential, coupling constants, EOS, collision, wall scheme, boundary conditions and calibration are unknown in this audit.

## Extraction contract for a future PDF session

For each selected primary source, record exact version/hash, equation/table/page, model class, force discretization, recovered pressure tensor/EOS, coexistence/mechanical stability, viscosity and density ratios, surface-tension tuning, interface thickness, wetting/curved-wall treatment, mass exchange, positivity/stability and benchmark parameter ranges. Keep paper claim, derived specialization and code realization separate.

Compare at matched physical conditions and resolution/error; retain failures and parameter tradeoffs. Required papers and acquisition priorities are in the [reference index](../references/REFERENCE_INDEX.md). A fair final ranking is **OPEN** until that work and a named implementation exist.
