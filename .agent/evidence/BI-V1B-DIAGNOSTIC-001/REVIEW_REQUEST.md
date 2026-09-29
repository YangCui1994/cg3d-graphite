# REVIEW REQUEST — BI-V1B-DIAGNOSTIC-001

- **Task ID:** BI-V1B-DIAGNOSTIC-001 (V1b diagnostic, per
  `.agent/episodes/bilateral-imbibition-v0.1/V1B_DIAGNOSTIC_CONTRACT.md`;
  launched from `.agent/episodes/bilateral-imbibition-v0.1/START_V1B.md`)
- **Product branch:** `agent-task/BI-V1B-DIAGNOSTIC-001`
- **Candidate SHA (exact):** `a9c6db87da2eeb3572607152391fe6863394ebee`
- **Base SHA:** `e9540bcadb86257c70b805afc98f2eec9626c64e`
- **Absolute product worktree path:**
  `D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-episode-worktrees\BI-V1B-DIAGNOSTIC-001`
- **Execution report:**
  `<worktree>/results/levelc_v1b/EXECUTION_REPORT.md`
- **Provenance:** `<worktree>/results/levelc_v1b/PROVENANCE.md`
  (machine-readable binding: `<worktree>/results/levelc_v1b/MANIFEST.json`)
- **Summary JSON:** `<worktree>/results/levelc_v1b/summary.json`

## Changed files (54, exact)

`tests/levelc_v1b.py` (new V1b driver; committed BEFORE the runs at
`cd5986b…`→`da9a13d…`, byte-identical in the candidate) and
`results/levelc_v1b/**` (53 new evidence files: per-run `report.json`,
`front.csv`, `probes.csv`, `axial_*.csv`, `static_series.csv`,
`fields_final.npz`, `.prov.json` sidecars, `logs/*.log|*.exit`,
`summary.json`, `pressure_budget.csv`, `gates.csv`, `MANIFEST.json`,
`EXECUTION_REPORT.md`, `PROVENANCE.md`).  Full list:
`git -C <worktree> diff --name-only e9540bca..a9c6db8`.
No other file changed; no solver source changed
(`lbm_solver_cg3d.py`, `cg3d/**`, V0 tests, V1 driver/results untouched).

## Primary run commands (exact; interpreter =
`C:\Users\yangc\anaconda3\envs\lbm\python.exe`)

```
tests/levelc_v1b.py static  --hy 26 --tag static_h26
tests/levelc_v1b.py static  --hy 40 --tag static_h40
tests/levelc_v1b.py dynamic --hy 26 --tag dyn_h26
tests/levelc_v1b.py dynamic --hy 40 --tag dyn_h40
tests/levelc_v1b.py dynamic --hy 26 --L 472 --tag dyn_h26_2L
tests/levelc_v1b.py collect
```

All shell exit codes 0 (`logs/*.exit`, mirrored in `MANIFEST.json`).
Producer revision of every run: `da9a13d…` (recorded in each
`report.json::prov.run_head` and in every `.prov.json` sidecar).

## Product worktree state

`git status --porcelain` is EMPTY — the product worktree is clean and
HEAD is exactly the candidate SHA above; the remote branch
`origin/agent-task/BI-V1B-DIAGNOSTIC-001` resolves to the same SHA
(verified by `git ls-remote` before this request was written).

## Reviewer pointers

- Contract: `.agent/episodes/bilateral-imbibition-v0.1/V1B_DIAGNOSTIC_CONTRACT.md`
- Reviewer contract:
  `.agent/episodes/bilateral-imbibition-v0.1/V1B_REVIEWER_CONTRACT.md`
- Upstream scientific review motivating V1b:
  `.agent/evidence/BI-VALIDATION-001/V1/V1/V1_EXTERNAL_SCIENTIFIC_REVIEW.md`
- Headline numbers for the independent checks: `summary.json`
  (static `Pc_static`/`C_static`; dynamic `V_meas`, `Pc_dynamic`,
  `V_hyd`, ratios; length-scan `L_eq/L1` = 0.488 vs old V1 ≈ 0.78;
  `Pc_dynamic/Pc_static` 0.92/0.79).  Gates g7/g8 and the static
  10%-scaling gate FAIL; g1–g6 PASS.  The executor did NOT tune
  anything to move any gate.

Write your review ONLY to
`D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-graphite\.agent_runtime\BI-V1B-DIAGNOSTIC-001\REVIEW.md`.
