"""viz3dlib.figset — The 5-panel report figure set."""
from __future__ import annotations

import os

from .anim import montage
from .panels import panel_clusters, panel_cutaway, panel_geometry, panel_slices
from .runio import load_run
from .selfcheck import qa_stats
from .style_env import LEVEL_GAP, _style


def figset(run_path, out_dir, style_name='report', cutaway=0.5, full=False,
           top=12, scale_bar=None, title=True, ghost_alpha=None,
           panels=('geo', 'slices', 'both', 'nw', 'wet', 'clusters')):
    """The standard panel set, one camera, one cutaway, one palette.

    ``both`` (the two fluids in one frame) comes before the single-phase
    panels on purpose: it is the panel that answers "where is the gas
    relative to the liquid", and the single-phase views only make sense once
    the reader has seen both."""
    run = load_run(run_path)
    st = _style(style_name)
    os.makedirs(out_dir, exist_ok=True)
    tag = run['tag']
    R = run['R_lu']
    if scale_bar is None:
        scale_bar = 2 * R if R else 50
    unit = 'lu'
    ttl = f'{tag}  (style={style_name})' if title else None
    print(f'[{tag}] {run["npz"]}  dom_x={run["dom"].start}..{run["dom"].stop}'
          f'  R_lu={R}')
    made = []

    def _run(fn, name, **kw):
        out = os.path.join(out_dir, name)
        try:
            fn(out, **kw)
            qa_stats(out)
            made.append(out)
        except Exception as exc:                              # noqa: BLE001
            print(f'  !! {name} failed: {type(exc).__name__}: {exc}')

    if 'geo' in panels:
        _run(lambda out, **kw: panel_geometry(run, out, st, **kw),
             f'{tag}_p0_geo.png', full=full, cutaway=1.0,
             scale_bar=scale_bar, title=ttl)
    if 'slices' in panels:
        _run(lambda out, **kw: panel_slices(run, out, st, **kw),
             f'{tag}_p1_slices.png', full=full)
    if 'both' in panels:
        _run(lambda out, **kw: panel_cutaway(run, out, st, focus='both',
                                             **kw),
             f'{tag}_p2_twophase.png', cutaway=cutaway, full=full,
             scale_bar=scale_bar, title=ttl, level_gap=LEVEL_GAP,
             ghost_alpha=ghost_alpha)
    if 'nw' in panels:
        _run(lambda out, **kw: panel_cutaway(run, out, st, focus='nw', **kw),
             f'{tag}_p3_nonwetting.png', cutaway=cutaway, full=full,
             scale_bar=scale_bar, title=ttl, ghost_alpha=ghost_alpha)
    if 'wet' in panels:
        _run(lambda out, **kw: panel_cutaway(run, out, st, focus='wet', **kw),
             f'{tag}_p4_wetting.png', cutaway=cutaway, full=full,
             scale_bar=scale_bar, title=ttl, ghost_alpha=ghost_alpha)
    if 'clusters' in panels:
        _run(lambda out, **kw: panel_clusters(run, out, st, top=top, **kw),
             f'{tag}_p5_clusters.png', cutaway=cutaway, full=full,
             scale_bar=scale_bar, title=ttl)
    if made:
        montage(made, os.path.join(out_dir, f'{tag}_qa_montage.png'))
    return made
