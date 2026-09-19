# Algorithm — 3D color-gradient two-phase LBM (CG3D)

This document describes the method implemented in `lbm_solver_cg3d.py` and
driven by `run_pcs_cg3d.py` / `run_ir_cg3d.py`. The operational parameter
reference (what to change when opening a new run) is
[`BC_IC_OUTPUT.md`](BC_IC_OUTPUT.md).

## 1. Model overview

| Item | Choice |
|---|---|
| Scheme | Rothman–Keller **color-gradient** two-phase LBM (Leclaire et al. line) |
| Lattice | D3Q19 |
| Collision | MRT, 19 moments, Lallemand–Luo-type basis (cond(M) = 4.3) |
| Phases | "red" = non-wetting (gas), "blue" = wetting (liquid), unit density ratio |
| Surface tension | Direct input: parameter `CapA`, measured σ = **1.012·CapA** |
| Wettability | Per-node `psi_solid` field (geometric adhesion), no spurious films |
| Drive | ρ-prescribed ψ-Dirichlet reservoirs + per-colour semi-permeable membranes → open system with pressure boundaries, stepped capillary-pressure ladder |
| Backend | Taichi; GPU (CUDA) by default, `LBM_ARCH=cpu` for CPU |

Interface width ≈ 2.2 lu and recoloring anisotropy < 0.1 % (measured on
static droplets).

## 2. Colour field and phase semantics

Each fluid node carries two distribution functions, f_r and f_b. The colour
(order-parameter) field is

```
psi = (rho_r - rho_b) / (rho_r + rho_b)
```

ψ = +1 is pure red (non-wetting / gas), ψ = −1 pure blue (wetting /
liquid). The total density ρ = ρ_r + ρ_b carries the pressure
(p = cs²ρ, cs² = 1/3), which is what the reservoirs prescribe; the colour
field is advected by the recoloring step below. The upstream code had a
parenthesisation bug in this formula (`rho_r - rho_b/(rho_r+rho_b)`); the
fixed form above is what runs here.

## 3. Collision: 19-moment MRT equilibrium with ρ

The MRT collision relaxes moments m = M·f toward the polynomial equilibrium
meq = M·feq(ρ, u). The critical numerical contribution of this port: the
**full ρ-carrying closed form** of the 19 equilibrium moments (the upstream
3D code omitted the ρ factors — invisible at ρ ≡ 1, wrong the moment
density-driven pressure boundaries push ρ away from 1):

```
m0  = rho                                  (density)
m1  = rho * u^2                            (energy)
m2  = 0                                    (eps)
m3, m5, m7   = rho*ux, rho*uy, rho*uz      (momenta)
m4, m6, m8   = 0                           (energy fluxes)
m9  = rho*(2ux^2 - uy^2 - uz^2)            (pxx)
m11 = rho*(uy^2 - uz^2)                    (pww)
m13, m14, m15 = rho*ux*uy, rho*uy*uz, rho*ux*uz   (shears)
m10, m12, m16, m17, m18 = 0
```

Derived once and verified to 4.4e-16 against a direct M·feq product
(200 random ρ/u points, f64).

Relaxation layout (S): conserved moments 0,3,5,7 unrelaxed; stress-family
moments 1,2,9–15 carry the viscosity relaxation `sv`; the remaining
4,6,8,16,17,18 use `sother`.

## 4. Surface tension and recoloring

Surface tension enters as a **perturbation of the equilibrium moments**
(injected into the five stress/trace moments 1, 9, 11, 13, 14, 15),
parameterised by `CapA`. In this codebase CapA *is* the surface tension in
lattice units: σ = 1.012·CapA (13-droplet Laplace fit, R² = 1.0000), so
unlike pseudopotential (Shan–Chen) models σ is a direct input, not an
emergent output.

After collision, the **Latva–Kokko-type pairwise recoloring** step
re-segregates the colours at the interface: f_r/f_b are redistributed
along each lattice direction according to the local colour gradient
direction. Structure follows Latva–Kokko & Rothman (2005) — pairwise,
antisymmetric in e_i, β = 1 — with a **min-of-equilibria amplitude**
(min over the link pair's g_r/g_b values) instead of the
β·ρ_Rρ_B/ρ²·f^eq form (ADR-001 §3.4), applied through direction pairs
kk = 1,3,5,7,9,11,13,15,17. This keeps the interface at ~2.2 lu wide with
<0.1 % anisotropy, which is the decisive advantage over diffuse-interface
models on under-resolved real geometries.

## 5. Viscosity

Both phases use matched kinematic viscosity in the shipped runs
(ν_r = ν_b = 0.1). The solver interpolates the relaxation frequency along
the interface with the standard colour-mass-weighted formulas
(wl/wg/lg0/l1/l2/g1/g2), so unequal viscosities are supported but untested
in the graphite line (μ_r ≠ 1 is an open item of the parent project).

## 6. Wettability

Solid nodes carry a per-node `psi_solid` ∈ [−1, +1] field ("wall colour").
Wetting emerges geometrically from the recoloring step at solid faces — no
spurious films, and mixed-wet patterns are possible by writing a spatially
varying field. Calibrated contact-angle registry (flat-plate droplets,
liquid-side angle):

| psi_solid | −0.75 | **−0.68** | −0.25 | 0 | +0.25 | +0.7 |
|---|---|---|---|---|---|---|
| θ_liq | 21.1° | **≈30° (battery-electrode convention)** | 83.9° | 95.7° | 112.9° | 157.1° |

All graphite runs here use ψ_solid = −0.68 (θ ≈ 30°).

## 7. Upstream lineage, fixed defects and the 2026-09 audit

Numerical tables (moment matrix M, bounce-back map, tension-injection
pattern, recoloring pairs, relaxation layout) come from the upstream module
[yjhp1016/taichi_LBM3D](https://github.com/yjhp1016/taichi_LBM3D)
`lbm_solver_3d_2phase.py`. The class structure, infrastructure and kernel
order come from this project's validated 2D canonical solver. Four known
upstream defects are **not** inherited:

1. meq without ρ factors (breaks ρ-pressure drive; fixed — §3);
2. the ψ parenthesisation bug (§2);
3. scalar-only ψ_solid (fixed: per-node field);
4. module-level grid globals with no infrastructure (fixed: class-based,
   with race-free per-colour membranes and f64 flux-counting reservoirs).

The 2026-09-19 numerical audit (ADR-001) found and fixed two further
density-driving defects in the inherited force/gradient code:

5. Guo (2002) force weights 1/cs² = 3 and 1/cs⁴ = 9 omitted in the
   moment-space forcing — momentum injected was F/3 while the half-force
   velocity correction assumed F (measured eff = 0.332 vs 1.0 after the
   fix; force-driven runs only, X2/X3 unaffected with F = 0);
6. density-dependent bulk-suppression threshold `|ρ_r − ρ_b| > 0.9` in
   Compute_C — normalised to `|ψ| > 0.9` (identical at ρ ≈ 1; the raw form
   failed at ρ_out = 0.89, the d = 0.22 rung of reservoir-driven ladders).

## 8. Open-system pressure boundaries

The domain is a slab open along x (flow direction), closed by walls at both
ends behind the reservoirs:

```
x:  0        3            11 12  14                    214  217 218        225   228
    | wall   | res_in     | M |buf|   GRAPHITE (real)   |buf| M  | res_out  | wall |
    | 3 lu   | 8 lu       | 1 |2lu|        200 lu       |3lu | 1  | 8 lu     | 3 lu |
      BB       rho=1+d/2   gas    open buffer             open   liquid     BB
               psi=+1      only   (NaN fix, sec.10)       only   psi=-1
                          passes                          passes
```

- **Reservoirs** (8 lu): ρ is prescribed (ρ_in = 1+δ/2, ρ_out = 1−δ/2) and ψ
  is pinned (+1 gas source / −1 liquid sink). The capillary pressure is
  Pc = δ/3 (cs² = 1/3). Stepping δ up/down is the drainage/imbibition drive.
- **Semi-permeable membranes** (1 lu): ψ-conditional bounce-back on a single
  plane — the inlet membrane passes only red (gas), the outlet only blue
  (liquid). Implemented race-free per colour; measured leak
  ~2e-8 pore volumes/step in the graphite runs.
- **Walls**: plain bounce-back (no-slip). **y/z**: periodic (the real cube's
  cross-face artificial connectivity is a declared artefact).

Because both phases can leave the domain through their own membrane, the
system is truly open: gas enters at the inlet, liquid leaves at the outlet
(drainage), and the reverse on imbibition — no closed-system saturation
artefacts.

## 9. Timestep order and run protocol

Kernel order per step (identical to the 2D canonical):
`collision(+recolor) → F=0 → streaming1 (atomic accumulate, ψ-conditional
membrane bounce-back) → Boundary_condition → streaming3 →
Boundary_condition_psi → apply_reservoirs`.

Run protocol (both drivers):

1. **Equilibration**: δ = 0 for 20 000 steps from the initial condition
   (pores liquid-full ψ=−1; inlet reservoir + inlet membrane pre-seeded gas).
2. **Ladder**: for each δ in `--ds`, run until quasi-steady
   (colour flux tolerance 5e-7 over a 15 000-step window, minimum 15 000
   steps) or a 150 000-step cap; saturation and fluxes are logged every 500
   steps; a ψ snapshot is written every 20 000 steps (`--dump-every`),
   plus one frame per rung end and an incremental `report_partial.json`.
3. **Imbibition** (`run_ir_cg3d.py`): the drainage ladder stops at the
   requested S_i, then `--ds-imbibe` steps δ back down to 0 with state
   carried across rungs in a single implementation (one continuous
   pressure-path history).

## 10. The rough-surface buffer rule

On sub-voxel-rough real geometries, the reservoir/membrane forcing
conditions must **not** rest on the solid face: a 1-lu throat simultaneously
under "prescribed ρ/ψ" and "bounce-back on two walls" collapses ρ → 0 and
diverges within ~200 equilibrium steps (the five-variant probe chain in
`probe_gx1_nan.py` isolates this; the same layout is stable on smooth
sphere-pack surfaces). The fix is geometric and requires **zero solver
changes**: pad both x faces with k ≥ reservoir(8) + membrane(1) + clean
channel(2) + margin lu of open pore (k = 14 here; k = 4 still NaNs).
`make_geo_buffer.py` implements it.

## 11. Validation status (parent project)

The solver was validated on a separate ladder before touching real geometry
(numbers from the parent project's validation report; those drivers are not
part of this repo):

- Laplace: σ = 1.012·CapA, 13 droplets, per-case ΔP–1/R fits R² ≥ 0.9999;
- Contact-angle registry of §6; infrastructure suite 8/8 (incl. a 250k-step
  longrun and membrane/reservoir mass accounting);
- Single-phase permeability of ordered sphere packs vs the
  Sangani–Acrivos analytical bound: 0.98–1.04 across solid fractions
  0.3–0.971 (after the superficial-velocity correction — Darcy flux must be
  averaged over *all* nodes, never fluid nodes only);
- Drainage of a Finney random close packing: percolation knee at
  C = Pc·R/σ = 6.38, bracketed by literature θ = 0°/30° network curves;
  imbibition-resaturation trapping S_nr = 0.162–0.200, matching
  network-model bands.

The graphite numbers in `RESULTS.md` inherit this validated pedigree but
carry their own resolution caveats (§6 there).

## 12. Units and parameter conventions

All parameters are in lattice units (lu). σ = 1.012·CapA; Pc = δ/3;
voxel size for the shipped geometry is 0.128 µm (BIL native). Physical
time conversion t_phys = t_lu·Δx²/ν_phys is supported by the drivers but
was not applied in the exploratory runs (dimensionless-group matching only).
Baseline of every shipped run: CapA = 0.06, ψ_solid = −0.68, ν_r = ν_b = 0.1.
