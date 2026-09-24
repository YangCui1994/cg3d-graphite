# PROVENANCE — BI-SOLVER-CONSERVATION-FIX-001

## Binding

- **Task:** BI-SOLVER-CONSERVATION-FIX-001 (authorized solver
  conservation fix; contract
  `.agent/episodes/bilateral-imbibition-v0.1/SOLVER_CONSERVATION_FIX_CONTRACT.md`)
- **Product base:** `1f5ee76fa183b42dd0ffcb291f389c3f1974a147`
  (conservation-audit attempt-2 candidate)
- **Product branch:** `agent-task/BI-SOLVER-CONSERVATION-FIX-001`
- **Final candidate:** recorded in `REVIEW_REQUEST.md`; all artifacts in
  this directory are committed on that branch and SHA256-hashed in
  `MANIFEST.json`.

## Commit history on the branch (candidate changes inspectable)

| commit | content |
|---|---|
| `503f474` | candidate switches T0-T4/C0-C1 + T1 projection + inv_M_f64 + F0 probe + F0/F1 driver + search report + literature |
| `9bd922d` | F0 results (all candidates) + LBM_OUTROOT hooks in V1c/V2 drivers (defaults unchanged) |
| `46be3f2` | first selection T1+C1 as production default (later rejected by A2 — kept for history) |
| `e3d5a93` | **final selection T3 + scoped-C1** (C1 scoped to cc>0; rejection rationale in code comments) |
| final | evidence package (this file, EXECUTION_REPORT, CANDIDATE_COMPARISON, MANIFEST, summary.json, figures) |

## Producer

- **Solver:** `lbm_solver_cg3d.py` — the only production source modified
  (scope: tables + constructor switches + collision static branches +
  dbg probe; diff vs base is inspectable via
  `git diff 1f5ee76 <candidate> -- lbm_solver_cg3d.py`).
- **Drivers:** `tests/conservation_fix.py` (F0/F1), existing production
  drivers for F2/F3/F4 (`run_level_a.py`, `test_compute_c_bulk.py`,
  `test_poiseuille_cg3d.py`, `levelb_laplace.py`,
  `levelb_contact_angle.py`, `test_postprocessing.py`,
  `levelc_v1c.py`, `levelc_v2_bilateral.py` — the latter two with the
  `LBM_OUTROOT` env hook, default unchanged).
- **Batches:** `run_f1_batch.sh`, `run_f1_60k_batch.sh`,
  `run_final_batch.sh`, `run_collect_finish.sh` (exact commands,
  sequential, one process per run).

## Environment

- Windows 11, conda env `lbm`: python 3.10.21, taichi 1.7.4 (CUDA /
  CPU backends), numpy 2.2.6. GPU: RTX 5080.
- Candidate selection via `LBM_TOTAL_FIX` / `LBM_COLOUR_FIX` env (the
  same switches the constructor exposes); production default since
  `e3d5a93` is T3/C1 — env vars reproduce any candidate, `T0/C0`
  reproduces the pre-fix arithmetic exactly.

## Runs (all logs + exit codes in `logs/`; machine data per run dir)

| group | runs | notes |
|---|---|---|
| diagnosis | `diag_C3_gpu` (audit driver, 4k) + `inv_m_colsum_check` | contract section 4 reproduction |
| F0 | `f0_T0C0/T1C0/T2C0/T3C0/T4C0/T1C1/T2C1` (C1 unscoped variants) + `f0_T3C1s` (scoped) | C3+C1 geometries, 1500+40 steps |
| F1 20k | `f1_T0C0/T1C0/T2C0/T3C0/T2C1/T1C1_20k` | GPU |
| F1 60k | `f1_T0C0_60k`, `f1_T3C0_60k`, `f1_T1C1_60k` (rejected candidate, kept) , `f1_T3C1s_60k` | GPU |
| F1 CPU | `f1_T1C1_20k_cpu`, `f1_T3C1s_20k_cpu` | backend comparison |
| F2 | `f2_*_T0` and `f2_*_T3C1s` (6 suites x 2) + superseded `f2_*_T1C1` (A2 failure evidence) | before/after |
| F3 | `f3_static_h{26,40,60,80}`, `f3_dyn_h{26,40}_{s,2L}`, `f3_collect` (one early collect exit=1: static set incomplete, resolved) | `levelc_v1c_fix/` |
| F4 | `f4_v2_primary` | `levelc_v2_fix/v2_primary/` |

Non-zero exits, all explained: `f3_collect` #1 (missing static_h26 ->
completed the set and re-ran, exit 0); the first T1+C1 regression batch
was aborted when A2 failed (its completed logs are retained as
rejected-candidate evidence; partial output dirs removed).

## Caveats

- GPU atomic adds: run-to-run bit-exactness not guaranteed (production
  property); all comparisons use committed single-run evidence; the
  CPU/GPU matrix bounds realization dependence.
- Literature PDFs under `literature/` carry source URLs and access
  dates in `LITERATURE_AND_IMPLEMENTATION_SEARCH.md`.
