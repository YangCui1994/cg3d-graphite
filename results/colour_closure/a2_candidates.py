"""BI-COLOUR-CLOSURE-001 — A2 stationarity isolation for the new
colour-only candidate combos (same protocol as the committed
results/conservation_fix/a2_isolation_check.py: uniform single-phase
N=24, 200 steps, gate max|v| < 1e-6 and |psi+1| < 1e-3).

Run (repo root):  python results/colour_closure/a2_candidates.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

os.environ.setdefault('LBM_ARCH', 'gpu')
sys.path.insert(0, ROOT)

from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

COMBOS = [
    ('T3', 'C1', 'A0'),    # accepted baseline (reference)
    ('T3', 'C1R', 'A0'),
    ('T3', 'C1X', 'A0'),
    ('T3', 'C1', 'A1'),
    ('T3', 'C1X', 'A1'),
]


def a2(fix, cf, acc, N=24, steps=200):
    s = ColorGradientSolver3D(N, N, N, total_fix=fix, colour_fix=cf,
                              acc_fix=acc)
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
    for fix, cf, acc in COMBOS:
        key = '%s+%s/%s' % (fix, cf, acc)
        out[key] = a2(fix, cf, acc)
        print(key, out[key], flush=True)
    with open(os.path.join(HERE, 'a2_candidates.json'), 'w') as fh:
        json.dump(dict(grid=24, steps=200, results=out), fh, indent=1)


if __name__ == '__main__':
    main()
