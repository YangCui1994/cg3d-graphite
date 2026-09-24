# REVIEW REQUEST — BI-V2-BILATERAL-001

- **Task ID:** BI-V2-BILATERAL-001 (revised V2 bilateral
  trapped-pocket verification, per
  `.agent/episodes/bilateral-imbibition-v0.1/V2_BILATERAL_CONTRACT.md`;
  launched from `.agent/episodes/bilateral-imbibition-v0.1/START_V2.md`).
- **Base SHA:** `2b82f9a5f448e756b5d5903b0df37f9a3b11d804`
- **Candidate SHA (exact):** `5e679d8d99d338f9ab28565c636f021a0f9211b2`
  (branch `agent-task/BI-V2-BILATERAL-001`; remote verified at this SHA)
- **Absolute product worktree path:**
  `D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-episode-worktrees\BI-V2-BILATERAL-001`
- **Execution report:**
  `<worktree>/results/levelc_v2/v2_primary/EXECUTION_REPORT.md`
- **Provenance / manifest:**
  `<worktree>/results/levelc_v2/v2_primary/PROVENANCE.md`,
  `<worktree>/results/levelc_v2/v2_primary/MANIFEST.json`
- **Changed files:** `tests/levelc_v2_bilateral.py`,
  `tests/v2_unit_check.py`, `results/levelc_v2/**` only
  (`git -C <worktree> diff --name-only 2b82f9a..5e679d8`); no solver /
  cg3d / prior-stage changes.
- **Primary run command:**
  `C:\Users\yangc\anaconda3\envs\lbm\python.exe tests/levelc_v2_bilateral.py --tag v2_primary`
  (60 000 steps, shell exit 0, console log `logs/v2_primary.log`).
- **Worktree state:** `git status --porcelain` EMPTY; HEAD = candidate.

## Headline numbers for independent verification

- Geometry h=40 / B=80 / G0=160 / nx=326 mirror-exact
  (`symmetry_check.json`); t=0 exactly one trapped cluster (38 400
  nodes, 6-neighbour z-periodic-only).
- Mirror symmetry: `max e_x = 0.0013 lu`, RMS 0.0010; full-field
  `E_psi ≤ 8.3e-5`; buffer gas occupancy 288 nodes per side, equal.
- Fronts stall after static-meniscus shaping: one-sided column-mean
  retreat 0.84 lu; `G_bulk` 150→146; pocket mean rho 1.0035→1.0041
  (+0.06% compression); `INTERACTION_ONSET = NOT_REACHED`; rate
  comparison `NOT_DISCRIMINATING` (0.09 lu window displacement — both
  contract-permitted outcomes).
- Clusters: 1 throughout; no fragmentation; no NaN; u_max 0.0254;
  bulk-node rho [0.935, 1.008]; all-fluid per-node min 0.8851
  (diffuse-interface structure — see the V1c-baseline comparison in
  EXECUTION_REPORT.md, from committed V1c fields).
- **g6 mass drift: letter-FAIL** — max ε_b 6.7e-4 > 5e-4 gate; signed
  decomposition shows BOTH colours positive (total +5.4e-4, ~7e-9/step
  relative), the same floor as the accepted V1c closure values
  (4.9e-4–6.8e-4).  The contract assigns the blocking judgment
  ("monotonically or by an order-one amount") to YOU; the trajectory is
  in `mass_stability_series.csv`.
- Two guardrail-interpretation decisions are DECLARED in
  EXECUTION_REPORT.md (equil window 5000; bulk-node rho semantics with
  per-node V1c evidence) — audit them against the contract's
  "approximately" wording and the baseline evidence.

Write your review ONLY to
`D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-graphite\.agent_runtime\BI-V2-BILATERAL-001\REVIEW.md`
(first lines: `stage: V2` / `attempt: 1` / `candidate: 5e679d8d99d338f9ab28565c636f021a0f9211b2` /
execution_report path).
