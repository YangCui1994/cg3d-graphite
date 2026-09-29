# Validation Artifact & Visualization Specification

Status: **binding for new validation work after 2026-09-27**

Applies to:
- current production CG validation;
- \`L17_CORE\` / Leclaire-Latt reference line;
- later Akai/wetting variants;
- future Taichi/f32 ports;
- V3/V4 porous-media validation.

## 1. Purpose

Every simulation case must leave behind an artifact that answers, without
re-reading the implementation history:

1. **What case was run?**
2. **What should the standard/theoretical result look like?**
3. **What did the simulation actually produce?**
4. **How large is the error or residual?**
5. **Is the discrepancy caused by the solver, the measurement instrument, or an invalid test?**
6. **Can the figures be regenerated from retained data?**

The research/evolution log remains responsible for *why* the implementation
changed. This specification is responsible for *what the validated behaviour
looks like*.

## 2. Two complementary records

### 2.1 Development/evolution record

Keep:
- bug mechanism;
- code/formulation change;
- superseded interpretation;
- causal diagnosis;
- reviewer findings.

Do **not** use it as the primary publication-facing validation summary.

### 2.2 Validation atlas

For each canonical case, retain a compact, visual record of:
- geometry and BCs;
- theoretical/reference expectation;
- initial/final fields;
- primary observable;
- error/residual;
- verdict and scope.

The atlas should be understandable without reconstructing Git history.

## 3. Immutable per-pass layout

Every validation pass gets a new immutable directory:

\`\`\`text
results/<solver-line>/pass-<NN>/
  VALIDATION_REPORT.md
  SUMMARY.json
  run_manifest.json

  case-01-<name>/
    README.md
    metadata.json
    metrics.json
    metrics.csv
    raw/
    figures/
    logs/
    render_manifest.json
    reproduce.py
\`\`\`

Never overwrite a previous pass. If a case is rerun after a code or
measurement correction, create a new pass.

## 4. Required per-case README

Each case README must contain the following blocks.

### 4.1 Case identity

\`\`\`text
Case ID:
Case name:
Solver mode:
Candidate SHA:
Physical target:
Reference/theory:
Verdict:
\`\`\`

### 4.2 Setup

Record at minimum:
- domain size;
- lattice;
- initial condition;
- solid geometry;
- boundary conditions;
- wetting/contact-angle convention;
- viscosity/density parameters;
- sigma;
- beta;
- forcing/gravity;
- precision/backend;
- run length;
- snapshot times.

### 4.3 Standard/reference result

State explicitly:
- governing relation;
- expected qualitative field;
- expected trend;
- quantitative acceptance gate.

Example:

\`\`\`text
Laplace:
Delta p = 2 sigma / R

Expected:
- Delta p linear in 2/R;
- intercept approximately zero;
- fitted sigma close to sigma_input.
\`\`\`

### 4.4 Actual result

Use a compact table:

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| example | ... | ... | ... | ... |

### 4.5 Interpretation boundary

Choose one:
- \`PASS\`
- \`FAIL_SOLVER\`
- \`FAIL_MEASUREMENT\`
- \`INVALID_TEST\`
- \`INCONCLUSIVE\`

A test-design failure must never be presented as a solver failure.

## 5. Mandatory retained simulation outputs

### 5.1 Every run

Retain:
- \`metadata.json\`;
- \`metrics.json\`;
- \`metrics.csv\` for time histories/sweeps;
- stdout/stderr or run log;
- candidate SHA and environment;
- code path/mode and all switches;
- exit code;
- exact figure-generation script.

### 5.2 Canonical validation cases

Retain enough raw state to regenerate every publication-facing figure.

Minimum snapshots:
- initial state;
- one representative intermediate state for dynamic cases;
- final/equilibrium state.

For small canonical domains, commit compressed raw arrays such as:
- \`rho\`;
- \`rho_r\`;
- \`rho_b\`;
- \`psi\`;
- velocity components or magnitude;
- solid mask;
- pressure/density proxy if used by the metric.

Recommended format: compressed NPZ with an explicit schema/version.

### 5.3 Large 3D porous runs

Do not commit an entire high-frequency 4D history by default.

Commit:
- selected full-resolution checkpoints needed for scientific claims, when size permits;
- otherwise decimated/downsampled fields;
- orthogonal slices;
- isosurface coordinates or render-ready reduced geometry;
- time-series metrics;
- a manifest containing the external/full-data location and SHA256.

The repository artifact must still be sufficient to understand the claim even
when the complete volume is stored outside Git.

## 6. Mandatory visualizations

Every canonical case must contain all three categories below.

### A. Geometry / field rendering

Purpose: show what was actually simulated.

Minimum:
- geometry/solid mask;
- initial phase field;
- final phase field.

For 3D:
- at least one fixed-camera isosurface view of \`psi = 0\`;
- orthogonal slices through the same registered coordinates;
- solid geometry visible or overlaid.

For 2D/slices:
- fixed coordinate extents;
- same colour scale between compared runs;
- solid region visibly distinguished.

### B. Primary scientific observable

Examples:
- Laplace: \`Delta p\` vs \`2/R\`;
- contact angle: measured vs prescribed theta + interface contour overlay;
- beta sweep: interface width vs beta + positivity flags;
- Jurin: inside/outside liquid height vs time;
- Washburn: \`x^2\` vs \`t\` when the assumptions support it;
- dynamic isotropy: interface Fourier amplitude vs time;
- conservation: total/component mass residual vs time.

### C. Error / residual view

Examples:
- theory-minus-measurement residual;
- relative error versus parameter;
- mass drift;
- contact-angle absolute error;
- symmetry error;
- fitted residual field.

The main result figure and error figure must not be the same plot with a
different title.

## 7. Rendering consistency

Within one solver line:
- fixed phase convention;
- fixed colour limits for \`psi\` (normally [-1,1]);
- fixed camera/view for A/B comparisons;
- fixed solid appearance;
- fixed axis orientation;
- units on every axis;
- candidate SHA or pass ID in caption/metadata;
- no auto-rescaling that makes two different fields look artificially similar.

## 8. Render manifest

Every case must include \`render_manifest.json\` recording:
- source raw file(s);
- source candidate SHA;
- plotted variable;
- slice/index or camera;
- min/max scale;
- isosurface level;
- time step;
- figure filename;
- script/version that created the figure.

A rendered figure without a regeneration path is not durable evidence.

## 9. Theory vs actual vs error is mandatory

Every publication-facing case must show the relationship visually and
numerically:

\`\`\`text
STANDARD / THEORY
       |
       v
EXPECTED observable
       |
       +------ measured simulation
       |          |
       |          v
       +------ residual / error
                  |
                  v
               verdict
\`\`\`

The reader should not need to infer the expected result from prose.

## 10. Historical-backfill rule

Old runs may lack raw fields because the previous workflow retained only
metrics/evidence JSON.

For such runs:
- backfill metric plots from committed evidence;
- clearly mark field rendering as \`NOT RETAINED — CANNOT RECONSTRUCT\`;
- never regenerate a plausible-looking field from summary metrics;
- preserve this gap as a provenance limitation.

The initial Leclaire historical backfill is:
\`docs/research/leclaire_cg/VALIDATION_ATLAS.md\`.

## 11. Relationship to reviews

A reviewer must inspect:
- README/theory definition;
- retained raw data;
- rendered figures;
- metrics JSON;
- reproduction script.

A PASS cannot rely only on a visually plausible rendering. The image is the
human-readable view; the raw metric and gate remain authoritative.

## 12. Promotion gate

Before a solver line is eligible for promotion or publication-facing use:

- every headline validation claim has a case artifact;
- every case artifact has standard/actual/error;
- every headline field claim has retained raw data and rendering;
- invalid/inconclusive tests are visually documented, not silently dropped;
- atlas/current headline agrees with machine-readable summary;
- historical superseded passes remain immutable.
