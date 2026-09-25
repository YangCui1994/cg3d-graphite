#!/usr/bin/env bash
# finish F3: static_h26 + static_h80 (collect needs the full set) + collect
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-SOLVER-CONSERVATION-FIX-001
LOGS=results/conservation_fix/logs
ROOT=results/conservation_fix
V1="LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1 LBM_OUTROOT=$ROOT/levelc_v1c_fix"
# wait for the V2 run to finish (single-GPU serialization)
while ps aux 2>/dev/null | grep -v grep | grep -q levelc_v2_bilateral; do sleep 60; done
echo "=== f3_static_h26 start $(date +%H:%M:%S)"
env $V1 "$PY" tests/levelc_v1c.py static --hy 26 --tag static_h26 > "$LOGS/f3_static_h26.log" 2>&1
echo "=== f3_static_h26 exit=$?"
echo "=== f3_static_h80 start $(date +%H:%M:%S)"
env $V1 "$PY" tests/levelc_v1c.py static --hy 80 --tag static_h80 > "$LOGS/f3_static_h80.log" 2>&1
echo "=== f3_static_h80 exit=$?"
echo "=== f3_collect start $(date +%H:%M:%S)"
env $V1 "$PY" tests/levelc_v1c.py collect > "$LOGS/f3_collect.log" 2>&1
echo "=== f3_collect exit=$?"
echo COLLECT_FINISH_DONE
