"""viz3dlib.selfcheck — qa_stats palette probe and the selfcheck acceptance run."""
from __future__ import annotations

import os
import numpy as np

from .plotting import add_domain_box, add_flow_markers, new_plotter, surface
from .runio import load_run
from .style_env import STYLE, WALL_T


HUE_BANDS = (('red', -25, 25), ('orange', 25, 55), ('yellow', 55, 70),
             ('green', 70, 160), ('cyan', 160, 195), ('blue', 195, 260),
             ('purple', 260, 320), ('magenta', 320, 335))


def qa_stats(path):
    """Cheap programmatic sanity: not blank, not a flat silhouette, and the
    intended phase actually rendered in the intended hue."""
    from PIL import Image

    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    bg = np.array(a[2, 2], dtype=np.int16)
    diff = np.abs(a - bg).sum(axis=2)
    fg = float((diff > 24).mean())
    uniq = len(np.unique(a.reshape(-1, 3), axis=0))
    line = (f'     {im.size[0]}x{im.size[1]}  ink={fg:.3f}  colors={uniq}'
            f'  mean={a.reshape(-1, 3).mean(0).round(0)}')
    hsv = np.asarray(im.convert('HSV')).astype(np.float32)
    sat = (hsv[..., 1] > 60) & (hsv[..., 2] > 40)
    if sat.sum() > 500:
        hue = hsv[..., 0][sat] * 360.0 / 255.0
        bands = []
        for name, lo, hi in HUE_BANDS:
            if lo < 0:
                m = (hue >= 360 + lo) | (hue < hi)
            else:
                m = (hue >= lo) & (hue < hi)
            if m.mean() > 0.08:
                bands.append(f'{name}:{m.mean():.2f}')
        line += '  hues[' + ' '.join(bands) + f'] sat={sat.mean():.3f}'
    print(line)
    return dict(ink=fg, colors=uniq)


def selfcheck(run_path, min_dl=0.06):
    """Assertions against the silent failure modes.

    Rendering bugs here do not crash — they quietly produce a mirrored or
    transposed picture that still looks plausible, so they have to be
    asserted, not eyeballed:
      1. axis order   (nx,ny,nz) + ravel(order='F') must map axis 0 -> x
      2. wall axis    reservoir/wall slabs must sit on the x extremes
      3. flow sense   non-wetting must enter from low x
      4. grayscale    phase colours must stay separable in a B/W print
    """
    import pyvista as pv

    fails = []
    print('selfcheck:', run_path)

    # 1. axis order -------------------------------------------------------
    n = (16, 8, 6)
    idx = np.broadcast_to(np.arange(n[0], dtype=np.float32)[:, None, None], n)
    m = surface(idx.copy(), level=8.0, scalars='idx')
    xs = float(np.ptp(m.points[:, 0]))
    ok = xs < 0.5 and abs(m.points[:, 0].mean() - 8.0) < 0.5
    print(f'  1 axis order   plane at x={m.points[:,0].mean():.2f} '
          f'(expect 8.0), x-spread={xs:.3f} (expect ~0) -> '
          f'{"PASS" if ok else "FAIL"}')
    fails += [] if ok else ['axis order']

    # 2. wall axis --------------------------------------------------------
    s = np.load(os.path.join(run_path, 'final.npz'))['solid']
    faces = dict(x_lo=s[:WALL_T].mean(), x_hi=s[-WALL_T:].mean(),
                 y_lo=s[:, :WALL_T].mean(), y_hi=s[:, -WALL_T:].mean(),
                 z_lo=s[:, :, :WALL_T].mean(), z_hi=s[:, :, -WALL_T:].mean())
    ok = (faces['x_lo'] > 0.99 and faces['x_hi'] > 0.99
          and max(faces['y_lo'], faces['y_hi'], faces['z_lo'],
                  faces['z_hi']) < 0.99)
    print('  2 wall axis    solid frac per face '
          + ' '.join(f'{k}={v:.2f}' for k, v in faces.items())
          + f' -> {"PASS" if ok else "FAIL"}')
    fails += [] if ok else ['wall axis']

    # 3. flow sense -------------------------------------------------------
    # The reservoir slabs are pinned by construction (+1 at the inlet, -1 at
    # the outlet), so they are an unambiguous orientation marker.  The phase
    # centroids in the domain are reported for information only: after
    # breakthrough both phases span the box and the residual-wetting
    # centroid can sit on either side of it, so they make a bad assertion.
    run = load_run(run_path)
    full_psi, full_solid = run['psi'], run['solid']
    rt = run['res_thick']
    nx = full_psi.shape[0]
    open_ = full_solid == 0
    in_sl = (slice(WALL_T, WALL_T + rt),)             # inlet reservoir slab
    out_sl = (slice(nx - WALL_T - rt + 1, nx - WALL_T),)
    pin = full_psi[in_sl][open_[in_sl]]
    pout = full_psi[out_sl][open_[out_sl]]
    ok = bool(pin.size and pout.size and pin.mean() > 0.95
              and pout.mean() < -0.95)
    print(f'  3 flow sense   reservoir psi (pore voxels only)  inlet='
          f'{pin.mean():+.3f}  outlet={pout.mean():+.3f}  (inlet holds +1 = '
          f'non-wetting source) -> {"PASS" if ok else "FAIL"}')
    fails += [] if ok else ['flow sense']
    solid = run['solid'][run['dom']]
    pore = solid == 0
    psi = full_psi[run['dom']]
    xi = np.arange(psi.shape[0], dtype=np.float64)

    def mean_x(mask):
        prof = mask.sum(axis=(1, 2)).astype(np.float64)
        return np.nan if prof.sum() == 0 else float((prof * xi).sum()
                                                    / prof.sum())

    print(f'     info: domain centroid x  non-wetting={mean_x((psi > 0) & pore):.1f}'
          f'  wetting={mean_x((psi < 0) & pore):.1f}  (centre '
          f'{psi.shape[0] / 2:.1f})')

    # 4. grayscale separation --------------------------------------------
    # Translucent elements must be composited over the ground first — the
    # ghost is nearly white once you account for its alpha, so checking the
    # raw swatch would report a false conflict.  Only pairs that actually
    # share a panel are tested, plus wet/non-wetting: those never appear in
    # the same frame, but the reader flips between the two panels, so they
    # still have to be separable in a B/W print.
    from PIL import Image

    def _lum(c):
        return np.asarray(Image.new('RGB', (1, 1), c).convert('L')).item() / 255

    pairs_to_test = [('bg', 'solid'), ('bg', 'nw'), ('bg', 'wet'),
                     ('ghost', 'nw'), ('ghost', 'wet'),
                     ('ghost', 'overflow'), ('wet', 'nw')]
    for sname, st in STYLE.items():
        def _rgb(c):
            return np.array(Image.new('RGB', (1, 1), c).getpixel((0, 0)),
                            dtype=float)

        bg = _rgb(st['bg'])
        eff = {k: _lum(st[k]) for k in ('bg', 'solid', 'wet', 'nw')}
        for key in ('ghost', 'overflow'):
            col, alpha = st[key]
            eff[key] = _lum(tuple(int(round(v)) for v in
                                  (alpha * _rgb(col)
                                   + (1 - alpha) * bg)))
        got = [(a, b, abs(eff[a] - eff[b])) for a, b in pairs_to_test]
        worst = min(got, key=lambda t: t[2])
        ok = worst[2] >= min_dl
        print(f'  4 grayscale    [{sname}] L=' +
              ' '.join(f'{k}:{v:.2f}' for k, v in eff.items()) +
              f'  worst {worst[0]}..{worst[1]} dL={worst[2]:.2f}'
              f' (min {min_dl}) -> {"PASS" if ok else "FAIL"}')
        if not ok:
            fails.append(f'grayscale[{sname}]')

    # 5. flow markers -----------------------------------------------------
    pl = new_plotter(STYLE['report'])
    add_domain_box(pl, (0.0, 20.0, 0.0, 10.0, 0.0, 10.0), STYLE['report'])
    tips = add_flow_markers(pl, STYLE['report'])
    pl.close()
    ok = (tips['inlet'][0] < tips['inlet'][1] < 10.0
          < tips['outlet'][0] < tips['outlet'][1])
    print(f'  5 flow markers inlet tail/tip x={tips["inlet"][0]:.1f}/'
          f'{tips["inlet"][1]:.1f}  outlet tail/tip x={tips["outlet"][0]:.1f}/'
          f'{tips["outlet"][1]:.1f}  (box 0..20, flow +x, both arrows point '
          f'+x) -> {"PASS" if ok else "FAIL"}')
    fails += [] if ok else ['flow markers']

    print('selfcheck:', 'ALL PASS' if not fails else f'FAILED {fails}')
    return fails
