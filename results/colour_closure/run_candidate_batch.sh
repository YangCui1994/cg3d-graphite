#!/usr/bin/env bash
# BI-COLOUR-CLOSURE-001 candidate comparison batch (contract D/E).
# Baseline (T3+C1/A0) evidence: dx_*_T3C1s, ac_C1_T3C1s_20k (this task,
# base run) + committed f0_T3C1s / f1_T3C1s_60k.
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-COLOUR-CLOSURE-001
LOGS=results/colour_closure/logs
mkdir -p "$LOGS"

run () {
  tag=$1; shift
  echo "=== $tag start $(date +%H:%M:%S)"
  "$PY" tests/colour_closure.py "$@" > "$LOGS/$tag.log" 2>&1
  echo "=== $tag exit=$? $(date +%H:%M:%S)"
}

# ---- the candidate: C1X + A1 ----
run dx_C1_T3C1X_A1  diagnose --geom C1 --cf C1X --acc A1 --tag dx_C1_T3C1X_A1 --pre-steps 1500 --probe-steps 40
run dx_C3_T3C1X_A1  diagnose --geom C3 --cf C1X --acc A1 --tag dx_C3_T3C1X_A1 --pre-steps 1500 --probe-steps 40
run ac_C1_T3C1X_A1_20k  accum --geom C1 --cf C1X --acc A1 --steps 20000 --tag ac_C1_T3C1X_A1_20k
run ac_C3_T3C1X_A1_60k  accum --geom C3 --cf C1X --acc A1 --steps 60000 --every 200 --tag ac_C3_T3C1X_A1_60k
run bg_C3_T3C1X_A1  budget --geom C3 --cf C1X --acc A1 --pre-steps 20000 --probe-steps 200 --tag bg_C3_T3C1X_A1

# ---- attribution arms (one intervention at a time) ----
run dx_C1_T3C1X  diagnose --geom C1 --cf C1X --acc A0 --tag dx_C1_T3C1X --pre-steps 1500 --probe-steps 40
run dx_C3_T3C1X  diagnose --geom C3 --cf C1X --acc A0 --tag dx_C3_T3C1X --pre-steps 1500 --probe-steps 40
run ac_C1_T3C1X_20k  accum --geom C1 --cf C1X --acc A0 --steps 20000 --tag ac_C1_T3C1X_20k
run ac_C3_T3C1X_60k  accum --geom C3 --cf C1X --acc A0 --steps 60000 --tag ac_C3_T3C1X_60k
run ac_C1_T3C1_A1_20k  accum --geom C1 --cf C1 --acc A1 --steps 20000 --tag ac_C1_T3C1_A1_20k
run ac_C3_T3C1_A1_60k  accum --geom C3 --cf C1 --acc A1 --steps 60000 --tag ac_C3_T3C1_A1_60k

# ---- reviewer-suggested rest-population candidate (f32-storage test) ----
run dx_C1_T3C1R  diagnose --geom C1 --cf C1R --acc A0 --tag dx_C1_T3C1R --pre-steps 1500 --probe-steps 40
run dx_C3_T3C1R  diagnose --geom C3 --cf C1R --acc A0 --tag dx_C3_T3C1R --pre-steps 1500 --probe-steps 40

# ---- baseline rerun (run-to-run band on the same machine) ----
run ac_C3_T3C1s_60k_rerun  accum --geom C3 --cf C1 --acc A0 --steps 60000 --tag ac_C3_T3C1s_60k_rerun

# ---- A2 isolation for new combos ----
echo "=== a2_candidates start $(date +%H:%M:%S)"
"$PY" results/colour_closure/a2_candidates.py > "$LOGS/a2_candidates.log" 2>&1
echo "=== a2_candidates exit=$? $(date +%H:%M:%S)"

echo CANDIDATE_BATCH_DONE
