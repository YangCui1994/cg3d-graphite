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

from run_common import (mid_slice_png, region_stats, eval_convergence,
                        label_periodic)
import numpy as np



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
    ap.add_argument('--pc-band', type=int, default=4,
                    help='width [lu] of the pore bands just inside each '
                         'membrane used for pc_measured (reservoir rho is '
                         'pinned, so its mean is trivially the nominal value)')
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
        """PR-1 instruments (Plan_20260919_v2 2.1-2.3), mirroring
        run_pcs_cg3d.measure."""
        psi = s.psi_snapshot()
        rho, v = s.macro_snapshot()
        red = np.where(dom_pore, (psi[dom, :, :] + 1.0) / 2.0, 0.0)
        rho_c, psi_c, v_c = rho[dom, :, :], psi[dom, :, :], v[dom, :, :, :]
        umax = float(np.sqrt(v_c[..., 0]**2 + v_c[..., 1]**2
                            + v_c[..., 2]**2).max())
        rs_in = region_stats(rho, psi, v, res_in.astype(bool))
        rs_out = region_stats(rho, psi, v, res_out.astype(bool))
        band_in_m = np.zeros_like(dom_pore)
        band_in_m[:args.pc_band] = dom_pore[:args.pc_band]
        band_out_m = np.zeros_like(dom_pore)
        band_out_m[-args.pc_band:] = dom_pore[-args.pc_band:]
        band_in = region_stats(rho_c, psi_c, v_c, band_in_m)
        band_out = region_stats(rho_c, psi_c, v_c, band_out_m)
        fd = region_stats(rho_c, psi_c, v_c, dom_pore)
        fl = s.reservoir_fluxes()
        return dict(s_nw=float(red.sum() / pore_cells),
                    s_nw_binary=float(((psi_c > 0.0) & dom_pore).sum()
                                      / pore_cells),
                    umax=umax,
                    rho_in_mean=rs_in['rho_mean'],
                    rho_out_mean=rs_out['rho_mean'],
                    p_in_mean=rs_in['p_mean'], p_out_mean=rs_out['p_mean'],
                    pc_band_in=band_in['p_mean'],
                    pc_band_out=band_out['p_mean'],
                    pc_measured=band_in['p_mean'] - band_out['p_mean'],
                    u_rms=fd['v_rms'], u_bulk_x=fd['v_bulk'][0],
                    inj_r=fl['inj_r'], inj_b=fl['inj_b'], inj_m=fl['inj_m'])

    def run_hold(d, label, phase):
        set_ladder(d)
        t0 = time.time()
        hist = []      # (it, s_nw): quasi-steady slope, unchanged
        samples = []   # (it, full diagnostic dict): rung-tail means
        it = 0
        reason = 'max-steps'
        while it < args.max_steps:
            it += 1
            s.step()
            if args.dump_every and it % args.dump_every == 0:
                dump_frame(it, d, phase)
            if it % args.every == 0:
                m = measure()
                hist.append((it, m['s_nw']))
                samples.append((it, m))
                w = [(i, sv) for i, sv in hist if i > it - args.qs_window]
                if (it >= args.min_steps and len(w) >= 4
                        and w[-1][0] - w[0][0] >= args.qs_window * 0.8):
                    slope = (w[-1][1] - w[0][1]) / (w[-1][0] - w[0][0])
                    if abs(slope) < args.qs_tol:
                        win = [(a2, dm) for a2, dm in samples
                               if a2 > it - args.qs_window]
                        conv = eval_convergence(
                            win, pore_cells, args.qs_tol,
                            args.pc_drift_tol, args.flux_tol,
                            args.u_rel_tol)
                        needed = (['saturation'] if args.qs_mode == 'sat'
                                  else ('saturation', 'pressure', 'flux',
                                        'kinetic'))
                        if all(c in conv['criteria_passed']
                               for c in needed):
                            reason = 'quasi-steady'
                            break
                if m['umax'] > args.umax_cap:
                    reason = 'umax-cap'
                    break
        sn_end = float(np.mean([sv for _, sv in hist[-20:]])) if hist else None
        diag = [dm for _, dm in samples[-20:]]
        tmean = lambda k: (float(np.mean([dm[k] for dm in diag]))
                           if diag else None)
        win = [(i, dm) for i, dm in samples if i > it - args.qs_window]
        if len(win) >= 2 and win[-1][0] > win[0][0]:
            span = win[-1][0] - win[0][0]
            flux_r_rate = (win[-1][1]['inj_r'] - win[0][1]['inj_r']) / span
            flux_b_rate = (win[-1][1]['inj_b'] - win[0][1]['inj_b']) / span
        else:
            flux_r_rate = flux_b_rate = None
        conv = eval_convergence(win, pore_cells, args.qs_tol,
                                args.pc_drift_tol, args.flux_tol,
                                args.u_rel_tol)
        conv['exit'] = dict(mode=args.qs_mode, reason=reason)
        if args.dump_every:
            dump_frame(it, d, phase)          # rung-end frame: every rung
        print(f'[{args.tag}] {phase} d={d:.4f} -> {reason} steps={it} '
              f'S_nw={sn_end:.4f} ({time.time()-t0:.0f}s)', flush=True)
        return dict(d=d, pc_nominal=d / 3.0, pc_measured=tmean('pc_measured'),
                    rho_in_mean=tmean('rho_in_mean'),
                    rho_out_mean=tmean('rho_out_mean'),
                    p_in_mean=tmean('p_in_mean'), p_out_mean=tmean('p_out_mean'),
                    u_rms=tmean('u_rms'), u_bulk_x=tmean('u_bulk_x'),
                    flux_r_rate=flux_r_rate, flux_b_rate=flux_b_rate,
                    phase=phase, steps=it, reason=reason, s_nw=sn_end,
                    s_nw_binary=tmean('s_nw_binary'),
                    convergence=conv)

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
    # PR-3 tasks 2.5-2.7: binary (psi > 0) vs continuous saturation, and
    # connectivity-parameterised clusters WITH periodic y/z merging (the
    # solver is y/z-periodic; plain ndimage.label splits spanning
    # clusters, over-counting n and under-counting 'largest').
    psi = s.psi_snapshot()
    red_dom = (psi[dom, :, :] > 0.0) & dom_pore
    lab, sizes = label_periodic(red_dom, conn=args.conn)
    n = int(len(sizes))
    total_red = float(red_dom.sum())
    s_nr = total_red / pore_cells                    # binary (legacy key)
    red_cont = np.where(dom_pore, (psi[dom, :, :] + 1.0) / 2.0, 0.0)
    s_nr_continuous = float(red_cont.sum() / pore_cells)
    mid_slice_png(psi, os.path.join(out, 'final.png'),
                  f'{args.tag}: S_nr={s_nr:.3f} (cont {s_nr_continuous:.3f}), '
                  f'clusters={n} (conn{args.conn}, periodic), '
                  f'largest={sizes[0] if n else 0.0:.0f}')
    fl = s.reservoir_fluxes()
    np.savez_compressed(os.path.join(out, 'final.npz'), psi=psi,
                        solid=solid, sizes=sizes)
    summary = dict(args=vars(args), ladder=ladder, s_nr=s_nr,
                   s_nr_continuous=s_nr_continuous,
                   cluster_topology=dict(conn=args.conn, periodic='y/z'),
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
