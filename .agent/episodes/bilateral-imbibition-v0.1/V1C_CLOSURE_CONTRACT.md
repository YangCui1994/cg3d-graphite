# V1c Closure Contract — Resolution Convergence + Differential Hydraulics

Task ID: BI-V1C-CLOSURE-001

## Objective

Close the two remaining single-front validation questions before V2:

1. static slit wettability resolution convergence;
2. distributed hydraulic-resistance accuracy after separating localized open-boundary resistance.

This task does not authorize solver-physics modification.

## Base

Product base:

\`a9c6db87da2eeb3572607152391fe6863394ebee\`

Branch:

\`agent-task/BI-V1C-CLOSURE-001\`

Read first:

- \`.agent/evidence/BI-V1B-DIAGNOSTIC-001/V1B_EXTERNAL_SCIENTIFIC_REVIEW.md\`
- \`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\` from the control checkout
- \`AGENTS.md\`
- existing V1b driver/evidence

## Fixed physics

Do not change:

- \`lbm_solver_cg3d.py\`;
- MRT / recoloring / wetting kernels;
- \`CapA=0.06\`;
- \`nu_l=nu_g=0.1\`;
- \`psi_solid=-0.68\`;
- unit density ratio;
- z-periodic slit;
- equal-pressure dynamic reservoirs;
- membrane/reservoir/buffer topology established in V1b.

If a solver change appears necessary: HUMAN_REQUIRED.

## Implementation

Create V1c-specific files only, preferably:

- \`tests/levelc_v1c.py\`
- \`results/levelc_v1c/**\`

Do not rewrite V1/V1b history.

## A. Static resolution convergence

Run static slit calibration at:

- h=26
- h=40
- h=60
- h=80

For h26/h40 a fresh rerun is preferred so all four cases use the same producer revision and measurement logic.

Measure:

\[
C_\mathrm{static}(h)=\frac{P_{c,\mathrm{static}}h}{2\sigma}
\]

and

\[
\theta_\mathrm{static}(h)
=\arccos(C_\mathrm{static})
\]

Record pressure stationarity separately from spurious-current magnitude.

Required output:

- \`C_static(h)\`;
- \`theta_static(h)\`;
- table vs \(1/h\);
- simple candidate convergence fits (e.g. constant, \(1/h\), \(1/h^2\)) with residuals;
- do not force a fit family if data do not support it.

Scientific readiness condition:

- trend must be reproducible and non-erratic;
- a plateau or coherent resolution trend must be identifiable;
- exact equality to the 30° droplet registry is not required.

## B. Improved dynamic pressure-band method

Rerun corrected dynamic cases:

- h26 short
- h26 ~2L
- h40 short
- h40 ~2L

Use the V1b boundary layout unchanged.

Replace fixed-distance pressure bands with a bulk-column rule.

At every pressure probe:

1. inspect the full slit cross-section;
2. mark a liquid-bulk column only if at least 95% of fluid nodes satisfy \(\psi<-0.9\);
3. mark a gas-bulk column only if at least 95% satisfy \(\psi>+0.9\);
4. exclude all mixed columns and at least two additional x columns on each side of the mixed-column envelope;
5. choose contiguous bulk-fit bands with at least 12 columns; if unavailable, mark that probe invalid rather than silently falling back;
6. report band counts and sensitivity to thresholds 0.85 / 0.90 / 0.95 as diagnostics.

Fit:

\[
p_l(x)=g_lx+c_l,\qquad
p_g(x)=g_gx+c_g
\]

and extrapolate to the declared meniscus reference \(x_m\):

\[
P_{c,\mathrm{dynamic}}
=
p_g(x_m)-p_l(x_m)
\]

## C. Differential hydraulic validation

For each height define:

\[
L_\mathrm{eff}
=
\frac{P_{c,\mathrm{dynamic}}h^2}
{12\mu V_\mathrm{meas}}
\]

For short/long pairs:

\[
a_h
=
\frac{
L_{\mathrm{eff,long}}-L_{\mathrm{eff,short}}
}{
L_\mathrm{long}-L_\mathrm{short}
}
\]

Primary engineering gates:

\[
|a_{26}-1|\le0.10
\]

\[
|a_{40}-1|\le0.10
\]

The intercept

\[
L_0(h)=L_\mathrm{eff}-a_hL
\]

is diagnostic, not required to be zero.

Also report \(L_0/h\).

## D. Front / stability gates

For all four dynamic cases:

- no NaN/Inf;
- no velocity-cap violation;
- zero imposed reservoir pressure difference;
- monotonic post-transient front;
- valid declared fit window;
- \(R^2[x,t]\ge0.995\);
- primary and secondary front speeds agree within 2%;
- colour-mass closure reported.

## E. Provenance

Every numerical artifact must bind to:

- candidate SHA;
- producer path;
- producer SHA256;
- exact command;
- timestamps;
- shell exit code.

No figures should be committed on the product branch unless generated from the final producer revision.

## F. Mandatory technical-document output

After the product candidate is frozen and the fresh reviewer completes, update on the control branch:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

The update is a **required deliverable**, not optional documentation.

It must add:

1. V1c Task ID / base / candidate SHA;
2. formulas actually used;
3. key implementation code excerpts from V1c;
4. static h26/h40/h60/h80 result table;
5. at least one SVG result figure for static convergence;
6. h26/h40 differential hydraulic table;
7. at least one SVG result figure for \(L_\mathrm{eff}\) vs \(L\);
8. before/after accuracy comparison against V1b;
9. explicit statement of what changed at SOLVER / BC / VAL / DIAG / HARNESS layers;
10. evidence paths and reviewer decision.

Every figure must be generated from committed numeric evidence and state the product candidate SHA in its caption or adjacent text.

If the simulations pass but this living document is not updated, the task is incomplete.

## Reviewer decision

Fresh reviewer chooses:

- PASS
- CHANGES_REQUESTED
- HUMAN_REQUIRED

PASS means only that V1c is technically/scientifically ready for external review. It does not authorize V2 automatically.

HUMAN_REQUIRED if:

- either differential slope fails by >10% with no finite measurement correction;
- static resolution trend remains erratic;
- solver modification is required;
- pressure-band selection cannot identify robust bulk regions.

## Stop

Stop after publication of:

- product evidence;
- fresh review;
- updated living technical document.

Do not start V2/V3.
