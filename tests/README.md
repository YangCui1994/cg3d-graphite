# tests/ — physics regression suite (Plan_20260919_v2, Phase 3 / PR-4)

## Levels

| Level | What | When | Files |
| --- | --- | --- | --- |
| A | structural sanity, seconds each | before every commit | `run_level_a.py` |
| B | numerical algorithm regression, minutes | after any solver change, before merges | `levelb_laplace.py`, `levelb_contact_angle.py`, `test_poiseuille_cg3d.py`, `test_compute_c_bulk.py` |
| numpy | post-processing / docs logic, no solver | any time | `test_postprocessing.py` |
| C | full benchmarks (Finney / graphite) | GPU, manual, not CI | parent-repo drivers + `run_pcs_cg3d.py` / `run_ir_cg3d.py` |

## Run

```bash
python tests/run_level_a.py            # A1-A5, one 32^3 instance
python tests/test_postprocessing.py    # 11 numpy checks
python tests/test_compute_c_bulk.py    # PR-2 1.1 regression
python tests/test_poiseuille_cg3d.py   # PR-2 1.2 regression (eff ~ 1.0)
python tests/levelb_laplace.py         # sigma vs 1.012*CapA, <3%, R2>=0.999
python tests/levelb_contact_angle.py   # theta(psi_solid=-0.68) ~ 30 +-6 deg
```

All exit non-zero on failure. Scratch outputs land in `tests_output/`
(gitignored).

## The Taichi JIT single-instance rule (machine-specific, mandatory)

Every `ColorGradientSolver3D` instance pays ~5.5 min JIT on this machine,
and a SECOND instance in the same process always misses the cache (the
cache key includes an instance counter). Therefore:

- each test file creates exactly ONE solver and re-initialises its fields
  between cases (`set_*` methods + `init` + host-side field resets);
- multi-case sweeps use a FIXED shape (e.g. `levelb_laplace.py` runs all
  radii at n=80 — the parent-repo original created a new solver per case);
- run test files as separate processes, never `import` one from another.

## Reference values (Level B tolerances, from the parent P-line)

| Quantity | Reference | Source |
| --- | --- | --- |
| sigma(CapA) | 1.012 x CapA | 13-droplet 3D Laplace fit, R^2 = 1.0000 |
| Guo eff factor | 1.0 (post PR-2 fix; was 0.330) | `test_poiseuille_cg3d.py` |
| theta_liq(psi_solid = -0.68) | ~30 deg | flat-plate registry, parent repo |
| k (S&A bound) | 0.98-1.04 | ordered/random pack P2 (parent, force-calibrated) |
| Finney drainage knee | C = 6.38 | parent P3 |
| P4 S_nr | 0.17-0.20 | parent repo |

Tolerances are recorded as percentages/absolute bands, never bitwise:
GPU atomics make f32 accumulation order nondeterministic.
