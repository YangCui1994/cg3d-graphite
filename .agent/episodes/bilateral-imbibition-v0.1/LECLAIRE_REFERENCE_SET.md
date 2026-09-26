# Leclaire / Latt CG reference set

Task: BI-CG-LECLAIRE-IMPLEMENTATION-001

Use the user's already-working **科研通** literature workflow to obtain papers
from DOI identifiers. This contract does not prescribe download commands or
local file locations.

## Mandatory sources

### R1 — canonical formulation

DOI: `10.1103/PhysRevE.95.033306`

S. Leclaire, A. Parmigiani, O. Malaspinas, B. Chopard, J. Latt,
"Generalized three-dimensional lattice Boltzmann color-gradient method for
immiscible two-phase pore-scale imbibition and drainage in porous media."

Role: primary algorithm specification. Treat equations, appendices and stated
operator ordering as canonical unless a later source explicitly changes them.

### R2 — same-group 3D CGM benchmark

DOI: `10.1142/S0129183117500851`

S. Leclaire, A. Parmigiani, B. Chopard, J. Latt,
"Three-dimensional lattice Boltzmann method benchmarks between color-gradient
and pseudo-potential immiscible multi-component models."

Role: implementation/behavior clarification, D3Q15/D3Q19/D3Q27 comparison,
interface-thickness and wetting/periodicity observations.

### R3 — later wetting-boundary improvement

DOI: `10.1016/j.advwatres.2018.03.014`

T. Akai, B. Bijeljic, M. J. Blunt,
"Wetting boundary condition for the color-gradient lattice Boltzmann method:
validation with analytical and experimental data."

Role: later wetting improvement / alternative. It is NOT part of the canonical
Leclaire-2017 baseline. Implement, if justified, as a separable option.

### R4 — later porous-media variant from the Leclaire/Parmigiani line

DOI: `10.1155/2019/5176410`

A. Parmigiani et al.,
"Characterization of Transport-Enhanced Phase Separation in Porous Media Using
a Lattice-Boltzmann Method."

Role: later porous-media algorithm ordering and practical CGM variant.

## Background source when needed

DOI: `10.1016/j.compfluid.2011.04.001`

S. Leclaire, M. Reggio, J.-Y. Trepanier,
"Isotropic color gradient for simulating very high-density ratios with a
two-phase flow lattice Boltzmann model."

Use only when the 2017 formulation depends on this earlier result.

## Source discipline

- Acquire the papers through 科研通 using the DOI identifiers above.
- Record DOI, title and role in the formulation artifact before using a source.
- Additional papers may be added only when directly needed to resolve an
  equation, implementation ambiguity or later optimization.
- For every added paper, record its DOI and why it is needed.
- Do not silently build a hybrid algorithm from unrelated literature.
- Public Palabos source is NOT the canonical CG source; the historical author
  CG branch was not recovered.
- Do not copy AGPL Palabos code into this repository.
