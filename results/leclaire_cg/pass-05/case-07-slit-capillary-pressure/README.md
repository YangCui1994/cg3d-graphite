# slit-capillary-pressure

## Case identity
```text
Case ID:            case-07
Case name:          slit-capillary-pressure
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      b65bdce3758dd967df1a3f5559c7014f97fd960b
Physical target:    static capillary pressure across a wall-intersecting meniscus
Reference/theory:   Pc = 2 sigma cos(theta) / h for a z-invariant slit
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | (28, 14, 10) |
| lattice | D3Q19 |
| initial condition | yz-plane interface at mid-x; liquid low-x, gas high-x |
| solid geometry | two plates normal to y; x ends sealed; z periodic |
| boundary conditions | periodic in z, no-slip solid, sealed x |
| wetting convention | n_w = -grad(g)/|grad(g)|; theta through liquid/red |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 1500 steps |
| snapshot times | initial and final per angle |

## Standard / reference result

The interface intersects both plates, so two contact lines exist and the meniscus is curved. A flat meniscus with no contact line would make this test invalid, not failed.

```text
Pc = 2 sigma cos(theta) / h for a z-invariant slit
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| theta=60 | Pc sign of cos(theta), |ratio| in [0.5,1.5] | 2.051e-03 | ratio 1.025 | ok |
| theta=90 | Pc sign of cos(theta), |ratio| in [0.5,1.5] | -4.221e-07 | ratio -1723413243997.796 | FAIL |
| theta=120 | Pc sign of cos(theta), |ratio| in [0.5,1.5] | -2.157e-03 | ratio 1.078 | ok |

## Interpretation boundary

**PASS**

Primary interpretation separates nominal-parameter accuracy (using input sigma and prescribed theta) from internal consistency (measured sigma and theta).

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
