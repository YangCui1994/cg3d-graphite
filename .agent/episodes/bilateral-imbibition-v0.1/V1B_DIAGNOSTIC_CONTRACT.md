# V1b Diagnostic Contract — Boundary / Static Pc / Dynamic Pc Separation

Task ID: BI-V1B-DIAGNOSTIC-001

## 1. Objective

Resolve the scientific ambiguity exposed by V1 before any bilateral-front or porous-media work.

V1b must separate:

1. bulk slit hydraulic resistance;
2. reservoir/membrane/open-buffer boundary resistance;
3. static slit capillary pressure for the current wall-colour wettability;
4. moving-meniscus capillary pressure and its relation to the observed front speed.

V1b is a **small synthetic diagnostic task**. It does not authorize solver-physics changes, V2, V3, graphite geometry, separator geometry, interface-gap sweeps, or PCS.

## 2. Authoritative inputs

Read before implementation:

- `.agent/evidence/BI-VALIDATION-001/V1/V1/V1_EXTERNAL_SCIENTIFIC_REVIEW.md`
- `.agent/episodes/bilateral-imbibition-v0.1/EPISODE_PLAN.md`
- `AGENTS.md`
- product-base `docs/BC_IC_OUTPUT.md`
- product-base `docs/ALGORITHM.md`

Scientific base candidate:

`e9540bcadb86257c70b805afc98f2eec9626c64e`

This contains the accepted V0 repair plus the V1 diagnostic implementation/evidence.

## 3. Fixed scientific assumptions

Do not change:

- D3Q19 MRT color-gradient solver formulation;
- `CapA = 0.06`;
- matched viscosities `nu_l = nu_g = 0.1`;
- unit-density-ratio formulation;
- wetting phase convention used by V1: `psi = -1`;
- non-wetting phase convention used by V1: `psi = +1`;
- wall colour `psi_solid = -0.68`;
- z-periodic slit concept;
- no externally imposed pressure difference in the dynamic filling cases;
- no solver source code.

The existing droplet-derived 30-degree contact-angle registry is a **reference diagnostic**, not an assumed dynamic capillary-pressure truth.

## 4. Allowed product changes

Create new V1b-specific files only, preferably:

- `tests/levelc_v1b.py`
- optional V1b-only helper/diagnostic files under `tests/`
- `results/levelc_v1b/**`

Do not modify:

- `lbm_solver_cg3d.py`
- `cg3d/**`
- existing V0 tests;
- existing V1 driver/results, except read-only use;
- `.agent/episodes/**/runner/episode_runner.py`.

If a solver change appears necessary, stop and report `HUMAN_REQUIRED`.

## 5. Dynamic boundary layout — V1b-A

Replace the V1 overlapping/abrupt reservoir layout with a separated open-boundary layout.

Default symmetric adaptation of the repository convention:

```text
3 lu solid wall
| 8 lu pinned wetting reservoir
| 1 lu phase-selective membrane
| >=2 lu open buffer
| uniform active slit
| >=2 lu open buffer
| 1 lu phase-selective membrane
| 8 lu pinned non-wetting reservoir
| 3 lu solid wall
```

Requirements:

- the membrane plane must not overlap either pinned reservoir mask;
- the active slit must not directly touch a pinned reservoir or membrane;
- the open buffer uses ordinary fluid nodes and the same slit cross-section;
- both reservoirs are pinned to `rho = 1`, so imposed pressure difference is zero;
- inlet membrane passes wetting phase / blocks non-wetting phase;
- outlet membrane passes non-wetting phase / blocks wetting phase;
- exact x-index layout must be printed and written to JSON;
- no hidden geometry changes between h=26 and h=40 except the y dimension.

If the repository implementation requires an outlet buffer of 3 lu rather than 2 lu, that is acceptable if explicitly recorded; overlap is not acceptable.

## 6. Same-slit static capillary calibration — V1b-B

Build a static calibration that does **not** use the dynamic reservoirs/membranes.

Preferred setup:

- long straight slit;
- y walls use the same `psi_solid=-0.68`;
- z periodic;
- x periodic with a wetting slab and non-wetting surroundings, producing two well-separated menisci;
- no pressure forcing and no reservoirs;
- interfaces separated far enough that they do not interact materially.

Alternative static setups are allowed only if they isolate the same slit wall/contact-line geometry without introducing the dynamic boundary resistance.

Run at least:

- h=26;
- h=40.

Relax to a defensible static state. Record the stopping/convergence diagnostic rather than equating process completion with convergence.

Measure bulk phase pressures away from both diffuse interfaces and calculate:

`Pc_static = |p_nonwetting - p_wetting|`

Then report:

`C_static = Pc_static * h / (2 sigma)`

and

`theta_static_slit = arccos(clamp(C_static,-1,1))`.

### Static consistency gate

The normalized coefficients `C_static` for h=26 and h=40 must agree within **10% relative difference**.

This is a project engineering consistency gate for resolution transfer, not a universal literature threshold.

The absolute difference from the existing 30-degree droplet registry is diagnostic and must be reported, not automatically failed.

## 7. Corrected dynamic filling — V1b-C

Run the corrected dynamic layout at:

- h=26;
- h=40.

Record at minimum:

- front position vs time using a diffuse-interface-robust primary definition;
- secondary front definition;
- exact fit window;
- `V_meas`;
- `R2[x,t]`;
- far-field liquid and gas pressure gradients;
- far-field-extrapolated `Pc_dynamic`;
- local boundary pressure jumps at both open-boundary transitions;
- reservoir densities;
- colour-mass accounting;
- `u_max`, `u_rms`;
- spurious/local current diagnostic near the moving interface;
- capillary number `Ca = mu V_meas / sigma`.

Do not use the old near-interface slab quantity `pc_measured_last` as a physical capillary-pressure measurement.

If retained for comparison, label it explicitly `INVALID_NEAR_INTERFACE_DIAGNOSTIC`.

### Dynamic reference law

For this matched-viscosity two-bath configuration:

`x(t) = x0 + V t`.

The classical gas-negligible `x^2 proportional to t` law is diagnostic only and is not a pass/fail gate.

Define `L_hyd` explicitly from the corrected geometry as the uniform slit-flow path between the sample-side boundary reference planes, including same-cross-section open-buffer length where appropriate.

Calculate:

`V_hyd = Pc_dynamic * h^2 / (12 mu L_hyd)`.

### Dynamic hard gates

For both h=26 and h=40:

1. no NaN/Inf;
2. no operational velocity-cap violation;
3. zero imposed reservoir pressure difference verified;
4. monotonic post-transient advance;
5. a declared post-transient interval exists and is valid — if the threshold is never reached, fail explicitly; never use `np.argmax(False...)=0` silently;
6. `R2[x,t] >= 0.995` on the declared interval;
7. `|V_meas/V_hyd - 1| <= 0.10`;
8. measured far-field pressure gradients are consistent with plane-Poiseuille at the observed velocity to within 10%;
9. colour-mass closure is reported and shows no unexplained order-one leakage.

The 10% values are project engineering gates for internal numerical consistency.

## 8. Length-sensitivity diagnostic — V1b-D

Repeat the corrected h=26 dynamic case with approximately 2x the uniform hydraulic length while keeping:

- slit height;
- wetting;
- surface tension;
- viscosity;
- boundary layout;
- reservoir/buffer thicknesses

unchanged.

Using the two measured speeds, infer the equivalent fixed extra hydraulic length `L_eq` from:

`V2/V1 = (L1 + L_eq)/(L2 + L_eq)`.

Report:

- `L1, L2`;
- `V1, V2`;
- `L_eq`;
- `L_eq/L1`;
- comparison with old V1 estimate (~0.78 of L1).

This is a **diagnostic**, not a hard numeric pass gate in V1b.

However, if `L_eq/L1` remains clearly order-one, the internal reviewer must not recommend proceeding to V2.

## 9. Dynamic/static comparison — V1b-E

For h=26 and h=40 report:

- `Pc_static`;
- `Pc_dynamic`;
- `Pc_dynamic/Pc_static`;
- `theta_static_slit`;
- an apparent moving-meniscus angle inferred from `Pc_dynamic` only as a model diagnostic;
- `Ca`.

Do not require static and dynamic angles to be equal.

If hydraulic consistency passes while `Pc_dynamic != Pc_static`, classify the difference as a moving-contact-line/model characteristic pending further Ca dependence. Do not automatically call it a solver defect.

## 10. Evidence/provenance requirements

The V1 evidence bundle exposed producer/provenance drift. V1b must close it.

Every primary output CSV/JSON must contain or be accompanied by:

- candidate SHA;
- producer script path;
- producer script Git blob SHA or file SHA256;
- exact command;
- start/end timestamp;
- exit code;
- parameter set.

Required durable files under `results/levelc_v1b/`:

- `PROVENANCE.md`
- `MANIFEST.json`
- `EXECUTION_REPORT.md`
- static h26/h40 numerical data;
- dynamic h26/h40 numerical data;
- length-scan numerical data;
- pressure-budget summary table;
- machine-readable summary JSON.

Figures are optional.

If figures are committed, they must be regenerated from the **final committed producer code** after the candidate commit is created, or their provenance must bind unambiguously to that exact source blob. Otherwise omit them.

Preserve a console log and exit code for every primary run.

## 11. Executor interpretation rules

Separate these statements:

- **measured fact**;
- **analytic relation**;
- **project engineering gate**;
- **model interpretation**;
- **unresolved scientific question**.

Do not tune `psi_solid`, `CapA`, viscosity, geometry height, or acceptance thresholds to make the case pass.

Do not change solver physics.

Do not present a stable front as proof of quantitatively correct wetting.

## 12. Internal reviewer decision

A fresh reviewer must choose exactly one:

- `PASS`
- `CHANGES_REQUESTED`
- `HUMAN_REQUIRED`

### PASS means only

- the V1b diagnostic contract was executed correctly;
- all static/dynamic hard gates above pass;
- evidence/provenance is auditable;
- no order-one boundary-resistance signature remains unexplained;
- no solver change was used.

PASS does **not** authorize V2 automatically. It means the package is ready for external scientific review.

### CHANGES_REQUESTED

Only for finite implementation/evidence defects that do not change scientific assumptions.

### HUMAN_REQUIRED

Use when:

- boundary resistance remains order-one;
- static slit scaling is inconsistent;
- dynamic hydraulic consistency fails without a finite measurement/implementation correction;
- solver physics would need modification;
- a new scientific assumption is required.

## 13. Stop boundary

After the fresh reviewer writes its decision, stop.

Do not start V2, V3, graphite, interface-gap, separator, or PCS work.
