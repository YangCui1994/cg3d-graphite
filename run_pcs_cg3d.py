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

PR-7 (2026-09-19): full-state checkpoints (cg3d.checkpoint).  The
equilibration end and EVERY rung end write <out>/ckpt/*.npz (complete
solver state + run-plan meta, ~0.85 GB at 200^3); --ckpt-every rolls a
live mid-rung checkpoint on top.  --resume <ckpt.npz> restores the
state and either continues the remaining plan into the SAME output dir
(--resume-plan continue: crash recovery; frame/ladder numbering picks
up where the interrupted attempt left off) or branches from the saved
configuration with a new --ds / --tag / parameters (--resume-plan new:
process switches and sensitivity branches).  See CHECKPOINT_RESUME.md.

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
from cg3d import OpenSystem, run_hold, run_equil, checkpoint

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
    ap.add_argument('--resume', default=None,
                    help='checkpoint npz written by this driver '
                         '(<out>/ckpt/...): restore the full solver state '
                         'and continue from there')
    ap.add_argument('--resume-plan', choices=('continue', 'new'),
                    default='continue',
                    help="continue = rerun the checkpoint's remaining rungs "
                         "into the SAME output dir (crash recovery; config "
                         "must match the checkpoint exactly).  new = treat "
                         "the restored state as the starting configuration "
                         "and run THIS invocation's --ds plan into this "
                         "--tag dir (process switch / sensitivity branch; "
                         "equilibration is skipped, flux counters restart "
                         "at the branch point).")
    ap.add_argument('--ckpt-every', type=int, default=20000,
                    help='rolling live checkpoint <out>/ckpt/live.npz '
                         'every N steps mid-rung (0 = off; must be a '
                         'multiple of --every).  Rung-end and equil-end '
                         'checkpoints are ALWAYS written.')
    args = ap.parse_args()

    if args.ckpt_every and args.ckpt_every % args.every:
        raise SystemExit('--ckpt-every must be a multiple of --every')

    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)
    ck_dir = os.path.join(out, 'ckpt')
    os.makedirs(ck_dir, exist_ok=True)

    # ---- run plan resolution: fresh, resume-continue or resume-new ----
    ladder = []          # accumulated rung rows (resumes reload theirs)
    m0 = None            # mass baseline for the sentry (t=0 of the ckpt's run)
    equil_s = None
    it_glob = 0          # cumulative steps: equil + all completed rungs
    rung_base = 0        # global index of the first rung this process runs
    it_start0 = 0        # mid-rung resume: steps the replayed rung starts from

    if args.resume:
        meta = checkpoint.read_meta(args.resume)
        if args.resume_plan == 'continue':
            checkpoint.check_continue(args, meta, 'pcs')
            if [float(x) for x in args.ds] != \
                    [float(x) for x in meta['plan_full']]:
                raise SystemExit('--ds differs from the checkpointed '
                                 'ladder; use --resume-plan new to run a '
                                 'different plan')
            geo, capa, psi_solid = (meta['geo'], meta['capa'],
                                    meta['psi_solid'])
            res_thick, pc_band = meta['res_thick'], meta['pc_band']
            plan = [float(x) for x in meta['plan_remaining']]
            it_glob = meta['it_total']
            rung_base = meta['rung_idx'] + (
                1 if meta['state'] == 'rung_end' else 0)
            it_start0 = meta['it_rung'] if meta['state'] == 'mid_rung' else 0
            m0, equil_s = meta['m0'], meta.get('equil_s')
            partial = os.path.join(out, 'report_partial.json')
            if os.path.exists(partial):
                with open(partial, encoding='utf-8') as f:
                    ladder = json.load(f)['ladder']
                if len(ladder) != rung_base:
                    raise SystemExit(
                        f'report_partial.json has {len(ladder)} rungs but '
                        f'the checkpoint stands at {rung_base}; the report '
                        f'and the checkpoint disagree — inspect manually')
            elif rung_base:
                raise SystemExit('checkpoint says rungs are complete but '
                                 'report_partial.json is missing; cannot '
                                 'rebuild the ladder rows')
        else:                                   # branch with new plan
            geo, capa, psi_solid = args.geo, args.capa, args.psi_solid
            res_thick, pc_band = args.res_thick, args.pc_band
            plan = [float(x) for x in args.ds]

        sys_ = OpenSystem(geo, capa, psi_solid,
                          res_thick=res_thick, pc_band=pc_band)
        s = sys_.s
        checkpoint.restore_state(s, args.resume)
        if args.resume_plan == 'new':
            checkpoint.zero_counters(s)
            m0 = dict(tot=s.total_mass(), r=s.color_masses()[0],
                      b=s.color_masses()[1])
        print(f'[{args.tag}] RESUMED from {args.resume}\n'
              f'[{args.tag}] state={meta["state"]} it_total={it_glob} '
              f'rung_base={rung_base} plan={[round(d, 4) for d in plan]}',
              flush=True)
    else:
        geo, capa, psi_solid = args.geo, args.capa, args.psi_solid
        res_thick, pc_band = args.res_thick, args.pc_band
        plan = [float(x) for x in args.ds]
        sys_ = OpenSystem(geo, capa, psi_solid,
                          res_thick=res_thick, pc_band=pc_band)
        s = sys_.s

    print(f'[{args.tag}] geo {sys_.shape[0]}x{sys_.shape[1]}x{sys_.shape[2]} '
          f'pore_cells={int(sys_.pore_cells)}', flush=True)
    if m0 is None:
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
        rungs' frames (gx2_drain kept only d03's).  Resumed runs pass
        global step numbers (see run_hold it_offset) so replayed rungs
        never collide with pre-crash frames."""
        def _dump(it):
            psi = s.psi_snapshot()[sys_.dom, :, :]
            red = np.where(sys_.dom_pore, (psi + 1.0) / 2.0, 0.0)
            q = np.clip(np.rint(psi * 100.0), -127, 127).astype(np.int8)
            np.savez_compressed(
                os.path.join(dump_dir, f'd{d:.4f}_{it:07d}.npz'),
                psi_q=q, it=it, d=d,
                s_nw=np.float32(red.sum() / sys_.pore_cells))
        return _dump

    def _ckpt_path(state, rung_idx, d, it_total):
        if state == 'mid_rung':
            return os.path.join(ck_dir, 'live.npz')
        if state == 'equil_end':
            return os.path.join(ck_dir, f'equil_end_it{it_total:07d}.npz')
        return os.path.join(ck_dir,
                            f'rung{rung_idx:02d}_d{d:.4f}_it{it_total:07d}.npz')

    def _write_ckpt(state, rung_idx, d, it_rung, it_total, plan_remaining):
        checkpoint.save_state(
            s, _ckpt_path(state, rung_idx, d, it_total),
            dict(driver='pcs', tag=args.tag, geo=geo, capa=capa,
                 psi_solid=psi_solid, res_thick=res_thick,
                 pc_band=pc_band, state=state, rung_idx=rung_idx,
                 it_rung=it_rung, it_total=it_total, d=float(d),
                 plan_full=[float(x) for x in args.ds],
                 plan_remaining=[float(x) for x in plan_remaining],
                 m0=m0, equil_s=equil_s))

    # ---- equil at d=0, then ladder ----
    if not args.resume:
        t0 = time.time()
        equil_s = run_equil(args, sys_, sample=True)
        print(f'[{args.tag}] equil {args.equil_steps} steps: S_nw='
              f'{equil_s:.4f} ({time.time()-t0:.0f}s)', flush=True)
        it_glob = args.equil_steps
        _write_ckpt('equil_end', -1, 0.0, 0, it_glob, plan)

    for k, d in enumerate(plan):
        rung_idx = rung_base + k
        it_start = it_start0 if k == 0 else 0
        # resumed runs number frames past the snapshot point; fresh runs
        # keep the legacy per-rung-local numbering
        off = (it_glob - it_start) if args.resume else 0

        def _live(itg, d_=d, ri_=rung_idx, off_=off, is_=it_start,
                  ig_=it_glob, k_=k):
            _write_ckpt('mid_rung', ri_, d_, itg - off_,
                        ig_ + (itg - off_ - is_), plan[k_:])

        row = run_hold(args, sys_, d, f'd{rung_idx:02d}_{d:.3f}',
                       dump_frame=make_dump_frame(d),
                       it_start=it_start, it_offset=off,
                       live_ckpt=_live, ckpt_every=args.ckpt_every)
        it_glob += row['steps'] - it_start
        ladder.append(row)
        with open(os.path.join(out, 'report_partial.json'), 'w',
                  encoding='utf-8') as f:      # survives an interrupted run
            json.dump(dict(args=vars(args),
                           note='incremental checkpoint', ladder=ladder),
                      f, indent=1, ensure_ascii=False)
        mid_slice_png(s.psi_snapshot(),
                      os.path.join(out, f'psi_d{rung_idx:02d}_{d:.3f}_'
                                  f'{row["steps"]:06d}.png'),
                      f'd{rung_idx:02d}_{d:.3f}: d={d:.3f} Pc={d/3.0:.4f} '
                      f'S_nw={row["s_nw"]:.3f} ({row["reason"]})',
                      contour=True)
        _write_ckpt('rung_end', rung_idx, d, row['steps'], it_glob,
                    plan[k + 1:])

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
                   sigma_lb=1.012 * capa,
                   n_spheres_region='Finney interior box', ladder=ladder,
                   equil_s_nw=equil_s, sentry=sentry,
                   resumed_from=args.resume, inj=fl)
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
