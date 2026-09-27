# Pass-04 Validation Report — Leclaire/Latt reference line

- stage: `BI-CG-LECLAIRE-PASS4-001`
- candidate SHA: `0b3da4e954878dc22618330caed9f0da0782d449`
- branch: `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`
- raw-data schema: `l17c_core_raw_v1`
- convention: n_w=-grad(g)/|grad(g)| solid->fluid; theta through liquid/red
- verdict counts: {'PASS': 7, 'FAIL_SOLVER': 2, 'INVALID_TEST': 1, 'INCONCLUSIVE': 1}

This is the **current headline** for this solver line. Passes 1, 2 and 3
remain in Git history and in `results/leclaire_cg/` and are **SUPERSEDED**;
their claims are not current.

## Case summary

| case | verdict | artifact |
|---|---|---|
| case-01 | **PASS** | `case-01-uniform-stationarity/README.md` |
| case-02 | **PASS** | `case-02-planar-interface/README.md` |
| case-03 | **FAIL_SOLVER** | `case-03-laplace-multi-radius/README.md` |
| case-04 | **PASS** | `case-04-contact-angle/README.md` |
| case-05 | **PASS** | `case-05-beta-width-validity/README.md` |
| case-06 | **PASS** | `case-06-axis-symmetry-isotropy/README.md` |
| case-07 | **INVALID_TEST** | `case-07-slit-capillary-pressure/README.md` |
| case-08 | **INCONCLUSIVE** | `case-08-jurin-equilibrium/README.md` |
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
| sigma_extrapolated_large_R | -0.000242866 |
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
| wall_normal | n_w = -grad(g)/|grad(g)|  (solid->fluid) |

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

### case-07 — INVALID_TEST

Artifact: `case-07-slit-capillary-pressure/`

| metric | value |
|---|---:|
| gap | 10 |
| sigma | 0.02 |
| verdict | INVALID_TEST |
| sign_change_across_60_120 | False |

### case-08 — INCONCLUSIVE

Artifact: `case-08-jurin-equilibrium/`

| metric | value |
|---|---:|
| rise_final | nan |
| rise_theory | 8.33333 |
| theta_prescribed_deg | 60 |
| g | 0.0003 |
| gap | 8 |
| verdict | INCONCLUSIVE |

### case-09 — FAIL_SOLVER

Artifact: `case-09-asymmetric-wall/`

| metric | value |
|---|---:|
| wall_band_red_relative | -0.068308 |
| max_red_excursion | 2.74915e-13 |
| max_blue_excursion | 2.74473e-13 |
| late_red_rate_per_step | -2.41926e-13 |
| late_blue_rate_per_step | -2.56478e-13 |
| red_drift | 3.62888e-10 |
| blue_drift | 3.84262e-10 |
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
| sigma_mech | 0.0153655 |
| sigma_input | 0.02 |
| sigma_ratio | 0.768275 |
| A_coefficient | 2.25 |
| omega_eff | 1 |
| predicted_from_derivation | 0.02 |
| verdict | PASS |
| note | Eq.(18) is not retuned; an offset is a reported result. |

> Eq.(18) is not retuned; an offset is a reported result.

## Reading rule

A verdict of `FAIL_SOLVER` is a solver result; `INVALID_TEST` and
`INCONCLUSIVE` are test-design outcomes and must never be presented as
solver failures. `EXPLORATORY_UNGATED` marks a diagnostic whose prefactor
is not closed from the source.
