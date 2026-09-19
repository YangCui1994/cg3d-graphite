"""Shared checkpoint figure + compat re-exports for the two cg3d drivers.

Deduped 2026-09-16 (PLAN_code_cleanup_2026-09 Step 3) from two near-verbatim
copies: the drainage driver additionally drew the psi=0 interface line on
each slice (contour=True); the imbibition driver never did (contour=False).
Note the old drainage signature carried an unused `solid` argument — dropped
here.  Outputs are pixel-identical to the per-driver originals.

PR-5 (2026-09-19): the numeric instruments (region_stats /
eval_convergence / label_periodic) moved to cg3d/diagnostics.py; they are
re-exported here so existing imports keep working.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from cg3d.diagnostics import (  # noqa: F401  (compat re-export)
    region_stats, eval_convergence, label_periodic)


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
