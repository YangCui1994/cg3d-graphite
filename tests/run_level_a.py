"""Level A regression suite (Plan_20260919_v2 Phase 3): fast checks that
can run before every commit — seconds each once JIT-warm.

JIT RULE: ONE solver instance for the whole process (Taichi JIT is
~5.5 min per instance on this machine and the 2nd instance in a process
always misses the cache); every test re-initialises the fields instead.

Run:  python tests/run_level_a.py   (exit 0 = pass)
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lbm_solver_cg3d as mod  # noqa: E402
from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

N = 32
FAIL = []


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name + ('  ' + detail if detail
                                                   else ''), flush=True)
    if not cond:
        FAIL.append(name)


def reset(s, psi, solid):
    """Full field reset between tests: geometry + phase + infra masks."""
    s.init(psi.astype(np.float32), solid.astype(np.int8))
    s.res_mask.from_numpy(np.zeros((N, N, N), np.int8))
    s.res_psi.from_numpy(np.zeros((N, N, N), np.float32))
    s.res_rho.from_numpy(np.zeros((N, N, N), np.float32))
    s.mem_r.from_numpy(np.zeros((N, N, N), np.int8))
    s.mem_b.from_numpy(np.zeros((N, N, N), np.int8))
    s.use_reservoirs = False
    s.inj_r[None] = 0.0
    s.inj_b[None] = 0.0
    s.inj_m[None] = 0.0
    s.set_body_force(0.0, 0.0, 0.0)


def main():
    t00 = time.time()

    # A1 — M / inv_M consistency (pure numpy on the module tables)
    M = mod.M.to_numpy().astype(np.float64)
    iM = mod.inv_M.to_numpy().astype(np.float64)
    err = float(np.abs(M @ iM - np.eye(19)).max())
    check('A1 M @ inv_M == I', err < 1e-5, f'max|err|={err:.2e}')

    s = ColorGradientSolver3D(N, N, N)
    solid0 = np.zeros((N, N, N), np.int8)

    # A2 — uniform single phase stays stationary (no spurious currents)
    reset(s, -np.ones((N, N, N)), solid0)
    m0 = s.color_masses()
    for _ in range(200):
        s.step()
    v = s.v.to_numpy()
    psi = s.psi_snapshot()
    check('A2 uniform phase stationary',
          float(np.abs(v).max()) < 1e-6 and float(np.abs(psi + 1).max())
          < 1e-3,
          f'max|v|={np.abs(v).max():.2e} psi_dev={np.abs(psi + 1).max():.1e}')

    # A3 — colour-mass conservation (periodic, no membranes/reservoirs).
    # Threshold 5e-6: the rhor/rhob accumulation fields are f32 (atomic
    # adds), so ~1e-7 relative roundoff over a few hundred steps is the
    # floor — the check guards against SYSTEMATIC leaks, not roundoff.
    m1 = s.color_masses()
    drift = max(abs((m1[0] - m0[0]) / max(m0[0], 1e-30)),
                abs((m1[1] - m0[1]) / max(m0[1], 1e-30)))
    check('A3 colour-mass conservation', drift < 5e-6,
          f'rel drift={drift:.2e}')

    # A4 — reservoir pins psi / rho at the target
    res = np.zeros((N, N, N), np.int8)
    res[:6, :, :] = 1
    reset(s, -np.ones((N, N, N)), solid0)
    s.set_reservoirs(res, 1.0, 1.05)          # red reservoir, rho = 1.05
    for _ in range(100):
        s.step()
    rho, _ = s.macro_snapshot()
    psi = s.psi_snapshot()
    check('A4 reservoir pins rho/psi',
          abs(float(rho[:6].mean()) - 1.05) < 1e-4
          and abs(float(psi[:6].mean()) - 1.0) < 1e-3,
          f'rho={rho[:6].mean():.5f} psi={psi[:6].mean():.4f}')

    # A5 — membrane blocks its colour (blue cannot cross a mem_b plane)
    reset(s, -np.ones((N, N, N)), solid0)
    psi0 = -np.ones((N, N, N), np.float32)
    psi0[:11, :, :] = 1.0                      # red left, blue right
    s.init(psi0, solid0)
    mem_b = np.zeros((N, N, N), np.int8)
    mem_b[10, :, :] = 1                        # blocks blue at x=10
    s.set_membranes(np.zeros_like(mem_b), mem_b)
    res_in = np.zeros((N, N, N), np.int8)
    res_in[:8, :, :] = 1
    res_out = np.zeros((N, N, N), np.int8)
    res_out[26:, :, :] = 1
    s.set_reservoirs(res_in, 1.0, 1.01)        # mild red push
    s.set_reservoirs(res_out, -1.0, 0.99)      # mild blue push
    for _ in range(400):
        s.step()
    psi = s.psi_snapshot()
    left = psi[:9, :, :]
    check('A5 membrane blocks blue (psi_left stays red)',
          float(left.min()) > 0.5,
          f'min psi[x<9]={left.min():.3f}')

    print(f'level A done in {time.time()-t00:.0f}s')
    if FAIL:
        print(f'FAIL: {FAIL}')
        sys.exit(1)
    print('LEVEL A: ALL PASS')


if __name__ == '__main__':
    main()
