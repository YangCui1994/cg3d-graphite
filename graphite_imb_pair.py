"""Imbibition before/after pair (user palette, 2D slices).

Before = end of drainage at S_i-level saturation: gx2_drain d03 last frame
          (step 140k, graphite-region S_nw=0.573; gx3's own drained state
          was S_i=0.558 -- same level, different run, path note in caption).
After  = gx3_ir final (post-imbibition): trapped gas S_nr=0.171.
Same geometry/psi_solid; gx3 final cropped to the same domain window as the
frames so graphite faces sit at x=2/202 in both.

Output: fig_gx_imb_pair.png  (2 rows xz/xy x 2 cols before/after)
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

RES = 'results_pcs_cg3d'
OUT = '../../../../output_docs/figures_graphite'

C_LIQ, A_LIQ = (0.20, 0.42, 0.78), 0.55
C_SOL, A_SOL = (0.44, 0.44, 0.44), 0.90
C_GAS, A_GAS = (0.82, 0.08, 0.08), 0.93


def phase_image(psi, solid):
    img = np.ones(psi.shape + (3,))
    pore = solid == 0
    for mask, c, a in (((pore & (psi < 0)), C_LIQ, A_LIQ),
                       ((~pore), C_SOL, A_SOL),
                       ((pore & (psi >= 0)), C_GAS, A_GAS)):
        img[mask] = a * np.array(c) + (1 - a)
    return img


def main():
    # before: last d03 frame (dom-cropped, 205x200x200)
    fr = np.load(f'{RES}/gx2_drain/frames/f_0140000.npz')
    solid_b = np.load(f'{RES}/gx2_drain/frames/f_solid.npz')['solid']
    psi_b = fr['psi_q'].astype(np.float32) / 100.0
    # after: gx3 final (full 228 cube) -> crop to the same dom window
    fin = np.load(f'{RES}/gx3_ir/final.npz')
    solid_a = fin['solid'][12:217]
    psi_a = fin['psi'][12:217]

    ny, nz = solid_b.shape[1], solid_b.shape[2]
    assert solid_a.shape == solid_b.shape, (solid_a.shape, solid_b.shape)
    fig, axes = plt.subplots(2, 2, figsize=(8.6, 8.2),
                             constrained_layout=True)
    ori = [['xz @ mid-y', 'xz @ mid-y'], ['xy @ mid-z', 'xy @ mid-z']]
    for c, (psi, sol, ttl) in enumerate((
            (psi_b, solid_b,
             'BEFORE: end of drainage   $S_i$=0.56 (gas connected)'),
            (psi_a, solid_a,
             'AFTER: end of imbibition   $S_{nr}$=0.17 (gas trapped)'))):
        draw = [(psi[:, ny // 2, :], sol[:, ny // 2, :]),
                (psi[:, :, nz // 2], sol[:, :, nz // 2])]
        for r, (p2, s2) in enumerate(draw):
            ax = axes[r, c]
            ax.imshow(phase_image(p2, s2).transpose(1, 0, 2), origin='lower',
                      interpolation='nearest', aspect='equal')
            ax.set_xticks([]), ax.set_yticks([])
            if r == 0:
                ax.set_title(ttl, fontsize=9.5)
            ax.text(0.03, 0.04, ori[r][c], transform=ax.transAxes,
                    fontsize=7.5, color='0.2',
                    bbox=dict(facecolor='white', edgecolor='none',
                              alpha=0.75, pad=1.5))
            ax.annotate('inlet', (0.01, -0.055), xycoords='axes fraction',
                        fontsize=8)
            ax.annotate('outlet', (0.99, -0.055), xycoords='axes fraction',
                        fontsize=8, ha='right')
    handles = [Patch(facecolor=C_SOL, alpha=A_SOL, label='graphite (solid)'),
               Patch(facecolor=C_LIQ, alpha=A_LIQ,
                     label='electrolyte (wetting, psi<0)'),
               Patch(facecolor=C_GAS, alpha=A_GAS,
                     label='gas (non-wetting, psi>0)')]
    fig.legend(handles=handles, loc='upper center', ncol=3, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 1.03))
    plt.savefig(f'{OUT}/fig_gx_imb_pair.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('fig_gx_imb_pair ok')


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
