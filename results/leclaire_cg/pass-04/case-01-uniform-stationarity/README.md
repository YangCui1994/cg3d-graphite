# uniform-stationarity

## Case identity
```text
Case ID:            case-01
Case name:          uniform-stationarity
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      a12c14f553c5a03a815dbfc96d5aa09a6f33083e
Physical target:    stationarity of the single-phase equilibrium
Reference/theory:   sum_i N_i^eq = rho ; u stays 0
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | (8, 8, 8) |
| lattice | D3Q19 |
| initial condition | psi=+1, rho=1, u=0 |
| solid geometry | none (periodic) |
| boundary conditions | periodic |
| wetting convention | n/a (no wall) |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 400 steps |
| snapshot times | 0, 400 |

## Standard / reference result

A uniform single-phase state must be an exact fixed point of the update.

```text
sum_i N_i^eq = rho ; u stays 0
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| max \|v\| | < 1e-12 | 8.774e-14 | 8.774e-14 | ok |
| max \|Delta rho\| | < 1e-12 | 7.272e-14 | 7.272e-14 | ok |

## Interpretation boundary

**PASS**

f64 roundoff on every field; no drift.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
