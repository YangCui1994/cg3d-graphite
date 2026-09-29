# V1c External Scientific Review — BI-V1C-CLOSURE-001

## Binding

- Product branch: \`agent-task/BI-V1C-CLOSURE-001\`
- Base: \`a9c6db87da2eeb3572607152391fe6863394ebee\`
- Candidate: \`2b82f9a5f448e756b5d5903b0df37f9a3b11d804\`
- Fresh internal reviewer: attempt 1 \`CHANGES_REQUESTED\`, attempt 2 \`PASS\`
- Control evidence: \`.agent/evidence/BI-V1C-CLOSURE-001/\`
- Living technical document:
  \`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`
- Review scope: external scientific decision on whether single-front validation
  is sufficient to proceed to a bilateral-front verification stage

## Executive decision

**V1c PASS is accepted.**

The current evidence is sufficient to close the single-front validation
episode for the purpose of proceeding to a simple bilateral-front numerical
verification.

This PASS means:

1. the distributed slit hydraulic resistance is quantitatively consistent
   with plane-Poiseuille theory at both tested resolutions;
2. the matched-viscosity two-phase front follows the expected
   constant-velocity generalized-Washburn form;
3. the residual open-system error has been isolated primarily as a localized
   reservoir/membrane/boundary intercept rather than a distributed bulk-flow
   error;
4. the slit wetting calibration is reproducible as a geometry/protocol-specific
   plateau, although it does not equal the flat-droplet 30-degree registry;
5. no solver-physics change is justified by the present evidence.

V2 is scientifically eligible to begin **after its contract is revised to
remove assumptions invalidated by V1/V1c**.

The old V2 contract must not be executed unchanged.

---

# 1. Static slit calibration

Committed V1c values:

| h | Pc_static | C_static = Pc h/(2 sigma) | theta_static |
|---:|---:|---:|---:|
| 26 | 3.69081e-3 | 0.79019 | 37.80 deg |
| 40 | 2.28032e-3 | 0.75110 | 41.31 deg |
| 60 | 1.63284e-3 | 0.80674 | 36.22 deg |
| 80 | 1.18327e-3 | 0.77949 | 38.79 deg |

A constant representation gives:

\`C_static = 0.7819 +/- 0.0308\`

with maximum residual approximately 3.9%.

Neither a \`1/h\` nor \`1/h^2\` convergence law is supported by these four
points. The correct reading is therefore a reproducible plateau/scatter band,
not a continuum extrapolation.

Equivalent slit angle:

approximately \`38.6 deg +/- 1.8 deg\`.

## Interpretation

This differs systematically from the existing flat-droplet registry
(\`theta ~= 30 deg\`, \`cos(theta)=0.866\`).

That difference must be carried as a **geometry/protocol-specific calibration
difference**, not silently replaced by the droplet value.

For V2:

- \`psi_solid=-0.68\` remains the implementation parameter;
- the 30-degree value must not be used as an absolute front-speed pass/fail
  reference;
- the V1c slit calibration may be quoted as a diagnostic reference only.

The plateau is sufficiently coherent for V2 because V2's primary questions
are symmetry, interface interaction, trapping topology and numerical
stability, not absolute physical filling time.

---

# 2. Distributed hydraulic accuracy

Define:

\[
L_\mathrm{eff}
=
\frac{P_{c,\mathrm{dynamic}} h^2}
{12\mu V}
\]

and for a short/long pair:

\[
a_h
=
\frac{
L_{\mathrm{eff,long}}-L_{\mathrm{eff,short}}
}{
L_\mathrm{long}-L_\mathrm{short}
}.
\]

V1c primary results:

| h | L_eff short | L_eff long | a_h | error from 1 |
|---:|---:|---:|---:|---:|
| 26 | 330.09 | 576.39 | **1.0436** | **4.4%** |
| 40 | 427.80 | 680.30 | **1.0699** | **7.0%** |

Both satisfy the project engineering gate:

\[
|a_h-1|\le 0.10.
\]

## Robustness check

The PASS is not created solely by the final V3 gradient filter.

When the gradient-consistency rung is removed and the less restrictive
position/width validity set is used, the median estimates remain
approximately:

- h26: \`a ~= 1.049\`;
- h40: \`a ~= 1.090\`;

both still within the 10% gate.

The published estimator-sensitivity table also retains the contaminated
attempt-1 variants and demonstrates explicitly which aggregate choices fail.

Therefore the V1c PASS is not a hidden threshold-tuning result.

---

# 3. Localized open-boundary resistance

The effective-length representation is:

\[
L_\mathrm{eff}\approx a_h L+L_0(h).
\]

V1c gives approximately:

- h26: \`L0/h ~= 3.0\`;
- h40: \`L0/h ~= 4.0\`.

The reservoir/membrane jumps account for a material fraction of the measured
dynamic pressure budget.

This remains a limitation of the **open validation system**.

It does not block the next bilateral verification because the planned V2
geometry uses:

- finite liquid buffers;
- solid outer walls;
- no density reservoirs;
- no phase-selective membranes;
- no imposed pressure difference.

Thus the principal localized artifact isolated in V1/V1b/V1c is not present
in the V2 geometry.

No claim is made that the open boundary implementation is universally
artifact-free.

---

# 4. Pressure-band methodology

V1c replaces the fixed-distance pressure bands with bulk-column selection.

The remaining threshold sensitivity is at most approximately 0.94% for the
reported primary aggregate.

The h40 short case is the weakest measurement:

- only a limited usable pre-exit interval exists;
- the most restrictive primary aggregate retains a relatively small number
  of probes;
- gas-side gradient magnitudes have substantial scatter.

However:

1. the differential result remains inside the gate under less restrictive,
   independently reported aggregates;
2. median and mean primary estimates both pass;
3. the front-position fit itself is exceptionally stable;
4. V2 will not use this pressure estimator as an absolute-speed gate.

Therefore this uncertainty is acceptable for transition to V2.

One hardening rule should be retained for future pressure diagnostics:
require the expected sign of the bulk pressure gradient in addition to its
magnitude whenever such a gradient is used as a validity criterion.

---

# 5. Front kinematics and mass/stability evidence

Across the V1c dynamic cases:

- no NaN/Inf;
- no operational velocity-cap violation;
- reservoir density pinning behaves as configured;
- front motion is monotonic;
- \`R2[x,t]\` is approximately 0.999975–1.000000;
- primary/secondary front estimates agree well inside 2%;
- colour-mass closure is approximately \`5e-4–7e-4\` relative;
- total colour-mass drift remains sub-percent.

This is sufficient evidence for a stable simple-channel moving-interface
baseline.

---

# 6. Important interpretation boundary

The V1c result validates, to the current project engineering accuracy:

- distributed hydraulic response;
- stable capillary-driven moving fronts;
- a reproducible slit-wetting calibration regime;
- the numerical machinery needed for the next topology/interference test.

It does **not** validate:

- real battery filling time;
- real air compressibility;
- equality of static and dynamic contact angles;
- the flat-droplet 30-degree registry as an absolute slit-dynamics law;
- the open reservoir/membrane implementation as resistance-free.

These boundaries must be carried into V2 documentation.

---

# 7. Required correction to the old V2 contract

The existing
\`.agent/episodes/bilateral-imbibition-v0.1/STAGE_V2_BILATERAL.md\`
must not be executed unchanged.

Two items are scientifically obsolete.

## 7.1 Remove x^2(t) as a primary bilateral observable

The old V2 contract asks for individual \`x^2 versus t\` behaviour.

V1 established that under matched viscosities the appropriate pre-interaction
simple-channel law is constant-velocity generalized Washburn:

\[
x(t)\approx x_0+Vt.
\]

For V2, pre-interaction observables should therefore be:

- left front \`x_L(t)\`;
- mirrored right-front coordinate \`x_R^*(t)\`;
- linear fitted rates \`V_L\`, \`V_R\`;
- left/right rate difference;
- symmetry error.

\`x^2(t)\` may be retained only as a diagnostic with no acceptance meaning.

No absolute theoretical speed based on \`cos 30 deg\` should be a hard gate.

## 7.2 Remove the nonexistent "gas isolation event"

The old V2 contract requires identification of the event at which the
central gas loses connectivity to both liquid-buffer interfaces.

In the specified straight-slit geometry:

\`liquid buffer | central gas | liquid buffer\`

with solid outer x walls and no gas vent path, the central gas pocket is
already topologically trapped by the two liquid fronts from the initial
condition.

There is therefore no later gas-vent-connectivity-to-buffer transition to
detect.

The correct topology questions are instead:

1. verify at initialization that the central non-wetting cluster is a single
   trapped cluster with the intended topology;
2. track its volume, mass proxy, mean density and pressure from t=0;
3. track the minimum gas-gap thickness between opposing fronts;
4. identify front-interaction / interface-overlap / coalescence events;
5. identify whether the central gas cluster remains single, fragments, or
   numerically disappears;
6. report connected/trapped classification explicitly, without inventing a
   vent-loss event.

If a V2 case with a genuine gas-connectivity transition is desired, it
requires a different geometry with an explicit vent or bypass and should be a
separate benchmark.

---

# 8. Recommended V2 primary geometry

Use \`h=40\` as the primary resolved slit height.

Reason:

- it has direct V1c static calibration;
- it has short/long differential hydraulic validation;
- its half-height is approximately 20 lu, comfortably above the local
  interface-width scale;
- it is less expensive than h60/h80 while more resolved than h26.

The V2 validation should not require an h60 repeat unless an unexplained
resolution-sensitive collision effect appears.

This is an engineering choice for the next benchmark, not a universal
resolution threshold.

---

# 9. V2 acceptance scope

V2 may use hard gates for:

- exact programmed mirror symmetry;
- left/right front-position symmetry;
- left/right pre-interaction fitted-rate symmetry;
- no NaN/Inf;
- operational stability;
- global colour-mass accounting;
- central gas-cluster topology tracking;
- reproducible collision/overlap event detection.

V2 should **not** use hard gates for:

- absolute front speed from the 30-degree registry;
- pocket pressure interpreted as real-air compression;
- collision distance against a literature threshold;
- final trapped volume against a literature threshold.

Pocket pressure/density is a numerical weak-compressibility diagnostic only.

---

# 10. Technical-document requirement for V2

The living document

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

must be updated after V2 with:

- revised bilateral physical model and equations;
- exact implementation geometry;
- key front/topology code excerpts;
- front-position and symmetry result figures;
- gas-pocket volume/pressure result figures;
- collision/overlap diagnostics;
- explicit comparison with the V1c single-front baseline;
- statement of any SOLVER / BC / VAL / DIAG / HARNESS changes.

V2 is incomplete without this update.

---

# Decision

**Decision: PASS — V1c single-front closure accepted.**

**V2 is scientifically authorized after the V2 contract is revised as
specified above.**

This decision does not authorize V3, graphite, separator, gap or PCS work.

No core solver change is recommended before V2.
