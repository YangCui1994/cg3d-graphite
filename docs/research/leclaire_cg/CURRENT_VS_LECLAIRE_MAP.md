# CURRENT PRODUCTION vs LECLAIRE-2017 — equation-level map

Task: `BI-CG-LECLAIRE-IMPLEMENTATION-001`
Current line examined: `lbm_solver_cg3d.py` at the task base
`6c30260dfe0c8b61ea9609e6bffa5c487312cf06` (unchanged by this task).
Baseline examined: `PAPER_FORMULATION.md` (R1, DOI `10.1103/PhysRevE.95.033306`).

Status vocabulary — exactly one per row:

- `SAME` — identical construction;
- `MATHEMATICALLY_EQUIVALENT` — different written form, equivalence derived below;
- `DIFFERENT` — both exist, not equivalent;
- `MISSING` — required by the paper, absent from the current line;
- `UNRESOLVED` — cannot be decided from the available sources.

Any row marked `MATHEMATICALLY_EQUIVALENT` carries its derivation in §A.
Rows marked `DIFFERENT` carry a quantitative statement of the difference.

---

## 1. Main table

| # | algorithmic element | paper (R1) | current production | status |
|---|---|---|---|---|
| 1 | lattice | D3Q19 | D3Q19 | `SAME` |
| 2 | connectivity **ordering** | Table IV order (shell-major: 1–6 axes, 7–18 diagonals) | `_init_lattice_tables` order: axes first, then (1,1,0)-type, then (1,0,1)-type, then (0,1,1)-type | `DIFFERENT` |
| 3 | lattice weights `W_i` | 1/3, 1/18, 1/36 | 1/3, 1/18, 1/36 | `SAME` |
| 4 | component densities `ρ_k`, colour-blind `ρ`, momentum | `ρ_k = Σ_i N_i^k`; `ρu = Σ_i N_i c_i` | `rho_r/rho_b` from streamed colour sums; `rho` from `f` | `MATHEMATICALLY_EQUIVALENT` (§A.1) |
| 5 | order parameter `ψ` | `(ρ_r−ρ_b)/(ρ_r+ρ_b)` (implied by Eq. 17) | `(rho_r−rho_b)/(rho_r+rho_b)` | `SAME` |
| 6 | zero-velocity weight `α`, density-ratio machinery | Eqs. (10)–(12), γ from `α_r, α_b` | no `α`; unit density ratio only | `MISSING` |
| 7 | sound-speed weight `ζ` (D3Q19) | 1/2 (Table VI + derivation) | not present; `p = ρ/3` assumed | `MISSING` |
| 8 | MRT matrix `M` | Table XI integer basis | different integer basis (rows 3,5,7,9,11,13,14,15 coincide up to the ordering of #2) | `DIFFERENT` (§A.2) |
| 9 | relaxation assignment `K` | `ω_eff` on {9,11,13,14,15}; `χω_eff` elsewhere | `sv` on {1,2,9..15}; `sother = 8(2−sv)/(8−sv)` on {4,6,8,16,17,18} | `DIFFERENT` (§A.3) |
| 10 | viscosity interpolation | Eq. (13) harmonic, **kinematic ν**, density-weighted; `ω_eff = 2/(6ν+1)` | quadratic blend **in ψ** of the relaxation rate over a ±0.1 band, coefficients built from `wl/wg` | `DIFFERENT` (§A.4) |
| 11 | equilibrium polynomial part | Eq. (4) `ρ[φ_i+ϕ_iα+W_i(3c·u+4.5(c·u)²−1.5u²)]` | `meq = M @ feq`, `feq = W_iρ(1+3c·u+4.5(c·u)²−1.5u²)` | `MATHEMATICALLY_EQUIVALENT` at `α=W0` (§A.5) |
| 12 | equilibrium density-gradient terms | Eq. (4) `ν[ψ_i(u·∇ρ)+ξ_i(G:c_i⊗c_i)]` | absent | `MISSING` |
| 13 | external forcing | Eqs. (6)–(9): `|ΔN⟩ = M⁻¹|Δm⟩`, plain momentum source in moment space | Guo (2002) in moment space **with** `3` and `9` weights and a `(1−½S)` prefactor | `DIFFERENT` (§A.6) |
| 14 | colour-gradient stencil | Eq. (17) with "3D fourth-order isotropic discretization" (coefficients deferred to R5 — see `PAPER_FORMULATION.md` §4.2, `UNRESOLVED` there) | `Compute_C`: `C = Σ_s 3 w_s e_s ψ(x+e_s)` | `MATHEMATICALLY_EQUIVALENT` (§A.7) — with the R5 caveat |
| 15 | gradient sampling at solid neighbours | wall normal rotated; `ψ` sampled from fluid only | solid neighbours contribute `psi_solid_f` (fictitious wall colour); `C` is additionally zeroed when `|ψ|>0.9` and a solid is adjacent | `DIFFERENT` |
| 16 | perturbation operator | Eqs. (15)–(16): added to `N_i` **after** collision, unrelaxed | injected into `meq[1,9,11,13,14,15]`, then relaxed by `S` | `DIFFERENT` (§A.8) |
| 17 | surface-tension calibration `A` | Eq. (18) `A = (9/4)ω_eff σ` | `CapA·|C|` injected at the moment level, no `ω_eff` factor | `DIFFERENT` (§A.8) |
| 18 | recoloring operator | Eqs. (19)–(20): `(ρ_k/ρ)N_i ± β(ρ_rρ_b/ρ²)cos ϑ_i N_i^(e)(ρ,0)` on the **post-perturbation `N_i`** | pairwise `min`-amplitude on the **equilibrium** colour split | `DIFFERENT` (§A.9) |
| 19 | explicit `β` and interface-width control | Eq. (19) `β = β*(Δx/Δx*)^η`; β is the sole interface-width knob (R2) | no β; amplitude implicitly fixed | `MISSING` |
| 20 | wetting BC | Eqs. (30)–(33): rotate orientation of `F`, preserve `|F|`, secant `n=2`, λ=1/2 | per-node scalar wall colour `psi_solid_f` (fictitious-density approach) | `DIFFERENT` |
| 21 | wall normal `n_w` | Eqs. (34)–(38): 3× D3Q27-weighted smoothing of the binary solid mask, then gradient | not computed; no `n_w` concept | `MISSING` |
| 22 | solid bounce-back | step (6) **full-way** on solid nodes, per colour, before streaming | **half-way** on the fluid node: `F[ci, LR[s]] += f[ci,s]` during streaming | `DIFFERENT` |
| 23 | operator ordering | BC → single-phase collision → wetting → perturbation → recoloring → full-way BB → streaming | collision(+perturbation via meq, +recoloring) → `F.fill(0)` → streaming1(+BB) → `Boundary_condition` → streaming3 → `Boundary_condition_psi` → `apply_reservoirs` | `DIFFERENT` (§A.10) |
| 24 | regularized density/velocity open BC | Eqs. (21)–(29) | `bc_*` modes 0/1/2: periodic, `feq(ρ_bc)` fill, velocity bounce-back | `DIFFERENT` (a project BC set with no paper counterpart; the paper's version is `MISSING`) |
| 25 | bulk suppression `|ψ|>0.9 → C=0` | not present | present (project-specific) | `DIFFERENT` (current-line extra) |
| 26 | per-colour membranes | not present | present (project-specific, race-free) | `DIFFERENT` (current-line extra) |
| 27 | density/ψ-prescribed reservoirs | not present | present (project-specific, f64 flux counters) | `DIFFERENT` (current-line extra) |
| 28 | conservation arithmetic overlay | not present | `total_fix=T3`, `colour_fix=C1X`, `acc_fix=A2` | `DIFFERENT` (current-line extra) |

Non-`SAME`/`EQUIVALENT` rows are the reason the paper's line was opened as a
separate implementation. Rows 16–22 are the load-bearing physics differences;
rows 25–28 are project engineering that the new line must **not** inherit by
default (`LECLAIRE_IMPLEMENTATION_CONTRACT.md` §1).

---

## 2. §A — derivations and quantitative statements

### A.1 Row 4 — `MATHEMATICALLY_EQUIVALENT` (component bookkeeping)

Both lines use `ρ_k = Σ_i N_i^k` and `ρ = ρ_r + ρ_b`. The current line carries
the total on the colour-blind field `f` and the components on the streamed
colour sums `rhor/rhob`, and reconstructs `ψ` from `rho_r/rho_b`. The paper
carries the two coloured fields directly. The relations
`ρ = Σ_k Σ_i N_i^k` and `ρu = Σ_i N_i c_i` are identical in both. The difference
is bookkeeping, not physics — **provided** the current line's colour split is
consistent with its colour-blind field, which is precisely the point of the
`C1X`/`A2` closure overlay (row 28) and of the defects it corrects.

### A.2 Row 8 — `DIFFERENT` (MRT basis)

Under the paper's Table IV ordering, the paper's `M` (`PAPER_FORMULATION.md`
§2.5) and the current `M` agree **only** on: the density row, the three momentum
rows, and the five stress rows. They differ on the energy rows.

Explicit relation for the energy row (`shell1` = indices 1–6, `shell2` = 7–18):

`paper_row1 = 19 · current_row1 − 11 · current_row0`

(verified algebraically: index 0 gives `−19−11 = −30`; the six axis entries give
`0−11 = −11`; the twelve diagonal entries give `19−11 = 8` — all matching the
published row). So the paper's energy moment lies in the span of the current
line's density and energy rows, but it is a **different basis vector**, and the
two matrices are not related by a permutation or scaling. A change of MRT basis
is only physics-neutral if the relaxation matrix is transformed with it
(`K' = T K T⁻¹`); the current line instead pairs its basis with an independently
chosen diagonal `K` (row 9). The two collision operators are therefore genuinely
different, not a notational variant.

This is exactly the class of claim the executor contract forbids accepting
without derivation, so it is stated as `DIFFERENT` and not as
`MATHEMATICALLY_EQUIVALENT`.

### A.3 Row 9 — `DIFFERENT` (relaxation assignment)

| moment group | paper | current |
|---|---|---|
| conserved (0,3,5,7) | `χω_eff` (immaterial) | unrelaxed |
| 9, 11, 13, 14, 15 (stresses) | `ω_eff` | `sv` ✓ same role |
| 10, 12 (extra stress-like) | `χω_eff` | `sv` ✗ |
| 1, 2 (energy-like) | `χω_eff` | `sv` ✗ |
| 4, 6, 8, 16, 17, 18 | `χω_eff` | `sother = 8(2−sv)/(8−sv)` ✗ |

`sother` is not of the form `χ·sv` for any constant `χ`, so even the "slow"
group does not match. Because a different `M` is in play (row 8), the diagonal
entries do not act on the same physical moments, and the discrepancy is not a
relabelling.

### A.4 Row 10 — `DIFFERENT` (viscosity interpolation)

Paper: `1/ν = (ρ_r/ρ)/ν_r + (ρ_b/ρ)/ν_b` — a **harmonic average of kinematic
viscosity** — then `ω_eff = 2/(6ν+1)`.

Current: `wl = 1/(ν_l/(1/3)+1/2)`, `wg` likewise, `lg0 = 2 wl wg/(wl+wg)`
(harmonic in `w`), then a **quadratic in `ψ`** on the band `|ψ| ≤ 0.1`:

`sv = lg0 + l1 ψ + l2 ψ²` for `ψ>0`, `sv = lg0 + g1 ψ + g2 ψ²` for `ψ<0`,
with `l1 = 2(wl−lg0)·10`, `l2 = −l1/0.2`, and correspondingly for `g`.

Behaviourally: the current law is a narrow-band polynomial blend of the
**relaxation rate**; the paper's is a global harmonic blend of the **viscosity**.
For equal viscosities both reduce to a constant and the difference is invisible —
so no single-phase test can discriminate them. They differ wherever
`ν_r ≠ ν_b`. Since `L17_CORE` runs at equal viscosities in the canonical set,
this row is recorded for completeness and is **not** a confound in the
validation results; the report says so explicitly.

### A.5 Row 11 — `MATHEMATICALLY_EQUIVALENT` at `α = W0`

Paper Eq. (4) polynomial part: `ρ[φ_i + ϕ_i α + W_i(3c_i·u + 4.5(c_i·u)² − 1.5u·u)]`.
Current: `feq = W_i ρ (1 + 3c_i·u + 4.5(c_i·u)² − 1.5u·u)`.

`PAPER_FORMULATION.md` §2.4 proves `φ_i + ϕ_i W0 = W_i` for all three D3Q19
shells. At unit density ratio the paper's `α = W0`, so the paper's bracket
becomes `W_i[1 + 3c_i·u + 4.5(c_i·u)² − 1.5u·u]` — identical to the current
`feq`. The current line then computes the moment-space equilibrium in closed
form; its own header records that this was verified against `M @ feq` to
`4.4e-16` over 200 random `(ρ,u)` points, which is an independent check of that
step.

Equivalence holds **only** at `α = W0`. It breaks for any non-unit density ratio
(row 6), which is a `MISSING` element in the current line rather than a
difference.

### A.6 Row 13 — `DIFFERENT` (forcing)

Paper: `|ΔN⟩ = M⁻¹|Δm⟩` with `Δm` non-zero only on the momentum moments. Because
`Σ_i c_i (M⁻¹|Δm⟩)` picks out exactly `Δm_{p_α}`, the source contributes the full
`ρg` per step, and Eq. (1) contains no `(1 − ½K)` prefactor.

Current: `GuoF` builds, for each moment row `s`,
`Σ_l w_l [3(e_l−u)·F + 9(e_l·u)(e_l·F)] M[s,l]`, and the collision applies
`m += (1 − 0.5 S_s) · GuoF_s`.

These differ in both the moment-space content (the Guo form is built from the
`3` and `9` factors, i.e. `1/c_s²` and `1/c_s⁴`) and the prefactor. The current
header records that the pre-fix version omitted the `3`/`9` weights and measured
`eff = 0.332` instead of `1.0`, and that the fixed version measures `eff = 0.9933`
on the Poiseuille regression. The paper's form needs no such calibration because
its moment-space source is exact by construction. Recorded as `DIFFERENT`; the
element is disabled in `L17_CORE`'s canonical runs, so it is not a confound.

### A.7 Row 14 — `MATHEMATICALLY_EQUIVALENT` (gradient stencil)

`PAPER_FORMULATION.md` §4.3 proves that `Σ_i 3W_i c_{iα} ψ(x+c_i)` has an exact
identity second-rank lattice sum and an isotropic fourth-rank lattice sum
(`T_xxxx = 1 = 3K`, `T_xxyy = 1/3 = K`), which is the content of "fourth-order
isotropic discretization". The current `Compute_C` is
`C = Σ_s 3 w_s e_s ψ(x+e_s)` — the same operator.

**Caveat, carried from the formulation:** R1 defers the coefficients to R5
(Leclaire et al., J. Sci. Comput. 59, 545 (2014)), which could not be obtained.
So the claim is "the current operator satisfies the isotropy property R1
requires for D3Q19", not "the current operator is byte-identical to R5's". If
R5's published operator uses a wider footprint, this row degrades to
`UNRESOLVED`. This is stated rather than hidden.

### A.8 Rows 16–17 — `DIFFERENT` (perturbation and the σ calibration)

This is the row the executor contract singles out: *"if the current MRT
stress-moment surface-tension formulation is claimed equivalent to the paper
perturbation operator, derive the mapping from distribution-space perturbation
to the moment basis. A successful Laplace test alone is not proof of
equivalence."* The derivation is therefore done in full.

**Paper side.** `PAPER_FORMULATION.md` §5.2 derives, for D3Q19 `W_i` and `B_i`,

`Σ_i ΔN_i^pert = 0`,  `Σ_i ΔN_i^pert c_{iα} = 0`,
`Σ_i ΔN_i^pert c_{iα}c_{iβ} = (2/9) A |F| (n̂_αn̂_β − δ_αβ)`.

With `A = (9/4) ω_eff σ` (Eq. 18):

`ΔΠ^paper_αβ = ω_eff σ |F| [ (1/2) n̂_αn̂_β − (1/2) δ_αβ ]`.

**Current side.** In the current basis (`PAPER_FORMULATION.md` §2.5 identifies the
current rows), the injection is

`Δm1 = a`, `Δm9 = (a/2)(2n_x²−n_y²−n_z²)`, `Δm11 = (a/2)(n_y²−n_z²)`,
`Δm13 = (a/2)n_xn_y`, `Δm14 = (a/2)n_yn_z`, `Δm15 = (a/2)n_xn_z`, with `a = CapA·cc`.

Translating to the momentum-flux tensor: `m1 = tr P − ρ`, `m9 = 2P_xx−P_yy−P_zz`,
`m11 = P_yy−P_zz`, `m13 = P_xy`, `m14 = P_yz`, `m15 = P_xz`. Solving the five
independent linear conditions with the ansatz `ΔP = α₁a δ + α₂a n̂⊗n̂`:

- `Δ tr P = a` gives `3α₁ + α₂ = 1`;
- `Δ(2P_xx−P_yy−P_zz) = (a/2)(3n_x²−1)` gives `α₂ = 1/2`, hence `α₁ = 1/6`;
- the off-diagonal conditions are then satisfied identically.

So the current line injects

`ΔΠ^current_αβ = S · CapA |C| [ (1/2) n̂_αn̂_β + (1/6) δ_αβ ]`

where the factor `S` appears because the injection is into `meq` and the
collision then applies `m ← m − S(m − meq)`; all six injected moments carry
`S = sv`, and `sv = ω_eff` for the stress group.

**Comparison.**

| part | paper | current |
|---|---|---|
| `n̂⊗n̂` coefficient | `+ (1/2) ω_eff σ |F|` | `+ (1/2) ω_eff CapA |C|` |
| `δ` coefficient | `− (1/2) ω_eff σ |F|` | `+ (1/6) ω_eff CapA |C|` |

The **deviatoric part is structurally equivalent** with the identification
`CapA ↔ σ` and `|C| ↔ |F|` — which is consistent with the production line's
independently measured `σ ≈ 1.012·CapA`.

The **isotropic part is not**: it has the **opposite sign** and a magnitude
smaller by a factor of 3.

Status: `DIFFERENT`. The isotropic discrepancy does not enter the Laplace law
(it is a pressure-like term, and a Laplace test measures only the `n̂⊗n̂` part) —
which is precisely why the contract forbids using a passing Laplace test as
proof. The current line's Calibration row is therefore recorded as a real
difference that no Laplace result can detect.

Consequence for validation of the new line: the isotropic part *is* observable
through the interface pressure jump at fixed curvature, so the `L17_CORE`
evidence reports the measured `Δp` at a matched droplet **and** the residual after
subtracting the Laplace prediction, rather than only `σ`.

### A.9 Row 18 — `DIFFERENT` (recoloring)

Paper (at unit density ratio, using `N_i^(e)(ρ,0) = ρW_i`, `PAPER_FORMULATION.md`
§6.2): the pairwise increment is

`ΔN_i = β (ρ_r ρ_b / ρ) W_i cos ϑ_i`.

Current (`collision`, the nine-pair loop):

```
ef      = e[kk] · C
cospsi  = min(g_r[kk], g_r[kk+1], g_b[kk], g_b[kk+1]) · ef/cc
g_r[kk] += cospsi ; g_r[kk+1] -= cospsi
g_b[kk] -= cospsi ; g_b[kk+1] += cospsi
```

At equilibrium the four arguments of `min` are `W_kk ρ_r`, `W_kk ρ_b` (the pair
members share `W` because they lie in the same shell), so the amplitude is
`W_kk · min(ρ_r, ρ_b)`. Hence the current pairwise increment is

`ΔN_kk = min(ρ_r, ρ_b) W_kk cos ϑ_kk`.

Two independent differences:

1. **Amplitude law.** Paper `β ρ_rρ_b/ρ` versus current `min(ρ_r, ρ_b)`. On the
   `ρ = 1` interface: at `ψ = 0` these are `β/4` and `1/2` (ratio `2/β`); at
   `ψ = 0.5` they are `β·0.1875` and `0.25` (ratio `1.33/β`); at `ψ = 0.9` they
   are `β·0.0475` and `0.05` (ratio `1.05/β`). The current amplitude is **not** a
   constant rescaling of the paper's — it has a different functional form. In
   particular the current line has **no `β` at all** (row 19).
2. **Which distribution is recolored.** The paper splits the **post-perturbation
   colour-blind `N_i`**, preserving its non-equilibrium part:
   `(ρ_k/ρ)N_i + …`. The current line builds `g_r = feq(s, ρ_r, v)` and
   `g_b = feq(s, ρ_b, v)` and recolors **those**. Since `feq` is linear in
   density, `g_r + g_b = feq(s, ρ, v)`, i.e. the colour channel is transported as
   the **equilibrium** at the local `(ρ, v)`, with the non-equilibrium part
   dropped. This is a structural difference in how the colour field advects, and
   it is the channel the project's conservation work had to add overlays for
   (row 28).

The current line's `min(...)` also acts as a clamp: off-equilibrium it bounds the
increment by the smallest of the four populations, which the paper's form does
not.

### A.10 Row 23 — `DIFFERENT` (operator ordering)

| | paper | current |
|---|---|---|
| gradient / wetting | computed, then orientation rotated (step 3), between collision and perturbation | `Compute_C` inside the collision kernel, using `psi_solid_f`; no separate wetting step |
| collision | single-phase MRT (step 2) and perturbation (step 4) are **separate operators**; the perturbation is unrelaxed | fused: perturbation enters as an equilibrium shift and is relaxed |
| recoloring | separate operator (step 5) on the post-perturbation `N_i` | fused into the same kernel |
| bounce-back | full-way on solid nodes (step 6) before streaming | half-way on fluid nodes during streaming |
| streaming | single global step (step 7) | split into `streaming1` (colour, atomic, membrane-aware) and `streaming3` (colour-blind) |
| boundary conditions | regularized density/velocity (step 1) | `Boundary_condition` (mass-style overwrite) and `Boundary_condition_psi`, plus `apply_reservoirs` |

The fused structure is not a reordering of the paper's steps; it changes which
quantities are relaxed and where the wetting modification enters. Recorded as
`DIFFERENT`.

---

## 3. What this map implies for the new line

1. The current production solver is **not** a Leclaire-2017 implementation with
   cosmetic differences. The differences cluster in exactly the places the
   project's own history has been fighting: the interfacial forcing (rows 16–17),
   the colour split (row 18), and the wall treatment (rows 15, 20, 21).
2. Rows 6, 7, 12, 19, 21 are `MISSING`; each one is a self-contained, testable
   addition. `IMPLEMENTATION_PLAN.md` lists them with the switch that isolates
   each.
3. Rows 25–28 are current-line engineering with no baseline counterpart. The
   contract requires that they **not** be inherited automatically; the new line
   therefore ships `L17_CORE` with none of them, and offers them only as an
   explicit, separately switchable overlay.
4. No row is marked `MATHEMATICALLY_EQUIVALENT` without a derivation, and the
   one claim the contract specifically warned about (perturbation ↔ stress-moment
   injection) is resolved as `DIFFERENT` by that derivation, not as equivalent.

## 4. Cross-check available at implementation time

The §A.8 derivation makes a falsifiable prediction that the implementation can
test: matching `n̂⊗n̂` coefficients requires `CapA·|C| = σ·|F|`. If a paper-faithful
`L17_CORE` and the production `CapA` line are driven to the same measured `σ`,
then `CapA/σ` must come out to the production line's independently measured
`1/1.012`. The validation report records this as a derived cross-check rather
than as an assumption.
