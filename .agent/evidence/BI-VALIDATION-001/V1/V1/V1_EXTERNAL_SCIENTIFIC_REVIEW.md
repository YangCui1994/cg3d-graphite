# V1 External Scientific Review — BI-VALIDATION-001

## Binding

- Product branch: `agent-episode/BI-VALIDATION-001`
- V0 accepted candidate: `280a46fed488b12975c3de96b5493362942822ec`
- V1 candidate: `e9540bcadb86257c70b805afc98f2eec9626c64e`
- V1 internal reviewer decision: `HUMAN_REQUIRED`
- Review scope: scientific/modeling checkpoint after V1; no V2/V3 authorization

## Executive finding

The V1 stop is scientifically justified.

The current V1 result does **not** establish that the color-gradient
wall-wetting model is wrong. It establishes that the present V1 test
cannot yet separate three contributions:

1. the correct two-phase hydraulic resistance of the slit;
2. a large artificial/fixed resistance associated with the reservoir /
   membrane layout;
3. the actual capillary pressure delivered by the moving meniscus, which
   is lower than the nominal value inferred from the static droplet
   contact-angle registry.

V2 and V3 should therefore remain unstarted.

## Independent physics check

### 1. Correct front law for the actual V1 configuration

For two immiscible columns in the same straight slit, equal-pressure
reservoirs, equal cross-section, and matched viscosities:

`mu_l = mu_g = mu`

the viscous pressure loss is

`Delta p_visc = 12 mu (L_l + L_g) V / h^2`.

Because `L_l + L_g = L_tot` is constant,

`V = Pc h^2 / (12 mu L_tot)`

is constant after the transient.

Therefore the correct generalized Washburn form for this particular V1
configuration is:

`x(t) = x0 + V t`

not a classical gas-negligible `x^2 proportional to t` law.

The original Stage Contract's gate 5 (`R2[x^2,t] >= 0.98`) is therefore
not a physically discriminating acceptance gate for this matched-viscosity
two-bath case. This is a contract-design error, not a solver failure.

### 2. Observed front dynamics are stable in form but wrong in rate

Committed V1 data give:

- h=26: `V_meas = 3.857e-3`, `V_nominal = 9.263e-3`
  -> measured/nominal = 0.416;
- h=40: `V_meas = 3.746e-3`, `V_nominal = 14.251e-3`
  -> measured/nominal = 0.263.

The trajectories are very nearly linear in time, stable, monotonic, and
well below the operational velocity cap.

The problem is therefore not failure to produce a steady capillary-driven
front. It is the pressure/resistance budget that determines the speed.

### 3. The boundary-resistance evidence is unusually strong

For h=26, the internal review localised approximately

`Delta p_boundary = 1.294e-3`

to the abrupt reservoir/membrane transitions.

At the measured velocity, the plane-Poiseuille pressure gradient is
approximately

`6.85e-6 per lu`.

Thus the observed boundary loss corresponds to an equivalent extra channel
length of

`L_eq,boundary ~= 1.294e-3 / 6.85e-6 ~= 189 lu`.

An independent doubled-length V1 diagnostic gives

`V(2L) / V(L) ~= 0.641`.

For a fixed extra resistance represented by an equivalent length `L_eq`,

`V(2L)/V(L) = (L + L_eq)/(2L + L_eq)`.

Using L=246 lu and the measured ratio gives

`L_eq ~= 193 lu`.

The agreement, approximately 189 vs 193 lu, comes from two independent
observables and strongly supports the existence of a large fixed/localised
extra resistance in the current boundary layout.

This should be removed before interpreting the remaining speed deficit as
a moving-contact-line property.

### 4. The moving-meniscus capillary pressure also differs from the nominal registry value

For h=26:

- nominal value from `sigma cos(theta_static)/b`:
  `Pc_nominal = 4.045e-3`;
- far-field-extrapolated moving-meniscus jump:
  `Pc_dynamic ~= 3.086e-3`;
- ratio:
  `Pc_dynamic/Pc_nominal ~= 0.763`.

If the large boundary resistance were absent while the measured moving
meniscus jump remained 3.086e-3, the hydraulic prediction would be about

`V ~= 7.07e-3`,

still below the nominal-static-angle prediction but much closer.

This remaining difference cannot yet be called a dynamic-contact-angle
effect because the same slit geometry has not been statically calibrated.

## Human/modeling resolutions made at this checkpoint

### R-V1-1 — retire the x^2 gate for this configuration

For matched-viscosity, equal-pressure two-bath validation, the acceptance
form is the constant-velocity generalized Washburn relation.

A future classical `x^2 proportional to t` benchmark would require a
different physical setup, for example a negligible displaced-phase
viscous resistance, and should be treated as a separate benchmark.

### R-V1-2 — current V1 does not validate absolute dynamic wetting

The current result may be retained as a useful failed/diagnostic case, but
it must not be promoted as quantitative validation of:

- absolute front speed;
- nominal static-contact-angle-to-capillary-pressure mapping during motion;
- slit-height scaling.

### R-V1-3 — do not modify the solver yet

There is sufficient evidence of boundary contamination that changing the
wall-wetting/collision implementation now would be premature.

First separate the boundary, static-geometry, and moving-contact-line
contributions.

## Required V1b diagnostic sequence

V1b should remain a small synthetic problem and should not introduce real
porous media.

### V1b-A — correct the open-boundary layout

Rebuild the single-front case using the repository's documented open-system
separation:

- prescribed reservoir;
- membrane outside the pinned reservoir;
- explicit open buffer between boundary forcing and the active slit;
- corresponding outlet-side separation;
- no overlap between a pinned reservoir mask and the membrane plane.

Record the exact lattice layout.

Repeat at least h=26 and h=40.

### V1b-B — same-slit static capillary-pressure calibration

In the same slit/wall geometry, create a stalled or quasi-static meniscus
and measure the bulk pressure jump by far-field extrapolation.

Do this for h=26 and h=40.

Report:

- `Pc_static`;
- `Pc_static * h / (2 sigma)`;
- equivalent static contact angle;
- resolution dependence.

The purpose is to establish whether the wall-colour registry calibrated on
the existing droplet test transfers to this slit geometry.

### V1b-C — corrected dynamic run

With the corrected boundary layout, record:

- `V_meas`;
- far-field `Pc_dynamic`;
- bulk liquid/gas pressure gradients;
- residual boundary pressure jumps;
- front linearity;
- mass accounting;
- local velocity/spurious-current diagnostics.

Primary hydraulic consistency check:

`V_hyd = Pc_dynamic h^2 / (12 mu L_tot)`.

Compare `V_meas` to `V_hyd`, not initially to
`sigma cos(theta_static)/b`.

A project engineering target of <=10% mismatch may be retained for this
internal consistency test because it is the same level of quantitative
accuracy the original V1 attempted to require.

### V1b-D — one length-sensitivity check

Repeat one corrected case at approximately 2x active length.

After boundary correction, verify that the fixed extra-resistance signature
seen in the present V1 is strongly reduced.

Report the equivalent extra length inferred from the two-length speed ratio:

`L_eq`.

For v0.1, treat `L_eq/L` primarily as a diagnostic; if it remains
order-one, V1b must not pass.

### V1b-E — dynamic/static comparison

Report

`Pc_dynamic/Pc_static`

and the corresponding apparent moving-meniscus contact angle / capillary
number.

Do not require dynamic and static angles to be equal a priori.

If the hydraulic consistency check passes but `Pc_dynamic` differs from
`Pc_static`, classify that difference as a model characteristic of the
moving contact line pending further Ca dependence, not automatically as a
solver bug.

## V1b promotion logic

### Eligible to proceed toward V2

V1b may be considered scientifically sufficient for V2 design if:

1. the corrected boundary layout removes the order-one fixed-resistance
   signature;
2. the measured front is stable and monotonic;
3. the observed velocity is quantitatively consistent with the independently
   measured **dynamic** capillary pressure and slit hydraulic resistance;
4. static slit calibration is reproducible across the two resolutions;
5. all remaining static-to-dynamic wetting differences are explicitly
   carried as diagnostics/model limitations rather than hidden inside an
   assumed 30-degree contact angle.

This would validate the numerical capillary-flow mechanism sufficiently for
the next topology/collision experiment, even if it does not validate
real-time battery filling rates.

### Must stop again

Stop before V2 if:

- order-one boundary resistance remains;
- h=26/h=40 static slit capillary pressure has inconsistent scaling;
- `V_meas` cannot be reconciled with independently measured
  `Pc_dynamic` and hydraulic resistance;
- the corrected case requires changing solver physics to obtain agreement.

## Required implementation/evidence corrections in V1b

The current V1 also exposed several execution/provenance issues that should
be fixed in the next diagnostic driver:

1. Explicitly detect the case where the requested fit-window threshold is
   never reached; do not allow `np.argmax(False...)` to silently return 0.
2. Remove or clearly invalidate the near-interface `pc_measured_last`
   diagnostic; use far-field bulk extrapolation for pressure-jump estimates.
3. Every committed CSV/JSON/PNG must identify the candidate SHA and producer
   revision.
4. Generate figures from the final committed producer code, or omit them.
5. Preserve console log + exit code for every primary run.
6. Keep h=26 and h=40 pressure diagnostics symmetrical so the resolution
   comparison is directly auditable.

## Assessment of the GLM reviewer

The internal reviewer performed well on the central scientific issue:

- it independently rejected the literal x^2 gate as non-discriminating;
- it verified the speed mismatch rather than accepting executor framing;
- it localised a major boundary pressure loss;
- it correctly escalated rather than tuning a threshold or modifying solver
  physics.

The main remaining weakness is artifact provenance: the review found that
some committed figures/JSONs were not produced by exactly the committed
driver revision. That did not change the numerical conclusion because the
gate-relevant values were independently reproducible from committed raw
series, but V1b should close this gap.

## Decision

**HUMAN_REQUIRED confirmed and resolved into a V1b re-plan.**

V2 and V3 remain not authorized.

The next execution task should be a focused V1b diagnostic episode, not a
rework of the existing V1 candidate under the old frozen contract.
