# V1b External Scientific Review — BI-V1B-DIAGNOSTIC-001

## Binding

- Product branch: `agent-task/BI-V1B-DIAGNOSTIC-001`
- Base: `e9540bcadb86257c70b805afc98f2eec9626c64e`
- Candidate: `a9c6db87da2eeb3572607152391fe6863394ebee`
- Fresh internal reviewer: `HUMAN_REQUIRED`
- Review scope: external scientific interpretation and next-step decision

## Executive decision

The internal `HUMAN_REQUIRED` decision is correct **under the frozen V1b
contract**, because the declared static-scaling and raw `V/V_hyd` gates
fail.

However, the evidence does **not** support the stronger interpretation that
the bulk hydraulic model or wall-wetting implementation is already shown to
be inconsistent.

V1b has instead isolated two effects:

1. a localized open-boundary resistance that remains substantial;
2. finite-resolution dependence of the slit capillary calibration.

The most important new result is that the **incremental bulk hydraulic
resistance at h=26 is already consistent with plane-Poiseuille theory to
within about 3.4%** once the localized offset is separated by a length
difference.

Therefore the next step should be a very small V1c convergence/differential
diagnostic, not a solver change and not a repeat of V1b.

V2/V3 remain unstarted until V1c closes this final ambiguity.

## 1. What V1b establishes reliably

### 1.1 Corrected open-boundary layout materially improved the case

h=26 front speed increased from approximately

`3.86e-3 -> 4.97e-3`

after separating the pinned reservoir, membrane and active slit with an open
buffer.

The old fixed-resistance signature was reduced substantially.

This directly confirms that a significant part of V1's apparent wetting-rate
deficit was a boundary-condition artifact rather than a wall-wetting
property.

### 1.2 Front dynamics remain stable and essentially constant velocity

For h=26, h=40 and h=26-2L:

- no NaN/Inf;
- reservoir pressure difference remains zero;
- fronts are monotonic;
- `R2[x,t]` is approximately 0.999998 or higher;
- primary and secondary front definitions agree closely.

Thus the matched-viscosity generalized-Washburn form remains supported:

`x = x0 + V t`.

The old `x^2 proportional to t` gate remains retired for this
configuration.

## 2. Key new result: differential hydraulic consistency at h=26

Define an effective hydraulic length from independently measured dynamic
capillary pressure and front speed:

`L_eff = Pc_dynamic h^2 / (12 mu V_meas)`.

Using committed V1b numbers:

### Short case

- `L1 = 241`
- `Pc1 = 2.884386e-3`
- `V1 = 4.974326e-3`
- `L_eff1 = 326.65 lu`

### Long case

- `L2 = 477`
- `Pc2 = 3.038931e-3`
- `V2 = 3.000209e-3`
- `L_eff2 = 570.60 lu`

Therefore:

`(L_eff2 - L_eff1)/(L2 - L1) = 1.034`.

The ideal bulk slit value is 1.

This is a **3.4% differential error**, comfortably inside the 10% level
used by the project for engineering consistency.

A two-point representation:

`L_eff ~= 1.034 L + 77.5 lu`.

Interpretation:

- the incremental resistance added by more ordinary slit length is
  quantitatively correct;
- an additional localized resistance remains as an intercept;
- the raw gate
  `V_meas = Pc_dynamic h^2/(12 mu L_hyd)`
  failed largely because it implicitly forced that intercept to zero.

This is a materially more informative test than the original g7 ratio.

## 3. Correction to the internal review: equivalent boundary length can depend on h

The internal reviewer argued that an identical x-boundary feature should not
have an equivalent length that changes strongly with slit height.

That inference is not generally valid.

A localized entrance/membrane resistance may scale as, for example,

`Delta p_local ~ mu V / h`

while distributed plane-Poiseuille resistance per unit length scales as

`dp/dx ~ mu V / h^2`.

Expressing the localized loss as an equivalent Poiseuille length then gives

`L_eq ~ h`.

Therefore the larger h=40 equivalent length is not, by itself, proof that
the residual originates at the moving meniscus.

It remains evidence that a localized/non-distributed resistance exists, but
its attribution requires a same-height length differential.

## 4. Static slit calibration: finite-resolution trend, not established failure of the registry

Measured:

- h=26: `C_static = Pc h/(2 sigma) = 0.67048`
- h=40: `C_static = 0.75248`
- droplet registry reference: `cos(30 deg) = 0.86603`.

The 11.5% h26/h40 difference narrowly fails the V1b 10% engineering gate.

The internal review additionally stated that a two-point
`C(h)=C_inf-a/h` extrapolation gives `C_inf ~ 0.42` and an implausible
large limiting angle.

That algebra is incorrect.

Using the two committed values:

`a = (C40-C26)/(1/26-1/40) = 6.09`

and

`C_inf = C26 + a/26 = 0.905`.

This corresponds to approximately

`theta_inf = 25.2 deg`.

With only two resolutions this is **not** evidence that the asymptotic angle
is actually 25.2 degrees. It is, however, a plausible finite-resolution
trend toward the existing 30-degree droplet registry, rather than evidence
of divergence away from it.

At least one or two larger slit heights are required before interpreting
the slit registry transfer.

## 5. Correction to the internal review: axial transition width is not diffuse-interface width

The internal reviewer noted an 11–17 lu transition in column-averaged
`psi(x)` and compared that directly with slit height.

That quantity mixes:

- true diffuse-interface thickness;
- the x-span of a curved meniscus across y;
- wall/contact-angle geometry.

It therefore cannot be interpreted directly as a diffuse interface
occupying 40–60% of the slit.

The repository's local interface-width diagnostic and the geometric
meniscus span must remain separate concepts.

This does not make h=26 fully resolved; it only removes an unsupported
argument for declaring it grossly under-resolved.

## 6. Dynamic pressure measurement

The fresh reviewer correctly found that the current far-field band placement
has an 8–9% method sensitivity near the interface-distortion zone.

This affects the absolute `Pc_dynamic` and `Pc_dynamic/Pc_static` values
but does not remove the length-differential result above.

For the next diagnostic, pressure-fit bands should be selected using an
explicit bulk-phase clearance rule rather than a fixed 12-lu distance from
the column-averaged meniscus.

Suitable rule:

- identify bulk nodes/columns satisfying a declared `|psi|` threshold;
- impose a minimum clearance from the entire curved-interface envelope;
- fit only within the resulting bulk plateau;
- report band-sensitivity.

## 7. Revised interpretation of V1b hard-gate failures

### Static scaling gate

Literal V1b result: **FAIL** (11.5% > 10%).

Scientific interpretation: unresolved finite-resolution convergence, not a
demonstrated model inconsistency.

### Raw dynamic `V/V_hyd` gate

Literal V1b result: **FAIL**.

Scientific interpretation: the gate assumed zero localized boundary
resistance. The h26 differential test shows that assumption is false while
the incremental bulk resistance is accurate.

Thus raw `V/V_hyd` should not remain the primary V1c validation metric.

### Gas-leg Poiseuille gate

The review shows the fitted gradient is strongly band-dependent and can be
near the theoretical value when measured sufficiently far from the
meniscus.

Treat the current g8 failure primarily as a measurement-definition issue
until a bulk-clearance rule is applied.

## 8. V1c — minimal remaining diagnostic

V1c should answer only two unresolved questions.

### V1c-A — static resolution convergence

Run the same static slit calibration at:

- h=60;
- h=80.

Keep all physics unchanged.

Combine h=26, 40, 60, 80 and report:

- `C_static(h)`;
- `theta_static_slit(h)`;
- plots/tables versus `1/h`;
- a simple convergence fit, with residuals;
- comparison of the inferred large-h limit with the droplet registry.

Do not force a particular `1/h` law if the four points do not support it.

Promotion need not require exact equality to 30 degrees. It requires a
clear, reproducible resolution trend or plateau that can be carried as the
model's slit calibration.

### V1c-B — h=40 length differential

Run one approximately 2x-length h=40 corrected dynamic case.

Use improved bulk pressure-fit bands.

For h=40 calculate:

`L_eff = Pc_dynamic h^2/(12 mu V)`

for both lengths and the differential slope:

`a_h40 = Delta L_eff / Delta L`.

Primary dynamic gate:

`|a_h40 - 1| <= 0.10`.

Recalculate h26 with the improved pressure-band method as well and require
its differential slope to remain within 10% of 1.

The localized intercept `L0(h)` is diagnostic. It is not required to be
zero because V2 will not use the open reservoir/membrane boundary.

### Optional, low-cost diagnostic

Report `L0/h` for h=26 and h=40.

If the values are of the same order, that would support a localized
entrance/membrane resistance interpretation.

It is not a hard gate.

## 9. V1c promotion criterion toward V2

External review may authorize V2 if:

1. h26 and h40 differential hydraulic slopes are each within 10% of 1;
2. static slit calibration shows a coherent resolution trend/plateau rather
   than erratic behaviour;
3. improved bulk pressure fitting removes the current measurement ambiguity;
4. front motion remains stable/monotonic;
5. no solver modification or parameter tuning was required.

Absolute raw `V/V_hyd(L)` with zero boundary intercept is **not** required.

The remaining localized open-boundary intercept will be documented as an
artifact of the open V1 validation system. V2's closed finite-buffer
geometry does not contain these reservoir/membrane boundaries.

## 10. Decision

**HUMAN_REQUIRED confirmed under the frozen V1b contract, but scientifically
resolved into a narrowly scoped V1c convergence/differential task.**

This review does not authorize V2 yet.

It also does not support modifying the solver.

The V1b candidate and evidence should be retained as a successful diagnostic
that exposed the limitations of the original acceptance metric and isolated
a boundary-resistance intercept.
