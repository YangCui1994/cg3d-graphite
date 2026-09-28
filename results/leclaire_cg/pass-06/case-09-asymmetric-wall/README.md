# asymmetric-wall

## Case identity
```text
Case ID:            case-09
Case name:          asymmetric-wall
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      9773a439f9f994225ce6515bd9f755815aa2c5af
Physical target:    closed asymmetric wall: global mass integrity and wall-band behaviour
Reference/theory:   closed box: total and component mass conserved; no wall mass transfer without a driving force
Verdict:            FAIL_SOLVER
```

## Setup

| item | value |
|---|---|
| domain size | (28, 16, 16) |
| lattice | D3Q19 |
| initial condition | liquid in the lower half |
| solid geometry | one-sided overhang + floor, all four lateral faces closed (verified in code) |
| boundary conditions | no-slip solid; closed box |
| wetting convention | n/a (no prescribed angle in this case) |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 1500 steps |
| snapshot times | initial, intermediate, final |

## Standard / reference result

Global and component mass are gated on the maximum time-history excursion and on the late-window rate, so the solid-node reservoir fill is separated from real creation.

```text
closed box: total and component mass conserved; no wall mass transfer without a driving force
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| closed topology | yes | True | - | ok |
| max red excursion | < 0.02 | 2.749e-13 | 2.749e-13 | ok |
| late red rate | < 1e-06/step | -2.419e-13 | - | ok |
| wall-band red change | < 0.02 | -0.0683 | - | FAIL |

## Interpretation boundary

**FAIL_SOLVER**

The wall-band change is reported but NOT attributed to wall mass transfer: making that claim needs a stationary/no-driving reference, which this round does not include.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_f32_v2`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
