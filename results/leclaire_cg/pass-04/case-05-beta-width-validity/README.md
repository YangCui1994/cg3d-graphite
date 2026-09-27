# beta-width-validity

## Case identity
```text
Case ID:            case-05
Case name:          beta-width-validity
Solver mode:        L17_CORE (NumPy/f64 reference)
Candidate SHA:      a12c14f553c5a03a815dbfc96d5aa09a6f33083e
Physical target:    beta controls interface width inside a positivity-bounded range
Reference/theory:   width(beta) monotone; |psi| <= 1 for a physical interface
Verdict:            PASS
```

## Setup

| item | value |
|---|---|
| domain size | (6, 6, 32) |
| lattice | D3Q19 |
| initial condition | psi=-tanh((z-c)/2) |
| solid geometry | none |
| boundary conditions | periodic |
| wetting convention | n/a |
| nu | 0.16666666666666666 |
| sigma | 0.02 |
| beta | swept |
| forcing | none |
| precision/backend | numpy f64 |
| run length | 600 steps |
| snapshot times | final per beta |

## Standard / reference result

An order parameter outside the component-fraction range is an over-sharpening warning and is excluded from the valid set.

```text
width(beta) monotone; |psi| <= 1 for a physical interface
```

## Actual result

| quantity | expected | measured | error/residual | status |
|---|---:|---:|---:|---|
| beta=0.0 | |psi|<=1 and separated | 0.0573 | width 20.000 | EXCLUDED |
| beta=0.5 | |psi|<=1 and separated | 0.9970 | width 1.839 | valid |
| beta=0.7 | |psi|<=1 and separated | 0.9999 | width 1.469 | valid |
| beta=1.0 | |psi|<=1 and separated | 1.0000 | width 1.123 | valid |
| beta=1.5 | |psi|<=1 and separated | 1.0168 | width 0.665 | EXCLUDED |
| beta=2.0 | |psi|<=1 and separated | 1.1141 | width 0.405 | EXCLUDED |

## Interpretation boundary

**PASS**

Monotone response is reported only over the positivity-valid set; the tested beta range is not claimed to be the stability envelope.

## Artifacts

- `raw/` compressed raw fields (`l17c_core_raw_v1`)
- `figures/` PNG + SVG; regeneration paths in `render_manifest.json`
- `metrics.json` / `metrics.csv`
- `reproduce.py` re-runs this case from the frozen candidate
- `logs/` run log
