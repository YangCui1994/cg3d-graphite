"""Initial-condition + boundary-condition figure for real graphite (2026-09-20).

Row 1  DRAINAGE t=0  — exact IC reconstruction, pure-numpy mirror of
       cg3d/protocol.py OpenSystem.__init__ (psi0): every pore is electrolyte
       (psi=-1), gas is preset ONLY in the inlet reservoir + inlet membrane
       plane x in [3, 12); outlet membrane stays liquid-prewet.
Row 2  IMBIBITION start-of-arm — the state imbibition inherits = end of the
       drainage ladder of gx3c_postaudit (d=0.074 rung-end dump frame,
       S_nw~0.53; sat criterion NOT passed -> Plan v2 Phase 7.3 will rerun
       converged states). Reservoir/membrane slabs reattached per protocol.

No solver import (no Taichi cost): geometry npz + dump frame only.

Outputs (results/figures/):
  fig_gx_ic_bc_drain.png   3D cutaway, drainage t=0
  fig_gx_ic_bc_imbibe.png  3D cutaway, imbibition start state
  fig_gx_ic_bc.png         2x2 composite: [3D render | annotated x-z slice]

Run:  "C:/Users/yangc/anaconda3/envs/lbm/python.exe" graphite_ic_bc_figs.py
"""
import os

import numpy as np

from viz3dlib.style_env import STYLE, check_env

GEO = 'geo_graphite_228b14.npz'
TAG = 'gx3c_postaudit'
FRAME = f'results_pcs_cg3d/{TAG}/frames/drain_d0.0740_0150000.npz'
FSOLID = f'results_pcs_cg3d/{TAG}/frames/f_solid.npz'
OUTDIR = 'results/figures'

WT, RT = 3, 8          # protocol wall_t / res_thick (OpenSystem defaults)
CUT = ('y', 0.5, 'hi')  # cut axis / fraction / keep half whose cut face
#                        faces the iso camera (camera sits at -y; keep='hi'
#                        exposes the y=100 cut plane toward it)


# ------------------------------------------------------------------ data
def build_fields():
    """(psi_drain_t0, psi_imbibe_start, solid_full) + QA prints/asserts."""
    dat = np.load(GEO)
    solid_full = dat['solid'].astype(np.int8)
    nx, ny, nz = solid_full.shape
    assert (nx, ny, nz) == (228, 200, 200), solid_full.shape
    x_in, x_out = WT + RT, nx - WT - RT          # 11, 217
    pore_full = solid_full == 0

    # --- psi0: verbatim mirror of cg3d/protocol.py:41-43 ---
    psi0 = np.where(solid_full == 0, -1.0, 0.0).astype(np.float32)
    psi0[WT:x_in + 1, :, :] = np.where(
        pore_full[WT:x_in + 1, :, :], 1.0, 0.0).astype(np.float32)

    dom = slice(x_in + 1, x_out)                 # [12, 217)
    assert psi0[dom][pore_full[dom]].min() == -1.0, 't=0 domain must be all blue'
    assert psi0[WT:x_in + 1][pore_full[WT:x_in + 1]].min() == 1.0, \
        't=0 inlet reservoir+membrane must be all gas'

    # --- imbibition start state = drain-end frame, protocol slabs reattached
    fr = np.load(FRAME)
    fsol = np.load(FSOLID)['solid'].astype(np.int8)
    assert np.array_equal(fsol, solid_full[dom]), 'frame solid != geo solid in dom'
    psi_q = fr['psi_q'].astype(np.float32) / 100.0
    assert psi_q.shape == (x_out - x_in - 1, ny, nz), psi_q.shape
    psi_imb = psi0.copy()                        # [3,12)=+1 gas source (pinned),
    psi_imb[dom] = psi_q                         # x=217 mem plane & res_out stay -1

    pore_dom = pore_full[dom]
    pore_cells = float(pore_dom.sum())
    red = np.where(pore_dom, (psi_q + 1.0) / 2.0, 0.0)
    s_nw_cont = float(red.sum() / pore_cells)
    s_nw_bin = float(((psi_q > 0.0) & pore_dom).sum() / pore_cells)
    s_frame = float(fr['s_nw'])
    assert abs(s_nw_cont - s_frame) < 0.01, (s_nw_cont, s_frame)
    print(f'QA imbibe-start frame: S_nw continuous {s_nw_cont:.4f} '
          f'(frame field {s_frame:.4f}, binary {s_nw_bin:.4f}; '
          f'report ladder tail-mean 0.532)')
    print(f'QA geo: pore fraction in graphite slab [14,214) = '
          f'{pore_full[14:214].mean():.4f}')
    return psi0, psi_imb, solid_full


# ------------------------------------------------------------------ 3D
def render_3d(psi_full, solid_full, out_png, title):
    """Full-domain cutaway: gas opaque, electrolyte glass, solid ghost,
    membrane planes + reservoir labels + flow markers (English: vtk's
    offscreen font has no CJK glyphs)."""
    from viz3dlib.plotting import (_bounds, _crop3, add_domain_box, add_fluid,
                                   add_flow_markers, add_scale_bar, new_plotter,
                                   save, set_iso_camera, surface)
    style = STYLE['report']
    cut_axis, cutaway, keep = CUT
    psi, origin = _crop3(psi_full, cut_axis, cutaway, keep)
    solid, _ = _crop3(solid_full, cut_axis, cutaway, keep)
    bounds = _bounds(origin, psi.shape)
    pore = solid == 0
    nx, ny, nz = psi_full.shape

    pl = new_plotter(style)
    ghost = surface(solid.astype(np.float32), 0.5, spacing=(1, 1, 1),
                    origin=origin, decimate=0.5)
    pl.add_mesh(ghost, color=style['ghost'][0], opacity=0.12, smooth_shading=False,
                lighting=True)
    nw = surface(psi, 0.0, pore=pore, mask_value=-1.0, origin=origin, decimate=0.5)
    wet = surface(psi, 0.0, pore=pore, mask_value=+1.0, origin=origin, decimate=0.5)
    add_fluid(pl, nw, style['nw'], style)                    # gas: opaque amber
    add_fluid(pl, wet, style['wet'], style, opacity=style['glass'])  # liquid: glass

    # semi-permeable membrane planes (green = neither phase colour)
    import pyvista as pv
    x_in, x_out = WT + RT, nx - WT - RT
    for xm, lab, lp in ((x_in, 'membrane x=11: gas only',
                         (x_in, ny * 0.52, nz * 1.06)),
                        (x_out, 'membrane x=217: liquid only',
                         (x_out, ny * 0.62, nz * 1.10))):
        pl.add_mesh(pv.Plane(center=(xm, ny / 2 - 0.5, nz / 2 - 0.5),
                             direction=(1, 0, 0), i_size=ny - 1, j_size=nz - 1),
                    color='#009E73', opacity=0.30, lighting=False)
        pl.add_point_labels([lp], [lab], font_size=13, text_color='#00694d',
                            shape='rounded_rect', shape_color='white',
                            shape_opacity=0.85, always_visible=True,
                            show_points=False)
    # reservoir pins (rho/psi targets from OpenSystem.set_ladder)
    for p, lab in (((WT + x_in) / 2, 'inlet reservoir\nrho=1+d/2, psi=+1 (gas)'),
                   ((x_out + 1 + nx - WT) / 2,
                    'outlet reservoir\nrho=1-d/2, psi=-1 (liquid)')):
        pl.add_point_labels([(p, -ny * 0.10, nz * 0.55)], [lab], font_size=13,
                            text_color=style['text'], shape='rounded_rect',
                            shape_color='white', shape_opacity=0.85,
                            always_visible=True, show_points=False)
    pl.add_point_labels([(nx * 0.55, -ny * 0.10, nz * 0.10)],
                        ['walls x<3, x>=225: bounce-back;  y/z: periodic'],
                        font_size=12, text_color='#595959', shape=None,
                        shape_opacity=0.0, always_visible=True, show_points=False)

    add_domain_box(pl, bounds, style, label=title)
    set_iso_camera(pl)
    add_scale_bar(pl, 50, style)
    add_flow_markers(pl, style)
    return save(pl, out_png, style)


# ------------------------------------------------------------------ 2D
def _phase_rgb(psi_xz, solid_xz, style):
    """Flat phase colours for the slice strips (same palette as the 3D)."""
    img = np.ones(psi_xz.shape + (3,), np.float32)
    hex2rgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    pore = solid_xz == 0
    img[pore & (psi_xz < 0)] = hex2rgb(style['wet'])
    img[pore & (psi_xz >= 0)] = hex2rgb(style['nw'])
    img[~pore] = hex2rgb(style['solid'])
    return img


WIDE = [(0, 3, 'wall (BB)'), (3, 11, 'res_in\n$\\rho$=1+$\\delta$/2, $\\psi$=+1'),
        (14, 214, 'graphite 200 lu'),
        (218, 225, 'res_out\n$\\rho$=1-$\\delta$/2, $\\psi$=-1'),
        (225, 228, 'wall (BB)')]
NARROW = [(11, 14, 'mem_b: gas only\n+ buf 2 lu'),
          (214, 218, 'buf 3 lu +\nmem_r: liquid only')]
YLO, YHI = -10.0, 216.0          # axes range: image 0..200, label band above


def draw_slice(ax, psi_full, solid_full, style, with_labels):
    ny = psi_full.shape[1]
    sl, so = psi_full[:, ny // 2, :], solid_full[:, ny // 2, :]
    ax.imshow(_phase_rgb(sl, so, style).transpose(1, 0, 2), origin='lower',
              interpolation='nearest', aspect='equal', extent=(0, 228, 0, 200))
    ymin, ymax = (0 - YLO) / (YHI - YLO), (200 - YLO) / (YHI - YLO)
    for xb in (3, 11, 12, 14, 214, 217, 218, 225):
        ax.axvline(xb, ymin=ymin, ymax=ymax, color='0.25', ls='--', lw=0.6)
    if with_labels:
        for x0, x1, lab in WIDE:
            ax.text((x0 + x1) / 2, 203, lab, rotation=90, ha='center',
                    va='bottom', fontsize=6.8, color='0.15')
        for x0, x1, lab in NARROW:
            ax.plot([x0, x1, ], [201.5, 201.5], color='0.25', lw=0.8)
            for xe in (x0, x1):
                ax.plot([xe, xe], [200.5, 201.5], color='0.25', lw=0.8)
            ax.text((x0 + x1) / 2, 203.5, lab, rotation=0, ha='center',
                    va='bottom', fontsize=6.3, color='0.15')
    ax.text(228, 209, 'y/z periodic', fontsize=7.5, color='0.35', ha='right')
    ax.text(2, -7, 'inlet $\\rightarrow$', fontsize=8, color='0.2')
    ax.text(226, -7, '$\\rightarrow$ outlet', fontsize=8, color='0.2',
            ha='right')
    ax.set_xlim(0, 228)
    ax.set_ylim(YLO, YHI)
    ax.set_xticks([]), ax.set_yticks([])


def composite(png_a, png_b, psi0, psi_imb, solid_full, out_png):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Patch
    from PIL import Image
    font_manager.fontManager.addfont(
        r'C:\Windows\Fonts\msyh.ttc') if os.path.exists(
        r'C:\Windows\Fonts\msyh.ttc') else None
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    style = STYLE['report']

    fig, axes = plt.subplots(2, 2, figsize=(15.5, 11.6), constrained_layout=True,
                             gridspec_kw=dict(width_ratios=(1.12, 1.0)))
    rows = [
        (png_a, psi0,
         'Drainage 初始时刻 t=0：pore 全域 electrolyte（$\\psi$=-1），'
         '仅入口 reservoir+膜预置 gas（$\\psi$=+1）；$\\delta$ 阶梯上调 0.03$\\to$0.074'),
        (png_b, psi_imb,
         'Imbibition 初始时刻 = drainage 终态（$\\delta$=0.074, S_nw$\\approx$0.53, '
         'max-steps 口径）；$\\delta$ 阶梯下调 0.055$\\to$0，electrolyte 复侵'),
    ]
    for r, (png, psi, ttl) in enumerate(rows):
        im = Image.open(png)
        axes[r, 0].imshow(im)
        axes[r, 0].set_title(ttl, fontsize=11.5, loc='left', fontweight='bold')
        axes[r, 0].set_xticks([]), axes[r, 0].set_yticks([])
        draw_slice(axes[r, 1], psi, solid_full, style, with_labels=(r == 0))
        axes[r, 1].set_title('x-z mid-y slice（全域 0..228，'
                             '竖直虚线 = BC 分带）', fontsize=10, loc='left')
    handles = [Patch(facecolor=style['wet'], label='electrolyte (wetting, $\\psi$<0)'),
               Patch(facecolor=style['nw'], label='gas (non-wetting, $\\psi$$\\geq$0)'),
               Patch(facecolor=style['solid'], label='graphite + walls (solid)'),
               Patch(facecolor='#009E73', label='semi-permeable membrane (3D)')]
    fig.legend(handles=handles, loc='upper center', ncol=4, fontsize=10,
               frameon=False, bbox_to_anchor=(0.5, 1.045))
    fig.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  -> {out_png} (composite)')


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    check_env()
    os.makedirs(OUTDIR, exist_ok=True)
    psi0, psi_imb, solid = build_fields()

    png_a = os.path.join(OUTDIR, 'fig_gx_ic_bc_drain.png')
    png_b = os.path.join(OUTDIR, 'fig_gx_ic_bc_imbibe.png')
    render_3d(psi0, solid, png_a,
              'DRAINAGE t=0 (IC): pores full electrolyte; gas preset at inlet '
              'reservoir | BC: open system, delta ladder up')
    render_3d(psi_imb, solid, png_b,
              'IMBIBITION start (= drainage end, d=0.074, S_nw~0.53) | BC: same '
              'open system, delta ladder down to 0')
    composite(png_a, png_b, psi0, psi_imb, solid,
              os.path.join(OUTDIR, 'fig_gx_ic_bc.png'))
    print('done.')


if __name__ == '__main__':
    main()
