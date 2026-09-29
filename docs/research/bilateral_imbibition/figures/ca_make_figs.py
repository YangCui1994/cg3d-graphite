"""Generate conservation-audit SVG figures for
ALGORITHM_IMPLEMENTATION_EVOLUTION.md (section: SOLVER Conservation Audit
— BI-CONSERVATION-AUDIT-001).

Reads ONLY committed audit evidence from the frozen candidate worktree;
candidate SHA stated in every caption.

Run (control checkout, conda env lbm):
  python docs/research/bilateral_imbibition/figures/ca_make_figs.py
"""
import csv
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EV = (r'D:\2026_agent_work\01_GLM_LBM3D_porous_media'
      r'\cg3d-episode-worktrees\BI-CONSERVATION-AUDIT-001'
      r'\results\conservation_audit')
CAND = '24b00dbe28d23c12049d05679542301ccc507eac'
OUT = HERE


def rd(tag, name):
    with open(os.path.join(EV, tag, name), newline='') as f:
        return list(csv.DictReader(f))


def rj(path):
    with open(os.path.join(EV, path)) as f:
        return json.load(f)


# ---- figure 1: long-horizon drift + backend overlay --------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))

for tag, ls, lab in [('C1_gpu', '--', 'C1 GPU (interface, no walls)'),
                     ('C3_gpu', '-', 'C3 GPU (interface + walls)'),
                     ('C3_cpu', ':', 'C3 CPU')]:
    rows = rd(tag, 'long_horizon_mass.csv')
    rep = rj(os.path.join(tag, 'case_report.json'))
    M0 = rep['M0']
    t = [float(r['step']) for r in rows]
    mf = [float(r['Mff']) / M0 - 1 for r in rows]
    mc = [(float(r['Mr']) + float(r['Mb'])) / M0 - 1 for r in rows]
    a1.plot(t, mf, ls, lw=1.4, label=lab + r'  $M_f$')
    a1.plot(t, mc, ls, lw=1.0, alpha=0.65, label=lab + r'  $M_c$')
a1.set_xlabel('timestep')
a1.set_ylabel(r'relative mass drift $(M-M_0)/M_0$')
a1.set_title('(a) long-horizon drift: linear leak in two-phase cases')
a1.legend(fontsize=7, loc='upper left', ncol=1)
a1.tick_params(labelsize=8)
a1.grid(alpha=0.3)

rows0 = rd('C0_24_gpu', 'long_horizon_mass.csv')
rows2 = rd('C2_gpu', 'long_horizon_mass.csv')
M0c0 = rj(os.path.join('C0_24_gpu', 'case_report.json'))['M0']
M0c2 = rj(os.path.join('C2_gpu', 'case_report.json'))['M0']
a2.plot([float(r['step']) for r in rows0],
        [float(r['Mff']) / M0c0 - 1 for r in rows0],
        lw=1.2, label=r'C0 GPU $24^3$ (uniform: slope 0, constant'
                      r' $+3.43{\times}10^{-7}$ offset)')
a2.plot([float(r['step']) for r in rows2],
        [float(r['Mff']) / M0c2 - 1 for r in rows2],
        lw=1.2, ls='--', label=r'C2 GPU (walls, single phase: slope 0,'
                               r' same bounded offset)')
a2.set_xlabel('timestep')
a2.set_ylabel(r'$(M_f-M_0)/M_0$')
a2.set_yscale('log')
a2.set_title('(b) isolation: no accumulating drift (one-time offset '
             'from the 2-step transient)', fontsize=8)
a2.legend(fontsize=8, loc='center right')
a2.tick_params(labelsize=8)
a2.grid(alpha=0.3)
fig.suptitle('BI-CONSERVATION-AUDIT-001 mass drift — candidate %s' % CAND[:8],
             fontsize=9, y=1.0)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_ca_drift_horizon.svg'), bbox_inches='tight')
plt.close(fig)

# ---- figure 2: sub-step localization ------------------------------------
lw = rj('late_window_identities.json')['runs']
cases = ['C1_gpu', 'C2_gpu', 'C3_gpu', 'C3_cpu']
labels = ['C1 GPU', 'C2 GPU', 'C3 GPU', 'C3 CPU']
ids = [('J1_collision', 'J1 collision (total $f$)'),
       ('J3_stream1', 'J3 streaming1'),
       ('J7_colortrans', 'J7 colour transport')]
j3 = {c: abs(rj(os.path.join(c, 'case_report.json'))
             ['identity_stats']['J3_stream1']['mean_rel_M0'])
      for c in cases}
fig, ax = plt.subplots(figsize=(7.2, 3.6))
import numpy as np
x = np.arange(len(cases))
w = 0.26
for i, (key, lab) in enumerate(ids):
    if key == 'J3_stream1':
        vals = [j3[c] for c in cases]
    else:
        vals = [abs(lw[c][key]['mean_rel']) for c in cases]
    ax.bar(x + (i - 1) * w, vals, w, label=lab)
    for xi, v in zip(x + (i - 1) * w, vals):
        if v == 0:
            ax.text(xi, 1e-13, '0', ha='center', fontsize=7)
ax.set_yscale('log')
ax.set_ylim(1e-13, 1e-7)
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel(r'mean $|J_k|/M_0$ per step (late window)')
ax.set_title('Sub-step localization: only the collision kernel leaks '
             '(J1 total, J7 colour); streaming exactly conservative — '
             'candidate %s' % CAND[:8], fontsize=9)
ax.legend(fontsize=8)
ax.grid(alpha=0.3, axis='y', which='both')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_ca_substep_localization.svg'),
            bbox_inches='tight')
plt.close(fig)

# ---- figure 3: spatial budget (C3 GPU) ----------------------------------
sb = rj(os.path.join('C3_gpu', 'case_report.json'))['spatial_budget']
regs = ['gas_bulk', 'interface', 'liq_bulk', 'wall_rows']
dmf = [sb[r]['ref1000']['dMf'] for r in regs]
dmc = [sb[r]['ref1000']['dMc'] for r in regs]
dmrho = [sb[r]['ref1000']['dMrho'] for r in regs]
fig, ax = plt.subplots(figsize=(7.2, 3.6))
x = np.arange(len(regs))
ax.bar(x - w, dmc, w, label=r'$\Delta M_c$ (colour channel)')
ax.bar(x, dmrho, w, label=r'$\Delta M_\rho$ (macro density)')
ax.bar(x + w, dmf, w, label=r'$\Delta M_f$ (total distribution)')
ax.axhline(0, color='k', lw=0.6)
ax.set_xticks(x)
ax.set_xticklabels(['gas bulk\n(17880)', 'interface band\n(960)',
                    'liquid bulk\n(8520)', 'wall rows\n(1440)'], fontsize=8)
ax.set_ylabel('mass change vs t=1000 (final t=20000)')
ax.set_title('C3 spatial budget: colour gas$\\to$liquid shift is meniscus '
             'dynamics; leaked $M_f$/$M_\\rho$ mass resides in the bulks — '
             'candidate %s' % CAND[:8], fontsize=9)
ax.legend(fontsize=8)
ax.grid(alpha=0.3, axis='y')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_ca_spatial_budget.svg'),
            bbox_inches='tight')
plt.close(fig)

# ---- figure 4: backend + scaling ----------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
runs = ['C0_24_gpu', 'C1_gpu', 'C2_gpu', 'C3_gpu', 'C0_24_cpu', 'C1_cpu',
        'C2_cpu', 'C3_cpu']
mff = []
mc = []
for r in runs:
    rep = rj(os.path.join(r, 'case_report.json'))
    mff.append(abs(rep['drift_fits']['Mff']['slope_per_step']))
    mc.append(abs(rep['drift_fits']['Mc']['slope_per_step']))
x = np.arange(len(runs))
a1.bar(x - w / 2, mff, w, label=r'$M_f$ total channel')
a1.bar(x + w / 2, mc, w, label=r'$M_c$ colour channel')
a1.set_yscale('log')
a1.set_ylim(1e-27, 1e-7)
a1.set_xticks(x)
a1.set_xticklabels([r.replace('_gpu', '\nGPU').replace('_cpu', '\nCPU')
                    for r in runs], fontsize=7)
a1.set_ylabel(r'$|$fitted slope$|$ per step')
a1.set_title('(a) isolation x backend matrix', fontsize=9)
a1.legend(fontsize=8)
a1.grid(alpha=0.3, axis='y', which='both')

rep = rj(os.path.join('C3_gpu', 'case_report.json'))['drift_fits']
for nm, mk in [('Mff', 'o'), ('Mc', 's')]:
    d = rep[nm]['drift_at']
    ks = sorted([int(k) for k in d if int(k) % 5000 == 0])
    a2.plot(ks, [d[str(k)] for k in ks], mk + '-', label=nm)
a2.set_xlabel('timestep')
a2.set_ylabel('relative drift')
a2.set_title('(b) C3 GPU horizon scaling: $\\Delta M_f\\propto T$ '
             '(linear, $R^2=0.9999$)', fontsize=9)
a2.legend(fontsize=8)
a2.grid(alpha=0.3)
fig.suptitle('Backend comparison and scaling — candidate %s' % CAND[:8],
             fontsize=9, y=1.0)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_ca_backend_scaling.svg'),
            bbox_inches='tight')
plt.close(fig)

print('wrote 4 SVGs to', OUT)
