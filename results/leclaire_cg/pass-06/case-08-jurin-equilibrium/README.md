# jurin-equilibrium

## Case identity
```text
Case ID:            case-08
Case name:          jurin-equilibrium
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      9773a439f9f994225ce6515bd9f755815aa2c5af
Physical target:    closed-system equilibrium Jurin rise, connected geometry
Reference/theory:   dh = 2 sigma cos(theta) / (rho g h)
Verdict:            FAIL_SOLVER
```

## Setup

| item | value |
|---|---|
| domain size | (24, 16, 44) |
| lattice | D3Q19 |
| initial condition | psi=+1 for z<20.0 (channel, reservoir and capillary all full and topologically connected) |
| solid geometry | floor+ceiling; barrier at x=x_w above the channel; slit walls at y<wall and y>=ny-wall above the channel |
| boundary conditions | periodic lateral; no-slip solid; closed box |
| wetting convention | n_w=+grad(g)/|grad(g)| fluid->solid; theta through liquid/red |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | gravity fz=-0.00025 (R1 Eqs. 6-9) |
| precision/backend | numpy f64 |
| run length | 4000 steps |
| snapshot times | initial, intermediate, final |

## Standard / reference result

The reservoir free surface sits above the channel top, so the capillary entrance is submerged and the liquid column is connected at t=0. The precheck solves the volume balance for this exact topology and aborts as INVALID_CONFIGURATION if either interface leaves its measurable window.

```text
dh = 2 sigma cos(theta) / (rho g h)
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| predicted capillary meniscus | inside [8,42] | 24.36 | - | ok |
| predicted reservoir surface | above channel (8), inside [8,42] | 16.36 | - | ok |
| rise | within 0.5-1.5x theory | 1.000 | ratio 0.125 | FAIL |

## Interpretation boundary

**FAIL_SOLVER**

Connected closed-system equilibrium test; dynamic Washburn imbibition remains out of scope for this stage.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_f32_v2`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
