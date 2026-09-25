"""A2 stationarity isolation (attempt-1 review minor item): re-run the
uniform single-phase 200-step A2 check for every candidate combo so the
isolation table in CANDIDATE_COMPARISON.md is backed by committed
evidence (the original isolation runs were executor console output; only
T0 / T1+C1 / T3+C1s had committed full-suite logs).

Run (repo root):  python results/conservation_fix/a2_isolation_check.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

os.environ.setdefault('LBM_ARCH', 'gpu')
sys.path.insert(0, ROOT)

from lbm_solver_cg3d import ColorGradientSolver3D   # noqa: E402


def a2(fix, cf, N=24, steps=200):
    s = ColorGradientSolver3D(N, N, N, total_fix=fix, colour_fix=cf)
    solid = np.zeros((N, N, N), dtype=np.int8)
    s.init(-np.ones((N, N, N), dtype=np.float32), solid)
    for _ in range(steps):
        s.step()
    v = np.abs(s.v.to_numpy()).max()
    psi = np.abs(s.psi_snapshot() + 1).max()
    return dict(max_v=float(v), psi_dev=float(psi),
                gate=bool(v < 1e-6 and psi < 1e-3))


def main():
    out = {}
    for fix, cf in [('T0', 'C0'), ('T1', 'C0'), ('T2', 'C0'),
                    ('T3', 'C0'), ('T4', 'C0'), ('T0', 'C1'),
                    ('T1', 'C1'), ('T2', 'C1'), ('T3', 'C1')]:
        key = '%s+%s' % (fix, cf)
        out[key] = a2(fix, cf)
        print('%-8s max|v|=%.3e psi_dev=%.1e gate=%s'
              % (key, out[key]['max_v'], out[key]['psi_dev'],
                 out[key]['gate']), flush=True)
    with open(os.path.join(HERE, 'a2_isolation.json'), 'w') as f:
        json.dump(dict(grid=24, steps=200, results=out), f, indent=1)
    print('written a2_isolation.json')


if __name__ == '__main__':
    main()
