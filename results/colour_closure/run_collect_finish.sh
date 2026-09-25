#!/usr/bin/env bash
# finish the V1c chain (statics h26/h80 were missing from the batch)
# + post-batch arms (baseline C1 240k attribution + perf pairs).
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-COLOUR-CLOSURE-001
LOGS=results/colour_closure/logs
ROOT=results/colour_closure
run2 () {
  log=$1; shift
  envs=()
  while [ "$1" != "--" ]; do envs+=("$1"); shift; done
  shift
  echo "=== $log start $(date +%H:%M:%S)"
  env "${envs[@]}" "$@" > "$LOGS/$log.log" 2>&1
  echo "=== $log exit=$? $(date +%H:%M:%S)"
}
V1="LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1X LBM_ACC_FIX=A2 LBM_OUTROOT=$ROOT/levelc_v1c_fix"
run2 f3_static_h26  $V1 -- "$PY" tests/levelc_v1c.py static --hy 26 --tag static_h26
run2 f3_static_h80  $V1 -- "$PY" tests/levelc_v1c.py static --hy 80 --tag static_h80
run2 f3_collect     $V1 -- "$PY" tests/levelc_v1c.py collect
bash results/colour_closure/run_post_batch.sh
echo COLLECT_FINISH_DONE
