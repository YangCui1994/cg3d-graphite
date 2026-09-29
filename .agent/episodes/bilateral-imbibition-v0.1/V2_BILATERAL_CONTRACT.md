# V2 Bilateral Contract — Symmetric Trapped-Pocket Verification

Task ID: BI-V2-BILATERAL-001

## 1. Objective

Verify the numerical behaviour of a **mirror-symmetric two-interface closed system**
before introducing porous-media complexity.

The primary V2 question is:

> Can the current CG3D solver evolve two opposing wetting interfaces around an
> initially trapped non-wetting pocket while preserving symmetry, colour mass,
> topology and numerical stability?

V2 is **not** an absolute filling-rate validation and does **not** require the
two fronts to collide.

## 2. Scientific authority and base

Read before implementation:

1. \`.agent/evidence/BI-V1C-CLOSURE-001/V1C_EXTERNAL_SCIENTIFIC_REVIEW_PASS.md\`
2. \`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`
3. \`.agent/episodes/bilateral-imbibition-v0.1/V2_REVIEWER_CONTRACT.md\`
4. \`AGENTS.md\`
5. \`docs/ALGORITHM.md\`

Product base:

\`2b82f9a5f448e756b5d5903b0df37f9a3b11d804\`

Product branch:

\`agent-task/BI-V2-BILATERAL-001\`

V1c is the accepted single-front numerical baseline.

## 3. Fixed physics

Do not change:

- \`lbm_solver_cg3d.py\`;
- D3Q19 MRT collision;
- color-gradient surface-tension formulation;
- recoloring;
- \`CapA = 0.06\`;
- \`nu_l = nu_g = 0.1\`;
- unit-density-ratio formulation;
- wetting phase \`psi=-1\`;
- non-wetting phase \`psi=+1\`;
- \`psi_solid=-0.68\`;
- z periodicity;
- solver operational caps already used by the project.

No parameter may be tuned to make V2 pass.

If a solver-physics change appears necessary, stop with \`HUMAN_REQUIRED\`.

## 4. Important interpretation carried from V1c

### 4.1 Pre-interaction law

Do **not** use classical \`x^2 proportional to t\` as a V2 acceptance law.

For the matched-viscosity simple-channel baseline, V1c established the
constant-velocity generalized-Washburn behaviour in the open system.

In V2 the central gas is already trapped, so pocket compression may decelerate
the fronts immediately. Therefore V2 does not require constant absolute speed.

Use front velocities only as **left/right symmetry summaries**, not as an
absolute hydraulic prediction.

### 4.2 Wettability reference

Keep \`psi_solid=-0.68\`.

Do not use the flat-droplet 30-degree registry as an absolute speed gate.

The V1c same-slit static calibration

\`C_static ~= 0.782 +/- 0.031\`

(\`theta_slit ~= 38.6 deg +/- 1.8 deg\`) is a diagnostic reference only.

### 4.3 Trapped gas exists from t=0

The central non-wetting phase is intentionally sealed between two liquid
regions.

There is **no later "gas loses connectivity to a vent" event** in this
geometry.

The initial central gas pocket must already be classified as trapped.

## 5. Primary geometry

Use the V1c-recommended resolved slit:

\`h = 40 lu\`

with:

- z periodic, \`nz = 6\`;
- y = one solid wall + 40-lu fluid slit + one solid wall;
- x outer walls are explicit solid/bounce-back;
- no density reservoirs;
- no phase-selective membranes;
- no imposed pressure gradient;
- no body force.

### 5.1 Baseline x layout

Use the deterministic symmetric baseline:

\`\`\`text
3-lu solid wall
| 80-lu wetting-liquid buffer
| 160-lu central non-wetting pocket
| 80-lu wetting-liquid buffer
| 3-lu solid wall
\`\`\`

Thus, before any optional indexing offset:

- wall thickness \`W = 3 lu\`;
- liquid-buffer thickness \`B = 80 lu = 2h\`;
- initial central gas length \`G0 = 160 lu = 4h\`.

This is a **project engineering baseline**, chosen to provide scale separation
and to define the reference \`B\` for the later V3 buffer-sensitivity study.
It is not a universal physical threshold.

If implementation details require a one-cell indexing shift, preserve exact
mirror symmetry and record the final indices explicitly.

## 6. Initial condition

At t=0:

- both side buffers: \`psi=-1\` wetting phase;
- central pocket: \`psi=+1\` non-wetting phase;
- all fluid nodes: \`rho=1\` through the normal solver initialization;
- all solid nodes use the same \`psi_solid=-0.68\`;
- no random perturbation;
- no imposed velocity.

The two initial phase interfaces must be exact mirror images.

## 7. Programmatic symmetry verification

Before the first timestep, verify and write to evidence:

- \`solid[x,y,z] == solid[nx-1-x,y,z]\`;
- \`psi0[x,y,z] == psi0[nx-1-x,y,z]\`;
- \`psi_solid[x,y,z] == psi_solid[nx-1-x,y,z]\`;
- left/right buffer lengths identical;
- central gas interval centred exactly on the mirror plane.

A failure is a hard implementation failure.

## 8. Required observables

Sample densely enough to resolve the transient and any topology change.

### 8.1 Front coordinates

Define a cross-sectional liquid fraction:

\[
\phi_l(x)
=
\left\langle \frac{1-\psi}{2}\right\rangle_{y,z,\ fluid}.
\]

Primary left/right front positions should be obtained from an interpolated
crossing of the column-averaged phase field / liquid fraction.

Record:

- \`x_left(t)\`;
- \`x_right(t)\`;
- mirrored right coordinate
  \[
  x_\mathrm{right}^{*}(t)=nx-1-x_\mathrm{right}(t);
  \]
- front mirror error
  \[
  e_x(t)=|x_\mathrm{left}-x_\mathrm{right}^{*}|;
  \]
- one-sided displacement from the initial interface;
- optional linear-fit rates over mechanically declared windows for symmetry
  comparison only.

Also record a secondary volumetric/swept-phase front definition.

### 8.2 Field-level symmetry

Record at least one full-field symmetry diagnostic, for example:

\[
E_\psi(t)
=
\frac{
\sum_{\mathrm{fluid}}
|\psi(x,y,z)-\psi(nx-1-x,y,z)|
}{
N_{\mathrm{fluid}}
}.
\]

Do not use field averaging to hide local asymmetry.

### 8.3 Central gas pocket

From t=0 onward record:

- binary gas volume (\`psi>0\`);
- continuous gas volume / saturation using \((1+\psi)/2\);
- gas colour-mass proxy;
- central gas-cluster count;
- largest-cluster size;
- central gas-cluster mean \`rho\`;
- central gas-cluster mean \`p=rho/3\`;
- global \`rho_min/rho_max\`;
- global colour masses;
- \`u_max\`, \`u_rms\`;
- gas occupancy in the nominal left/right liquid-buffer regions.

### 8.4 Gas-gap / interface-interaction diagnostics

Define mechanically:

1. **bulk-gas column**:
   at least 95% of fluid nodes in the x column satisfy \`psi>+0.9\`;
2. **bulk-liquid column**:
   at least 95% satisfy \`psi<-0.9\`;
3. **mixed column**:
   neither condition holds.

Record:

- longest central contiguous bulk-gas interval;
- its length \`G_bulk(t)\`;
- left/right mixed-interface envelopes;
- separation between the two mixed envelopes;
- minimum central gas-gap metric.

Define \`INTERACTION_ONSET\` as the first sampled state where no bulk-gas
column remains between the two mixed-interface envelopes.

This is an event definition, **not a requirement that the event occur**.

If no interaction occurs before the run ends, record
\`INTERACTION_ONSET = NOT_REACHED\`.

## 9. Cluster topology

Use a declared topology compatible with the synthetic domain:

- primary connectivity: **6-neighbour**;
- periodic merge: **z only**;
- x: non-periodic;
- y: non-periodic because of the solid slit walls.

At t=0 verify:

- exactly one intended central non-wetting cluster in the active fluid region;
- it is not connected to any external vent or reservoir, because none exists.

Track whether the gas cluster:

- remains single;
- fragments;
- loses bulk-gas cells but remains diffuse;
- numerically disappears.

An unexplained fragmentation/disappearance **before interface-envelope
interaction** is a blocking finding.

## 10. Closed-system mass accounting

There are no reservoirs in V2.

Let initial colour masses be \((M_r^0,M_b^0)\).

Record:

\[
\epsilon_r(t)
=
\frac{|M_r(t)-M_r^0|}
{\max(M_r^0,1)}
\]

and likewise for blue.

Project engineering conservation gate:

\[
\max_t(\epsilon_r,\epsilon_b)\le5\times10^{-4}.
\]

This is a numerical conservation gate, not a physical-law tolerance.

If this threshold is exceeded monotonically or by an order-one amount, the
reviewer must treat it as blocking.

## 11. Operational weak-compressibility boundary

Use the existing project sentries:

- \`u_max <= 0.12\`;
- fluid density should remain inside approximately
  \[
  0.89 \le \rho \le 1.11.
  \]

These are operational numerical guardrails, not a validated real-gas EOS
range.

If the trapped pocket requires density outside this range to continue
evolving, stop with \`HUMAN_REQUIRED\` rather than interpreting the result as
real gas compression.

## 12. Run duration / termination

Run the primary case to a declared fixed cap of at least **60,000 steps**,
unless an earlier blocking event occurs.

The executor may additionally report a quasi-steady window if:

- front positions / gas-gap metrics plateau;
- pocket mean pressure becomes stationary;
- no topology event is active.

Do not require the interfaces to meet.

Do not declare lack of collision a failure.

## 13. Hard gates

1. no NaN/Inf;
2. \`u_max <= 0.12\`;
3. fluid density remains inside the operational \`[0.89,1.11]\` guardrail;
4. exact initial geometry / IC / wettability symmetry passes programmatically;
5. throughout the run,
   \[
   e_x(t)\le \max(2\ \mathrm{lu},\,0.02\,d(t)),
   \]
   where \`d(t)\` is the mean one-sided front displacement;
6. global red/blue colour-mass drift satisfies section 10;
7. the initial central gas pocket is correctly identified as one trapped
   non-wetting cluster;
8. no unexplained gas-cluster fragmentation or disappearance occurs before
   \`INTERACTION_ONSET\`;
9. if \`INTERACTION_ONSET\` occurs, the event is reproducibly identified by the
   declared bulk/mixed-column rule and the gas topology is tracked through it;
10. reviewer can reproduce the principal symmetry, mass and topology metrics
    from committed evidence.

### Conditional rate-symmetry diagnostic

If both fronts move by at least 2 lu over a mechanically declared
pre-interaction window, fit \`V_L\` and \`V_R\` and require:

\[
\frac{2|V_L-V_R|}
{|V_L|+|V_R|}
\le0.05.
\]

If total displacement is <2 lu, report the rate comparison as
\`NOT_DISCRIMINATING\`; do not fail V2 solely for that reason.

## 14. Diagnostic-only quantities

No hard literature threshold is imposed on:

- total front displacement;
- equilibrium gas-gap length;
- pocket pressure magnitude;
- pocket compression ratio;
- collision / overlap distance;
- final trapped-gas volume;
- local spurious-current peak;
- minimum \`|psi|\` in the interaction region;
- static-vs-dynamic contact-angle interpretation.

Report them.

## 15. Scientific interpretation boundary

The trapped phase uses the solver's weakly compressible unit-density EOS:

\[
p=\rho/3.
\]

Pocket \`rho\`, \`p\` and volume are numerical/topological diagnostics.

Do **not** interpret them as quantitatively validated real-air compression.

V2 PASS means the **numerical bilateral/trapped-pocket mechanism** is stable
and auditable.

It does not validate physical battery gas compressibility.

## 16. Optional near-contact stress probe

Only after the primary case is complete, the executor may run one additional
small symmetric case with a narrower initial gas gap to inspect diffuse-interface
overlap.

This probe is optional and diagnostic only.

It must not be used to tune the primary case or create a collision requirement.

If run, record the initial gap explicitly and do not claim a literature
critical distance.

## 17. Product outputs

Create V2-specific files only, preferably:

- \`tests/levelc_v2_bilateral.py\`;
- optional V2-only helper under \`tests/\`;
- \`results/levelc_v2/**\`.

Required durable product evidence:

- \`EXECUTION_REPORT.md\`;
- \`PROVENANCE.md\`;
- \`MANIFEST.json\`;
- machine-readable \`summary.json\`;
- front/symmetry time series;
- gas-pocket/topology time series;
- mass/stability time series;
- initial/mid/final phase snapshots or reduced slice data;
- console logs + shell exit code.

Do not modify:

- \`lbm_solver_cg3d.py\`;
- \`cg3d/**\`;
- V1/V1b/V1c source/results;
- episode runner.

## 18. Evidence provenance

Every numerical artifact must bind to:

- final candidate SHA or an explicitly recorded producer ancestor whose source
  is byte-identical in the final candidate;
- producer path;
- producer SHA256;
- exact command;
- timestamps;
- shell exit code;
- parameters.

Figures committed to the product branch are optional.

## 19. Mandatory living technical-document update

After the candidate is frozen and the fresh reviewer completes, update on the
control branch:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

The V2 section must include:

1. Task ID / base / candidate SHA;
2. bilateral closed-system physical model and equations;
3. exact geometry schematic and indices;
4. key implementation code excerpts:
   - mirror symmetry check;
   - front extraction;
   - gas-gap / interaction detection;
   - z-periodic cluster merge;
5. front/mirror-error result figure;
6. gas-gap / trapped-pocket volume / mean rho or p result figure;
7. topology/event table;
8. mass/stability table;
9. comparison against the V1c single-front baseline;
10. explicit SOLVER / BC / VAL / DIAG / HARNESS change classification;
11. reviewer decision and evidence paths.

All figures must be generated from committed V2 numeric evidence and include
the V2 candidate SHA in the caption or adjacent text.

If the simulation/review passes but this document is not updated, V2 is
incomplete.

## 20. Fresh reviewer decision

Choose exactly one:

- \`PASS\`
- \`CHANGES_REQUESTED\`
- \`HUMAN_REQUIRED\`

### PASS

Means:

- contract executed correctly;
- symmetry/mass/stability/topology gates pass;
- any interaction event is correctly handled;
- no physical interpretation outside the weak-compressibility boundary is
  required;
- evidence is auditable.

PASS returns to external scientific review.

It does **not** auto-authorize V3.

### CHANGES_REQUESTED

Only for finite implementation/evidence defects that do not change the
scientific problem.

### HUMAN_REQUIRED

Use if:

- density/compression leaves the operational numerical range;
- solver modification would be required;
- trapped gas disappears/fragmentation is unexplained;
- bilateral symmetry fails for a reason not attributable to a finite
  measurement bug;
- deciding how to proceed requires changing the physical problem.

## 21. Stop boundary

After the fresh reviewer and technical-document publication, stop.

Do not start V3.

Do not start graphite / separator / gap / PCS work.
