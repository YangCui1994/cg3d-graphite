stage: V1
attempt: 1
candidate: e9540bcadb86257c70b805afc98f2eec9626c64e
execution_report: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/real/V1/round-01/execution_report.md

# review — V1 single-front dynamic wetting (attempt 1)

## binding

- Product worktree `D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-VALIDATION-001`, branch `agent-episode/BI-VALIDATION-001`.
- `git rev-parse HEAD` returns `e9540bcadb86257c70b805afc98f2eec9626c64e`, exactly the frozen candidate, and `git status --porcelain` is empty: the tree matches the candidate, so binding is unambiguous.
- Parent commit is `280a46fed488b12975c3de96b5493362942822ec`, as the execution report states.
- Diff scope: 17 files added, none modified, none deleted. `git diff --stat 280a46f e9540bc -- . ':(exclude)tests' ':(exclude)results'` is empty, so no solver, driver or geometry file changed. The report's "no solver file was touched" claim is correct and independently verified.
- The driver uses only existing solver interfaces (`ColorGradientSolver3D`, `set_psi_solid_field`, `set_membranes`, `set_reservoirs`, `init`, `step`, `psi_snapshot`, `macro_snapshot`, `color_masses`, `reservoir_fluxes`), all present in `lbm_solver_cg3d.py` with the semantics the driver assumes. The membranes are used as documented in `docs/BC_IC_OUTPUT.md:11-24` (`mem_r` blocks the psi>0/gas fraction, `mem_b` blocks the psi<0/liquid fraction; the inlet gets `mem_r`, the outlet `mem_b`).
- Wettability semantics check: `docs/BC_IC_OUTPUT.md:26` (registry, liquid-side angle: psi_solid −0.68 → 30°) and the wall-colour treatment at `lbm_solver_cg3d.py:428-452` support the driver's premise that the invading psi = −1 phase is the wetting one at psi_solid = −0.68. The candidate's own measurements confirm it empirically (the wall-adjacent layer leads the centreline; `sag_y_wall_minus_centre = 5.0` lu in `v1_h26_report.json`). One incidental note: the solver docstring at `lbm_solver_cg3d.py:180-183` names psi>0 "liquid"/red, which is inverted relative to the driver and the docs; with matched viscosity (0.1/0.1) this is inert here, and it is a pre-existing repository inconsistency, not introduced by this candidate.

## coverage

### requirement table (V1 stage contract, gates as written)

| Requirement | Status | Evidence |
|---|---|---|
| gate 1 — no NaN/Inf, no stability-cap violation | pass | `nan_at = null`; u_max peak 0.02358 (h26) / 0.02422 (h40) against the 0.12 cap; recomputed from the probe CSVs |
| gate 2 — correct zero imposed pressure difference | pass | both pinned reservoirs read rho = 1.000000 at every probe in both runs (recomputed) |
| gate 3 — monotonic capillary advance after initialization | pass | zero reversals in either run (smallest increment 0.754 / 0.487 lu per 250 steps) |
| gate 4 — post-transient interval ≥ 40 % of the usable trajectory | pass | h26: 100 % of the declared trajectory, 74 % of the x ≥ x0+3b trajectory; h40: 88 %. See N2 for how the declared rule degrades at h40 |
| gate 5 — x² vs t has R² ≥ 0.98 on that interval | ambiguous, and window-dependent: h26 literal pass 0.999747, h40 literal fail 0.979203 | recomputed; the report's gate-5 row quotes h26 only. As a form test the gate is non-discriminating here (S3) |
| gate 6 — slope within 10 % of the chosen relation | fail, decisively | h26 −58.36 %, h40 −73.71 % (recomputed: −0.583585, −0.737145) |
| gate 7 — colour-mass accounting closes, no drift trend | pass, with a wording caveat | closure 4.2e-4 (h26) / 4.5e-4 (h40) of the exchanged mass; the residual accumulates monotonically, contradicting "no trend" as phrased (N4) |
| gate 8 — larger resolved channel does not qualitatively change the conclusion; normalized slope reported | satisfied as worded | the conclusion is unchanged (same stable form, same gate-6 failure); the normalized slope is reported, and is 0.971 against the required 1.538 |
| geometry: smooth synthetic, ≥ ~6 interface widths wall-to-centreline | marginal for h26, met for h40 | b = 13 lu = 5.9 interface widths (interface ≈ 2.2 lu, `docs/ALGORITHM.md:21`); the h40 case has 9.1. This is a soft v0.1 design target, not one of the eight gates (N8) |
| geometry/IC deterministic and reproducible | pass | no RNG; deterministic arrays; fixed membrane/reservoir masks |
| driver records front vs t, extraction definition, colour-mass accounting, pressure/density summaries, u_max/u_rms, exact parameters | pass | `*_front.csv`, `*_probe.csv`, `*_report.json`, header docstring at `tests/levelc_imbibition.py:149-175`; the dynamic-angle proxy (`xf_y`, sag) is present as an optional diagnostic |
| not on real graphite | pass | straight synthetic slit, z periodic |
| reference relation appropriate to the configuration, fit window declared before interpretation | pass | derivation in the driver header (`tests/levelc_imbibition.py:25-61`) and in report §1; the constant-velocity law is the correct law here (S1), and the window rule was declared a priori |

### validation table (what this review actually checked)

| Claim | Verified | Method / file |
|---|---|---|
| candidate identity, clean tree | yes | `git rev-parse HEAD`, `git status --porcelain` |
| no solver/driver change | yes | `git show --numstat`, empty non-tests/results diff |
| V, R², gate 6 for both runs | yes | `reviewer_evidence/verify_v1_evidence_output.txt` |
| committed `analyze()` reproduces the committed report keys | yes | `reviewer_evidence/reproduce_report_numbers_output.txt` — every gate key matches to ≤ 5e-7 relative |
| monotonicity, reservoir densities, u_max, colour-mass closure | yes | recomputed from committed probe CSVs |
| meniscus jump = 0.76 × nominal Laplace | yes | `reviewer_evidence/analyze_axial_profile_output.txt`: +3.086e-3 vs 4.045e-3 |
| "~1.35e-3 unaccounted" drop | yes, and localised further | `analyze_boundary_drops_output.txt`: single-cell drops of −2.979e-4 at x = 11→12 and −9.957e-4 at x = 257→258, summing to 1.294e-3 |
| L-scan ratio 0.641 | yes | recomputed from `diag/Lscan_series.csv`: 2.474e-3 vs 3.857e-3 |
| figures were produced by the committed driver | no — disproved | `results/levelc_v1/v1_h40_run.log:13` records the figure step failing; the committed PNG has a different panel set (N5) |
| report JSONs are raw driver output | no — disproved | they contain `x_fit` arrays the committed `analyze()` never writes and lack the `c` key it writes (N5) |
| gate 8 "does not change the conclusion" (qualitative) | yes | same stable form, same direction of gate-6 failure at both resolutions |

No GPU simulation was re-run. Every gate-relevant quantity is re-derivable from the committed series, and running the committed `analyze()` on the committed CSVs reproduces the report exactly, so an independent GPU re-run would only re-consume JIT time without adding information.

## findings

### blocking

**B1 — gate 6 fails by a wide margin, verified independently.**
h26: V = 3.857e-3 against V_pred = 9.263e-3 → −58.4 %; h40: V = 3.746e-3 against 14.251e-3 → −73.7 %. The tolerance is 10 %. The number is window-insensitive (the wider x ≥ x0+3b windows give −58.5 % and −73.5 %), so it is not a fit-window artefact. `results/levelc_v1/v1_h26_report.json`, `v1_h40_report.json`, recomputed in `reviewer_evidence/verify_v1_evidence_output.txt`.

**B2 — the anomaly is unexplained and splits into two effects that both have to be removed for gate 6 to pass.**
From the committed axial profile (h26, final snapshot at 20 000 steps):
- the far-field pressure gradients match plane Poiseuille for the *observed* speed (liquid −7.056e-6/lu, gas −6.891e-6/lu against −6.847e-6/lu), so the columns themselves are not anomalous;
- the meniscus jump obtained by extrapolating those lines to the interface is 3.086e-3 = 0.763 × the nominal σcosθ/b = 4.045e-3;
- the remaining ≈ 1.3e-3 is *not* near the meniscus: it sits in two single-cell transitions at the pinned reservoir planes, −2.979e-4 at x = 11→12 and −9.957e-4 at x = 257→258, i.e. 43× and 145× the plane-Poiseuille gradient per lattice cell. This is a new decomposition relative to the report, which quantified the unaccounted drop (≈ 1.35e-3) but not where it lives.
The h_y dependence compounds the problem: V(40)/V(26) = 0.971 where the declared relation requires 1.538, so the deficit is not a simple additive length offset (a two-point resistance fit gives both a proportional excess, a = 1.34× plane Poiseuille, and a fixed term equivalent to ~194 lu of channel). No single mechanism is singled out by the data as presented.

**B3 — no in-scope numerical or measurement correction restores gate 6.**
Best case, quantified: if the entire 1.29e-3 boundary loss were removed by rebuilding the boundary layout to the repository's documented convention, the front would be driven by the measured 3.086e-3 jump alone, giving V = 7.07e-3 — still 24 % below the required 9.263e-3. The residual gap requires the moving meniscus to deliver the full σcosθ/b, which is a property of the wall-colour/diffuse-interface treatment (or of the effective contact angle at a moving contact line) — a solver/model question, and V1 authorises no solver change. Corroborating: the h40 case, which comfortably meets the resolution target, is *worse* (−73.7 %), so under-resolution of the primary case is not the cause.

**B4 — a scientific-assumption decision is required before V1 can have a defensible acceptance rule.**
The stage contract's gate 5 is written in terms of x² vs t, which cannot hold in the episode's fixed configuration (matched viscosity, equal-pressure baths, defined escape path): the total series resistance is length-independent, so the post-transient law is x = x0 + Vt. The executor derives this correctly and flags the mismatch; gate 5's literal pass on the h26 declared window is, as the executor says, non-discriminating. Whether V1's dynamic-wetting acceptance is reformulated on the constant-velocity relation (with the h_y-independence test as the accompanying form check), or the configuration is changed so that a genuine x² ~ t regime exists, is a modeling decision, not a reviewer call.

### non-blocking

**N1 — the gate table does not disclose that h40 fails gate 5 literally.** h40's declared window gives R²(x²~t) = 0.979203 < 0.98 (`v1_h40_report.json`), while the report's gate-5 row quotes only h26's 0.99975. The table is presented as one result per gate; per-run status should be separated.

**N2 — the declared mechanical window rule degrades silently.** `tests/levelc_imbibition.py:370-379` computes `i_lo = int(np.argmax(x >= x_lo))` with `x_lo = x0 + 5·h_y`. For h40 the front never reaches 240, `argmax` returns 0, and the "trajectory" silently becomes the whole series including the initial transient (`trajectory_idx = [0, 159]`), with no note; the `window_note` fallback exists only for the t-transient condition. For h26 the declared window holds just 23 samples (front advance ratio 1.12), which the report does disclose. The consequence is that the declared-window numbers are weakly constrained and the strong linearity claim actually rests on the wider windows, which are not the declared ones.

**N3 — the driver records a meniscus-jump diagnostic that is invalid, and the JSON presents it as a measurement.** `tests/levelc_imbibition.py:247-252` takes p_liq and p_gas from slabs 3–9 lu either side of the front crossing. The committed profile shows a p = rho/3 well of ≈ 1.96e-2 inside the interface band (six times the capillary jump), so those slabs do not measure the jump: `pc_measured_last` is +1.42e-4 for h26 (≈ 3.5 % of nominal) and −3.07e-3 for h40 (wrong sign relative to the capillary drive). The execution report does not quote these values (it uses the axial-extrapolation value, correctly), but the JSON exposes them without a validity caveat. Either measure the jump from far-field extrapolation inside the driver or mark the band diagnostic invalid.

**N4 — the gate-7 wording overstates the drift check.** The claim "the residual does not trend with time" is not what the data show: the injection-versus-field residual grows monotonically with the exchanged mass (h26: −0.019 → −10.0 over 40 000 steps, i.e. a constant ≈ 4.2e-4 relative closure). The relative level is small and consistent with f32 field summation (the counters are f64 by design), so the closure conclusion stands; only the phrasing is wrong.

**N5 — the evidence bundle and the committed source were not co-produced, which the report and PROVENANCE do not disclose.** Three facts: (a) `results/levelc_v1/v1_h40_run.log:13` shows the figure step failing with a shape mismatch (141 vs 47), yet `fig_v1_h40.png` is committed; (b) that figure's four panels ("front position / naive Washburn form / kinetic diagnostics / reservoir densities" plus a suptitle) are not the committed driver's panel set (`tests/levelc_imbibition.py:311-345` ends with an imshow of the final psi field), and the committed block cannot produce that shape mismatch — so the executed driver was a different revision from the committed one; (c) the committed report JSONs contain `fit_*['x_fit']` arrays that the committed `analyze()` never writes, lack the `c` key it does write, and for h40 the `fit_x2` array has 47 entries while its own fit window has 141. The figure's *content* is consistent with the h40 evidence (front 40→187, R²_lin = 0.999968, slope 0.908, R² = 0.9792, u_max ≈ 0.021–0.024, reservoir rho ≡ 1.000), so this is not a wrong-run substitution. The mitigating fact that keeps this non-blocking: every gate-relevant number reproduces exactly from the committed raw series with the committed `analyze()`, so the science is traceable even though the artifact-level provenance chain has a hole (no committed producer for the figures, no committed log for the primary run, and a PROVENANCE claim that everything came from the driver plus the three diagnostics).

**N6 — boundary layout deviates from the repository's documented convention.** `docs/BC_IC_OUTPUT.md:11-28` documents 3-lu walls, 8-lu reservoirs, a 1-lu membrane and a 2-lu open buffer, with an explicit "do not skip" buffer rule. The candidate uses a 10-lu liquid reservoir whose pinned region *includes* the membrane plane x = 11, a 2-lu gas reservoir, and no buffer. The report discloses only the gas-reservoir thickness (§6.4). No NaN occurred (the geometry is smooth), but this layout is a plausible contributor to the boundary drops localised in B2 and should be brought to convention before any follow-up run, so that the boundary contribution can be separated from the meniscus effect.

**N7 — evidence gaps in the bundle.** The pressure-field diagnostics exist only for h26 and only as single final snapshots (the diagnostic time series stay in untracked `.npz` files on the Windows machine, as PROVENANCE states), so the h40 pressure decomposition cannot be checked from the bundle; there is no committed console log or exit-code record for the primary h26 run; and the report's §3/§5 quotes V = 3.842e-3 / 3.773e-3, which are the wider-window fits rather than the declared-window values (3.857e-3 / 3.746e-3) — immaterial to the conclusion, but the window is not stated.

**N8 — the primary case sits just under a soft geometry target.** h26 has b = 13 lu = 5.9 interface widths against the contract's "at least about six" v0.1 design target. This is a project design choice, not one of the eight gates, and the h40 case (9.1 widths) covers the intent — and, being worse, rules resolution out as the cause of the anomaly.

## scientific / modeling review

**S1 — the comparison equation is the right one for this configuration.** With matched viscosity and two equal-pressure baths, the liquid and gas columns are in series over a fixed total length, so the Washburn resistance (mu_l·l_liq + mu_g·l_gas) is constant and the post-transient law is x = x0 + Vt with V = Pc·h_y²/(12·mu·L_tot); the 2D-slit form uses h_y²/12, and Pc = σcosθ/b with b = h_y/2 is correct for a z-invariant meniscus (z periodic removes the second principal curvature). I re-derived this independently before reading the report's argument. The executor's choice is also unfavourable to itself: the naive gas-negligible x² ~ t form gives −69 % / −87 %, larger deficits than the relation actually used. There is no evidence of cherry-picking the relation.

**S2 — the front extractor is appropriate, and the anomaly is not a measurement artefact.** The primary (volumetric swept-length) definition integrates over the diffuse interface and the cross-section; the secondary (column-mean crossing) definition tracks it with a small offset, and fitted slopes are insensitive to the choice. The advance is strictly monotone and linear in t with R² = 0.9999979 over a 2.4× advance, i.e. the *form* of the matched-viscosity series-resistance dynamics is reproduced. The static contact-angle validation from the V0 stage is not being used as dynamic proof: the executor reports the implied apparent angle (≈ 50°) explicitly as a diagnostic.

**S3 — why gate 5 cannot decide anything here.** For a constant-velocity front, K_fit/K_naive ≈ ⟨x⟩/L_tot and R²(x² ~ t) approaches 1 for short advances (the executor's own note: below ~3.5× advance). On the declared h26 window the advance ratio is only 1.12, so the literal gate-5 pass carries no information; on the wider windows the same data give 0.988 (h26) and 0.994 (h40). The honest readings are the ones the executor supplies — this is a contract-design issue (B4), not a data problem.

**S4 — the regime is stable and quasi-steady in shape, wrong in rate.** Both runs are free of non-finite values, hold the reservoir densities at exactly 1.0, keep u_max far below the cap, and end at the 40 000-step cap rather than the planned x_stop because the front is slower than predicted. The flow is quasi-steady (last-quarter V within 1.6 % of the declared-window fit; far-field gradients consistent with Poiseuille at the observed speed). The executor does not present exit code 0 as convergence, which is the right treatment.

**S5 — mass accounting.** The injected colour mass is accumulated in f64 counters, so the 4e-4 relative closure against the f32 field sums is the expected numerical floor; there is no systematic *relative* drift. Total density mass does not close (inj_m = −103.8 / −118.8), which is inherent to density-prescribed (pressure) reservoirs and should not be presented as mass conservation — the report keeps to the colour-mass statement, which is the meaningful one, subject to N4's wording.

**S6 — physical meaning.** The measurements show a moving meniscus whose capillary pressure is ≈ 0.76× the wall-colour Laplace value at Ca ≈ 6e-3, i.e. an effective dynamic contact angle near 50° rather than the 30° registry value, plus a large boundary-region loss. The first is exactly the kind of effect V1 exists to quantify; whether it is admissible model behaviour (dynamic wetting) or an artefact of the diffuse-interface/contact-line treatment cannot be settled from this evidence. No existing evidence is invalidated by the candidate, since no shared file changed, and the report's §8 statement to that effect is correct.

## missing evidence

- h40 pressure-field diagnostics: the axial and front profiles are h26-only, so the boundary-drop decomposition cannot be checked at the second resolution where the anomaly is worse. With B2/B3 in play this is the one measurement that would most sharpen a next step.
- A static (stalled) meniscus pressure-jump measurement in this same slit geometry. The V0 contact-angle calibration used a floor droplet, a different geometry; the candidate has no independent check that σcosθ/b is what this slit-plus-wall-colour combination delivers before the front starts moving. This is the executor's own suggested next measurement and I agree it is the right fork.
- Diagnostic time series (.npz) are untracked on the Windows machine by design; the manifest records their location, which the episode's evidence model permits, but it means the spurious-current history ("~2× Poiseuille decaying over 20–25 lu") is not independently checkable off-machine.
- h26 console log and exit code: no committed record, so the report's "exit 0" for command 1 is an executor claim only.

## decision

Decision: HUMAN_REQUIRED

## rationale

A hard gate fails (gate 6, by 2.4× and 3.8× against a 10 % tolerance), the failure is verified independently, and it is not repairable inside this stage. The stage contract says that when gates 4–6 fail but the trajectory is stable, the reviewer may request changes only if a finite numerical or measurement correction exists; here none does. The measurement of V is sound and window-insensitive; the reference relation is correct as derived; and the quantified best case for an in-scope boundary-layout correction still leaves V 24 % below the required value, with the remaining gap residing in the moving meniscus's capillary pressure — a solver/model property that V1 does not authorise changing. On top of that, the contract's gate 5 is written in a form that cannot hold in the episode's own fixed configuration, so a defensible V1 acceptance rule needs a modeling decision rather than another measurement. The Episode Contract's escalation conditions are therefore all live: a hard gate fails for a reason that may reveal a solver/model limitation, the anomaly is large enough that promotion would need a new acceptance rule, and V1 has not established a defensible *quantitative* capillary-filling regime (its qualitative form is defensible). This is a scientific finding about the current wetting/BC treatment, not an executor defect: the candidate is a well-built, honest piece of work that reports its own unfavourable numbers, does not tune the anomaly away, and changes no solver code. N1–N8 are real but none of them would change the outcome.

## next action

Stop the stage for the human/modeling checkpoint before any rework or promotion. The checkpoint needs to settle two questions, and no further V1 run should be started until it does:

1. Acceptance form. Either V1's dynamic-wetting acceptance is reformulated on the configuration-appropriate constant-velocity relation (V = Pc·h_y²/(12·mu·L_tot)) with the h_y-scaling test as the companion form check, or the configuration is changed (for example a viscosity contrast) so that a genuine x² ~ t regime exists and the contract's gate 5 becomes meaningful.
2. Model admissibility. Whether an effective moving-meniscus jump of 0.763 × σcosθ/b and a boundary-region loss of ~1.3e-3 (equivalent to ~194 lu of channel) are acceptable model behaviour for this diffuse-interface formulation, or a defect in the wall-colour/contact-line or reservoir/membrane treatment that must be investigated before V2/V3 can be designed.

The single most informative next measurement, which I endorse from report §10 with a concrete reading: stall a meniscus in this same slit (pin the two reservoirs at a small density difference) and read the jump by far-field extrapolation. If it returns ≈ σcosθ/b = 4.045e-3, the deficit is a dynamic moving-contact-line effect; if it already returns ≈ 3e-3, the static calibration does not carry to this geometry. In parallel, and independently of that result, bring the boundary layout to the repository's documented convention (8-lu reservoirs, 1-lu membrane, 2-lu open buffer, membrane plane outside the pinned region), because that is the one part of the deficit that is provably a configuration choice and it must be removed from the budget before any conclusion about the wall-colour implementation is drawn. Parenthetically for planning: V2/V3 acceptance must not be designed on the x² ~ t form, and no absolute front-speed prediction from σcosθ may be treated as validated until question 2 is answered.
