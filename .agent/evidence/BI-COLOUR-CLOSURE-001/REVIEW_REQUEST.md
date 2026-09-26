# REVIEW REQUEST — BI-COLOUR-CLOSURE-001 (attempt 1)

## Binding

- **Task:** BI-COLOUR-CLOSURE-001 (narrow colour-channel closure;
  contract
  `.agent/episodes/bilateral-imbibition-v0.1/COLOUR_CLOSURE_CONTRACT.md`,
  entry point `START_COLOUR_CLOSURE.md`)
- **Base:** `e256b4857a6e51510b75358994d7c5bcc742781e`
- **Branch:** `agent-task/BI-COLOUR-CLOSURE-001` (pushed)
- **Candidate (this review):** `6c30260` (commit chain
  `388892e -> 71d2a4b -> 1854a58 -> 246a463 -> 6c30260`; do not
  rewrite)
- **Reviewer contract:**
  `.agent/episodes/bilateral-imbibition-v0.1/COLOUR_CLOSURE_REVIEWER_CONTRACT.md`
- **Prior external review (the blockers this task closes):**
  `.agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md`
  (B1: C3 60k one-sided colour drift; B2: periodic-C1 local bias)

## Where the evidence lives

Worktree:
`D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-episode-worktrees\BI-COLOUR-CLOSURE-001`
(clean at `6c30260` on the branch above).  Evidence
`results/colour_closure/` (253-file SHA256 MANIFEST.json, generated
by `make_manifest.py`); the frozen prior evidence
`results/conservation_fix/` is byte-identical to base.

## What changed (vs base)

- `lbm_solver_cg3d.py`: colour-channel only; T3 total path
  byte-frozen.  dbg probes (post-recolor sums, per-node cc,
  post-correction populations; `dbg_local`-gated);
  `colour_fix` += `C1R`, `C1X`; new `acc_fix` A0/A1/A2; production
  default now **T3 + C1X + A2** (env-overridable; `C1`/`A0`
  reproduce the interim accepted scoped closure).
- `tests/colour_closure.py` (new task-local driver: reproduce /
  diagnose / accum / budget; production kernels in production
  step order); `tests/conservation_fix.py` make_solver gains an
  optional `acc` passthrough (default 'A0' preserves prior replay).
- `results/colour_closure/**` evidence; no other trees touched.

## Diagnosis (before any code change; contract B/C)

- Biased class (periodic C1, B2): NON-FROZEN `cc==0` nodes — pure
  (chi ~ 1e-12), adjacent to the diffuse interface — carrying the
  uncorrected equilibrium-construction leak (R_r +4.66e-9,
  frac_pos 0.785 == Req_r; far bulk bit-frozen ~1e-19; `cc>0`
  closed by scoped-C1, −7.9e-12).
- Periodic-C1 accumulation (base): +8.85e-10/step (R2 0.927,
  second half +8.08e-10 R2 0.965) — ACCUMULATES.
- C3 budget identity (t=20k): dMr −1.2825e-5 = sumR +6.99e-6 +
  sumdacc −1.982e-5 (residual 7.7e-12) — the C3 drift is dominated
  by f32 scatter-accumulate rounding, OPPOSITE sign to the local
  leak, partially cancelling.  Hence every single-intervention arm
  fails a frozen gate (C1X/A0 −3.54e-9 on C1; C1/A1 +2.45e-9 on
  C1; C1X/A1 closure-f32 residue −9.2e-10 persists; C1R absorbed
  by f32 storage — computed Rc1 −3.79e-9 but stored residual stays
  at leak level; C1/A2 +9.46e-10 scope still needed).

## Selected candidate: T3 + C1X + A2

C1X = weighted closure with natural guard (cc>0 or dr!=0; frozen
nodes have dr==0 exactly — strict no-op).  A2 = f64 colour pipeline
end to end (f64 g locals + f64 accumulate; the closure makes the
outgoing sum EXACTLY rho_r; only the rho_r store rounds once).

- F0 local closure: every class to f64 epsilon (R_r ~ −6e-17);
  dacc ~ 0 exactly.
- C3 60k: colour +8.09e-12/step (R2 0.583, frac_pos 0.561);
  120k: +2.69e-12 (R2 0.415, alternating quarters); total channel
  −2.5e-11 / +1.0e-11 (inside the accepted T3 floor band).
- Periodic C1: 20k −1.08e-10; 60k −6.40e-11 (13.8x, segments
  −1.09e-10/−5.8e-11/−3.6e-11 decaying); **240k: +1.81e-11
  (R2 0.280, frac_pos 0.55; quarters +1.9e-10/−5.0e-12/+1.2e-11/
  −4.7e-13)** vs the BASE at 240k still +1.05e-9 (R2 0.9986).
  The residual is a decaying transient, NOT called a bounded
  floor; horizon/scaling evidence provided for owner re-scope
  judgement per contract E.
- A2 stationarity: max|v| EXACTLY 0.0, psi_dev exactly 0.0 — all
  7 combos (a2_candidates.json).
- Regressions (unchanged gates): F2 Level A/Laplace 0.42%/
  contact 31.2°/Poiseuille 1.0010/Compute_C/postproc PASS;
  F3 a26 1.0618 / a40 1.0741 (≤0.10), dynamic all_hard ×4,
  statics plateau (0.7904/0.7516/0.8068/0.7715); non-gated
  L0/h(h26) 3.02→2.64 disclosed; F4 V2 gates all True (g4/g10
  null by design), eps_r 5.87e-6 / eps_b 5.16e-7 (12.7x/384x
  better than the accepted fix; gate 5e-4), mirror 7.4e-4,
  single cluster, symmetry intact.
- Perf: net-zero within noise (C3 2833→2853, C1 2838→2809 st/s).

## Commands (repo root, lbm env python)

```bash
python tests/colour_closure.py reproduce
python tests/colour_closure.py diagnose --geom C1 --tag dx_C1_T3C1s          # base
python tests/colour_closure.py diagnose --geom C3 --tag dx_C3_T3C1s
python tests/colour_closure.py accum --geom C1 --steps 20000 --tag ac_C1_T3C1s_20k
python tests/colour_closure.py budget --geom C3 --pre-steps 20000 --probe-steps 200 --tag bg_C3_T3C1s
# candidate arms: add --cf C1X --acc A2 (full matrix in run_*.sh)
python results/colour_closure/a2_candidates.py
bash results/colour_closure/run_regression_batch.sh
```

## Reviewer instructions

Follow the reviewer contract exactly.  Do not read the executor
transcript; do not use the GPU; verify the worktree is clean at
`6c30260`, descending from `e256b485`, T3 total path frozen (no
V3/BC/physical-parameter/gate changes; check the diff yourself).
Recompute the load-bearing numbers from the committed
machine-readable evidence (class_stats.csv, mass_series.csv,
budget_*.csv/json, a2_candidates.json, levelc_*/reports,
MANIFEST).  State exactly which node class caused the base
one-sided residual and whether it accumulates; recompute the
candidate-mechanism / long-horizon / regression checks per the
contract; do not label a one-sided trend bounded.  Write ONLY
`.agent_runtime/BI-COLOUR-CLOSURE-001/REVIEW.md` and
`.agent_runtime/BI-COLOUR-CLOSURE-001/REVIEW_SESSION.json` in THIS
worktree (D:\...\cg3d-graphite).  REVIEW.md starts
`stage: colour-closure / candidate: 6c30260` and ends with a
single `Decision: PASS|CHANGES_REQUESTED|HUMAN_REQUIRED` line.
Even PASS authorizes neither V3 nor promotion; external scientific
review follows.  Stop after writing.
