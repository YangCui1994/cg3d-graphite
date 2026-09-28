# contact-angle

## Case identity
```text
Case ID:            case-04
Case name:          contact-angle
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      9773a439f9f994225ce6515bd9f755815aa2c5af
Physical target:    static contact angle vs prescribed, frozen convention
Reference/theory:   measured theta_liquid = prescribed theta_c
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | (30, 30, 30) |
| lattice | D3Q19 |
| initial condition | hemispherical tanh blob on the wall |
| solid geometry | floor slab, 2 layers |
| boundary conditions | periodic + no-slip solid |
| wetting convention | n_w = +grad(g)/|grad(g)| = fluid -> solid; theta through liquid/red |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 1600 steps |
| snapshot times | initial and final per angle |

## Standard / reference result

Circle fit to the psi=0 contour in the (r,z) plane; the angle is read where the fitted circle meets the wall plane, through the liquid/red phase.

```text
measured theta_liquid = prescribed theta_c
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| theta=60 | within 15 deg | 65.19 | 5.19 | fit ok |
| theta=90 | within 15 deg | 95.70 | 5.70 | fit ok |
| theta=120 | within 15 deg | 129.40 | 9.40 | fit ok |

## Interpretation boundary

**PASS**

Convention frozen by WETTING_PHASE_CONVENTION.md; the sessile droplet consumes it and does not choose it.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_f32_v2`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
