# Conservation Audit Contract — BI-CONSERVATION-AUDIT-001

## 0. Task identity

- **Task ID:** BI-CONSERVATION-AUDIT-001
- **Purpose:** locate and classify the monotone mass drift observed in V1c/V2 before any V3 trapped-pocket / buffer-sensitivity study
- **Scientific base:** V2 candidate
  \`5e679d8d99d338f9ab28565c636f021a0f9211b2\`
- **Control review:** \`.agent/evidence/BI-V2-BILATERAL-001/V2_EXTERNAL_SCIENTIFIC_REVIEW_PASS.md\`

This is a **diagnostic solver-audit task**.

It does not authorize:

- changing collision physics;
- changing recoloring;
- changing bounce-back formulas;
- changing the pressure EOS;
- changing wall wetting;
- changing MRT relaxation;
- tuning tolerances to hide the drift;
- starting V3.

If the audit identifies a solver defect, stop and return a solver-fix proposal for a separate task.

---

# 1. Audit question

The accepted V2 candidate shows a monotone closed-system mass drift of order

\[
5.5\times10^{-4}
\text{ to }
9.2\times10^{-4}
\]

over 60k steps, depending on bookkeeping channel.

The audit must answer:

1. **At which solver sub-step does the first measurable mass imbalance appear?**
2. **Is the drift primarily:**
   - floating-point / atomic accumulation;
   - recoloring;
   - colour-population transport;
   - total-distribution transport;
   - bounce-back / wall handling;
   - macro reconstruction;
   - inconsistent bookkeeping between total and colour populations?
3. **Does the drift require an actual solver correction before V3?**
4. **If it is only a bounded floating-point floor, what measured scaling law supports that conclusion?**

The audit must localize the mechanism before any correction is attempted.

---

# 2. Fixed solver and physics

The audit base is the exact V2 solver implementation.

Do not modify:

- \`lbm_solver_cg3d.py\`;
- \`cg3d/**\`;
- V1/V1b/V1c/V2 result history;
- the episode runner.

Allowed changes are audit-only files, preferably:

- \`tests/conservation_audit.py\`;
- optional small audit helpers under \`tests/\`;
- \`results/conservation_audit/**\`.

The audit driver may call the existing solver kernels directly in the same order as \`step()\`.

No solver code may be edited to add diagnostics.

If an internal quantity cannot be measured without modifying the solver, document the missing observable and stop rather than silently changing production code.

---

# 3. Mass definitions

At every audit checkpoint record all available conserved-mass views.

## 3.1 Total-distribution mass

\[
M_f
=
\sum_{\mathrm{fluid}}\sum_{q=0}^{18} f_q
\]

Record separately for the current total-distribution field used by the solver at that checkpoint:

- \`f\`;
- \`F\` where relevant.

Because \`F\` is a streaming accumulator / alternate storage field, do not add \`f+F\` unless the solver state at that checkpoint mathematically requires both. Document which field is authoritative at every checkpoint.

## 3.2 Colour-population mass

\[
M_c
=
\sum_{\mathrm{fluid}}(\rho_r+\rho_b)
\]

Also record independently:

\[
M_r=\sum\rho_r,
\qquad
M_b=\sum\rho_b.
\]

Where transitional colour accumulators exist, also record:

\[
M_{r,\mathrm{acc}}=\sum rhor,
\qquad
M_{b,\mathrm{acc}}=\sum rhob.
\]

## 3.3 Macro density mass

\[
M_\rho
=
\sum_{\mathrm{fluid}}\rho.
\]

## 3.4 Cross-representation residuals

At each checkpoint report:

\[
\delta_{fc}
=
\frac{M_f-M_c}{M_0},
\]

\[
\delta_{f\rho}
=
\frac{M_f-M_\rho}{M_0},
\]

\[
\delta_{c\rho}
=
\frac{M_c-M_\rho}{M_0}.
\]

These residuals are the primary diagnostic observables.

Use float64 host reductions for all audit sums.

---

# 4. Per-step decomposition

Reproduce the production timestep exactly, but expose checkpoints.

Production order:

\`\`\`text
collision(+recolor)
→ F.fill(0)
→ streaming1
→ Boundary_condition
→ streaming3
→ Boundary_condition_psi
→ apply_reservoirs   [only if enabled]
\`\`\`

The audit cases in this task must use **no reservoirs**, so \`apply_reservoirs\` is absent.

For each audited step record states:

\`\`\`text
S0  before collision
S1  after collision
S2  after F.fill(0)
S3  after streaming1
S4  after Boundary_condition
S5  after streaming3
S6  after Boundary_condition_psi
\`\`\`

Also record the start of the next step and verify whether:

\[
S6(n)
\equiv
S0(n+1)
\]

for every mass representation that should be identical.

The audit must not merely compare every 1000 steps; it must include per-substep measurements.

---

# 5. Isolation matrix

Run at least the following four cases.

The exact domain may be small for speed, but it must be large enough to contain a stable interface where applicable.

Recommended dimensions are starting points, not hard requirements.

---

## C0 — periodic single phase, no solid

Purpose:

> isolate pure collision / streaming / accumulation without interface or wall effects.

Suggested:

- \(N_x=N_y=N_z=24\) or 32;
- no solid;
- \(\psi=-1\) everywhere;
- \(\rho=1\);
- zero velocity;
- no force;
- no reservoirs;
- periodic all directions.

Run:

- at least 5000 steps;
- detailed sub-step logging for the first 20 steps;
- long-horizon summary every 100–500 steps.

Expected:

- no recoloring contribution because colour gradient should vanish;
- wall bookkeeping absent.

---

## C1 — periodic two phase, no solid

Purpose:

> add interface + colour-gradient + recoloring, while keeping wall/bounce-back absent.

Geometry:

- periodic domain;
- one wetting slab / one non-wetting slab or two interfaces;
- interfaces far apart;
- same \`CapA=0.06\`;
- matched \`nu=0.1\`;
- no force.

Run:

- at least 10k steps;
- sub-step logging for first 20 and one late window.

Primary comparison:

\[
\Delta M_{\rm C1}-\Delta M_{\rm C0}
\]

to isolate interface/recoloring-associated effects.

---

## C2 — single phase slit with bounce-back walls

Purpose:

> add wall / bounce-back bookkeeping without a two-phase interface.

Geometry:

- straight slit;
- y walls;
- z periodic;
- x periodic if convenient;
- pure single phase;
- no force;
- no reservoirs.

Run:

- at least 10k steps.

Primary comparison:

\[
\Delta M_{\rm C2}-\Delta M_{\rm C0}.
\]

---

## C3 — two-phase slit with bounce-back walls

Purpose:

> closest minimal analogue of V2.

Geometry:

- same wall wetting \(\psi_\mathrm{solid}=-0.68\);
- two phases;
- z periodic;
- x arrangement chosen so interfaces are present but no open boundaries exist;
- no force;
- no reservoirs.

This case should be as close as practical to the V2 closed trapped-pocket mechanism while remaining small.

Primary comparison:

\[
\Delta M_{\rm C3}
\]

against C0/C1/C2.

---

# 6. Spatial budget

For C3 and one relevant late snapshot, partition the fluid mass budget into at least:

1. wall-adjacent rows;
2. interface bands;
3. gas-pocket bulk;
4. liquid bulk;
5. remaining interior.

The partition must be defined mechanically from geometry and \(\psi\).

Report per region:

\[
\Delta M_r,
\quad
\Delta M_b,
\quad
\Delta M_c,
\quad
\Delta M_\rho.
\]

The purpose is to test the V2 reviewer's preliminary observation that mass is redistributed differently between:

- interface bands;
- pocket;
- interior;
- wall-adjacent rows.

Do not infer causality from the spatial budget alone; combine it with the per-kernel audit.

---

# 7. Precision/backend audit

At minimum run C0 and C3 on the normal GPU backend.

If practical, also run a small C0/C1/C2/C3 matrix on CPU.

The purpose is not performance benchmarking.

Compare drift rates:

\[
r_M
=
\frac{1}{T}
\frac{|M(T)-M(0)|}{M(0)}.
\]

Interpretation:

- similar CPU/GPU drift pattern → more likely algorithm/bookkeeping;
- strongly GPU-only drift → atomic ordering / float32 accumulation becomes more plausible;
- do not declare either mechanism from one case alone.

Do not change field precision in production solver in this audit.

A float64 experimental implementation, if desired, belongs in a later dedicated solver task.

---

# 8. Scaling tests

To distinguish a fixed per-step floating-point floor from geometry-dependent loss, run at least one scaling probe.

Recommended choices:

### Domain-size scaling

For C0 or C1:

- N = 16 / 24 / 32 or similar.

### Horizon scaling

For one representative case:

- 5k / 10k / 20k steps.

Report whether:

\[
|\Delta M|
\propto T
\]

and whether the relative rate is approximately constant.

If drift is linear in time, report the fitted slope and \(R^2\).

If drift scales with interface area or wall area, report that normalized scaling.

---

# 9. Hard audit requirements

The audit is complete only if:

1. all four C0–C3 cases run successfully;
2. at least one detailed per-kernel sub-step trace exists for each case;
3. \`M_f\`, \`M_c\`, \`M_\rho\` are compared explicitly;
4. the first checkpoint where each cross-representation residual becomes nonzero is identified;
5. a spatial budget is provided for C3;
6. at least one precision/backend comparison is reported, or an explicit reason why it could not be run;
7. at least one scaling probe is reported;
8. no solver source change is made.

---

# 10. Diagnostic outcome classes

The executor must classify the evidence into one of the following, without forcing a choice if evidence is ambiguous.

## A — bounded floating-point accumulation

Use only if evidence shows:

- no discrete bookkeeping imbalance at a specific kernel;
- residual scales with arithmetic order / backend / domain size in a manner consistent with floating-point accumulation;
- no region or kernel shows a systematic missing/excess mass transfer.

## B — colour/total-population bookkeeping mismatch

Use if:

- \(\rho_r+\rho_b\) and total \(f\)-mass diverge at a specific sub-step;
- the mismatch is repeatable and not explained by the intended transient storage representation.

## C — bounce-back / wall transport imbalance

Use if:

- C0/C1 are clean;
- C2/C3 introduce the drift;
- sub-step localization points to streaming / bounce-back / boundary handling.

## D — recoloring / interface imbalance

Use if:

- C0/C2 are clean;
- C1/C3 show the drift;
- mismatch appears at collision/recoloring or colour-population reconstruction.

## E — macro reconstruction mismatch

Use if:

- distribution/colour masses remain mutually consistent;
- \(\rho\) diverges only after macro reconstruction.

## U — unresolved

Use if the evidence does not uniquely support A–E.

---

# 11. No-fix rule

This task must not repair the solver.

If a specific defect is identified:

- name the kernel / code path;
- identify the relevant conservation identity;
- estimate expected correction scope;
- list regressions that would need rerun;
- return \`PASS_DIAGNOSIS_READY_FOR_FIX\`.

If the result is only a bounded numerical floor:

- quantify its scaling;
- state a defensible operational bound;
- return \`PASS_BOUNDED_FLOOR\`.

If unresolved:

- return \`HUMAN_REQUIRED\`.

---

# 12. Evidence outputs

Create under:

\`results/conservation_audit/\`

Required:

- \`EXECUTION_REPORT.md\`
- \`PROVENANCE.md\`
- \`MANIFEST.json\`
- \`summary.json\`
- \`substep_mass_trace.csv\`
- \`long_horizon_mass.csv\`
- \`spatial_budget.csv\`
- \`backend_comparison.csv\` or explicit \`NOT_RUN\` record
- \`scaling_results.csv\`
- console logs + shell exit codes
- candidate-bound source/provenance metadata

Recommended:

- one machine-readable per-case report.

---

# 13. Mandatory technical-document update

After the fresh reviewer completes, update:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

Add a new section:

\`SOLVER Conservation Audit — BI-CONSERVATION-AUDIT-001\`

It must include:

1. task/base/candidate SHA;
2. the mass identities;
3. solver-step decomposition;
4. audit code excerpts;
5. C0–C3 matrix;
6. one figure of mass residual vs timestep;
7. one figure showing sub-step localization;
8. spatial budget figure/table;
9. CPU/GPU or scaling comparison;
10. final mechanism classification A–E/U;
11. whether a solver-fix task is required;
12. evidence paths.

The living document is a required output.

---

# 14. Fresh reviewer decision

Reviewer chooses exactly one:

- \`PASS_DIAGNOSIS_READY_FOR_FIX\`
- \`PASS_BOUNDED_FLOOR\`
- \`CHANGES_REQUESTED\`
- \`HUMAN_REQUIRED\`

Reviewer must not modify solver code.

## PASS_DIAGNOSIS_READY_FOR_FIX

Use when the mass-loss mechanism is localized strongly enough to justify a separate solver-fix task.

## PASS_BOUNDED_FLOOR

Use only when the observed drift is quantitatively consistent with a bounded numerical-precision floor and no discrete algorithmic imbalance is found.

## CHANGES_REQUESTED

Use for finite audit/evidence defects.

## HUMAN_REQUIRED

Use for unresolved or conflicting evidence that requires changing audit assumptions.

---

# 15. Stop boundary

After fresh review + technical-document publication:

**STOP.**

Do not:

- change solver physics;
- start V3;
- start graphite / separator / gap / PCS work.
