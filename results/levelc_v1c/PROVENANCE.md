# PROVENANCE — BI-V1C-CLOSURE-001 (attempt 2)

## Producer chain

| Revision | Content | Role |
|---|---|---|
| `032d273…` | `tests/levelc_v1c.py` (initial driver, unit-tested bulk-column rule) | **producer of all 8 primary runs** (their `prov.run_head` records it) |
| `5f18caa…` | collect-only fix (2-D design matrix) | collect outputs (attempt 1) |
| `17bdb1b…`/`4d4dcb3…`+ | validity ladder (B1/B2 correction) + `reanalyze` mode + collect variant fix | **attempt-2 aggregation**: reanalyze of the 4 dynamic runs + collect |
| this commit | `results/levelc_v1c/**` only | final candidate; `tests/levelc_v1c.py` byte-identical to the last producer |

Attempt-2 rework changed NO simulation input: every dynamic report was
recomputed by `reanalyze` from the UNCHANGED committed
`front.csv`/`probes.csv` of the attempt-1 runs (same `analyze_dynamic`
production path; `prov_reanalysis` in each report records command,
run_head, producer sha256, timestamps; `MANIFEST.json` mirrors both the
original run provenance and the reanalysis entry).  Static runs are
untouched from attempt 1.

Every `report.json` embeds `prov`; every CSV has a
`<name>.prov.json` sidecar; console logs and shell exit codes live in
`logs/`.  New attempt-2 artifacts: `estimator_sensitivity.csv` and the
`validity_variants` / `mass_accounting` blocks in the reports/summary.

## Runs (product worktree, GPU/CUDA, conda env `lbm`, python 3.10.21 /
taichi 1.7.4)

| Tag | Shell exit | Ended |
|---|---|---|
| static_h26 / h40 / h60 / h80 | 0 | Pc stationary (drift < 1e-3) at 19 750 / 12 500 / 12 000 / 13 000 steps |
| dyn_h26_s | 0 | x_stop at 40 250 |
| dyn_h26_2L | 0 | steps_cap 60 000 |
| dyn_h40_s | 0 | x_stop at 36 500 |
| dyn_h40_2L | 0 | steps_cap 60 000 |
| collect (attempt 2) | 0 | summary/tables/estimator_sensitivity/MANIFEST |
| reanalyze ×4 (attempt 2) | 0 | no GPU; aggregation only |

Fixed physics everywhere: `CapA=0.06`, `sigma=1.012·CapA`,
`nu_l=nu_g=0.1`, `rho0=1`, `psi_solid=-0.68`, z-periodic slit,
equal-pressure reservoirs, V1b boundary topology unchanged
(mem/reservoir/buffer x-indices identical to V1b; see `layout` in each
dynamic report and `static` domains nx=240, slab [90,150)).

## Derived-artifact rule

No figures committed on the product branch.  The SVG figures required
by the V1c contract section F are generated on the CONTROL branch from
this committed numeric evidence by a committed script, with the
candidate SHA in the caption.
