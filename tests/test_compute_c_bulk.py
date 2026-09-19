"""Regression test 1.1 (Plan_20260919_v2): Compute_C bulk suppression must
be density-independent.

The single-phase-next-to-solid suppression in Compute_C originally used
``abs(rho_r - rho_b) > 0.9`` — a threshold on the RAW colour-density
difference.  Under rho-pressure driving the outlet side sits at
rho = 1 - d/2 (X2 ladder reaches d = 0.22 -> rho = 0.89), where pure red
gives |rho_r - rho_b| = 0.89 < 0.9: the suppression silently fails and
spurious wall forces appear exactly at the high-Pc rungs.

The fix normalises the criterion by the local total density
(|rho_r - rho_b| > 0.9 * (rho_r + rho_b), i.e. |psi| > 0.9), which is
IDENTICAL at rho ~ 1 (all Laplace / contact-angle calibrations) and only
changes behaviour where the old one was provably wrong.

Run:  python tests/test_compute_c_bulk.py   (exit 0 = pass)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

N = 12


def build():
    s = ColorGradientSolver3D(N, N, N)
    solid = np.zeros((N, N, N), dtype=np.int8)
    solid[0, :, :] = 1                      # one solid wall at x = 0
    psi = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
    s.init(psi, solid)
    return s, solid


def set_uniform_phase(s, solid, rho_r, rho_b):
    """Overwrite the colour fields directly (probe reads fields, no step)."""
    s.rho_r.from_numpy(np.full((N, N, N), rho_r, dtype=np.float32))
    s.rho_b.from_numpy(np.full((N, N, N), rho_b, dtype=np.float32))
    psi = np.full((N, N, N), (rho_r - rho_b) / (rho_r + rho_b),
                  dtype=np.float32)
    psi[solid > 0] = 0.0
    s.psi.from_numpy(psi)


def norm_at(s, x):
    """|C| norm of the node at (x, N//2, N//2) — adjacent to the wall for
    x = 1 (psi_solid default +0.7 vs bulk psi -> non-zero raw gradient)."""
    C = s.color_gradient_snapshot()
    return float(np.linalg.norm(C[x, N // 2, N // 2]))


def main():
    s, solid = build()
    failures = []

    # A) pure red at rho = 0.89 (outlet side of the d = 0.22 rung):
    #    suppression MUST apply  (old criterion: 0.89 < 0.9 -> FAILED to suppress)
    set_uniform_phase(s, solid, 0.89, 0.0)
    cA = norm_at(s, 1)
    print(f'A  pure red  rho=0.89 next to solid: |C| = {cA:.3e}  '
          f'(expect 0)')
    if cA != 0.0:
        failures.append('A')

    # B) pure red at rho = 1.0: suppression applies (unchanged behaviour)
    set_uniform_phase(s, solid, 1.0, 0.0)
    cB = norm_at(s, 1)
    print(f'B  pure red  rho=1.00 next to solid: |C| = {cB:.3e}  '
          f'(expect 0)')
    if cB != 0.0:
        failures.append('B')

    # C) interface psi = +0.2 at rho = 1.0: NOT suppressed (bulk test does
    #    not fire) -> wall colour contribution survives
    set_uniform_phase(s, solid, 0.6, 0.4)
    cC = norm_at(s, 1)
    print(f'C  psi=+0.2  rho=1.00 next to solid: |C| = {cC:.3e}  '
          f'(expect > 0)')
    if not (cC > 0.0):
        failures.append('C')

    # D) same psi = +0.2 at rho = 1.1: same outcome as C (rho-independence)
    set_uniform_phase(s, solid, 0.66, 0.44)
    cD = norm_at(s, 1)
    print(f'D  psi=+0.2  rho=1.10 next to solid: |C| = {cD:.3e}  '
          f'(expect > 0)')
    if not (cD > 0.0):
        failures.append('D')

    if failures:
        print(f'FAIL: cases {failures}')
        sys.exit(1)
    print('PASS: bulk suppression is density-independent; interface '
          'behaviour unchanged')


if __name__ == '__main__':
    main()
