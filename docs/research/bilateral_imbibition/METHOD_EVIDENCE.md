# Bilateral Spontaneous Imbibition — Method Evidence

Task `ADS-BILATERAL-EVIDENCE-001`. Evidence acquisition only: no solver,
test, or geometry change was made or designed here. Every important
statement cites `E-XXX` items in `EVIDENCE_NOTES.md` (support types:
DIRECT = stated in a cited source or verified in this repository; INFERENCE
= reasoned synthesis, never attributed to a source). Sources resolve in
`SOURCE_INDEX.md`.

---

## 1. Scope and Current Proposed Problem

The intended future simulation is **closed-system bilateral spontaneous
imbibition** in a graphite-electrode / interface-gap / PCS / separator
stack: two finite liquid buffers wet a gas-filled pore space from opposite
x-ends; no external pressure gradient in the baseline; outer ends currently
expected to be closed solid / bounce-back, subject to later scientific
review. Non-wetting-phase pockets sealed between the two advancing fronts
are an expected outcome, not an accident.

This is a **different well-posed problem** from the existing workflow: the
shipped `OpenSystem` protocol prescribes ρ/ψ in two reservoirs, exchanges
both phases through semi-permeable membranes, and walks a capillary-pressure
ladder Pc = δ/3 — pressure control with phase escape. The planned baseline
instead fixes total mass inside closed walls — mass budget with phase
capture. [E-031, E-029]

Planning-context geometry notes (not validated in this task): separator and
Cu as unresolved hard solid / bounce-back; interface gap configurable,
target ≈ 5 / 10 / 20 µm; PCS optional. **PCS here means separator-coating
particles** (an annular/hollow-disk first representation, outer radius ≈
5 µm, inner ≈ 3 µm, coffee-ring-like) — it is **not** the existing
`run_pcs_cg3d.py` Pc–S ladder driver, and the two must never be conflated.
With the current graphite voxel size (0.128 µm) these sizes correspond to
≈ 39–156 lu (gap) and ≈ 39/23 lu (PCS radii) — arithmetic context only, not
a resolution endorsement.

## 2. Existing CG3D Capabilities Relevant to This Case

| Capability | Current implementation | Existing validation | Sufficient for new case? | Gap |
|---|---|---|---|---|
| Two-phase CG-MRT dynamics, D3Q19 | `ColorGradientSolver3D`; σ direct input; recolouring; f32 GPU | Laplace σ=1.012·CapA (R²=1.0000); Finney drainage knee; permeability vs S&A bound [E-010] | Yes, for hydrodynamics | None known at unit ratio |
| Wettability (static) | Per-node ψ_solid wall colour seen by `Compute_C`/recolouring [E-011] | Static θ registry; Level-B θ(−0.68)=30°±6° [E-010] | **No** | Dynamic (moving contact line) wetting unvalidated [E-011, E-012] |
| Dynamic capillary filling | — (never run) | — | No | Purpose-built LW/Jurin case required [E-001, E-002, E-014] |
| Trapped-gas statistics | `label_periodic` (6/18/26 + wrap merge); cluster CCDF in reports [E-025] | 3D graphite I–R S_nr=0.171, 32 clusters; 2D θ-monotone trends [E-024] | Partially | Bilateral/closed topology new; calibre declaration needed [E-025] |
| Mass/p sentinels | f64 `color_masses`, `total_mass`, reservoir fluxes; `region_stats` p=ρ/3 [E-020] | leak 1.4–1.8e-8 pv/step in graphite runs [E-020] | Yes, as instrumentation | Pocket-local (cluster-masked) sums not yet wired as a diagnostic [E-020] |
| Open-system pressure boundaries | Reservoirs + semi-permeable membranes + ladder (`OpenSystem`) [E-031] | Multi-indicator quasi-steady criteria; X2/X3 runs [E-031] | Not applicable | The closed baseline does not use it [E-031] |
| Closed outer walls (plain BB) | Standard `solid` bounce-back; used in probes | X1 probe E: stable 3000 steps on raw rough graphite [E-032] | Plausible | Only a short no-drive probe; not exercised under imbibition [E-032] |
| Weak-compressibility regime | Single shared ρ field; p=cs²ρ | Ladder traversed ρ 0.89–1.14 stably [E-017] | Conditional | Sealed-pocket Δρ of a few–10% expected; no validity threshold exists to cite [E-015, E-016, E-017] |

## 3. Q1 — Dynamic Wetting

### Evidence-supported conclusions

- A Lucas–Washburn-type benchmark **is appropriate** for this solver family:
  a 3D CG-MRT model was validated with the full two-viscosity dimensionless
  LW form (Eq. 60 of S-LECLAIRE-PRE; inlet = wetting + more viscous fluid;
  equal pressures at both tube ends), and the battery-filling literature
  uses LW wetting rates as its standard dynamic yardstick. [E-001, E-003]
- The form to compare is the **dimensionless front position l\*(t\*)** with
  viscosity-ratio and cos θc parameters (or, at CG3D's matched viscosities
  and unit ratio, the classical x²∝t scaling with a computable prefactor,
  since σ is a direct input). [E-001, E-010]
- The validation ladder in the precedent treats **Jurin (static) and
  Washburn (dynamic) as separate rungs**; CG3D currently has only the static
  rung. Static θ validation does **not** establish dynamic wetting accuracy.
  [E-002, E-012]
- Krüger 2017 cannot be cited for any of this: no LW benchmark, no dynamic
  contact-angle theory, no colour-gradient coverage in the book. [E-004]

### Important limitations

- Early-time effects (inertial/transient departure from x²∝t) are **not**
  treated in any local source; no local paper fits or excludes an early
  window. Early times must not be forced onto the asymptotic scaling; the
  fit window choice is a planner decision with no literature number behind
  it. [E-003]
- Contact-line pinning and spurious-current distortion of apparent angles
  are documented CG-family hazards (qualitative only). [E-006, E-005]
- CG3D's own artefact numbers are static-only; nothing is known about
  current peaks at moving fronts. [E-010, E-026]
- Verification cases should avoid periodic hiding of wetting-BC deficiencies
  (a CG benchmark survey warns that periodic validations can mask them).
  [E-007]
- The real graphite geometry cannot host a resolved LW test (throat p50 =
  1.73 lu < interface width 2.2 lu); the benchmark must be a synthetic
  resolved tube/slab. [E-013, E-014]
- Viscosity: shipped runs use matched ν=0.1 both phases; unequal
  viscosities are supported by the formulas but untested in this line. The
  planned case inherits the matched-viscosity compromise. [E-010, S-CG3D-ALGO §5]

### Candidate verification observables

Front position vs time (per side), t^0.5 fit window + R², wetting-rate
constant, Jurin height (static companion), umax/u_rms history, colour-mass
drift, dual-calibre saturation. [E-027 for the bundle; E-001, E-003 for the
core observables]

### What remains unresolved

Whether the **geometric wall-colour wetting mechanism** of this solver
reproduces LW with the already-calibrated ψ_solid ↔ θ mapping, or whether
dynamic advancing angles drift from the static registry — unanswerable
without the purpose-built test. [E-011, E-012, E-014]

## 4. Q2 — Closed Trapped Gas

### Evidence-supported conclusions

- A sealed pocket pressurises through the solver's isothermal EOS: extra
  pressure Δp appears as Δρ = 3Δp in the shared ρ field (p = cs²ρ), and LBM
  validity is framed as weak compressibility with O(Ma²) density deviation.
  [E-009]
- **No source, textbook or paper, provides a universal numeric threshold**
  for acceptable density variation; the repo's own ρ ±0.11 band and umax-cap
  0.12 are operational guardrails, not validity criteria. Any stop rule must
  be justified per-run. [E-015, E-021]
- The unit-density-ratio model represents the *mechanism* of compression
  (ρ rise + volume shrink) but not the *contrast* of a real gas: the pocket
  behaves as a second weakly-compressible liquid-like phase. [E-016, E-008]
- Expected order of pressurisation with shipped parameters: Δp ~ 2σcosθ/r
  gives Δρ of ~3% (r=10 lu) to ~10% (r=3 lu) — inside densities the solver
  has already traversed (0.89–1.14) in boundary-driven ladders, though
  never cavity-produced. [E-017]
- No application paper ever compresses trapped gas — all vent it — so there
  is no literature expectation for pocket pressure to compare against.
  [E-018, E-019]

### Important limitations

- The order estimate above is inference (geometry-dependent curvature); it
  sizes diagnostics, it does not bound the run. [E-017]
- One closed-system multiphase study exists locally (SC family, uniform
  drive) and never quantifies cavity pressure despite a compressible gas
  EOS. [E-019]

### Candidate diagnostics

Pocket-local (cluster-masked) ρ_mean and p=ρ/3; pocket volume vs time;
consistency check ρV vs time for the sealed cluster (mass conservation
inside the pocket); global colour-mass drift (leakage); interface-band
volume fraction near the pocket (finite-interface artefact indicator);
umax history (instability); Laplace consistency p_pocket − p_liquid vs
σ·curvature. Separation logic: physical compression = uniform ρ rise with
mass-conserving cluster; finite-interface artefact = volume change without
commensurate ρ rise; leakage = global colour-mass drift; instability =
ρ oscillation / umax divergence. [E-020, E-025, E-027; separation is
inference built on E-009 + E-020]

### What remains unresolved

At what point a run should be classified inconclusive rather than
interpreted: **no defensible universal threshold exists** — the run must
carry its own admissibility argument (e.g. diagnostics stationary, mass
drift below the project's measured leak floor ~2e-8 pv/step as a *reference
magnitude*, no divergence). [E-015, E-020, E-021]

## 5. Q3 — Opposing Front Collision

### Evidence-supported conclusions

- **No established benchmark exists for opposing-front collision in this
  corpus** (11 sources verified by keyword): no source simulates two wetting
  fronts advancing toward each other and isolating a non-wetting phase.
  [E-023]
- The one direct artefact statement: **diffuse CG interfaces facilitate
  coalescence** between bubbles/drops — the very mechanism that stabilises
  CG (finite ~2.2 lu interface) spuriously merges approaching interfaces.
  When the residual gas gap between two fronts approaches ~2 interface
  widths, the fronts are no longer individually resolved. [E-022, E-013]
- Known/plausible risks with local backing: recolouring lattice pinning and
  spurious-current peaks (no CG3D measurement exists for either under
  motion) [E-005, E-006, E-026]; colour-mass loss is monitorable with
  existing f64 sentinels (project leak floor 1.4–1.8e-8 pv/step; 2D CG line
  0/19 divergences) [E-020, E-024]; topology changes (snap-off) at
  under-resolved throats are the documented graphite caveat [E-013];
  cluster-identification ambiguity (connectivity, ψ>0 threshold, periodic
  wrap) is real and must be declared per statistic. [E-025]
- Trapping itself is established single-front behaviour of this solver
  family, with magnitudes (3D S_nr≈0.17; 2D θ-monotone 3.4%→10.3%) and
  cluster statistics. [E-024]

### Known numerical risks

artificial interface annihilation / premature merging [E-022]; excessive
interface diffusion at small gaps [E-022, E-013]; colour-mass loss [E-020];
lattice pinning [E-006]; spurious-current peaks (unmeasured) [E-026];
finite-interface overlap ~2×2.2 lu [E-013, E-022]; resolution-driven
topology change [E-013]; labelling ambiguity [E-025].

### Candidate verification observables

Front positions x₁(t), x₂(t) individually (LW-comparable until interaction
distance); gas-gap thickness vs time; cluster count/size CCDF vs time;
pocket ρ/p/volume vs time; min |ψ| along the collision plane (blend
monitor); colour-mass drift; collision-region velocity extrema. [E-027]

### What remains unresolved

Everything quantitative: no source gives a merge/annihilation distance, a
spurious-current peak scale at collision, or a mass-loss bound for this
configuration. The verification case must establish its own baselines.
[E-023, E-026]

## 6. Q4 — Finite Closed Reservoirs

### Evidence-supported conclusions

- The baseline is **defensible as a numerical representation of capillary
  uptake without imposed drive**, with caveats on three sides:
  1. Stability: plain closed bounce-back walls are the *stable* member of
     the X1 probe family on the raw rough graphite geometry (3000 steps,
     no drive) — the historical NaN trigger was reservoir/membrane forcing
     on rough surfaces, which the closed baseline does not need at its
     outer ends. [E-032]
  2. Wave artefacts: velocity/density boundaries reflect pressure waves;
     closed walls reflect too; non-reflecting BCs exist for single-phase but
     multiphase open BCs are an open research area — no artefact-free
     option exists, the choice is a physical statement. [E-028, E-033]
  3. Precedent: **no local source has ever run a finite closed liquid
     buffer**; the application standard is effectively-infinite open
     reservoirs + membranes (8 lu Wanner / 4 lu HLBM), and the vent/boundary
     design perturbs trapped gas by O(1) factors (open outlet halves it;
     edge-escape artefacts documented). [E-029, E-030]
- An open pressure boundary would answer a **materially different
  problem** (pressure-controlled Pc with phase escape — the existing
  `OpenSystem` ladder), not a variant of the closed one. [E-031, E-033]

### Reservoir-size sensitivity requirements

Minimum proposed: front dynamics and end-state observables invariant under
a ≥2× liquid-buffer thickness change (synthetic stack); monitoring of any
reflected-wave signature (ρ oscillations at the closed ends) during
imbibition onset. No numeric invariance tolerance is defensible from the
corpus. [E-034]

### What remains unresolved

Whether the outer ends should be closed at all (reserved decision, §9);
whether liquid-buffer depletion (meniscus entering the porous structure /
interfaces interacting with the outer walls) produces its own artefact
class — no precedent exists either way. [E-029, E-033]

## 7. Requirements That Are Strong Enough for a Future Contract

| ID | Requirement | Evidence IDs | Strict gate or diagnostic? |
|---|---|---|---|
| R1 | Dynamic-wetting verification must precede interpretation of imbibition dynamics: a purpose-built resolved tube/slab case with Jurin (static) + Lucas–Washburn (dynamic) rungs, solver settings identical to the target run | E-001, E-002, E-012, E-013, E-014 | Strict gate (run must exist and be reported); the pass criteria themselves follow the repo's existing regression style (e.g. θ band, σ band), not new numbers |
| R2 | Global colour-mass conservation must be monitored with the f64 sentinels every sampling interval; drift reported alongside every result | E-020, E-024 | Strict gate (monitoring mandatory); reference magnitude 1.4–1.8e-8 pv/step from shipped runs, not a new threshold |
| R3 | All cluster statistics must declare connectivity (6/18/26), ψ threshold, periodic-merge setting, and report both saturation calibres (continuous + binary) | E-025 | Strict gate (declaration, not values) |
| R4 | Pressure/density diagnostics use p = cs²ρ (p=ρ/3) per region, incl. pocket-local p once clusters exist | E-009, E-020 | Strict gate (diagnostics defined) |
| R5 | Operational stability caps (umax-cap 0.12, ρ band ±0.11) may be reused only labelled as operational guardrails of this project, never as literature validity thresholds | E-015, E-021 | Contract wording requirement |
| R6 | No hard numerical acceptance threshold may be cited for weak-compressibility validity, coalescence distance, or spurious-current peaks — such thresholds do not exist in the evidence base | E-015, E-022, E-023, E-026 | Contract wording requirement |

## 8. Candidate Diagnostics That Should NOT Yet Be Hard Gates

- Collision-region spurious-velocity peak magnitude (no CG3D measurement,
  no source number). [E-026]
- Minimum |ψ| / interface-blend metric along the collision plane (motivated
  by E-022, unmeasured anywhere).
- Pocket pressure vs Laplace-curvature consistency (definition sound; no
  expected tolerance). [E-009 + E-027]
- Reservoir/buffer-size invariance magnitude (sensitivity required, R-level
  TBD by planner; no tolerance number). [E-034]
- Early-time LW fit-window exclusion length (no source number). [E-003]
- Per-pocket gas-mass conservation (ρV) drift bound (machinery exists;
  bound undefined). [E-020]

## 9. Open Scientific Decisions Reserved for External Review

1. **Closed vs open outer ends.**
   - Question: are closed solid/BB outer walls the right baseline?
   - Evidence both ways: closed walls stable on this geometry and create the
     intended sealed-pocket physics [E-032, E-030]; all application
     precedent uses open reservoirs, and vent design changes trapping by
     O(1) factors [E-029, E-030]; open ends answer the existing
     pressure-ladder problem instead [E-031].
   - Consequences: determines whether Q2 compression physics exists in the
     baseline at all; changes driver/protocol requirements.
   - Can work proceed without resolving it? Yes — the verification cases
     (LW tube, collision case) are largely boundary-design-agnostic.
     [E-033]
2. **Is unit-ratio gas compression the intended physical claim?**
   - Question: is a liquid-like-compressibility gas pocket scientifically
     acceptable for the episode's purpose?
   - Evidence: mechanism representable, contrast not [E-016]; family limits
     documented [E-008]; no precedent either way [E-018, E-019].
   - Consequences: frames what conclusions the run can support (pressure/
     stability/morphology yes; real-gas volume compression no).
   - Can proceed? Yes, with the boundary declared up front. [E-016]
3. **Matched viscosity.** Real electrolyte/gas viscosity ratios are O(50+);
   solver supports unequal ν but the line never tested it. Consequence:
   dynamics (LW prefactor, Ca regime) carry a declared compromise; statics
   unaffected. Can proceed. [E-010, S-CG3D-ALGO §5]
4. **Interface-gap / PCS resolution policy.** Gap 5 µm ≈ 39 lu is resolved
   against the 2.2 lu interface, but the graphite interior stays
   under-resolved (throat p50 1.73 lu) — a mixed-resolution domain whose
   artefact budget must be stated. Geometry choices themselves are planner
   property (not validated here). [E-013]
5. **Whether interior semi-permeable membranes (liquid-buffer walls) are
   wanted between buffers and stack.** Any membrane/reservoir forcing on
   rough surfaces re-arms the X1 NaN mechanism unless the buffer rule is
   applied; plain BB avoids it. Feasibility-critical implementation
   decision. [E-032, S-CG3D-ALGO §10]

## 10. Recommended Next Planning Step

The evidence is now sufficient for an external planner to **specify the
verification ladder and its instrumentation** without further literature
work:

1. a resolved synthetic single-tube/slab case: Jurin + Lucas–Washburn rungs
   with the shipped θ/σ settings (R1), fixing the dynamic-wetting gap;
2. a resolved symmetric two-front collision case in a simple channel/slit
   (no porous medium): records the E-027 observable set, establishing the
   project's own baselines for merge distance, mass drift, and current
   peaks where literature provides none;
3. a buffer-size sensitivity protocol for the closed-baseline synthetic
   stack (E-034);
4. a declared decision list (§9) to be settled before the porous-stack run
   is designed.

What is *not* yet sufficient: any quantitative acceptance thresholds for
the collision case, compression validity, or buffer invariance — these must
be grown from the verification cases themselves, per R6. No implementation
was designed in this task.
