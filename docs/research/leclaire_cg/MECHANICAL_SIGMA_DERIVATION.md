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

## 6. Measured value and the honest gap

pass-04, `case-11-mechanical-sigma`, σ_input = 0.02, ω_eff = 1:

| quantity | value |
|---|---|
| `sigma_mech` measured | **0.01537** |
| `sigma_input` | 0.02000 |
| ratio | **0.768** |
| prediction from §5 | 1.000 |

The diagnostic is reported against a 0.7–1.3 band (declared before the
run) and passes, but the prediction is 1.0 and the measurement is 0.768.
That 23 % shortfall is a real residual and is **not** explained here.
Candidate causes, none of which was tested:

1. **Discrete `∫|F| dz`.** §5 uses the continuum total variation. The
   discrete isotropic stencil sums to the total variation only up to the
   stencil's truncation error, and for the finite interface width used
   here (2.5 lu) that error is not necessarily small.
2. **Bulk reference.** A single window on one side is used. A non-zero
   residual slope in the bulk (a slowly varying background) would bias the
   integral.
3. **Equilibration.** 800 steps at this width; the profile is close to but
   not necessarily exactly at the discrete fixed point.
4. **Single centreline.** The integral uses one column; a small y- or
   x-dependence would add noise, though not a systematic 23 %.

## 7. Comparison with the other two estimates of σ

| route | value | ratio to σ_input |
|---|---|---|
| input | 0.02000 | 1.000 |
| mechanical (this diagnostic) | 0.01537 | 0.768 |
| Laplace, free-intercept regression (case 03) | see pass-04 SUMMARY | ~1.1 |

The mechanical and Laplace routes **disagree by roughly a factor of 1.5**.
That is the most useful thing this diagnostic produced: it rules out the
simplest explanation of the Laplace offset (a single global constant by
which the solver's surface tension is wrong), because a global constant
would move both estimators in the same direction. Whatever produces the
Laplace offset is therefore specific to the Laplace geometry or to its
pressure estimator, not a uniform prefactor on the perturbation.

This conclusion is offered as a constraint on the next investigation, not
as a diagnosis.

## 8. Status

- prefactor: **closed** from R1 Eqs. (16) and (18) plus the D3Q19 moment
  algebra; no factor invented.
- gate: 0.7–1.3, declared before the run.
- verdict: **PASS** against that band, with the 0.768 ratio reported and
  the 23 % residual left explicitly unexplained.
- `A = (9/4) ω_eff σ` was **not** retuned.
