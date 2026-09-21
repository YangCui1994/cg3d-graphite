"""cg3d.ic_figs — deterministic initial-condition QA figures for the
direct-imbibition setup (CG3D-IMB-001-R1, task §6).

Pure NumPy + matplotlib (no Taichi, no solver stepping).  All plotted
data come from cg3d.protocol.build_layout — the SAME authoritative
layout/IC builder the solver path uses (OpenSystem calls it) — so the
figures cannot drift from the implementation.

Outputs per prewet_layers value N:
  initial_state_profile_prewet_<N>.png   x-plane phase fractions
                                          (liquid/gas pore, solid) with
                                          zone markers (visualization A)
  initial_state_slice_prewet_<N>.png     central x-z slice, solid/
                                          liquid/gas distinguished,
                                          zone labels (visualization B)
plus one:
  initial_state_compare.png              the two cases side by side
                                          (visualization C)

These are QA artifacts (review evidence), not publication figures.

Run from repo root:
  python -m cg3d.ic_figs --geo geo_graphite_228b14.npz --prewet 2 6 \
      --out .agent/evidence/CG3D-IMB-001/figures

The prewet values are QA EXAMPLES only — no value is physically
validated.
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

from .protocol import build_layout, resolve_real_bounds  # noqa: E402


def phase_fractions(lay):
    """Per-x-plane cell fractions (liquid pore / gas pore / solid) from
    a build_layout dict — the exact arrays the profile figure plots.

    Classification: solid = walled solid map; liquid/gas = pore cells by
    the sign of psi0.  Returns (liq, gas, sol), each length nx summing
    to ~1 per plane."""
    solid = lay['solid'] != 0
    liq = ((lay['psi0'] < 0.0) & ~solid).mean(axis=(1, 2))
    gas = ((lay['psi0'] > 0.0) & ~solid).mean(axis=(1, 2))
    sol = solid.mean(axis=(1, 2))
    return liq, gas, sol


def _zone_lines(ax, lay, prewet, nx, top=None):
    """Vertical markers at the layout's meaningful x positions."""
    x_in, x_out = lay['dom'].start - 1, lay['dom'].stop
    wt = 3
    lo, hi = lay['x_real_lo'], lay['x_real_hi']
    kw = dict(color='0.35', lw=0.8, ls='--')
    for x, txt in ((x_in, 'inlet mem'), (x_out, 'outlet mem')):
        ax.axvline(x, **kw)
        ax.text(x, (top if top is not None else 1.02), f' {txt}',
                rotation=90, va='top', ha='left', fontsize=6, color='0.35')
    ax.axvspan(wt, x_in, color='tab:blue', alpha=0.06)
    ax.axvspan(x_out + 1, nx - wt, color='tab:red', alpha=0.06)
    ax.axvspan(lo, lo + prewet, color='tab:blue', alpha=0.18)
    ax.axvline(lo, color='tab:blue', lw=0.8)
    ax.axvline(hi, color='tab:blue', lw=0.8, ls=':')
    ax.text(lo + 0.5, 0.02, f'pre-wet {prewet} lu', rotation=90,
            va='bottom', ha='left', fontsize=6, color='tab:blue')


def profile_figure(lay, prewet, path):
    """Visualization A: x-plane liquid/gas/solid fractions."""
    nx = lay['shape'][0]
    x_in = lay['dom'].start - 1
    x_out = lay['dom'].stop
    wt = 3
    lo, hi = lay['x_real_lo'], lay['x_real_hi']
    liq, gas, sol = phase_fractions(lay)
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    xs = np.arange(nx)
    ax.fill_between(xs, 0, liq, color='tab:blue', alpha=0.55,
                    label='liquid pore')
    ax.fill_between(xs, liq, liq + gas, color='tab:red', alpha=0.45,
                    label='gas pore')
    ax.plot(xs, liq + gas + sol, color='0.2', lw=0.6, label='total (1)')
    _zone_lines(ax, lay, prewet, nx)
    for x, txt, y in ((wt + (x_in - wt) / 2, 'liq reservoir', 0.5),
                      ((x_in + 1 + lo) / 2, 'left buffer', 0.5),
                      ((lo + hi) / 2, 'REAL DOMAIN (bulk gas)', 0.9),
                      ((hi + x_out) / 2, 'right buffer', 0.5),
                      ((x_out + 1 + nx - wt) / 2, 'gas reservoir', 0.5)):
        ax.text(x, y, txt, ha='center', fontsize=6.5, color='0.25')
    ax.set_xlabel('x [lu]')
    ax.set_ylabel('x-plane cell fraction')
    ax.set_xlim(0, nx)
    ax.set_ylim(0, 1.08)
    ax.set_title(f'direct-imbibition IC x-profile  '
                 f'prewet_layers={prewet}  (real domain '
                 f'x=[{lo},{hi}), explicit real_x)')
    ax.legend(loc='center right', fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _classify(lay, j):
    """Central x-z slice at y=j: 0 solid / 1 liquid / 2 gas."""
    solid = lay['solid'][:, j, :] != 0
    slc = np.zeros(solid.shape, np.uint8)
    psi = lay['psi0'][:, j, :]
    slc[~solid & (psi < 0)] = 1
    slc[~solid & (psi > 0)] = 2
    return slc


def _slice_panel(ax, lay, prewet, j=None, title=''):
    nx = lay['shape'][0]
    j = lay['shape'][1] // 2 if j is None else j
    slc = _classify(lay, j)
    from matplotlib.colors import ListedColormap
    ax.imshow(slc.T, origin='lower', aspect='auto', interpolation='nearest',
              cmap=ListedColormap(['0.55', 'tab:blue', 'tab:red']),
              vmin=0, vmax=2, extent=[0, nx, 0, slc.shape[1]])
    x_in = lay['dom'].start - 1
    x_out = lay['dom'].stop
    lo, hi = lay['x_real_lo'], lay['x_real_hi']
    for x, txt in ((x_in, 'in mem'), (x_out, 'out mem')):
        ax.axvline(x, color='k', lw=0.8, ls='--')
        ax.text(x + 0.5, slc.shape[1] * 0.98, txt, rotation=90,
                va='top', fontsize=6)
    ax.axvspan(lo, lo + prewet, color='k', alpha=0.10)
    ax.axvline(lo, color='k', lw=0.7)
    ax.axvline(hi, color='k', lw=0.7, ls=':')
    for x, txt in ((7, 'liq res'), ((x_in + 1 + lo) / 2, 'buf'),
                   ((lo + hi) / 2, 'REAL: pre-wet | gas bulk'),
                   ((hi + x_out) / 2, 'buf'), (x_out + 4, 'gas res')):
        ax.text(x, -0.06 * slc.shape[1], txt, ha='center', va='top',
                fontsize=6.5, color='0.2',
                transform=ax.transData)
    ax.set_title(title, fontsize=8)
    ax.set_xlabel('x [lu]  (flow direction →)', fontsize=7)


def slice_figure(lay, prewet, path, j=None):
    """Visualization B: central x-z slice (x horizontal, flow direction)."""
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    _slice_panel(ax, lay, prewet, j,
                 f'direct-imbibition IC central x-z slice  '
                 f'prewet_layers={prewet}  '
                 f'(grey solid / blue liquid / red gas)')
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def compare_figure(lays, prewets, path, j=None):
    """Visualization C: the pre-wet cases side by side — only the
    intended liquid penetration depth changes."""
    fig, axes = plt.subplots(len(lays), 1, figsize=(7.0, 2.3 * len(lays)),
                             sharex=True)
    if len(lays) == 1:
        axes = [axes]
    for ax, lay, n in zip(axes, lays, prewets):
        _slice_panel(ax, lay, n, j,
                     f'prewet_layers={n}')
    fig.suptitle('direct-imbibition IC: prewet_layers comparison '
                 '(QA example values, not physically validated)',
                 fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def make_figures(geo_path, prewet_values, out_dir, real_bounds=None):
    """Build layouts with the SAME builder as the solver and write the
    QA figures.  Returns the list of written paths."""
    dat = np.load(geo_path)
    rb = resolve_real_bounds(dat, real_bounds)
    solid = dat['solid'].astype(np.int8)
    os.makedirs(out_dir, exist_ok=True)
    lays, paths = [], []
    for n in prewet_values:
        lay = build_layout(solid, orientation='imbibition',
                           prewet_layers=n, real_bounds=rb)
        lays.append(lay)
        paths.append(os.path.join(
            out_dir, f'initial_state_profile_prewet_{n}.png'))
        profile_figure(lay, n, paths[-1])
        paths.append(os.path.join(
            out_dir, f'initial_state_slice_prewet_{n}.png'))
        slice_figure(lay, n, paths[-1])
    paths.append(os.path.join(out_dir, 'initial_state_compare.png'))
    compare_figure(lays, list(prewet_values), paths[-1])
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--geo', required=True)
    ap.add_argument('--prewet', type=int, nargs='+', required=True,
                    help='prewet_layers QA values (examples only, not '
                         'physically validated)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--real-bounds', type=int, nargs=2, default=None,
                    metavar=('LO', 'HI'))
    args = ap.parse_args()
    for p in make_figures(args.geo, args.prewet, args.out,
                          real_bounds=args.real_bounds):
        print('wrote', p)


if __name__ == '__main__':
    main()
