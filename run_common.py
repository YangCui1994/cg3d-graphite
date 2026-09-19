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
