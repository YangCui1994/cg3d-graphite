# V1 evidence bundle — spontaneous capillary filling (Lucas-Washburn) in a straight slit

Stage: **BI-VALIDATION-001 / V1** (executor round 1).
Everything here was produced by `tests/levelc_imbibition.py` and the three
`tests/levelc_diag_*.py` diagnostics **without any solver change** — the
solver, drivers and geometry generators are byte-identical to the round base
commit (see the execution report for the base/candidate SHAs).

## Environment

| Item | Value |
|---|---|
| machine | Windows 10.0.26200, NVIDIA GeForce RTX 5080 (16303 MiB) |
| python | 3.10.21 (conda env `lbm`, `C:\Users\yangc\anaconda3\envs\lbm\python.exe`) |
| taichi | 1.7.4, `arch=cuda` (default `LBM_ARCH`), `offline_cache=True` |
| numpy | 2.2.6 |
| calibration reused | `CapA = 0.06` -> `sigma = 1.012*CapA = 0.06072`; `nu_l = nu_g = 0.1`; `psi_solid = -0.68` (theta_liq = 30 deg, registry) |

## Configuration (identical in every run below)

Straight slit, `h_y = 26` or `40` lu, **z periodic (6 layers)** so the
meniscus is exactly two dimensional, sealed on all other faces; open system:
liquid reservoir pinned at `(psi=-1, rho=1)`, inlet membrane `mem_r=1`
(blocks gas); gastight outlet membrane `mem_b=1` (blocks liquid) and gas
reservoir pinned at `(psi=+1, rho=1)`. Both baths are therefore at the same
nominal pressure: **zero imposed pressure difference**. Initial condition: a
wetting slug from the slit inlet to `x0 = 40`, non-wetting phase ahead.

Declared (pre-run) analytic relation for this configuration — matched
viscosity, so the two columns are in series and the total series resistance
is the full channel length:

    V = Pc*h_y^2/(12*mu*L_tot),  Pc = sigma*cos(theta)/b,  b = h_y/2,  mu = nu
    i.e. x(t) = x0 + V*t   (constant velocity; NOT x^2 ~ t)

## Commands run (all exit code 0)

| # | Command | Output |
|---|---|---|
| 1 | `python tests/levelc_imbibition.py --tag v1_h26 --steps 40000` | `v1_h26_*` |
| 2 | `python tests/levelc_imbibition.py --hy 40 --tag v1_h40 --steps 40000` | `v1_h40_*`, `v1_h40_run.log` |
| 3 | `DIAG_STEPS=8000 DIAG_EVERY=1000 python tests/levelc_diag_front.py` | `diag/front_profiles_h26.csv` |
| 4 | `DIAG_STEPS=20000 DIAG_EVERY=4000 python tests/levelc_diag_axial.py` | `diag/axial_profiles_h26.csv` |
| 5 | `DIAG_NX=508 DIAG_STEPS=16000 python tests/levelc_diag_lscan.py` | `diag/Lscan_series.csv` |

The diagnostics re-enter the production driver module
(`import levelc_imbibition`) and call the same `build()` / solver sequence /
`extract_front()` — they add read-only field dumps only.

## Files, sha256 (first 16 hex) and size

```
a0bc4027384cb8ce     15640  diag/axial_profiles_h26.csv
25d854f0f8f1caec     12929  diag/front_profiles_h26.csv
baa1f84de1257503       529  diag/Lscan_series.csv
99209b4bcdb29808    122092  fig_v1_h26.png
30fe205f2f37723d    132976  fig_v1_h40.png
07da2e0aa4a56bb1      3255  v1_h26_front.csv
3132f118fd372909      4667  v1_h26_probe.csv
3cb0c36255564514      3455  v1_h26_report.json
1244f25b5075c6dc      3258  v1_h40_front.csv
19cb0230ea17d91f      4648  v1_h40_probe.csv
df688f7b9bf5150d      4817  v1_h40_report.json
e91f1828835bcae1      4030  v1_h40_run.log
dd0fe243282c106f      3160  tests/levelc_diag_axial.py
8c981566ebee7561      2471  tests/levelc_diag_front.py
beb26a19958acb38      2468  tests/levelc_diag_lscan.py
fb732676f6933cfd     19888  tests/levelc_imbibition.py
```

Column meanings: `*_front.csv` = `step,x_vol,x_cross` (the front series,
sampled every 250 steps); `*_probe.csv` = the per-1000-step probes
(reservoir densities, band pressures, colour masses, the f64 injection
counters, `u_max`, `u_rms`); `*_report.json` = the driver's declared
relation, window indices, fitted slopes, gate numbers and all parameters;
`diag/*.csv` = axial (x) profiles of `psi`, `rho`, `v_x`, `|v|` at the end
of each diagnostic run; `Lscan_series.csv` = the front series of the
doubled-length case.

## Note on file locations

Because `.gitignore` excludes `tests_output/` and `*.npz`, the raw run outputs
(`series.npz` with the full time series plus the final `psi` field, and the
diagnostics' `.npz` profiles) stay untracked on the Windows machine under
`tests_output/levelc_imbibition/`; everything needed to reconstruct or
re-fit the results is committed here as CSV/JSON/PNG.
