"""Regression test 1.2 (Plan_20260919_v2): body-forced Poiseuille with the
CG3D solver (single phase, Guo forcing).

History: the original GuoF omitted the 1/cs^2 (=3) and 1/cs^4 (=9) factors
of the Guo (2002) force weights, so the momentum actually injected per step
is F/3, while the half-force velocity correction in streaming3 uses F/2.
The 2D/3D P2 permeability validations absorbed this via a MEASURED
effective-force factor (channel calibration, results_p2_ordered/p2_report:
"Guo effective factor = fx*0.330").  This test measures that factor
directly on the 3D solver:

  eff = u_mean / (fx * h^2 / (12 nu))      -> 1.0 for exact Guo

Before the fix: eff ~ 0.33 (matches the 2D measurement 0.330).
After the fix:  eff ~ 1.0 and the profile L2 error vs the analytic
parabola is a few percent (half-way BB at tau = 0.8, non-magic).

Run:  python tests/test_poiseuille_cg3d.py   (exit 0 = pass)
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

N = 32
WT = 4                    # wall thickness (y)
NU = 0.1                  # nu_g = niu_g default
FX = 2.0e-6
STEPS = 20000
SAMPLE_FROM = 15000
H = N - 2 * WT            # half-way bounce-back channel width
CS2 = 1.0 / 3.0


def main():
    s = ColorGradientSolver3D(N, N, N)          # niu_l = niu_g = 0.1
    solid = np.zeros((N, N, N), dtype=np.int8)
    solid[:, :WT, :] = 1
    solid[:, -WT:, :] = 1
    psi = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
    s.set_body_force(FX, 0.0, 0.0)
    s.init(psi, solid)
    fluid = solid == 0

    t0 = time.time()
    umeans = []
    for it in range(1, STEPS + 1):
        s.step()
        if it >= SAMPLE_FROM and it % 500 == 0:
            _, v = s.macro_snapshot()
            umeans.append(float(v[..., 0][fluid].mean()))
    umean = float(np.mean(umeans))

    uth = FX * H ** 2 / (12.0 * NU)             # exact Guo expectation
    eff = umean / uth

    # profile L2 vs analytic parabola u(d) = F/(2 rho nu) d (H - d)
    _, v = s.macro_snapshot()
    prof = v[..., 0].mean(axis=(0, 2))[WT:N - WT]
    y = np.arange(WT, N - WT)
    d = y - WT + 0.5
    ana = FX / (2.0 * NU) * d * (H - d)
    l2 = float(np.sqrt(np.sum((prof - ana) ** 2) / np.sum(ana ** 2)))

    print(f'u_mean = {umean:.6e}, analytic = {uth:.6e}')
    print(f'effective force factor eff = {eff:.4f}   (1.0 = exact Guo)')
    print(f'profile L2 vs parabola    = {l2:.4f}    ({time.time()-t0:.0f}s)')

    ok = (0.97 <= eff <= 1.03) and (l2 < 0.05)
    if not ok:
        print('FAIL: eff outside [0.97, 1.03] or L2 >= 5%')
        sys.exit(1)
    print('PASS: Guo forcing injects the full body force; Poiseuille '
          'profile matches the analytic parabola')


if __name__ == '__main__':
    main()
