# REVIEW REQUEST — BI-SOLVER-CONSERVATION-FIX-001 (attempt 4)

## Binding

- **Task:** BI-SOLVER-CONSERVATION-FIX-001 (authorized solver
  conservation fix)
- **Base:** `1f5ee76fa183b42dd0ffcb291f389c3f1974a147`
- **Branch:** `agent-task/BI-SOLVER-CONSERVATION-FIX-001`
- **Attempt-1 candidate:** `2d45b9e5468dd28e953115824bfc836f43317247`
  (CHANGES_REQUESTED, B1–B5 + minor)
- **Attempt-2 candidate:** `8554ee78b6d3d6d28bdb4943dbe1768f27adaaf4`
  (CHANGES_REQUESTED, seven documentation items)
- **Attempt-3 candidate:** `b75253e01efa8ee5a2ebd1ed61501274ebe902da` (CHANGES_REQUESTED, one blocking number + two optional sweeps)
- **Attempt-4 candidate (this review):** `e256b4857a6e51510b75358994d7c5bcc742781e`
- **Prior reviews:** `REVIEW_ATTEMPT_1.md`, `REVIEW_ATTEMPT_2.md`,
  `REVIEW_ATTEMPT_3.md` in this directory
- **Reviewer contract:**
  `.agent/episodes/bilateral-imbibition-v0.1/SOLVER_CONSERVATION_FIX_REVIEWER_CONTRACT.md`

## Revision scope (attempt 3 -> attempt 4)

The attempt-3 review's exact next action, one commit
(`git diff b75253e e256b48` — documentation only):

1. CANDIDATE_COMPARISON selected-candidate total-channel R2 corrected
   0.81 -> **0.62**, script-extracted from
   `f1_T3C1s_60k/f1_report.json` (0.6246), consistent with
   EXECUTION_REPORT;
2. MANIFEST regenerated for the changed hash (198 files);
3. optional sweeps applied: probe allocation stated as 10 per-node f64
   fields (12 f64 values per node); production A2 gate N=32 named;
4. controller-side section-17 publication remains post-review per
   START section 8.

## Where the evidence lives

Worktree
`D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-episode-worktrees\BI-SOLVER-CONSERVATION-FIX-001`,
evidence `results/conservation_fix/` (198-file SHA256 MANIFEST); frozen
baselines `results/levelc_v1c/`, `results/levelc_v2/`,
`results/conservation_audit/`.

## Reviewer instructions

Follow the reviewer contract with REVIEW_ATTEMPT_2.md as the prior
finding set. Verify the seven items are implemented with no new defect
(`git diff 8554ee7 b75253e --stat` lists only the revision files;
solver/tests byte-identical; raw evidence untouched; MANIFEST hashes
re-verify); confirm the attempt-2 scientific conclusions still stand.
Do not read the executor transcript. Write only `REVIEW.md` +
`REVIEW_SESSION.json` in this directory; REVIEW.md starts
`stage: conservation-fix / attempt: 3 / candidate: b75253e...` and ends
with a single `Decision: PASS|CHANGES_REQUESTED|HUMAN_REQUIRED` line.
Even PASS does not authorize V3. Stop after writing.
