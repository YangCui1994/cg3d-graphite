"""
3D CG imbibition-residual (I-R) runs (P4 driver, 2026-09-12)
============================================================
Extends run_pcs_cg3d.py with a REVERSED ladder: drain to S_i (ladder
up to --ds-drain's last value, held quasi-steady), then step the rho
difference back DOWN to zero so the wetting phase re-invades; the
final S_nw at d=0 is the residual nonwetting saturation S_nr(S_i).
At the end, connected components of the trapped nonwetting phase give
the cluster-size CCDF (Herring-2015 style comparison).

Three runs (S_i spread) are launched sequentially by ir_chain.bat/py:
  drain ladders differ only in the last delta; imbibe ladder shared.

PR-5 (2026-09-19): geometry/ladder/convergence live in cg3d.protocol
(OpenSystem + run_hold) — shared verbatim with run_pcs_cg3d.py; this
driver keeps argparse, per-phase frame naming, trapped-cluster analysis
and report layout.

Run from repo root:
  python run_ir_cg3d.py --geo results_p3_geo/finney_r25_n200.npz \
      --tag p4_si1 --ds-drain 0.014 0.019 0.025 0.034 0.040 \
      --ds-imbibe 0.030 0.022 0.015 0.009 0.004 0.0
"""
import argparse
import json
import os

import matplotlib
matplotlib.use('Agg')

import numpy as np

from run_common import mid_slice_png, label_periodic
from cg3d import OpenSystem, run_hold, run_equil


def _save_partial(args, ladder):
    """Incremental checkpoint: the partial ladder survives an interrupted
    run (2026-09-15 rule — output must never be head/tail-only)."""
    with open(os.path.join('results_pcs_cg3d', args.tag,
                           'report_partial.json'), 'w',
              encoding='utf-8') as f:
        json.dump(dict(args=vars(args), note='incremental checkpoint',
                       ladder=ladder), f, indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--geo', required=True)
    ap.add_argument('--capa', type=float, default=0.06)
    ap.add_argument('--psi-solid', type=float, default=-0.75)
    ap.add_argument('--ds-drain', type=float, nargs='+', required=True)
    ap.add_argument('--ds-imbibe', type=float, nargs='+',
                    default=[0.030, 0.022, 0.015, 0.009, 0.004, 0.0])
    ap.add_argument('--res-thick', type=int, default=8)
    ap.add_argument('--equil-steps', type=int, default=20000)
    ap.add_argument('--min-steps', type=int, default=15000)
    ap.add_argument('--max-steps', type=int, default=150000)
    ap.add_argument('--qs-window', type=int, default=15000)
    ap.add_argument('--qs-tol', type=float, default=5e-7)
    ap.add_argument('--qs-mode', choices=('sat', 'multi'), default='sat',
                    help="quasi-steady exit rule (PR-3 task 2.4): 'sat' = "
                         "legacy saturation-slope only (baseline-"
                         "comparable); 'multi' = saturation AND pressure "
                         "AND flux AND kinetic. The convergence record is "
                         "always written either way.")
    ap.add_argument('--pc-drift-tol', type=float, default=0.01)
    ap.add_argument('--flux-tol', type=float, default=1e-6)
    ap.add_argument('--u-rel-tol', type=float, default=0.05)
    ap.add_argument('--conn', type=int, choices=(6, 18, 26), default=6,
                    help='cluster connectivity for the trapped-gas CCDF '
                         '(PR-3 task 2.6; 6 = legacy default). Periodic '
                         'y/z merge (task 2.7) is always on.')
    ap.add_argument('--every', type=int, default=500)
    ap.add_argument('--umax-cap', type=float, default=0.12)
    ap.add_argument('--dump-every', type=int, default=20000,
                    help='dump an int8-quantised psi frame every N steps '
                         '(DEFAULT ON per 2026-09-15 user rule: never '
                         'head/tail-only output; 0 disables).  Frames are '
                         'named per phase+rung so rungs never overwrite '
                         'each other.')
    ap.add_argument('--pc-band', type=int, default=4,
                    help='width [lu] of the pore bands just inside each '
                         'membrane used for pc_measured')
    ap.add_argument('--tag', required=True)
    args = ap.parse_args()

    out = os.path.join('results_pcs_cg3d', args.tag)
    os.makedirs(out, exist_ok=True)

    sys_ = OpenSystem(args.geo, args.capa, args.psi_solid,
                      res_thick=args.res_thick, pc_band=args.pc_band)
    s = sys_.s

    dump_dir = os.path.join(out, 'frames')
    if args.dump_every:
        os.makedirs(dump_dir, exist_ok=True)
        np.savez_compressed(os.path.join(dump_dir, 'f_solid.npz'),
                            solid=sys_.solid[sys_.dom, :, :].astype(np.int8))

    def make_dump_frame(d, phase):
        def _dump(it):
            psi = s.psi_snapshot()
            q = np.clip(np.rint(psi[sys_.dom, :, :] * 100.0), -127, 127
                        ).astype(np.int8)
            red = np.where(sys_.dom_pore,
                           (psi[sys_.dom, :, :] + 1.0) / 2.0, 0.0)
            np.savez_compressed(
                os.path.join(dump_dir, f'{phase}_d{d:.4f}_{it:07d}.npz'),
                psi_q=q, it=it, d=d,
                s_nw=np.float32(red.sum() / sys_.pore_cells))
        return _dump

    run_equil(args, sys_)
    print(f'[{args.tag}] equil done', flush=True)

    ladder = []
    for k, d in enumerate(args.ds_drain):
        ladder.append(run_hold(args, sys_, d, f'drain{k:02d}', 'drain',
                               dump_frame=make_dump_frame(d, 'drain'),
                               rung_end_frame=True))
        _save_partial(args, ladder)
    for k, d in enumerate(args.ds_imbibe):
        ladder.append(run_hold(args, sys_, d, f'imb{k:02d}', 'imbibe',
                               dump_frame=make_dump_frame(d, 'imbibe'),
                               rung_end_frame=True))
        _save_partial(args, ladder)

    # ---- trapped cluster analysis on the final state ----
    # PR-3 tasks 2.5-2.7: binary (psi > 0) vs continuous saturation, and
    # connectivity-parameterised clusters WITH periodic y/z merging (the
    # solver is y/z-periodic; plain ndimage.label splits spanning
    # clusters, over-counting n and under-counting 'largest').
    psi = s.psi_snapshot()
    red_dom = (psi[sys_.dom, :, :] > 0.0) & sys_.dom_pore
    lab, sizes = label_periodic(red_dom, conn=args.conn)
    n = int(len(sizes))
    total_red = float(red_dom.sum())
    s_nr = total_red / sys_.pore_cells             # binary (legacy key)
    red_cont = np.where(sys_.dom_pore,
                        (psi[sys_.dom, :, :] + 1.0) / 2.0, 0.0)
    s_nr_continuous = float(red_cont.sum() / sys_.pore_cells)
    mid_slice_png(psi, os.path.join(out, 'final.png'),
                  f'{args.tag}: S_nr={s_nr:.3f} '
                  f'(cont {s_nr_continuous:.3f}), clusters={n} '
                  f'(conn{args.conn}, periodic), '
                  f'largest={sizes[0] if n else 0.0:.0f}')
    fl = s.reservoir_fluxes()
    np.savez_compressed(os.path.join(out, 'final.npz'), psi=psi,
                        solid=sys_.solid, sizes=sizes)
    summary = dict(args=vars(args), ladder=ladder, s_nr=s_nr,
                   s_nr_continuous=s_nr_continuous,
                   cluster_topology=dict(conn=args.conn, periodic='y/z'),
                   n_clusters=n, largest=float(sizes[0]) if n else 0.0,
                   sizes_top=[float(v) for v in sizes[:50]], inj=fl)
    with open(os.path.join(out, 'report.json'), 'w',
              encoding='utf-8') as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f'[{args.tag}] I-R DONE: '
          f'S_i={ladder[len(args.ds_drain)-1]["s_nw"]:.3f}'
          f' -> S_nr={s_nr:.3f}, clusters={n}, '
          f'largest={sizes[0] if n else 0.0:.0f}', flush=True)
    del s


if __name__ == '__main__':
    main()
