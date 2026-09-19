# ADR 001 — Hydrodynamic equilibrium & force formulation of the CG3D solver

Status: accepted (2026-09-19, PR-2 of Plan_20260919_v2)
Scope: `lbm_solver_cg3d.py` — answers tasks 1.2, 1.3, 1.4, 1.5, 1.6 of the
numerical-correctness audit. Companion fixes: commits `pr2.1` (Compute_C
criterion) and `pr2.2` (Guo weights).

## 1. What the current implementation is

Two-distribution colour-gradient (Rothman–Keller lineage) model on D3Q19 MRT:

1. **Colour field**: ψ = (ρ_r − ρ_b)/(ρ_r + ρ_b); pressure p = cs²·ρ with
   ρ = ρ_r + ρ_b (no bulk free energy — ideal-equation pressure).
2. **Collision (total distribution)**: 19-moment MRT, meq in closed form
   with **full ρ factors** (docstring table; verified vs M@feq to 4.4e-16).
3. **Surface tension**: added directly in moment space to meq[1] (energy)
   and meq[9, 11, 13, 14, 15] — see §4.
4. **Recoloring**: pairwise antisymmetric transfer with min-of-equilibria
   amplitude, β = 1 — see §5.
5. **Wettability**: per-node ψ_solid entering the colour-gradient stencil at
   solid neighbours; bulk suppression next to solid — see §6.
6. **Forcing**: Guo (2002) moment-space force with (I − S/2), half-force
   velocity correction u = (Σf·e + F/2)/ρ — see §3.

## 2. What the literature model is

- Equilibrium structure: Gunstensen et al. (1991) / Tölke et al. (2002) /
  Ahrenholz (2008) — colour-split distributions f_r, f_b share the local
  velocity u; each relaxes toward feq(ρ_colour, u); surface tension enters
  via a gradient-anisotropic stress; recoloring separates the colours.
- Moment basis: Lallemand & Luo (2000) D3Q19 (this M, cond(M) = 4.3).
- Forcing: Guo, Zheng & Shi (2002) — Δm = (I − S/2)·M·F̄ with
  F̄_i = w_i[(e_i − u)/cs² + (e_i·u)e_i/cs⁴]·F, macroscopic
  u = (Σf·e + F/2)/ρ.
- Recoloring: Latva–Kokko & Rothman (2005) — f_i^R = (ρ_R/ρ)f_i* +
  β·A(e_i·n̂), pairwise odd in e_i, amplitude A ∝ ρ_Rρ_B/ρ² · f_i^eq.

## 3. Differences found and decisions

### 3.1 Equilibrium (task 1.3) — KEEP

The upstream 3D module omitted the ρ factors in meq (defect #1 of the
2026-09-11 upstream audit; ALGORITHM §7): invisible at ρ ≡ 1, breaks
ρ-pressure driving. The current full-ρ closed form is the correct M@feq of
the standard CG equilibrium — **not** a deviation from the literature, but
the faithful implementation of it. The "local-rho equilibrium" question is
settled: colour-split feq(ρ_r, u) / feq(ρ_b, u) IS the standard
formulation (Gunstensen/Tölke/Ahrenholz); no alternative formulation is in
play. **Decision: keep, no code change.**

### 3.2 Guo forcing (task 1.2) — FIXED (commit pr2.2)

The original GuoF omitted the 1/cs² = 3 and 1/cs⁴ = 9 weights, so the
momentum actually injected per step was F/3 while streaming3's half-force
correction used F/2 — a provable inconsistency (lattice moment algebra:
Σ_l e_{lx}·w_l·[(e_l−u)·F] = cs²·F_x), confirmed by measurement on both
solvers: eff = 0.332 (3D, tests/test_poiseuille_cg3d.py) and 0.330 (2D,
results_p2_ordered channel calibration, 2026-09-11). Historical k results
stay valid: the P2 line divided by the measured eff explicitly.
**Decision: restore the Guo weights (3, 9). After the fix eff = 0.9933 and
the Poiseuille L2 drops from 0.67 to 0.0075.** Reservoir-driven runs are
untouched (F = 0 ⇒ GuoF inert; drainage smoke S_nw bit-stable at 0.843).
The parent repo's 2D canonical and its `lbm_solver_cg3d.py` copy still
carry the old form — flagged for cross-repo follow-up, not silently mixed.

### 3.3 Surface-tension operator (task 1.4) — KEEP, DOCUMENTED

The stress-sector additions are exactly the deviatoric projector:
meq[9,11,13,14,15] += 0.5·CapA·|∇ψ|·(n⊗n − I/3 components), i.e. an
effective interfacial stress 0.5·CapA·|∇ψ|·(n⊗n − I/3), PLUS a trace-part
shift meq[1] += CapA·|∇ψ| (upstream :322-327; both inherited). Moment
identities used in this check: M row 9 ↔ 2e_x² − e_y² − e_z²,
row 11 ↔ e_y² − e_z², rows 13/14/15 ↔ e_xe_y / e_ye_z / e_xe_z (verified
against the shipped M table). The pair (0.5·deviatoric + 1·trace) is NOT
the moment image of any single 4th-order-isotropic velocity-space
perturbation (the K-ansatz w_i[(e·n)²−1/3] gives trace:deviator ratio 4.5×
smaller) — it is a direct moment-space construction inherited from the 2D
lineage. Its acceptance rests on the benchmarks, which hold: σ = 1.012·CapA
(13-droplet Laplace fit, R² = 1.0000), interface width ~2.2 lu with
<0.1 % anisotropy. **Decision: keep; no code change. Do not "normalise"
it to a textbook form — that would change every calibrated number.**

### 3.4 Recoloring (task 1.5) — KEEP, RENAMED IN DOCS

Implementation (collision, 9 opposite pairs kk = 1,3,5,7,9,11,13,15,17):
transfer Δ_kk = min(g_r[kk], g_r[kk+1], g_b[kk], g_b[kk+1])·(e_kk·C)/|C|,
applied antisymmetrically (+Δ on kk, −Δ on kk+1 for red; mirrored for
blue); g_r/g_b are feq(ρ_r, u)/feq(ρ_b, u). Structure = Latva–Kokko &
Rothman (2005) pairwise segregation with β = 1; the **amplitude is the
min of the four link equilibria**, not the β·ρ_Rρ_B/ρ²·f^eq form. The
min-amplitude variant was inherited from upstream (:358) via the 2D
canonical; its original author is unidentified. **Decision: keep the
algorithm; docs now say "Latva–Kokko-type pairwise recoloring
(min-of-equilibria amplitude, β = 1)" instead of bare "Latva–Kokko
recoloring".** Benchmarks unchanged by a rename.

### 3.5 Wettability (task 1.6) — KEEP; suppression fixed (commit pr2.1)

Wall colour ψ_solid enters via the gradient stencil (solid neighbours
contribute 3·w_s·e_s·ψ_solid), with per-node field support (defect #3 of
the upstream audit, fixed). Mathematical consistency: the stencil weights
3·w_s·e_s = c_s⁻²·w_s·e_s are the standard isotropic gradient; the θ(ψ_solid)
calibration (flat-plate droplets, θ registry in the parent repo) is a
geometry-level consequence of the recoloring at solid faces. The
bulk-suppression guard (zero C for pure phase next to solid) used a
density-dependent threshold — fixed in pr2.1 to the normalised |ψ| > 0.9;
**identical at ρ ≈ 1 (calibrations untouched), correct at ρ = 1 ∓ d/2**
(the old form failed precisely at the d = 0.22 rung where ρ_out = 0.89).

## 4. Final formulation adopted

This ADR + commits pr2.1/pr2.2. Summary of what changed numerically:

| Item | Change | Affects |
| --- | --- | --- |
| Compute_C bulk criterion | normalized | pure-phase cells at ρ ≠ 1 near solid (high-|d| rungs of reservoir-driven ladders) |
| Guo force weights | 3/9 restored | force-driven runs only (k benchmarks; X2/X3 unaffected, F = 0) |
| Everything else | none | — |

Old-vs-new benchmark quantification is deferred to Phase 5
(docs/NUMERICAL_AUDIT_2026_09.md) by design.
