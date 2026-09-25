#!/usr/bin/env bash
# BI-COLOUR-CLOSURE-001 horizon/scaling evidence: extend the candidate
# (T3+C1X+A2) beyond 60k to characterize the decaying periodic-C1
# residual (contract E horizon/scaling clause).
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-COLOUR-CLOSURE-001
LOGS=results/colour_closure/logs
run () {
  tag=$1; shift
  echo "=== $tag start $(date +%H:%M:%S)"
  "$PY" tests/colour_closure.py "$@" > "$LOGS/$tag.log" 2>&1
  echo "=== $tag exit=$? $(date +%H:%M:%S)"
}
run ac_C1_T3C1X_A2_240k accum --geom C1 --cf C1X --acc A2 --steps 240000 --every 400 --tag ac_C1_T3C1X_A2_240k
run ac_C3_T3C1X_A2_120k accum --geom C3 --cf C1X --acc A2 --steps 120000 --every 400 --tag ac_C3_T3C1X_A2_120k
echo HORIZON_BATCH_DONE
