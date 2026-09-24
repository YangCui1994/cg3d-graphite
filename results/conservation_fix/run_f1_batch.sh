#!/usr/bin/env bash
# BI-SOLVER-CONSERVATION-FIX-001 F1 batch: C3 long-horizon 20k per combo.
# T4 eliminated at F0 (negative control: R_f +1.494e-8, frac_pos 0.94).
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

run f1_T0C0_20k T0 C0 20000
run f1_T1C0_20k T1 C0 20000
run f1_T2C0_20k T2 C0 20000
run f1_T3C0_20k T3 C0 20000
run f1_T2C1_20k T2 C1 20000
run f1_T1C1_20k T1 C1 20000
echo F1_20K_DONE
