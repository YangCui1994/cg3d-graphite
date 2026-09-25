"""Executor-side check of the f32 inv_M zeroth-column defect (B2, derived
artifact; no simulation).

Reproduces, from the solver's own stored tables, the number the attempt-1
reviewer derived independently: sum_s inv_M[s, 0] must equal 1 exactly for
the moment roundtrip to conserve the zeroth moment in f32; the stored f32
inverse gives 1 + 1.49e-8, which predicts the measured per-step relative
drift of the total-distribution channel.

Read-only: imports the solver module (tables only; no field is stepped).
Run (repo root, CPU backend to avoid touching the GPU):
  LBM_ARCH=cpu python results/conservation_audit/inv_m_colsum_check.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

os.environ.setdefault('LBM_ARCH', 'cpu')
sys.path.insert(0, ROOT)

import lbm_solver_cg3d as lbm   # noqa: E402  (module-level ti.init(cpu))


def main():
    inv = lbm.inv_M.to_numpy()          # the exact f32 table the kernels use
    M = lbm.M.to_numpy()
    colsum = inv.sum(axis=0, dtype=np.float64)
    out = dict(
        colsum_inv_M_f64=colsum.tolist(),
        colsum0_minus_1=float(colsum[0] - 1.0),
        max_abs_other_colsums=float(np.abs(colsum[1:]).max()),
        M_row0_integer=bool(np.array_equal(M[0], np.ones(19))),
        predicted_total_channel_rate_per_step=float(colsum[0] - 1.0),
        measured_C3_gpu=1.5556e-08,
        measured_C3_cpu=1.5173e-08,
        note='sum_s inv_M[s,0] != 1 in f32: the stored f32 inverse does '
             'not conserve the zeroth moment; prediction vs measurement '
             '(attempt-1 review, reproduced executor-side): +4.4%/+1.8%')
    with open(os.path.join(HERE, 'inv_m_colsum_check.json'), 'w') as f:
        json.dump(out, f, indent=1)
    print('colsum(inv_M)[0] - 1 = %+.17e' % out['colsum0_minus_1'])
    print('max |colsum[l>0]|      = %.3e' % out['max_abs_other_colsums'])
    print('M row 0 integer ones  =', out['M_row0_integer'])


if __name__ == '__main__':
    main()
