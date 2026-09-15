"""viz3dlib.plotting — PyVista primitives: meshes, plotter setup, annotations, save."""
from __future__ import annotations

import numpy as np

from .style_env import VIEWS, WINDOW, _warn


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
