"""BI-COLOUR-CLOSURE-001 — F2/F3/F4 regression table extractor.

Prints the V0/V1c/V2 regression values from the committed logs and
machine-readable reports (no hand-typed numbers).

Run (repo root):  python results/colour_closure/make_regression_tables.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, 'logs')


def log(name):
    with open(os.path.join(LOGS, name + '.log')) as f:
        return f.read()


def grab(text, pattern):
    m = re.search(pattern, text)
    return m.group(1) if m else '??'


print('### F2 (V0 suite, unchanged gates)')
rows = []
for mode in ('T0', 'CAND'):
    lap = log('f2_laplace_%s' % mode)
    con = log('f2_contact_%s' % mode)
    poi = log('f2_poiseuille_%s' % mode)
    lev = log('f2_levelA_%s' % mode)
    rows.append([
        mode,
        'PASS' if 'LEVEL A: ALL PASS' in lev else 'FAIL',
        grab(lap, r'sigma=(\S+) \(expect'),
        grab(lap, r'rel (\S+)%'),
        grab(con, r'theta_liq = (\S+) deg'),
        grab(poi, r'eff = (\S+)'),
        'PASS' if 'PASS' in log('f2_computeC_%s' % mode) else 'FAIL',
        'PASS' if 'PASS' in log('f2_postproc_%s' % mode) else 'FAIL',
    ])
print('| mode | Level A | sigma | sigma rel | theta | Poiseuille eff | '
      'Compute_C | postproc |')
print('|---|---|---:|---:|---:|---:|---|---|')
for r in rows:
    print('| %s | %s | %s | %s%% | %s | %s | %s | %s |' % tuple(r))

print()
print('### F3 (V1c, thresholds unchanged: |a-1| <= 0.10)')
st = {}
for h in (26, 40, 60, 80):
    t = log('f3_static_h%d' % h)
    st[h] = grab(t, r'C=(\S+) theta')
print('| static | C (V1c baseline 0.7902/0.7511/0.8067/0.7795; '
      'fix-task 0.7902/0.7513/0.8070/0.7834) |')
print('|---|---|')
for h in (26, 40, 60, 80):
    print('| h%d | %s |' % (h, st[h]))
import csv as _csv
with open(os.path.join(HERE, 'levelc_v1c_fix',
                       'differential_table.csv')) as f:
    dt = list(_csv.DictReader(f))
print()
print('| h | a_h | L0/h (V1c base 3.0220/4.2489; fix 3.053/4.322) |')
print('|---|---:|---:|')
for r in dt:
    print('| %s | %s | %s |' % (r['h'], r['a_h'], r['L0_over_h']))
with open(os.path.join(HERE, 'levelc_v1c_fix', 'gates.csv')) as f:
    gt = list(_csv.DictReader(f))
print()
print('| tag | g1 | g2 | g3 | g4 | g5 | g6 | g7 | g8 | all_hard |')
print('|---|---|---|---|---|---|---|---|---|---|')
for r in gt:
    if r['mode'] == 'dynamic':
        print('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r['tag'], r['g1_no_nan'], r['g2_umax'], r['g3_zero_dp'],
            r['g4_monotonic'], r['g5_window'], r['g6_r2'],
            r['g7_front_agree'], r['g8_band_frac'], r['all_hard']))

print()
print('### F4 (V2 primary, 60k; gates: mirror, eps<=5e-4, topology)')
r = json.load(open(os.path.join(HERE, 'levelc_v2_fix', 'v2_primary',
                                'report.json')))


def deep(d, path):
    for k in path.split('.'):
        d = d[k]
    return d


vals = dict(
    max_eps_r=deep(r, 'mass_stability.max_eps_r') if 'mass_stability'
    in r else None,
)
print('```json')
print(json.dumps(dict(
    gates=r['gates'],
    mirror=deep(r, 'symmetry') if 'symmetry' in r else None,
    max_eps_r=r.get('max_eps_r'),
    max_eps_b=r.get('max_eps_b'),
    cluster_count_max=r.get('cluster_count_max'),
    cluster_count_final=r.get('cluster_count_final'),
    V_bin_change_pct=r.get('V_bin_change_pct'),
    steps=r.get('steps_run'),
), indent=1, default=str)[:1800])
print('```')

print()
print('### F10 perf pairs (same grid/horizon, JIT excluded)')
for tag in ('perf_C3_T3C1s_20k', 'perf_C3_T3C1X_A2_20k',
            'perf_C1_T3C1s_20k', 'perf_C1_T3C1X_A2_20k'):
    p = os.path.join(HERE, tag, 'accum_report.json')
    if os.path.exists(p):
        rr = json.load(open(p))
        print('%-22s %.0f steps/s  %.1f MLUPS'
              % (tag, rr['steady_steps_per_s'], rr['mlups']))
