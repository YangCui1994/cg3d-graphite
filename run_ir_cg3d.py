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

Run from 2phase/:
  python run_ir_cg3d.py --geo results_p3_geo/finney_r25_n200.npz \
      --tag p4_si1 --ds-drain 0.014 0.019 0.025 0.034 0.040 \
      --ds-imbibe 0.030 0.022 0.015 0.009 0.004 0.0
"""
import argparse
import json
import os
import time

import matplotlib
matplotlib.use('Agg')

from run_common import mid_slice_png
import numpy as np
from scipy import ndimage



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
    ap.add_argument('--every', type=int, default=500)
    ap.add_argument('--umax-cap', type=float, default=0.12)
    ap.add_argument('--dump-every', type=int, default=20000,
                    help='dump an int8-quantised psi frame every N steps '
                         '(DEFAULT ON per 2026-09-15 user rule: never '
                         'head/tail-only output; 0 disables).  Frames are '
                         'named per phase+rung so rungs never overwrite '
                         'each other.')
    ap.add_argument('--tag', required=True)
    args = ap.parse_args()

    from lbm_solver_cg3d import ColorGradientSolver3D

    out = os.path.join('results_pcs_cg3d', args.tag)
    os.makedirs(out, exist_ok=True)
    dat = np.load(args.geo)
    solid_full = dat['solid'].astype(np.int8)
    nx, ny, nz = solid_full.shape
    pore_full = solid_full == 0
    wt = 3
    rt = args.res_thick
    x_in = wt + rt
    x_out = nx - wt - rt
    solid = solid_full.copy()
    solid[:wt, :, :] = 1
    solid[nx - wt:, :, :] = 1
    dom = slice(x_in + 1, x_out)
    dom_pore = pore_full[dom, :, :]

    psi0 = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
    psi0[wt:x_in + 1, :, :] = np.where(
        pore_full[wt:x_in + 1, :, :], 1.0, 0.0).astype(np.float32)
    psi0[x_in, :, :] = np.where(
        pore_full[x_in, :, :], 1.0, 0.0).astype(np.float32)
    mem_r = np.zeros_like(solid)
    mem_b = np.zeros_like(solid)
    mem_b[x_in, :, :] = 1
    mem_r[x_out, :, :] = 1
    res_in = np.zeros_like(solid)
    res_in[wt:x_in, :, :] = 1
    res_out = np.zeros_like(solid)
    res_out[x_out + 1:nx - wt, :, :] = 1

    s = ColorGradientSolver3D(nx, ny, nz, CapA=args.capa)
    s.set_psi_solid(args.psi_solid)
    s.set_membranes(mem_r, mem_b)

    def set_ladder(d):
        s.set_reservoirs(res_in, 1.0, 1.0 + d / 2.0)
        s.set_reservoirs(res_out, -1.0, 1.0 - d / 2.0)

    set_ladder(0.0)
    s.init(psi0, solid)
    pore_cells = float(dom_pore.sum())

    dump_dir = os.path.join(out, 'frames')
    if args.dump_every:
        os.makedirs(dump_dir, exist_ok=True)
        np.savez_compressed(os.path.join(dump_dir, 'f_solid.npz'),
                            solid=solid[dom, :, :].astype(np.int8))

    def dump_frame(it, d, phase):
        psi = s.psi_snapshot()
        q = np.clip(np.rint(psi[dom, :, :] * 100.0), -127, 127
                    ).astype(np.int8)
        red = np.where(dom_pore, (psi[dom, :, :] + 1.0) / 2.0, 0.0)
        np.savez_compressed(
            os.path.join(dump_dir, f'{phase}_d{d:.4f}_{it:07d}.npz'),
            psi_q=q, it=it, d=d,
            s_nw=np.float32(red.sum() / pore_cells))

    def measure():
        psi = s.psi_snapshot()
        _, v = s.macro_snapshot()
        red = np.where(dom_pore, (psi[dom, :, :] + 1.0) / 2.0, 0.0)
        u = v[dom, :, :, :]
        umax = float(np.sqrt(u[..., 0]**2 + u[..., 1]**2
                            + u[..., 2]**2).max())
        return float(red.sum() / pore_cells), umax

    def run_hold(d, label, phase):
        set_ladder(d)
        t0 = time.time()
        hist = []
        it = 0
        reason = 'max-steps'
        while it < args.max_steps:
            it += 1
            s.step()
            if args.dump_every and it % args.dump_every == 0:
                dump_frame(it, d, phase)
            if it % args.every == 0:
                sn, um = measure()
                hist.append((it, sn))
                w = [(i, sv) for i, sv in hist if i > it - args.qs_window]
                if (it >= args.min_steps and len(w) >= 4
                        and w[-1][0] - w[0][0] >= args.qs_window * 0.8):
                    slope = (w[-1][1] - w[0][1]) / (w[-1][0] - w[0][0])
                    if abs(slope) < args.qs_tol:
                        reason = 'quasi-steady'
                        break
                if um > args.umax_cap:
                    reason = 'umax-cap'
                    break
        sn_end = float(np.mean([sv for _, sv in hist[-20:]]))
        if args.dump_every:
            dump_frame(it, d, phase)          # rung-end frame: every rung
        print(f'[{args.tag}] {phase} d={d:.4f} -> {reason} steps={it} '
              f'S_nw={sn_end:.4f} ({time.time()-t0:.0f}s)', flush=True)
        return dict(d=d, pc=d / 3.0, phase=phase, steps=it,
                    reason=reason, s_nw=sn_end)

    for it in range(1, args.equil_steps + 1):
        s.step()
    print(f'[{args.tag}] equil done', flush=True)

    ladder = []
    for k, d in enumerate(args.ds_drain):
        ladder.append(run_hold(d, f'drain{k:02d}', 'drain'))
        _save_partial(args, ladder)
    for k, d in enumerate(args.ds_imbibe):
        ladder.append(run_hold(d, f'imb{k:02d}', 'imbibe'))
        _save_partial(args, ladder)

    # ---- trapped cluster analysis on the final state ----
    psi = s.psi_snapshot()
    red_dom = (psi[dom, :, :] > 0.0) & dom_pore
    lab, n = ndimage.label(red_dom)
    sizes = np.sort(ndimage.sum(red_dom, lab, range(1, n + 1)))[::-1]
    total_red = float(red_dom.sum())
    s_nr = total_red / pore_cells
    mid_slice_png(psi, os.path.join(out, 'final.png'),
                  f'{args.tag}: S_nr={s_nr:.3f}, clusters={n}, '
                  f'largest={sizes[0] if n else 0:.0f}')
    fl = s.reservoir_fluxes()
    np.savez_compressed(os.path.join(out, 'final.npz'), psi=psi,
                        solid=solid, sizes=sizes)
    summary = dict(args=vars(args), ladder=ladder, s_nr=s_nr,
                   n_clusters=n, largest=float(sizes[0]) if n else 0.0,
                   sizes_top=[float(v) for v in sizes[:50]], inj=fl)
    with open(os.path.join(out, 'report.json'), 'w',
              encoding='utf-8') as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f'[{args.tag}] I-R DONE: S_i={ladder[len(args.ds_drain)-1]["s_nw"]:.3f}'
          f' -> S_nr={s_nr:.3f}, clusters={n}, '
          f'largest={sizes[0] if n else 0:.0f}', flush=True)
    del s


if __name__ == '__main__':
    main()
