"""viz3d.py — PyVista rendering layer for 3D CG / porous-media runs.

Replaces the matplotlib Poly3DCollection route in vis3d_report.py, which
cannot order translucent surfaces correctly (painter's algorithm) and has
no depth cue.  Everything here is offscreen, scripted and reproducible:
post-processing never touches Taichi, so it carries no JIT-compile cost and
can run after a GPU batch has exited.

Design rules (see LBM/notes/VIZ_3D_STYLE.md):
  * at most ONE translucent phase per view — the solid ghost; a 200^3 random
    pack muddies to mud otherwise.  Solid is clipped to the same cutaway
    plane as the fluids ("look into an open box").
  * orthographic projection always — perspective makes far clusters look
    smaller and quietly breaks cross-run comparison of cluster sizes.
  * focus phase opaque, context phases translucent or clipped away.
  * the camera is derived from the domain box, not the data, so every run of
    the same geometry renders from an identical viewpoint.
  * two style presets: ``report`` (white page, blue liquid / red-orange
    non-wetting / translucent grey solid) and ``slide`` (dark ground, white
    gas).  Curves (Pc-S, k, CCDF, I-R) stay in matplotlib 2D.

Axis order: run npz stores fields as (nx, ny, nz) while VTK ImageData is
x-fastest, so every field is uploaded as ``a.ravel(order='F')`` with
``dimensions=a.shape``.  Getting this wrong transposes the geometry.

Usage (from 2phase/):
  python viz3d.py figset   --run results_pcs_cg3d/p3b_finney
  python viz3d.py figset   --run results_pcs_cg3d/p4_siA --style slide
  python viz3d.py geometry --run results_pcs_cg3d/p3b_finney --full
  python viz3d.py cutaway  --run results_pcs_cg3d/p3b_finney --focus wet
  python viz3d.py clusters --run results_pcs_cg3d/p4_siA --top 12
  python viz3d.py slices   --run results_pcs_cg3d/p3b_finney
  python viz3d.py animate  --series results_pcs_cg3d/<tag>/frames --opaque both       --view top --cut-axis z --cut-keep lo --cutaway 0.65 --ghost-alpha 0.12
  python viz3d.py selfcheck --run results_pcs_cg3d/p3b_finney
  python viz3d.py explore  --series results_pcs_cg3d/<tag>/frames  # on-screen

``explore`` is the one interactive entry point (mouse orbit + a frame slider
+ key toggles); everything else is offscreen and scriptable.
"""
from __future__ import annotations

import argparse
import os
import sys

"""Thin CLI entry; the implementation lives in the viz3dlib/ package
(split 2026-09-16, PLAN_code_cleanup_2026-09 Step 3 — zero behavior
change; the original module docstring above is kept verbatim)."""

from viz3dlib.anim import animate
from viz3dlib.explore import explore
from viz3dlib.figset import figset
from viz3dlib.panels import panel_clusters, panel_cutaway, panel_geometry, panel_slices
from viz3dlib.runio import load_run
from viz3dlib.selfcheck import qa_stats, selfcheck
from viz3dlib.style_env import LEVEL_GAP, STYLE, VIEWS, WINDOW, _style, check_env
from viz3dlib import panels as _panels


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cmd', choices=['figset', 'geometry', 'cutaway',
                                    'clusters', 'slices', 'selfcheck',
                                    'animate', 'explore'])
    ap.add_argument('--run', default=None, help='run dir or final.npz')
    ap.add_argument('--tag', default=None, help='override the run tag')
    ap.add_argument('--series', default=None,
                    help='animate: frame dir, glob, or single npz')
    ap.add_argument('--solid', default=None,
                    help='animate: npz with the solid mask, when frames '
                         'do not carry it')
    ap.add_argument('--window', default=None,
                    help='animate: WxH, e.g. 1000x780')
    ap.add_argument('--duration', type=int, default=450,
                    help='animate: ms per GIF frame')
    ap.add_argument('--every', type=int, default=1,
                    help='animate: keep every Nth frame')
    ap.add_argument('--max-frames', type=int, default=None)
    ap.add_argument('--colors', type=int, default=256,
                    help='animate: GIF palette size (lower = smaller file)')
    ap.add_argument('--gif-width', type=int, default=None,
                    help='animate: downscale the GIF to this width')
    ap.add_argument('--view', default=None, choices=list(VIEWS),
                    help='camera preset: iso (up=z) or front (up=y, '
                         'landscape; cut along z with it)')
    ap.add_argument('--cut-axis', default='y', choices=list('xyz'))
    ap.add_argument('--cut-keep', default='hi', choices=['lo', 'hi'])
    ap.add_argument('--play-ms', type=int, default=450,
                    help='explore: playback interval in ms')
    ap.add_argument('--selftest', action='store_true',
                    help='explore: build the scene, exercise every key '
                         'handler and screenshot, then exit (no window loop)')
    ap.add_argument('--label-fmt', default=None,
                    help='animate: e.g. "{tag}  S_nw={s_nw:.2f}"')
    ap.add_argument('--opaque', default=None,
                    choices=['auto', 'nw', 'wet', 'both'],
                    help='which phase stays solid in the two-phase view.  '
                         'Defaults to auto (per-frame majority) for stills; '
                         'animate() defaults to nw, the invading phase in '
                         'drainage -- pass wet for imbibition.')
    ap.add_argument('--out', default=None)
    ap.add_argument('--style', default='report', choices=list(STYLE))
    ap.add_argument('--cutaway', type=float, default=0.5,
                    help='fraction of x kept (1.0 = whole box)')
    ap.add_argument('--full', action='store_true',
                    help='include wall + reservoir slabs')
    ap.add_argument('--focus', default='both',
                    choices=['both', 'nw', 'wet'])
    ap.add_argument('--level', type=float, default=None,
                    help='psi contour level (default: interface midline 0)')
    ap.add_argument('--ghost-alpha', type=float, default=None,
                    help='absolute opacity of the solid ghost (0-1).  Omit '
                         'for the per-style default.  Raise it to make the '
                         'rock more present, lower it if the pale rock washes '
                         'the fluids out.')
    ap.add_argument('--level-gap', type=float, default=LEVEL_GAP,
                    help='inset both fluid surfaces by this much (psi units) '
                         'in the two-phase panel; 0 shares the psi=0 surface')
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--scale-bar', type=float, default=None)
    ap.add_argument('--no-title', action='store_true')
    ap.add_argument('--no-flow', action='store_true',
                    help='omit the inlet/outlet arrows (on by default)')
    ap.add_argument('--decimate', type=float, default=None)
    args = ap.parse_args()
    check_env()
    if args.no_flow:
        _panels.FLOW = False

    if args.cmd == 'selfcheck':
        raise SystemExit(1 if selfcheck(args.run) else 0)

    if args.cmd == 'explore':
        if not (args.series or args.run):
            raise SystemExit('explore needs --series (or --run for a single '
                             'final state)')
        win = (1280, 1000)
        if args.window:
            try:
                win = tuple(int(v) for v in args.window.lower().split('x'))
            except Exception:                                # noqa: BLE001
                raise SystemExit('--window expects WxH, e.g. 1280x1000')
        return explore(series=args.series, run_path=args.run,
                       style_name=args.style, cutaway=args.cutaway,
                       cut_axis=args.cut_axis, cut_keep=args.cut_keep,
                       view=args.view or 'top', opaque=args.opaque or 'both',
                       ghost_alpha=(0.12 if args.ghost_alpha is None
                                    else args.ghost_alpha),
                       level_gap=args.level_gap, window=win,
                       decimate=args.decimate, max_frames=args.max_frames,
                       play_ms=args.play_ms, scale_bar=args.scale_bar,
                       selftest=args.selftest)

    if args.cmd == 'animate':
        if not args.series:
            raise SystemExit('animate needs --series')
        win = WINDOW
        if args.window:
            try:
                win = tuple(int(v) for v in args.window.lower().split('x'))
            except Exception:                                # noqa: BLE001
                raise SystemExit('--window expects WxH, e.g. 1000x780')
        out = args.out or 'results_p5_figs_pv3d/anim'
        os.makedirs(out, exist_ok=True)
        animate(args.series, out, args.style, cutaway=args.cutaway,
                cut_axis=args.cut_axis, cut_keep=args.cut_keep, window=win,
                duration=args.duration, ghost_alpha=args.ghost_alpha,
                scale_bar=args.scale_bar, decimate=args.decimate,
                solid_path=args.solid, label_fmt=args.label_fmt,
                every=args.every, max_frames=args.max_frames,
                colors=args.colors, gif_width=args.gif_width,
                tag=args.tag, opaque=args.opaque or 'nw',
                view=args.view or 'front')
        return

    if not args.run:
        raise SystemExit(f'{args.cmd} needs --run')

    run = load_run(args.run)
    st = _style(args.style)
    out = args.out or os.path.join('results_p5_figs_pv3d', run['tag'])
    if out.lower().endswith('.png'):
        raise SystemExit('--out is an output DIRECTORY for every command; '
                         'panel filenames are fixed')
    os.makedirs(out, exist_ok=True)
    sb = args.scale_bar if args.scale_bar is not None else (
        2 * run['R_lu'] if run['R_lu'] else 50)
    ttl = None if args.no_title else f'{run["tag"]}  (style={args.style})'

    if args.cmd == 'figset':
        figset(args.run, out, args.style, cutaway=args.cutaway,
               full=args.full, top=args.top, scale_bar=sb,
               title=not args.no_title, ghost_alpha=args.ghost_alpha)
        return
    names = {'both': 'p2_twophase', 'nw': 'p3_nonwetting',
             'wet': 'p4_wetting'}
    name = {'geometry': 'p0_geo', 'cutaway': names[args.focus],
            'clusters': 'p5_clusters', 'slices': 'p1_slices'}[args.cmd]
    out_png = os.path.join(out, f'{run["tag"]}_{name}.png')
    if args.cmd == 'geometry':
        panel_geometry(run, out_png, st, cutaway=1.0, full=args.full,
                       scale_bar=sb, title=ttl, decimate=args.decimate)
    elif args.cmd == 'cutaway':
        panel_cutaway(run, out_png, st, focus=args.focus, level=args.level,
                      cutaway=args.cutaway, full=args.full, scale_bar=sb,
                      title=ttl, decimate=args.decimate,
                      level_gap=args.level_gap,
                      ghost_alpha=args.ghost_alpha,
                      cut_axis=args.cut_axis, cut_keep=args.cut_keep,
                      view=args.view or 'iso')
    elif args.cmd == 'clusters':
        panel_clusters(run, out_png, st, top=args.top, cutaway=args.cutaway,
                       full=args.full, scale_bar=sb, title=ttl,
                       decimate=args.decimate)
    else:
        panel_slices(run, out_png, st, full=args.full)
    qa_stats(out_png)


if __name__ == '__main__':
    main()
