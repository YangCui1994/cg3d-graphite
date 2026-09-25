#!/usr/bin/env bash
# post-regression: baseline-C1 240k total-channel attribution arm +
# default-flip sanity (run AFTER the default flip commit).
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
run ac_C1_T3C1s_240k accum --geom C1 --cf C1 --acc A0 --steps 240000 --every 400 --tag ac_C1_T3C1s_240k
# F10 perf: same grid/horizon timing pairs (JIT excluded by the driver)
run perf_C3_T3C1s_20k   accum --geom C3 --cf C1  --acc A0 --steps 20000 --every 2000 --tag perf_C3_T3C1s_20k
run perf_C3_T3C1X_A2_20k accum --geom C3 --cf C1X --acc A2 --steps 20000 --every 2000 --tag perf_C3_T3C1X_A2_20k
run perf_C1_T3C1s_20k   accum --geom C1 --cf C1  --acc A0 --steps 20000 --every 2000 --tag perf_C1_T3C1s_20k
run perf_C1_T3C1X_A2_20k accum --geom C1 --cf C1X --acc A2 --steps 20000 --every 2000 --tag perf_C1_T3C1X_A2_20k
echo POST_BATCH_DONE
