# Scientific Masterline — CG3D Two-Phase LBM

> **Document type:** scientific source-of-truth / model lineage  
> **Status:** normative at the science layer  
> **Updated through:** Pass-4 fresh review + external review R3  
> **Purpose:** answer one question: **what physical/numerical formulation are we actually using, where did each element come from, how does it differ from the other line, and what is currently validated?**

This document is deliberately different from:
- implementation history;
- agent task contracts;
- review logs;
- validation evidence.

Those documents remain useful, but **none of them individually defines the current scientific model**.

---

# 0. Scientific hierarchy

Use the following hierarchy when two documents appear to disagree.

## S0 — primary literature

The paper itself is authoritative for what that paper states.

## S1 — this scientific masterline

This file is authoritative for:
- which literature element belongs to which model line;
- which formulation is currently canonical for the project;
- which elements are project-specific extensions;
- which scientific claims are accepted / unresolved / rejected.

## S2 — equation-level formulation documents

Examples:
- \`PAPER_FORMULATION.md\`
- \`CURRENT_VS_LECLAIRE_MAP.md\`
- \`FOLLOWUP_OPTIMIZATION_MAP.md\`

These contain derivations and detailed equation mapping.

If an S2 file conflicts with S1 because an old statement was not cleaned up,
S1 gives the current scientific status and the S2 file must be corrected.

## S3 — validation atlas / case artifacts

These answer:
- what was simulated;
- expected result;
- measured result;
- error;
- verdict.

They are evidence, not the definition of the model.

## S4 — algorithm / implementation evolution logs

Example:
\`bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

These preserve chronology and debugging causality.

They are **historical**, not a current source-of-truth.

## S5 — \`.agent/**\` contracts and evidence

These preserve task execution, provenance and reviews.

They never redefine physics by themselves.

---

# 1. There are two distinct CG model lines in this repository

The largest source of confusion so far has been treating “the CG solver” as if
there were one formulation.

There are currently **two scientifically distinct lines**.

\`\`\`text
                        CG3D project
                            |
             +--------------+--------------+
             |                             |
     CURRENT PRODUCTION CG             L17 REFERENCE CG
     lbm_solver_cg3d.py                 experimental/leclaire_cg/
             |                             |
     hybrid / project-specific         Leclaire-2017 paper line
             |                             |
     V0/V1/V2/V3 history              clean-room f64 reference
\`\`\`

They share the same broad color-gradient family but are **not mathematically the
same solver**.

This distinction must remain explicit in all future documentation.

---

# 2. Model line A — current production CG

Primary code:
\`lbm_solver_cg3d.py\`

Scientific status:
**project production baseline, not a paper-faithful Leclaire-2017 implementation**

## 2.1 Core characteristics

| module | production implementation |
|---|---|
| lattice | D3Q19 |
| collision | MRT |
| phase field | \(\psi=(\rho_r-\rho_b)/(\rho_r+\rho_b)\) |
| density ratio | unit-density regime |
| equilibrium | project closed-form MRT equilibrium |
| viscosity | project relaxation-rate blending |
| surface tension | moment-space stress/equilibrium injection |
| recoloring | pairwise min-amplitude recoloring |
| explicit beta | absent |
| wetting | fictitious wall colour \(\psi_{solid}\) |
| bounce-back | project half-way style in streaming |
| open-system support | reservoirs, membranes, pressure/psi boundaries |
| backend | Taichi/CUDA |
| arithmetic extensions | T3 + C1X + A2 |

## 2.2 Important project-specific solver corrections

These are not Leclaire-paper changes; they are corrections/extensions of the
production implementation.

Examples already established in the historical evolution record:

- complete density dependence in the MRT equilibrium;
- normalized phase-field definition;
- Guo forcing 3/9 factors;
- normalized wall-adjacent bulk suppression;
- per-node wall colour;
- finite-precision conservation work:
  - T3: f64 inverse reconstruction accumulator;
  - C1X: weighted local colour closure;
  - A2: f64 post-equilibrium colour closure/transport path.

These belong to the **production numerical implementation layer**.

They must not be retroactively attributed to Leclaire et al.

## 2.3 Production baseline evidence

Historical V0-level evidence includes:
- Poiseuille mean-flow efficiency ~0.9933;
- Poiseuille profile L2 error ~0.0075;
- production Laplace calibration near \(\sigma\approx1.012\,CapA\);
- flat-wall \(\psi_{solid}\) contact-angle calibration;
- later conservation correction closure.

These results validate the production line **within the geometries actually tested**.

They do not prove equivalence to the L17 reference line.

---

# 3. Model line B — Leclaire/Latt reference CG

Primary code:
\`experimental/leclaire_cg/**\`

Intended role:
**clean-room executable scientific reference before any Taichi port**

Backend:
NumPy / f64

This line exists so that paper formulation, code and benchmark evidence can be
audited without production-specific physics or f32/GPU arithmetic confounds.

---

# 4. Literature lineage

## R1 — Leclaire et al. 2017 PRE — canonical baseline

DOI:
\`10.1103/PhysRevE.95.033306\`

Role:
**canonical formulation for L17_CORE**

Key elements taken from R1:

### Collision / equilibrium
- D3Q19 MRT;
- R1 Eq.(4) equilibrium, including:
  \[
  \nu\psi_i(\mathbf u\cdot\nabla\rho)
  \]
  and
  \[
  \nu\xi_i(\mathbf G:\mathbf c_i\mathbf c_i);
  \]
- harmonic kinematic-viscosity interpolation;
- \(\omega_{eff}=2/(6\nu+1)\).

### Interfacial perturbation
\[
\Delta N_i^{pert}
=
A|F|
\left[
W_i\frac{(F\cdot c_i)^2}{|F|^2}-B_i
\right]
\]

with

\[
\boxed{
A=\frac94\omega_{eff}\sigma
}
\]

The perturbation is applied **after** collision and is **unrelaxed**.

### Recoloring
R1 Eqs.(19)-(20):
- recolor the post-perturbation colour-blind distribution;
- explicit \(\beta\);
- component-conserving colour split.

### Wetting
R1 Eqs.(30)-(38):
- modify colour-gradient orientation at wall sites;
- secant construction, \(\lambda=1/2\), stop at \(n=2\);
- smooth binary solid image three times;
- R1 defines:
  \[
  \boxed{
  \mathbf n_w=\nabla g^{(3)}
  }
  \]
  with \(g=1\) in solid and \(g=0\) in fluid.

Therefore R1's \(\mathbf n_w\) points **fluid -> solid**.

### Wall-adjacent gradient
R1 numerical setup:
- isotropic gradient in bulk;
- standard Cartesian one-dimensional forward/backward/centred differences at
  \(X_W\).

### Open boundaries
R1 Eqs.(21)-(29) regularized density/velocity boundaries are part of the paper,
but are **not yet implemented in L17_CORE**.

This is an explicit scope exclusion, not an accidental omission.

---

# 5. R2 — Leclaire et al. 2017 benchmark paper

DOI:
\`10.1142/S0129183117500851\`

Role:
**behavioural clarification / benchmark evidence, not a new baseline formulation**

Used for:
- D3Q15/D3Q19/D3Q27 CGM benchmark context;
- confirmation that recoloring \(\beta\) controls numerical interface thickness;
- clarification that CG interface thickness can be controlled independently of
  physical parameters;
- warning that periodic closure can conceal wetting-boundary defects by
  cancellation.

R2 does **not** replace R1 as the canonical L17 formulation.

---

# 6. R3 — Akai, Bijeljic & Blunt 2018

DOI:
\`10.1016/j.advwatres.2018.03.014\`

Role:
**later optional wetting-boundary variant**

Key difference from R1 wetting:

\`\`\`text
R1:
bulk colour gradient
 -> secant orientation correction

R3:
identify C_FB / C_SB
 -> extrapolate colour field onto solid-boundary sites
 -> reconstruct interface normal
 -> closed-form contact-angle rotation
\`\`\`

Project status:
- code path implemented as a separate, default-off option;
- not part of \`L17_CORE\`;
- not yet quantitatively validated sufficiently for a Leclaire-vs-Akai claim.

Do not call R3 an “improved default” until A/B evidence exists.

---

# 7. R4 — Parmigiani et al. 2019 porous-media application

DOI:
\`10.1155/2019/5176410\`

Role:
**later porous-media application/variant in the same research lineage**

Published differences include:
- D3Q15 application;
- forced porous-media flow;
- simplified/perfectly-nonwetting treatment for its specific application;
- additional recoloring-related mass-conservation handling described in that
  application.

Project status:
**not part of L17_CORE and not currently implemented as a canonical project
variant**

Do not import R4 behaviour into L17_CORE merely because it is later.

---

# 8. R5 — Leclaire et al. 2014 isotropic gradient support

DOI:
\`10.1007/s10915-013-9772-2\`

Role:
supporting source for the higher-order isotropic discrete-gradient family.

Current status:
**full table-to-D3Q19 mapping remains UNRESOLVED**

Important distinction:

- project L17 uses:
  \[
  F_\alpha=3\sum_iW_i c_{i\alpha}\psi(x+c_i)
  \]
- this D3Q19 operator has an independent second-/fourth-rank isotropy
  derivation;
- the project therefore does **not** require an unresolved R5 table mapping to
  justify the working D3Q19 stencil.

Do not state “R5 mapping CLOSED / exactly 3W_i” as a sourced fact until the table
mapping ambiguity is actually resolved.

---

# 9. Production CG vs L17_CORE — load-bearing differences

This is the science-level summary. Detailed algebra lives in
\`CURRENT_VS_LECLAIRE_MAP.md\`.

| module | production CG | L17_CORE | science status |
|---|---|---|---|
| lattice | D3Q19 | D3Q19 | same family |
| MRT basis / relaxation | project basis/assignment | R1 tables/assignment | different |
| density-gradient equilibrium terms | absent in production baseline | R1 Eq.(4) present | different |
| viscosity interpolation | project relaxation-rate blend | harmonic \(\nu\) | different |
| perturbation | injected into moment equilibrium and relaxed | distribution-space, post-collision, unrelaxed | different |
| sigma parameter | CapA calibration | \(A=(9/4)\omega\sigma\) | different parameterization |
| recoloring | min-amplitude pairwise | R1 Eq.(19)-(20) | different |
| explicit beta | no | yes | missing in production |
| wetting | fictitious wall colour | gradient-orientation BC | different |
| wall normal | not used | R1 \(\nabla g\) | L17-only |
| bounce-back | project half-way style | R1 full-way solid-node | different |
| reservoirs/membranes | yes | no in current L17 scope | production extension |
| T3/C1X/A2 | yes | no by default | project arithmetic extension |

Conclusion:

> The production solver is **not** “Leclaire with some engineering changes”.
> It is a distinct CG implementation that shares the same broad method family.

This is why future A/B work should replace one module at a time rather than
switch the whole production solver in one step.

---

# 10. Project-specific numerical extensions are not physical formulation changes

The following belong to the project implementation layer, not to the paper
formulation:

- T3;
- C1X;
- A2;
- reservoir masks;
- phase-selective membranes;
- per-node wall-colour maps;
- evidence/provenance harnesses;
- visualization/NPZ retention pipeline.

They may be scientifically necessary for a robust executable solver, but they
must remain separately labelled from paper equations.

---

# 11. Current project phase convention

The project physical mapping is fixed:

\`\`\`text
red  = electrolyte / liquid / wetting phase
blue = gas / non-wetting phase

psi = (rho_red-rho_blue)/rho
F = grad(psi) = gas -> liquid

contact angle = measured through liquid/red
g = 1 solid, 0 fluid
\`\`\`

Current science correction after Pass-4 review:

R1 defines:

\[
\boxed{
\mathbf n_w=+\frac{\nabla g}{|\nabla g|}
}
\]

which points fluid -> solid.

The Pass-4 frozen convention used \(-\nabla g\), and therefore implemented the
complementary liquid-side angle.

Status:

**Pass-4 wetting convention is rejected and must be corrected before the
reference line can close.**

The old \`WETTING_PHASE_CONVENTION.md\` is temporarily superseded on this one
point until it is corrected.

---

# 12. Current scientific validation state

Updated after pass-06 (`BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001`), frozen source `9773a439f9f994225ce6515bd9f755815aa2c5af`.
Machine-readable summary: `results/leclaire_cg/pass-06/SUMMARY.json`.

Verdicts: {'PASS': 8, 'FAIL_SOLVER': 3}

| scientific claim | status | current interpretation |
|---|---|---|
| R1 D3Q19 tables / MRT transcription | PASS | source-level checks |
| R1 Eq.(4) equilibrium | PASS | `psi_i (u . grad rho)`, the scalar form |
| Eq.(4) moving-state mass source | CLOSED | multi-percent wall-case mass creation eliminated |
| R1 `X_W` gradient | PASS | 1D Cartesian wall rule |
| explicit beta controls width | PASS in the positivity-valid range | beta 0.5-1.0 valid |
| R1 perturbation ordering | PASS | post-collision, unrelaxed |
| `A = (9/4) omega sigma` | PASS as formulation | not retuned anywhere |
| canonical wall normal | PASS | `n_w = +grad(g)/|grad(g)|` fluid->solid, and every machine-readable artifact now states it |
| phase / contact-angle convention | PASS | theta through liquid/red; `cos(theta_liquid) = -(z_c-z_w)/R` |
| sessile contact angle 60/90/120 | PASS | 65.19 / 95.70 / 129.40 deg, inside the 15 deg gate |
| slit Pc geometry | PASS | transverse walls, real contact lines |
| slit Pc sign and magnitude | PASS | +/zero/- across 60/90/120; ratios 1.025 and 1.078 |
| Jurin geometry and connectivity | PASS | reservoir, barrier, slit and lower channel verified as ONE fluid component with the entrance submerged |
| Jurin result | **FAIL_SOLVER** | rise ~1.0 lu against 8.0 theory; does not scale with 1/g, so the meniscus appears pinned rather than slowly equilibrating |
| mechanical sigma | PASS, premises closed | ratio 0.9999953, recomputable from the retained `N_i` |
| Laplace `1/R` linearity | PASS | high `R^2` |
| Laplace sigma scale | FAIL / unresolved | free-intercept ~1.13; per-radius 1.02-1.06; zero-intercept ~1.04 |
| f64 global conservation | PASS in tested cases | not transferable to Taichi/f32 without its own audit |
| asymmetric-wall global mass closure | PASS | wall-band attribution still unresolved |
| raw-field publication artifact | PASS | raw NPZ tracked; all 36 manifest paths verified |
| source/evidence one-SHA reproducibility | PASS | the frozen SHA produced the whole evidence run |
| Taichi/f32 Leclaire port | HOLD | reference model not yet closed |
| production promotion | HOLD | no module promoted |

The wetting reference line is now closed on convention, measurement and
geometry. It is **not** closed on the Jurin capillary-rise benchmark, which
fails on a geometry where Jurin's law finally applies.

# 13. Current accepted causal findings

These are useful scientific/debugging results and should remain visible.

## 13.1 Eq.(4) mass-source chain

Wrong implementation:

\[
\psi_i(c_i\cdot\nabla\rho)
\]

instead of:

\[
\psi_i(u\cdot\nabla\rho)
\]

broke the zeroth-moment equilibrium identity in moving density-gradient states.

Observed consequence:
multi-percent global mass creation in the asymmetric wall case.

After correction:
global component-mass excursions returned to f64 roundoff.

Status:
**strong causal diagnosis**

## 13.2 Wetting complement chain

Pass-4 used:
- liquid/red angle convention;
- \(F=gas\to liquid\);
- but \(\mathbf n_w=-\nabla g\).

R1 uses:
\[
\mathbf n_w=+\nabla g.
\]

The contact-angle instrument also used the complementary spherical-cap sign.

Observed signatures:
- droplet angle appeared to pass under the defective instrument;
- valid slit Pc had approximately correct magnitude but opposite sign;
- Jurin tube emptied rather than rose.

Status:
**one coherent convention error explains all three wetting observations**

---

# 14. Open scientific questions

## Q1 — wetting convention closure

Next action:
- use R1 \(+\nabla g\);
- keep theta through liquid/red;
- correct circle-fit geometry;
- rerun contact angle, slit Pc and Jurin without redesigning their current
  valid geometries unless a separate defect appears.

## Q2 — sigma calibration

Known:
- Laplace response is strongly linear in curvature;
- fitted sigma is ~12–13% high;
- \(A=(9/4)\omega\sigma\) is source-correct and must not be retuned.

Unknown:
- finite-radius contribution;
- pressure estimator contribution;
- discrete-gradient normalization contribution;
- mechanical-stress interpretation.

## Q3 — mechanical sigma

Current status:
exploratory.

Need:
- geometry satisfying derivation premises;
- recomputable retained stress/distribution data;
- clean bulk windows;
- explicit treatment of one vs two interfaces.

## Q4 — beta vs physical resolution

Current evidence only supports:
beta changes lattice interface width and has a positivity/stability window.

It does not yet calibrate the paper refinement exponent \(\eta\).

## Q5 — production vs L17 attribution

After the L17 reference closes, compare modules separately:

1. recoloring;
2. perturbation/surface-tension operator;
3. wetting;
4. viscosity interpolation;
5. bounce-back / wall treatment.

Do not switch all modules simultaneously if the goal is causal attribution.

---

# 15. Planned scientific progression

\`\`\`text
Stage S1
Close NumPy/f64 L17 reference
    |
    +-- correct R1 wall-normal convention
    +-- correct liquid-side angle instrument
    +-- rerun theta / Pc / Jurin
    +-- close raw artifact provenance
    +-- keep Laplace offset explicit
    |
Stage S2
Port verified L17 modules to Taichi/f32
    |
    +-- repeat conservation audit
    +-- repeat canonical validation
    |
Stage S3
Module-level production-vs-L17 A/B
    |
    +-- recoloring
    +-- perturbation
    +-- wetting
    +-- wall/bounce-back
    |
Stage S4
Return to battery-relevant porous geometry
    |
    +-- bilateral canonical geometry
    +-- graphite
    +-- separator
    +-- PCS/gap
\`\`\`

This ordering is intentional: porous-media discrepancies should not be used to
debug a still-ambiguous basic wetting formulation.

---

# 16. Document ownership / update rule

Every future scientific change must update this file if it changes any of:

- canonical equation;
- source paper attribution;
- phase/wetting convention;
- model-line membership;
- accepted validation status;
- unresolved scientific question;
- promotion boundary.

A normal bug fix that does not change scientific interpretation belongs only in
the evolution log.

A new validation run belongs primarily in the validation atlas.

A new reviewer finding belongs in \`.agent/evidence/**\`, and must update this
file only if it changes the accepted scientific state.

---

# 17. Current “one-sentence truth”

As of this revision:

> **The project has a validated-but-custom production CG solver and a separate
> NumPy/f64 Leclaire-2017 reference implementation whose bulk formulation is
> largely source-faithful; the remaining reference-model blockers are the
> Pass-4 wetting convention/instrument error, reproducible raw-artifact binding,
> and an unresolved ~12–13% Laplace sigma-scale offset. No Leclaire module is
> yet authorized for production promotion.**
