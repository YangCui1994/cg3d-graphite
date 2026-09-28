# jurin-equilibrium

## Case identity
```text
Case ID:            case-08
Case name:          jurin-equilibrium
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      b65bdce3758dd967df1a3f5559c7014f97fd960b
Physical target:    closed-system equilibrium Jurin rise
Reference/theory:   dh = 2 sigma cos(theta) / (rho g h)
Verdict:            FAIL_SOLVER
```

## Setup

| item | value |
|---|---|
| domain size | (20, 16, 48) |
| lattice | D3Q19 |
| initial condition | liquid fills z<14 in the reservoir and z<20 in the capillary (a connected column inside the capillary) |
| solid geometry | floor+ceiling solid; slit walls for z>=18 |
| boundary conditions | periodic lateral; no-slip solid; closed box |
| wetting convention | n_w=-grad(g)/|grad(g)|; theta through liquid/red |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | gravity fz=-0.0003 (R1 Eqs. 6-9) |
| precision/backend | numpy f64 |
| run length | 4000 steps |
| snapshot times | initial, intermediate, final |

## Standard / reference result

Equilibrium rise of the capillary meniscus above the flat reservoir level. The initial condition already places liquid inside the capillary, and the reachability precheck aborts as INVALID_CONFIGURATION if the predicted equilibrium leaves the measurement window.

```text
dh = 2 sigma cos(theta) / (rho g h)
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| predicted capillary level | inside [18,46] | 21.56 | - | ok |
| rise | within 0.5-1.5x theory | nan | ratio nan | FAIL |

## Interpretation boundary

**FAIL_SOLVER**

Closed-system equilibrium test; dynamic Washburn imbibition is out of scope for this stage.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
