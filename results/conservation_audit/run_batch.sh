#!/usr/bin/env bash
# BI-CONSERVATION-AUDIT-001 batch driver: full C0-C3 matrix, GPU + CPU.
# Each case runs in its own process (shape-specific JIT; LBM_ARCH selects
# the backend via the solver's module-level ti.init).
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-CONSERVATION-AUDIT-001
LOGS=results/conservation_audit/logs
mkdir -p "$LOGS"

run () {  # run <tag> <extra args...>
  tag=$1; shift
  echo "=== $tag start $(date +%H:%M:%S) ==="
  "$PY" tests/conservation_audit.py run --tag "$tag" "$@" \
    > "$LOGS/$tag.log" 2>&1
  ec=$?
  echo "=== $tag exit=$ec $(date +%H:%M:%S) ==="
  if [ $ec -ne 0 ]; then echo "!!! $tag FAILED"; tail -5 "$LOGS/$tag.log"; fi
}

# ---- GPU matrix ----
run C0_24_gpu --case C0 --arch gpu
run C0_16_gpu --case C0 --arch gpu --dims 16,16,16
run C0_32_gpu --case C0 --arch gpu --dims 32,32,32
run C1_gpu    --case C1 --arch gpu
run C2_gpu    --case C2 --arch gpu
run C3_gpu    --case C3 --arch gpu

# ---- CPU matrix (reduced horizons: 5k, C3 10k; late windows adjusted) ----
run C0_24_cpu --case C0 --arch cpu
run C1_cpu    --case C1 --arch cpu --steps 5000 --late-trace 4900:20
run C2_cpu    --case C2 --arch cpu --steps 5000 --late-trace 4900:20
run C3_cpu    --case C3 --arch cpu --steps 10000 --late-trace 9000:20 \
              --budget-ref-step 1000

# ---- aggregate ----
"$PY" tests/conservation_audit.py analyze > "$LOGS/analyze.log" 2>&1
echo "=== analyze exit=$? ==="
echo BATCH_DONE
