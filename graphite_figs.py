"""Figures for the graphite exploratory arm (PLAN_3d_graphite_exploratory_v1).

Run AFTER the GPU batches finish (reads report.json / checkpoint pngs only):
  python graphite_figs.py --tag-drain gx2_drain200 --tag-ir gx3_ir200

Outputs to ../output_docs/figures_graphite/ (relative to 2phase/):
  fig_gx_pcs.png     Pc-S ladder (+ entry annotation)
  fig_gx_slices.png  checkpoint slice montage with inlet/outlet markers
  fig_gx_ir.png      I-R point + trapped-gas cluster CCDF
"""
import argparse
import glob
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

OUT = '../../../../output_docs/figures_graphite'
RES = 'results_pcs_cg3d'


def fig_pcs(tag):
    import os as _os
    rp = f'{RES}/{tag}/report.json'
    if not _os.path.exists(rp):
        rp = f'{RES}/{tag}/report_partial.json'
    rep = json.load(open(rp))
    lad = rep['ladder']
    # pc_nominal since PR-1 (Plan_20260919_v2 2.1); 'pc' = pre-audit
    # reports (results/baseline/)
    pc = [r.get('pc_nominal', r.get('pc')) for r in lad]
    snw = [r['s_nw'] for r in lad]
    fig, ax = plt.subplots(figsize=(4.8, 3.7))
    ax.plot(pc, snw, 'o-', ms=6, mfc='w', mec='k', lw=1.3)
    for r, x, y in zip(lad, pc, snw):
        ax.annotate(f"{r['reason'][:2]}", (x, y), xytext=(3, 5),
                    textcoords='offset points', fontsize=6, color='0.45')
    # entry: rung where S_nw first jumps by >0.1 over the previous rung
    jump = [i for i in range(1, len(snw)) if snw[i] - snw[i - 1] > 0.1]
    if jump:
        ax.axvline(pc[jump[0]], color='r', ls=':', lw=1)
        ax.annotate('entry', (pc[jump[0]], 0.55), color='r', fontsize=8,
                    rotation=90, va='center', ha='right')
    ax.set_xlabel('Pc_nominal [lu] (= delta/3)')
    ax.set_ylabel('$S_{nw}$')
    ax.set_title(f'Primary drainage, real graphite 200$^3$ ({tag})',
                 fontsize=9)
    plt.tight_layout()
    plt.savefig(f'{OUT}/fig_gx_pcs.png', dpi=150)
    plt.close()
    print('fig_gx_pcs ok')


def fig_slices(tag, picks=None):
    files = sorted(glob.glob(f'{RES}/{tag}/psi_d*.png'))
    if picks:
        groups = {}
        for f in files:
            groups.setdefault(f.split('_')[1], []).append(f)
        files = [sorted(g)[-1] for g in list(groups.values())[:picks]]
    files = files[-4:]
    if not files:
        print('no checkpoint pngs (run with --dump-every next time)')
        return
    ims = [Image.open(f) for f in files]
    w = min(i.width for i in ims)
    ims = [i.resize((w, int(i.height * w / i.width))) for i in ims]
    H = max(i.height for i in ims)
    pad = 34
    canvas = Image.new('RGB', (w * len(ims), H + pad), 'white')
    d = ImageDraw.Draw(canvas)
    for k, im in enumerate(ims):
        canvas.paste(im, (k * w, pad))
        x0 = k * w
        # the driver panel's right subplot (xz@mid-y) has x horizontal
        d.text((x0 + int(w * 0.53), H + 8), 'inlet \u2192', fill='black')
        d.text((x0 + w - 8, H + 8), '\u2192 outlet', fill='black', anchor='ra')
        d.text((x0 + 6, H + 8), os.path.basename(files[k])[:22],
               fill=(100, 100, 100))
    canvas.save(f'{OUT}/fig_gx_slices.png')
    print('fig_gx_slices ok')


def fig_ir(tag):
    rep = json.load(open(f'{RES}/{tag}/report.json'))
    n_drain = len(rep['args']['ds_drain'])
    s_i = rep['ladder'][n_drain - 1]['s_nw']
    s_nr = rep['s_nr']
    sizes = np.array(rep['sizes_top'])
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))
    axes[0].plot([s_i], [s_nr], 'o', ms=9, mfc='w', mec='k')
    axes[0].annotate(f'S_i={s_i:.3f}\nS_nr={s_nr:.3f}', (s_i, s_nr),
                     xytext=(8, 6), textcoords='offset points', fontsize=9)
    axes[0].set_xlabel('$S_i$ (gas after drainage)')
    axes[0].set_ylabel('$S_{nr}$ (trapped gas)')
    axes[0].set_title(f'imbibition residual, n={rep["n_clusters"]} clusters',
                      fontsize=9)
    s = np.sort(sizes)[::-1]
    axes[1].loglog(s, np.arange(1, len(s) + 1) / len(s), 'o-', ms=3, lw=1)
    axes[1].set_xlabel('trapped cluster size [voxels]')
    axes[1].set_ylabel('CCDF')
    axes[1].set_title(f'top cluster {s[0] / sum(sizes) * 100:.1f}% of trapped',
                      fontsize=9)
    plt.tight_layout()
    plt.savefig(f'{OUT}/fig_gx_ir.png', dpi=150)
    plt.close()
    print('fig_gx_ir ok')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag-drain', default='gx2_drain200')
    ap.add_argument('--tag-ir', default='gx3_ir200')
    ap.add_argument('--picks', type=int, default=4)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(f'{RES}/{args.tag_drain}/report.json') or \
       os.path.exists(f'{RES}/{args.tag_drain}/report_partial.json'):
        fig_pcs(args.tag_drain)
        fig_slices(args.tag_drain, picks=args.picks)
    else:
        print('no drain report yet')
    if os.path.exists(f'{RES}/{args.tag_ir}/report.json'):
        fig_ir(args.tag_ir)
    else:
        print('no ir report yet')


if __name__ == '__main__':
    main()
