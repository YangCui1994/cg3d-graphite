#!/usr/bin/env bash
# BI-COLOUR-CLOSURE-001 retry of the arms lost to the mid-batch edit
# + the A2 (f64 colour pipeline) candidate batch.
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
# lost attribution arms
run dx_C1_T3C1X  diagnose --geom C1 --cf C1X --acc A0 --tag dx_C1_T3C1X --pre-steps 1500 --probe-steps 40
run dx_C3_T3C1X  diagnose --geom C3 --cf C1X --acc A0 --tag dx_C3_T3C1X --pre-steps 1500 --probe-steps 40
run ac_C1_T3C1X_20k  accum --geom C1 --cf C1X --acc A0 --steps 20000 --tag ac_C1_T3C1X_20k
run ac_C3_T3C1X_60k  accum --geom C3 --cf C1X --acc A0 --steps 60000 --tag ac_C3_T3C1X_60k
run ac_C1_T3C1_A1_20k  accum --geom C1 --cf C1 --acc A1 --steps 20000 --tag ac_C1_T3C1_A1_20k
run ac_C3_T3C1_A1_60k  accum --geom C3 --cf C1 --acc A1 --steps 60000 --tag ac_C3_T3C1_A1_60k
run dx_C1_T3C1R  diagnose --geom C1 --cf C1R --acc A0 --tag dx_C1_T3C1R --pre-steps 1500 --probe-steps 40
run dx_C3_T3C1R  diagnose --geom C3 --cf C1R --acc A0 --tag dx_C3_T3C1R --pre-steps 1500 --probe-steps 40
run ac_C3_T3C1s_60k_rerun  accum --geom C3 --cf C1 --acc A0 --steps 60000 --tag ac_C3_T3C1s_60k_rerun
echo "=== a2_candidates start $(date +%H:%M:%S)"
"$PY" results/colour_closure/a2_candidates.py > "$LOGS/a2_candidates.log" 2>&1
echo "=== a2_candidates exit=$? $(date +%H:%M:%S)"
# A2 candidate batch
bash results/colour_closure/run_a2_batch.sh
echo RETRY_A2_BATCH_DONE
