# PAPER_FORMULATION — Leclaire/Latt D3Q19 colour-gradient LBM

Executable scientific specification for `L17_CORE`, derived from the canonical
source R1 (DOI `10.1103/PhysRevE.95.033306`) with the mandatory additional
sources recorded in `REFERENCE_MANIFEST.md`.

This is a specification, not a paper summary. Every element below states its
source identifier, its D3Q19 specialisation, the exact constants, and whether
the statement is **explicit** in the source, **derived here**, or
**UNRESOLVED**.

Scope of this document: the **D3Q19, single-density-ratio** specialisation that
`L17_CORE` implements. The general DmQn, variable-density-ratio machinery is
transcribed where it defines the baseline but is marked as out of scope for this
task's implementation.

Page convention: R1 is cited as `[R1 Eq.(N), journal p.033306-M / PDF p.M+1]`
(the UNIGE deposition carries a one-page cover sheet). R2/R3/R4 are cited with
their own page numbers as extracted.

---

## 0. Notation, lattice, and constants

### 0.1 D3Q19 connectivity vectors — **explicit** [R1 Table IV, PDF p.26 / journal 033306-25]

R1 fixes a specific velocity ordering. It is reproduced verbatim because the MRT
matrix and the momentum/viscosity index tables are only valid in this ordering
(R1 states this explicitly at journal 033306-5: *"the only difference here
concerns the ordering indexes i of the velocity space which is different from
these studies … so that all the matrices and indexes are presented here with the
same ordering"*).

| i | c_i | i | c_i |
|---|---|---|---|
| 0 | (0, 0, 0) | 10 | (1, 0, 0) |
| 1 | (−1, 0, 0) | 11 | (0, 1, 0) |
| 2 | (0, −1, 0) | 12 | (0, 0, 1) |
| 3 | (0, 0, −1) | 13 | (1, 1, 0) |
| 4 | (−1, −1, 0) | 14 | (1, −1, 0) |
| 5 | (−1, 1, 0) | 15 | (1, 0, 1) |
| 6 | (−1, 0, −1) | 16 | (1, 0, −1) |
| 7 | (−1, 0, 1) | 17 | (0, 1, 1) |
| 8 | (0, −1, −1) | 18 | (0, 1, −1) |
| 9 | (0, −1, 1) | | |

Grouping used by the weight tables:
`{|c_i|² = 0} = {0}`; `{|c_i|² = 1} = {1…6}`; `{|c_i|² = 2} = {7…18}`.

Opposite direction map: `opp(1)=10, opp(2)=11, opp(3)=12, opp(4)=13, opp(5)=14,
opp(6)=15, opp(7)=16, opp(8)=17, opp(9)=18`; `opp(0)=0`.

### 0.2 D3Q19 lattice weights — **explicit** [R1 Table IV, PDF p.26 / journal 033306-25]

| quantity | \|c\|² = 0 | \|c\|² = 1 | \|c\|² = 2 |
|---|---|---|---|
| `W_i` | 1/3 | 1/18 | 1/36 |
| `φ_i` | 0 | 1/12 | 1/24 |
| `ϕ_i` | 1 | −1/12 | −1/24 |
| `ψ_i` | −5/2 | −1/6 | 1/24 |
| `ξ_i` | 0 | 1/4 | 1/8 |
| `B_i` | −2/9 | 1/54 | 1/27 |

`W_i` are the standard D3Q19 weights, so `Σ_i W_i = 1`, `Σ_i W_i c_i c_i = (1/3)I`.

### 0.3 Sound-speed weight ζ — **explicit, with the D3Q19 value resolved by derivation**

[R1 Table VI, PDF p.27 / journal 033306-26] gives ζ as a fraction per lattice.
Text extraction of that table is ambiguous on its own, but the value is pinned
by the constraint R1 states at journal 033306-5: *"the speed of sound weight ζ in
Eq. (11) is chosen such that if the free parameters α_k = W0, then the square of
the isothermal speed of sound will be equal to 1/3"*, together with Eq. (11)
`p_k = ρ_k ζ (1 − α_k)`.

**Derivation** `[DERIVED HERE]`: requiring `ζ(1 − W0) = 1/3` gives the four
fractions the table prints.

| lattice | `W0` | ζ | printed numerator/denominator |
|---|---|---|---|
| D2Q9 | 4/9 | 3/5 | 3 / 5 |
| D3Q15 | 2/9 | 3/7 | 3 / 7 |
| **D3Q19** | **1/3** | **1/2** | **1 / 2** |
| D3Q27 | 8/27 | 9/19 | 9 / 19 |

The extracted numerators `3,3,1,9` and denominators `5,7,2,19` match exactly, so
the reading is confirmed by two independent routes.

**D3Q19 value used by `L17_CORE`: ζ = 1/2.**

### 0.4 Zero-velocity weight α and the density ratio — **explicit** [R1 Eqs.(10)–(12), PDF p.6 / journal 033306-5]

- density ratio: `γ = ρ_r⁰/ρ_b⁰ = (1 − α_b)/(1 − α_r)` (Eq. 10)
- pressure: `p_k = ρ_k ζ (1 − α_k) = ρ_k (c_s^k)²` (Eq. 11)
- interpolation: `α = [ρ_r/(ρ_r+ρ_b)] α_r + [ρ_b/(ρ_r+ρ_b)] α_b` (Eq. 12)
- convention: `α_b = W0` (blue is the least dense), `0 < α_b ≤ α_r < 1`.

**`L17_CORE` scope: unit density ratio, γ = 1 → α_r = α_b = W0 = 1/3 (D3Q19).**
This is the case R1 calls the reference case for the benchmark comparisons. The
task contract's validation matrix does not require a variable density ratio.

Substituting `α = W0` into Eq. (4) collapses the polynomial factor to the
standard one — see §2.4.

---

## 1. Component densities and the colour / order parameter

**Explicit** [R1 Eqs.(2)–(3), PDF p.5 / journal 033306-4]:

- component density: `ρ_k = Σ_i N_i^k`  (Eq. 2)
- colour-blind density: `ρ = Σ_k ρ_k`
- momentum from the colour-blind set: `ρ u = Σ_i N_i c_i`  (Eq. 3)

The colour / order parameter is not given a numbered equation in R1; it is
defined implicitly by the colour gradient, Eq. (17), which is the gradient of
`(ρ_r − ρ_b)/(ρ_r + ρ_b)`. So

`ψ ≡ (ρ_r − ρ_b)/(ρ_r + ρ_b)`, with `ρ_r = (ρ/2)(1+ψ)`, `ρ_b = (ρ/2)(1−ψ)`.

Label for this element: **explicit (Eq. 17 implies it)**, not inferred.

Note for the map: R1's recoloring Eq. (19)–(20) is written with `ρ_r/ρ` and
`ρ_b/ρ`, i.e. it uses the **normalised** component fractions, consistent with
`(ρ/2)(1±ψ)`.

---

## 2. Colour-blind total distribution and the D3Q19 MRT collision

### 2.1 Operator splitting — **explicit** [R1 journal 033306-4, steps (1)–(7)]

R1 states the time step `t → t+1` as an ordered sequence of seven operations.
Quoting the structure of journal 033306-4 with the labels R1 uses:

| step | operation | applies to |
|---|---|---|
| (1) | external boundary condition `N_i^k(x,t*) = Ω⁽⁰⁾(N_i^k(x,t))` | `∀k, ∀i, x ∈ X_E` |
| (2) | **single-phase collision** `|N(x,t**)) = Ω⁽¹⁾(|N(x,t*)))` | `x ∈ X_F` |
| (3) | **wetting boundary condition**: modification of the normal vector | `x ∈ X_W` |
| (4) | **multiphase collision (perturbation)** `N_i(x,t***) = Ω⁽²⁾(N_i(x,t**))` | `∀i, x ∈ X_F` |
| (5) | **multiphase collision (recoloring)** `N_i^k(x,t****) = Ω⁽³⁾(N_i(x,t***))` | `∀k, ∀i, x ∈ X_F` |
| (6) | **full-way bounce-back** `N_i^k(x,t*****) = N_opp(i)^k(x,t****)` | `∀k, ∀i, x ∈ X_S` |
| (7) | **streaming** `N_i^k(x+c_i, t+1) = N_i^k(x, t*****)` | `∀k, ∀i, x ∈ X_L` |

Set definitions — **explicit**: `X_L` lattice sites; `X_F` fluid sites; `X_S`
solid sites; `X_E ⊂ X_F` external-boundary sites; `X_W ⊂ X_F` fluid sites with
at least one solid neighbour.

**This ordering is load-bearing and is the baseline `L17_CORE` must reproduce.**
The two properties that matter most for downstream comparisons:

1. the wetting condition (step 3) acts **between** the single-phase collision and
   the perturbation, and it modifies only the *orientation* of the colour
   gradient used by the perturbation;
2. the perturbation (step 4) acts on the **post-collision colour-blind
   distribution directly**, not on an equilibrium moment. This is a structural
   difference from the current production solver — see
   `CURRENT_VS_LECLAIRE_MAP.md`.

### 2.2 Colour-blind single-phase MRT collision — **explicit** [R1 Eq.(1), PDF p.5 / journal 033306-4]

`Ω⁽¹⁾(|N⟩) = |N⟩ − M⁻¹ K M (|N⟩ − |N⁽ᵉ⁾⟩) + |ΔN⟩`   (Eq. 1)

- `M` — moment matrix, §2.5.
- `K` — diagonal relaxation matrix, §2.6.
- `|ΔN⟩` — external forcing term, §2.7.
- Dirac/kets are R1's notation for expansion in velocity space over index `i`.

### 2.3 The equilibrium `N⁽ᵉ⁾` — **explicit** [R1 Eqs.(4)–(5), PDF p.6 / journal 033306-5]

`N_i⁽ᵉ⁾(ρ,u) = ν[ ψ_i (u·∇ρ) + ξ_i (G : c_i ⊗ c_i) ] + ρ[ φ_i + ϕ_i α + W_i ( 3 c_i·u + (9/2)(c_i·u)² − (3/2) u·u ) ]`   (Eq. 4)

with

`G = (u ⊗ ∇ρ) + (u ⊗ ∇ρ)ᵀ`   (Eq. 5)

and `ν` the **local** kinematic viscosity from §3. The symbol `:` is tensor
contraction; `⊗` is the tensor product.

**D3Q19 specialisation.** Using §0.2:

`N_i⁽ᵉ⁾ = ν[ ψ_i (u·∇ρ) + ξ_i (G:c_i⊗c_i) ] + ρ[ φ_i + ϕ_i α + W_i (3c_i·u + 4.5(c_i·u)² − 1.5 u·u) ]`

### 2.4 Reduction at unit density ratio — **derived here** `[DERIVED HERE]`

At `α = W0` the polynomial part collapses to the standard weight because
`φ_i + ϕ_i W0 = W_i` for D3Q19. Verified against §0.2:

| \|c\|² | `φ_i + ϕ_i·(1/3)` | `W_i` |
|---|---|---|
| 0 | `0 + 1·(1/3)` = 1/3 | 1/3 ✓ |
| 1 | `1/12 − (1/12)(1/3)` = 1/12·(2/3) = 1/18 | 1/18 ✓ |
| 2 | `1/24 − (1/24)(1/3)` = 1/24·(2/3) = 1/36 | 1/36 ✓ |

So at unit density ratio

`N_i⁽ᵉ⁾ = ν[ ψ_i (u·∇ρ) + ξ_i (G:c_i⊗c_i) ] + ρ W_i [1 + 3c_i·u + 4.5(c_i·u)² − 1.5 u·u]`

— the standard density-weighted second-order equilibrium **plus** the two
density-gradient terms carried by `ψ_i` and `ξ_i`.

**Implementation consequence (recorded so it is not lost):** `L17_CORE` must
retain the `ψ_i, ξ_i` terms. A bare `ρ W_i (…)` equilibrium would silently drop
them and is *not* the paper's equilibrium except where `∇ρ = 0` and `u = 0`.
For a uniform-density single-phase test the two coincide exactly, which is why
the stationarity test alone cannot discriminate them — the planar-interface and
`∇ρ ≠ 0` tests are the discriminating ones.

### 2.5 MRT matrix `M` for D3Q19 — **explicit** [R1 Table XI, PDF p.29 / journal 033306-28]

Transcribed from the published table. The extraction was cross-validated two
ways (word-coordinate row reconstruction, and independent identification of rows
3/5/7 as `j_x, j_y, j_z`, row 9 as `2c_x²−c_y²−c_z²`, row 11 as `c_y²−c_z²`,
rows 13/14/15 as `c_xc_y, c_yc_z, c_xc_z` under §0.1's ordering — all 19×3
entries matched).

```
row  0:  1   1   1   1   1   1   1   1   1   1   1   1   1   1   1   1   1   1   1
row  1: -30 -11 -11 -11  8   8   8   8   8   8  -11 -11 -11  8   8   8   8   8   8
row  2:  12  -4  -4  -4  1   1   1   1   1   1  -4  -4  -4  1   1   1   1   1   1
row  3:  0   -1   0   0  -1  -1  -1  -1   0   0   1   0   0   1   1   1   1   0   0
row  4:  0    4   0   0  -1  -1  -1  -1   0   0  -4   0   0   1   1   1   1   0   0
row  5:  0    0  -1   0  -1   1   0   0  -1  -1   0   1   0   1  -1   0   0   1   1
row  6:  0    0   4   0  -1   1   0   0  -1  -1   0  -4   0   1  -1   0   0   1   1
row  7:  0    0   0  -1   0   0  -1   1  -1   1   0   0   1   0   0   1  -1   1  -1
row  8:  0    0   0   4   0   0  -1   1  -1   1   0   0  -4   0   0   1  -1   1  -1
row  9:  0    2  -1  -1   1   1   1   1  -2  -2   2  -1  -1   1   1   1   1  -2  -2
row 10:  0   -4   2   2   1   1   1   1  -2  -2  -4   2   2   1   1   1   1  -2  -2
row 11:  0    0   1  -1   1   1  -1  -1   0   0   0   1  -1   1   1  -1  -1   0   0
row 12:  0    0  -2   2   1   1  -1  -1   0   0   0  -2   2   1   1  -1  -1   0   0
row 13:  0    0   0   0   1  -1   0   0   0   0   0   0   0   1  -1   0   0   0   0
row 14:  0    0   0   0   0   0   0   0   1  -1   0   0   0   0   0   0   0   1  -1
row 15:  0    0   0   0   0   0   1  -1   0   0   0   0   0   0   0   1  -1   0   0
row 16:  0    0   0   0  -1  -1   1   1   0   0   0   0   0   1   1  -1  -1   0   0
row 17:  0    0   0   0   1  -1   0   0  -1  -1   0   0   0  -1   1   0   0   1   1
row 18:  0    0   0   0   0   0  -1   1   1  -1   0   0   0   0   0   1  -1  -1   1
```

Row identification (used only for sanity checks; the implementation uses the
matrix, not these labels):

- 0 = density `ρ`; 3, 5, 7 = momenta `j_x, j_y, j_z` (R1 Table VII: `p_x=3`,
  `p_y=5`, `p_z=7` for D3Q19);
- 9 = `2c_x²−c_y²−c_z²`, 11 = `c_y²−c_z²`, 13 = `c_xc_y`, 14 = `c_yc_z`,
  15 = `c_xc_z` — the **stress** moments;
- 1 and 2 are energy-like and energy-square-like moments in **this** basis;
  4, 6, 8 are energy-flux-like and 10, 12, 16, 17, 18 higher-order (ghost)
  moments.

**Warning carried forward.** Rows 1 and 2 of this basis are **not** the rows the
current production solver uses (the production `M` row 1 is `[−1,0,…,0,1,…,1]`).
This is a change of basis, not a physics change, *provided* the relaxation
assignment is carried with it. See `CURRENT_VS_LECLAIRE_MAP.md` §3.

### 2.6 Relaxation matrix `K` — **explicit** [R1 journal 033306-5, R1 Table VIII, PDF p.28 / journal 033306-27]

R1: *"The diagonal matrix K is also lattice dependent and the diagonal
coefficients K_υ,υ are related to the viscosity of the fluids, so their values
are set to the usual effective relaxation parameter ω_eff. The indexes υ are
given in Table VIII … The other diagonal coefficients are set to χω_eff. The
constant factor 0 < χ ≤ 1 may improve the stability of the model. With χ = 1,
the multiple-relaxation-time operator becomes a single-relaxation-time
operator."*

D3Q19 viscosity indexes, **explicit** [Table VIII]: `υ ∈ {9, 11, 13, 14, 15}` —
exactly the five stress moments identified above.

So for D3Q19:

```
K[j,j] = ω_eff        for j in {9, 11, 13, 14, 15}
K[j,j] = χ · ω_eff    otherwise
```

Conserved moments are `j ∈ {0,3,5,7}`. R1 does not list an exception for them;
because `m_j = m_j⁽ᵉ⁾` exactly for conserved moments, assigning them `χω_eff`
changes nothing. `L17_CORE` follows the literal reading (all non-`υ` entries get
`χω_eff`) and documents that the choice is immaterial.

R1's stability guidance — **explicit**: lowering `χ` may improve stability but
"lowering this value too much may affect accuracy" (journal 033306-5). R2's
benchmark uses `χ = 1` for D2Q9 and reports MRT-vs-SRT differences; R1's porous
network runs use `χ = 4/5` (per the project's own note on the random-network
case). **`L17_CORE` default: χ = 1** (the single-relaxation-time limit, which is
the simplest faithful reading of the published formula and matches the
benchmark paper's main setting); `χ` is exposed as a parameter, not hard-coded.

### 2.7 External force term — **explicit** [R1 Eqs.(6)–(9), PDF p.6 / journal 033306-5]

`|ΔN⟩ = M⁻¹ |Δm⟩`   (Eq. 6)

`|Δm⟩` has all components zero except the momentum indexes:
`Δm_{p_x} = ρ g_x`, `Δm_{p_y} = ρ g_y`, `Δm_{p_z} = ρ g_z`   (Eqs. 7–9)

with `p_x, p_y, p_z` per Table VII (D3Q19: 3, 5, 7) and `g` the acceleration.

**Note.** R1's forcing is a **plain momentum-source injection in moment space**,
not the Guo (2002) scheme with `1/c_s²` and `1/c_s⁴` weights that the current
production solver uses. The paper's `|ΔN⟩` already equals the intended momentum
increment per step (because `M⁻¹|Δm⟩` contributes `Σ_i ΔN_i c_i = Δm` exactly),
so there is no `(1 − ½K)` prefactor in Eq. (1). See
`CURRENT_VS_LECLAIRE_MAP.md` §7.

`L17_CORE` scope: this term is implemented but **disabled by default** (`g = 0`);
the canonical validation set is driven by reservoirs/geometries rather than body
force. The element is still specified so that the A/B attribution is possible.

---

## 3. Viscosity interpolation — **explicit** [R1 Eqs.(13)–(14), PDF p.6 / journal 033306-5]

Harmonic, density-weighted:

`1/ν = [ρ_r/(ρ_r+ρ_b)] (1/ν_r) + [ρ_b/(ρ_r+ρ_b)] (1/ν_b)`   (Eq. 13)

`ω_eff = 2 / (6ν + 1)`   (Eq. 14)

R1 adds: *"Note that other viscosity interpolation schemes are possible [62]."*

For equal viscosities `ν_r = ν_b = ν`, Eq. (13) gives `ν` everywhere and
`ω_eff` is a constant — the case used by all `L17_CORE` canonical tests.

**Distinction that must not be lost:** R1's Eq. (13) is a harmonic average of
**kinematic viscosity** `ν`. The current production solver's blend is a
quadratic polynomial in `ψ` of the relaxation rate on a narrow band. These are
different objects; see `CURRENT_VS_LECLAIRE_MAP.md` §4.

---

## 4. Colour-gradient stencil / isotropic weights

### 4.1 What R1 states — **explicit**

- `F = ∇[ (ρ_r − ρ_b)/(ρ_r + ρ_b) ]`   (Eq. 17)
- R1 §II.B: the wetting condition rotates `F`, keeping `|F|`.
- R1 §III: *"…the color F and the density ∇ρ gradients, **3D fourth-order
  isotropic discretizations** [88] are used on all lattice sites"* [R1 PDF p.24
  and PDF p.26; the same sentence also appears in R1's method summary].
- Reference [88] is Leclaire, El-Hachem, Trépanier, Reggio, J. Sci. Comput. **59**,
  545 (2014), DOI `10.1007/s10915-013-9772-2`.

### 4.2 Status of the exact coefficients — **UNRESOLVED**

R1 does **not** print the stencil coefficients; it defers to [88], and [88] is
not obtainable (see `REFERENCE_MANIFEST.md`, R5 — no OA location, no repository
copy, no Wayback PDF). Therefore the literal published coefficient set for the
gradient is **UNRESOLVED** and `L17_CORE` may not claim to reproduce it
byte-for-byte.

### 4.3 Working stencil actually implemented — **derived here** `[DERIVED HERE]`

`L17_CORE` uses the second-neighbour-shell lattice gradient

`F_α(x) = 3 Σ_i W_i c_{iα} ψ(x + c_i)`

and the derivation that this operator is **fourth-order isotropic on D3Q19** is
supplied here rather than attributed to R5.

*Derivation.* Write the estimate `g_α = Σ_i a_i c_{iα} ψ(x+c_i)` with `a_i`
depending only on `|c_i|`. Taylor-expanding,

`g_α = (Σ_i a_i c_{iα}c_{iβ}) ∂_βψ + (1/6)(Σ_i a_i c_{iα}c_{iβ}c_{iγ}c_{iδ}) ∂_β∂_γ∂_δψ + …`

(odd-rank sums vanish by lattice symmetry). With `a_i = 3W_i`:

- 2nd rank: `Σ_i 3W_i c_{iα}c_{iβ} = δ_{αβ}` — the identity operator. ✓
- 4th rank: shell weights `3·(1/18) = 1/6` (6 axis directions) and
  `3·(1/36) = 1/12` (12 face diagonals). Then
  `T_{xxxx} = (1/6)(2) + (1/12)(8) = 1`,
  `T_{xxyy} = (1/6)(0) + (1/12)(4) = 1/3`,
  and all odd components vanish. The isotropic 4th-rank form
  `K(δ_{αβ}δ_{γδ}+δ_{αγ}δ_{βδ}+δ_{αδ}δ_{βγ})` has `T_{xxxx}=3K`, `T_{xxyy}=K`;
  `K = 1/3` reproduces both. ✓

Hence the leading anisotropic error is absent at 3rd and 4th order: the residual
3rd-order term is `(1/6)∂_α(∇²ψ)`, which is **isotropic**, and this is exactly
the sense in which R1's "fourth-order isotropic discretization" is meant.

*Consequence for the map.* Under this reading the current production solver's
`Compute_C` (a `Σ 3 w_i e_i ψ` sum, with solid neighbours supplying a wall
colour) uses the **same operator**; the difference is in the *wall sampling*,
not in the stencil. This is recorded as `SAME` on the stencil and `DIFFERENT` on
the wall sampling in `CURRENT_VS_LECLAIRE_MAP.md`.

*Honest caveat for the reviewer.* If R5's published operator is in fact a
different (larger-footprint) stencil, then `L17_CORE` differs from the published
runs on this one element. Nothing else in the formulation depends on it, and the
difference would be an isotropy-order refinement, not a change of physics.

---

## 5. Perturbation (interfacial-tension) operator

### 5.1 Statement — **explicit** [R1 Eqs.(15)–(18), PDF p.6 / journal 033306-5]

`Ω_i⁽²⁾(N_i) = N_i + ΔN_i^pert`   (Eq. 15)

`ΔN_i^pert = A |F| [ W_i (F·c_i)²/|F|² − B_i ]`   (Eq. 16)

`F = ∇[ (ρ_r − ρ_b)/(ρ_r + ρ_b) ]`   (Eq. 17)

`A = (9/4) ω_eff σ`   (Eq. 18)

`B_i` per §0.2. `A` is space- and time-dependent (through `ω_eff`, i.e. through
the local viscosity); `σ` is the target interfacial tension.

R1 attributes the validity of this operator — that it reproduces the capillary
stress tensor of the macroscopic two-phase equations when `B_i` are well chosen —
to Reis & Phillips [43] and Liu et al. [35].

### 5.2 Conserved quantities and the capillary stress — **derived here** `[DERIVED HERE]`

Using D3Q19 `W_i` and `B_i`:

- zeroth moment. `Σ_i W_i (F̂·c_i)² = (1/3)|F̂|² = 1/3` and
  `Σ_i B_i = −2/9 + 6(1/54) + 12(1/27) = 1/3`. Hence
  **`Σ_i ΔN_i^pert = 0` — mass is conserved exactly.**
- first moment. Both `Σ_i W_i (F̂·c_i)² c_{iα}` and `Σ_i B_i c_{iα}` vanish by
  lattice symmetry (odd rank). Hence
  **`Σ_i ΔN_i^pert c_{iα} = 0` — momentum is conserved exactly.**
- second moment. With `Σ_i W_i c_{iα}c_{iβ}c_{iγ}c_{iδ} = (1/9)(δ_{αβ}δ_{γδ} +
  δ_{αγ}δ_{βδ} + δ_{αδ}δ_{βγ})`,

  `Σ_i W_i (F̂·c_i)² c_{iα}c_{iβ} = (1/9)(δ_{αβ} + 2F̂_αF̂_β)`

  and `Σ_i B_i c_{iα}c_{iβ} = δ_{αβ}/3` (shell 1 contributes `2/54 = 1/27`,
  shell 2 contributes `8/27`). Therefore

  **`Σ_i ΔN_i^pert c_{iα}c_{iβ} = (2/9) A |F| (F̂_αF̂_β − δ_{αβ})`**

  i.e. the perturbation adds a momentum-flux contribution of exactly the
  capillary-stress **structure**: an isotropic subtraction plus an `n̂ ⊗ n̂`
  addition, with the isotropic and deviatoric parts locked in the fixed ratio
  `−1 : +1`.

This ratio is the fingerprint used in `CURRENT_VS_LECLAIRE_MAP.md` to test the
production solver's moment-space injection for equivalence.

### 5.3 Ordering and scope

- The perturbation is applied **after** the single-phase collision and the
  wetting modification, and **before** recoloring (steps 3→4→5).
- It is applied on **all fluid sites** `x ∈ X_F`.
- The added term is **not** relaxed; it is added directly to `N_i` (contrast
  with the production solver, which injects into the equilibrium and lets the
  collision relax it).

`|F|` in Eqs. (16) and (18) is the **discrete gradient magnitude at the node**,
computed with the §4.3 operator and, at wall-adjacent nodes, with the §6.3
re-oriented `F`.

---

## 6. Explicit `β` semantics, recoloring, and interface-width control

### 6.1 Recoloring operator — **explicit** [R1 Eqs.(19)–(20), PDF p.7 / journal 033306-6]

`Ω_i^r⁽³⁾(N_i) = (ρ_r/ρ) N_i + β (ρ_r ρ_b/ρ²) cos(ϑ_i) N_i⁽ᵉ⁾(ρ, 0)`   (Eq. 19)

`Ω_i^b⁽³⁾(N_i) = (ρ_b/ρ) N_i − β (ρ_r ρ_b/ρ²) cos(ϑ_i) N_i⁽ᵉ⁾(ρ, 0)`   (Eq. 20)

with:
- `N_i` the **colour-blind post-perturbation** distribution (step 5 input);
- `N_i⁽ᵉ⁾(ρ, 0)` the equilibrium Eq. (4) evaluated at the **total** density `ρ`
  and **zero velocity**;
- `ϑ_i` the angle between the colour gradient `F` and the lattice vector `c_i`.

**D3Q19 evaluation of the zero-velocity equilibrium** `[DERIVED HERE]`: at `u = 0`
the terms `ψ_i (u·∇ρ)` and `ξ_i (G:c_i⊗c_i)` both vanish identically because
both are linear in `u` (Eq. 5). So

`N_i⁽ᵉ⁾(ρ, 0) = ρ (φ_i + ϕ_i α)`, which at `α = W0` reduces to `ρ W_i` (§2.4).

**The `i = 0` term.** `c_0 = 0`, so `ϑ_0` is undefined and `cos ϑ_0` is taken as
`0`. This is **not stated explicitly** in R1; it is recorded as a convention.
It is the only choice consistent with Eq. (16)'s structure and with exact
conservation: with `cos ϑ_0 ≡ 0`, `Σ_i cos ϑ_i N_i⁽ᵉ⁾(ρ,0) = ρ Σ_i W_i
(F̂·c_i) = 0`, so `Σ_i Ω_i^r = (ρ_r/ρ) Σ_i N_i = ρ_r` **exactly**, giving exact
component-mass conservation. Label: **derived/convention**.

### 6.2 Pairwise form used by `L17_CORE` — **derived here** `[DERIVED HERE]`

For the opposite pair `(i, opp(i))`, `W_i = W_opp(i)` and `c_opp(i) = −c_i`, so
`cos ϑ_opp(i) = −cos ϑ_i`. The two symmetric members therefore receive equal and
opposite corrections:

`ΔN_i = +β (ρ_r ρ_b/ρ) W_i cos ϑ_i`, `ΔN_opp(i) = −β (ρ_r ρ_b/ρ) W_i cos ϑ_i`
(at unit density ratio, using `N⁽ᵉ⁾ = ρW_i`).

This is the form `L17_CORE` implements, over the nine opposite pairs of D3Q19
`(1,10) (2,11) (3,12) (4,13) (5,14) (6,15) (7,16) (8,17) (9,18)`, with the rest
population left untouched.

### 6.3 `β` semantics and interface-width control — **explicit, partially**

[R1 Eq. (19), journal 033306-6]: `β = β* (Δx/Δx*)^η`, where `Δx*` and `Δx` are
**physical** spacing steps (explicitly *"not spacing steps in lattice units"*),
`β*` and `Δx*` are reference values "that would be used on a coarse lattice", and
`η` is "linked to the rate at which the numerical interface thickness is reduced
in the physical space with lattice refinement" [77].

R1 does **not** give a closed-form `β ↔ interface-width` relation. It only
states that `β` *controls* the numerical interface thickness.

R2 supplies the operative clarification — **explicit** [R2, extracted p.15 and
p.6]: for the CGM the Cahn number (dimensionless interface thickness) is
controlled **solely** by the recoloring parameter and, unlike the pseudopotential
model, **does not vary with the physical parameters**; `β` and the physical
parameters are mutually independent knobs.

**Consequences recorded for the validation matrix:**
- the paper's own scaling law `β = β*(Δx/Δx*)^η` requires **two** resolutions to
  calibrate `(β*, η)`; a single-resolution measurement cannot test it;
- because our runs are in lattice units, `Δx/Δx*` is the lattice-refinement
  ratio. The honest test at fixed lattice is therefore the **`β ↔ measured
  interface width` monotonic-response curve**, not a claim about a specific `η`.
  This is what test 5 of the required canonical set measures, and the report
  states explicitly that `η` is **not** determined by it.

---

## 7. Wetting boundary condition

**Explicit** [R1 §II.E, Eqs.(30)–(33) and Eqs.(34)–(38), journal 033306-7…-9].

### 7.1 Principle

The contact angle is imposed by changing **only the orientation** of the colour
gradient near the wall: `F = |F| n_c` is rotated so that its angle with the wall
normal `n_w` equals the target `θ_c`. **`|F|` is unchanged** — R1 calls this "a
kind of Dirichlet boundary condition only for the orientation of the color
gradient". This is executed on `x ∈ X_W`, i.e. fluid sites with at least one
solid neighbour, at step (3), i.e. after the single-phase collision and before
the perturbation.

R1's stated motivation — **explicit** [journal 033306-8]: the widely used
"fictitious coloured densities in the solid lattice sites" approach (the
standard GRLR wetting BC) "may lead to a nonphysical fluid flow in a thin layer
along the solid boundary" and the contact angle is "not accurately captured",
requiring case-by-case fine-tuning. R1 asserts the proposed BC "automatically
works for complex geometry".

### 7.2 The secant solve — **explicit** [Eqs.(30)–(33)]

Solve `f(v_c) = v_c · n_w − |v_c| cos θ_c = 0`   (Eq. 30)

One equation, three unknowns; the solution set is a cone about `n_w`. R1
resolves it by restricting the search to the plane spanned by `n_c` and `n_w`:

`v_c⁽⁰⁾ = n_c`   (Eq. 31)

`v_c⁽¹⁾ = n_c − λ (n_c + n_w)`   (Eq. 32)

`v_c⁽ⁿ⁾ = [ v_c⁽ⁿ⁻²⁾ f(v_c⁽ⁿ⁻¹⁾) − v_c⁽ⁿ⁻¹⁾ f(v_c⁽ⁿ⁻²⁾) ] / [ f(v_c⁽ⁿ⁻¹⁾) − f(v_c⁽ⁿ⁻²⁾) ]`   (Eq. 33)

**Published parameter choices — explicit:** `λ = 1/2` "for simplicity", and the
iteration **always stops at `n = 2`** to avoid unnecessary cost (the argument
being that the interface orientation changes little per LBM step, so `n_c` is
already a good initial guess).

Finally `v_c⁽²⁾` is **normalised** (the recurrence does not preserve norm) and
replaces the `n_c` used in the perturbation step.

### 7.3 Wall normal `n_w` — **explicit** [Eqs.(34)–(38), journal 033306-9]

Preprocessing, once, before the time loop:

1. smooth the binary solid indicator `g` three times with a D3Q27-weighted
   3×3×3 stencil: `g⁽ⁿ⁾(α,β,γ) = Σ_{i,j,k=−1}^{1} w(i²+j²+k²) g⁽ⁿ⁻¹⁾(α+i,β+j,γ+k)`
   (Eq. 34) with `w(0)=8/27, w(1)=2/27, w(2)=1/54, w(3)=1/216` (Eqs. 35–38);
2. `n_w = ∇g⁽³⁾` at the fluid sites near the boundary, using the same gradient
   operator as §4.3; store it.

R1 notes the gradient of the **un**smoothed grey image may be used directly if a
grey (micro-CT) image is available; the binary `g` is still needed elsewhere.

### 7.4 `L17_CORE` status

- Implemented in full for D3Q19, including the three-iteration smoothing and the
  `n = 2` secant with `λ = 1/2` normalisation.
- **`θ_c` sign convention:** R1's `f` uses `cos θ_c` with `n_c` the gradient
  normal. The direction convention (whether `θ_c` is measured through the red or
  the blue phase) is **not stated explicitly** in R1's Eq. (30). R3 §2.2.2
  records that the colour-gradient literature measures `θ` "through the red
  fluid" up to a point and then switches to blue-phase convention. Therefore the
  measured contact angle from `L17_CORE` is reported **together with the
  measured `ψ`-side it was evaluated on**, so that the convention is visible in
  the evidence rather than assumed. This is flagged as a genuine ambiguity
  inherited from the sources.

---

## 8. Solid handling and bounce-back ordering

**Explicit** [R1 journal 033306-4, step (6)]:

`N_i^k(x, t*****) = N_opp(i)^k(x, t****)`, `∀k, ∀i, ∀x ∈ X_S`

i.e. **full-way bounce-back at solid nodes**, applied to the two *coloured*
distributions after recoloring, before the global streaming step (7).

Consequences that `L17_CORE` must respect:

- Solid nodes hold distributions for the whole lattice (so `X_L` includes
  `X_S`; R1's step (7) streams over all of `X_L`).
- Bounce-back is applied **per colour**, which is what makes it possible for
  component densities to be exchanged with walls without a separate wall
  closure.
- R1 cites [70] for this form; it is the classical full-way (or "bounce-back on
  the solid node") scheme, **not** the half-way bounce-back that the production
  solver implements by returning the packet to the originating fluid node.

---

## 9. Regularized density / velocity open boundaries

**Explicit, and out of scope for `L17_CORE` execution** [R1 §II.D, Eqs.(21)–(29),
journal 033306-6…-7].

R1 generalises the single-phase regularized density and velocity boundary
conditions [67] to lattices whose zero-velocity weight is variable:

- `Υ_k⁽²⁾ = (c_s^k)² = ζ(1 − α_k)`   (Eq. 21)
- `Υ_k⁽⁴⁾ = λ Υ_k⁽²⁾`, with `λ = 1/3` for **all** of D2Q9/D3Q15/D3Q19/D3Q27
  (Eq. 22; R1 explicitly calls this "a subtle consideration")
- reconstruction: `N_i = N_i⁽⁰⁾(ρ_bc, u_bc) + N_i⁽¹⁾(P_bc⁽¹⁾)`   (Eq. 23)
- density from the incoming/zero/normal subsets:
  `ρ_bc = [1/(1+u_⊥)](2ρ⁺ + ρ⁰)`   (Eq. 24), with
  `ρ⁰ = Σ_{i: c_i·n=0} N_i` (Eq. 25) and `ρ⁺ = Σ_{i: c_i·n>0} N_i` (Eq. 26)
- off-equilibrium closure `N_i⁽¹⁾ = [W_i/(2Υ⁽⁴⁾)] Q_i : P⁽¹⁾`, `Q_i = c_ic_i − Υ⁽²⁾I`
  (Eq. 27), with `N_i⁽¹⁾ = N_opp(i)⁽¹⁾` for `c_i·n < 0` (Eq. 28) and
  `P⁽¹⁾ = Σ_i Q_i N_i⁽¹⁾` (Eq. 29).

At unit density ratio (`α = W0`, D3Q19) these reduce to `Υ⁽²⁾ = 1/3`,
`Υ⁽⁴⁾ = 1/9` — the textbook values, and the generalisation becomes inert.

**Decision for this task:** `L17_CORE` does **not** implement Eqs. (21)–(29). The
canonical validation matrix in the executor contract is satisfiable with
periodic, no-slip and reservoir-style boundaries, and a partial or approximated
regularized open-boundary implementation would be a larger fidelity risk than
omitting it. This is recorded as an explicit scope exclusion, not as an
unremarked gap. `FOLLOWUP_OPTIMIZATION_MAP.md` lists it as a future switchable
element.

---

## 10. Summary of implementation-relevant constants (D3Q19, unit density ratio)

| symbol | value | source |
|---|---|---|
| `W_i` | 1/3, 1/18, 1/36 | R1 Table IV |
| `φ_i` | 0, 1/12, 1/24 | R1 Table IV |
| `ϕ_i` | 1, −1/12, −1/24 | R1 Table IV |
| `ψ_i` | −5/2, −1/6, 1/24 | R1 Table IV |
| `ξ_i` | 0, 1/4, 1/8 | R1 Table IV |
| `B_i` | −2/9, 1/54, 1/27 | R1 Table IV |
| `ζ` | 1/2 | R1 Table VI + derivation (§0.3) |
| `α` | 1/3 (= `W0`) | R1 Eq. (10) at `γ = 1` |
| `M` | 19×19 integer matrix, §2.5 | R1 Table XI |
| `υ` (viscosity moments) | {9, 11, 13, 14, 15} | R1 Table VIII |
| `p` (momentum moments) | {3, 5, 7} | R1 Table VII |
| `ω_eff` | `2/(6ν+1)` | R1 Eq. (14) |
| `Υ⁽²⁾`, `Υ⁽⁴⁾` | 1/3, 1/9 | R1 Eqs. (21)–(22) at `α = W0` |
| `A` | `(9/4) ω_eff σ` | R1 Eq. (18) |
| `λ` (secant) | 1/2, stop at n=2 | R1 Eqs. (31)–(33) |
| smoothing weights | 8/27, 2/27, 1/54, 1/216, 3 passes | R1 Eqs. (34)–(38) |

## 11. Items explicitly labelled UNRESOLVED

1. **Exact published gradient stencil coefficients** — R1 defers to R5 [88],
   which could not be obtained. `L17_CORE` implements a stencil with an
   independent fourth-order-isotropy proof (§4.3) and says so.
2. **Contact-angle sign convention in Eq. (30)** — not stated in R1; reported
   with the measured phase instead of assumed (§7.4).
3. **`η` in the `β` refinement law** — requires two physical resolutions to
   calibrate; not determined by the lattice-unit tests in this task (§6.3).
4. **Whether the rest population participates in recoloring** — R1 writes
   `∀i`; `cos ϑ_0` is undefined, so `cos ϑ_0 ≡ 0` is adopted as a convention and
   shown to be the mass-conserving choice (§6.1).

No other element of this formulation was filled in by intuition.
