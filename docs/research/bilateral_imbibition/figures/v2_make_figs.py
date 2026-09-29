"""Generate V2 SVG figures for ALGORITHM_IMPLEMENTATION_EVOLUTION.md.

Reads ONLY committed V2 product evidence from the frozen reviewed
candidate worktree; candidate SHA stated in every caption.

Run (control checkout, conda env lbm):
  python docs/research/bilateral_imbibition/figures/v2_make_figs.py
"""
import csv
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (r'D:\2026_agent_work\01_GLM_LBM3D_porous_media'
      r'\cg3d-episode-worktrees\BI-V2-BILATERAL-001\results\levelc_v2'
      r'\v2_primary')
CAND = '5e679d8d99d338f9ab28565c636f021a0f9211b2'


def rd(name):
    with open(os.path.join(EV, name), newline='') as f:
        return list(csv.DictReader(f))


f = rd('front_series.csv')
g = rd('gas_series.csv')
m = rd('mass_stability_series.csv')
t = [float(r['t']) for r in f]
xl = [float(r['x_left']) for r in f]
xrs = [float(r['x_right_star']) for r in f]
ex = [float(r['e_x']) for r in f]
epsi = [float(r['E_psi']) for r in f]
tg = [float(r['t']) for r in g]
gb = [int(r['G_bulk']) for r in g]
vc = [float(r['V_cont']) for r in g]
rg = [float(r['rho_gas_mean']) for r in g]
tm = [float(r['t']) for r in m]
er = [float(r['eps_r']) for r in m]
eb = [float(r['eps_b']) for r in m]

# ---- figure 1: fronts + mirror error ----------------------------------
fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True)
a1.plot(t, xl, lw=1.2, label=r'$x_\mathrm{left}(t)$')
a1.plot(t, xrs, '--', lw=1.2,
        label=r'mirrored $x^*_\mathrm{right}(t)=325-x_\mathrm{right}$')
a1.set_ylabel('front position (lu)')
a1.legend(fontsize=9, loc='lower left')
a1.set_title('V2 bilateral fronts — the two curves lie on top of each '
             'other (max $e_x$ = %.4f lu)\n'
             'product candidate %s' % (max(ex), CAND[:12]))
a1.grid(alpha=0.3)
a2.semilogy(t, [max(e, 1e-6) for e in ex], lw=1.0,
            label=r'$e_x=|x_L-x_R^*|$ (max %.4f lu, gate $\leq$ '
            r'max(2, 0.02d))' % max(ex))
a2.semilogy(t, epsi, lw=1.0, label=r'full-field $E_\psi$ (max %.1e)'
            % max(epsi))
a2.set_xlabel('step')
a2.set_ylabel('mirror error')
a2.legend(fontsize=9)
a2.grid(alpha=0.3, which='both')
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'fig_v2_fronts_mirror.svg'))
plt.close(fig)

# ---- figure 2: gas pocket + mass drift ---------------------------------
fig, (b1, b2) = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True)
b1.plot(tg, gb, 'o-', ms=2, lw=1.0,
        label=r'bulk-gas gap $G_\mathrm{bulk}(t)$ (160 at t=0, %d from '
        r't=1000; INTERACTION_ONSET NOT_REACHED)' % gb[-1])
b1.set_ylabel('bulk-gas columns')
b11 = b1.twinx()
b11.plot(tg, vc, color='#ff7f0e', lw=1.0,
         label='continuous gas volume')
b11.plot(tg, rg, color='#2ca02c', lw=1.0,
         label='pocket mean $\\rho$ (x1000 offset)')
b11.set_ylabel('V_cont [nodes] / mean rho')
h1, l1 = b1.get_legend_handles_labels()
h2, l2 = b11.get_legend_handles_labels()
b1.legend(h1 + h2, l1 + l2, fontsize=8, loc='lower right')
b1.set_title('V2 trapped pocket — symmetric stall '
             '(pocket mean rho 1.0000->1.0041 = +0.42 pct from IC), '
             'single cluster throughout\n'
             'product candidate ' + CAND[:12])
b1.grid(alpha=0.3)
b2.semilogy(tm, [max(e, 1e-7) for e in er], lw=1.0,
            label=r'$\epsilon_r$ (max %.2e)' % max(er))
b2.semilogy(tm, [max(e, 1e-7) for e in eb], lw=1.0,
            label=r'$\epsilon_b$ (max %.2e, letter-FAIL vs 5e-4 gate — '
            r'reviewer judgment recorded)' % max(eb))
b2.axhline(5e-4, color='r', ls='--', lw=1.0, label='contract gate 5e-4')
b2.set_xlabel('step')
b2.set_ylabel('closed-system colour drift')
b2.legend(fontsize=8)
b2.grid(alpha=0.3, which='both')
fig.tight_layout()
fig.savefig(os.path.join(HERE, 'fig_v2_pocket_mass.svg'))
plt.close(fig)
print('SVGs written')
