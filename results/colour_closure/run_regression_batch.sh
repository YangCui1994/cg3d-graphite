#!/usr/bin/env bash
# BI-COLOUR-CLOSURE-001 regression batch for the selected candidate
# (T3 + C1X + A2), thresholds unchanged:
#   F2 V0 suite (Level A incl. production A2 N=32, Compute_C,
#      Poiseuille, Laplace, contact, postprocessing) — T0 before,
#      candidate after
#   F3 V1c static + dynamic a26/a40 chain
#   F4 V2 primary (h40/B80/G160, 60k)
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-COLOUR-CLOSURE-001
LOGS=results/colour_closure/logs
ROOT=results/colour_closure
mkdir -p "$LOGS"

run2 () {  # run2 <logname> <env...> -- <cmd...>
  log=$1; shift
  envs=()
  while [ "$1" != "--" ]; do envs+=("$1"); shift; done
  shift
  echo "=== $log start $(date +%H:%M:%S)"
  env "${envs[@]}" "$@" > "$LOGS/$log.log" 2>&1
  echo "=== $log exit=$? $(date +%H:%M:%S)"
}

# ---- F2: V0 suite, before (T0+C1/A0 pre-fix arithmetic) and after ----
for MODE in T0 CAND; do
  if [ "$MODE" = T0 ]; then E=(LBM_TOTAL_FIX=T0 LBM_COLOUR_FIX=C0 LBM_ACC_FIX=A0);
  else E=(LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1X LBM_ACC_FIX=A2); fi
  run2 f2_levelA_$MODE        "${E[@]}" -- "$PY" tests/run_level_a.py
  run2 f2_computeC_$MODE      "${E[@]}" -- "$PY" tests/test_compute_c_bulk.py
  run2 f2_poiseuille_$MODE    "${E[@]}" -- "$PY" tests/test_poiseuille_cg3d.py
  run2 f2_laplace_$MODE       "${E[@]}" -- "$PY" tests/levelb_laplace.py
  run2 f2_contact_$MODE       "${E[@]}" -- "$PY" tests/levelb_contact_angle.py
  run2 f2_postproc_$MODE      "${E[@]}" -- "$PY" tests/test_postprocessing.py
done

# ---- F3: V1c regressions on the candidate ----
V1="LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1X LBM_ACC_FIX=A2 LBM_OUTROOT=$ROOT/levelc_v1c_fix"
run2 f3_static_h40  $V1 -- "$PY" tests/levelc_v1c.py static --hy 40 --tag static_h40
run2 f3_static_h60  $V1 -- "$PY" tests/levelc_v1c.py static --hy 60 --tag static_h60
run2 f3_dyn_h26_s   $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 26 --tag dyn_h26_s
run2 f3_dyn_h26_2L  $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 26 --L 472 --tag dyn_h26_2L
run2 f3_dyn_h40_s   $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 40 --tag dyn_h40_s
run2 f3_dyn_h40_2L  $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 40 --L 472 --tag dyn_h40_2L
run2 f3_collect     $V1 -- "$PY" tests/levelc_v1c.py collect

# ---- F4: V2 primary on the candidate ----
V2="LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1X LBM_ACC_FIX=A2 LBM_OUTROOT=$ROOT/levelc_v2_fix"
run2 f4_v2_primary  $V2 -- "$PY" tests/levelc_v2_bilateral.py --tag v2_primary

echo REGRESSION_BATCH_DONE
