# axis-symmetry-isotropy

## Case identity
```text
Case ID:            case-06
Case name:          axis-symmetry-isotropy
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      b65bdce3758dd967df1a3f5559c7014f97fd960b
Physical target:    equal-wavelength x/y axis symmetry of interface dynamics
Reference/theory:   equal-wavelength x and y waves must evolve identically
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | [32, 16, 16] and [16, 32, 16] |
| lattice | D3Q19 |
| initial condition | sinusoidal interface, lambda=16 lu in both arms |
| solid geometry | none |
| boundary conditions | periodic |
| wetting convention | n/a |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | 0.7 |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 600 steps |
| snapshot times | initial and final per arm |

## Standard / reference result

The domain is rotated with the wave so both arms have the same lattice wavelength; the tracked quantity is the interface-height Fourier mode, not an averaged field maximum.

```text
equal-wavelength x and y waves must evolve identically
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| equal wavelength | yes | 16.0 vs 16.0 | - | ok |
| amplitude asymmetry | < 0.05 | 1.589e-13 | 1.589e-13 | ok |

## Interpretation boundary

**PASS**

Scope limited to axis symmetry on a cubic lattice; a rotated/diagonal case would be needed to claim general rotational isotropy.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
