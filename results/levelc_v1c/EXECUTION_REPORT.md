# EXECUTION REPORT — BI-V1C-CLOSURE-001 (attempt 2)

- Task: V1c closure per `V1C_CLOSURE_CONTRACT.md`, launched from
  `START_V1C.md`.  Attempt 1 reviewed CHANGES_REQUESTED (B1 aggregate
  contamination, B2 window filter); this attempt implements the
  prescribed correction by re-aggregation only — **no GPU rerun, no
  solver change, per-probe simulation evidence unchanged** (the same
  `reanalyze` production path recomputes every report from the
  committed `front.csv`/`probes.csv`).
- Base SHA: `a9c6db87da2eeb3572607152391fe6863394ebee`
- Producer chain: runs `032d273…` → collect fix `5f18caa…` → validity
  ladder `17bdb1b…`/`4d4dcb3…`+this fix (the candidate's file); all
  ancestors of this candidate, documented in `PROVENANCE.md`.
- Candidate: this commit.

## B1/B2 corrections (declared validity ladder)

Per-probe validity before ANY aggregate (`V0` 12-column bulk rule and
t-window → `V1` + x-window `x_ic_exit ≤ x_m ≤ x_stop` (B2) → `V2` +
band widths ≥ 20 columns (~9 interface widths) → `V3` gradient
consistency `0.5 ≤ |dp/dx|/G(V_meas) ≤ 2.0` on both bands, G from the
INDEPENDENT front fit).  V3 (gradient) is the PRIMARY; median AND mean
for every variant plus an `r2 ≥ 0.90` alternative are published in
`estimator_sensitivity.csv`.  Deviations from the review's illustrative
numbers, and why, are declared in the driver docstring: the 3h/4h
positional margins structurally empty the h40 short window
(`x_ic_exit = 122 > buf0 − 4h = 90`), and a pure-r² primary is
unsuitable because h40-short bulk-band fits sit at 0.85–0.90 r² even
at 100+ columns (committed `probes.csv`), while the gradient criterion
excludes exactly the contaminated probes the review identified
(gradients 0.03×/4.3× analytic, `r2_gas` down to 0.002).

## Measured facts (primary = V3 gradient, median)

### Differential hydraulics (primary gates)

| h | `L_eff1`→`L_eff2` (L 241→477) | `a_h` | gate | `L0` | `L0/h` |
|---|---|---|---|---|---|
| 26 | 331.5→578.5 | **1.0436** | **PASS** (4.4%) | 77.9 lu | 3.00 |
| 40 | 425.5→681.6 | **1.0699** | **PASS** (7.0%) | 157.5 lu | 3.94 |

Estimator sensitivity (`estimator_sensitivity.csv`, a_h per variant ×
median/mean): h26 = 1.039–1.059 across ALL variants (all PASS); h40 =
1.065–1.096 for every defensible variant (median or mean), while the
attempt-1 contaminated sets (`V0`/`V1` mean: 1.1206/1.1302) reproduce
the reviewer's FAIL diagnosis — the contamination is now isolated,
counted, and excluded explicitly.  Fully-valid probe counts:
22/35, 43/55, 13/25, 38/49.

### Static resolution convergence (unchanged from attempt 1)

`C_static` = 0.7902 / 0.7511 / 0.8067 / 0.7795 (h = 26/40/60/80),
θ = 37.80°/41.31°/36.22°/38.79°; all four runs reached declared Pc
stationarity (drift < 1e-3) at 19 750/12 500/12 000/13 000 steps.
Constant fit `C = 0.7819`, `resid_max = 0.031` (±3.9%); `over_h` R² =
0.007, `over_h2` R² = 0.0001 — no 1/h-type law supported
(non-monotonic h40 dip); the data support a reproducible, non-erratic
plateau `C ≈ 0.782 ± 0.031` (θ ≈ 38.6° ± 1.8°).  Plateau level is
method-conditional: threshold sensitivity reaches 1.03% at h80
(`Pc_thr095` vs 0.90), and the V1b↔V1c h26 shift (0.6705→0.7902, 18%)
reflects both the band-rule change AND a different slab/relaxation
protocol (V1b: nx=160, slab [60,100), fixed bands; V1c: nx=240, slab
[90,150), bulk-column) — reported as method/protocol-conditional, not
fully attributed to the band rule alone.

### Front/stability gates (D)

All four dynamic cases `all_hard` PASS: no NaN, umax ≤ 0.12, reservoir
pinning exact, monotonic, valid windows, R2 = 0.99998–1.00000,
primary/secondary front speeds agree ≤ 2%, base-band fraction ≥ 0.94.
Front speeds reproduce V1b bit-comparably (4.9740e-3 / 5.5888e-3 /
3.0002e-3).  `Pc_dynamic` threshold sensitivity (0.85/0.90/0.95) of
the PRIMARY aggregates ≤ 0.6% — distinct from V1b's band-PLACEMENT
sensitivity (8–9%), which the bulk-column rule removed.

### Mass accounting (g9, reported)

Colour-mass closure vs reservoir bookkeeping: `closure_rel` =
4.9e-4–6.8e-4 across the four dynamic runs (attempt-1 report understated
this as ~1e-4); total colour-mass drift reconstructed from committed
closure/inj finals is 0.04–0.27% over 36 500–60 000 steps
(`mass_accounting` in summary.json).  No order-one leakage; reporting
only, per contract.

### g3 caveat (review non-blocking 4)

`g3_zero_dp` verifies reservoir pinning (deviations exactly 0), i.e. BC
application; the informative dynamical numbers are the recorded
`jump_in`/`jump_out` (19–49% of `Pc_dynamic`), reported per run.

## Commands (this attempt, no GPU)

```
levelc_v1c.py reanalyze --tag dyn_h26_s   (and _2L, h40_s, h40_2L)
levelc_v1c.py collect                     (exit 0)
```

## Suggested next action

Fresh review (attempt 2) of this candidate against
`V1C_REVIEWER_CONTRACT.md`; on PASS, the mandatory technical-document
update is executed from this candidate's committed evidence.
