"""Shared checkpoint figure for the two cg3d drivers.

Deduped 2026-09-16 (PLAN_code_cleanup_2026-09 Step 3) from two near-verbatim
copies: the drainage driver additionally drew the psi=0 interface line on
each slice (contour=True); the imbibition driver never did (contour=False).
Note the old drainage signature carried an unused `solid` argument — dropped
here.  Outputs are pixel-identical to the per-driver originals.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

_CONN_STRUCT = {6: ndimage.generate_binary_structure(3, 1),
                18: ndimage.generate_binary_structure(3, 2),
                26: ndimage.generate_binary_structure(3, 3)}


def _seam_offsets(struct, ax):
    """Structural offsets with a +1 step along `ax` (each cross-seam
    neighbour direction, counted once)."""
    offs = []
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            for oz in (-1, 0, 1):
                off = (ox, oy, oz)
                if off[ax] == 1 and struct[ox + 1, oy + 1, oz + 1]:
                    offs.append(off)
    return offs


def label_periodic(mask, conn=6, periodic_axes=(1, 2)):
    """Connected components with wrap-around merging (PR-3, tasks
    2.6/2.7).  The solver is y/z-periodic, so a phase cluster touching
    both ends of a periodic axis is ONE cluster; plain ndimage.label
    splits it.  Implementation: label non-periodically, then union-find
    merge label pairs that are neighbours across each periodic seam
    (plane 0 vs plane -1, offsets with a +1 step along the seam axis).
    NOTE: padding with one wrapped layer does NOT work — the pad copy
    and the original cell get different labels.  Returns
    (labels, sizes_sorted_desc); sizes count interior cells only."""
    m = np.asarray(mask, dtype=bool)
    S = _CONN_STRUCT[conn]
    lab, n = ndimage.label(m, structure=S)
    if n == 0:
        return lab, np.array([], dtype=np.int64)
    parent = list(range(n + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    dims = m.shape
    for ax in periodic_axes:
        d1, d2 = [d for d in range(3) if d != ax]
        plo = [slice(None)] * 3
        plo[ax] = 0
        phi = [slice(None)] * 3
        phi[ax] = -1
        lo_l, hi_l = lab[tuple(plo)], lab[tuple(phi)]
        lo_m, hi_m = m[tuple(plo)], m[tuple(phi)]
        for off in _seam_offsets(S, ax):
            o1, o2 = off[d1], off[d2]
            # neighbour B = A - off on the in-plane axes, +1 across seam
            sA1 = slice(max(0, o1), dims[d1] + min(0, o1))
            sB1 = slice(max(0, -o1), dims[d1] + min(0, -o1))
            sA2 = slice(max(0, o2), dims[d2] + min(0, o2))
            sB2 = slice(max(0, -o2), dims[d2] + min(0, -o2))
            a = lo_l[sA1, sA2]
            am = lo_m[sA1, sA2]
            b = hi_l[sB1, sB2]
            bm = hi_m[sB1, sB2]
            both = am & bm & (a > 0) & (b > 0)
            if both.any():
                for x, y in zip(a[both].tolist(), b[both].tolist()):
                    rx, ry = find(x), find(y)
                    if rx != ry:
                        parent[max(rx, ry)] = min(rx, ry)

    roots = np.array([find(i) for i in range(n + 1)])
    _, inv = np.unique(roots[1:], return_inverse=True)
    relabel = np.zeros(n + 1, dtype=lab.dtype)
    relabel[1:] = inv + 1
    lab2 = relabel[lab]
    sizes = np.sort(np.bincount(lab2.ravel())[1:])[::-1]
    return lab2, sizes


def eval_convergence(win, pore_cells, qs_tol, pc_drift_tol=0.01,
                     flux_tol=1e-6, u_rel_tol=0.05):
    """Multi-indicator quasi-steady record (PR-3, task 2.4; structure per
    Plan_20260919_v2 §Phase 2).  win = trailing window of (it, dict)
    sample pairs carrying s_nw / pc_measured / inj_r / inj_b / u_rms
    (PR-1 instruments).  Returns a JSON-ready dict answering "why did
    this rung exit"; thresholds live in the driver's config layer."""
    out = dict(criteria_passed=[], thresholds=dict(
        saturation_slope=qs_tol, pc_drift=pc_drift_tol,
        phase_flux=flux_tol, u_rms_rel=u_rel_tol))
    if len(win) < 2:
        return out
    its = [i for i, _ in win]
    ms = [m for _, m in win]
    span = its[-1] - its[0]
    if span <= 0:
        return out
    out['saturation_slope'] = (ms[-1]['s_nw'] - ms[0]['s_nw']) / span
    pcs = [m['pc_measured'] for m in ms]
    pc_scale = max(abs(float(np.mean(pcs))), 1e-12)
    out['pc_drift'] = (max(pcs) - min(pcs)) / pc_scale
    fr = (ms[-1]['inj_r'] - ms[0]['inj_r']) / span / pore_cells
    fb = (ms[-1]['inj_b'] - ms[0]['inj_b']) / span / pore_cells
    out['phase_flux'] = abs(fr) + abs(fb)
    us = [m['u_rms'] for m in ms]
    out['u_rms_rel'] = (max(us) - min(us)) / max(float(np.mean(us)), 1e-30)
    if abs(out['saturation_slope']) < qs_tol:
        out['criteria_passed'].append('saturation')
    if out['pc_drift'] < pc_drift_tol:
        out['criteria_passed'].append('pressure')
    if out['phase_flux'] < flux_tol:
        out['criteria_passed'].append('flux')
    if out['u_rms_rel'] < u_rel_tol:
        out['criteria_passed'].append('kinetic')
    return out


def region_stats(rho, psi, v, mask):
    """PR-1 instrument (Plan_20260919_v2, tasks 2.1-2.3): host-side
    regional diagnostics from snapshot arrays.

    rho, psi: (nx, ny, nz) float; v: (nx, ny, nz, 3); mask: boolean array
    of the same shape.  Pressure uses the ideal LBM relation p = cs^2 rho
    with cs^2 = 1/3 (incompressible limit; this solver has no bulk free
    energy).  Pure numpy, no solver state touched."""
    m = np.asarray(mask, dtype=bool)
    n = int(m.sum())
    if n == 0:
        return dict(n=0, rho_mean=None, p_mean=None, psi_mean=None,
                    v_rms=None, v_bulk=(None, None, None))
    rho_m = float(rho[m].mean(dtype=np.float64))
    vmag2 = (v[..., 0]**2 + v[..., 1]**2 + v[..., 2]**2)[m]
    vb = v[m]
    return dict(n=n,
                rho_mean=rho_m,
                p_mean=rho_m / 3.0,
                psi_mean=float(psi[m].mean(dtype=np.float64)),
                v_rms=float(np.sqrt(vmag2.mean(dtype=np.float64))),
                v_bulk=(float(vb[:, 0].mean(dtype=np.float64)),
                        float(vb[:, 1].mean(dtype=np.float64)),
                        float(vb[:, 2].mean(dtype=np.float64))))



def mid_slice_png(psi, path, title, contour=False):
    """Two mid-slices (yz at mid-x, xz at mid-y) of psi, light enough for
    every checkpoint."""
    nx = psi.shape[0]
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.4))
    for ax, sl, name in ((axes[0], psi[nx // 2], 'yz@mid-x'),
                         (axes[1], psi[:, psi.shape[1] // 2], 'xz@mid-y')):
        im = ax.imshow(sl.T, origin='lower', cmap='RdBu', vmin=-1.2,
                       vmax=1.2, aspect='equal')
        if contour:
            ax.contour(sl.T, levels=[0.0], colors='k', linewidths=0.4)
        ax.set_title(name, fontsize=8)
        ax.set_xticks([]), ax.set_yticks([])
    fig.colorbar(im, ax=axes, shrink=0.8, label='psi')
    fig.suptitle(title, fontsize=9)
    plt.savefig(path, dpi=120)
    plt.close()
