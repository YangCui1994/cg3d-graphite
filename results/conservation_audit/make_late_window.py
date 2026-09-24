"""Regenerate late_window_identities.json (derived artifact, N3 fix).

Committed generator: reads identities.csv + case_report.json for ALL run
dirs under results/conservation_audit and writes the late-window (last 20
traced steps) statistics for J1/J6/J7. No simulation is re-run; raw
evidence files are read-only.

Run (repo root):  python results/conservation_audit/make_late_window.py
"""
import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out = {}
    for tag in sorted(os.listdir(HERE)):
        rd = os.path.join(HERE, tag)
        rp = os.path.join(rd, 'case_report.json')
        ip = os.path.join(rd, 'identities.csv')
        if not (os.path.isfile(rp) and os.path.isfile(ip)):
            continue
        with open(rp) as f:
            rep = json.load(f)
        with open(ip, newline='') as f:
            rows = list(csv.DictReader(f))
        stp = [int(r['step']) for r in rows]
        lo = max(stp) - 19
        d = {'M0': rep['M0'], 'late_window': [int(lo), int(max(stp))]}
        for key in ['J1_collision', 'J6_macro', 'J7_colortrans']:
            v = np.array([float(x[key]) for t, x in zip(stp, rows)
                          if t >= lo])
            d[key] = dict(mean_rel=float(v.mean() / rep['M0']),
                          frac_pos=float((v > 0).mean()))
        out[tag] = d
        print('%-10s late[%5d,%5d] J1 rel %+.3e pos %.2f'
              % (tag, lo, max(stp), d['J1_collision']['mean_rel'],
                 d['J1_collision']['frac_pos']))
    with open(os.path.join(HERE, 'late_window_identities.json'), 'w') as f:
        json.dump(dict(generator='results/conservation_audit/'
                                'make_late_window.py',
                       late_window_last20=True,
                       runs=out), f, indent=1, sort_keys=True)
    print('runs:', len(out))


if __name__ == '__main__':
    main()
