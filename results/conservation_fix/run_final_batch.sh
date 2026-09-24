#!/usr/bin/env bash
# BI-SOLVER-CONSERVATION-FIX-001 final batch: re-verify the reselected
# candidate T3+scoped-C1 through F0/F1 (+CPU), then F2 (V0 before/after),
# F3 (V1c chain), F4 (V2 primary).
set -u
PY=/c/Users/yangc/anaconda3/envs/lbm/python.exe
cd /d/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-SOLVER-CONSERVATION-FIX-001
LOGS=results/conservation_fix/logs
ROOT=results/conservation_fix
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

# ---- F0 + F1 for reselected T3 + scoped C1 ----
"$PY" tests/conservation_fix.py f0 --fix T3 --cf C1 --tag f0_T3C1s \
  > "$LOGS/f0_T3C1s.log" 2>&1
echo "=== f0_T3C1s exit=$? $(date +%H:%M:%S)"
run2 f1_T3C1s_20k  LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1 -- "$PY" tests/conservation_fix.py f1 --fix T3 --cf C1 --steps 20000 --tag f1_T3C1s_20k
run2 f1_T3C1s_60k  LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1 -- "$PY" tests/conservation_fix.py f1 --fix T3 --cf C1 --steps 60000 --tag f1_T3C1s_60k
run2 f1_T3C1s_20k_cpu LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1 -- "$PY" tests/conservation_fix.py f1 --fix T3 --cf C1 --steps 20000 --tag f1_T3C1s_20k_cpu --arch cpu

# ---- F2: V0 suite, before (T0) and after (T3+C1s) ----
for MODE in T0 T3C1s; do
  if [ "$MODE" = T0 ]; then E=(LBM_TOTAL_FIX=T0 LBM_COLOUR_FIX=C0);
  else E=(LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1); fi
  run2 f2_levelA_$MODE        "${E[@]}" -- "$PY" tests/run_level_a.py
  run2 f2_computeC_$MODE      "${E[@]}" -- "$PY" tests/test_compute_c_bulk.py
  run2 f2_poiseuille_$MODE    "${E[@]}" -- "$PY" tests/test_poiseuille_cg3d.py
  run2 f2_laplace_$MODE       "${E[@]}" -- "$PY" tests/levelb_laplace.py
  run2 f2_contact_$MODE       "${E[@]}" -- "$PY" tests/levelb_contact_angle.py
  run2 f2_postproc_$MODE      "${E[@]}" -- "$PY" tests/test_postprocessing.py
done

# ---- F3: V1c regressions on the selected fix ----
V1="LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1 LBM_OUTROOT=$ROOT/levelc_v1c_fix"
run2 f3_static_h40  $V1 -- "$PY" tests/levelc_v1c.py static --hy 40 --tag static_h40
run2 f3_static_h60  $V1 -- "$PY" tests/levelc_v1c.py static --hy 60 --tag static_h60
run2 f3_dyn_h26_s   $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 26 --tag dyn_h26_s
run2 f3_dyn_h26_2L  $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 26 --L 472 --tag dyn_h26_2L
run2 f3_dyn_h40_s   $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 40 --tag dyn_h40_s
run2 f3_dyn_h40_2L  $V1 -- "$PY" tests/levelc_v1c.py dynamic --hy 40 --L 472 --tag dyn_h40_2L
run2 f3_collect     $V1 -- "$PY" tests/levelc_v1c.py collect

# ---- F4: V2 primary on the selected fix ----
V2="LBM_TOTAL_FIX=T3 LBM_COLOUR_FIX=C1 LBM_OUTROOT=$ROOT/levelc_v2_fix"
run2 f4_v2_primary  $V2 -- "$PY" tests/levelc_v2_bilateral.py --tag v2_primary

echo FINAL_BATCH_DONE
