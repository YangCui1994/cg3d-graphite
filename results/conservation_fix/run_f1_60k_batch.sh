#!/usr/bin/env bash
# BI-SOLVER-CONSERVATION-FIX-001 F1 60k batch + CPU comparison.
# Contract F1: 60k for baseline (T0+C0), numerical reference (T3+C0),
# and final selected candidate (T1+C1); CPU/GPU for the selected.
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-SOLVER-CONSERVATION-FIX-001
LOGS=results/conservation_fix/logs
mkdir -p "$LOGS"

run () {
  tag=$1; fix=$2; cf=$3; steps=$4; arch=${5:-gpu}
  echo "=== $tag start $(date +%H:%M:%S)"
  "$PY" tests/conservation_fix.py f1 --fix "$fix" --cf "$cf" \
    --steps "$steps" --tag "$tag" --arch "$arch" \
    > "$LOGS/$tag.log" 2>&1
  echo "=== $tag exit=$? $(date +%H:%M:%S)"
}

run f1_T0C0_60k T0 C0 60000
run f1_T3C0_60k T3 C0 60000
run f1_T1C1_60k T1 C1 60000
run f1_T1C1_20k_cpu T1 C1 20000 cpu
echo F1_60K_DONE
