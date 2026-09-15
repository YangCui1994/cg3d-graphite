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
import json
import os
import sys

import numpy as np

# x[0:WALL_T) and x[nx-WALL_T:) are solid walls in the run_pcs_cg3d layout:
#   wall | inlet reservoir | mem_b | pore domain | mem_r | outlet reservoir | wall
WALL_T = 3

STYLE = {
    'report': dict(
        bg='white',
        solid='#b0b0b0',            # opaque, geometry panel
        ghost=('#8a8a8f', 0.16),    # translucent context
        wet='#2166ac',
        # amber, NOT the 2D series' dark red: blue-vs-darkred is only
        # dL=0.067 in grayscale (blue-vs-#d62728 is 0.008), i.e. liquid and
        # gas become the same grey in a B/W print.  Amber keeps the warm
        # family and gives dL=0.224; see VIZ_3D_STYLE.md.
        nw='#e08214',
        overflow=('#7f7f7f', 0.9),   # darker than the ghost so it still reads
        text='#1a1a1a',
        box='#8a8a8f',
        # Matte: a broad specular highlight washes the shading gradient out
        # and the gradient is what carries the 3D form.  Keep it tight and
        # weak.
        specular=0.08, specular_power=30,
        # alpha for the majority fluid in the two-phase panel ("glass")
        glass=0.30,
        psi_cmap=['#2166ac', '#f2f2f2', '#e08214'],
        # Chromatic only (no grays — those are reserved for solid/ghost) and
        # greens/magentas first: the phase colours (blue wet, amber non-wet)
        # are reserved, so a 4-cluster figure must not lead with a blue or
        # amber blob that reads as "liquid"/"gas".
        clusters=['#009E73', '#CC79A7', '#8C564B', '#8172B2', '#B79F00',
                  '#55A868', '#4C72B0', '#D55E00', '#56B4E9', '#E69F00',
                  '#0072B2', '#DD8452'],
    ),
    'slide': dict(
        bg='#1b1b1b',
        solid='#8a8a8f',
        ghost=('#8a8a8f', 0.20),    # dark grounds swallow low alpha
        wet='#2f7fd0',
        nw='#f5f5f5',               # white gas — only readable on a dark ground
        overflow=('#9a9a9a', 0.9),
        text='#f0f0f0',
        box='#6e6e73',
        specular=0.08, specular_power=30,
        glass=0.30,
        psi_cmap=['#2f7fd0', '#2b2b2b', '#f5f5f5'],        clusters=['#009E73', '#CC79A7', '#E69F00', '#A0E7A0', '#E8A0C8',
                  '#F0E442', '#D55E00', '#8CD0E3', '#F5C6A5', '#FFD86B',
                  '#56B4E9', '#9FD8F5'],
    ),
}

# Camera presets.  'iso' keeps the matplotlib elev/azim used by
# vis3d_report.py (up = z, so the z axis fills the frame height).  'front'
# puts up = y so the frame is landscape: the thin axis is vertical, the
# inlet-to-outlet x axis runs left-to-right, and the line of sight is mostly
# along z -- pair it with cut_axis='z', since you must cut along the view
# direction to expose the interior.
CAM_ELEV, CAM_AZIM = 18.0, -55.0
VIEWS = {
    'iso': dict(elev=CAM_ELEV, azim=CAM_AZIM, up=(0, 0, 1)),
    'front': dict(dirv=(0.25, 0.20, 0.95), up=(0, 1, 0)),
    # looking down onto a horizontal cut plane (pair with cut_axis='z',
    # cut_keep='lo' so the exposed face points up at the camera)
    'top': dict(elev=58.0, azim=-55.0, up=(0, 0, 1)),
}
WINDOW = (1800, 1500)
DPI_SCALE = 2          # screenshot(scale=2) -> ~300 dpi at 6 in print width

# inset (in psi units) applied to both fluid surfaces in the two-phase panel.
# 0 = the two bodies share the psi=0 boundary exactly (VTK resolves the
# coincident topology); raise it if that shared interface ever speckles.
LEVEL_GAP = 0.0


def check_env():
    """Fail with the fix, not a bare ModuleNotFoundError.

    On this machine a bare `python` is the *base* conda env, while pyvista
    lives in the `lbm` env, so the first symptom is an unhelpful
    "No module named 'pyvista'" from deep inside a render call.
    """
    try:
        __import__('numpy')
        __import__('pyvista')
    except ImportError as exc:
        raise SystemExit(
            f'viz3d: cannot import {exc.name} with interpreter\n'
            f'  {sys.executable}\n'
            'viz3d needs pyvista/vtk, which are installed in the conda env '
            '`lbm`, not in the base env a bare `python` resolves to.  Use '
            'either:\n'
            '  conda activate lbm   &&  python viz3d.py <args>\n'
            '  viz3d.cmd <args>                       (launcher, this dir)\n'
            '  "C:/Users/yangc/anaconda3/envs/lbm/python.exe" viz3d.py <args>'
        ) from None
    for mod, why in (('scipy', 'clusters/explore'),
                     ('matplotlib', 'slices'),
                     ('PIL', 'qa_stats/gif')):
        try:
            __import__(mod)
        except ImportError:
            print(f'  note: {mod} is missing — {why} will not work '
                  f'(pip install {mod})', file=sys.stderr)


def _style(name):
    if name not in STYLE:
        raise SystemExit(f'unknown style {name!r}; pick from {list(STYLE)}')
    return STYLE[name]


# ----------------------------------------------------------------- run I/O
def load_run(path):
    """Load a run directory (or a .npz) into a dict of fields + metadata.

    Returns dict with psi, solid, geo_meta, res_thick, dom (x slice of the
    pore domain, reservoir/membrane slabs excluded), R_lu, tag.
    """
    d = path if os.path.isdir(path) else os.path.dirname(path)
    npz = os.path.join(path, 'final.npz') if os.path.isdir(path) else path
    if not os.path.exists(npz):
        raise SystemExit(f'no final.npz under {path}')
    z = np.load(npz)
    out = {k: z[k] for k in z.files}
    if 'psi' not in out or 'solid' not in out:
        raise SystemExit(f'{npz} needs psi and solid (got {list(out)})')

    meta, res_thick, r_lu = {}, 8, None
    rj = os.path.join(d, 'report.json')
    if os.path.exists(rj):
        with open(rj, encoding='utf-8') as f:
            rep = json.load(f)
        meta = rep
        res_thick = int(rep.get('args', {}).get('res_thick', 8))
        g = rep.get('geo')
        if isinstance(g, str):
            try:
                g = json.loads(g.replace("'", '"'))
            except Exception:                                    # noqa: BLE001
                g = None
        if isinstance(g, dict):
            r_lu = g.get('R_lu')

    nx = out['psi'].shape[0]
    x_in = WALL_T + res_thick + 1              # first pore-domain plane
    x_out = nx - WALL_T - res_thick            # last pore-domain plane + 1
    out.update(tag=os.path.basename(d.rstrip('/\\')), npz=npz,
               meta=meta, res_thick=res_thick, R_lu=r_lu,
               dom=slice(x_in, x_out))
    return out


def pore_domain(run, full=False):
    """(psi, solid) restricted to the pore domain unless full=True."""
    if full:
        return run['psi'], run['solid']
    return run['psi'][run['dom']], run['solid'][run['dom']]


# ------------------------------------------------------------- primitives
def to_image(arrs, spacing=(1, 1, 1), origin=(0, 0, 0)):
    """numpy (nx,ny,nz) fields -> pv.ImageData (x-fastest, see module doc)."""
    import pyvista as pv

    shape = next(iter(arrs.values())).shape
    img = pv.ImageData(dimensions=shape, spacing=spacing, origin=origin)
    for k, a in arrs.items():
        img.point_data[k] = np.ascontiguousarray(
            np.asarray(a, dtype=np.float32).ravel(order='F'))
    return img


def surface(field, level=0.0, pore=None, mask_value=-1.0, spacing=(1, 1, 1),
            origin=(0, 0, 0), scalars='f', decimate=None, quiet=False,
            allow_empty=False):
    """Marching-cubes isosurface of `field` at `level`.

    ``pore`` (bool, 1 = open) masks the solid out by setting those voxels to
    ``mask_value``; pass -1 to have the surface stop at grain walls
    (non-wetting phase) and +1 to have it follow them (wetting phase).  The
    masked-continuum trick keeps the surface sub-voxel smooth and exactly at
    the grain boundary, instead of the blocky look of contouring a binary
    indicator.
    """
    f = np.asarray(field, dtype=np.float32)
    if pore is not None:
        f = np.where(pore, f, np.float32(mask_value))
    img = to_image({scalars: f}, spacing=spacing, origin=origin)
    mesh = img.contour([level], scalars=scalars)
    if decimate:
        try:
            mesh = mesh.decimate(decimate)
        except Exception:                                        # noqa: BLE001
            pass
    if mesh.n_points == 0:
        msg = f'isosurface at {level:+.3f} is empty — check level/field'
        if not allow_empty:
            raise SystemExit(msg)
        if not quiet:
            print(f'     ! {msg}')
        return None
    mesh.compute_normals(inplace=True, auto_orient_normals=True)
    if not quiet:
        print(f'     surface {scalars}={level:+.3f}  pts={mesh.n_points} '
              f'tris={mesh.n_cells}')
    return mesh


# ------------------------------------------------------------- plot setup
def new_plotter(style, window=WINDOW, off_screen=True):
    import pyvista as pv

    pv.OFF_SCREEN = off_screen
    pl = pv.Plotter(off_screen=off_screen, window_size=window)
    pl.background_color = style['bg']
    pl.enable_depth_peeling(number_of_peels=8)   # correct translucent order
    try:
        pl.enable_ssao(radius=0.55, bias=0.01)   # depth cue; flat looks
    except Exception as exc:                                  # noqa: BLE001
        _warn('ssao', exc)
    try:
        pl.enable_anti_aliasing('ssaa')
    except Exception as exc:                                  # noqa: BLE001
        _warn('anti-aliasing', exc)
    return pl


def _crop3(a, axis, cutaway, keep='lo'):
    """Cut `a` along `axis`, returning (cropped, origin_indices).

    ``keep='lo'`` keeps index range [0, c) and ``'hi'`` keeps [n-c, n).
    Static panels cut on x (dropping the downstream half); an animation
    following an advancing front must cut on y instead, so the whole
    inlet-to-outlet extent stays on screen -- an x-cut would hide the second
    half of the invasion inside the discarded material.
    """
    if cutaway >= 1.0:
        return a, (0, 0, 0)
    if isinstance(axis, str):
        axis = 'xyz'.index(axis)
    n = a.shape[axis]
    c = max(int(n * cutaway), 2)
    sl = [slice(None)] * 3
    sl[axis] = slice(n - c, n) if keep == 'hi' else slice(0, c)
    origin = [0, 0, 0]
    origin[axis] = n - c if keep == 'hi' else 0
    return a[tuple(sl)], tuple(origin)


def _bounds(origin, shape, spacing=(1, 1, 1)):
    """Bounding box of a cropped block, in world coordinates."""
    lo = [origin[i] * spacing[i] for i in range(3)]
    hi = [(origin[i] + shape[i] - 1) * spacing[i] for i in range(3)]
    return (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])


def add_fluid(pl, mesh, color, style, opacity=1.0, name=None):
    """One fluid body, opaque by default.

    The wetting and non-wetting fluids tile disjoint parts of the pore space
    (they meet only at the psi=0 interface), so they need no transparency to
    be shown together — the only translucent object in a cutaway is the
    solid ghost.
    """
    pl.add_mesh(mesh, color=color, opacity=opacity, smooth_shading=True,
                specular=style['specular'],
                specular_power=style['specular_power'], lighting=True,
                name=name)
    return mesh


def add_domain_box(pl, bounds, style, label=None):
    """Wireframe of the shown sub-domain + optional tag.  The box is what
    reset_camera() fits, which is what makes the camera run-independent."""
    import pyvista as pv

    box = pv.Box(bounds=bounds)
    # return the ACTOR (not the mesh): the interactive viewer removes and
    # re-adds the box, and remove_actor needs a vtkProp
    actor = pl.add_mesh(box, style='wireframe', color=style['box'],
                        line_width=1.5, lighting=False)
    if label:
        try:
            pl.add_text(label, position='upper_left', font_size=11,
                        color=style['text'])
        except Exception as exc:                              # noqa: BLE001
            _warn('add_text', exc)
    return actor


def set_iso_camera(pl, zoom=0.92, view='iso'):
    """Orthographic view from the named preset (see VIEWS)."""
    if view not in VIEWS:
        raise SystemExit(f'unknown view {view!r}; have {list(VIEWS)}')
    spec = VIEWS[view]
    pl.enable_parallel_projection()
    pl.camera.up = spec['up']
    c = np.array(pl.center, dtype=float)
    if 'dirv' in spec:
        d = np.asarray(spec['dirv'], dtype=float)
        d = d / np.linalg.norm(d)
    else:
        el, az = np.radians(spec['elev']), np.radians(spec['azim'])
        d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az),
                      np.sin(el)])
    diag = float(np.linalg.norm(np.ptp(np.asarray(pl.bounds).reshape(3, 2),
                                       axis=1)))
    pl.camera_position = [c + d * diag * 1.8, c, spec['up']]
    pl.reset_camera()
    if zoom != 1.0:
        # VTK's camera.zoom magnifies above 1, so the old default of 1.12
        # was silently cropping the geometry at the frame edges (the ink
        # mask touched all four borders).  Below 1 adds the margin instead.
        pl.camera.zoom(zoom)


def add_scale_bar(pl, length, style, unit='lu', anchor='lower left'):
    """Data, not decoration: a bar of known length in lattice units."""
    import pyvista as pv

    x0, x1, y0, y1, z0, z1 = pl.bounds
    p0 = np.array([x0 + 0.06 * (x1 - x0), y0 + 0.06 * (y1 - y0), z0])
    p1 = p0 + np.array([0, length, 0])
    pl.add_mesh(pv.Line(p0, p1), color=style['text'], line_width=4,
                lighting=False)
    try:
        pl.add_point_labels([(p0 + p1) / 2 + np.array([0, 0, 0])],
                            [f'{length:g} {unit}'], font_size=11,
                            text_color=style['text'], shape=None,
                            shape_opacity=0.0, always_visible=True,
                            show_points=False)
    except Exception as exc:                                  # noqa: BLE001
        _warn('scale-bar label', exc)


FLOW = True          # inlet/outlet markers on 3D panels (CLI: --no-flow)


def add_flow_markers(pl, style):
    """Inlet/outlet arrows under the -x/+x ends of the box: flow direction
    is data.

    Drainage layout: red (non-wetting) enters at low x, blue exits at high
    x.  The arrows sit OUTSIDE the box, below it and in front of it (4.5%
    of the box extent each way), derived from the ACTIVE camera so the
    recipe holds for every view: `below` = the screen-vertical axis
    (argmax |up|: z for iso, y for front), `front` = the depth axis,
    offset toward the camera.  Inside the volume they are depth-occluded
    by the opaque fluid meshes (verified on p3b_finney); at mid-y under
    the box the outlet arrow clips past the right frame edge on
    full-frame scenes (verified on gx3 graphite).  Labels stay English —
    vtk's offscreen font has no CJK glyphs.  Unlit, text-coloured: same
    conventions as the scale bar.
    Returns {name: (tail_x, tip_x)} so selfcheck can assert placement."""
    import pyvista as pv

    x0, x1, y0, y1, z0, z1 = pl.bounds
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    ext = np.array([dx, dy, dz], dtype=float)
    up = np.asarray(pl.camera.up, dtype=float)
    below = int(np.argmax(np.abs(up)))
    dvec = np.asarray(pl.camera.direction, dtype=float)
    front = max((a for a in range(3) if a != below),
                key=lambda a: abs(dvec[a]))
    fsign = -np.sign(dvec[front]) if dvec[front] != 0 else 1.0
    anchor = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    anchor[below] -= 0.045 * ext[below]
    anchor[front] += fsign * 0.045 * ext[front]
    L = 0.08 * dx
    tails = {'inlet': np.array([x0 + 0.015 * dx, anchor[1], anchor[2]]),
             'outlet': np.array([x1 - 0.015 * dx - L, anchor[1], anchor[2]])}
    lift = np.zeros(3)
    lift[below] = 0.05 * ext[below]
    for name, tail in tails.items():
        pl.add_mesh(pv.Arrow(start=tuple(tail), direction=(1.0, 0.0, 0.0),
                             scale=L), color=style['text'], lighting=False)
        # label anchor: mid-arrow on the left (inlet has margin), tail-end on
        # the right so the centred text cannot clip past the frame edge
        lx = 0.5 * L if name == 'inlet' else 0.0
        try:
            pl.add_point_labels(
                [tail + lift + np.array([lx, 0.0, 0.0])],
                [name], font_size=15, text_color=style['text'], shape=None,
                shape_opacity=0.0, always_visible=True, show_points=False)
        except Exception as exc:                              # noqa: BLE001
            _warn(f'flow-marker label {name}', exc)
    return {k: (v[0], v[0] + L) for k, v in tails.items()}


def save(pl, out_png, style, title=None, transparent=False):
    pl.screenshot(out_png, transparent_background=transparent or None)
    pl.close()
    print(f'  -> {out_png}')
    return out_png


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


def montage(pngs, out_png, cols=3):
    from PIL import Image

    ims = [Image.open(p).convert('RGB') for p in pngs if os.path.exists(p)]
    if not ims:
        return None
    w = max(i.width for i in ims)
    h = max(i.height for i in ims)
    rows = int(np.ceil(len(ims) / cols))
    sheet = Image.new('RGB', (w * cols, h * rows), 'white')
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    sheet.thumbnail((2400, 2400))
    sheet.save(out_png)
    print(f'  -> {out_png} (QA sheet)')
    return out_png


# ---------------------------------------------------------------- panels
def panel_geometry(run, out_png, style, cutaway=1.0, full=False,
                   smooth_solid=False, spacing=(1, 1, 1), show_box=True,
                   scale_bar=None, title=None, decimate=None):
    """P0: the sphere pack itself, opaque.  cutaway<1 opens the box."""
    psi, solid = pore_domain(run, full=full)
    if cutaway < 1.0:
        solid = solid[:max(int(solid.shape[0] * cutaway), 2)]
    if smooth_solid:
        solid = _smooth_binary(solid.astype(np.float32))
    mesh = surface(solid.astype(np.float32), 0.5, spacing=spacing,
                   decimate=decimate)
    pl = new_plotter(style)
    pl.add_mesh(mesh, color=style['solid'], smooth_shading=True,
                specular=style['specular'],
                specular_power=style['specular_power'], lighting=True)
    if show_box:
        add_domain_box(pl, _domain_bounds(run, solid, full, spacing), style,
                       label=title)
    set_iso_camera(pl)
    if scale_bar:
        add_scale_bar(pl, scale_bar, style)
    if FLOW:
        add_flow_markers(pl, style)
    return save(pl, out_png, style)


def panel_cutaway(run, out_png, style, focus='both', level=None,
                  cutaway=0.5, ghost_solid=True, full=False,
                  spacing=(1, 1, 1), smooth_solid=False, scale_bar=None,
                  title=None, decimate=None, level_gap=0.0, ghost_alpha=None,
                  cut_axis='x', cut_keep='lo', solid_mesh=None,
                  psi_override=None, opaque=None, quiet=False,
                  window=WINDOW, view='iso'):
    """The pore-scale fluids in a cutaway box, solid as a ghost.

    ``focus='both'`` (default) shows the wetting and non-wetting phases in
    the same frame — they occupy disjoint pore volume, so a single-phase
    panel silently renders the other fluid as empty white background, which
    reads as "nothing there".  ``'nw'`` / ``'wet'`` isolate one phase when
    that is what the panel is arguing.

    ``solid_mesh`` / ``psi_override`` / ``glass`` exist for the animation
    loop: the rock never changes, so its mesh is built once and passed in,
    and the glass/opaque assignment must stay frozen across frames or the
    colours flip halfway through the clip.
    """
    psi, solid = (pore_domain(run, full=full) if psi_override is None
                  else (psi_override, run['solid'][run['dom']]))
    psi, origin = _crop3(psi, cut_axis, cutaway, cut_keep)
    solid, _ = _crop3(solid, cut_axis, cutaway, cut_keep)
    bounds = _bounds(origin, psi.shape, spacing)
    pore = solid == 0

    def _both_levels():
        if focus == 'nw':
            return [('nw', 0.0 if level is None else level, -1.0,
                     style['nw'], 1.0)]
        if focus in ('wet', 'wetting'):
            return [('wet', 0.0 if level is None else -abs(level), 1.0,
                     style['wet'], 1.0)]
        if focus in ('both', 'two'):
            g = abs(level_gap)
            # The majority phase goes glass and the minority stays opaque:
            # a pore-filling wetting phase hides every trapped non-wetting
            # blob inside it if both are solid, and vice versa in drainage.
            frac_nw = float(((psi > 0.0) & pore).sum()) / max(pore.sum(), 1)
            # `opaque` names the phase that stays OPAQUE.  In a film of an
            # invasion it must be pinned to the invading phase, not chosen
            # per frame: the invader starts at ~1% of the pore, so a
            # data-driven choice would render the advancing front as glass
            # exactly when it is the thing to watch.
            if opaque == 'both':
                # ket_drain.gif recipe: dark ground + both fluids opaque.
                # The two fluids tile disjoint voxels, so nothing is hidden
                # as long as they are not both *translucent*; the solid
                # ghost is the only see-through object.
                if not quiet:
                    print(f'     two-phase: nw occupies {frac_nw:.3f} of '
                          f'pore -> both fluids opaque')
                return [('nw', g, -1.0, style['nw'], 1.0),
                        ('wet', -g, 1.0, style['wet'], 1.0)]
            nw_opaque = (frac_nw < 0.5 if opaque in (None, 'auto')
                         else opaque == 'nw')
            if not quiet:
                print(f'     two-phase: nw occupies {frac_nw:.3f} of pore -> '
                      f'opaque={"nw" if nw_opaque else "wet"}'
                      f'{" (pinned)" if opaque not in (None, "auto") else ""}')
            return [('nw', g, -1.0, style['nw'],
                     1.0 if nw_opaque else style['glass']),
                    ('wet', -g, 1.0, style['wet'],
                     1.0 if not nw_opaque else style['glass'])]
        raise SystemExit(f"focus must be 'both', 'nw' or 'wet', "
                         f"got {focus!r}")

    meshes = [(tag, surface(psi, lvl, pore=pore, mask_value=mask,
                            spacing=spacing, origin=origin,
                            decimate=decimate), col, alpha)
              for tag, lvl, mask, col, alpha in _both_levels()]

    pl = new_plotter(style, window=window)
    if ghost_solid:
        gcol, galpha = style['ghost']
        if ghost_alpha is None:
            # with a glass fluid already in the frame, keep the ghost faint
            # so the fluid is the translucent layer the eye resolves
            if len(meshes) > 1:
                galpha *= 0.6
        else:
            # absolute opacity, not a multiplier: a multiplier compounds
            # with the 0.6 above and quietly makes the rock invisible
            galpha = float(ghost_alpha)
        if solid_mesh is None:
            s = (_smooth_binary(solid.astype(np.float32)) if smooth_solid
                 else solid)
            solid_mesh = surface(s.astype(np.float32), 0.5, spacing=spacing,
                                 origin=origin,
                                 decimate=0.5 if decimate is None else decimate)
        pl.add_mesh(solid_mesh, color=gcol, opacity=galpha,
                    smooth_shading=False, lighting=True)
    for tag, mesh, col, alpha in meshes:
        add_fluid(pl, mesh, col, style, opacity=alpha, name=tag)
    if len(meshes) == 2 and not quiet:
        # the two bodies are contiguous at psi=0; VTK resolves the coincident
        # topology, but a hairline inset is available via --level-gap if the
        # shared interface ever speckles.
        print(f'     pts nw={meshes[0][1].n_points} '
              f'wet={meshes[1][1].n_points}  level_gap={abs(level_gap):g}')
    add_domain_box(pl, bounds, style, label=title)
    set_iso_camera(pl, view=view)
    if scale_bar:
        add_scale_bar(pl, scale_bar, style)
    if FLOW:
        add_flow_markers(pl, style)
    return save(pl, out_png, style)


def panel_clusters(run, out_png, style, top=12, cutaway=1.0, full=False,
                   min_voxels=8, ghost_solid=True, spacing=(1, 1, 1),
                   scale_bar=None, title=None, decimate=None):
    """P4: trapped non-wetting clusters, one colour each, ranked by volume.

    Only `top` clusters get a palette colour; everything smaller is drawn in
    a neutral tint so the picture does not overstate the ranking."""
    from scipy import ndimage

    psi, solid = pore_domain(run, full=full)
    if cutaway < 1.0:
        c = max(int(psi.shape[0] * cutaway), 2)
        psi, solid = psi[:c], solid[:c]
    pore = solid == 0
    red = (psi > 0.0) & pore
    lab, n = ndimage.label(red)
    if n == 0:
        raise SystemExit('no non-wetting clusters found')
    sizes = ndimage.sum(red, lab, index=np.arange(1, n + 1))
    keep = [i for i in np.argsort(sizes)[::-1] if sizes[i] >= min_voxels]
    top = keep[:top]
    overflow = keep[len(top):]
    pore_vox = int(pore.sum())
    print(f'  {n} clusters, {len(keep)} >= {min_voxels} voxels, '
          f'top share {sum(sizes[i] for i in top) / pore_vox:.4f} of pore')

    pl = new_plotter(style)
    if ghost_solid:
        gcol, galpha = style['ghost']
        ghost = surface(solid.astype(np.float32), 0.5, spacing=spacing,
                        decimate=0.4 if decimate is None else decimate)
        pl.add_mesh(ghost, color=gcol, opacity=galpha, lighting=True)

    cmap = style['clusters']
    legend = []
    for rank, idx in enumerate(top):
        lb = idx + 1
        # contour inside the cluster's own padded bounding box: cheap, and
        # keeps a 24-cluster figure to a few seconds
        bb = ndimage.find_objects(lab == lb)[0]
        sl = tuple(slice(max(b.start - 1, 0), min(b.stop + 1, s))
                   for b, s in zip(bb, lab.shape))
        sub = lab[sl] == lb
        f = np.where(sub, psi[sl], np.float32(-1.0))
        origin = tuple(s.start for s in sl)
        m = surface(f, 0.0, spacing=spacing, origin=origin,
                    decimate=decimate)
        col = cmap[rank % len(cmap)]
        add_fluid(pl, m, col, style, name=f'cluster{rank}')
        legend.append([f'c{rank + 1}  {sizes[idx] / pore_vox * 100:.1f}%', col])
    if overflow:
        ocol, oalpha = style['overflow']
        for idx in overflow:
            lb = idx + 1
            bb = ndimage.find_objects(lab == lb)[0]
            sl = tuple(slice(max(b.start - 1, 0), min(b.stop + 1, s))
                       for b, s in zip(bb, lab.shape))
            f = np.where(lab[sl] == lb, psi[sl], np.float32(-1.0))
            m = surface(f, 0.0, spacing=spacing,
                        origin=tuple(s.start for s in sl))
            pl.add_mesh(m, color=ocol, opacity=oalpha, lighting=True)
        legend.append([f'{len(overflow)} smaller', ocol])

    add_domain_box(pl, _domain_bounds(run, psi, full, spacing), style,
                   label=title)
    set_iso_camera(pl)
    try:
        # light legend box in both styles so the default black text stays
        # readable on the dark slide ground
        pl.add_legend(legend, border=True, size=(0.26, 0.34),
                      loc='upper right')
    except Exception as exc:                                  # noqa: BLE001
            _warn('add_legend', exc)
    if scale_bar:
        add_scale_bar(pl, scale_bar, style)
    if FLOW:
        add_flow_markers(pl, style)
    return save(pl, out_png, style)


def panel_slices(run, out_png, style, full=False, vlim=1.2):
    """P1: three orthogonal mid-slices of psi with the grain contour.

    The diverging map runs blue(psi<0, wetting) -> pale(interface) ->
    warm(psi>0, non-wetting), i.e. the same phase colours as the surface
    panels, so P1/P2/P3 read as one palette.  NB the in-loop
    run_pcs_cg3d.mid_slice_png uses plain RdBu, which maps psi>0 to blue —
    the opposite sense; see VIZ_3D_STYLE.md.  post3d.slice_montage remains
    available for ad-hoc multi-field montages."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list('psi_phase', style['psi_cmap'])
    psi, solid = pore_domain(run, full=full)
    nx, ny, nz = psi.shape
    planes = ((psi[nx // 2], 'yz @ mid-x'), (psi[:, ny // 2], 'xz @ mid-y'),
              (psi[:, :, nz // 2], 'xy @ mid-z'))
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.9),
                             constrained_layout=True)
    for ax, (sl, name) in zip(axes, planes):
        im = ax.imshow(sl.T, origin='lower', cmap=cmap, vmin=-vlim,
                       vmax=vlim, aspect='equal')
        ax.contour(sl.T, levels=[0.0], colors='k', linewidths=0.4)
        ax.set_title(name, fontsize=9)
        ax.set_xticks([]), ax.set_yticks([])
        if FLOW and 'x' in name.split('@')[0].strip():
            # x runs horizontally on the xz/xy planes: mark the flow ends
            ax.text(0.02, 0.05, 'inlet \u2192', transform=ax.transAxes,
                    fontsize=8)
            ax.text(0.98, 0.05, '\u2192 outlet', transform=ax.transAxes,
                    fontsize=8, ha='right')
    fig.colorbar(im, ax=axes, shrink=0.82, label='psi')
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f'  -> {out_png}')
    return out_png


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


# ------------------------------------------------------------- animation
def _series_files(spec, skip=('f_solid',)):
    """Frame list from a directory, a glob, or a single file."""
    if os.path.isdir(spec):
        fs = sorted(os.path.join(spec, f) for f in os.listdir(spec)
                    if f.endswith('.npz')
                    and not any(f.startswith(s) for s in skip))
    elif any(ch in spec for ch in '*?['):
        import glob as _glob
        fs = sorted(_glob.glob(spec))
    else:
        fs = [spec]
    if not fs:
        raise SystemExit(f'no frames matched {spec!r}')
    return fs


def _load_frame(path):
    """(psi, solid|None, meta) from a dump frame.

    Accepts the CG naming (`psi`, or the int8 `psi_q` written by the
    runner's --dump-every, quantised at 0.01 = 1/220 of the phase range) and
    the Shan-Chen naming (`phase` = rho1-rho2, or rho1/rho2 themselves), so
    one animation path serves both solver families.
    """
    z = np.load(path)
    src = None
    for key, fn in (('psi', lambda a: a.astype(np.float32)),
                    ('psi_q', lambda a: a.astype(np.float32) / 100.0),
                    ('phase', lambda a: a.astype(np.float32)),
                    ('rho1', None)):
        if key == 'rho1':
            if 'rho1' in z.files and 'rho2' in z.files:
                psi = (z['rho1'].astype(np.float32)
                       - z['rho2'].astype(np.float32))
                src = 'rho1-rho2'
                break
            continue
        if key in z.files:
            psi = fn(z[key])
            src = key
            break
    else:
        raise SystemExit(f'{path} has no psi / psi_q / phase / rho1-rho2')
    solid = z['solid'].astype(np.int8) if 'solid' in z.files else None
    meta = {}
    for k in z.files:
        if k in ('psi', 'psi_q', 'phase', 'rho1', 'rho2', 'solid'):
            continue
        try:
            meta[k] = float(z[k])
        except Exception:                                    # noqa: BLE001
            pass
    return psi, solid, meta, src


def _frame_label(tag, meta, fmt=None):
    if fmt:
        try:
            return fmt.format(tag=tag, **meta)
        except Exception as exc:                              # noqa: BLE001
            _warn('label format', exc)
    parts = [tag]
    if 'it' in meta or 'step' in meta:
        parts.append(f'step {int(meta.get("it", meta.get("step", 0)))}')
    for key, name in (('Pc', 'Pc'), ('d', 'dP'), ('s_nw', 'S_nw')):
        if key in meta:
            parts.append(f'{name}={meta[key]:.4f}' if key in ('d', 'Pc')
                         else f'{name}={meta[key]:.3f}')
    return '   '.join(parts)


def make_gif(pngs, gif_path, duration=450, colors=256, max_width=None):
    """Assemble PNGs into a looping GIF; per-frame adaptive palette."""
    from PIL import Image

    ims = [Image.open(p).convert('RGB') for p in pngs]
    if max_width and ims[0].width > max_width:
        ims = [im.resize((max_width, max(1, round(im.height * max_width
                                                  / im.width))),
                         Image.LANCZOS) for im in ims]
    frames = [im.quantize(colors=colors, method=Image.MEDIANCUT)
              for im in ims]
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True)
    size = os.path.getsize(gif_path)
    print(f'  -> {gif_path}  {len(frames)} frames  {duration} ms  '
          f'{ims[0].width}x{ims[0].height}  {size / 1e6:.2f} MB')
    return gif_path


def animate(series, out_dir, style_name='report', cutaway=0.55,
            cut_axis='y', cut_keep='hi', window=(1000, 780), duration=450,
            ghost_alpha=0.15, scale_bar=None, decimate=None, solid_path=None,
            label_fmt=None, every=1, max_frames=None, colors=256,
            gif_width=None, tag=None, merge_solid=True, opaque='nw',
            view='iso'):
    """Render a frame series in a fixed camera and write a looping GIF.

    Defaults differ from the static panels on purpose:
      * cut on **y** (not x): cutting x throws away the downstream half of
        the box, so an advancing front would vanish at the cut plane.  A
        y-cut keeps inlet-to-outlet across the frame, inlet on the left.
      * the solid sits at an absolute opacity of 0.15 (not the static
        panels' faintest ghost) so the skeleton reads as a rock you can see
        the fluids through, rather than vanishing.
      * the glass/opaque assignment is frozen from the whole series, so the
        colours do not swap halfway through the clip.
    """
    fs = _series_files(series)[::max(every, 1)]
    if max_frames:
        fs = fs[:max_frames]
    tag = tag or os.path.basename(os.path.normpath(
        series if os.path.isdir(series) else os.path.dirname(series)))
    st = _style(style_name)
    os.makedirs(out_dir, exist_ok=True)
    print(f'[{tag}] {len(fs)} frames from {series}')

    psi0, solid, meta0, src = _load_frame(fs[0])
    print(f'     phase field from {src!r}')
    if solid is None:
        cand = os.path.join(series if os.path.isdir(series)
                            else os.path.dirname(series), 'f_solid.npz')
        src = solid_path or (cand if os.path.exists(cand) else None)
        if src is None:
            raise SystemExit('no solid in the frames and no --solid given')
        solid = np.load(src)['solid'].astype(np.int8)
        print(f'     solid from {src}  {solid.shape}')
    nx = psi0.shape[0]
    run = dict(psi=psi0, solid=solid, dom=slice(0, nx), tag=tag,
               R_lu=None, npz=fs[0], res_thick=0, meta={})

    # solid never changes: build (and crop) its mesh once for the whole clip
    solid_c, origin = _crop3(solid, cut_axis, cutaway, cut_keep)
    ghost = None
    if merge_solid:
        ghost = surface(solid_c.astype(np.float32), 0.5,
                        spacing=(1, 1, 1), origin=origin,
                        decimate=0.5 if decimate is None else decimate)
        print(f'     solid ghost mesh: {ghost.n_points} pts (built once)')

    # The opaque phase is frozen for the whole clip; flipping mid-animation
    # would read as a rendering bug.  Default 'nw' = the invading phase in
    # drainage stays solid, so the advancing front is never lost inside a
    # glass wash.  Pass opaque='wet' for an imbibition film.
    psi_last, _, meta_last, _ = _load_frame(fs[-1])
    pc, _ = _crop3(psi_last, cut_axis, cutaway, cut_keep)
    sc, _ = _crop3(solid, cut_axis, cutaway, cut_keep)
    frac_nw = float(((pc > 0.0) & (sc == 0)).sum()) / max((sc == 0).sum(), 1)
    print(f'     final S_nw(cropped)={frac_nw:.3f}; opaque={opaque} '
          f'(frozen for the whole clip)')

    pngs = []
    for k, f in enumerate(fs):
        psi, _, meta, _ = _load_frame(f)
        m = dict(meta0)
        m.update(meta)
        out_png = os.path.join(out_dir, f'anim_{k:04d}.png')
        panel_cutaway(run, out_png, st, focus='both', cutaway=cutaway,
                      cut_axis=cut_axis, cut_keep=cut_keep,
                      solid_mesh=ghost, psi_override=psi, opaque=opaque,
                      ghost_alpha=ghost_alpha, decimate=decimate,
                      scale_bar=scale_bar, window=window, view=view,
                      title=_frame_label(tag, m, label_fmt), quiet=True)
        pngs.append(out_png)
        if (k + 1) % 5 == 0 or k == len(fs) - 1:
            print(f'     frame {k + 1}/{len(fs)}', flush=True)
    montage([pngs[i] for i in np.linspace(0, len(pngs) - 1,
                                         min(8, len(pngs))).astype(int)],
            os.path.join(out_dir, f'{tag}_anim_qa.png'), cols=4)
    gif = os.path.join(out_dir, f'{tag}_drain.gif')
    make_gif(pngs, gif, duration=duration, colors=colors,
             max_width=gif_width)
    return gif


# ----------------------------------------------------------------- helpers
def _warn(what, exc):
    """Cosmetic failures must be visible, never silently swallowed."""
    print(f'  ! {what}: {type(exc).__name__}: {exc}')


def _smooth_binary(a, sigma=0.8):
    """Gaussian-blurred binary field for a smoother 0.5 level set.

    Opt-in only: the solver sees voxelised spheres, so the default renders
    the staircase honestly.  Blurring pulls the surface slightly inward.
    """
    from scipy import ndimage

    return ndimage.gaussian_filter(np.asarray(a, dtype=np.float32), sigma)


def _domain_bounds(run, psi, full, spacing=(1, 1, 1)):
    x0 = 0.0 if full else float(run['dom'].start)
    n = psi.shape
    return (x0 * spacing[0], x0 * spacing[0] + (n[0] - 1) * spacing[0],
            0.0, (n[1] - 1) * spacing[1],
            0.0, (n[2] - 1) * spacing[2])


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
    global FLOW
    if args.no_flow:
        FLOW = False

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
