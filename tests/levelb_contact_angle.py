"""Level B regression — contact angle theta(psi_solid) (Plan_20260919_v2
Phase 3). Ported from the parent repo's
validation/validation_cg3d_contact_angle.py (2D/3D registry: psi_solid
-0.68 -> theta_liq ~ 30 deg, battery-electrolyte convention).

Estimator (same as parent post3d.contact_angle): centroid of the gas
(psi>0) blob; on probe planes, circle-fit the TOP contour of the
thresholded cross-section; theta_liq = arccos((cy - wall_row)/r).

Acceptance (quick mode): psi_solid = -0.68 reproduces theta_liq = 30 deg
within +-6 deg (registry band). With the PR-2 Compute_C fix this is
unchanged by construction (calibration ran at rho ~ 1).

Run:  python tests/levelb_contact_angle.py
Outputs -> tests_output/contact_angle/
"""
import os
import sys
import time

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

OUTROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'tests_output', 'contact_angle')
N, H, R0, WT = 48, 40, 16, 3
PSI_SOLID = -0.68
THETA_EXPECT = 30.0
TOL_DEG = 6.0


def make_floor_droplet_ic(n, h, R0, wt=WT):
    ax = np.arange(n)
    az = np.arange(n)
    ay = np.arange(h)
    X, Y, Z = np.meshgrid(ax, ay, az, indexing='ij')
    solid = np.zeros((n, h, n), dtype=np.int8)
    solid[:, :wt, :] = 1
    cx = cz = n / 2 - 0.5
    cy = wt - 0.5
    inside = (X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2 <= R0 * R0
    psi = np.where(inside & (solid == 0), 1.0, -1.0).astype(np.float32)
    return psi, solid


def theta_of(psi, wall_row):
    """Quiet 6-plane circle-fit theta (parent post3d estimator)."""
    mask = psi > 0.0
    if mask.sum() < 200:
        return float('nan'), []
    ix0, iy0, iz0 = [int(m) for m in np.array(np.where(mask)).mean(axis=1)]
    nx, ny, nz = psi.shape
    thetas = []
    probes = [('x', i) for i in (ix0 - 3, ix0, ix0 + 3) if 0 <= i < nx] + \
             [('z', i) for i in (iz0 - 3, iz0, iz0 + 3) if 0 <= i < nz]
    for axname, ip in probes:
        mk = mask[ip, :, :] if axname == 'x' else mask[:, :, ip].T
        pts = []
        for a in np.where(mk.any(axis=0))[0]:
            ys = np.where(mk[:, a])[0]
            if len(ys) >= 1:
                pts.append((a, ys.max()))
        pts = np.asarray(pts, dtype=float)
        if len(pts) < 8:
            continue

        def resid(q):
            return np.hypot(pts[:, 0] - q[0], pts[:, 1] - q[1]) - q[2]

        q0 = [pts[:, 0].mean(), pts[:, 1].mean() - np.ptp(pts[:, 1]) / 2,
              max(np.ptp(pts[:, 1]) / 2, 3.0) + 1e-3]
        try:
            sol = least_squares(resid, q0)
        except Exception:
            continue
        ca, cy, r = sol.x
        if not np.isfinite(r) or r <= 2:
            continue
        dy = cy - wall_row
        if abs(dy) >= r:
            continue
        # liquid-side angle (registry convention; see parent file header)
        thetas.append(float(np.degrees(np.arccos(np.clip(dy / r, -1, 1)))))
    if not thetas:
        return float('nan'), []
    return float(np.median(thetas)), thetas


def main():
    os.makedirs(OUTROOT, exist_ok=True)
    s = ColorGradientSolver3D(N, H, N, CapA=0.06)
    s.set_psi_solid(PSI_SOLID)
    psi0, solid = make_floor_droplet_ic(N, H, R0)
    s.init(psi0, solid)
    wall_row = 3.0

    th_prev, stable_for = None, 0
    theta = float('nan')
    t0 = time.time()
    for it in range(1, 12001):
        s.step()
        if it % 250 == 0:
            theta, _ = theta_of(s.psi_snapshot(), wall_row)
            if not np.isnan(theta) and th_prev is not None:
                if abs(theta - th_prev) < 0.3:
                    stable_for += 250
                else:
                    stable_for = 0
                if stable_for >= 1500 and it >= 4000:
                    break
            if not np.isnan(theta):
                th_prev = theta
    theta, all_th = theta_of(s.psi_snapshot(), wall_row)
    print(f'psi_solid={PSI_SOLID}: theta_liq = {theta:.1f} deg '
          f'(expect {THETA_EXPECT:.0f} +- {TOL_DEG:.0f}); steps={it}, '
          f'wall={time.time()-t0:.0f}s')
    np.save(os.path.join(OUTROOT, 'theta_data.npy'),
            np.array([PSI_SOLID, theta, it]))
    if not (abs(theta - THETA_EXPECT) <= TOL_DEG):
        print('FAIL: theta outside registry band')
        sys.exit(1)
    print('LEVEL B (contact angle): PASS — registry reproduced')


if __name__ == '__main__':
    main()
