# conservation

## Case identity
```text
Case ID:            case-10
Case name:          conservation
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      9773a439f9f994225ce6515bd9f755815aa2c5af
Physical target:    total and component mass conservation of the reference solver
Reference/theory:   total and component mass are invariants of the update
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | (8, 8, 24) |
| lattice | D3Q19 |
| initial condition | psi=-tanh((z-c)/2) |
| solid geometry | none |
| boundary conditions | periodic |
| wetting convention | n/a |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 1000 steps |
| snapshot times | final per arm |

## Standard / reference result

The paper's recolouring is mass-exact by construction (the rest population is untouched and sum_i W_i cos(theta_i) = 0); the project-style overlay is offered as a default-off arm and is never described as paper-faithful.

```text
total and component mass are invariants of the update
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| None total/step | < 1e-12 | 2.788e-13 | - | ok |
| f64_arithmetic total/step | < 1e-12 | 2.024e-14 | - | ok |

## Interpretation boundary

**PASS**

Scope: NumPy/f64 reference only; a Taichi/f32 port needs its own audit.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_f32_v2`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
