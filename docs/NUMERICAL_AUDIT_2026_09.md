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
Launched 2026-09-19; results table to be filled from
`results_pcs_cg3d/pr6_{old,new}/report.json`.

| Metric | old | new | rel. change | Note |
| --- | --: | --: | ---: | --- |
| S_nw per rung (0.03 → 0.281) | pending | pending | | |
| entry rung | pending | pending | | |
| plateau S_nw | pending | pending | | |
| exit reasons | pending | pending | | |

Interpretation guide: differences concentrated at d ≥ 0.18 (ρ_out ≤
0.91) point at the Compute_C fix; differences anywhere else would be
unexpected (Guo inert, post-processing reported separately).

## 4. Full-scale reruns (pending GPU time; validation gates are green)

Commands (full X2b ladder, run from repo root, ~7.4 h each on the
RTX 5080):

```bash
python make_geo_buffer.py   # regenerates geo_graphite_228b14.npz if absent
python run_pcs_cg3d.py --geo geo_graphite_228b14.npz --tag gx2c_postaudit \
    --ds 0.03 0.04 0.055 0.074 0.1 0.135 0.182 0.245 0.281 \
    --psi-solid -0.68
python run_ir_cg3d.py --geo geo_graphite_228b14.npz --tag gx3c_postaudit \
    --ds-drain 0.03 0.055 0.074 --ds-imbibe 0.055 0.04 0.025 0.012 0.0 \
    --psi-solid -0.68
```

Comparison targets vs `results/baseline/`: σ/θ (already verified above),
entry Pc, drainage plateau, S_i, S_nr (continuous + binary), cluster
count, largest cluster (expect the periodic-merge change to LOWER
n_clusters and RAISE largest vs baseline — that is a reporting fix, not
a physics change).
