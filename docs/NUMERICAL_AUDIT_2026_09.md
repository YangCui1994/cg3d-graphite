# NUMERICAL AUDIT 2026-09 — cg3d-graphite

Plan_20260919_v2 Phase 5 deliverable. Compares the pre-audit baseline
(tag `baseline-pre-audit-2026-09`, archived reports in
`results/baseline/`) against the post-audit code (PR-1..PR-5) on the
validation ladder. **No assumption that new ≈ old** — differences are
attributed to specific modifications via the PR granularity
(see `docs/CHANGELOG_NUMERICS.md`).

## 1. What changed numerically (summary; details in ADR-001 / CHANGELOG)

| Change | Commit | Affects |
| --- | --- | --- |
| Compute_C bulk criterion normalized (\|ψ\|>0.9) | pr2.1 | pure-phase cells at ρ≠1 next to solid: the high-\|d\| rungs of reservoir-driven ladders (ρ_out = 1−d/2 < 0.91 for d ≥ 0.18) |
| Guo force weights 3/9 restored | pr2.2 | force-driven runs only (F = 0 in X2/X3 ⇒ zero effect) |
| periodic cluster merge + conn parameterisation | pr3 | reported n_clusters / largest for I–R finals (post-processing only) |
| dual saturation + multi-indicator convergence records | pr1/pr3 | report fields only |

## 2. Validation ladder (Level A / B, all green 2026-09-19)

| Gate | Result | Before the fix |
| --- | --- | --- |
| Level A suite (5 checks) | ALL PASS (8 s) | — |
| Poiseuille (Guo) | eff = 0.9933, L2 = 0.0075 | eff = 0.3322, L2 = 0.67 |
| Laplace σ(CapA=0.06) | 0.0609 vs 1.012·CapA = 0.0607 → **0.32 %**, R² = 1.00000, anisotropy 0.15 % | identical expected (ρ≈1 invariant) |
| Contact angle θ(ψ_solid=−0.68) | 31.0° (registry 30 ± 6) | identical expected (ρ≈1 invariant) |
| Compute_C density-independence | PASS (4 cases) | case ρ=0.89 failed (\|C\|=0.15) |
| Poiseuille/mass/membrane/reservoir (Level A) | PASS | — |

**Conclusion of the correctness gates:** the two PR-2 fixes are
calibration-preserving where they must be (σ, θ at ρ ≈ 1) and
corrective where the old code was provably wrong (forcing magnitude,
density-dependent suppression).

## 3. Reduced-scale graphite drainage: old vs new (same geometry, same ladder)

Setup: `geo_graphite_228b14.npz`, ψ_solid = −0.68, CapA = 0.06,
reduced 5-rung ladder ds = {0.03, 0.055, 0.10, 0.182, 0.281}
(entry→plateau subset of X2b), equil 8k, rung caps 6k/20k, qs-window 8k.
Old = baseline tag in a git worktree; new = master (post PR-5).
Run 2026-09-19, both codes, same geometry file; reports archived as
`results/data/pr6_{old,new}_drain_report.json`.

| d | S_nw old | S_nw new | ΔS_nw | reason old | reason new |
| --- | --- | --- | --- | --- | --- |
| 0.030 | 0.0365 | 0.0362 | −0.0003 | max-steps | max-steps |
| 0.055 | 0.0756 | 0.0731 | −0.0025 | max-steps | max-steps |
| 0.100 | 0.1818 | 0.1732 | −0.0085 | max-steps | max-steps |
| 0.182 | 0.4141 | 0.3981 | −0.0160 | max-steps | max-steps |
| 0.281 | 0.6420 | 0.6303 | −0.0118 | max-steps | max-steps |

- entry rung identical (d = 0.100 in both); plateau (last rung)
  −1.83 % relative; sentry leaks equal to 2 digits (leak_r 4.2e-4 both).
- All rungs hit the step cap in BOTH codes (reduced ladder, still
  draining at cap: flux_r ≈ 8.9 mass/step at the top rung) — the
  comparison is between equal-length transients, not quasi-steady ends.
- Attribution: differences are negligible at ρ ≈ 1 (d ≤ 0.055, outlet
  ρ ≥ 0.97) and grow systematically with d — exactly the footprint of
  the Compute_C fix (pr2.1), the only modification that acts where
  ρ ≠ 1. Direction: the corrected suppression removes spurious wall
  currents that had slightly aided red invasion. Guo fix is inert
  (F = 0); post-processing fields are new-only (pc_measured 0.0242 at
  the top rung reflects the mid-invasion pressure state, meaningful
  only at quasi-steady).
- Caveat: reduced ladder, single seed-geometry, transient rungs — the
  definitive numbers are the full-scale reruns in §4.

## 4. Full-scale X2 rerun (complete) and X3 rerun

X2 commands (baseline ladder, run 2026-09-19/20, `gx2c_postaudit`):

```bash
python run_pcs_cg3d.py --geo geo_graphite_228b14.npz --tag gx2c_postaudit \
    --ds 0.03 0.04 0.055 0.074 0.1 0.135 0.182 0.245 0.281 \
    --psi-solid -0.68
```

### X2 drainage: baseline (gx2b) vs post-audit (gx2c)

| d | S_nw base | S_nw new | ΔS | rel | reason base | reason new | steps base | steps new |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.030 | 0.0393 | 0.0385 | −0.0008 | −2.1 % | quasi-steady | quasi-steady | 25000 | 24000 |
| 0.040 | 0.0978 | 0.0750 | −0.0228 | −23.3 % | quasi-steady | quasi-steady | 83500 | 48500 |
| 0.055 | 0.2984 | 0.2671 | −0.0313 | −10.5 % | max-steps | max-steps | 150000 | 150000 |
| 0.074 | 0.5721 | 0.5407 | −0.0314 | −5.5 % | max-steps | max-steps | 150000 | 150000 |
| 0.100 | 0.6284 | 0.6172 | −0.0113 | −1.8 % | quasi-steady | quasi-steady | 46500 | 55500 |
| 0.135 | 0.6542 | 0.6411 | −0.0131 | −2.0 % | quasi-steady | quasi-steady | 31000 | 28500 |
| 0.182 | 0.6706 | 0.6565 | −0.0141 | −2.1 % | quasi-steady | quasi-steady | 18000 | 17000 |
| 0.245 | 0.6796 | 0.6661 | −0.0135 | −2.0 % | quasi-steady | quasi-steady | 15000 | 15000 |
| 0.281 | 0.6837 | 0.6706 | −0.0132 | −1.9 % | quasi-steady | quasi-steady | 15000 | 15000 |

- **Entry rung identical (d = 0.055); plateau −1.93 % relative
  (0.6706 vs 0.6837) — matching the reduced-scale estimate (−1.83 %).**
- equil S_nw identical (0.0190); sentry same magnitude (leak_r 2.7e-3
  vs 2.8e-3); exit-reason pattern identical (same rungs hit the caps).
- Largest relative change at d = 0.040 (−23 %, −0.023 absolute): the
  early-invasion rung, where the front sweeps along solid walls and the
  Compute_C fix removes spurious wall currents — same attribution as
  the reduced pair, amplified in the invasion-knee region (0.04–0.074).
- New-only diagnostics: pc_measured runs [−0.001 → 0.023 → 0.010]
  across the ladder (nonzero where invasion is active, small drift at
  plateau — the last rung passes saturation/flux/kinetic but not yet
  the 1 % pressure criterion); flux_r ≈ −0.56 mass/step at the plateau
  rung. The band pressures mix both phases where menisci sit inside the
  bands, so pc_measured ≠ pc_nominal by construction (§3.1); full
  interpretation of its plateau value is left as a documented open
  diagnostic, not a physics claim.

### X3 imbibition-residual rerun (running)

```bash
python run_ir_cg3d.py --geo geo_graphite_228b14.npz --tag gx3c_postaudit \
    --ds-drain 0.03 0.055 0.074 --ds-imbibe 0.055 0.04 0.025 0.012 0.0 \
    --psi-solid -0.68
```

Comparison targets vs `results/baseline/`: S_i, S_nr (continuous +
binary), cluster count, largest cluster (expect the periodic-merge
change to LOWER n_clusters and RAISE largest vs baseline — that is a
reporting fix, not a physics change). Table to be filled on completion.
