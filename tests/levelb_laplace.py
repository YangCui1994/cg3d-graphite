"""Level B regression — Laplace law dP = 2 sigma / R (Plan_20260919_v2
Phase 3). Ported from the parent repo's validation/validation_cg3d_laplace.py
(2phase/, P1-validated: sigma = 1.012 CapA, R^2 = 1.0000 over 13 droplets).

Restructured for the JIT single-instance rule: the parent created a NEW
solver per (CapA, R) — each pays ~5.5 min JIT on this machine. This port
uses ONE fixed-shape instance (n = 80) re-initialised per case.

Acceptance (quick mode): sigma_fit within 3% of 1.012*CapA and fit
R^2 >= 0.999.  With the PR-2 fixes this must reproduce the parent's
calibration: Laplace runs at rho ~ 1 +- 2 sigma/R (|dP| ~ 6e-3), where the
normalized Compute_C criterion is identical to the old one.

Run:  python tests/levelb_laplace.py            (quick: CapA 0.06)
      python tests/levelb_laplace.py --full     (parent sweep)
Outputs -> tests_output/laplace/
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

CS2 = 1.0 / 3.0
OUTROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'tests_output', 'laplace')
SIGMA_PER_CAPA = 1.012          # parent calibration (13-droplet fit)


def make_droplet_ic(n, R, offset=0.0):
    ax = np.arange(n)
    X, Y, Z = np.meshgrid(ax, ax, ax, indexing='ij')
    c = n / 2 - 0.5 + offset
    psi0 = np.where((X - c) ** 2 + (Y - c) ** 2 + (Z - c) ** 2 <= R * R,
                    1.0, -1.0)
    return psi0.astype(np.float32), X, Y, Z, c


def measure_dP(s, X, Y, Z, c, R):
    rho, _ = s.macro_snapshot()
    r = np.sqrt((X - c) ** 2 + (Y - c) ** 2 + (Z - c) ** 2)
    return (CS2 * (rho[r < R * 0.5].mean() - rho[r > R * 1.5].mean()),
            float(rho[r < R * 0.5].mean()), float(rho[r > R * 1.5].mean()))


def run_case(s, n, R, CapA, offset, steps_max, check_every, stable_steps,
             tol, X, Y, Z):
    psi0, _, _, _, c = make_droplet_ic(n, R, offset)
    solid = np.zeros((n, n, n), np.int8)
    s.set_surface_tension(CapA)
    s.init(psi0, solid)
    dP_prev, stable_for, converged = None, 0, False
    t0 = time.time()
    for it in range(1, steps_max + 1):
        s.step()
        if it % check_every == 0:
            dP, _, _ = measure_dP(s, X, Y, Z, c, R)
            if dP_prev is not None and abs(dP) > 0:
                rel = abs(dP - dP_prev) / abs(dP)
                stable_for = stable_for + check_every if rel < tol else 0
                if it >= stable_steps and stable_for >= stable_steps:
                    converged = True
                    break
            dP_prev = dP
    dP, rho_in, rho_out = measure_dP(s, X, Y, Z, c, R)
    psi = s.psi_snapshot()
    R_eff = float((3.0 * (psi > 0).sum() / (4.0 * np.pi)) ** (1.0 / 3.0))
    return dict(R=R, CapA=CapA, offset=offset, dP=dP, R_eff=R_eff,
                converged=converged, steps=it,
                wall=round(time.time() - t0, 1))


def linear_fit(x, y):
    A = np.vstack([x, np.ones_like(x)]).T
    (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = a * x + b
    r2 = 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return a, b, r2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--full', action='store_true',
                    help='parent sweep (4 CapA x 3 radii + probes)')
    args = ap.parse_args()
    os.makedirs(OUTROOT, exist_ok=True)

    capas = [0.02, 0.06, 0.136, 0.2] if args.full else [0.06]
    radii = [16, 20, 25] if args.full else [14, 18, 22]
    n = 4 * max(radii) if not args.full else 4 * max(radii)
    n = max(n, 80) if not args.full else n

    s = ColorGradientSolver3D(n, n, n)         # ONE instance, re-init per case
    ax = np.arange(n)
    X, Y, Z = np.meshgrid(ax, ax, ax, indexing='ij')

    rows = []
    for CapA in capas:
        for R in radii:
            print(f'=== CapA={CapA}, R={R} (n={n}) ===', flush=True)
            row = run_case(s, n, R, CapA, 0.0, 20000, 500, 1500, 0.004,
                           X, Y, Z)
            rows.append(row)
            print('  dP=%.5f R_eff=%.2f conv=%s steps=%d wall=%.0fs'
                  % (row['dP'], row['R_eff'], row['converged'],
                     row['steps'], row['wall']), flush=True)
        # anisotropy probe: middle radius, half-node offset
        R = radii[len(radii) // 2]
        row = run_case(s, n, R, CapA, 0.5, 20000, 500, 1500, 0.004, X, Y, Z)
        rows.append(row)
        print('  [offset probe] dP=%.5f' % row['dP'], flush=True)

    results = {}
    ok_all = True
    for CapA in capas:
        sel = [r for r in rows if r['CapA'] == CapA and r['offset'] == 0.0]
        x = np.array([1.0 / r['R_eff'] for r in sel])
        y = np.array([r['dP'] for r in sel])
        a, b, r2 = linear_fit(x, y)
        sigma = a / 2.0
        expect = SIGMA_PER_CAPA * CapA
        rel = abs(sigma / expect - 1.0) if expect > 0 else 1.0
        results[CapA] = dict(sigma=sigma, r2=r2, intercept=b, rel_err=rel)
        print(f'CapA={CapA}: sigma={sigma:.4f} (expect {expect:.4f}, '
              f'rel {rel*100:.2f}%), R2={r2:.5f}, intercept={b:.5f}')
        ok_all &= (rel < 0.03) and (r2 >= 0.999)

    np.savez(os.path.join(OUTROOT, 'laplace_data.npz'),
             rows=np.array(rows, dtype=object),
             sigma=np.array([results[c]['sigma'] for c in capas]),
             capa=np.array(capas))
    if not ok_all:
        print('FAIL: sigma deviates >3% from 1.012*CapA or R2 < 0.999')
        sys.exit(1)
    print('LEVEL B (Laplace): PASS — sigma calibration reproduced')


if __name__ == '__main__':
    main()
