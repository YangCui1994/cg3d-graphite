# CG3D-IMB-002 — Production-Geometry Pilot Validation Evidence

Executed-evidence record for the bounded direct-imbibition pilot
(prewet_layers = 4 / 2 / 6, 10,000-step horizon) on the real buffered
graphite geometry. Nothing unrun is reported as passed.

- **Source commit used by ALL pilot runs:** `ef13a4d`
  (branch `agent-dev/direct-imbibition-pilot`; the solver/protocol/
  driver tree is identical to the accepted Step-0 candidate `3eef436`
  — `git diff 3eef436..ef13a4d` touches only `.agent/` documents).
  The analysis helper `imb_pilot_figs.py` (committed in the evidence
  commit) was used ONLY post-hoc on saved outputs; it does not enter
  any simulation path.
- **Execution environment:** Windows, RTX 5080 (CUDA, Taichi 1.7.4),
  `C:\Users\yangc\anaconda3\envs\lbm\python.exe`, GPU arch (driver
  default; `LBM_ARCH` unset), runs launched sequentially, one case at
  a time.
- **Recorded:** 2026-09-21.

> **10,000 steps is a bounded pilot horizon, NOT a convergence
> criterion.** No case below is claimed converged, and no remaining gas
> is claimed trapped (remaining gas ≠ trapped gas in this open system;
> outlet-connectivity analysis is not implemented).

---

## 0. Geometry gate (executed BEFORE any GPU run)

| Field | Value |
|---|---|
| Command | inline NumPy check (repo root) + driver startup lines |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | NumPy / static |
| Key result | `geo_graphite_228b14.npz` exists; shape `(228, 200, 200)` int8 (expected buffered production dimensions); structured `real_x = [14, 214]` present via `resolve_real_bounds`; `solid` sha256 prefix `45fab2c9cfd8b3da` (byte-identical to the accepted baseline geometry); real-region porosity 0.4475 (matches the documented graphite-region phi); buffer slabs x∈[12,14) and [214,217) all open pore. No regeneration needed; real bounds NEVER inferred from solid occupancy. Each run's console log additionally confirms `real structure x=[14,214)` from the structured field. |
| Interpretation | structural (gate) |

## 1. Pilot case N=4 (run order 1)

| Field | Value |
|---|---|
| Command | `<python> run_imbibition_cg3d.py --geo geo_graphite_228b14.npz --tag imb_pilot_n4 --delta 0 --prewet-layers 4 --psi-solid -0.68 --capa 0.06 --min-steps 10000 --max-steps 10000 --every 500 --dump-every 1000 --ckpt-every 0` |
| Result | **PASS** |
| Exit code | 0 |
| Steps reached | exactly 10,000 (`reason: max-steps`, the configured horizon) |
| rho / psi finite | yes — all report diagnostics finite (`s_nw`, `s_nw_binary`, `umax_last`, `rho_in/out_mean`, `u_rms`) and `final.npz` psi all finite |
| umax | max representative (last sample) 0.0291 (cap 0.12; no umax-cap termination) |
| Final `gas_saturation_real` | 0.9484 (continuous variant 0.9474) |
| Final `gas_saturation_dom` | 0.9300 |
| Local output directory | `results_imb_cg3d/imb_pilot_n4/` (gitignored; IC `psi_ic.npz`+`ic.png`, 10 frames + rung-end, `report.json`, `report_partial.json`, `final.npz`, `final.png`); console log `results_imb_cg3d/imb_pilot_n4_console.log` |
| Wall time | 475.6 s (~21 steps/s incl. frame I/O) |
| Boundary anomalies | none observed — pre-wet zone `[14,18)` liquid at IC, invasion front advanced monotonically +x (pore-basis liquid front x=17→22 over 10k steps), no NaN, no rough-boundary failure signature, no phase-direction reversal |

## 2. Pilot case N=2 (run order 2)

| Field | Value |
|---|---|
| Command | same as N=4 with `--tag imb_pilot_n2 --prewet-layers 2` |
| Result | **PASS** |
| Exit code | 0 |
| Steps reached | exactly 10,000 (`max-steps`) |
| rho / psi finite | yes (same audit basis as N=4) |
| umax | 0.0346 (last sample; no umax-cap) |
| Final `gas_saturation_real` | 0.9581 (continuous 0.9570) |
| Final `gas_saturation_dom` | 0.9393 |
| Local output directory | `results_imb_cg3d/imb_pilot_n2/` + `imb_pilot_n2_console.log` |
| Wall time | 475.8 s |
| Boundary anomalies | none observed (pre-wet `[14,16)`; front x=15→20) |

## 3. Pilot case N=6 (run order 3)

| Field | Value |
|---|---|
| Command | same as N=4 with `--tag imb_pilot_n6 --prewet-layers 6` |
| Result | **PASS** |
| Exit code | 0 |
| Steps reached | exactly 10,000 (`max-steps`) |
| rho / psi finite | yes (same audit basis) |
| umax | 0.0294 (last sample; no umax-cap) |
| Final `gas_saturation_real` | 0.9391 (continuous 0.9380) |
| Final `gas_saturation_dom` | 0.9211 |
| Local output directory | `results_imb_cg3d/imb_pilot_n6/` + `imb_pilot_n6_console.log` |
| Wall time | 475.8 s |
| Boundary anomalies | none observed (pre-wet `[14,20)`; front x=19→24) |

## 4. Cross-case trajectory evidence (post-processing)

| Field | Value |
|---|---|
| Command | `<python> imb_pilot_figs.py --geo geo_graphite_228b14.npz --run n2:results_imb_cg3d/imb_pilot_n2 --run n4:results_imb_cg3d/imb_pilot_n4 --run n6:results_imb_cg3d/imb_pilot_n6 --steps 0 1000 5000 10000 --out .agent/evidence/CG3D-IMB-002/figures` |
| Result | **PASS** |
| Exit code | 0 |
| Execution class | NumPy (deterministic post-processing of saved frames; explicit `real_x`; no solver) |
| Key result | binary `gas_saturation_real` vs step (frame psi quantised to ±0.005; t=0 from full-precision `psi_ic.npz`): step 0 / 1k / 2k / 5k / 10k — N=2: 0.9898/0.9830/0.9793/0.9710/0.9581; N=4: 0.9799/0.9732/0.9697/0.9615/0.9484; N=6: 0.9700/0.9637/0.9603/0.9519/0.9390. Liquid imbibed by 10k: 0.0318/0.0315/0.0309 (≈ identical); N=2−N=6 spread 0.0199 at t=0 vs 0.0190 at 10k — the difference stays ≈ the initial saturation offset. Pore-basis liquid front advances ≈ +5 lu in all three cases. Reservoir flux counters (10k steps): liquid injected ≈ +1.16e5, gas removed ≈ −8.8e4, `u_bulk_x` ≈ +5.5e-4 (net +x displacement) in all three. |
| Interpretation | smoke/pilot comparison — NOT physical validation, NOT trapped-gas analysis |

## 5. Figures (committed)

All under `.agent/evidence/CG3D-IMB-002/figures/`; generation commands
as in entries 4 and 6; each rendering-sanity scanned (non-blank,
expected colour composition).

| File | Content |
|---|---|
| `gas_saturation_real_vs_step.png` | early-time real-region gas saturation vs step, N=2/4/6; **both binary (solid lines) and continuous (dashed)** bases shown |
| `imbibition_slices_compare.png` | central x-z slices at steps 0 / 1,000 / 5,000 / 10,000 (rows = N; grey solid / blue liquid / red gas; real-domain bounds marked; +x arrow = invasion direction); all cases reached 10,000 so no "last available" substitution was needed |
| `final_phase_profile_compare.png` | x-plane liquid/gas/solid fractions at step 10,000 for N=2/4/6 over the whole membrane-interior domain — **buffer regions shown, not hidden**; membranes (dashed) and real bounds (solid/dotted black) marked |
| `initial_state_profile_prewet_{2,4,6}.png` | IC x-profiles per N (reference for separating the direct pre-wet offset from dynamic differences) |
| `initial_state_slice_prewet_{2,4,6}.png` | IC central slices per N |
| `initial_state_compare.png` | the three ICs side by side |

Initial-state figures were regenerated with the accepted tool:
`<python> -m cg3d.ic_figs --geo geo_graphite_228b14.npz --prewet 2 4 6
--out .agent/evidence/CG3D-IMB-002/figures`.

**prewet_layers = 2 / 4 / 6 are QA/sensitivity values only. None is
physically validated; none is claimed preferred.**

## 6. Figure rendering sanity scan

| Field | Value |
|---|---|
| Command | inline PIL/NumPy colour-composition scan over all committed figures |
| Result | **PASS** (after one iteration: the first `imbibition_slices_compare.png` rendered liquid in the gas colour bin — ListedColormap binning bug in the NEW analysis helper only, no simulation data affected; fixed, figure regenerated, blue liquid now present: 19,700 blue-dominant px) |
| Exit code | 0 |
| Execution class | NumPy |
| Interpretation | structural |

## NOT_RUN / out-of-scope

| Item | Status |
|---|---|
| Cases beyond the 10,000-step horizon; extended-time or rerun-until-quiet campaigns | NOT_RUN — outside the bounded pilot |
| Trapped-gas (outlet-connectivity) analysis of final states | NOT_RUN — not implemented by design (CG3D-IMB-001-R1 deferral); nothing here labels remaining gas as trapped |
| Full production direct-imbibition campaign; physical validation of any N | NOT_RUN — requires human modeling decisions (preferred N, horizon, outlet model) |

## Reproduction notes

`<python>` = `C:\Users\yangc\anaconda3\envs\lbm\python.exe`. Raw pilot
outputs stay in the gitignored `results_imb_cg3d/imb_pilot_n{2,4,6}/`
directories (frames, IC/final npz, reports, console logs); nothing
large is committed. Runs were launched sequentially on an idle GPU
(verified `nvidia-smi`: 0 % util, no CUDA processes before each launch).
