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

PR-7 (2026-09-19): full-state checkpoints (cg3d.checkpoint), as in
run_pcs_cg3d.py: equil-end + every-rung-end checkpoints under
<out>/ckpt/, a rolling mid-rung live checkpoint (--ckpt-every) and
--resume {continue,new}.  Continuing a drainage run from a
run_pcs_cg3d.py checkpoint with THIS driver's --ds-imbibe plan
(--resume-plan new) is the cross-process "drain elsewhere, imbibe
here" branch.  See CHECKPOINT_RESUME.md.

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
from cg3d import OpenSystem, run_hold, run_equil, checkpoint


def _save_partial(args, ladder, resumed_from=None):
    """Incremental checkpoint: the partial ladder survives an interrupted
    run (2026-09-15 rule — output must never be head/tail-only)."""
    with open(os.path.join('results_pcs_cg3d', args.tag,
                           'report_partial.json'), 'w',
              encoding='utf-8') as f:
        json.dump(dict(args=vars(args), note='incremental checkpoint',
                       ladder=ladder, resumed_from=resumed_from),
                  f, indent=1, ensure_ascii=False)


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
    ap.add_argument('--resume', default=None,
                    help='checkpoint npz (<out>/ckpt/... or a drainage '
                         'checkpoint from run_pcs_cg3d.py with '
                         '--resume-plan new): restore the full solver '
                         'state and continue from there')
    ap.add_argument('--resume-plan', choices=('continue', 'new'),
                    default='continue',
                    help="continue = rerun the checkpoint's remaining rungs "
                         "into the SAME output dir (crash recovery; config "
                         "must match the checkpoint exactly, driver "
                         "included).  new = treat the restored state as the "
                         "starting configuration and run THIS invocation's "
                         "--ds-drain/--ds-imbibe plan into this --tag dir "
                         "(process switch / sensitivity branch; "
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

    out = os.path.join('results_pcs_cg3d', args.tag)
    os.makedirs(out, exist_ok=True)
    ck_dir = os.path.join(out, 'ckpt')
    os.makedirs(ck_dir, exist_ok=True)

    # ---- run plan resolution: fresh, resume-continue or resume-new ----
    def _cli_pairs():
        return ([['drain', float(x)] for x in args.ds_drain]
                + [['imbibe', float(x)] for x in args.ds_imbibe])

    ladder = []
    it_glob = 0
    rung_base = 0
    it_start0 = 0

    if args.resume:
        meta = checkpoint.read_meta(args.resume)
        if args.resume_plan == 'continue':
            checkpoint.check_continue(args, meta, 'ir')
            if _cli_pairs() != [[p, float(d)] for p, d in meta['plan_full']]:
                raise SystemExit('--ds-drain/--ds-imbibe differ from the '
                                 'checkpointed ladder; use --resume-plan '
                                 'new to run a different plan')
            geo, capa, psi_solid = (meta['geo'], meta['capa'],
                                    meta['psi_solid'])
            res_thick, pc_band = meta['res_thick'], meta['pc_band']
            plan = [(p, float(d)) for p, d in meta['plan_remaining']]
            it_glob = meta['it_total']
            rung_base = meta['rung_idx'] + (
                1 if meta['state'] == 'rung_end' else 0)
            it_start0 = meta['it_rung'] if meta['state'] == 'mid_rung' else 0
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
            plan = _cli_pairs()

        sys_ = OpenSystem(geo, capa, psi_solid,
                          res_thick=res_thick, pc_band=pc_band)
        s = sys_.s
        checkpoint.restore_state(s, args.resume)
        if args.resume_plan == 'new':
            checkpoint.zero_counters(s)
        print(f'[{args.tag}] RESUMED from {args.resume} '
              f'(source driver={meta.get("driver")}, '
              f'state={meta["state"]}, it_total={it_glob}, '
              f'rung_base={rung_base}, plan={plan})', flush=True)
    else:
        geo, capa, psi_solid = args.geo, args.capa, args.psi_solid
        res_thick, pc_band = args.res_thick, args.pc_band
        plan = _cli_pairs()
        sys_ = OpenSystem(geo, capa, psi_solid,
                          res_thick=res_thick, pc_band=pc_band)
        s = sys_.s

    print(f'[{args.tag}] geo {sys_.shape[0]}x{sys_.shape[1]}x{sys_.shape[2]} '
          f'pore_cells={int(sys_.pore_cells)}', flush=True)

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
            dict(driver='ir', tag=args.tag, geo=geo, capa=capa,
                 psi_solid=psi_solid, res_thick=res_thick,
                 pc_band=pc_band, state=state, rung_idx=rung_idx,
                 it_rung=it_rung, it_total=it_total, d=float(d),
                 plan_full=_cli_pairs(),
                 plan_remaining=[[p, float(x)] for p, x in plan_remaining]))

    if not args.resume:
        run_equil(args, sys_)
        print(f'[{args.tag}] equil done', flush=True)
        it_glob = args.equil_steps
        _write_ckpt('equil_end', -1, 0.0, 0, it_glob, plan)

    for k, (phase, d) in enumerate(plan):
        rung_idx = rung_base + k
        ph_k = sum(1 for p, _ in plan[:k] if p == phase)
        label = f'{phase}{ph_k:02d}'
        it_start = it_start0 if k == 0 else 0
        # resumed runs number frames past the snapshot point; fresh runs
        # keep the legacy per-rung-local numbering
        off = (it_glob - it_start) if args.resume else 0

        def _live(itg, d_=d, ri_=rung_idx, off_=off, is_=it_start,
                  ig_=it_glob, k_=k):
            _write_ckpt('mid_rung', ri_, d_, itg - off_,
                        ig_ + (itg - off_ - is_), plan[k_:])

        ladder.append(run_hold(args, sys_, d, label, phase,
                               dump_frame=make_dump_frame(d, phase),
                               rung_end_frame=True,
                               it_start=it_start, it_offset=off,
                               live_ckpt=_live, ckpt_every=args.ckpt_every))
        it_glob += ladder[-1]['steps'] - it_start
        _save_partial(args, ladder, resumed_from=args.resume)
        _write_ckpt('rung_end', rung_idx, d, ladder[-1]['steps'], it_glob,
                    plan[k + 1:])

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
    drain_rows = [r for r in ladder if r.get('phase') == 'drain']
    s_i = drain_rows[-1]['s_nw'] if drain_rows else None
    summary = dict(args=vars(args), ladder=ladder, s_nr=s_nr,
                   s_nr_continuous=s_nr_continuous,
                   cluster_topology=dict(conn=args.conn, periodic='y/z'),
                   n_clusters=n, largest=float(sizes[0]) if n else 0.0,
                   sizes_top=[float(v) for v in sizes[:50]], inj=fl,
                   s_i=s_i, resumed_from=args.resume)
    with open(os.path.join(out, 'report.json'), 'w',
              encoding='utf-8') as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f'[{args.tag}] I-R DONE: '
          f'S_i={s_i:.3f} -> S_nr={s_nr:.3f}, clusters={n}, '
          f'largest={sizes[0] if n else 0.0:.0f}', flush=True)
    del s


if __name__ == '__main__':
    main()
