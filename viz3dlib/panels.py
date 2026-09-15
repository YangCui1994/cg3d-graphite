"""viz3dlib.panels — The individual figure panels (geometry / cutaway / clusters / slices)."""
from __future__ import annotations

import numpy as np

from .plotting import _bounds, _crop3, add_domain_box, add_flow_markers, add_fluid, add_scale_bar, new_plotter, save, set_iso_camera, surface
from .runio import _domain_bounds, _smooth_binary, pore_domain
from .style_env import WINDOW, _warn


FLOW = True          # inlet/outlet markers on 3D panels (CLI: --no-flow)


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
