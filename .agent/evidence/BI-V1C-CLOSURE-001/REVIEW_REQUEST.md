# REVIEW REQUEST — BI-V1C-CLOSURE-001 (attempt 2, rework)

- **Task ID:** BI-V1C-CLOSURE-001; this is the bounded rework after the
  attempt-1 CHANGES_REQUESTED review at
  `.agent_runtime/BI-V1C-CLOSURE-001/REVIEW_ATTEMPT_1.md` (copy of the
  original REVIEW.md; read it first — its B1/B2 are the rework target).
- **Product branch:** `agent-task/BI-V1C-CLOSURE-001`
- **Candidate SHA (exact):** `2b82f9a5f448e756b5d5903b0df37f9a3b11d804`
  (parent of the attempt-1 candidate `cfff538…`; NO history rewrite)
- **Base SHA:** `a9c6db87da2eeb3572607152391fe6863394ebee`
- **Absolute product worktree path:**
  `D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-episode-worktrees\BI-V1C-CLOSURE-001`
- **Execution report (attempt 2):**
  `<worktree>/results/levelc_v1c/EXECUTION_REPORT.md`
- **Provenance:** `<worktree>/results/levelc_v1c/PROVENANCE.md`
  (chain `032d273` runs → `5f18caa` collect → `17bdb1b`/`4d4dcb3`+
  validity ladder & reanalyze; simulation evidence UNCHANGED — the four
  dynamic reports were recomputed by `reanalyze` from the committed
  `front.csv`/`probes.csv`; each report carries `prov_reanalysis`)
- **Summary JSON:** `<worktree>/results/levelc_v1c/summary.json`

## What changed since attempt 1 (B1/B2 correction, no GPU, no solver)

1. **B2**: the `Pc_dynamic` aggregate now honours the full declared
   window (`t ≥ t_tr` AND `x_ic_exit ≤ x_m(t_probe) ≤ x_stop`, front
   position joined by interpolation).
2. **B1**: per-probe validity ladder before ANY aggregate —
   `V0` 12-col bulk rule → `V1` window-x → `V2` band widths ≥ 20
   columns → `V3` (PRIMARY) gradient consistency
   `0.5 ≤ |dp/dx|/G(V_meas) ≤ 2.0` both bands (G from the independent
   front fit).  Median AND mean for every variant plus an `r2 ≥ 0.90`
   alternative are first-class output (`estimator_sensitivity.csv`;
   `validity_variants` in each report).  Probes failing validity are
   counted per variant, never silently repaired; empty primary set
   fails explicitly.
   Deviations from the review's illustrative "3h/4h margins, r² ≥
   0.995" are DECLARED with reasons in the driver docstring: the 3h/4h
   margins structurally empty the h40 short window (x_ic_exit 122 >
   buf0−4h 90), and pure-r² primaries are unsuitable because h40-short
   bulk-band fits sit at r² 0.85–0.90 even at 100+ columns — while the
   gradient criterion excludes exactly the contaminated probes the
   review identified (0.03×/4.3× gradients, r²_gas → 0.002).
3. Attempt-1 non-blocking items addressed in EXECUTION_REPORT.md:
   static method-band (thr sensitivity 1.03% at h80; the 18%
   V1b↔V1c h26 shift attributed to method AND protocol change), mass
   closure 4.9e-4–6.8e-4 + total drift 0.04–0.27%
   (`mass_accounting`), g3 pinning caveat, sensitivity-definition
   separation (V1b band-placement vs V1c threshold).

## Headline numbers (primary = V3 gradient, median)

- **a26 = 1.0436** (gate PASS, 4.4%); **a40 = 1.0699** (PASS, 7.0%).
  Sensitivity: h26 1.039–1.059 (all variants); h40 1.065–1.130
  (contaminated V0/V1 mean = 1.121/1.130 reproduce the attempt-1 FAIL
  diagnosis; defensible variants 1.065–1.096).
- Fully-valid probe counts: 22/35, 43/55, 13/25, 38/49.
- Static: unchanged from attempt 1 (plateau C ≈ 0.782 ± 0.031).

## Worktree state

`git status --porcelain` EMPTY; HEAD = candidate SHA; remote branch
resolves to the same SHA (verified before this request was written).

Write your review ONLY to
`D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-graphite\.agent_runtime\BI-V1C-CLOSURE-001\REVIEW.md`
(first lines: `stage: V1C` / `attempt: 2` / `candidate: 2b82f9a5f448e756b5d5903b0df37f9a3b11d804` /
execution_report path).
