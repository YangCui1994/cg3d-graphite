# Validation Report — Leclaire/Latt reference line (pass-06)

- stage: `BI-CG-LECLAIRE-JURIN-PROVENANCE-CLOSURE-001`
- candidate SHA: `9773a439f9f994225ce6515bd9f755815aa2c5af`
- branch: `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`
- raw-data schema: `l17c_core_raw_f32_v2`
- convention: n_w = +grad(g)/|grad(g)| = fluid -> solid; theta through liquid/red
- verdict counts: {'PASS': 8, 'FAIL_SOLVER': 3}

This is the **current headline** for this solver line. Passes 1-5
remain in Git history and under `results/leclaire_cg/` and are
**SUPERSEDED**; their claims are not current. Pass-4 in particular used
the superseded wall normal `-grad(g)` and the complementary circle-fit
sign, so its contact-angle, slit-Pc and Jurin verdicts are void.

## Case summary

| case | verdict | artifact |
|---|---|---|
| case-01 | **PASS** | `case-01-uniform-stationarity/README.md` |
| case-02 | **PASS** | `case-02-planar-interface/README.md` |
| case-03 | **FAIL_SOLVER** | `case-03-laplace-multi-radius/README.md` |
| case-04 | **PASS** | `case-04-contact-angle/README.md` |
| case-05 | **PASS** | `case-05-beta-width-validity/README.md` |
| case-06 | **PASS** | `case-06-axis-symmetry-isotropy/README.md` |
| case-07 | **PASS** | `case-07-slit-capillary-pressure/README.md` |
| case-08 | **FAIL_SOLVER** | `case-08-jurin-equilibrium/README.md` |
| case-09 | **FAIL_SOLVER** | `case-09-asymmetric-wall/README.md` |
| case-10 | **PASS** | `case-10-conservation/README.md` |
| case-11 | **PASS** | `case-11-mechanical-sigma/README.md` |

## Per-case evidence

### case-01 — PASS

Artifact: `case-01-uniform-stationarity/`

| metric | value |
|---|---:|
| max_abs_v | 8.77442e-14 |
| max_abs_drho | 7.27196e-14 |
| red_mass_drift | 3.72324e-11 |
| blue_mass_drift | 0 |
| verdict | PASS |

### case-02 — PASS

Artifact: `case-02-planar-interface/`

| metric | value |
|---|---:|
| interface_pos_initial | 16 |
| interface_pos_final | 15.9943 |
| interface_pos_drift | 0.00566575 |
| amplitude_ratio | 0.999867 |
| max_spurious_v | 2.19979e-13 |
| verdict | PASS |

### case-03 — FAIL_SOLVER

Artifact: `case-03-laplace-multi-radius/`

| metric | value |
|---|---:|
| sigma_input | 0.02 |
| sigma_free_intercept | 0.0225384 |
| sigma_zero_intercept | 0.0208243 |
| intercept | -0.000487216 |
| r2 | 0.999956 |
| sigma_ratio | 1.12692 |
| sigma_1overR_fit_unstable | -0.000242866 |
| r2_vs_invR | 0.99255 |
| verdict | FAIL_SOLVER |
| note | Eq.(18) A=(9/4)omega*sigma is NOT retuned; an offset is a result. |

> Eq.(18) A=(9/4)omega*sigma is NOT retuned; an offset is a result.

### case-04 — PASS

Artifact: `case-04-contact-angle/`

| metric | value |
|---|---:|
| verdict | PASS |
| phase_convention | theta measured through psi>0 liquid/red |
| wall_normal | n_w = +grad(g)/|grad(g)| = fluid -> solid |

### case-05 — PASS

Artifact: `case-05-beta-width-validity/`

| metric | value |
|---|---:|
| monotone_in_beta | True |
| verdict | PASS |

### case-06 — PASS

Artifact: `case-06-axis-symmetry-isotropy/`

| metric | value |
|---|---:|
| equal_wavelength | True |
| amplitude_asymmetry | 1.58921e-13 |
| verdict | PASS |
| scope | axis symmetry on a cubic lattice, not general rotational isotropy |

### case-07 — PASS

Artifact: `case-07-slit-capillary-pressure/`

| metric | value |
|---|---:|
| gap | 10 |
| sigma | 0.02 |
| verdict | PASS |
| sign_change_across_60_120 | True |
| zero_at_90_ok | True |
| zero_bound | 0.0001 |
| ratio_band_ok | True |
| pc90_theory_is_zero | 2.44929e-19 |
| note | ratio gate applied to the 60/120 arms only; the 90 deg arm is gated on an absolute near-zero bound |

> ratio gate applied to the 60/120 arms only; the 90 deg arm is gated on an absolute near-zero bound

### case-08 — FAIL_SOLVER

Artifact: `case-08-jurin-equilibrium/`

| metric | value |
|---|---:|
| rise_final | 1 |
| rise_theory | 8 |
| rise_ratio | 0.125 |
| theta_prescribed_deg | 60 |
| g | 0.00025 |
| gap | 10 |
| verdict | FAIL_SOLVER |
| geometry | connected reservoir + barrier + slit + lower channel (external review R4 section 6) |
| capillary_interface_exists | True |
| reservoir_interface_exists | True |

### case-09 — FAIL_SOLVER

Artifact: `case-09-asymmetric-wall/`

| metric | value |
|---|---:|
| wall_band_red_relative | -0.068308 |
| max_red_excursion | 2.74915e-13 |
| max_blue_excursion | 2.74148e-13 |
| late_red_rate_per_step | -2.41926e-13 |
| late_blue_rate_per_step | -2.55871e-13 |
| red_drift | 3.62888e-10 |
| blue_drift | 3.83807e-10 |
| n_components_final | 1 |
| max_abs_v | 0.000327518 |
| verdict | FAIL_SOLVER |
| attribution | wall-band change is NOT attributed to wall mass transfer; no stationary reference case was run |

### case-10 — PASS

Artifact: `case-10-conservation/`

| metric | value |
|---|---:|
| verdict | PASS |
| scope_limitation | EXTERNAL REVIEW B10: this result is for the isolated NumPy/f64 reference implementation only. The project's earlier conservation defect was precision/backend specific, so this must NOT be generalised to a Taichi/f32 port without repeating the audit there. |

> EXTERNAL REVIEW B10: this result is for the isolated NumPy/f64 reference implementation only. The project's earlier conservation defect was precision/backend specific, so this must NOT be generalised to a Taichi/f32 port without repeating the audit there.

### case-11 — PASS

Artifact: `case-11-mechanical-sigma/`

| metric | value |
|---|---:|
| sigma_mech | 0.0199999 |
| sigma_input | 0.02 |
| sigma_ratio | 0.999995 |
| A_coefficient | 2.25 |
| omega_eff | 1 |
| predicted_from_derivation | 0.02 |
| verdict | PASS |
| verdict_reason | premises closed and ratio inside the predeclared band |
| note | EXPLORATORY unless premises closed; A=(9/4)omega*sigma is not retuned and the raw N_i distribution is retained so the stress observable is recomputable from the committed snapshot alone. |

> EXPLORATORY unless premises closed; A=(9/4)omega*sigma is not retuned and the raw N_i distribution is retained so the stress observable is recomputable from the committed snapshot alone.

## Reading rule

A verdict of `FAIL_SOLVER` is a solver result; `INVALID_TEST` and
`INCONCLUSIVE` are test-design outcomes and must never be presented as
solver failures. `EXPLORATORY_UNGATED` marks a diagnostic whose prefactor
is not closed from the source.
