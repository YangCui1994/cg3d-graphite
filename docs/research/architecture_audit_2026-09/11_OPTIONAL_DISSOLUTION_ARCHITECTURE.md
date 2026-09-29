# 11 — Optional dissolution and weak-compressibility coupling

## Status and scope

**FACT / owner discussion:** the required baseline is weakly compressible porous-media imbibition with simultaneous two-sided liquid invasion. The owner agreed to explore an optional gas-dissolution extension and asked whether compression and dissolution can be decoupled. This authorizes architectural consideration, not implementation, an assumed timescale separation, a chosen gas law, or replacement of the existing solver. No dissolution simulation has been implemented or validated in this audit.

**PROPOSAL:** preserve a no-dissolution baseline and assess a separately switchable transport/interface-transfer module. The reviewer must challenge this choice and compare its complexity with alternatives. Do not make optional dissolution a blocker to baseline delivery.

## Physical distinction and candidate equations

Compression changes pressure/density/volume at fixed gas inventory (absent boundary flux). Dissolution transfers a chemical species from the free gas to solution. In a closed system the sum of free and dissolved amounts of that species is conserved. Solvent mass is separate: dissolving gas does not chemically turn it into solvent.

A dilute, isothermal, single-effective-gas extension could start with liquid-interior advection–diffusion of molar concentration c, diffusivity D and velocity u:

`∂c/∂t + div(c u) = div(D grad(c))`.

This is a bulk equation, **not a complete moving-interface discretization**. A conservative phase-restricted formulation, moving-interface balance, solid boundary condition, and consistent transport through changing liquid volume must still be derived.

An equilibrium interface could use `c* = H_cp p_g`, explicitly defining H_cp as concentration divided by pressure and p_g as the gas species' absolute partial pressure. A finite-rate alternative is `J = k_L (c* - c_interface)`, with J positive from gas to liquid. These are alternative interface closures, not two independent prescriptions to impose simultaneously. Required configurable inputs include D, Henry coefficient/convention, initial dissolved concentration, temperature assumptions and external concentration/flux boundaries; k_L is additional only for finite-rate transfer. They may initially be dimensionless research parameters, without requesting electrode experiments now.

**OPEN:** existing unit-density LBM pressure `rho/3` and numerical compressibility are not by themselves calibrated absolute gas partial pressure or a real-gas pressure–inventory–volume law. Derive the mapping and closure before enabling pressure-dependent solubility. Do not bolt an independent ideal-gas pressure update onto the existing EOS without consistency analysis. The amount transferred, density/volume response, momentum balance and interface motion must be mutually consistent. Changing phase color alone, weakening recoloring, or deleting small bubbles is not a validated dissolution law.

## What can be decoupled?

| Level | Candidate approximation | Admission / limitation |
|---|---|---|
| Separate software modules | hydrodynamics/interface; dissolved-species transport; interfacial exchange; conservation ledger | generally useful organization, but no physical independence follows |
| One-way post-processing | freeze a flow/interface history and estimate concentration or early transfer | only while transfer-induced geometry/pressure changes are negligible; cannot establish dissolution-driven renewed invasion |
| Sequential two-way coupling | advance flow, advance species/transfer, update gas inventory consistently, feed back to flow | proposed first coupled route; must establish time-splitting convergence and conservation |
| Quasi-static mechanical response | relax mechanics between slow dissolution increments | requires mechanical relaxation to be short relative to dissolution; weak compressibility alone does not establish this |
| Tighter coupling / subiterations | resolve significant flow/transfer feedback within each interval | may be needed near rapid mass loss, gas-pocket disappearance, reconnection or threshold invasion |

Pressure affects solubility; dissolution changes inventory and interface geometry; geometry alters transport pathways and fluid motion. Complete physical decoupling is therefore not a default for closed trapped gas. Distinguish acoustic/pressure equilibration from viscous-capillary/front relaxation. The relevant dissolution time is an inventory/flux timescale (with geometry, solubility and driving concentration); `L²/D` only estimates diffusion time and is not automatically the bubble lifetime. Numerical LBM sound speed is not automatically the physical acoustic speed.

**PROPOSED exchange contract:** the flow module supplies phase geometry, velocity and a pressure quantity with an explicit mapping; transport supplies integrated species transfer; the coupling layer applies equal-and-opposite inventory changes and the derived mass/volume/momentum updates; diagnostics track inventory, boundary flux and splitting error. Connected-component IDs may assist diagnostics, but a per-pocket pressure/inventory closure must handle pocket splitting/merging and must not replace locally resolved mechanics without justification.

## Alternative routes to review

1. Reduced gas-pocket mass-transfer law: inexpensive exploration, with geometry-dependent closure assumptions.
2. Henry/transport/interface-transfer extension to existing flow: modular candidate, requiring a conservative moving-interface implementation.
3. Multicomponent pseudopotential or free-energy formulation: more integrated component partitioning, but new thermodynamic/transport calibration and potentially substantial storage/model changes. No claim that SC automatically provides correct dissolution.

For the GPU budget, compare finite-volume/difference scalar transport with an additional LB distribution, buffers and masks; do not assume one stored scalar is the entire overhead. No resource benchmark has been performed here.

## Proposed numerical verification before any promotion

- Zero-transfer/off switch recovers the no-dissolution baseline.
- Fixed-interface diffusion and partition-equilibrium tests with independent solutions.
- Closed-domain free-plus-dissolved species balance and an open-domain flux balance; positivity and no transfer into solid sites.
- Isolated bubble benchmark within the assumptions of the selected reference, followed by confined pore/throat geometries.
- Grid/interface-width and coupling-time-step sensitivity, including agreement with a tighter-coupled reference where practicable.
- Two-sided invasion followed by gas isolation, dissolution and possible renewed invasion; report pocket splitting/merging/disappearance without numerical deletion masquerading as physical transfer.

Thresholds, time mapping and the minimal test set remain for reviewer design. These are proposed numerical checks, not experimental calibration requirements or authorized runs.

## Primary reading leads and evidence boundary

The preceding discussion checked publisher/author records and abstracts; this pack does **not** contain a full extraction or replication of these papers. Treat the architectural synthesis above as a proposal, not a result attributed to any single paper.

| Source | Specific reading purpose |
|---|---|
| [Analysis of Henry’s law and a unified lattice Boltzmann equation for conjugate mass transfer problem (2019)](https://doi.org/10.1016/j.ces.2019.01.021) | interface partition and flux treatment; determine whether and how it extends to moving, shrinking gas pockets |
| [Maes & Soulaine, A new compressive scheme to simulate species transfer across fluid interfaces using the Volume-Of-Fluid method (2018)](https://doi.org/10.1016/j.ces.2018.06.026) | CST/C-CST treatment of concentration transport; VOF method, not a drop-in CG implementation |
| [He et al., Dissolution process of a single bubble under pressure with a large-density-ratio multicomponent multiphase lattice Boltzmann model (2020)](https://doi.org/10.1103/PhysRevE.102.063306) | integrated pseudopotential alternative and pressure/solubility behavior; not validation of current unit-density code |
| [Yu et al., Bubble dissolution kinetics in porous media (2026)](https://doi.org/10.1103/jr19-lxmr) | confinement changes transfer area, diffusion distance and concentration fields; scrutinize applying free-space Epstein–Plesset kinetics to pores |

No additional PDFs need to be supplied by the owner to begin architecture review. Obtain exact full texts before accepting an implementation recipe or quantitative dissolution prediction.
