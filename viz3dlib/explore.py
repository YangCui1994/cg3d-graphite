"""viz3dlib.explore — Interactive offscreen/onscreen exploration scene."""
from __future__ import annotations

import os
import numpy as np

from .anim import _load_frame, _series_files
from .plotting import _bounds, _crop3, add_domain_box, new_plotter, set_iso_camera, surface
from .runio import load_run
from .style_env import _style, _warn


# ----------------------------------------------------------- interactive
GHOST_STEPS = (0.0, 0.06, 0.12, 0.20, 0.35, 1.0)


CUT_STEPS = (1.0, 0.85, 0.75, 0.65, 0.5, 0.35)


AXIS_STEPS = (('z', 'lo'), ('y', 'hi'), ('x', 'lo'))


def explore(series=None, run_path=None, style_name='slide', cutaway=0.65,
            cut_axis='z', cut_keep='lo', view='top', opaque='both',
            ghost_alpha=0.12, level_gap=0.1, window=(1280, 1000),
            decimate=None, max_frames=None, play_ms=450, spacing=(1, 1, 1),
            scale_bar=None, selftest=False, selftest_png=None):
    """Interactive on-screen viewer for a frame series (or one final state).

    The only part of this module that does not run offscreen, so it needs a
    desktop session.  VTK supplies mouse navigation for free:

        left-drag   orbit        wheel     zoom       middle-drag  pan

    Added on top:
        slider      scrub frames
        space       play / pause (playback costs one contour per frame, so
                    the first pass is slow and later loops are instant)
        n / p       next / previous frame
        g           cycle solid-ghost opacity (see GHOST_STEPS)
        c           cycle cut fraction (see CUT_STEPS)
        x           cycle cut axis/keep (see AXIS_STEPS)
        o           cycle opaque phase: both -> nw -> wet
        b           toggle the domain box
        r           reset the camera to the preset
        q           close

    Frames are loaded and contoured lazily and cached, so scrubbing is
    instant once a frame has been visited.
    """
    import pyvista as pv

    st = _style(style_name)
    if series:
        fs = _series_files(series)
    elif run_path:
        r = load_run(run_path)
        fs = [r['npz']]
    else:
        raise SystemExit('explore needs --series or --run')
    if max_frames:
        fs = fs[:max_frames]
    psi0, solid, meta0, src = _load_frame(fs[0])
    if solid is None:
        cand = os.path.join(os.path.dirname(fs[0]), 'f_solid.npz')
        if not os.path.exists(cand):
            raise SystemExit('no solid in the frames and no --solid given')
        solid = np.load(cand)['solid'].astype(np.int8)
    tag = os.path.basename(os.path.dirname(fs[0])) or 'run'
    print(f'explore: {len(fs)} frames, field from {src!r}, solid '
          f'{solid.shape}')
    print('  mouse: drag=orbit wheel=zoom middle=pan | keys: space n p g c x '
          'o b r q')

    state = dict(k=0, playing=False, ghost=float(ghost_alpha),
                 cut=float(cutaway), axis=cut_axis, keep=cut_keep,
                 opaque=opaque)
    scache, fcache = {}, {}

    def crop(psi):
        return _crop3(psi, state['axis'], state['cut'], state['keep'])

    def solid_mesh():
        key = (state['axis'], state['cut'], state['keep'])
        if key not in scache:
            sc, origin = crop(solid)
            scache[key] = (surface(sc.astype(np.float32), 0.5,
                                   spacing=spacing, origin=origin,
                                   decimate=0.5 if decimate is None
                                   else decimate, quiet=True,
                                   allow_empty=True), origin)
        return scache[key]

    def fluid_meshes(k):
        key = (k, state['axis'], state['cut'], state['keep'],
               state['opaque'], abs(level_gap))
        if key in fcache:
            return fcache[key]
        psi, _, _m, _s = _load_frame(fs[k])
        pc, origin = crop(psi)
        sc, _ = crop(solid)
        pore = sc == 0
        frac_nw = float(((pc > 0.0) & pore).sum()) / max(pore.sum(), 1)
        g = abs(level_gap)
        op = state['opaque']
        if op == 'both':
            spec = [('nw', g, -1.0, st['nw'], 1.0),
                    ('wet', -g, 1.0, st['wet'], 1.0)]
        else:
            nw_op = (frac_nw < 0.5) if op == 'auto' else (op == 'nw')
            spec = [('nw', g, -1.0, st['nw'],
                     1.0 if nw_op else st['glass']),
                    ('wet', -g, 1.0, st['wet'],
                     1.0 if not nw_op else st['glass'])]
        out = []
        for tg, lvl, mask, col, alpha in spec:
            m = surface(pc, lvl, pore=pore, mask_value=mask,
                        spacing=spacing, origin=origin, decimate=decimate,
                        quiet=True, allow_empty=True)
            if m is not None:
                out.append((tg, m, col, alpha))
        fcache[key] = (out, origin, frac_nw)
        return fcache[key]

    bounds = _bounds((0, 0, 0), psi0.shape, spacing)
    # the selftest drives the same scene but offscreen, so a shell can run
    # it; the real window is exercised by the probe at the end of selftest
    pl = new_plotter(st, window=window, off_screen=bool(selftest))
    box_actor = [None]
    solid_actor = [None]
    hud_actor = [None]
    fluid = []

    def add_box():
        if box_actor[0] is not None:
            pl.remove_actor(box_actor[0], render=False)
        if state.get('box', True):
            box_actor[0] = add_domain_box(pl, bounds, st)

    def hud():
        psi, _, meta, _ = _load_frame(fs[state['k']])
        parts = [f'{tag}   frame {state["k"] + 1}/{len(fs)}']
        if 'it' in meta:
            parts.append(f'step {int(meta["it"])}')
        if 's_nw' in meta:
            parts.append(f'S_nw={meta["s_nw"]:.3f}')
        parts.append(f'ghost={state["ghost"]:.2f}  cut={state["cut"]:.2f} '
                     f'({state["axis"]},{state["keep"]})  opaque='
                     f'{state["opaque"]}')
        txt = '   '.join(parts)
        if hud_actor[0] is not None:
            pl.remove_actor(hud_actor[0], render=False)
        hud_actor[0] = pl.add_text(txt, position='upper_left', font_size=10,
                                   color=st['text'])

    def show(k=None, render=True):
        nonlocal fluid
        if k is not None:
            state['k'] = int(k) % len(fs)
        for a in fluid:
            pl.remove_actor(a, render=False)
        fluid = []
        meshes, _origin, _f = fluid_meshes(state['k'])
        gcol, _ga = st['ghost']
        for tg, m, col, alpha in meshes:
            fluid.append(pl.add_mesh(m, color=col, opacity=alpha,
                                     smooth_shading=True,
                                     specular=st['specular'],
                                     specular_power=st['specular_power'],
                                     lighting=True, name=f'{tg}'))
        _set_ghost()
        hud()
        if render:
            pl.render()

    def _set_ghost():
        sm, _o = solid_mesh()
        if solid_actor[0] is not None:
            pl.remove_actor(solid_actor[0], render=False)
        if sm is not None and state['ghost'] > 0:
            gcol, _ga = st['ghost']
            solid_actor[0] = pl.add_mesh(sm, color=gcol,
                                         opacity=state['ghost'],
                                         smooth_shading=False, lighting=True)
        else:
            solid_actor[0] = None

    def rebuild(k=None, render=True):
        scache.clear()
        solid_mesh()
        show(k, render=render)

    def on_slide(v):
        show(int(round(float(v))))

    def tick(*_a):
        if state['playing']:
            show(state['k'] + 1)

    # --- initial scene: box first so the camera fits a fixed frame
    add_box()
    set_iso_camera(pl, view=view)
    rebuild(render=False)
    pl.add_slider_widget(on_slide, rng=[0, len(fs) - 1], value=0,
                         title='frame', pointa=(0.25, 0.05),
                         pointb=(0.90, 0.05), interaction_event='end',
                         fmt='%.0f')
    pl.add_key_event('space', lambda: state.update(
        playing=not state['playing']))
    pl.add_key_event('n', lambda: show(state['k'] + 1))
    pl.add_key_event('p', lambda: show(state['k'] - 1))

    def cycle_ghost():
        i = GHOST_STEPS.index(state['ghost']) if state['ghost'] in \
            GHOST_STEPS else 0
        state['ghost'] = GHOST_STEPS[(i + 1) % len(GHOST_STEPS)]
        _set_ghost()
        hud()
        pl.render()

    def cycle_cut():
        i = CUT_STEPS.index(state['cut']) if state['cut'] in CUT_STEPS else 0
        state['cut'] = CUT_STEPS[(i + 1) % len(CUT_STEPS)]
        rebuild()

    def cycle_axis():
        i = (AXIS_STEPS.index((state['axis'], state['keep']))
             if (state['axis'], state['keep']) in AXIS_STEPS else 0)
        state['axis'], state['keep'] = AXIS_STEPS[(i + 1) % len(AXIS_STEPS)]
        rebuild()

    def cycle_opaque():
        order = ['both', 'nw', 'wet']
        state['opaque'] = order[(order.index(state['opaque']) + 1)
                                % len(order)] if state['opaque'] in order \
            else 'both'
        fcache.clear()
        show()

    def toggle_box():
        state['box'] = not state.get('box', True)
        add_box()
        pl.render()

    pl.add_key_event('g', cycle_ghost)
    pl.add_key_event('c', cycle_cut)
    pl.add_key_event('x', cycle_axis)
    pl.add_key_event('o', cycle_opaque)
    pl.add_key_event('b', toggle_box)
    pl.add_key_event('r', lambda: set_iso_camera(pl, view=view))
    pl.add_key_event('q', lambda: pl.close())

    if selftest:
        # stage 1: every key handler, offscreen (no window, no blocking loop)
        for fn in (cycle_ghost, cycle_cut, cycle_axis, cycle_opaque,
                   toggle_box, lambda: show(1), lambda: show(0)):
            fn()
        pl.render()
        out = selftest_png or f'_explore_selftest_{tag}.png'
        pl.screenshot(out)
        meta = fcache[(0, state['axis'], state['cut'], state['keep'],
                       state['opaque'], abs(level_gap))]
        print(f'  selftest logic OK: {len(fs)} frames, {len(fluid)} fluid '
              f'actors, frac_nw={meta[2]:.3f} -> {out}')
        pl.close()
        # stage 2: prove a real window can be created on this machine.
        # show(interactive=False) renders one frame and returns instead of
        # entering the interactor loop, so nothing hangs and no window is
        # left behind.
        probe = f'_explore_probe_{tag}.png'
        try:
            pl2 = new_plotter(st, window=(640, 560), off_screen=False)
            add_domain_box(pl2, bounds, st)
            m2, _o, _f = fluid_meshes(0)
            for _tg, m, col, alpha in m2:
                pl2.add_mesh(m, color=col, opacity=alpha, smooth_shading=True,
                             lighting=True)
            set_iso_camera(pl2, view=view)
            pl2.show(interactive=False, screenshot=probe, auto_close=True)
            print(f'  selftest on-screen OK: real VTK window rendered -> '
                  f'{probe}')
        except Exception as exc:                              # noqa: BLE001
            print(f'  ! on-screen probe FAILED: {type(exc).__name__}: {exc}')
            print('    (the interactive viewer needs a desktop session)')
        return out

    try:
        pl.iren.add_timer_event(max_steps=10 ** 9, duration=int(play_ms),
                                callback=tick)
    except Exception as exc:                                  # noqa: BLE001
        _warn('playback timer (space still toggles, frames step with n/p)',
              exc)
    try:
        pl.show()
    except Exception as exc:                                  # noqa: BLE001
        pl.close()
        raise SystemExit(
            f'could not open an interactive window ({type(exc).__name__}: '
            f'{exc}).  This needs a desktop session; use figset / animate for '
            f'headless output instead.')
    return None
