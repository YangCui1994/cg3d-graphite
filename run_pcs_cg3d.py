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

PR-5 (2026-09-19): geometry/ladder/convergence live in cg3d.protocol
(OpenSystem + run_hold) — shared verbatim with run_ir_cg3d.py; this
driver keeps argparse, frame naming, sentry and report layout.

Run from repo root:
  python run_pcs_cg3d.py --geo results_p3_geo/finney_r25_n150.npz \
      --tag p3a_tune --ds 0.036 0.048 0.062 0.080 0.104 0.134 0.174 0.22
"""
import argparse
import json
import os
import time

import matplotlib
matplotlib.use('Agg')

import numpy as np

from run_common import mid_slice_png
from cg3d import OpenSystem, run_hold, run_equil

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
    ap.add_argument('--qs-mode', choices=('sat', 'multi'), default='sat',
                    help="quasi-steady exit rule (PR-3 task 2.4): 'sat' = "
                         "legacy saturation-slope only (baseline-"
                         "comparable); 'multi' = saturation AND pressure "
                         "AND flux AND kinetic. The convergence record is "
                         "always written either way.")
    ap.add_argument('--pc-drift-tol', type=float, default=0.01,
                    help='multi-mode: rel pc_measured (max-min) over the '
                         'trailing window')
    ap.add_argument('--flux-tol', type=float, default=1e-6,
                    help='multi-mode: net colour flux rate per pore cell '
                         'per step')
    ap.add_argument('--u-rel-tol', type=float, default=0.05,
                    help='multi-mode: rel u_rms (max-min) over the window')
    ap.add_argument('--every', type=int, default=500)
    ap.add_argument('--dump-every', type=int, default=20000,
                    help='also save an int8 psi frame every N steps to '
                         '<out>/frames/ (0 = off).  Frames are quantised at '
                         '0.01 psi and cropped to the pore domain; the solid '
                         'is written once as f_solid.npz.  For animations -- '
                         'see 2phase/viz3d.py animate.')
    ap.add_argument('--umax-cap', type=float, default=0.12)
    ap.add_argument('--pc-band', type=int, default=4,
                    help='width [lu] of the pore bands just inside each '
                         'membrane used for pc_measured (the pressure the '
                         'sample actually sees; reservoir rho is pinned, '
                         'so its mean is trivially the nominal value)')
    ap.add_argument('--tag', required=True)
    args = ap.parse_args()

    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)

    sys_ = OpenSystem(args.geo, args.capa, args.psi_solid,
                      res_thick=args.res_thick, pc_band=args.pc_band)
    s = sys_.s
    print(f'[{args.tag}] geo {sys_.shape[0]}x{sys_.shape[1]}x{sys_.shape[2]} '
          f'pore_cells={int(sys_.pore_cells)}', flush=True)
    m0 = dict(tot=s.total_mass(), r=s.color_masses()[0],
              b=s.color_masses()[1])

    dump_dir = os.path.join(out, 'frames')
    if args.dump_every:
        os.makedirs(dump_dir, exist_ok=True)
        np.savez_compressed(os.path.join(dump_dir, 'f_solid.npz'),
                            solid=sys_.solid[sys_.dom, :, :].astype(np.int8))
        print(f'[{args.tag}] dumping a frame every {args.dump_every} steps '
              f'-> {dump_dir}', flush=True)

    def make_dump_frame(d):
        """int8-quantised psi, cropped to the pore domain.

        2026-09-15 user rule: output must never be head/tail-only, so
        --dump-every now defaults ON (20000).  Frames carry the rung delta
        in the name — a bare step counter let later rungs overwrite earlier
        rungs' frames (gx2_drain kept only d03's)."""
        def _dump(it):
            psi = s.psi_snapshot()[sys_.dom, :, :]
            red = np.where(sys_.dom_pore, (psi + 1.0) / 2.0, 0.0)
            q = np.clip(np.rint(psi * 100.0), -127, 127).astype(np.int8)
            np.savez_compressed(
                os.path.join(dump_dir, f'd{d:.4f}_{it:07d}.npz'),
                psi_q=q, it=it, d=d,
                s_nw=np.float32(red.sum() / sys_.pore_cells))
        return _dump

    # ---- equil at d=0, then ladder ----
    t0 = time.time()
    equil_s = run_equil(args, sys_, sample=True)
    print(f'[{args.tag}] equil {args.equil_steps} steps: S_nw='
          f'{equil_s:.4f} ({time.time()-t0:.0f}s)', flush=True)

    ladder = []
    for k, d in enumerate(args.ds):
        row = run_hold(args, sys_, d, f'd{k:02d}_{d:.3f}',
                       dump_frame=make_dump_frame(d))
        ladder.append(row)
        with open(os.path.join(out, 'report_partial.json'), 'w',
                  encoding='utf-8') as f:      # survives an interrupted run
            json.dump(dict(args=vars(args),
                           note='incremental checkpoint', ladder=ladder),
                      f, indent=1, ensure_ascii=False)
        mid_slice_png(s.psi_snapshot(),
                      os.path.join(out, f'psi_d{k:02d}_{d:.3f}_'
                                  f'{row["steps"]:06d}.png'),
                      f'd{k:02d}_{d:.3f}: d={d:.3f} Pc={d/3.0:.4f} '
                      f'S_nw={row["s_nw"]:.3f} ({row["reason"]})',
                      contour=True)

    # ---- save ----
    fin = s.psi_snapshot()
    np.savez_compressed(os.path.join(out, 'final.npz'), psi=fin,
                        solid=sys_.solid, ds=np.array(args.ds))
    fl = s.reservoir_fluxes()
    m1 = dict(tot=s.total_mass(), r=s.color_masses()[0],
              b=s.color_masses()[1])
    sentry = dict(leak_r=abs((m1['r'] - m0['r']) - fl['inj_r']) / m0['tot'],
                  leak_b=abs((m1['b'] - m0['b']) - fl['inj_b']) / m0['tot'],
                  leak_m=abs((m1['tot'] - m0['tot']) - fl['inj_m'])
                  / m0['tot'])
    summary = dict(args=vars(args), geo=sys_.geo_meta,
                   sigma_lb=1.012 * args.capa,
                   n_spheres_region='Finney interior box', ladder=ladder,
                   equil_s_nw=equil_s, sentry=sentry,
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
