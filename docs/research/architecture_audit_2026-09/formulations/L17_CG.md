# L17 CG — formulation navigation sheet

**Identity:** Leclaire et al., PRE 95, 033306 (2017), DOI [10.1103/PhysRevE.95.033306](https://doi.org/10.1103/PhysRevE.95.033306). “L17_CORE” below means the implemented NumPy/f64, unit-density specialization, not all capabilities of the paper.

## Reuse the existing extraction

[PAPER_FORMULATION](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/PAPER_FORMULATION.md) contains equation/table/page mappings; [REFERENCE_MANIFEST](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/docs/research/leclaire_cg/REFERENCE_MANIFEST.md) contains source hashes and access records. R1 journal page 033306-M maps to PDF page M+1 for that UNIGE copy. No PDFs were re-extracted during this audit: paper-level statements here are **repository transcription claims** cross-checked selectively against code.

| Element | Existing source locator | Code locator / audit boundary |
|---|---|---|
| D3Q19 velocities/weights/MRT | R1 Tables IV, XI; formulation §§0–2 | [lattice.py](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/experimental/leclaire_cg/lattice.py); ordering is not shell-major |
| Density and velocity | R1 Eqs.(2)–(3) | [macroscopic](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/experimental/leclaire_cg/operators.py) |
| Equilibrium | R1 Eqs.(4)–(5) | `equilibrium`: scalar `u·grad rho`, plus tensor contraction, not `c_i·grad rho` in first term |
| Viscosity | R1 Eqs.(13)–(14) | `viscosity_harmonic`, `omega_eff` |
| Gradient | R1 Eq.(17), R5 support | isotropic bulk + Cartesian wall gradient; full R5 table attribution unresolved |
| Perturbation | R1 Eqs.(15)–(18) | `perturbation`; post-collision and unrelaxed |
| Recolouring | R1 Eqs.(19)–(20) | `recolor`; splits post-perturbation N |
| Wetting / normal | R1 Eqs.(30)–(38) | secant orientation, smoothed solid mask; current canonical normal +grad(g) |
| Domain/order | R1 algorithm steps | [solver.step](https://github.com/YangCui1994/cg3d-graphite/blob/5dca114bc40c40743029a9439101958b13eaf721/experimental/leclaire_cg/solver.py): fluid-only operators, solid-node BB, stream |

## Load-bearing expressions — inherited extraction, not retuned here

`1/nu = (rho_r/rho)/nu_r + (rho_b/rho)/nu_b`, `omega=2/(6nu+1)`.

`Delta N_i = A |F| [W_i (F·c_i)^2/|F|^2 - B_i]`, `A=(9/4) omega sigma`.

`N_i^r = (rho_r/rho) N_i + beta*(rho_r*rho_b/rho^2)*cos(theta_i)*N_i^eq(rho,0)`; blue has the opposite segregation term. Here `cos(theta_i)` uses the direction norm; the rest direction needs its defined zero contribution.

Canonical current convention: `g=1` solid, `F=grad psi` gas→liquid, `n_w=+grad(g)/|grad(g)|` fluid→solid, contact angle through red/liquid. The earlier opposite-normal convention is superseded in current code, but stale prose remains.

## Implemented versus described versus unverified

**FACT:** alpha defaults to 1/3; initial total density is common to both phases; the solver does not expose the paper's general variable-density machinery as a validated model. R1 regularized open boundaries (Eqs.21–29) are excluded. The moment source adds total rho*g, not a phase-selective force. Those restrictions are central to the Jurin issue.

**FACT / source claim:** Akai wetting exists as a default-off later variant, with a separate rotation-only variant. It is not a validated improvement merely because implemented. Arithmetic overlay must also be labeled separately from core.

**OPEN:** R5 coefficient-table mapping, Laplace regression/finite-radius offset, asymmetric wall-band attribution, and correct scope of the capillary-rise diagnostic. Mechanical sigma, contact-angle sign and slit Pc have positive stored evidence with bounded scope; do not reopen them casually or extrapolate them to all configurations.

Read [evidence map](../05_VALIDATION_EVIDENCE_MAP.md) and [latest review conflict](../06_FAILURE_CASE_STUDIES.md) before treating the formulation as closed or scheduling a Taichi port.
