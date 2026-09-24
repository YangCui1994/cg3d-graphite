# EXECUTION REPORT — BI-V1C-CLOSURE-001

- Task: V1c closure — static resolution convergence + differential
  hydraulics (`V1C_CLOSURE_CONTRACT.md`), executor = interactive ZCode
  session per `START_V1C.md` section 3.
- Base SHA: `a9c6db87da2eeb3572607152391fe6863394ebee` (V1b candidate)
- Candidate: this commit (`results/levelc_v1c/**` +
  `tests/levelc_v1c.py`; no solver change, no V1/V1b history change).
- Primary runs (all shell exit 0; logs + `.exit` under `logs/`):

| Tag | Command (interpreter = conda env `lbm`) | Ended |
|---|---|---|
| static_h26 | `levelc_v1c.py static --hy 26 --tag static_h26` | Pc stationary @19 750 |
| static_h40 | `… static --hy 40 --tag static_h40` | Pc stationary @12 500 |
| static_h60 | `… static --hy 60 --tag static_h60` | Pc stationary @12 000 |
| static_h80 | `… static --hy 80 --tag static_h80` | Pc stationary @13 000 |
| dyn_h26_s | `… dynamic --hy 26 --tag dyn_h26_s` | x_stop @40 250 |
| dyn_h26_2L | `… dynamic --hy 26 --L 472 --tag dyn_h26_2L` | steps_cap 60 000 |
| dyn_h40_s | `… dynamic --hy 40 --tag dyn_h40_s` | x_stop @36 500 |
| dyn_h40_2L | `… dynamic --hy 40 --L 472 --tag dyn_h40_2L` | steps_cap 60 000 |
| (collect) | `levelc_v1c.py collect` | exit 0 |

## Measured facts

### A — static resolution convergence (V1c-A)

| h | `Pc_static` | `C_static` | `theta_static_slit` |
|---|---|---|---|
| 26 | 3.690809e-3 | 0.7902 | 37.80° |
| 40 | 2.280325e-3 | 0.7511 | 41.31° |
| 60 | 1.632839e-3 | 0.8067 | 36.22° |
| 80 | 1.183271e-3 | 0.7795 | 38.79° |

Convergence-fitting (C vs 1/h, contract A: constant / 1/h / 1/h²,
residuals): constant `C = 0.7819` with `resid_max = 0.031` (±3.9%
scatter); `over_h` R² = 0.007, `over_h2` R² = 0.0001 — **no 1/h-type
convergence law is supported by the four points** (non-monotonic: h40
dip).  The data support an identifiable plateau
`C_static ≈ 0.782 ± 0.031` (`theta ≈ 38.6° ± 1.8°`), reproducible and
non-erratic; exact equality to the 30° droplet registry is not claimed
and not required by the contract.  V1b's fixed-band h26/h40 difference
of 11.5% shrinks to 5.1% under the bulk-column rule (the V1b value was
band-placement-biased; see V1b external review section 6).

### C — differential hydraulics (V1c-C, primary gates)

| h | L1→L2 | `L_eff1`→`L_eff2` | `a_h` | gate | `L0` | `L0/h` |
|---|---|---|---|---|---|---|
| 26 | 241→477 | 329.6→576.3 | **1.0454** | **PASS** (4.5%) | 77.6 lu | 2.99 |
| 40 | 241→477 | 424.2→681.0 | **1.0880** | **PASS** (8.8%) | 162.0 lu | 4.05 |

`L0/h` values are the same order (2.99 vs 4.05), supporting the
localized entrance/membrane-resistance interpretation of the intercept
(V1b external review section 3); V2's closed finite-buffer geometry
does not contain these boundaries.

### B — bulk-column pressure bands (V1c-B)

Valid-bulk-probe fractions inside the fit windows: 33/35, 55/55, 24/25,
49/49 (≥0.94 everywhere; gate g8 ≥ 0.8 PASS).  Threshold sensitivity of
`Pc_dynamic` across 0.85/0.90/0.95 is ≤ 0.7% everywhere (e.g. h26
short: 2.9099e-3 / 2.9099e-3 / 2.9254e-3) — the V1b 8–9% band-placement
ambiguity is removed.  Invalid probes fail explicitly (`band_valid=0`
rows in `probes.csv`; no silent fallback).

### D — front/stability gates

All four dynamic cases: g1 no NaN ✓, g2 umax ≤ 0.12 ✓, g3 reservoir
deviations 0.0 ✓, g4 monotonic ✓, g5 window valid ✓ (explicit threshold
rule), g6 R2 ≥ 0.995 ✓ (0.99998–1.00000), g7 primary/secondary front
speeds agree ≤ 2% ✓, g8 band fraction ✓.  Colour-mass closure reported
(`closure_r/b_last` in reports; relative ~1e-4, no order-one leakage).
Front speeds reproduce V1b bit-comparably: 4.9740e-3 vs 4.9743e-3 (h26
short), 5.5888e-3 vs 5.5878e-3 (h40 short), 3.0002e-3 (h26 2L) — same
solver, same layout, deterministic.

## Before/after vs V1b

| Metric | V1b (fixed bands) | V1c (bulk-column) |
|---|---|---|
| `Pc_dynamic` band sensitivity | 8–9% | ≤ 0.7% |
| static h26/h40 C difference | 11.5% (gate FAIL) | 5.1% (4-point plateau 0.782±0.031) |
| h26 differential slope `a26` | 1.034 (review-derived) | 1.045 (gate PASS) |
| h40 differential slope `a40` | not measurable (no h40 2L) | 1.088 (gate PASS) |
| raw `V/V_hyd(L_hyd)` interpretation | FAIL, mixed effects | retired as primary metric (intercept L0 documented) |

## Interpretation (contract section 11 separation)

- Measured fact: both primary differential gates pass; the incremental
  bulk hydraulic resistance per unit slit length matches
  plane-Poiseuille within 4.5% (h26) / 8.8% (h40).
- Analytic relation: `L_eff = Pc_dynamic h²/(12 μ V_meas)`,
  `a_h = ΔL_eff/ΔL` — used as declared.
- Project engineering gate: PASS at the 10% level for both heights.
- Model interpretation: the residual intercept `L0(h) ∝ h·(3–4)` is
  consistent with a localized entrance/membrane loss scaling
  `Δp_local ~ μV/h` (V1b external review section 3), an artifact of
  the open V1 validation system that V2's closed buffers do not share.
- Unresolved (diagnostic): the h40 dip in `C_static(h)`; the ~0.92/0.79
  `Pc_dynamic/Pc_static` ratios inherited from V1b reanalysis are not
  re-quoted here because the static reference value itself moved
  (0.67→0.79 at h26) with the corrected band method.

## Deviations

- Producer revisions: primary runs at `032d273…`; the collect-only
  constant-fit design-matrix fix at `5f18caa…` (static/dynamic code
  paths identical; the final candidate carries `5f18caa`'s file).
  Documented in `PROVENANCE.md`.
- No figures on the product branch (contract E); SVG figures are
  generated on the control branch from this committed evidence.

## Suggested next action

Independent fresh review against `V1C_REVIEWER_CONTRACT.md`;
afterwards the mandatory technical-document update
(`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`)
is executed from this candidate's committed evidence.
