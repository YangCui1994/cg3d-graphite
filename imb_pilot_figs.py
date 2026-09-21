"""CG3D-IMB-002 pilot comparison figures (2026-09-21).

Deterministic post-processing ONLY: reads the saved outputs of
run_imbibition_cg3d.py (frames psi_q int8 + f_solid over the
membrane-interior dom, psi_ic.npz at t=0, final.npz, report.json),
uses the EXPLICIT real-domain bounds from the geometry npz
(resolve_real_bounds — never solid occupancy), and writes the small
comparison figures required by the pilot task.  No Taichi, no solver
physics, no source-data mutation.

Metric basis (documented for every figure):
  - frames store psi quantised to psi_q = rint(psi*100) in int8
    (|psi_q| <= 127), so the recovered psi is exact to +-0.005;
  - binary gas fraction     = mean(psi > 0)  over real-region PORE cells;
  - continuous gas fraction = mean((psi+1)/2) over the same cells;
  - t = 0 comes from psi_ic.npz (full float32 psi);
  - the t = 10000 endpoint additionally cross-checks against the
    driver's own report.json gas_saturation_* (computed from the
    unquantised field).

Run from repo root (after the three pilot cases):
  python imb_pilot_figs.py --geo geo_graphite_228b14.npz \
      --run n2:results_imb_cg3d/imb_pilot_n2 \
      --run n4:results_imb_cg3d/imb_pilot_n4 \
      --run n6:results_imb_cg3d/imb_pilot_n6 \
      --steps 0 1000 5000 10000 \
      --out .agent/evidence/CG3D-IMB-002/figures

Outputs: gas_saturation_real_vs_step.png, imbibition_slices_compare.png,
final_phase_profile_compare.png plus a per-run metrics audit on stdout.
10,000 steps is a bounded pilot horizon, NOT a convergence criterion;
remaining gas is remaining gas, NOT trapped gas.
"""
import argparse
import glob
import json
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                  # noqa: E402
from matplotlib.colors import ListedColormap    # noqa: E402
from matplotlib.patches import FancyArrow       # noqa: E402
import numpy as np                               # noqa: E402

from cg3d.protocol import resolve_real_bounds   # noqa: E402

C_SOLID, C_LIQ, C_GAS = '0.55', 'tab:blue', 'tab:red'


def load_run(run_dir, geo, wall_t=3, res_thick=8):
    """Frame stack for one pilot run: dict(it -> psi float32 over dom),
    solid map over dom, dom-local real bounds, report dict."""
    dat = np.load(geo)
    lo, hi = resolve_real_bounds(dat)               # explicit, [14,214)
    dom_start = wall_t + res_thick + 1              # 12, driver defaults
    lo_l, hi_l = lo - dom_start, hi - dom_start     # dom-local indices
    sol = np.load(os.path.join(run_dir, 'frames', 'f_solid.npz'))['solid']
    assert sol.shape[0] > hi_l and lo_l >= 0, 'real bounds outside dom'
    frames = {}
    ic = os.path.join(run_dir, 'psi_ic.npz')
    if os.path.exists(ic):
        frames[0] = np.load(ic)['psi'].astype(np.float32)
    for p in sorted(glob.glob(os.path.join(run_dir, 'frames',
                                           'imb_d*_*.npz'))):
        m = re.search(r'_(\d{7})\.npz$', p)
        if m:
            q = np.load(p)['psi_q']
            frames[int(m.group(1))] = q.astype(np.float32) / 100.0
    with open(os.path.join(run_dir, 'report.json'),
              encoding='utf-8') as f:
        rep = json.load(f)
    return dict(dir=run_dir, frames=frames, solid=sol,
                lo=lo, hi=hi, lo_l=lo_l, hi_l=hi_l, report=rep)


def gas_sat_real(run, psi):
    """(binary, continuous) gas fraction over the real-region pore cells."""
    pore = run['solid'][run['lo_l']:run['hi_l']] == 0
    ps = psi[run['lo_l']:run['hi_l']]
    n = float(pore.sum())
    return (float(((ps > 0.0) & pore).sum()) / n,
            float(np.where(pore, (ps + 1.0) / 2.0, 0.0).sum()) / n)


def audit(run, name):
    """Finiteness / endpoint audit from report + final state."""
    rep = run['report']
    row = rep['ladder'][-1]
    floats = [row.get(k) for k in
              ('s_nw', 's_nw_binary', 'umax_last', 'rho_in_mean',
               'rho_out_mean', 'u_rms')]
    floats += [rep.get(k) for k in
               ('gas_saturation_real', 'gas_saturation_dom')]
    fin = all(v is not None and np.isfinite(v) for v in floats)
    finz = np.load(os.path.join(run['dir'], 'final.npz'))['psi']
    max_it = max(run['frames'])
    return dict(name=name, steps=row['steps'], reason=row['reason'],
                finite_report=bool(fin),
                finite_final_psi=bool(np.isfinite(finz).all()),
                umax_last=row.get('umax_last'),
                gas_sat_real=rep['gas_saturation_real'],
                gas_sat_real_cont=rep['gas_saturation_real_continuous'],
                gas_sat_dom=rep['gas_saturation_dom'],
                max_frame_it=max_it, wall_s=row.get('wall_s'))


def fig_time_history(runs, out):
    """B: binary (+dashed continuous) real-region gas saturation vs step."""
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for name, r in runs.items():
        its = sorted(r['frames'])
        b, c = zip(*(gas_sat_real(r, r['frames'][i]) for i in its))
        ax.plot(its, b, '-o', ms=3, label=f'N={name[1]} (binary)')
        ax.plot(its, c, '--', lw=1, alpha=0.7,
                label=f'N={name[1]} (continuous)')
    ax.set_xlabel('simulation step')
    ax.set_ylabel('gas saturation, REAL region [14,214)')
    ax.set_title('Direct-imbibition pilot: early-time real-electrode gas '
                 'saturation\n(prewet 2/4/6 are QA values; 10,000 steps is '
                 'a pilot horizon, not convergence;\nremaining gas, NOT '
                 'trapped gas)')
    ax.legend(fontsize=7, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def _slice_ax(ax, run, psi, step, label_end):
    """Central x-z slice classified solid/liquid/gas with zone marks.
    Classification codes: 0 solid / 1 liquid (psi<=0) / 2 gas (psi>0),
    rendered with ListedColormap + vmin=0/vmax=2 (bin edges 0, 2/3, 4/3
    — code 1 lands in the blue bin, 2 in the red bin)."""
    solid = run['solid'] != 0
    j = solid.shape[1] // 2
    slc = np.zeros(solid[:, j, :].shape, np.uint8)     # 0 solid
    ps = psi[:, j, :]
    slc[~solid[:, j, :] & (ps <= 0)] = 1               # liquid
    slc[~solid[:, j, :] & (ps > 0)] = 2                # gas
    nx, nz = slc.shape
    ax.imshow(slc.T, origin='lower', aspect='auto', interpolation='nearest',
              cmap=ListedColormap([C_SOLID, C_LIQ, C_GAS]),
              vmin=0, vmax=2, extent=[0, nx, 0, nz])
    for x, ls in ((run['lo_l'], '-'), (run['hi_l'], ':')):
        ax.axvline(x, color='k', lw=0.9, ls=ls)
    lab = f'step {step}' + (f' (last, ended @{label_end})'
                            if step != label_end else '')
    ax.set_title(lab, fontsize=8)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.annotate('+x', xy=(nx * 0.985, nz * 0.06), fontsize=8,
                ha='right', color='k')
    ax.add_patch(FancyArrow(nx * 0.70, -nz * 0.10, nx * 0.18, 0,
                            width=nz * 0.025, head_width=nz * 0.09,
                            color='k', clip_on=False))


def fig_slices(runs, steps, out):
    """C: same-step central-slice grid; rows = N, cols = steps."""
    order = sorted(runs)
    avail_steps = [s if any(s in runs[n]['frames'] for n in order)
                   else max(runs[order[0]]['frames']) for s in steps]
    fig, axes = plt.subplots(len(order), len(steps),
                             figsize=(2.5 * len(steps), 2.0 * len(order)))
    for r_i, name in enumerate(order):
        run = runs[name]
        last = max(run['frames'])
        for c_i, s in enumerate(steps):
            ax = axes[r_i, c_i]
            use = s if s in run['frames'] else last
            _slice_ax(ax, run, run['frames'][use], s, use)
            if c_i == 0:
                ax.set_ylabel(f'N={name[1]}', fontsize=9)
    fig.suptitle('Direct-imbibition pilot: same-step central x-z slices '
                 '(grey solid / blue liquid / red gas;\nblack lines = '
                 'real-domain bounds [14,214); arrow = +x invasion '
                 'direction)', fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=160)
    plt.close(fig)


def fig_final_profiles(runs, out):
    """D: x-plane liquid/gas/solid fractions at the pilot endpoint,
    whole membrane-interior dom (buffers visible)."""
    order = sorted(runs)
    fig, axes = plt.subplots(len(order), 1, figsize=(6.8, 2.3 * len(order)),
                             sharex=True)
    if len(order) == 1:
        axes = [axes]
    for ax, name in zip(axes, order):
        run = runs[name]
        psi = run['frames'][max(run['frames'])]
        solid = run['solid'] != 0
        liq = ((psi < 0) & ~solid).mean(axis=(1, 2))
        gas = ((psi > 0) & ~solid).mean(axis=(1, 2))
        sol = solid.mean(axis=(1, 2))
        xs = np.arange(run['lo'] - run['lo_l'],     # absolute x labels
                       run['lo'] - run['lo_l'] + solid.shape[0])
        ax.fill_between(xs, 0, liq, color=C_LIQ, alpha=0.55,
                        label='liquid pore')
        ax.fill_between(xs, liq, liq + gas, color=C_GAS, alpha=0.45,
                        label='gas pore')
        ax.plot(xs, sol, color='0.2', lw=0.6, label='solid')
        for x, ls in ((run['lo'], '-'), (run['hi'], ':')):
            ax.axvline(x, color='k', lw=0.9, ls=ls)
        for x in (11, 217):
            ax.axvline(x, color='0.5', lw=0.7, ls='--')
        ax.set_ylabel(f'N={name[1]}\nfraction', fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=0.3)
    axes[-1].set_xlabel('absolute x [lu]  (dashed: membranes x=11/217; '
                        'black: real bounds 14/214)')
    axes[0].legend(fontsize=7, loc='center right')
    fig.suptitle('Direct-imbibition pilot endpoint (step '
                 f'{max(runs[order[0]]["frames"])}): x-plane phase profile '
                 '— buffers shown, not hidden', fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=160)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--geo', required=True)
    ap.add_argument('--run', required=True, action='append',
                    help='name:dir, name like n2/n4/n6')
    ap.add_argument('--steps', type=int, nargs='+',
                    default=[0, 1000, 5000, 10000])
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    runs = {}
    for spec in args.run:
        name, d = spec.split(':', 1)
        runs[name] = load_run(d, args.geo)

    os.makedirs(args.out, exist_ok=True)
    for name, r in sorted(runs.items()):
        a = audit(r, name)
        print(json.dumps(a))
    fig_time_history(runs, os.path.join(
        args.out, 'gas_saturation_real_vs_step.png'))
    fig_slices(runs, args.steps, os.path.join(
        args.out, 'imbibition_slices_compare.png'))
    fig_final_profiles(runs, os.path.join(
        args.out, 'final_phase_profile_compare.png'))
    print('wrote 3 comparison figures to', args.out)


if __name__ == '__main__':
    main()
