# Production CG — formulation navigation sheet

**Scope:** `lbm_solver_cg3d.py` at production closure `6c30260`; identical solver blob at L17 package `5dca114`. This sheet summarizes code and existing derivations. It is not a new paper-faithfulness certification.

## Exact sources

- [implementation](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/lbm_solver_cg3d.py): lattice initialization, `Compute_C`, `collision`, `streaming1/3`, boundary and reservoir methods.
- [ADR-001](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/adr/001-hydrodynamic-equilibrium.md): equilibrium/force derivation and upstream corrections.
- [equation map](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/CURRENT_VS_LECLAIRE_MAP.md): full MRT, interpolation, interfacial and recolouring comparison.
- [closure report](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/colour_closure/EXECUTION_REPORT.md) and [residual diagnosis](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/results/colour_closure/LOCAL_RESIDUAL_DIAGNOSIS.md): arithmetic layer.

## Compact executable description — FACT from code / repository derivation

D3Q19 has weights `(1/3,1/18,1/36)` by speed shell. Total pressure uses `p=rho/3`; phase field is `(rho_r-rho_b)/(rho_r+rho_b)`. Polynomial equilibrium is `f_eq_i=W_i*rho*(1+3 e_i·u+4.5(e_i·u)^2-1.5|u|^2)` represented in the project's MRT basis. Do not substitute the L17 matrix/ordering into these tables.

Viscosity uses the implemented narrow `|psi|<=0.1` quadratic relaxation blend, not the L17 harmonic kinematic-viscosity formula. Guo forcing contains the 3/9 weights, `(1-S/2)` source prefactor and half-force velocity convention.

The bulk colour gradient is `C=3 sum_i W_i e_i psi(x+e_i)`; solid neighbours supply `psi_solid_f`, with a project wall-adjacent bulk suppression rule. Interfacial tension shifts moments 1,9,11,13,14,15 in equilibrium and is then relaxed. `sigma≈1.012 CapA` is a measured production calibration over documented tests, not an identity for all settings.

Colour transport builds equilibrium component populations and transfers opposite-pair increments:

`Delta = min(g_r[k],g_r[k+1],g_b[k],g_b[k+1]) * (e_k·C)/|C|`.

There is no independently adjustable L17 beta. Preserve the raw expression: the geometric cosine would also divide by `|e_k|`, which is sqrt(2) for diagonal links. The existing map's cosine shorthand deserves correction/verification before using its amplitude ratios quantitatively.

The colour-blind and colour channels stream separately; fluid-side half-way-style BB, per-colour membranes and reservoirs are project infrastructure. Read [BC semantics](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/BC_IC_OUTPUT.md) for actual face/order meanings, not parameter names alone.

## Arithmetic is a separate layer

T3 uses f64 inverse reconstruction, C1X weighted local colour closure, A2 f64 colour arithmetic/accumulation with final storage rounding. These are selected production corrections, not R1 paper elements and not proof that every GPU implementation conserves identically.

## Interpretation limits / open items

Historical graphite convention is red=gas, blue=liquid. Other drivers may map colours differently. Explicitly bind physical phase to each case. Unit-density and matched-viscosity validations do not validate real liquid/air property ratios, gas dissolution or compression. Wall-colour calibration on flat walls does not establish arbitrary rough-wall dynamic contact angle.

Original source attribution of the min-amplitude variant is unresolved in ADR-001. The more recent formulation map establishes differences from L17, not a complete primary-literature pedigree for every production choice. Preserve benchmarked code while the reviewer assesses its proper scientific scope.
