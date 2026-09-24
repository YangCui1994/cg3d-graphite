# PROVENANCE — BI-V1C-CLOSURE-001

## Producer chain

| Revision | Content | Role |
|---|---|---|
| `032d273…` | `tests/levelc_v1c.py` (initial driver, unit-tested bulk-column rule) | **producer of all 8 primary runs** (their `prov.run_head` records it) |
| `5f18caa…` | same file + collect-only fix (2-D design matrix for the constant convergence fit) | producer of the `collect` outputs (tables/summary/MANIFEST); static/dynamic code paths identical to `032d273` |
| this commit | `results/levelc_v1c/**` only | final candidate; `tests/levelc_v1c.py` byte-identical to `5f18caa` |

Every `report.json` embeds `prov` (producer path, producer sha256,
run_head, exact command with interpreter, started_at, worktree_dirty,
exit_code); every CSV has a `<name>.prov.json` sidecar with the same
fields plus the artifact sha256.  `MANIFEST.json` mirrors per-run
shell exit codes and hashes every artifact.  Console logs:
`logs/<tag>.log` + `logs/<tag>.exit`.

The `collect` outputs (static_table / differential_table / gates /
summary / MANIFEST) are derived tables computed from the committed
per-run `report.json` files at `5f18caa…`; those inputs were produced
at `032d273…`.  Both revisions are ancestors of the final candidate
and the driver file in the candidate is byte-identical to the last
producer, so every artifact binds unambiguously to committed code.

## Runs (product worktree, GPU/CUDA, conda env `lbm`, python 3.10.21 /
taichi 1.7.4)

| Tag | Shell exit | Ended |
|---|---|---|
| static_h26 / h40 / h60 / h80 | 0 | Pc stationary (drift < 1e-3) at 19 750 / 12 500 / 12 000 / 13 000 steps |
| dyn_h26_s | 0 | x_stop at 40 250 |
| dyn_h26_2L | 0 | steps_cap 60 000 |
| dyn_h40_s | 0 | x_stop at 36 500 |
| dyn_h40_2L | 0 | steps_cap 60 000 |
| collect | 0 | summary/tables/MANIFEST |

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
