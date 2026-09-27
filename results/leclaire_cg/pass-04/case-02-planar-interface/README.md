# planar-interface

## Case identity
```text
Case ID:            case-02
Case name:          planar-interface
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      a12c14f553c5a03a815dbfc96d5aa09a6f33083e
Physical target:    planar interface stationarity
Reference/theory:   interface must not translate or dissolve
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | (6, 6, 32) |
| lattice | D3Q19 |
| initial condition | psi=-tanh((z-16)/2) |
| solid geometry | none |
| boundary conditions | periodic |
| wetting convention | n/a |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 1000 steps |
| snapshot times | 0, 1000 |

## Standard / reference result

The interface carries no driving force, so both its position and its phase amplitude must be stationary.

```text
interface must not translate or dissolve
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| position drift | < 0.5 lu | 0.0057 | 0.0057 | ok |
| amplitude ratio | > 0.95 | 0.999867 | 1.33e-04 | ok |

## Interpretation boundary

**PASS**

converged steady state; residual is f64-level.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
