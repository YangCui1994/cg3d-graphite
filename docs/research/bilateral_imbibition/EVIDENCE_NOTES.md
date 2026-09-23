# Evidence Notes — Bilateral Spontaneous Imbibition (ADS-BILATERAL-EVIDENCE-001)

One principal claim per item. Support types: `DIRECT` (stated in the cited
source), `PARTIAL` (source supports part of the claim), `INFERENCE`
(synthesis by this task, never attributable to a source). Source IDs resolve
in `SOURCE_INDEX.md`. PDF page numbers are 1-based PDF pages.

---

## E-001 — Washburn's law is an established CG-MRT validation benchmark, with a two-viscosity dimensionless form

- **Question:** Q1
- **Claim:** A 3D colour-gradient LBM with MRT has been validated against Lucas–Washburn capillary filling using the full two-fluid form (both viscosities non-negligible), not only x²∝t; the analytical comparison used is a dimensionless interface position l* vs t* with the viscosity ratio μO/μI and cos θc as parameters (their Eq. 60), with pressure equal at both tube ends and the inlet fluid required to be the wetting and more viscous fluid.
- **Source ID:** S-LECLAIRE-PRE
- **Location:** pp. 4–5 (validation programme, "both fluid viscosities are non-negligible"), p. 9 (Sect. setup), p. 13 + Eq. (60), p. 14 (water/hexane ρI/ρO=1.5094, μI/μO=3.2277)
- **Support type:** DIRECT
- **Evidence summary:** The paper's own validation ladder is Jurin (static) → Washburn (dynamic) → 3D capillary waves → porous-media drainage/imbibition. The Washburn test fills a single cylindrical pore initially containing the outlet fluid.
- **Applicability to current CG3D:** Same model family (colour gradient, MRT, D3Q19). This is the strongest local precedent that a purpose-built single-tube LW test is the appropriate dynamic-wetting benchmark for this solver.
- **Limitations:** Their test used density/viscosity ratios of O(1–3); CG3D ships matched viscosities and unit density ratio, so the two-fluid prefactor is simpler here. Their wetting BC is a prescribed contact angle in the colour-gradient forcing; CG3D uses geometric wall colour (E-011).
- **Code reference:** —
- **Confidence:** HIGH

## E-002 — Static and dynamic wetting validations are separate ladder rungs (Jurin ≠ Washburn)

- **Question:** Q1
- **Claim:** The reference CG validation programme treats the static meniscus test (Jurin's law, incl. rotated geometry up to 50°) and the dynamic filling test (Washburn) as two distinct validations; passing one does not certify the other.
- **Source ID:** S-LECLAIRE-PRE
- **Location:** p. 5 ("validating our wetting boundary condition against (1) Jurin's law … and (2) Washburn's law"), pp. 9–13
- **Support type:** DIRECT
- **Evidence summary:** Both tests are listed and executed separately before porous-media runs.
- **Applicability to current CG3D:** CG3D currently has only the static rung (contact-angle registry, E-011). A dynamic rung is missing and, by this precedent, is required before spontaneous-imbibition dynamics are interpreted.
- **Limitations:** The source does not state that geometric wall-colour wetting (as opposed to prescribed-angle forcing) needs the same ladder; that transfer is an inference (E-014b).
- **Code reference:** `tests/levelb_contact_angle.py` (static only)
- **Confidence:** HIGH

## E-003 — Lucas–Washburn theory and wetting-rate constants are used in the battery-electrolyte-filling literature

- **Question:** Q1
- **Claim:** Battery filling studies use LW scaling as the quantitative dynamic yardstick: Wanner & Birke devote a theory section to it and report wetting rates k (mm/s^0.5) from both experiment and simulation (e.g. graphite k≈1.363 experimental vs ≈1.17 simulated); HLBM validates x∝√t with R²>0.97 and extracts θ and effective pore radius from the fit.
- **Source ID:** S-WANNER; S-HLBM
- **Location:** S-WANNER PDF pp. 4, 9–11; S-HLBM PDF pp. 15–16
- **Support type:** DIRECT
- **Evidence summary:** Both papers make LW the dynamic benchmark for electrolyte invasion into porous electrodes — the application closest to the planned case.
- **Applicability to current CG3D:** Supports choosing LW-type observables (front position vs t^0.5, wetting-rate constant) as the recorded quantities for any future dynamic validation.
- **Limitations:** Neither paper fits the *early-time* regime or states error bars on the exponent; Wanner's Ca (=3.8e-4) is a project-derived number, not quoted in the paper.
- **Code reference:** —
- **Confidence:** HIGH

## E-004 — Krüger 2017 contains no LW benchmark and no colour-gradient coverage

- **Question:** Q1, Q2
- **Claim:** The local textbook does not discuss Lucas–Washburn/capillary-filling benchmarks at all (zero full-text hits) and chapter 9 covers only Shan–Chen and free-energy models, not the colour-gradient family; it also contains no dynamic-contact-angle treatment (no Cox–Voinov–Hoffman, no hysteresis, "pinning" never occurs).
- **Source ID:** S-KRUGER
- **Location:** full-text keyword verification; pp. 348, 418–419 (other methods acknowledged but not reviewed); pp. 371–374 (contact angle as *equilibrium* material parameter)
- **Support type:** DIRECT
- **Evidence summary:** Establishes that the standard textbook cannot be cited for CG dynamic wetting; the evidence must come from CG-specific sources (E-001–E-003) instead.
- **Applicability to current CG3D:** Prevents over-claiming textbook support for the planned benchmark.
- **Limitations:** Absence evidence only, verified against the page-marked full text.
- **Code reference:** —
- **Confidence:** HIGH

## E-005 — Spurious currents: cause, magnitude, and coupling to surface tension and density ratio

- **Question:** Q1, Q3
- **Claim:** Spurious (micro-)currents arise from non-isotropic discretization of the surface-tension force; a documented SC example has culling below ~1e-3 lu/t; magnitude grows with surface tension; they cap free-energy density ratios at ~10 and are a principal reason multiphase models struggle at high density ratios.
- **Source ID:** S-KRUGER
- **Location:** pp. 403–407 (esp. Fig. 9.13 on p. 404), p. 370, p. 409
- **Support type:** DIRECT
- **Evidence summary:** The book attributes microcurrents to tangential force errors on a steady interface and reviews isotropy/forcing remedies.
- **Applicability to current CG3D:** CG3D's own measured artefact level is much lower on static droplets (E-010), but interface *motion* (front collision) is where current peaks matter and no CG3D measurement exists (E-026).
- **Limitations:** Book numbers are for SC/free-energy, not CG; transfer to CG magnitude is only by S-LECLAIRE-IJMPC's qualitative comparison.
- **Code reference:** —
- **Confidence:** HIGH (for the book's own statements)

## E-006 — Recolouring causes lattice pinning and spurious velocities can distort the equilibrium contact angle

- **Question:** Q1, Q3
- **Claim:** In multiphase LBM reviews, the colour-recolouring mechanism is identified as a source of lattice pinning of the contact line, and strong spurious velocities can distort the *equilibrium* contact angle a simulation settles to; conversely the diffuse interface regularises the contact line (no stress singularity).
- **Source ID:** S-LIU; S-ZAHID
- **Location:** S-LIU pp. 15–16 (pining/spurious distortion of equilibrium angle), p. 3; S-ZAHID pp. 9–10 ("lattice pinning" as historical CG defect)
- **Support type:** DIRECT
- **Evidence summary:** Two independent reviews flag pinning and spurious-current distortion of apparent wetting as CG-family hazards.
- **Applicability to current CG3D:** The CG3D θ-registry was measured on a resting droplet; pinning will matter when the contact line *moves* through pore throats, particularly at the planned geometry's under-resolved graphite side (E-013).
- **Limitations:** Neither review quantifies pinning thresholds; no CG-specific number.
- **Code reference:** —
- **Confidence:** HIGH (qualitative)

## E-007 — Periodic boundaries can hide wetting-BC deficiencies

- **Question:** Q1, Q4
- **Claim:** A CG benchmark survey notes that validations performed with periodic boundaries can mask deficiencies of the wetting boundary condition.
- **Source ID:** S-LECLAIRE-IJMPC
- **Location:** p. 6 (survey discussion of wetting BC validation practice)
- **Support type:** DIRECT
- **Evidence summary:** One-sentence but explicit methodological caution from a CG benchmark paper.
- **Applicability to current CG3D:** The CG3D contact-angle registry uses walls + droplet (not periodic) so it is not directly implicated, but any future verification case should avoid periodic hiding of wetting defects.
- **Limitations:** Statement is about validation practice, not a measured artefact.
- **Code reference:** —
- **Confidence:** MEDIUM (single-sentence source statement, not replicated elsewhere locally)

## E-008 — CG practical density-ratio limits: ~20 dynamic, higher static

- **Question:** Q2
- **Claim:** For colour-gradient models, density ratios above ≈20 are reported as impractical in complex setups (very small time steps); ratios ~10³ are achievable only in static tests across multiphase LBM generally, while dynamic problems are limited to O(10); the original CG work demonstrated 10:1 dynamically and ≈200 statically.
- **Source ID:** S-LECLAIRE-PRE; S-LIU; S-GRUNAU
- **Location:** S-LECLAIRE-PRE p. 4; S-LIU p. 10; S-GRUNAU pp. 10–11
- **Support type:** DIRECT
- **Evidence summary:** Consistent multi-source picture: the model family sits at low density ratios, especially under motion.
- **Applicability to current CG3D:** CG3D runs at ratio exactly 1 (matched phases, E-020). The literature therefore supports it as safely inside the family's demonstrated envelope — and equally implies the model cannot represent a real gas/liquid compression contrast (both phases share the same EOS).
- **Limitations:** None material for this use.
- **Code reference:** `lbm_solver_cg3d.py` constructor (single `niu_l/niu_g`, single ρ field)
- **Confidence:** HIGH

## E-009 — p = cs²ρ and the weak-compressibility / Ma² framing

- **Question:** Q2
- **Claim:** LBM's isothermal equation of state p = cs²ρ is central to the method, and LBM is valid only for weakly compressible phenomena (u ≪ cs, Ma² ≪ 1); compressibility error is O(Ma²), steady-state density deviations are δρ/ρ₀ = O(Ma²), and the setup rule given is "keep local δρ small compared to ρ₀".
- **Source ID:** S-KRUGER
- **Location:** p. 32 (EOS central, Exercise 1.4), p. 131 (weak compressibility), pp. 164–165 (O(Ma²) error), p. 313 (setup rule), p. 533 (δρ/ρ₀ = O(Ma²))
- **Support type:** DIRECT
- **Evidence summary:** The textbook's compressibility framing, used by the diagnostics of this repo (p=ρ/3, E-021).
- **Applicability to current CG3D:** A sealed gas pocket compressed by capillary pressure Δp must appear as Δρ = Δp/cs² = 3Δp in the solver's single ρ field. Weak-compressibility validity then demands 3Δp ≪ ρ₀·(Ma²-ish budget) — but the sources give **no universal numeric threshold** (E-016).
- **Limitations:** The book states orders, not pass/fail numbers.
- **Code reference:** `cg3d/diagnostics.py::region_stats` (p = ρ/3)
- **Confidence:** HIGH

## E-010 — CG3D's measured artefact level on static droplets; interface width 2.2 lu

- **Question:** Q1, Q3
- **Claim:** The current CG3D reports interface width ≈2.2 lu with recolouring anisotropy <0.1% on static droplets, Laplace σ = 1.012·CapA (13-droplet fit, R²=1.0000), and a static contact-angle registry (ψ_solid=−0.68 → θ_liq≈30°±6°); both are Level-B regressions in this repo.
- **Source ID:** S-CG3D-ALGO; S-CG3D-TESTS
- **Location:** ALGORITHM §1, §4, §6, §11; `tests/levelb_laplace.py` (acceptance: within 3% of 1.012·CapA, R²≥0.999); `tests/levelb_contact_angle.py` (30°±6°)
- **Support type:** DIRECT (verified in current repository)
- **Evidence summary:** Static surface tension and static wetting are validated and regression-locked at the execution base.
- **Applicability to current CG3D:** Establishes the "static baseline" the future dynamic case starts from; σ is a known direct input, so LW predictions are computable a priori.
- **Limitations:** All static; says nothing about moving contact lines, pinning, or front collision.
- **Code reference:** `tests/levelb_laplace.py`, `tests/levelb_contact_angle.py`, `lbm_solver_cg3d.py::Compute_C` / recolouring loop
- **Confidence:** HIGH

## E-011 — Wall-colour wetting in CG3D is geometric (recolouring-level), calibrated only statically

- **Question:** Q1
- **Claim:** Wettability enters through a per-node ψ_solid "wall colour" that the colour-gradient and recolouring steps see at solid faces; there is no separate contact-angle forcing term, and the only calibration/validation of it is the static droplet registry.
- **Source ID:** S-CG3D-SOLVER; S-CG3D-ALGO
- **Location:** `Compute_C` (solid neighbours contribute ψ_solid to the gradient), `set_psi_solid*`; ALGORITHM §6
- **Support type:** DIRECT (verified in current repository)
- **Evidence summary:** The wetting mechanism differs from Leclaire's prescribed-angle wetting forcing; its dynamic behaviour (advancing contact angle under motion) is unvalidated.
- **Applicability to current CG3D:** Any dynamic-wetting claim must first pass a purpose-built LW/Jurin-type test with this specific mechanism (E-002 precedent), not just the existing registry.
- **Limitations:** None.
- **Code reference:** `lbm_solver_cg3d.py::Compute_C`, `set_psi_solid_field`
- **Confidence:** HIGH

## E-012 — Static contact-angle validation does not establish dynamic wetting accuracy

- **Question:** Q1
- **Claim:** Validating an equilibrium contact angle does not certify the dynamics of a moving contact line; the field's own validation practice treats them as separate tests, and reviews warn that spurious velocities and pinning specifically affect moving/advancing contact lines.
- **Source ID:** synthesis of S-KRUGER (E-004: angle is an equilibrium parameter; no dynamic treatment), S-LECLAIRE-PRE (E-002: separate Jurin and Washburn rungs), S-LIU (E-006: pinning/spurious distortion)
- **Location:** see E-002/E-004/E-006
- **Support type:** INFERENCE
- **Evidence summary:** No single source states the sentence verbatim; it follows from the field's separation of static/dynamic rungs plus the identified moving-contact-line hazards.
- **Applicability to current CG3D:** Core motivation for adding a dynamic rung before interpreting bilateral imbibition dynamics.
- **Limitations:** Inference, not a source statement; a planner may weigh it differently, but the underlying three facts are DIRECT.
- **Code reference:** —
- **Confidence:** MEDIUM-HIGH

## E-013 — Real-graphite side of the planned geometry is under-resolved for interface physics

- **Question:** Q1, Q3, Q4
- **Claim:** In the shipped graphite geometry, throat p50 = 1.73 lu < interface width 2.2 lu; fine pores are hydraulic dead zones; without a control arm, curve anomalies cannot be attributed to physics vs under-resolution. In the 2D CG line (by contrast) throats were 11.3–18.0 lu, i.e. resolved.
- **Source ID:** S-CG3D-RESULTS (§6 item 2); S-NOTES-2DCG (§2 table)
- **Location:** RESULTS.md §6; 2D report §2
- **Support type:** DIRECT (both are project-verified measurements)
- **Evidence summary:** The graphite subcrop is deliberately run under-resolved; the 2D evidence line was resolved.
- **Applicability to current CG3D:** Any purpose-built verification case (tube, gap channel) must be resolved (throat/gap ≫ 2.2 lu) or it reproduces this same caveat; bilateral collision inside the real graphite remains exploratory-grade.
- **Limitations:** Numbers refer to the 200³ subcrop; other crops differ.
- **Code reference:** `docs/RESULTS.md` §6
- **Confidence:** HIGH

## E-014 — An LW-type benchmark for CG3D must be purpose-built and resolved (not extracted from the real geometry)

- **Question:** Q1
- **Claim:** Since the real graphite geometry cannot host a resolved capillary tube (E-013) and CG3D's wetting is unvalidated dynamically (E-011), the appropriate benchmark is a synthetic resolved tube/slab run with the same solver settings, following the Leclaire ladder (Jurin → Washburn).
- **Source ID:** synthesis of E-001, E-002, E-011, E-013
- **Location:** —
- **Support type:** INFERENCE
- **Evidence summary:** Design consequence of the DIRECT items above; no additional source needed.
- **Applicability to current CG3D:** Defines the minimum first verification case for the future episode.
- **Limitations:** Geometry/parameters of the test are planner decisions (not designed here).
- **Code reference:** —
- **Confidence:** MEDIUM-HIGH

## E-015 — No defensible universal numeric threshold for "acceptable" density variation exists in the local sources

- **Question:** Q2
- **Claim:** Neither Krüger 2017 nor any local CG source states a universal pass/fail density-variation or Mach threshold for weak-compressibility validity; the textbook gives only order statements (O(Ma²), δρ small vs ρ₀), and repo documents carry *operational* bands (ρ within ±0.11 in shipped ladders; umax-cap 0.12) that are run-design guardrails, not literature thresholds.
- **Source ID:** S-KRUGER; S-CG3D-BCIC
- **Location:** S-KRUGER pp. 131, 164–165, 313, 533 (orders only); BC_IC_OUTPUT §4 (±0.11, umax 0.12)
- **Support type:** DIRECT (absence of threshold; presence of operational bands)
- **Evidence summary:** The task's instruction "do not invent a universal threshold" is confirmed as the correct evidence posture.
- **Applicability to current CG3D:** Any future "stop rule" for sealed-pocket compression must be justified case-by-case (e.g. divergence of diagnostics), not cited to literature.
- **Limitations:** Absence in local corpus ≠ absence in the wider literature (not searched; out of scope offline).
- **Code reference:** `docs/BC_IC_OUTPUT.md` §4
- **Confidence:** HIGH (for the local corpus)

## E-016 — Sealed-pocket compression in CG3D is mechanically representable but physically idealised

- **Question:** Q2
- **Claim:** In this solver, a sealed gas pocket under extra pressure Δp responds by Δρ = 3Δp in the shared ρ field (p = cs²ρ, unit ratio), i.e. the pocket behaves as an isothermal weakly-compressible *liquid-like* gas; real gas (ω≈1.0 for air) would compress far more at the same Δp. The compression mechanism exists; the compressibility contrast does not.
- **Source ID:** synthesis of S-CG3D-SOLVER (E-020 single EOS), S-KRUGER (E-009), S-GRUNAU/S-LIU/S-LECLAIRE-PRE (E-008 family limits)
- **Location:** —
- **Support type:** INFERENCE
- **Evidence summary:** Numerical-mechanism statement (Δρ=3Δp is arithmetic from the code); the physical-idealisation judgement is inference from the unit-ratio model plus the family's documented ratio limits.
- **Applicability to current CG3D:** Sets the honest boundary: the future run can answer "what pressure does the pocket reach and does it stay stable", not "how much does real gas compress".
- **Limitations:** Must not be presented as a source statement; the planner should confirm the desired physical claim before the episode is designed.
- **Code reference:** `lbm_solver_cg3d.py` (ρ field shared by both colours; `streaming3` ρ=Σf)
- **Confidence:** MEDIUM-HIGH

## E-017 — Expected magnitude of pocket pressurisation in the planned case (order estimate)

- **Question:** Q2
- **Claim:** With shipped parameters (σ≈0.0606, θ≈30°) and a pocket bounded by menisci of radius r, Laplace pressurisation Δp ~ σ(2cosθ)/r in lattice units gives, e.g., r=3 lu → Δp≈0.035 → Δρ≈0.10 (≈10% of ρ₀); r=10 lu → Δρ≈0.03. Pocket densities of the same order were already traversed by the existing open ladder (ρ 0.89–1.14) without instability.
- **Source ID:** synthesis (Laplace law from E-010 σ; capillary geometry arithmetic; ladder ρ range from S-CG3D-SOLVER docstring / BCIC)
- **Location:** —
- **Support type:** INFERENCE
- **Evidence summary:** Back-of-envelope scaling only, to size the diagnostic range. The r↔Δp mapping depends on actual meniscus curvature, which the simulation itself determines.
- **Applicability to current CG3D:** Indicates Δρ of a few % to ~10% — outside the small-δρ comfort framing of E-009 but inside densities the solver has already survived; exactly the regime where diagnostics (E-021) must decide admissibility run-by-run.
- **Limitations:** Estimate, not evidence; the ladder's ρ range was boundary-prescribed, not cavity-produced.
- **Code reference:** `lbm_solver_cg3d.py` module docstring (ρ_res 1.30–1.38 note), `Compute_C` comment (ρ_out=0.89 at d=0.22)
- **Confidence:** MEDIUM

## E-018 — Trapped-gas end states in battery filling are always vented, never compressed

- **Question:** Q2
- **Claim:** All local battery-filling papers route displaced gas to an outlet (gas reservoir or open boundary): Wanner reports final entrapments 7.3% (graphite), 5.84% (+arrester), 11.3% (separator), 10.1% (combined); HLBM reports S1,final < 100% with gas exiting via outlet reservoir and an explicit "incompressible" assumption; Shodiev reports air trapped in dead-end/isolated pores that never fills; none discusses gas compressibility or cavity pressure.
- **Source ID:** S-WANNER; S-HLBM; S-SHODIEV
- **Location:** S-WANNER PDF pp. 10–11; S-HLBM PDF pp. 23–24, 43; S-SHODIEV pp. 18–30
- **Support type:** DIRECT
- **Evidence summary:** The application literature offers trapped-gas *magnitudes* (valuable for expectations) but zero precedent for the planned closed compression physics.
- **Applicability to current CG3D:** Expected trapped-gas saturation band (≈5–11% at θ≈30–90°, cf. also E-024) and the confirmation that the closed baseline is a deliberately new physical statement.
- **Limitations:** Entrapment numbers are model-/geometry-specific.
- **Code reference:** —
- **Confidence:** HIGH

## E-019 — Trapped-gas morphology is path- and position-dependent (closest closed-system study)

- **Question:** Q2, Q3
- **Claim:** In the one local closed-domain imbibition/drainage study (SC, fully periodic, uniform density-rate drive), gas cluster morphology differs strongly by path: drainage clusters congregate at grain surfaces with suction jumps at pore openings, imbibition clusters disperse with uniform suction drops, and entrapped gas in dead-end pores measurably lowers suction; the gas EOS is compressible (Carnahan–Starling MCMP) but cavity pressure is never quantified.
- **Source ID:** S-WANG
- **Location:** pp. 1–2, 5, 7–10
- **Support type:** DIRECT
- **Evidence summary:** Documents that a closed, gas-retaining protocol is numerically feasible in a multiphase LBM (different family), and that trapped-phase distribution — not just amount — is an outcome worth recording.
- **Applicability to current CG3D:** Supports recording cluster size/shape distributions (CCDF) as first-class observables; also shows the drive protocol (uniform vs boundary-localised) shapes the result.
- **Limitations:** Shan–Chen family, uniform drive, soil geometry — transfer to CG + bilateral fronts is qualitative.
- **Code reference:** —
- **Confidence:** MEDIUM (for transfer; HIGH for its own statements)

## E-020 — CG3D colour/mass accounting machinery already exists

- **Question:** Q2, Q3
- **Claim:** The solver exposes f64 colour-mass sentinels (`color_masses`, `total_mass`, reservoir flux counters), and the shipped graphite runs measured membrane leak ≈1.4–1.8e-8 pore-volumes/step; in the closed baseline (no membranes/reservoirs) the same sentinels measure global mass conservation directly, and region-wise ρ/ψ/v statistics exist (`region_stats`).
- **Source ID:** S-CG3D-SOLVER; S-CG3D-DIAG; S-CG3D-RESULTS (§2–3 leak numbers)
- **Location:** `color_masses`, `reservoir_fluxes`, `apply_reservoirs` counters; `region_stats`
- **Support type:** DIRECT (verified in current repository)
- **Evidence summary:** The instrumentation needed to separate "physical compression" from "mass leakage" is present at the execution base.
- **Applicability to current CG3D:** Per-pocket diagnostics (gas mass inside a labelled cluster) are a small post-processing extension of existing label+snapshot machinery — but that is implementation talk for the planner, not a change made here.
- **Limitations:** Sentinels are global; pocket-local mass needs cluster-masked sums (exists conceptually via `label_periodic` + ψ>0 mask).
- **Code reference:** `lbm_solver_cg3d.py::color_masses`, `cg3d/diagnostics.py`
- **Confidence:** HIGH

## E-021 — Existing operational guardrails (umax-cap, ρ band) are run-design values, not physics thresholds

- **Question:** Q2, Q3
- **Claim:** The shipped drivers cap umax at 0.12 (≈ Ma 0.21 in this normalisation, u·√3) and expect ρ within ±0.11; these are operational stability guardrails of this project's runs, chosen by experience, without literature warrant as validity thresholds.
- **Source ID:** S-CG3D-BCIC
- **Location:** §4 (数值参数速查)
- **Support type:** DIRECT (project-documented), with the classification "operational, not scientific" being this task's reading
- **Evidence summary:** Available as pragmatic stop-rule candidates, provided they are labelled as such.
- **Applicability to current CG3D:** A future closed-system run can reuse them as *declared operational* bounds; anything stricter needs its own justification.
- **Limitations:** None.
- **Code reference:** `run_pcs_cg3d.py` / `run_ir_cg3d.py` argparse (as documented in BC_IC_OUTPUT §4)
- **Confidence:** HIGH

## E-022 — Diffuse CG interfaces facilitate coalescence (direct source statement)

- **Question:** Q3
- **Claim:** "Larger diffuse interfaces increase numerical stability and decrease the magnitude of spurious currents. However, diffuse interfaces facilitate coalescence between modeled bubbles/drops. Consequently thinner interfaces may be desirable … for applications that involve the interaction between many bubbles/drops." (paraphrase of Appendix A; exact wording verified.)
- **Source ID:** S-LECLAIRE-IJMPC
- **Location:** p. 26, Appendix A
- **Support type:** DIRECT
- **Evidence summary:** The single most on-point local statement about interface-interaction artefacts in CG models: the mechanism that keeps CG3D stable (finite ~2.2 lu interface) is also the mechanism that can spuriously merge/annihilate two approaching interfaces.
- **Applicability to current CG3D:** In the planned collision, when the residual gas gap between the two fronts approaches ~2 interface widths, the fronts are no longer individually resolved and may artificially merge or annihilate; this must be monitored (E-027).
- **Limitations:** Qualitative; no distance/magnitude criterion given.
- **Code reference:** —
- **Confidence:** HIGH

## E-023 — No local source studies opposing-front collision; no established benchmark exists in this corpus

- **Question:** Q3
- **Claim:** Across all 11 literature sources, no simulation of two wetting fronts advancing toward one another and isolating a non-wetting phase was found; the nearest partial analogues are (i) blob trapping behind a single advancing front in a 2D pore network (S-LIU p. 34), (ii) mid-stack inlet wetting both electrodes outward with diverging fronts and an open outlet (S-JEON), (iii) coalescence remark (E-022).
- **Source ID:** all sources (verified absence); S-LIU; S-JEON
- **Location:** keyword verification across corpus; S-LIU p. 34; S-JEON index §3–4
- **Support type:** DIRECT (absence)
- **Evidence summary:** The planned collision case has no off-the-shelf benchmark; a purpose-built verification case with its own observables is required.
- **Applicability to current CG3D:** The future episode's collision validation will be internally defined; claiming literature precedent for it would be wrong.
- **Limitations:** Corpus is local-only; wider literature not searched (offline scope).
- **Code reference:** —
- **Confidence:** HIGH (for this corpus)

## E-024 — CG imbibition trapping already measured in this project family (2D and 3D)

- **Question:** Q3
- **Claim:** The project has prior CG trapped-gas measurements: 3D graphite open-system I–R gives S_nr = 0.171 with 32 clusters, largest ganglion 66.7% of trapped gas (12% of pore volume), inside the Finney validation band (0.16–0.20); 2D CG imbibition (θ=30/60/90°, 3 seeds) gives monotone θ→trapped trends with CG 3.40% at θ=30° and 10.31% at 90°, and the 2D open-outlet arm halves trapped gas vs a gas-only membrane (−46% to −70%).
- **Source ID:** S-CG3D-RESULTS (§4); S-NOTES-2DCG (§1, §6)
- **Location:** RESULTS.md §4; 2D report §1 items 1/4/6, §6
- **Support type:** DIRECT (project-verified runs)
- **Evidence summary:** Trapping under *single-front* imbibition is established behaviour of this solver family, including its magnitude and cluster statistics; the vent-path effect is first-order.
- **Applicability to current CG3D:** Baseline expectations and an existing analysis pipeline (cluster CCDF, dual-calibre saturation) for the bilateral case; also direct evidence that boundary/vent design changes trapping by O(1) factors (feeds Q4).
- **Limitations:** All single-front, open-system; none bilateral or closed.
- **Code reference:** `docs/RESULTS.md` §4; parent-project note (outside repo)
- **Confidence:** HIGH

## E-025 — Cluster identification has known ambiguities already documented in this repo

- **Question:** Q3
- **Claim:** Cluster labelling depends on connectivity (6/18/26) and on the ψ>0 threshold; periodic wrap merging is mandatory in this solver (y/z periodic) or clusters are split; and the continuous vs binary saturation calibres differ by the interface-volume fraction, which the repo already treats as a resolution diagnostic.
- **Source ID:** S-CG3D-DIAG; S-CG3D-BCIC
- **Location:** `label_periodic` docstring; BC_IC_OUTPUT §3.2
- **Support type:** DIRECT (verified in current repository)
- **Evidence summary:** The ambiguity list the task asks about (cluster identification ambiguity) is real and already partially handled.
- **Applicability to current CG3D:** The bilateral case must declare conn + threshold + periodicity in every reported cluster statistic; the two-calibre saturation pair should be reported.
- **Limitations:** Interface-band nodes belong to neither pure phase; no canonical assignment exists.
- **Code reference:** `cg3d/diagnostics.py::label_periodic`, `eval_convergence`
- **Confidence:** HIGH

## E-026 — No CG3D spurious-current measurement exists for moving fronts or collision regions

- **Question:** Q1, Q3
- **Claim:** The repo's artefact measurements (anisotropy <0.1%, static droplets) are static; no measurement of spurious-current peaks during front advance or at interface-interface approach exists at the execution base.
- **Source ID:** S-CG3D-ALGO (§1 static measurements only)
- **Location:** §1, §4
- **Support type:** DIRECT (absence in repo docs; verified)
- **Evidence summary:** A candidate diagnostic gap: umax/u_rms tracking exists in drivers, but no collision-specific current analysis.
- **Applicability to current CG3D:** The future verification case should record velocity-field statistics localised to the collision region (proposed diagnostic, not a gate).
- **Limitations:** —
- **Code reference:** `cg3d/protocol.py::measure` (umax, u_rms global only)
- **Confidence:** HIGH

## E-027 — Collision-specific observables to record (proposed)

- **Question:** Q3
- **Claim:** The quantities a purpose-built collision verification case should record are: individual front positions x₁(t), x₂(t) (LW-comparable until interaction distance); residual gas-gap thickness vs time; gas-cluster count/size CCDF vs time; pocket ρ/p and volume vs time; minimum |ψ| along the collision plane (interface-blend monitor); colour-mass drift; and velocity extrema in the collision region.
- **Source ID:** synthesis of E-001 (front-position observable), E-019 (cluster morphology), E-020 (mass/p sentinels), E-022 (blend monitor motivated), E-025 (labelling calibres), E-026 (local currents)
- **Location:** —
- **Support type:** INFERENCE / PROPOSED DIAGNOSTIC
- **Evidence summary:** Each observable traces to a DIRECT item; the bundle is this task's proposal.
- **Applicability to current CG3D:** All are computable from existing snapshot+label machinery.
- **Limitations:** Explicitly not thresholds; no pass/fail values are proposed.
- **Code reference:** —
- **Confidence:** MEDIUM (as a proposal)

## E-028 — Velocity/density boundaries reflect pressure waves; multiphase open BCs are an open research area

- **Question:** Q4
- **Claim:** In LBM, enforcing velocity or density at boundaries reflects sound waves back into the domain (LBM solves compressible NSE; non-reflecting/absorbing BCs exist as a remedy); and open boundary conditions for *multiphase* flows "have not yet been thoroughly investigated", with pressure BCs particularly hard (risk of artificial condensation/evaporation).
- **Source ID:** S-KRUGER
- **Location:** pp. 21–22 (FAQ), p. 219 (§5.3.5), p. 507 + §12.4 p. 533 (non-reflecting), p. 411 (multiphase open BCs)
- **Support type:** DIRECT
- **Evidence summary:** Textbook-level warning that any boundary choice (closed walls reflecting, or prescribed ρ/ψ reservoirs) has wave artefacts; the multiphase-open direction is explicitly immature.
- **Applicability to current CG3D:** Both candidate outer-end designs (closed BB walls vs open reservoirs) carry artefact classes; neither is artefact-free, so the choice is a physical-statement decision (E-033), and wave-reflection diagnostics belong in the run.
- **Limitations:** Book is single-phase-scoped for the reflection mechanics; transfer to two-phase is by analogy.
- **Code reference:** —
- **Confidence:** HIGH (statements), MEDIUM (transfer to two-phase)

## E-029 — Battery-filling BC designs are open, effectively-infinite supply systems

- **Question:** Q4
- **Claim:** Wanner & Birke: 8-lu reservoirs at both ends with 1-lu semi-permeable membranes (inlet electrolyte-pass, outlet gas-pass), x-periodic; HLBM: 4-lu density-prescribed reservoirs both ends + membranes, x/z periodic, saturation counted only between membranes; both step inlet density/force — an effectively infinite supply, never a finite buffer; neither discusses buffer exhaustion.
- **Source ID:** S-WANNER; S-HLBM
- **Location:** S-WANNER PDF p. 7 (+p. 10 artefact admission); S-HLBM PDF pp. 22–23
- **Support type:** DIRECT
- **Evidence summary:** The application literature's standard answer to the supply problem is "open reservoir + membrane", not "finite closed buffer".
- **Applicability to current CG3D:** The current CG3D `OpenSystem` protocol is the same design (E-031); the planned finite closed buffer is outside every local precedent.
- **Limitations:** —
- **Code reference:** `cg3d/protocol.py::OpenSystem`
- **Confidence:** HIGH

## E-030 — Boundary design measurably changes trapped gas (open vs vent, periodic escape)

- **Question:** Q4
- **Claim:** Two independent project/literature results: (i) 2D CG — fully open outlet halves trapped gas relative to a gas-only membrane (−46% to −70% across θ); (ii) Wanner — at ≥24 kPa, edge-adjacent gas escapes through non-periodic walls while fully enclosed gas cannot, an explicit boundary artefact on the trapped inventory; and the x-periodic BC "may have some impact".
- **Source ID:** S-NOTES-2DCG (§6); S-WANNER (PDF pp. 7, 10)
- **Location:** as cited
- **Support type:** DIRECT
- **Evidence summary:** Vent-path and boundary-topology choices perturb trapped-gas outcomes by O(1) factors — the same order as wettability itself.
- **Applicability to current CG3D:** The closed-outer-wall choice of the planned baseline is therefore physically consequential (it *creates* the sealed-pocket physics) and must be justified as a physical statement, not convenience.
- **Limitations:** Magnitudes from 2D/literature geometries, not the planned 3D stack.
- **Code reference:** —
- **Confidence:** HIGH

## E-031 — The current open-system protocol differs physically from the planned closed baseline

- **Question:** Q4
- **Claim:** The shipped workflow (`OpenSystem` + pressure ladder) prescribes ρ/ψ in both reservoirs, exchanges both phases through semi-permeable membranes, and drives Pc = δ/3; the planned baseline instead fixes total mass inside closed outer walls with no imposed pressure difference — a different well-posed problem (mass budget vs pressure control), not a parameter change.
- **Source ID:** S-CG3D-PROTOCOL; S-CG3D-ALGO (§8)
- **Location:** `OpenSystem`, `set_ladder`, `run_hold`; ALGORITHM §8
- **Support type:** DIRECT (verified in current repository)
- **Evidence summary:** Confirms the task premise: the new case is outside the existing protocol and needs its own driver/validation logic (design reserved to the planner).
- **Limitations:** —
- **Code reference:** `cg3d/protocol.py`
- **Confidence:** HIGH

## E-032 — Plain closed bounce-back walls were stable on the rough graphite geometry (X1 probe E)

- **Question:** Q4
- **Claim:** In the X1 NaN investigation, the mode with **no membranes and no reservoirs, plain bounce-back walls**, was stable for 3000 steps on the raw rough graphite geometry, while reservoir/membrane forcing resting on the rough surface diverged; the fix for the open system was geometric padding (14 lu open buffer).
- **Source ID:** S-CG3D-RESULTS (§2, probe table)
- **Location:** RESULTS.md §2 (mode E row + fix paragraph)
- **Support type:** DIRECT (project-verified probe)
- **Evidence summary:** The outer-boundary mechanism of the planned closed baseline (plain BB walls) is the *stable* member of the probed family on this geometry.
- **Applicability to current CG3D:** Removes one feasibility risk for the closed baseline; the X1 lesson applies to reservoir/membrane layouts, which the closed baseline need not use at its outer ends (though interior membranes for buffers, if any, would need the buffer rule).
- **Limitations:** 3000 steps only, no drive, no interface motion; not a stability proof for the full bilateral run.
- **Code reference:** `docs/RESULTS.md` §2; `probe_gx1_nan.py` (mode E)
- **Confidence:** MEDIUM-HIGH

## E-033 — Closed vs open outer ends is a physical-statement decision with consequences on both sides

- **Question:** Q4
- **Claim:** Choosing closed outer walls (planned baseline) asserts a fixed-mass, gas-capturing problem: trapped gas is compressed and the end state is set by mass conservation + capillary equilibrium (E-016/E-017); choosing open pressure boundaries instead answers the established reservoir-driven problem where Pc is controlled and phases escape (E-031, E-029) — a materially different physical question. Evidence on both sides: closed walls are stable on this geometry (E-032) and match a "sealed cell / worst-case gas retention" statement; open ends follow all application precedent (E-029) and avoid compression-regime uncertainty (E-016, E-017).
- **Source ID:** synthesis of E-016, E-017, E-029, E-031, E-032
- **Location:** —
- **Support type:** INFERENCE
- **Evidence summary:** The decision framework; no source decides it.
- **Applicability to current CG3D:** Reserved for external review (METHOD_EVIDENCE §9).
- **Limitations:** Work can proceed on verification cases (tube LW, collision case) without resolving it — those cases are boundary-design-agnostic in their first rungs.
- **Code reference:** —
- **Confidence:** MEDIUM-HIGH

## E-034 — Reservoir/buffer-size sensitivity requirements (proposed minimum)

- **Question:** Q4
- **Claim:** Before the porous-stack result is interpreted, a minimum sensitivity study should demonstrate invariance to the liquid-buffer size (e.g. front dynamics and end-state observables stable under a ≥2× buffer-thickness change), because no local source has ever run a finite closed buffer (E-029 absence) and wave reflection from the closed ends is documented physics in LBM boundaries (E-028).
- **Source ID:** synthesis of E-028 (reflection) + E-029 (absence of precedent)
- **Location:** —
- **Support type:** INFERENCE / PROPOSED DIAGNOSTIC
- **Evidence summary:** The *need* for a sensitivity check follows from documented artefact classes; the specific protocol is a proposal.
- **Applicability to current CG3D:** Buffers of the planned geometry (gap/channel) are cheap to enlarge in a synthetic stack.
- **Limitations:** No numeric invariance tolerance is defensible from the corpus; not a hard gate.
- **Code reference:** —
- **Confidence:** MEDIUM

---

### Support-type inventory

DIRECT: E-001, E-002, E-003, E-004, E-005, E-006, E-007, E-008, E-009,
E-010, E-011, E-013, E-015, E-018, E-019, E-020, E-021, E-022, E-023,
E-024, E-025, E-026, E-028, E-029, E-030, E-031, E-032.
INFERENCE (incl. proposed diagnostics): E-012, E-014, E-016, E-017, E-027,
E-033, E-034.
No PARTIAL items were needed; where a source covers part of a claim the
item was either split or downgraded to INFERENCE.
