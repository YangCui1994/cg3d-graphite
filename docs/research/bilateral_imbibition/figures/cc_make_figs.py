"""BI-COLOUR-CLOSURE-001 figures.

Reads ONLY committed product evidence (CSV/JSON under
results/colour_closure/ plus the committed baseline
results/conservation_fix/f1_T3C1s_60k); candidate SHA is annotated per
figure in the living-document captions.

Run (repo root, env lbm):
  python results/colour_closure/figures/cc_make_figs.py
"""
import csv
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.dirname(HERE)          # results/colour_closure
CF = os.path.join(os.path.dirname(EV), 'conservation_fix')
OUT = HERE


def rj(path):
    with open(path) as f:
        return json.load(f)


def series(tag, root=EV):
    with open(os.path.join(root, tag, 'mass_series.csv'),
              newline='') as f:
        rows = list(csv.DictReader(f))
    if root == EV:
        M0 = rj(os.path.join(root, tag, 'accum_report.json'))['M0']
        t = np.array([int(r['step']) for r in rows])
        mr = np.array([float(r['Mr']) for r in rows])
        mb = np.array([float(r['Mb']) for r in rows])
        mf = np.array([float(r['Mff']) for r in rows])
    else:                            # committed f1 driver CSV
        M0 = rj(os.path.join(root, tag, 'f1_report.json'))['M0']
        t = np.array([int(r['step']) for r in rows])
        mr = np.array([float(r['Mr']) for r in rows])
        mb = np.array([float(r['Mb']) for r in rows])
        mf = np.array([float(r['Mff']) for r in rows])
    return t, mf / M0 - 1.0, mr / M0 - 1.0, mb / M0 - 1.0, \
        (mr + mb) / M0 - 1.0


# ---- figure 1: diagnosis -----------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
rows = list(csv.DictReader(open(os.path.join(EV, 'dx_C1_T3C1s',
                                             'x_profile.csv'))))
x = np.array([int(r['x']) for r in rows])
a1.plot(x, np.array([float(r['Req_r']) for r in rows]) * 1e9, '-',
        lw=1.3, label='Req_r (eq-stage leak, uncorrected)')
a1.plot(x, np.array([float(r['R_r']) for r in rows]) * 1e9, '-',
        lw=1.3, label='R_r (post scoped-C1)')
a1.plot(x, np.abs(np.array([float(r['net_r']) for r in rows])) * 1e9,
        ':', lw=1.1, label='|net_r| (mass motion)')
a1.set_yscale('symlog', linthresh=1e-3)
a1.set_xlabel('x (periodic slab, interface at x=32)')
a1.set_ylabel('per-node residual (1e-9 / step)')
a1.set_title('(a) periodic C1: biased band = non-frozen cc==0 nodes')
a1.legend(fontsize=7, loc='lower right')
a1.axvspan(28, 44, color='0.92')

rows = list(csv.DictReader(open(os.path.join(EV, 'bg_C3_T3C1s',
                                             'budget_class.csv'))))
idx = {(r['class'], r['quantity']): float(r['mean']) for r in rows}
classes = ['cc>0', 'cc==0', 'mixed', 'pure', 'wall_adj', 'non_wall']
xx = np.arange(len(classes))
sr = [idx[(c, 'sum_R_r')] * 1e9 for c in classes]
da = [idx[(c, 'sum_dacc_r')] * 1e9 for c in classes]
a2.bar(xx - 0.2, sr, 0.4, label='local closure R_r (per node)')
a2.bar(xx + 0.2, da, 0.4, label='accumulate rounding dacc_r')
a2.set_xticks(xx)
a2.set_xticklabels(classes, fontsize=8)
a2.set_ylabel('per-node per-step mean (1e-9)')
a2.set_title('(b) C3 budget by class: two opposite mechanisms')
a2.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_cc_diagnosis.svg'))
plt.close(fig)

# ---- figure 2: candidate comparison ------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.8))
serieses = [
    ('ac_C1_T3C1s_20k', EV, '-', 'C1 scoped / A0 (base, 20k)'),
    ('ac_C1_T3C1X_20k', EV, '--', 'C1X / A0 (closure only, 20k)'),
    ('ac_C1_T3C1_A1_20k', EV, ':', 'C1 / A1 (f64 accumulate only, 20k)'),
    ('ac_C1_T3C1X_A1_20k', EV, '-.', 'C1X / A1 (20k)'),
    ('ac_C1_T3C1X_A2_20k', EV, '-', 'C1X / A2 f64 pipeline (20k)'),
]
for tag, root, ls, lab in serieses:
    p = os.path.join(root, tag, 'mass_series.csv')
    if not os.path.exists(p):
        continue
    t, _, _, _, mc = series(tag, root)
    a1.plot(t, mc * 1e6, ls, lw=1.3, label=lab)
a1.set_xlabel('timestep')
a1.set_ylabel('colour drift (M_c/M_0 - 1, 1e-6)')
a1.set_title('(a) periodic C1 accumulation')
a1.legend(fontsize=7)

serieses2 = [
    ('f1_T3C1s_60k', CF, '-', 'C1 scoped / A0 (committed base, 60k)'),
    ('ac_C3_T3C1s_60k_rerun', EV, ':', 'C1 scoped / A0 (rerun, 60k)'),
    ('ac_C3_T3C1X_60k', EV, '--', 'C1X / A0 (60k)'),
    ('ac_C3_T3C1_A1_60k', EV, '-.', 'C1 / A1 (60k)'),
    ('ac_C3_T3C1X_A1_60k', EV, '--', 'C1X / A1 (60k)'),
    ('ac_C3_T3C1X_A2_60k', EV, '-', 'C1X / A2 f64 pipeline (60k)'),
]
for tag, root, ls, lab in serieses2:
    p = os.path.join(root, tag, 'mass_series.csv')
    if not os.path.exists(p):
        continue
    t, _, _, _, mc = series(tag, root)
    a2.plot(t, mc * 1e6, ls, lw=1.3, label=lab)
a2.set_xlabel('timestep')
a2.set_ylabel('colour drift (M_c/M_0 - 1, 1e-6)')
a2.set_title('(b) C3 slit 60k')
a2.legend(fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig_cc_candidates.svg'))
plt.close(fig)
print('figures written to', OUT)
