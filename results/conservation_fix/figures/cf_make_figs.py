"""BI-SOLVER-CONSERVATION-FIX-001 figures.

Reads ONLY committed product evidence (CSV/JSON under
results/conservation_fix/ of the candidate worktree); candidate SHA is
annotated per figure in the living document captions.

Run (repo root, env lbm):  python results/conservation_fix/figures/cf_make_figs.py
"""
import csv
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.dirname(HERE)          # results/conservation_fix
OUT = HERE


def rj(rel):
    with open(os.path.join(EV, rel)) as f:
        return json.load(f)


def series(tag):
    with open(os.path.join(EV, tag, 'long_horizon_mass.csv'),
              newline='') as f:
        rows = list(csv.DictReader(f))
    rep = rj(os.path.join(tag, 'f1_report.json'))
    M0 = rep['M0']
    t = np.array([int(r['step']) for r in rows])
    mf = np.array([float(r['Mff']) for r in rows]) / M0 - 1
    mc = np.array([float(r['Mr']) + float(r['Mb']) for r in rows]) / M0 - 1
    return t, mf, mc


# ---- figure 1: long-horizon drift comparison ---------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
for tag, ls, lab in [
        ('f1_T0C0_60k', '-', 'T0+C0 baseline (60k)'),
        ('f1_T3C0_60k', '--', 'T3+C0 reference (60k)'),
        ('f1_T3C1s_60k', '-', 'T3+C1(scoped) SELECTED (60k)'),
        ('f1_T2C1_20k', ':', 'T2+C1 rejected (20k)')]:
    t, mf, mc = series(tag)
    a1.plot(t, mf * 1e4, ls, lw=1.4, label=lab)
    a2.plot(t, mc * 1e4, ls, lw=1.4, label=lab)
a1.set_xlabel('timestep')
a1.set_ylabel(r'total-channel drift $(M_f-M_0)/M_0$  [$10^{-4}$]')
a1.set_title('(a) total distribution channel', fontsize=9)
a1.legend(fontsize=7)
a1.grid(alpha=0.3)
a2.set_xlabel('timestep')
a2.set_ylabel(r'colour drift $(M_c-M_0)/M_0$  [$10^{-4}$]')
a2.set_title('(b) colour channel', fontsize=9)
a2.legend(fontsize=7)
a2.grid(alpha=0.3)
fig.suptitle('BI-SOLVER-CONSERVATION-FIX-001: C3 long-horizon drift '
             'candidate comparison', fontsize=9, y=1.0)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_cf_drift_comparison.svg'),
            bbox_inches='tight')
plt.close(fig)

# ---- figure 2: F0 local identities + A2 stationarity --------------------
f0 = rj('f0_T0C0/f0_report.json')['geoms']['C3']['probe']
cands = ['T0+C0', 'T1+C0', 'T2+C0', 'T3+C0', 'T4+C0', 'T3+C1(scoped)']
tags = ['f0_T0C0', 'f0_T1C0', 'f0_T2C0', 'f0_T3C0', 'f0_T4C0', 'f0_T3C1s']
rf, rr = [], []
for tg in tags:
    g = rj(os.path.join(tg, 'f0_report.json'))['geoms']['C3']['probe']
    rf.append(g['R_f']['mean'])
    rr.append(g['R_r']['mean'])
x = np.arange(len(cands))
w = 0.36
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
a1.bar(x - w / 2, rf, w, label=r'$R_f$ total (per node/collision)')
a1.bar(x + w / 2, rr, w, label=r'$R_r$ colour')
a1.axhline(0, color='k', lw=0.6)
a1.set_yscale('symlog', linthresh=1e-12)
a1.set_xticks(x)
a1.set_xticklabels(cands, fontsize=7, rotation=20)
a1.set_title('(a) F0 local closure (C3; T4 = negative control)', fontsize=9)
a1.legend(fontsize=8)
a1.grid(alpha=0.3, axis='y', which='both')
a2v = [0.0, 4.463e-6, 4.463e-6, 0.0, 4.463e-6, 0.0]
cols = ['tab:blue' if v < 1e-6 else 'tab:red' for v in a2v]
a2.bar(x, a2v, 0.5, color=cols)
a2.axhline(1e-6, color='r', ls='--', lw=1, label='A2 gate 1e-6')
a2.set_yscale('symlog', linthresh=1e-9)
a2.set_xticks(x)
a2.set_xticklabels(cands, fontsize=7, rotation=20)
a2.set_ylabel(r'uniform-phase $\max|v|$ after 200 steps')
a2.set_title('(b) V0 A2 stationarity gate (unchanged)', fontsize=9)
a2.legend(fontsize=8)
a2.grid(alpha=0.3, axis='y', which='both')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_cf_f0_a2.svg'), bbox_inches='tight')
plt.close(fig)

# ---- figure 3: V2 regression before/after --------------------------------
base = rj(os.path.join('..', '..', 'results', 'levelc_v2', 'v2_primary',
                       'report.json')) if os.path.exists(
    os.path.join(EV, '..', '..', 'results', 'levelc_v2', 'v2_primary',
                 'report.json')) else None
fix = rj('levelc_v2_fix/v2_primary/report.json')
if base:
    names = ['max e_x (lu)', r'max $\epsilon_r$', r'max $\epsilon_b$']
    bvals = [base['max_e_x'], base['max_eps_r'], base['max_eps_b']]
    fvals = [fix['max_e_x'], fix['max_eps_r'], fix['max_eps_b']]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(x - 0.2, bvals, 0.4, label='V2 baseline (candidate 5e679d8)')
    ax.bar(x + 0.2, fvals, 0.4,
           label='V2 on fixed solver (this candidate)')
    ax.axhline(5e-4, color='r', ls='--', lw=1,
               label='original g6 value 5e-4')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9)
    ax.set_title('F4: V2 bilateral regression — mirror error and colour '
                 'mass drift before/after', fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis='y', which='both')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig_cf_v2_regression.svg'),
                bbox_inches='tight')
    plt.close(fig)

print('figures written to', OUT)
