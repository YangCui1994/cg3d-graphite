# Mechanical surface tension for a planar interface — derivation

Status: **derivation + diagnostic**. The diagnostic is implemented as
`case-11-mechanical-sigma` in the pass-04 artifact tree.

Purpose: obtain an estimate of the surface tension that does **not** go
through the Laplace pressure, so the Laplace calibration can be checked
against an independent route.

This document sources every prefactor before any code was written
(`LECLAIRE_PASS4_VALIDATION_CONTRACT.md` §7).

---

## 1. What is being computed

For a planar interface with unit normal `n`,

    sigma = ∫ (P_N - P_T) dn

where `P_N = n_a n_b Π_ab` is the normal component of the momentum-flux
tensor and `P_T` is the tangential component. Every prefactor below is
sourced; nothing is fitted.

## 2. The perturbation's second moment

R1 Eq. (16), with `F̂ = F/|F|`:

    ΔN_i^pert = A |F| [ W_i (F̂ · c_i)^2 − B_i ]

`A` is R1 Eq. (18): `A = (9/4) ω_eff σ`.

Contracting over the D3Q19 weights (`PAPER_FORMULATION.md` §5.2), using
`Σ_i W_i c_a c_b c_g c_d = (1/9)(δ_ab δ_gd + δ_ag δ_bd + δ_ad δ_bg)` and
`Σ_i B_i c_a c_b = δ_ab / 3`:

    Σ_i ΔN_i^pert c_a c_b = (2/9) A |F| (F̂_a F̂_b − δ_ab)

so the perturbation's contribution to the momentum-flux tensor is

    ΔΠ_ab = (2/9) A |F| (n_a n_b − δ_ab)                                    (★)

## 3. Which components, and the value for a planar interface

Take the interface normal along `z`, `n = ẑ`. Then

    ΔΠ_zz = (2/9) A |F| (1 − 1)  =  0
    ΔΠ_xx = ΔΠ_yy = (2/9) A |F| (0 − 1) = −(2/9) A |F|

So the interface contribution to the normal–tangential difference is

    P_N − P_T  :=  Π_zz − Π_xx  =  (2/9) A |F|                             (†)

`Π_xx = Π_yy` for an isotropic planar interface, so either in-plane
direction may serve as `P_T`; the diagnostic uses their mean.

## 4. Discrete quadrature

    sigma_mech = Σ_z [ (Π_zz(z) − Π_zz^bulk) − (Π_xx(z) − Π_xx^bulk) ] · Δz

with Δz = 1 in lattice units, a plain sum over nodes (the simplest
quadrature consistent with the lattice; no weighting is invented). The
bulk reference is the mean over a window far from the interface on one
side of the box. The subtraction is what removes the constant `ρ/3`
background and leaves the interface contribution.

## 5. Closure of the prefactor

Because the perturbation is applied to the distribution **after** the
collision (R1 step 4) and is **not relaxed**, it enters the post-collision
population and therefore the momentum flux **directly**. No collision or
relaxation prefactor is required.

This is the point to be explicit about, because it is where a factor would
otherwise be invented: in an equilibrium-shift formulation the same
perturbation would be relaxed and a factor of order `S` or `(1 − S/2)`
would appear here. `L17_CORE` uses the paper's unrelaxed operator, so the
raw second moment (★) *is* the stress contribution.

Setting `∫|F| dz` for a monotone profile running from ψ = −1 to ψ = +1:
`|∇ψ|` integrates to the total variation, which is exactly **2**,
independent of the profile width or shape. Hence

    sigma_mech = (2/9) A · 2 = (4/9) A
               = (4/9) · (9/4) ω_eff σ
               = ω_eff σ

At `ω_eff = 1` this is exactly `σ_input`. **The derivation therefore
predicts `sigma_mech / sigma_input = 1` with no free parameter.**

## 6. Measured value

Two passes have run this diagnostic. **The Pass-4 number is a failed
diagnostic and is kept only as history; the Pass-5 number is the current
result.**

### 6.1 Pass-4 — failed diagnostic (superseded)

| quantity | value |
|---|---|
| `sigma_mech` | 0.01537 |
| `sigma_input` | 0.02000 |
| ratio | 0.768 |
| prediction from §5 | 1.000 |

That run integrated over the whole periodic domain, which contains **two**
interfaces, and subtracted a bulk reference taken from a window that was not
demonstrably clear of the interface shoulder. External review R3-7 therefore
required the geometry and the reference window to be corrected, and
reclassified the result as `EXPLORATORY / UNGATED`. The 23 % shortfall in
that run is **not** explained by any physical effect; it was a diagnostic
defect.

### 6.2 Pass-5 — corrected and recomputable

The case now isolates exactly ONE of the two periodic interfaces, places
the bulk reference at the midpoint between them, retains the full `N_i`
distribution in the raw snapshot so the stress observable is recomputable
from the committed file alone, and reports the discrete total variation as
a consistency check.

| quantity | value |
|---|---|
| `sigma_mech` | **0.0199999067** |
| `sigma_input` | 0.0200000000 |
| ratio | **0.9999953** |
| discrete total variation | 2.0000 (continuum target 2, rel. error 0.0000) |
| interfaces in the integration window | 1 |

The committed stress profile sums over the stated integration window to the
same 0.0199999067, so the reported metric is reproduced by the profile
itself at the text-evidence level. All four E8 premises are closed, so this
is a validating verdict rather than an exploratory one.

*Precision note.* The retained raw arrays are f32 even though the solver is
f64 (schema `l17c_core_raw_f32_v2`, stated explicitly for this reason). For
this integral the f32 retention is sufficient; a binary-level recomputation
reproduces the quoted ratio to the precision the raw file carries.

## 7. Comparison with the other estimates of σ

| route | value / σ_input |
|---|---|
| input | 1.000 |
| mechanical (this diagnostic, Pass-5) | **1.000** |
| Laplace, per-radius local values (case 03) | 1.018 – 1.056 |
| Laplace, zero-intercept fit | 1.041 |
| Laplace, free-intercept regression | 1.127 |

The Pass-4 comparison in this section previously read 0.768 for the
mechanical route and concluded that a single global prefactor was ruled out.
The Pass-5 result **sharpens** that conclusion rather than reversing it: the
mechanical observable now returns σ_input essentially exactly, while the
Laplace routes sit 2–13 % high with a clear finite-radius/intercept
structure.

The consequence is that suspicion moves further away from a global
amplitude error in the R1 perturbation — which mechanical sigma now
contradicts at the 5e-6 level — and toward the Laplace measurement itself:
slope/intercept coupling, the finite-radius correction, the pressure
estimator, and the radius definition. That is a constraint on the next
investigation, not a diagnosis.

## 8. Status

- prefactor: **closed** from R1 Eqs. (16) and (18) plus the D3Q19 moment
  algebra; no factor invented.
- premises (external review E8): **all closed** — one interface isolated, clean
  bulk window, full `N_i` retained, discrete total-variation consistency
  verified at 2.0000.
- gate: 0.7–1.3, declared before the run.
- verdict: **PASS**, ratio 0.9999953.
- `A = (9/4) omega_eff sigma` was **not** retuned.
