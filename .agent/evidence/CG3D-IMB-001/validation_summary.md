# CG3D-IMB-001 — Validation Evidence Summary

This file is the durable record of executed validation evidence for the
direct-imbibition task family on `cg3d-graphite`. It complements (does
not replace) controller-side independent capture. All entries below
were actually executed on this machine; nothing unrun is reported as
passed.

- **Rework candidate commit:** `3eef436`
  ("fix(imb): CG3D-IMB-001-R1 rework — explicit real bounds, neutral
  gas metrics, IC QA figures", branch `agent-dev/direct-imbibition-step0`)
- **Parent candidate:** `9317924` (first implementation; its validation
  record lives in `.agent_runtime/execution_report.md`, not committed)
- **Execution environment:** Windows, `C:\Users\yangc\anaconda3\envs\lbm\python.exe`
  (Python 3.10.21, NumPy, matplotlib, Taichi 1.7.4 x64 CPU),
  `LBM_ARCH=cpu`, commands run from the repo root on the frozen commit
  (no source edits between the runs below and the commit).
- **Recorded:** 2026-09-21T15:03:57Z

Status vocabulary: PASS / FAIL / NOT_RUN / INCONCLUSIVE. Execution
class: NumPy / CPU solver / GPU smoke / static. Interpretation:
structural / regression / smoke / scientific. **No entry below is a
scientific/physical validation; no production GPU run was launched.**

---

## 1. Direct-imbibition layout tests (V1, V3, T1, T2, T3, T4, T5)

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> tests/test_direct_imbibition_layout.py` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | NumPy (+ matplotlib for T5c/d) |
| Key result | 37/37 checks. T1: explicit real bounds stay `[16,32)` although the first solid plane is x=18; `resolve_real_bounds` priority arg > npz `real_x` > None; malformed bounds rejected. T2: prewet N=4/10 counted from x=16 (all-pore planes 16–17 liquid); imbibition without bounds raises with guidance. T3: all-open drainage builds (`x_real=None`). T4 static scan: `gas_saturation_real/dom` present, no `s_nr`/`label_periodic`/`--conn`, deferral stated. T5: `phase_fractions` == independent recomputation; 5 figure files written. Drainage oracle D1–D4 byte-identical to pre-change statements. |
| Interpretation | structural + regression |
| Artifact | stdout (test prints per-check PASS lines); scratch figures under gitignored `tests_output/imb_figs/` |

## 2. Direct-imbibition runtime tests (V2 behavioural, V4, smoke §6.E, A0/A7)

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> tests/test_direct_imbibition_runtime.py` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | CPU solver (one Taichi instance, re-init between cases per the JIT rule) |
| Key result | A0: imbibition without real bounds fails BEFORE solver construction (ValueError, message names real_bounds/real_x). A1–A3, V4: left reservoir psi=−1 rho=1.0, right psi=+1 rho=1.0 at delta=0 (equal nominal densities). A4: solver psi after init == build_layout psi0. A7: `x_real=[16,32)` from npz real_x. B1–B3 smoke: 60 steps finite, psi∈[−1.004, 1.000], s_nw=0.662, umax=0.017. C1a/C2a: blocked-colour mass EXACTLY 0.0 (deterministic membrane bounce); C1b blue entered through mem_r (351.8), C2b red crossed mem_b outward (724.0). |
| Interpretation | structural + regression + smoke (NOT physical validation) |
| Artifact | stdout; synthetic geos in gitignored `tests_output/` |

## 3. Post-processing regression (shared diagnostics)

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> tests/test_postprocessing.py` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | NumPy |
| Key result | ALL PASS (11 checks, cg3d.diagnostics unchanged) |
| Interpretation | regression |

## 4. Level-A structural suite

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> tests/run_level_a.py` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | CPU solver |
| Key result | LEVEL A: ALL PASS (A1–A5, 13 s; solver untouched by this rework — belt-and-braces) |
| Interpretation | regression / structural |

## 5. Checkpoint / resume end-to-end (driver-level drainage + I-R regression)

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> tests/test_checkpoint_resume.py` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | CPU solver (real `run_pcs_cg3d.py` / `run_ir_cg3d.py` as subprocesses) |
| Key result | ALL PASS incl. full-vs-resumed trajectory match max&#124;Δpsi&#124; = 2.98e-07, rung s_nw diff 0.0, mid-rung crash recovery, ir cross-driver branch. Existing drainage/I-R semantics unchanged; their synthetic geo carries no `real_x` → also proves the drainage backward-compatibility path. |
| Interpretation | regression |
| Artifact | scratch outputs under gitignored `results_pcs_cg3d/ck_selftest*` |

## 6. Direct-imbibition driver smoke — npz real_x path

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> run_imbibition_cg3d.py --geo tests_output/imb_synth_geo_48.npz --tag imb_smoke_r1f --prewet-layers 4 --min-steps 15 --max-steps 30 --qs-window 15 --qs-tol 0 --every 5 --dump-every 0 --ckpt-every 0` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | CPU solver |
| Key result | 30 steps, exit by max-steps as configured; resolves real domain `[16,32)` from real_x; final line `gas_saturation_real=0.738 (dom 0.668); remaining gas, trapped-gas analysis NOT implemented`; `psi_ic.npz` + `ic.png` + report written. |
| Interpretation | smoke (NOT physical validation) |
| Artifact | gitignored `results_imb_cg3d/imb_smoke_r1f/` |

## 7. Direct-imbibition driver — missing-bounds error path

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> run_imbibition_cg3d.py --geo tests_output/imb_synth_geo_48_norx.npz --tag imb_err --prewet-layers 4 --max-steps 5 --every 5 --dump-every 0 --ckpt-every 0` |
| Result | **PASS** (fails exactly as designed) |
| Exit code | 1 |
| Execution class | CPU solver (fails pre-JIT, no solver constructed) |
| Key result | `ValueError: direct imbibition requires EXPLICIT real-domain bounds … Pass real_bounds=(lo, hi) or use a buffered geometry npz with the structured real_x=[lo,hi] field` |
| Interpretation | structural |
| Artifact | `tests_output/imb_err_log.txt` (gitignored) |

## 8. Direct-imbibition driver smoke — `--real-bounds` CLI override

| Field | Value |
|---|---|
| Command | `LBM_ARCH=cpu <python> run_imbibition_cg3d.py --geo tests_output/imb_synth_geo_48_norx.npz --tag imb_ovr_f --real-bounds 16 32 --prewet-layers 4 --min-steps 15 --max-steps 30 --qs-window 15 --qs-tol 0 --every 5 --dump-every 0 --ckpt-every 0` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | CPU solver |
| Key result | Same trajectory/metrics as the npz path (`gas_saturation_real=0.738 (dom 0.668)`), confirming explicit-arg priority end-to-end. |
| Interpretation | smoke |
| Artifact | gitignored `results_imb_cg3d/imb_ovr_f/` |

## 9. Production geometry explicit bounds (NumPy check)

| Field | Value |
|---|---|
| Command | `<python> -c "from cg3d.protocol import resolve_real_bounds; import numpy as np; print(resolve_real_bounds(np.load('geo_graphite_228b14.npz')))"` plus per-N `build_layout` zone checks (inline script, repo root) |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | NumPy |
| Key result | `real_x -> (14, 214)` exactly as documented. prewet=2: liquid pores `[3,16)`, gas `[16,214)`; prewet=6: liquid `[3,20)`, gas `[20,214)`; all solid nodes psi=0; prewet-zone pore cells 36 371 / 107 552. The shipped npz `solid` array is byte-identical to the pre-rework file (sha256 `45fab2c9cfd8b3da…` before and after the in-place `real_x` addition; the npz itself is gitignored/untracked, so the field exists in the local production file and in regenerations via the updated `make_geo_buffer.py`). |
| Interpretation | structural |

## 10. Initial-state QA figures (task §6)

| Field | Value |
|---|---|
| Command | `<python> -m cg3d.ic_figs --geo geo_graphite_228b14.npz --prewet 2 6 --out .agent/evidence/CG3D-IMB-001/figures` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | NumPy |
| Key result | 5 files written (see list below), built from the SAME `build_layout` the solver uses (verified by T5a: plotted `phase_fractions` equal an independent recomputation from the layout arrays). |
| Interpretation | structural (QA evidence) |

Committed figures (`.agent/evidence/CG3D-IMB-001/figures/`):

- `initial_state_profile_prewet_2.png` — x-plane liquid/gas/solid fractions, N=2
- `initial_state_profile_prewet_6.png` — same, N=6
- `initial_state_slice_prewet_2.png` — central x-z slice, N=2
- `initial_state_slice_prewet_6.png` — same, N=6
- `initial_state_compare.png` — both N side by side

**prewet_layers = 2 and 6 are QA example values only — neither is
physically validated, and no value is claimed as preferred.**

## 11. Figure rendering sanity scan

| Field | Value |
|---|---|
| Command | inline PIL/Numpy scan (per figure: non-blank std, dark text/marker pixel count, blue-dominant pixels left half > right half, red-dominant right > left) |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | NumPy |
| Key result | all 5 figures OK (e.g. profile N=6: blue L/R = 16 056/603, red L/R = 49 958/71 077, dark pixels 15 584); N=6 shows more blue than N=2 as intended. A zai-vision visual pass was attempted first but timed out (known tool flakiness); the pixel scan is the deterministic fallback. |
| Interpretation | structural |

---

## NOT_RUN entries

| Validation | Result | Reason |
|---|---|---|
| Full production 200³/228³ GPU campaign (direct imbibition on real graphite) | NOT_RUN | forbidden by task (CG3D-IMB-001-R1 §R3 / §8); no physical convergence claim is made anywhere |
| `levelb_laplace.py`, `levelb_contact_angle.py`, `test_poiseuille_cg3d.py`, `test_compute_c_bulk.py` | NOT_RUN | solver numerics (`lbm_solver_cg3d.py`) untouched by this rework — changes are confined to protocol layout, driver, figures, tests; these suites were green at the parent candidate `9317924` and nothing in them changed |
| Physical validation of any `prewet_layers` value; trapped-gas (outlet-connectivity) analysis | NOT_RUN / not implemented | reserved human decisions (see task §9); `trapped_gas_analysis='NOT_IMPLEMENTED'` recorded in the driver report |

## Environment note for reproduction

`<python>` above = `C:\Users\yangc\anaconda3\envs\lbm\python.exe`.
Test files are standalone scripts (repo convention): run each as its
own process; the runtime test deliberately creates exactly ONE Taichi
solver instance (machine JIT-cache rule, tests/README.md).
