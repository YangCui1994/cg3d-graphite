"""
3D CG drainage Pc-S ladder run (P3a/P3b driver, 2026-09-12)
============================================================
Mirrors the 2D run_pcs_cg_matched.py pressure ladder, but drives with
DENSITY-PRESCRIBED RESERVOIRS instead of body force (plan section 5):

  x: [wall | red reservoir rho=1+d/2 | mem_b (passes red) | DOMAIN |
      mem_r (passes blue) | blue reservoir rho=1-d/2 | wall]
  y/z: periodic.  Pc_LB = cs^2 * d = d/3.

Drainage: non-wetting red (psi=+1) invades the strongly water-wet pack
(psi_solid=-0.75 -> theta_liq ~ 21 deg) as d steps up; each hold runs
until quasi-steady (|dS_nw/dstep| < tol over a trailing window) or the
step cap.  State carries over between steps = primary drainage path on
ONE realization.

Geometry: interior sub-box of the Finney RCP specimen (npz from
finney_to_solid.py) or any (solid, meta) npz.

Run from 2phase/:
  python run_pcs_cg3d.py --geo results_p3_geo/finney_r25_n150.npz \
      --tag p3a_tune --ds 0.036 0.048 0.062 0.080 0.104 0.134 0.174 0.22
"""
import argparse
import json
import os
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from run_common import mid_slice_png
import numpy as np

OUTROOT = 'results_pcs_cg3d'



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--geo', required=True, help='npz with solid+meta')
    ap.add_argument('--capa', type=float, default=0.06,
                    help='CapA=0.06 (sigma=0.0606): keeps the rho ladder '
                         'within +-0.11 of unity; interface width is '
                         'CapA-independent (~2.2 lu, P1 sweep)')
    ap.add_argument('--psi-solid', type=float, default=-0.75)
    ap.add_argument('--ds', type=float, nargs='+',
                    default=[0.036, 0.048, 0.062, 0.080, 0.104,
                             0.134, 0.174, 0.22],
                    help='rho differences d=rho_in-rho_out per hold; '
                         'Pc = d/3')
    ap.add_argument('--res-thick', type=int, default=8)
    ap.add_argument('--equil-steps', type=int, default=20000)
    ap.add_argument('--min-steps', type=int, default=15000)
    ap.add_argument('--max-steps', type=int, default=150000)
    ap.add_argument('--qs-window', type=int, default=15000)
    ap.add_argument('--qs-tol', type=float, default=5e-7)
    ap.add_argument('--every', type=int, default=500)
    ap.add_argument('--dump-every', type=int, default=20000,
                    help='also save an int8 psi frame every N steps to '
                         '<out>/frames/ (0 = off).  Frames are quantised at '
                         '0.01 psi and cropped to the pore domain; the solid '
                         'is written once as f_solid.npz.  For animations -- '
                         'see 2phase/viz3d.py animate.')
    ap.add_argument('--umax-cap', type=float, default=0.12)
    ap.add_argument('--tag', required=True)
    args = ap.parse_args()

    from lbm_solver_cg3d import ColorGradientSolver3D

    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)

    dat = np.load(args.geo)
    solid_full = dat['solid'].astype(np.int8)
    nx, ny, nz = solid_full.shape
    geo_meta = str(dat['meta'][0]) if 'meta' in dat else '{}'
    pore_full = solid_full == 0
    print(f'[{args.tag}] geo nx={nx} phi_solid={solid_full.mean():.4f}',
          flush=True)

    # --- layout: wall | red res | mem_b | domain | mem_r | blue res | wall
    wt = 3
    rt = args.res_thick
    x_imem_in = wt + rt                    # inlet membrane plane
    x_imem_out = nx - wt - rt              # outlet membrane plane
    solid = solid_full.copy()
    solid[:wt, :, :] = 1
    solid[nx - wt:, :, :] = 1
    dom = slice(x_imem_in + 1, x_imem_out)
    dom_pore = pore_full[dom, :, :]

    psi0 = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
    psi0[wt:x_imem_in + 1, :, :] = np.where(
        pore_full[wt:x_imem_in + 1, :, :], 1.0, 0.0).astype(np.float32)
    psi0[x_imem_in, :, :] = np.where(
        pore_full[x_imem_in, :, :], 1.0, 0.0).astype(np.float32)
    # outlet membrane stays blue-pre-wet
    mem_r = np.zeros_like(solid)
    mem_b = np.zeros_like(solid)
    mem_b[x_imem_in, :, :] = 1             # inlet: blocks blue, red enters
    mem_r[x_imem_out, :, :] = 1            # outlet: blocks red, blue leaves
    res_in = np.zeros_like(solid)
    res_in[wt:x_imem_in, :, :] = 1
    res_out = np.zeros_like(solid)
    res_out[x_imem_out + 1:nx - wt, :, :] = 1

    s = ColorGradientSolver3D(nx, ny, nz, CapA=args.capa)
    s.set_psi_solid(args.psi_solid)
    s.set_membranes(mem_r, mem_b)

    def set_ladder(d):
        """rho_in = 1+d/2, rho_out = 1-d/2 -> Pc = cs^2 d."""
        s.set_reservoirs(res_in, 1.0, 1.0 + d / 2.0)
        s.set_reservoirs(res_out, -1.0, 1.0 - d / 2.0)

    set_ladder(0.0)
    s.init(psi0, solid)
    m0 = dict(tot=s.total_mass(), r=s.color_masses()[0],
              b=s.color_masses()[1])

    pore_cells = float(dom_pore.sum())

    dump_dir = os.path.join(out, 'frames')
    if args.dump_every:
        os.makedirs(dump_dir, exist_ok=True)
        np.savez_compressed(os.path.join(dump_dir, 'f_solid.npz'),
                            solid=solid[dom, :, :].astype(np.int8))
        print(f'[{args.tag}] dumping a frame every {args.dump_every} steps '
              f'-> {dump_dir}', flush=True)

    def dump_frame(it, d):
        """int8-quantised psi, cropped to the pore domain.

        2026-09-15 user rule: output must never be head/tail-only, so
        --dump-every now defaults ON (20000).  Frames carry the rung delta
        in the name — a bare step counter let later rungs overwrite earlier
        rungs' frames (gx2_drain kept only d03's)."""
        psi = s.psi_snapshot()[dom, :, :]
        red = np.where(dom_pore, (psi + 1.0) / 2.0, 0.0)
        q = np.clip(np.rint(psi * 100.0), -127, 127).astype(np.int8)
        np.savez_compressed(
            os.path.join(dump_dir, f'd{d:.4f}_{it:07d}.npz'),
            psi_q=q, it=it, d=d,
            s_nw=np.float32(red.sum() / pore_cells))

    def measure():
        psi = s.psi_snapshot()
        _, v = s.macro_snapshot()
        red = np.where(dom_pore, (psi[dom, :, :] + 1.0) / 2.0, 0.0)
        u_mag = np.sqrt((v[dom, :, :, 0])**2 + (v[dom, :, :, 1])**2
                        + (v[dom, :, :, 2])**2)
        return dict(s_nw=float(red.sum() / pore_cells),
                    umax=float(u_mag.max()))

    def run_hold(d, label):
        set_ladder(d)
        t0 = time.time()
        hist = []
        it = 0
        reason = 'max-steps'
        while it < args.max_steps:
            it += 1
            s.step()
            if args.dump_every and it % args.dump_every == 0:
                dump_frame(it, d)
            if it % args.every == 0:
                m = measure()
                hist.append((it, m['s_nw']))
                w = [(i, sv) for i, sv in hist
                     if i > it - args.qs_window]
                if (it >= args.min_steps and len(w) >= 4
                        and w[-1][0] - w[0][0] >= args.qs_window * 0.8):
                    slope = (w[-1][1] - w[0][1]) / (w[-1][0] - w[0][0])
                    if abs(slope) < args.qs_tol:
                        reason = 'quasi-steady'
                        break
                if it % 10000 == 0:
                    print(f'[{args.tag}] {label} {it} S_nw='
                          f'{hist[-1][1]:.4f} umax={m["umax"]:.3f}',
                          flush=True)
                    if m['umax'] > args.umax_cap:
                        reason = 'umax-cap'
                        break
        tail = [sv for _, sv in hist[-20:]]
        row = dict(d=d, pc=d / 3.0, steps=it, reason=reason,
                   s_nw=float(np.mean(tail)), umax_last=m['umax'],
                   wall_s=round(time.time() - t0, 1))
        mid_slice_png(s.psi_snapshot(),
                      os.path.join(out, f'psi_{label}_{it:06d}.png'),
                      f'{label}: d={d:.3f} Pc={d/3.0:.4f} '
                      f'S_nw={row["s_nw"]:.3f} ({reason})', contour=True)
        print(f'[{args.tag}] {label} -> {reason} steps={it} '
              f'S_nw={row["s_nw"]:.4f} wall={row["wall_s"]}s', flush=True)
        return row

    # ---- equil at d=0, then ladder ----
    t0 = time.time()
    hist = []
    for it in range(1, args.equil_steps + 1):
        s.step()
        if it % args.every == 0:
            hist.append((it, measure()['s_nw']))
    print(f'[{args.tag}] equil {args.equil_steps} steps: S_nw='
          f'{hist[-1][1]:.4f} ({time.time()-t0:.0f}s)', flush=True)

    ladder = []
    for k, d in enumerate(args.ds):
        ladder.append(run_hold(d, f'd{k:02d}_{d:.3f}'))
        with open(os.path.join(out, 'report_partial.json'), 'w',
                  encoding='utf-8') as f:      # survives an interrupted run
            json.dump(dict(args=vars(args),
                           note='incremental checkpoint', ladder=ladder),
                      f, indent=1, ensure_ascii=False)

    # ---- save ----
    fin = s.psi_snapshot()
    np.savez_compressed(os.path.join(out, 'final.npz'), psi=fin,
                        solid=solid, ds=np.array(args.ds))
    fl = s.reservoir_fluxes()
    m1 = dict(tot=s.total_mass(), r=s.color_masses()[0],
              b=s.color_masses()[1])
    sentry = dict(leak_r=abs((m1['r'] - m0['r']) - fl['inj_r']) / m0['tot'],
                  leak_b=abs((m1['b'] - m0['b']) - fl['inj_b']) / m0['tot'],
                  leak_m=abs((m1['tot'] - m0['tot']) - fl['inj_m'])
                  / m0['tot'])
    summary = dict(args=vars(args), geo=geo_meta,
                   sigma_lb=1.012 * args.capa,
                   n_spheres_region='Finney interior box', ladder=ladder,
                   equil_s_nw=hist[-1][1], sentry=sentry,
                   inj=fl)
    with open(os.path.join(out, 'report.json'), 'w',
              encoding='utf-8') as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f'[{args.tag}] LADDER DONE: ' + ' '.join(
        f'{r["d"]:.3f}->{r["s_nw"]:.3f}({r["reason"][:2]})'
        for r in ladder), flush=True)
    print(f'[{args.tag}] sentry {sentry}', flush=True)
    del s


if __name__ == '__main__':
    main()
