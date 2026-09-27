# BI-CG-LECLAIRE-PASS4-001 — Final Reference-Model Validation Contract

## 0. Purpose

Close the remaining **reference-model** ambiguities before any Taichi/f32 port
or production A/B work.

This stage is intentionally narrow:

1. freeze the wetting/phase convention;
2. replace invalid capillary-pressure and Jurin geometries;
3. diagnose the remaining Laplace sigma offset without retuning the paper;
4. add a planar mechanical-sigma diagnostic;
5. preserve direct field renderings and raw snapshots for every case;
6. clean the durable scientific record so the latest files contain one current
   truth.

## 1. Binding

Stage ID:
\`BI-CG-LECLAIRE-PASS4-001\`

Control branch:
\`agent-dev/bilateral-episode-v0.1\`

Continue on product branch:
\`agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001\`

Starting product evidence tip:
\`a12c14f553c5a03a815dbfc96d5aa09a6f33083e\`

Starting code candidate:
\`5a3929fa1cefb7359893d6c19ed0ec8a7c80a91d\`

Do not rebase, amend, squash or rewrite prior history.

Read as binding:
- \`docs/research/leclaire_cg/WETTING_PHASE_CONVENTION.md\`
- \`docs/research/leclaire_cg/VALIDATION_ARTIFACT_SPEC.md\`
- \`.agent/evidence/BI-CG-LECLAIRE-IMPLEMENTATION-001/EXTERNAL_SCIENTIFIC_REVIEW_R2_CHANGES_REQUESTED.md\`

## 2. Hard scope boundary

Do NOT:
- modify \`lbm_solver_cg3d.py\`;
- promote anything to production;
- port to Taichi/f32;
- execute revised V3;
- run graphite / separator / PCS production geometries;
- tune R1 Eq.(18) coefficient to make Laplace pass;
- introduce a new multiphase model family.

This remains a NumPy/f64 scientific-reference stage.

## 3. D1 — freeze wetting convention

Implement the normative convention exactly:

\`\`\`text
red  = liquid/electrolyte/wetting
blue = gas/non-wetting
psi  = (rho_red-rho_blue)/rho
F    = grad(psi) = gas -> liquid
g    = 1 solid, 0 fluid
n_w  = -grad(g)/|grad(g)| = solid -> fluid
theta = measured through red/liquid
\`\`\`

### D1.1 Analytic convention unit test

Before simulation:
- create analytic planar interface/wall cases for 60/90/120 deg;
- verify the geometric angle returned through liquid/red;
- verify the R1 secant operator rotates toward the correct branch;
- verify flipping \`n_w\` produces the complementary/opposite convention and is
  rejected by the canonical test.

The canonical \`L17_CORE\` path must no longer depend on an arbitrary
\`wetting_sign\` default.

A debug override may remain but must not be the default and must be labelled
non-canonical.

### D1.2 Sessile-droplet validation

Run 60/90/120 deg.

Improve the measurement instrument enough that the predeclared fit-quality
criterion is actually measurable. Prefer sub-grid contour extraction / local
normal fitting over increasing domain size blindly.

Predeclare:
- contour/fit-quality gate;
- angle-error gate;
- minimum snapshot times.

Retain:
- initial field;
- final field;
- \(\psi=0\) contour;
- fitted interface;
- wall line;
- angle wedge;
- measured-vs-prescribed plot;
- absolute-error plot.

## 4. D2 — valid slit capillary-pressure benchmark

The fluid-fluid interface must intersect the walls.

Use a geometry equivalent to:

\`\`\`text
x = longitudinal / meniscus direction
y = slit gap direction
z = periodic extrusion

solid wall at low y
fluid gap h
solid wall at high y

red liquid | curved meniscus | blue gas
\`\`\`

Seal x ends or otherwise prove that the static pressure measurement is not
polluted by a periodic second-interface topology.

Run at minimum:
- theta_liquid = 60 deg;
- theta_liquid = 90 deg;
- theta_liquid = 120 deg.

Theory:

\[
P_c=\frac{2\sigma\cos\theta}{h}
\]

for a z-invariant parallel-plate slit.

### Required outputs

For each theta:
- geometry rendering;
- final \(\psi\) field with \(\psi=0\) contour;
- contact lines visible at both walls;
- pressure/density profile through the meniscus;
- measured \(P_c\);
- predicted \(P_c\) using input \(\sigma,\theta\);
- predicted \(P_c\) using independently measured \(\sigma_{eff},\theta_{meas}\);
- residual/error.

Primary interpretation must separate:
1. nominal paper-parameter accuracy;
2. internal consistency using measured sigma/theta.

A correct sign change across 60/90/120 is a mandatory sanity check.

Do not count a flat meniscus with no contact line as a solver FAIL.

## 5. D3 — valid closed-system Jurin equilibrium benchmark

This stage validates **equilibrium Jurin rise**, not dynamic Washburn
imbibition.

Use a closed connected-liquid geometry with:
- a wide reservoir;
- a narrow vertical slit/capillary;
- common liquid connection below;
- gas above;
- gravity/body force downward;
- no open boundary requirement.

Theory:

\[
\Delta h=\frac{2\sigma\cos\theta}{\rho g h}.
\]

### Reachability precheck — mandatory

Before executing the simulation, compute from the chosen parameters:

- predicted \(\Delta h\);
- reservoir measurement range;
- capillary measurement range;
- expected final capillary level;
- clearance to the capillary entrance/top.

Abort the case as \`INVALID_CONFIGURATION\` before expensive simulation if the
predicted equilibrium is outside the measurable capillary region.

The initial condition must already place a connected liquid column inside the
capillary or otherwise guarantee that the equilibrium path is reachable.

### Required outputs

- geometry rendering with reservoir and capillary labelled;
- initial \(\psi\);
- intermediate \(\psi\);
- final \(\psi\);
- reservoir level and capillary level over time;
- final \(\Delta h\) versus theory;
- error plot.

## 6. D4 — Laplace sigma-offset diagnosis

Do not change:

\[
A=(9/4)\omega_{eff}\sigma.
\]

### D4.1 Larger-radius study

Use at least four resolved radii, with geometry chosen so:
- droplets do not interact with periodic images;
- accepted points have adequate \(R/W\);
- equilibrium radius is measured from the final field.

Report:
1. \(\Delta p\) vs \(2/R_{measured}\) with free intercept;
2. zero-intercept fit;
3. local \(\sigma_i=\Delta p_i R_i/2\);
4. \(\sigma_i\) vs \(1/R_i\) and an extrapolated large-R value if the data
   support a stable two-parameter fit.

Do not claim an infinite-radius value unless the fit is numerically stable and
the residuals support it.

Retain final droplet renderings at every radius.

### D4.2 No calibration retuning

A failing sigma scale is a result. Do not alter R1's coefficient to force the
gate.

## 7. D5 — planar mechanical-sigma diagnostic

Create:

\`docs/research/leclaire_cg/MECHANICAL_SIGMA_DERIVATION.md\`

Before coding a gate, derive from the R1 perturbation / capillary-stress
relation the exact discrete quantity corresponding to:

\[
\sigma = \int (P_N-P_T)\,dn
\]

for a planar interface.

Requirements:
- source every prefactor;
- distinguish raw perturbation second moment from the macroscopic stress if a
  collision/relaxation prefactor is required;
- state which normal and tangential components are used;
- state the discrete quadrature.

If the prefactor cannot be closed from the source, mark the diagnostic
\`EXPLORATORY / UNGATED\` rather than inventing a factor.

Compare the mechanical estimate with:
- \(\sigma_{input}\);
- the Laplace large-R estimate.

Retain:
- \(P_N-P_T\) profile;
- cumulative integral;
- final integrated value;
- residual/error.

## 8. D6 — complex-wall visualization

Rerun the corrected asymmetric-wall case under the frozen canonical wetting
convention.

Keep the existing global-mass diagnostics.

Add:
- initial/intermediate/final \(\psi\) snapshots;
- solid overlay;
- \(\psi=0\) contour;
- wall-band definition overlay;
- wall-band red mass versus time;
- global red/blue/total mass residual versus time;
- at least one contact-line/interface-position diagnostic.

Do not label wall-band redistribution nonphysical unless a stationary/no-driving
reference makes that attribution possible.

## 9. D7 — immutable Pass-4 artifact tree

Do not overwrite \`results/leclaire_cg/\` pass-3 evidence.

Create:

\`\`\`text
results/leclaire_cg/pass-04/
  VALIDATION_REPORT.md
  SUMMARY.json
  run_manifest.json
  case-01-.../
  ...
  case-10-.../
  case-11-mechanical-sigma/
\`\`\`

Follow \`VALIDATION_ARTIFACT_SPEC.md\` exactly.

### Raw snapshots

For these small canonical cases, retain compressed raw state sufficient to
regenerate the visualizations:
- solid mask;
- psi;
- rho;
- rho_r;
- rho_b;
- velocity or velocity magnitude;
- any pressure/stress diagnostic used.

Minimum times:
- initial;
- one representative intermediate time for dynamic cases;
- final/equilibrium.

### Figure set

Every case must contain:
1. geometry/field rendering;
2. primary observable plot;
3. error/residual plot.

Every figure must have a \`render_manifest.json\` regeneration path.

## 10. D8 — durable-document cleanup

Make the latest versions internally consistent without deleting Git history.

Required:
- current R5 mapping status appears once and is consistent;
- current 科研通 acquisition statement appears once and is consistent;
- Table-IV ordering is non-shell-major everywhere;
- old pass-1/pass-2 results are explicitly labelled \`SUPERSEDED\`;
- pass-4 becomes the only current headline in \`EXECUTION_REPORT.md\` / atlas;
- do not leave "Laplace RESOLVED" if pass-4 evidence does not support it.

Update:
- \`VALIDATION_ATLAS.md\` with pass-4 renderings and current status;
- algorithm-evolution record with the Eq.(4) mass-source causal chain.

## 11. Full rerun and evidence

After all code/test/instrument changes are frozen:
1. run unit checks;
2. run the full canonical matrix once;
3. run case 11 mechanical-sigma diagnostic;
4. generate all raw snapshots and figures from that same frozen candidate;
5. verify every figure regenerates;
6. update pass-04 report/summary;
7. do not edit acceptance gates after seeing results.

Record:
- source candidate SHA;
- evidence commit SHA;
- exact environment;
- per-case exit codes;
- wall time;
- raw-data schema version.

## 12. Commit discipline

Use separate commits, at minimum:

1. \`convention:\` normative wetting convention + analytic unit lock;
2. \`validation-fix:\` corrected Pc/Jurin geometries and instruments;
3. \`diagnostic:\` Laplace/mechanical-sigma work;
4. \`visualization:\` raw snapshot/render pipeline;
5. \`validation:\` frozen pass-04 evidence;
6. \`docs:\` durable-record cleanup / atlas update.

Corrections after a failed run are new commits; never amend history.

## 13. Stop rule

After pass-04 evidence and review request are committed:
- STOP;
- do not port to Taichi;
- do not change production;
- do not start V3/graphite.

The next action is a fresh independent review.
