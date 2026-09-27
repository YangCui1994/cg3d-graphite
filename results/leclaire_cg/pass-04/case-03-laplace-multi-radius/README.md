# laplace-multi-radius

## Case identity
```text
Case ID:            case-03
Case name:          laplace-multi-radius
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      a12c14f553c5a03a815dbfc96d5aa09a6f33083e
Physical target:    Laplace law and sigma calibration at larger radii
Reference/theory:   Delta p = 2 sigma / R ; regress Delta p on 2/R
Verdict:            FAIL_SOLVER
```

## Setup

| item | value |
|---|---|
| domain size | (28, 28, 28) |
| lattice | D3Q19 |
| initial condition | spherical tanh droplet |
| solid geometry | none (periodic images must not interact) |
| boundary conditions | periodic |
| wetting convention | n/a |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 1000 steps per radius |
| snapshot times | one final snapshot per radius |

## Standard / reference result

Four resolved radii; radius measured from the final phase field as the equivalent-sphere radius. Free- intercept and zero-intercept fits are both reported, plus the local sigma_i and its 1/R trend.

```text
Delta p = 2 sigma / R ; regress Delta p on 2/R
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| sigma_fit (free intercept) | within 0.9-1.1x 0.02 | 0.02254 | 1.127x | FAIL |
| R^2 | > 0.95 | 0.99996 | - | ok |
| intercept | < 0.25x mean dp | -4.87e-04 | - | ok |
| sigma_zero_intercept | - | 0.02082 | 1.041x | reported |
| sigma_extrapolated(1/R->0) | - | -0.00024 | -0.012x | reported |

## Interpretation boundary

**FAIL_SOLVER**

The +offset is an unresolved calibration result, not a gate to be tuned away. See MECHANICAL_SIGMA_DERIVATION.md.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
