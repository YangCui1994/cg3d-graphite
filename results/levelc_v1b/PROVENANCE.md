# PROVENANCE — BI-V1B-DIAGNOSTIC-001

Every primary artifact under `results/levelc_v1b/` is bound to the
producer below.  `MANIFEST.json` carries the machine-readable form
(sha256 per artifact, per-run command / head / timestamps / exit codes).

## Producer chain

| Revision | Content | Role |
|---|---|---|
| `cd5986b…` | `tests/levelc_v1b.py` (initial driver) | committed BEFORE any run; superseded within minutes, no run used it |
| `da9a13d…` | `tests/levelc_v1b.py` (records real interpreter path in `prov`) | **producer of every run**; file sha256 `f66aabb236281b00…` |
| this commit | `results/levelc_v1b/**` only | final candidate; `tests/levelc_v1b.py` byte-identical to `da9a13d` |

Each `report.json` embeds `prov` with `run_head = da9a13d…`,
`producer_sha256 = f66aabb…`, exact `command` (real interpreter path),
`started_at`, `worktree_dirty=false`.  Each CSV carries a sidecar
`<name>.prov.json` with the same fields plus the artifact sha256.
Shell-level console logs and exit codes live in `logs/*.log` /
`logs/*.exit` and are mirrored in `MANIFEST.json::runs`.

## Runs (all from the product worktree, GPU/CUDA backend, conda env `lbm`)

| Tag | Command (interpreter abbreviated) | Shell exit | Ended |
|---|---|---|---|
| static_h26 | `lbm/python tests/levelc_v1b.py static --hy 26 --tag static_h26` | 0 | steps_cap 60 000 |
| static_h40 | `lbm/python tests/levelc_v1b.py static --hy 40 --tag static_h40` | 0 | steps_cap 60 000 |
| dyn_h26 | `lbm/python tests/levelc_v1b.py dynamic --hy 26 --tag dyn_h26` | 0 | x_stop at 40 250 |
| dyn_h40 | `lbm/python tests/levelc_v1b.py dynamic --hy 40 --tag dyn_h40` | 0 | x_stop at 36 500 |
| dyn_h26_2L | `lbm/python tests/levelc_v1b.py dynamic --hy 26 --L 472 --tag dyn_h26_2L` | 0 | steps_cap 60 000 |
| (collect) | `lbm/python tests/levelc_v1b.py collect` | 0 | summary/budget/gates/MANIFEST |

Environment: python 3.10.21 / taichi 1.7.4 (cuda), Windows.  Fixed
parameters in every run: `CapA=0.06`, `sigma=1.012·CapA`,
`nu_l=nu_g=0.1`, `rho0=1`, `psi_solid=-0.68`, z-periodic slit,
`mu = nu·rho0 = 0.1`.

## Derived artifacts binding rule

No figures are committed.  All committed numerical artifacts (CSV,
JSON, final-field `npz`) were written by `tests/levelc_v1b.py` at
revision `da9a13d…` during the runs listed above; that exact file is
byte-identical in this candidate, so every artifact is unambiguously
bound to the committed producer revision.  `EXECUTION_REPORT.md`,
`PROVENANCE.md` and `MANIFEST.json` are metadata written after the
runs and cite the producer chain above.
