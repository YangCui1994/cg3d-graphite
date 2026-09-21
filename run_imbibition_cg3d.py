"""
3D CG direct-imbibition driver (CG3D-IMB-001, 2026-09-21)
=========================================================
Independent, fresh-start direct imbibition: an initially gas-filled
porous graphite structure is contacted by electrolyte from ONE side.
This is NOT the drainage -> imbibition I-R hysteresis protocol of
run_ir_cg3d.py (which is unchanged); no drainage checkpoint or
residual-liquid state is involved.

Layout (orientation='imbibition' in cg3d.protocol.OpenSystem; phase
roles per .agent/decisions/DIRECT_IMBIBITION_BASELINE.md):

  x: [wall | liquid reservoir psi=-1 | mem_r (passes liquid) |
      left open-pore buffer, liquid | first --prewet-layers pore
      layers of the REAL structure, liquid | remaining real pore
      space, gas | right open-pore buffer, gas |
      mem_b (passes gas) | gas reservoir psi=+1 | wall]

  LEFT = liquid contact                 RIGHT = gas exit

Baseline drive: --delta 0 (default) -> equal reservoir densities
(1.0 / 1.0), so the imbibition is spontaneous / capillary-driven.
--delta != 0 would be pressure-assisted imbibition (FUTURE WORK, not
validated by this task).

--prewet-layers is REQUIRED on purpose: the physically preferred value
is unresolved (provisional numerical example: 4 lu).  Do not treat any
particular value as physically validated.

Protocol differences vs the drainage drivers, deliberate:
  * NO equilibration phase: at d=0 the capillary drive acts from step 1,
    so settling steps would run part of the experiment before the
    measurement starts.  Stepping starts at it=1 from the IC.
  * The initial state itself is a deliverable: an IC frame (psi_ic.npz
    + ic.png) is always written.
Convergence/exit rules, frames, checkpoints reuse cg3d.protocol.run_hold
and the PR-7 checkpoint machinery verbatim (single rung at --delta).

Run from repo root:
  python run_imbibition_cg3d.py --geo geo_graphite_228b14.npz \
      --tag imb_n4 --prewet-layers 4
"""
import argparse
import json
import os

import matplotlib
matplotlib.use('Agg')

import numpy as np

from run_common import mid_slice_png, label_periodic
from cg3d import OpenSystem, run_hold, checkpoint


def _save_partial(args, ladder):
    """Incremental checkpoint (2026-09-15 rule: never head/tail-only)."""
    with open(os.path.join('results_imb_cg3d', args.tag,
                           'report_partial.json'), 'w',
              encoding='utf-8') as f:
        json.dump(dict(args=vars(args), note='incremental checkpoint',
                       ladder=ladder), f, indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--geo', required=True)
    ap.add_argument('--capa', type=float, default=0.06)
    ap.add_argument('--psi-solid', type=float, default=-0.68,
                    help='graphite electrode convention (theta_liq ~ 30 '
                         'deg, docs/ALGORITHM.md §6); the drainage '
                         'drivers default to -0.75 (Finney line)')
    ap.add_argument('--prewet-layers', type=int, required=True,
                    help='N real-structure pore layers pre-wetted liquid '
                         'adjacent to the liquid-contact side.  REQUIRED '
                         'because the physically preferred value is '
                         'UNRESOLVED — any value used (e.g. 4) is a '
                         'provisional numerical baseline, not a validated '
                         'physical parameter.')
    ap.add_argument('--delta', type=float, default=0.0,
                    help='reservoir density difference d (Pc = cs^2 d). '
                         'The validated direct-imbibition baseline is '
                         'd=0 (equal reservoir densities, spontaneous/'
                         'capillary-driven). d != 0 = pressure-assisted '
                         'imbibition: FUTURE WORK, not validated.')
    ap.add_argument('--res-thick', type=int, default=8)
    ap.add_argument('--min-steps', type=int, default=15000)
    ap.add_argument('--max-steps', type=int, default=150000)
    ap.add_argument('--qs-window', type=int, default=15000)
    ap.add_argument('--qs-tol', type=float, default=5e-7)
    ap.add_argument('--qs-mode', choices=('sat', 'multi'), default='sat')
    ap.add_argument('--pc-drift-tol', type=float, default=0.01)
    ap.add_argument('--flux-tol', type=float, default=1e-6)
    ap.add_argument('--u-rel-tol', type=float, default=0.05)
    ap.add_argument('--conn', type=int, choices=(6, 18, 26), default=6,
                    help='cluster connectivity for the residual-gas CCDF '
                         '(periodic y/z merge always on)')
    ap.add_argument('--every', type=int, default=500)
    ap.add_argument('--umax-cap', type=float, default=0.12)
    ap.add_argument('--dump-every', type=int, default=20000,
                    help='int8 psi frame every N steps (DEFAULT ON per '
                         '2026-09-15 user rule; 0 disables)')
    ap.add_argument('--pc-band', type=int, default=4)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--ckpt-every', type=int, default=20000,
                    help='rolling live checkpoint every N steps mid-rung '
                         '(0 = off; multiple of --every).  Rung-end '
                         'checkpoint is ALWAYS written.')
    args = ap.parse_args()

    if args.ckpt_every and args.ckpt_every % args.every:
        raise SystemExit('--ckpt-every must be a multiple of --every')

    out = os.path.join('results_imb_cg3d', args.tag)
    os.makedirs(out, exist_ok=True)
    ck_dir = os.path.join(out, 'ckpt')
    os.makedirs(ck_dir, exist_ok=True)

    sys_ = OpenSystem(args.geo, args.capa, args.psi_solid,
                      res_thick=args.res_thick, pc_band=args.pc_band,
                      orientation='imbibition',
                      prewet_layers=args.prewet_layers)
    s = sys_.s
    xr = sys_.x_real
    print(f'[{args.tag}] geo {sys_.shape[0]}x{sys_.shape[1]}x'
          f'{sys_.shape[2]} pore_cells(dom)={int(sys_.pore_cells)}', flush=True)
    print(f'[{args.tag}] direct imbibition: real structure x=[{xr.start},'
          f'{xr.stop}), pre-wet liquid x=[{xr.start},'
          f'{xr.start + args.prewet_layers}), delta={args.delta} '
          f'(reservoirs: left psi=-1 rho={1.0 + args.delta / 2.0}, '
          f'right psi=+1 rho={1.0 - args.delta / 2.0})', flush=True)

    # ---- IC artifacts: the initial state is itself a deliverable ----
    psi0 = s.psi_snapshot()
    np.savez_compressed(
        os.path.join(out, 'psi_ic.npz'),
        psi=psi0[sys_.dom, :, :].astype(np.float32),
        solid=sys_.solid[sys_.dom, :, :].astype(np.int8),
        prewet_layers=args.prewet_layers, delta=args.delta)
    mid_slice_png(psi0, os.path.join(out, 'ic.png'),
                  f'{args.tag} IC: prewet={args.prewet_layers} lu, '
                  f'd={args.delta}')

    dump_dir = os.path.join(out, 'frames')
    if args.dump_every:
        os.makedirs(dump_dir, exist_ok=True)
        np.savez_compressed(os.path.join(dump_dir, 'f_solid.npz'),
                            solid=sys_.solid[sys_.dom, :, :].astype(np.int8))

    def _dump(it):
        psi = s.psi_snapshot()
        q = np.clip(np.rint(psi[sys_.dom, :, :] * 100.0), -127, 127
                    ).astype(np.int8)
        red = np.where(sys_.dom_pore,
                       (psi[sys_.dom, :, :] + 1.0) / 2.0, 0.0)
        np.savez_compressed(
            os.path.join(dump_dir, f'imb_d{args.delta:.4f}_{it:07d}.npz'),
            psi_q=q, it=it, d=args.delta,
            s_nw=np.float32(red.sum() / sys_.pore_cells))

    def _live(itg):
        checkpoint.save_state(
            s, os.path.join(ck_dir, 'live.npz'),
            dict(driver='imb', tag=args.tag, geo=args.geo, capa=args.capa,
                 psi_solid=args.psi_solid, res_thick=args.res_thick,
                 pc_band=args.pc_band, state='mid_rung', rung_idx=0,
                 it_rung=itg, it_total=itg, d=float(args.delta),
                 prewet_layers=args.prewet_layers,
                 plan_full=[['imbibe', float(args.delta)]],
                 plan_remaining=[]))

    ladder = [run_hold(args, sys_, args.delta, 'imb00', 'imbibe',
                       dump_frame=_dump if args.dump_every else None,
                       rung_end_frame=True,
                       live_ckpt=_live, ckpt_every=args.ckpt_every)]
    _save_partial(args, ladder)
    checkpoint.save_state(
        s, os.path.join(ck_dir,
                        f'rung00_d{args.delta:.4f}_it{ladder[0]["steps"]:07d}.npz'),
        dict(driver='imb', tag=args.tag, geo=args.geo, capa=args.capa,
             psi_solid=args.psi_solid, res_thick=args.res_thick,
             pc_band=args.pc_band, state='rung_end', rung_idx=0,
             it_rung=ladder[0]['steps'], it_total=ladder[0]['steps'],
             d=float(args.delta), prewet_layers=args.prewet_layers,
             plan_full=[['imbibe', float(args.delta)]],
             plan_remaining=[]))

    # ---- residual (trapped) gas at the end of direct imbibition ----
    psi = s.psi_snapshot()
    red_dom = (psi[sys_.dom, :, :] > 0.0) & sys_.dom_pore
    lab, sizes = label_periodic(red_dom, conn=args.conn)
    n = int(len(sizes))
    s_nr = float(red_dom.sum()) / sys_.pore_cells        # dom-wide (legacy def)
    red_real = (psi[xr, :, :] > 0.0) & sys_.real_pore
    s_nr_real = float(red_real.sum()) / float(sys_.real_pore.sum())
    red_cont = np.where(sys_.dom_pore,
                        (psi[sys_.dom, :, :] + 1.0) / 2.0, 0.0)
    s_nr_continuous = float(red_cont.sum() / sys_.pore_cells)
    mid_slice_png(psi, os.path.join(out, 'final.png'),
                  f'{args.tag}: S_nr={s_nr:.3f} (real-only {s_nr_real:.3f}, '
                  f'cont {s_nr_continuous:.3f}), clusters={n} '
                  f'(conn{args.conn}, periodic), '
                  f'largest={sizes[0] if n else 0.0:.0f}')
    fl = s.reservoir_fluxes()
    np.savez_compressed(os.path.join(out, 'final.npz'), psi=psi,
                        solid=sys_.solid, sizes=sizes)
    summary = dict(args=vars(args), ladder=ladder, s_nr=s_nr,
                   s_nr_real=s_nr_real, s_nr_continuous=s_nr_continuous,
                   cluster_topology=dict(conn=args.conn, periodic='y/z'),
                   n_clusters=n, largest=float(sizes[0]) if n else 0.0,
                   sizes_top=[float(v) for v in sizes[:50]], inj=fl,
                   real_dom=[xr.start, xr.stop])
    with open(os.path.join(out, 'report.json'), 'w',
              encoding='utf-8') as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f'[{args.tag}] DIRECT IMBIBITION DONE: '
          f'S_nr={s_nr:.3f} (real-only {s_nr_real:.3f}), clusters={n}, '
          f'largest={sizes[0] if n else 0.0:.0f}', flush=True)
    del s


if __name__ == '__main__':
    main()
