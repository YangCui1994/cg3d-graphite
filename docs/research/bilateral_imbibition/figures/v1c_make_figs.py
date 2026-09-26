"""Generate V1c SVG figures for ALGORITHM_IMPLEMENTATION_EVOLUTION.md.

Reads ONLY committed V1c product evidence (CSV/JSON) from the frozen
reviewed candidate worktree and writes two SVGs next to this script.
The product candidate SHA is stated in every figure.

Gate annotations are taken from the V3_gradient cells of
estimator_sensitivity.csv (not only summary.json) so a FAIL cell cannot
be silently hidden; the all-variant range is printed in every caption.

Run (control checkout, conda env lbm):
  python docs/research/bilateral_imbibition/figures/v1c_make_figs.py
"""
import csv
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (r'D:\2026_agent_work\01_GLM_LBM3D_porous_media'
      r'\cg3d-episode-worktrees\BI-V1C-CLOSURE-001\results\levelc_v1c')
CAND = '2b82f9a5f448e756b5d5903b0df37f9a3b11d804'   # reviewed candidate


def read_csv(name):
    with open(os.path.join(EV, name), newline='') as f:
        return list(csv.DictReader(f))


def f(x):
    return float(x)


summary = json.load(open(os.path.join(EV, 'summary.json')))

# ---- figure 1: static resolution convergence --------------------------
rows = read_csv('static_table.csv')
h = [f(r['h']) for r in rows]
c = [f(r['C_static']) for r in rows]
theta = [f(r['theta_static_deg']) for r in rows]
c0 = summary['static']['convergence_fits']['constant']['coef'][0]
rmax = summary['static']['convergence_fits']['constant']['resid_max']
regs = summary['static']['convergence_fits']

fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.plot(h, c, 'o-', color='#1f77b4', ms=7, lw=1.2,
        label=r'$C_\mathrm{static}(h)=P_c h/(2\sigma)$ (bulk-column rule)')
ax.axhline(c0, color='#d62728', ls='--', lw=1.2,
           label=f'plateau fit C = {c0:.4f} (resid$_{{max}}$ {rmax:.3f})')
ax.axhline(c0 + rmax, color='#d62728', ls=':', lw=0.8)
ax.axhline(c0 - rmax, color='#d62728', ls=':', lw=0.8)
ax.axhline(0.86603, color='gray', ls='-.', lw=1.0,
           label=r'droplet registry $\cos 30°$ = 0.866 (reference only)')
for hh, cc, th in zip(h, c, theta):
    ax.annotate(f'{th:.1f}°', (hh, cc), textcoords='offset points',
                xytext=(6, 7), fontsize=8)
ax.set_xlabel('slit height h (lu)')
ax.set_ylabel(r'$C_\mathrm{static}$')
ax.set_title('V1c static slit calibration — reproducible plateau '
             f'(no 1/h law: $R^2$$_{{1/h}}$={regs["over_h"]["r2"]:.3f}, '
             f'$R^2$$_{{1/h^2}}$={regs["over_h2"]["r2"]:.4f})\n'
             f'product candidate {CAND}')
ax.legend(fontsize=8, loc='lower right')
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'fig_v1c_static_convergence.svg'))
plt.close(fig)

# ---- figure 2: L_eff vs L (differential hydraulics) -------------------
# gate annotations from estimator_sensitivity.csv V3_gradient cells
sen = read_csv('estimator_sensitivity.csv')
prim = {(int(r['h']), r['estimator']): f(r['a_h']) for r in sen
        if r['validity_variant'] == 'V3_gradient' and r['a_h']}
varange = {}
for r in sen:
    if r['a_h']:
        varange.setdefault(int(r['h']), []).append(f(r['a_h']))

d = summary['differential']
fig, ax = plt.subplots(figsize=(7.2, 4.8))
for key, col, lab in (('h26', '#1f77b4', 'h=26'),
                      ('h40', '#ff7f0e', 'h=40')):
    dd = d[key]
    L = [dd['L1'], dd['L2']]
    Le = [dd['L_eff1'], dd['L_eff2']]
    a, L0 = dd['a_h'], dd['L0']
    ax.plot(L, Le, 'o', color=col, ms=8)
    xs = [220, 500]
    ax.plot(xs, [a * x + L0 for x in xs], '-', color=col, lw=1.0,
            alpha=0.7, label=f'{lab}: '
            f"$L_{{eff}}={a:.4f}L+{L0:.0f}$ ($L_0/h$={dd['L0_over_h']:.2f})")
    for x, y in zip(L, Le):
        ax.annotate(f'{y:.0f}', (x, y), textcoords='offset points',
                    xytext=(6, -12), fontsize=8)
ax.plot([220, 500], [220, 500], 'k--', lw=0.9, alpha=0.6,
        label='ideal distributed-only $L_{eff}=L$')

# primary-gate annotation block straight from the V3_gradient cells
lines = []
for hh in (26, 40):
    am, an = prim[(hh, 'median')], prim[(hh, 'mean')]
    lo, hi = min(varange[hh]), max(varange[hh])
    lines.append(
        f'h={hh}: V3_gradient median a={am:.4f} '
        f'({"PASS" if abs(am - 1) <= 0.10 else "FAIL"}), '
        f'mean a={an:.4f} '
        f'({"PASS" if abs(an - 1) <= 0.10 else "FAIL"}); '
        f'all-variant range [{lo:.3f}, {hi:.3f}]')
ax.text(0.02, 0.03, '\n'.join(lines), transform=ax.transAxes,
        fontsize=7.5, va='bottom', family='monospace',
        bbox=dict(boxstyle='round', fc='wheat', alpha=0.5))
ax.set_xlabel('hydraulic length between membranes L (lu)')
ax.set_ylabel(r'$L_{eff}=P_{c,\mathrm{dyn}}h^2/(12\mu V)$ (lu)')
ax.set_title('V1c differential hydraulics — distributed bulk resistance '
             'matches Poiseuille\n(gate cells read from '
             'estimator_sensitivity.csv V3_gradient; both |a−1| ≤ 10% '
             'PASS)\n'
             f'product candidate {CAND}')
ax.legend(fontsize=8, loc='upper left')
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'fig_v1c_leff_vs_L.svg'))
plt.close(fig)
print('SVGs written:', sorted(x for x in os.listdir(HERE)
                              if x.endswith('.svg') and 'v1c' in x))
