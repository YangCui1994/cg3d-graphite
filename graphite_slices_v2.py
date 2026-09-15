"""v2 slice figures for the graphite report (user-requested recolor + boundary map).

Renders FROM DATA (frames + final.npz), not from the old checkpoint PNGs:
  fig_gx_slices_v2.png  constant-delta (d=0.074) invasion progression, 4 steps
                        x 2 orientations; graphite=opaque gray, electrolyte=blue,
                        gas=strong opaque red (user palette; gas most present)
  fig_gx_solid_only.png solid-only mid-slices (final state) + to-scale x-boundary
                        map: wall / reservoir / membrane / buffer / graphite
  fig_gx_anim_strip.png 3-frame strip from the iso animation (t=20k/80k/140k)

In-figure text stays English (matplotlib default font has no CJK); the PDF
captions carry the Chinese explanation.
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch, Rectangle
from PIL import Image
import numpy as np

RES = 'results_pcs_cg3d'
OUT = '../../../../output_docs/figures_graphite'

# user palette: graphite slightly opaque gray, electrolyte blue,
# gas even more opaque red (gas must dominate the eye)
C_LIQ, A_LIQ = (0.20, 0.42, 0.78), 0.55      # electrolyte (psi < 0)
C_SOL, A_SOL = (0.44, 0.44, 0.44), 0.90      # graphite solid
C_GAS, A_GAS = (0.82, 0.08, 0.08), 0.93      # gas (psi > 0)


def phase_image(psi, solid):
    """Per-pixel categorical color, alpha-blended over white."""
    img = np.ones(psi.shape + (3,))
    pore = solid == 0
    for mask, c, a in (((pore & (psi < 0)), C_LIQ, A_LIQ),
                       ((~pore), C_SOL, A_SOL),
                       ((pore & (psi >= 0)), C_GAS, A_GAS)):
        img[mask] = a * np.array(c) + (1 - a)
    return img


def draw_phase_ax(ax, psi, solid, title):
    ax.imshow(phase_image(psi, solid).transpose(1, 0, 2), origin='lower',
              interpolation='nearest', aspect='equal')
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_title(title, fontsize=8.5)


def progression():
    """d03 frames (constant delta=0.074): 4 steps x (xz@mid-y, xy@mid-z)."""
    solid = np.load(f'{RES}/gx2_drain/frames/f_solid.npz')['solid']
    picks = ['f_0020000.npz', 'f_0060000.npz', 'f_0100000.npz',
             'f_0140000.npz']
    snw = {20: 0.35, 60: 0.44, 100: 0.51, 140: 0.57}   # graphite-region
    frames = [np.load(f'{RES}/gx2_drain/frames/{p}') for p in picks]
    ny, nz = solid.shape[1], solid.shape[2]
    fig, axes = plt.subplots(2, 4, figsize=(12.6, 7.0), constrained_layout=True)
    for c, z in enumerate(frames):
        psi = z['psi_q'].astype(np.float32) / 100.0
        t = int(z['it']) // 1000
        draw_phase_ax(axes[0, c], psi[:, ny // 2, :], solid[:, ny // 2, :],
                      f'xz @ mid-y   step {t}k   S_nw={snw[t]:.2f}')
        draw_phase_ax(axes[1, c], psi[:, :, nz // 2], solid[:, :, nz // 2],
                      f'xy @ mid-z   step {t}k')
    for r in range(2):
        axes[r, 0].annotate('inlet', (0.01, -0.075),
                            xycoords='axes fraction', fontsize=9)
        axes[r, 0].annotate('outlet', (0.99, -0.075),
                            xycoords='axes fraction', fontsize=9, ha='right')
    handles = [Patch(facecolor=C_SOL, alpha=A_SOL, label='graphite (solid)'),
               Patch(facecolor=C_LIQ, alpha=A_LIQ,
                     label='electrolyte (wetting, psi<0)'),
               Patch(facecolor=C_GAS, alpha=A_GAS,
                     label='gas (non-wetting, psi>0)')]
    fig.legend(handles=handles, loc='upper center', ncol=3, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 1.04))
    fig.suptitle('Constant-pressure invasion, delta=0.074 '
                 '(main-invasion rung); graphite faces at x=2/202 '
                 '(cropped domain = x=14/214 in the full layout)',
                 fontsize=10)
    plt.savefig(f'{OUT}/fig_gx_slices_v2.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('fig_gx_slices_v2 ok')


ZONES = [   # (x0, x1, facecolor, label)  -- full 228-cube layout, to scale
    (0, 3, '0.25', 'wall'),
    (3, 11, '#f2b8b8', 'res in'),
    (12, 14, '#ffffff', 'buf'),
    (14, 214, '0.72', 'GRAPHITE  x=14..214'),
    (214, 217, '#ffffff', 'buf'),
    (218, 225, '#bcd2ee', 'res out'),
    (225, 228, '0.25', 'wall'),
]


def zone_bar(ax):
    ax.set_xlim(0, 228), ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([0, 14, 114, 214, 228])      # sparse: fine edges live in
    ax.tick_params(labelsize=7)                 # the zone colors themselves
    for x0, x1, fc, lab in ZONES:
        ax.add_patch(Rectangle((x0, 0.15), x1 - x0, 0.7, facecolor=fc,
                               edgecolor='0.4', lw=0.4))
        if x1 - x0 > 40:
            ax.text((x0 + x1) / 2, 0.5, lab, ha='center', va='center',
                    fontsize=8.5)
    for x in (11, 217):
        ax.axvline(x, color='k', ls='--', lw=1.1)
    ax.set_xlabel('x [lu];  dashed lines = semi-permeable membranes '
                  '(x=11 gas-side, x=217 liquid-side)', fontsize=8)


def layout_image(solid2d):
    """Solid slice with the boundary layout tinted in-place: walls dark,
    inlet-reservoir pore faint red (gas source), outlet-reservoir pore
    faint blue (liquid sink), buffer/bulk pore white, graphite gray."""
    img = np.ones(solid2d.shape + (3,))
    nx, ny = solid2d.shape
    xi = np.arange(nx)[:, None]
    img[solid2d == 1] = np.array(C_SOL)                  # graphite
    img[((xi < 3) | (xi >= 225)) & (solid2d == 1)] = 0.22   # walls darker
    pore = solid2d == 0
    img[pore & ((xi >= 3) & (xi < 11))] = 0.65 + 0.35 * np.array(
        (0.95, 0.45, 0.45))                              # faint red tint
    img[pore & ((xi >= 218) & (xi < 225))] = A_LIQ * np.array(
        C_LIQ) + (1 - A_LIQ)                             # faint blue tint
    return img


def solid_only():
    z = np.load(f'{RES}/gx2b_drain/final.npz')
    solid = z['solid']
    ny, nz = solid.shape[1], solid.shape[2]
    fig = plt.figure(figsize=(8.2, 9.4))
    gs = GridSpec(4, 1, height_ratios=[3.0, 0.9, 3.0, 0.9], hspace=0.42)
    for row, (sl, ttl) in enumerate((
            (solid[:, ny // 2, :], 'solid only, xz @ mid-y  '
             '(graphite gray, walls near-black, reservoirs tinted)'),
            (solid[:, :, nz // 2], 'solid only, xy @ mid-z'))):
        ax_img = fig.add_subplot(gs[row * 2])
        ax_bar = fig.add_subplot(gs[row * 2 + 1], sharex=ax_img)
        ax_img.imshow(layout_image(sl).transpose(1, 0, 2), origin='lower',
                      interpolation='nearest', aspect='auto',
                      extent=(0, 228, 0, 200))
        for x in (14, 214):
            ax_img.axvline(x, color='k', lw=1.3)
        ax_img.set_title(ttl + '   (black lines = graphite faces x=14/214)',
                         fontsize=9)
        ax_img.set_xticks([0, 14, 114, 214, 228])
        ax_img.tick_params(labelsize=7)
        ax_img.set_ylabel('transverse [lu]', fontsize=8)
        zone_bar(ax_bar)
    ax_bar.annotate('inlet', (0.0, -0.85), xycoords='axes fraction',
                    fontsize=10)
    ax_bar.annotate('outlet', (1.0, -0.85), xycoords='axes fraction',
                    fontsize=10, ha='right')
    handles = [
        Patch(facecolor='0.72', label='graphite (real structure, 200 lu)'),
        Patch(facecolor='#ffffff', edgecolor='0.4',
              label='open-pore buffer pad (14 lu, decoupling fix)'),
        Patch(facecolor='#f2b8b8',
              label='inlet reservoir psi=+1 (gas source, 8 lu)'),
        Patch(facecolor='#bcd2ee',
              label='outlet reservoir psi=-1 (liquid sink, 8 lu)'),
        Patch(facecolor='0.25', label='solid wall, bounce-back (3 lu)'),
        Patch(facecolor='none', edgecolor='k', ls='--',
              label='semi-permeable membrane (plane)'),
    ]
    fig.legend(handles=handles, loc='upper center', ncol=3, fontsize=8.5,
               frameon=False, bbox_to_anchor=(0.5, 1.05))
    plt.savefig(f'{OUT}/fig_gx_solid_only.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('fig_gx_solid_only ok')


def anim_strip():
    picks = ['anim_0000.png', 'anim_0003.png', 'anim_0006.png']
    ims = [Image.open(f'{OUT}/anim_gx_d03/{p}') for p in picks]
    w = 620
    ims = [im.resize((w, int(im.height * w / im.width))) for im in ims]
    h = min(im.height for im in ims)
    canvas = Image.new('RGB', (w * 3 + 8, h), 'white')
    for k, im in enumerate(ims):
        canvas.paste(im, (k * (w + 4), 0))
    canvas.save(f'{OUT}/fig_gx_anim_strip.png')
    print('fig_gx_anim_strip ok')


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(OUT, exist_ok=True)
    progression()
    solid_only()
    # anim_strip() dropped from the report: 3D amber/navy palette conflicts
    # with the requested 2D red/blue/gray scheme; tiny burned-in captions
    # (visual review 2026-09-15). The GIF itself stays a supplementary file.
