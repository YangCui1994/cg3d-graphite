# mechanical-sigma

## Case identity
```text
Case ID:            case-11
Case name:          mechanical-sigma
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      a12c14f553c5a03a815dbfc96d5aa09a6f33083e
Physical target:    mechanical surface tension for a planar interface
Reference/theory:   sigma = int (P_N - P_T) dn   with dPi_ab = (2/9) A |F| (n_a n_b - delta_ab)
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | (6, 6, 64) |
| lattice | D3Q19 |
| initial condition | psi=-tanh((z-c)/2.5) |
| solid geometry | none |
| boundary conditions | periodic |
| wetting convention | n/a |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 800 steps |
| snapshot times | final |

## Standard / reference result

See MECHANICAL_SIGMA_DERIVATION.md for the full derivation; the quadrature is a plain sum over nodes (dz = 1) after subtracting the bulk momentum-flux value.

```text
sigma = int (P_N - P_T) dn   with dPi_ab = (2/9) A |F| (n_a n_b - delta_ab)
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| sigma_mech | within 0.7-1.3x sigma_input | 0.01537 | ratio 0.768 | ok |

## Interpretation boundary

**PASS**

The derivation closes the prefactor from R1 Eqs. (16)-(18) and needs no collision/relaxation factor because the perturbation is applied to the distribution AFTER the collision and therefore enters the momentum flux directly.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
