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

## 2026-09-19 PR-3 — post-processing correctness (tasks 2.4-2.7)

- `run_common.py`: `label_periodic` (connectivity-parameterised CC with
  y/z seam union-find merge; the one-layer wrap-padding approach provably
  does NOT merge — pad copies get different labels) and
  `eval_convergence` (four-indicator quasi-steady record).
- Both drivers: `convergence` dict per rung (saturation_slope / pc_drift /
  phase_flux / u_rms_rel + criteria_passed + thresholds + exit reason),
  `--qs-mode sat|multi` (default sat = baseline-comparable exit rule;
  record always written), `s_nw_binary` alongside continuous `s_nw`.
- `run_ir_cg3d.py`: final cluster analysis via `label_periodic`
  (`--conn 6|18|26`, default 6 = legacy; periodic merge always on),
  `s_nr_continuous` + `cluster_topology` in the report.
- Regression: tests/test_postprocessing.py (11 checks, pure numpy, ALL
  PASS — connectivity split/merge, y and y+z seam rings, interior-only
  sizes, each convergence criterion failing in isolation); GPU smokes:
  run_ir multi-mode report carries the full record (exit=max-steps with
  saturation still drifting, pressure/flux/kinetic passed), run_pcs
  legacy sat-mode exits quasi-steady at S_nw=0.843 unchanged.
- NOTE: periodic merge changes n_clusters/largest vs the pre-audit X3
  numbers (splitting over-counted n); baseline archived in
  results/baseline/, difference quantified in Phase 5.

## 2026-09-19 PR-2 task 1.2 — Guo force weights restored (commit af2b2c5)

- `lbm_solver_cg3d.py` GuoF: added 1/cs² = 3 and 1/cs⁴ = 9 weights
  (Guo, Zheng & Shi 2002). Momentum injected per step was F/3 while the
  half-force velocity correction used F/2.
- Theory: lattice moment algebra (Σ e_x w[(e−u)·F] = cs²F_x) + Guo 2002
  moment-space forcing formula; ADR-001 §3.2.
- Regression: tests/test_poiseuille_cg3d.py — before: eff = 0.3322
  (matches 2D P2 measured 0.330), L2 = 0.67; after: eff = 0.9933,
  L2 = 0.0075. Drainage smoke (reservoir-driven, F = 0): S_nw 0.843
  unchanged, sentry ~3e-5. Force-driven k benchmarks from the parent repo
  divided by measured eff, so historical numbers remain valid.

## 2026-09-19 PR-2 task 1.1 — Compute_C bulk criterion normalized (commit d5b7808)

- `lbm_solver_cg3d.py` Compute_C: `abs(rho_r-rho_b) > 0.9` →
  `> 0.9*(rho_r+rho_b)` (i.e. |ψ| > 0.9).
- Theory: raw threshold is density-dependent; at the outlet side of
  reservoir-driven ladders rho = 1 − d/2 reaches 0.89 (d = 0.22 rung),
  where pure red failed the threshold and the spurious-current
  suppression silently turned off next to solid.
- Regression: tests/test_compute_c_bulk.py — before: case A failed
  (|C| = 0.15 at ρ = 0.89); after: PASS; interface cases bit-identical
  (ρ ≈ 1 invariance: σ = 1.012 CapA and θ registry untouched by
  construction).

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
