#!/usr/bin/env bash
# BI-COLOUR-CLOSURE-001 A2 batch: f64 colour pipeline end to end
# (f64 g locals + f64 accumulate + exact weighted closure).
# Candidate: T3 + C1X + A2.
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

run dx_C1_T3C1X_A2  diagnose --geom C1 --cf C1X --acc A2 --tag dx_C1_T3C1X_A2 --pre-steps 1500 --probe-steps 40
run dx_C3_T3C1X_A2  diagnose --geom C3 --cf C1X --acc A2 --tag dx_C3_T3C1X_A2 --pre-steps 1500 --probe-steps 40
run ac_C1_T3C1X_A2_20k  accum --geom C1 --cf C1X --acc A2 --steps 20000 --tag ac_C1_T3C1X_A2_20k
run ac_C1_T3C1X_A2_60k  accum --geom C1 --cf C1X --acc A2 --steps 60000 --tag ac_C1_T3C1X_A2_60k
run ac_C3_T3C1X_A2_60k  accum --geom C3 --cf C1X --acc A2 --steps 60000 --tag ac_C3_T3C1X_A2_60k
run bg_C3_T3C1X_A2  budget --geom C3 --cf C1X --acc A2 --pre-steps 20000 --probe-steps 200 --tag bg_C3_T3C1X_A2
run ac_C1_T3C1_A2_20k  accum --geom C1 --cf C1 --acc A2 --steps 20000 --tag ac_C1_T3C1_A2_20k

echo A2_BATCH_DONE
