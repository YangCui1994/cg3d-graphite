# CHANGELOG — numerical changes

One entry per modification that can change simulation results
(Plan_20260919_v2, rule 2: separate commit + theory source + regression
test + before/after). Entries appended top-down, newest first.

Format:

```text
## YYYY-MM-DD <task-id> <one-line summary>   (commit <hash>)
- What changed (file:line)
- Theory source / reasoning
- Regression evidence (test + before/after numbers)
```

## 2026-09-19 PR-1 Instruments — report schema + diagnostics (no solver change)

- `run_common.py`: new `region_stats(rho, psi, v, mask)` (pure-numpy host
  helper; p = cs^2 rho).
- `run_pcs_cg3d.py` / `run_ir_cg3d.py`: `measure()` extended; ladder rows
  now carry `pc_nominal` (rename of `pc`), `pc_measured` (pore-band
  pressure difference inside each membrane, `--pc-band` default 4),
  `rho_in/out_mean`, `p_in/out_mean`, `u_rms`, `u_bulk_x`,
  `flux_r/b_rate` (trailing-window reservoir mass rates). Convergence
  logic (dS/dt slope) untouched — instrumentation only.
- `graphite_figs.py`: reads `pc_nominal` with fallback to legacy `pc`.
- Docs: `docs/BC_IC_OUTPUT.md` §3.1 (schema + pc_measured semantics).
- Regression evidence: smoke runs on synthetic 56x40x40 pore (empty box):
  reservoir pinning exact (rho_in 1.0500 / rho_out 0.9500 at d=0.10);
  gentle case d=0.02 quasi-steady: pc_measured 0.0139 vs pc_nominal 0.0067,
  difference 0.0072 ~ meniscus capillary jump 2*sigma/R (sigma=0.0606,
  R~20 lu) — instrument reads the sample-side pressure including the
  in-band interface jump, as designed. Files in results_pcs_cg3d/ are
  gitignored scratch; numbers recorded here.

## 2026-09-19 Phase 0 baseline frozen (no numerical change)

- Tag `baseline-pre-audit-2026-09` created; pre-audit results archived to
  `results/baseline/` (see `results/baseline/PROVENANCE.md` for revision +
  environment). requirements.txt pinned to the exact producing versions.
- No solver/driver code touched in this entry.
