#!/usr/bin/env bash
# BI-COLOUR-CLOSURE-001 diagnosis batch (contract B + C + budget):
#   dx_C1_T3C1s : periodic two-phase C1, per-node-class partition
#   dx_C3_T3C1s : two-phase slit C3, per-node-class partition
#   ac_C1_T3C1s_20k : contract C periodic-C1 accumulation series
#   bg_C3_T3C1s : C3 late-window closure budget (20k pre + 200 probed)
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

run dx_C1_T3C1s diagnose --geom C1 --tag dx_C1_T3C1s --pre-steps 1500 --probe-steps 40
run dx_C3_T3C1s diagnose --geom C3 --tag dx_C3_T3C1s --pre-steps 1500 --probe-steps 40
run ac_C1_T3C1s_20k accum --geom C1 --steps 20000 --every 200 --tag ac_C1_T3C1s_20k
run bg_C3_T3C1s budget --geom C3 --pre-steps 20000 --probe-steps 200 --tag bg_C3_T3C1s
echo DIAGNOSIS_BATCH_DONE
