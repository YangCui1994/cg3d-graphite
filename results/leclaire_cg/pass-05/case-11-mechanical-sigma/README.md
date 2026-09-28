# mechanical-sigma

## Case identity
```text
Case ID:            case-11
Case name:          mechanical-sigma
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      b65bdce3758dd967df1a3f5559c7014f97fd960b
Physical target:    planar mechanical surface tension (exploratory)
Reference/theory:   sigma = int (P_N - P_T) dn with dPi_ab = (2/9) A |F| (n_a n_b - delta_ab)
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
| snapshot times | final (includes the full N_i field) |

## Standard / reference result

The integral is taken over a window containing exactly ONE interface (the periodic domain has two), with the bulk reference centred on the midpoint between them. The discrete total variation is reported as a consistency check against the continuum value 2.

```text
sigma = int (P_N - P_T) dn with dPi_ab = (2/9) A |F| (n_a n_b - delta_ab)
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| sigma_mech | band 0.7-1.3x | 0.02000 | ratio 1.000 | PASS |
| premises closed | yes | True | - | ok |
| discrete total variation | 2.0 | 2.0000 | 0.0% | ok |

## Interpretation boundary

**PASS**

premises closed and ratio inside the predeclared band. Mechanical sigma is EXPLORATORY by contract E8 unless the premises, the isolation of one interface and the recomputability of the observable are all closed.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
