# 04 — Formulation comparison without a premature ranking

Rows summarize inspected code and repository extractions, not independently reverified primary-paper equations. Full CG algebra remains in [the existing 28-row equation map](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/CURRENT_VS_LECLAIRE_MAP.md). SC is intentionally evidence-limited; see [its formulation sheet](formulations/SHAN_CHEN.md).

| Element | Production CG | L17_CORE implemented | SC / modern pseudopotential candidate |
|---|---|---|---|
| Lattice / backend | D3Q19, Taichi/f32 storage + f64 corrections | D3Q19, NumPy/f64 | candidate unspecified; cannot compare speed yet |
| Density / EOS | unit-density regime, p=rho/3 | alpha=1/3 specialization; p=rho/3 | distinguish multicomponent immiscible from single-component liquid-vapour |
| Equilibrium / collision | project MRT basis, closed-form equilibrium | R1 table basis, Eq.(4) density-gradient terms | select forcing/collision/EOS before equation comparison |
| Viscosity | narrow-band quadratic relaxation-rate blend | harmonic kinematic viscosity, omega=2/(6nu+1) | variant-dependent, not established locally |
| Interfacial stress | shift equilibrium moments then relax | post-collision unrelaxed perturbation; A=(9/4) omega sigma | interparticle-potential family; modern tunability papers must be read |
| Colour separation | equilibrium-channel pairwise minimum amplitude; no exposed beta | post-perturbation distribution split with explicit beta | not a recolouring parameter comparison |
| Wall treatment | fictitious wall colour and bulk suppression | gradient rotation, fluid→solid normal, full-way solid-node BB | wetting scheme and curved-wall behaviour are candidate choices |
| External force | Guo moment force + half-force velocity | plain momentum increment rho*g in both phases | must use consistent candidate-specific recovered hydrodynamics |
| Open boundaries | reservoirs, membranes, pressure/psi modes | R1 regularized open BC not implemented | not established |
| Calibration evidence | production Laplace and flat-wall registry | mechanical sigma PASS; Laplace gate unresolved; wetting tests scoped | no matched repo evidence |
| Battery interpretation | exploratory porous results | canonical synthetic tests only | no application claim justified |

**INFERENCE:** a passing Laplace slope cannot identify all operator differences. Equal-viscosity/equal-density cases cannot validate unequal-property behaviour. Nor can a numerical closure overlay establish missing gas physics.

**Contested derivation:** the existing map §A.9 replaces `(e_i·C)/|C|` with `cos(theta_i)` in its production comparison. Production code lacks an explicit division by `|e_i|`; face diagonals have length sqrt(2). The raw expressions and lattice norms need checking before accepting amplitude ratios as a complete equivalence/difference derivation. This pack preserves the source map and flags this extra issue for review.

## Proposed fair comparison contract

Choose named formulations and match physical dimensionless conditions (Ca, viscosity ratio, density ratio, gravity/Bond number where relevant), geometry, contact-angle convention, interface-width/throat ratio and measurement windows. Report attainable parameter ranges rather than forcing an unsupported match. Use each method's calibrated lattice parameters, not the same numeric CapA/G/beta.

Separate (1) formulation correctness, (2) benchmark applicability, (3) discretization/refinement, (4) precision/backend, and (5) cost at comparable error. A bounded initial matrix could use planar interface, Laplace/mechanical stress, non-axis-aligned wetting, two-fluid capillary displacement, closed pocket pressure balance and mass/positivity. This is a **PROPOSAL**, not an authorized run.

No ranking is defensible until the modern SC primary sources, exact implementation and matched tests exist. Older repository claims that CG has a decisive general advantage on under-resolved pores or that pseudopotential surface tension cannot be separately controlled are not sufficient evidence for this decision.

## Application and implementation dimensions still to compare

**INFERENCE:** the 0.25 micrometre/lu working constraint makes resolved throat/interface size and unresolved binder treatment central to selection. Compare physical model, geometry closure and storage architecture separately. Both SC homogenization papers and LBPM grayscale CG now have concrete leads; grayscale is not an SC-exclusive capability. See [readiness/gaps](10_REVIEW_READINESS_AND_GAPS.md) and the [implementation map](references/IMPLEMENTATION_REFERENCE_MAP.md). No speed or memory ranking follows from solver-family names alone.
