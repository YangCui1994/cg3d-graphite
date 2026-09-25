"""BI-COLOUR-CLOSURE-001 — generate all derived report tables from the
committed machine-readable evidence (CSV/JSON).  Outputs markdown
fragments to stdout; the reports (LOCAL_RESIDUAL_DIAGNOSIS.md,
CANDIDATE_COMPARISON.md) quote these verbatim.

Run (repo root):
  python results/colour_closure/make_report_tables.py diagnosis
  python results/colour_closure/make_report_tables.py candidates
"""
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_csv(rel):
    return list(csv.DictReader(open(os.path.join(HERE, rel))))


def load_json(rel):
    return json.load(open(os.path.join(HERE, rel)))


def fmt(x, digits=3):
    if x == 0:
        return '0'
    return ('%+.' + str(digits) + 'e') % x


def class_table(tag, classes, quantities):
    rows = load_csv('%s/class_stats.csv' % tag)
    idx = {(r['class'], r['quantity']): r for r in rows}
    out = ['| class | quantity | n | mean | std | frac_pos | max_abs |',
           '|---|---|---:|---:|---:|---:|---:|']
    for cls in classes:
        for q in quantities:
            r = idx.get((cls, q))
            if r is None:
                continue
            out.append('| %s | %s | %s | %s | %s | %.3f | %s |'
                       % (cls, q, r['n'], fmt(float(r['mean'])),
                          fmt(float(r['std'])), float(r['frac_pos']),
                          fmt(float(r['max_abs']))))
    return '\n'.join(out)


def accum_table(tags):
    out = ['| tag | Mr slope/step | R2 | Mb slope/step | R2 | Mc slope/step '
           '| R2 | Mc frac_pos | Mff slope/step | R2 |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for tag in tags:
        rep_path = os.path.join(HERE, tag, 'accum_report.json')
        if not os.path.exists(rep_path):
            continue
        f = load_json('%s/accum_report.json' % tag)['drift_fits']
        out.append('| %s | %s | %.4f | %s | %.4f | %s | %.4f | %.3f | '
                   '%s | %.4f |'
                   % (tag, fmt(f['Mr']['slope_per_step']), f['Mr']['r2'],
                      fmt(f['Mb']['slope_per_step']), f['Mb']['r2'],
                      fmt(f['Mc']['slope_per_step']), f['Mc']['r2'],
                      f['Mc']['frac_pos'],
                      fmt(f['Mff']['slope_per_step']), f['Mff']['r2']))
    return '\n'.join(out)


def segmented_table(tag, M0key='M0'):
    p = os.path.join(HERE, tag, 'mass_series.csv')
    if not os.path.exists(p):
        return '(missing)'
    rows = load_csv('%s/mass_series.csv' % tag)
    t = np.array([float(r['step']) for r in rows])
    Mr = np.array([float(r['Mr']) for r in rows])
    Mb = np.array([float(r['Mb']) for r in rows])
    Mff = np.array([float(r['Mff']) for r in rows])
    M0 = load_json('%s/accum_report.json' % tag)[M0key]
    Mc = (Mr + Mb) / M0 - 1.0
    tot = Mff / M0 - 1.0
    out = ['| interval | colour slope/step | R2 | frac_pos | total '
           'slope/step | R2 |', '|---|---:|---:|---:|---:|---:|']
    spans = [(1, len(t) and int(t[-1]))]
    hi = int(t[-1])
    thirds = sorted({1, hi // 3, 2 * hi // 3, hi})
    for lo, h in [(thirds[i], thirds[i + 1])
                  for i in range(len(thirds) - 1)] + [(1, hi)]:
        m = (t >= lo) & (t <= h)

        def fit(y):
            pp = np.polyfit(t[m], y[m], 1)
            yh = np.polyval(pp, t[m])
            r2 = 1 - np.sum((y[m] - yh) ** 2) / np.sum((y[m] - y[m].mean()) ** 2)
            fp = (np.diff(y[m]) > 0).mean()
            return pp[0], r2, fp
        cs, cr, cf = fit(Mc)
        ts, tr, _ = fit(tot)
        out.append('| %d-%d | %s | %.4f | %.3f | %s | %.4f |'
                   % (lo, h, fmt(cs), cr, cf, fmt(ts), tr))
    return '\n'.join(out)


def budget_table(tags):
    out = ['| tag | dMr/step | sumR_r | sumdacc_r | identity resid | '
           'dMb/step | sumR_b | sumdacc_b | identity resid |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for tag in tags:
        p = os.path.join(HERE, tag, 'budget_report.json')
        if not os.path.exists(p):
            continue
        m = load_json('%s/budget_report.json' % tag)['means']
        out.append('| %s | %s | %s | %s | %.1e | %s | %s | %s | %.1e |'
                   % (tag, fmt(m['dMr']), fmt(m['sumR_r']),
                      fmt(m['sumdacc_r']), m['identity_resid_r'],
                      fmt(m['dMb']), fmt(m['sumR_b']),
                      fmt(m['sumdacc_b']), m['identity_resid_b']))
    return '\n'.join(out)


def a2_table():
    p = os.path.join(HERE, 'a2_candidates.json')
    if not os.path.exists(p):
        return '(pending)'
    d = load_json('a2_candidates.json')['results']
    out = ['| combo | max abs v | psi dev | gate (<1e-6, <1e-3) |',
           '|---|---:|---:|---|']
    for k, v in d.items():
        out.append('| %s | %s | %s | %s |'
                   % (k, fmt(v['max_v']), fmt(v['psi_dev']),
                      'PASS' if v['gate'] else 'FAIL'))
    return '\n'.join(out)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'diagnosis'
    if which == 'diagnosis':
        print('### dx_C1_T3C1s key classes (red channel)')
        print(class_table('dx_C1_T3C1s',
                          ['ALL', 'cc>0', 'cc==0', 'mixed', 'pure'],
                          ['Req_r', 'R_r', 'Rc1_r', 'dacc_r', 'net_r']))
        print()
        print('### dx_C3_T3C1s key classes (red channel)')
        print(class_table('dx_C3_T3C1s',
                          ['ALL', 'cc>0', 'cc==0', 'wall_adj', 'pure'],
                          ['Req_r', 'R_r', 'Rc1_r', 'dacc_r', 'net_r']))
        print()
        print('### periodic-C1 accumulation (contract C, 20k, every 200)')
        print(accum_table(['ac_C1_T3C1s_20k']))
        print()
        print('### C3 budget identity (t=20k, 200 probed steps)')
        print(budget_table(['bg_C3_T3C1s']))
        print()
        print('### C3 budget per-class means (red)')
        rows = load_csv('bg_C3_T3C1s/budget_class.csv')
        out = ['| class | sum_R_r mean | frac_pos | sum_dacc_r mean | '
               'frac_pos |', '|---|---:|---:|---:|---:|']
        idx = {(r['class'], r['quantity']): r for r in rows}
        for cls in ('cc>0', 'cc==0', 'mixed', 'pure', 'wall_adj',
                    'non_wall'):
            a = idx.get((cls, 'sum_R_r'))
            b = idx.get((cls, 'sum_dacc_r'))
            if a and b:
                out.append('| %s | %s | %.3f | %s | %.3f |'
                           % (cls, fmt(float(a['mean'])),
                              float(a['frac_pos']),
                              fmt(float(b['mean'])),
                              float(b['frac_pos'])))
        print('\n'.join(out))
    elif which == 'candidates':
        print('### periodic-C1 accumulation across candidates (20k)')
        print(accum_table(['ac_C1_T3C1s_20k', 'ac_C1_T3C1X_20k',
                           'ac_C1_T3C1_A1_20k', 'ac_C1_T3C1X_A1_20k',
                           'ac_C1_T3C1_A2_20k', 'ac_C1_T3C1X_A2_20k']))
        print()
        print('### C3 60k across candidates')
        print(accum_table(['ac_C3_T3C1s_60k_rerun', 'ac_C3_T3C1X_60k',
                           'ac_C3_T3C1_A1_60k', 'ac_C3_T3C1X_A1_60k',
                           'ac_C3_T3C1X_A2_60k']))
        print()
        for tag in ('ac_C3_T3C1s_60k_rerun', 'ac_C3_T3C1X_A1_60k',
                    'ac_C3_T3C1_A1_60k', 'ac_C3_T3C1X_A1_60k'):
            print('### segmented: %s' % tag)
            print(segmented_table(tag))
            print()
        print('### candidate budgets')
        print(budget_table(['bg_C3_T3C1s', 'bg_C3_T3C1X_A1',
                            'bg_C3_T3C1X_A2']))
        print()
        print('### A2 isolation')
        print(a2_table())
        print()
        print('### C1R rest-population f32-storage survival (F0, cc>0)')
        print(class_table('dx_C1_T3C1R', ['cc>0'],
                          ['Req_r', 'R_r', 'Rc1_r']))
        print()
        print('### candidate local closure (red, ALL + classes)')
        print(class_table('dx_C1_T3C1X_A2', ['ALL', 'cc>0', 'cc==0'],
                          ['Req_r', 'R_r', 'Rc1_r', 'dacc_r']))
        print()
        print(class_table('dx_C3_T3C1X_A2', ['ALL', 'cc>0', 'cc==0',
                                             'wall_adj'],
                          ['Req_r', 'R_r', 'Rc1_r', 'dacc_r']))


if __name__ == '__main__':
    main()
