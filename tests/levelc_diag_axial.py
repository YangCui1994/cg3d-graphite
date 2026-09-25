"""Diagnostic (evidence script) 2: full-range axial rho/psi/|v| profiles.

Same production code path as tests/levelc_imbibition.py.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'tests_output', 'levelc_diag')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(HERE, '..'))
import levelc_imbibition as L  # noqa: E402
from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

STEPS = int(os.environ.get('DIAG_STEPS', '20000'))
EVERY = int(os.environ.get('DIAG_EVERY', '4000'))
g = L.build(262, 26, 40, 257)
nx, ny, nz = g['nx'], g['ny'], g['nz']
y0, y1 = g['y0'], g['y1']
g['x0q'], g['x1q'] = L.X_IN, g['xout']

s = ColorGradientSolver3D(nx, ny, nz, niu_l=L.NU, niu_g=L.NU, CapA=L.CAPA)
s.set_psi_solid_field(g['psi_solid'])
s.set_membranes(g['mem_r'], g['mem_b'])
s.set_reservoirs(g['liq_res'], -1.0, 1.0)
s.set_reservoirs(g['gas_res'], 1.0, 1.0)
s.init(g['psi0'], g['solid'])

rows = []
for it in range(1, STEPS + 1):
    s.step()
    if it % EVERY:
        continue
    psi = s.psi_snapshot()
    rho, v = s.macro_snapshot()
    xv, xc = L.extract_front(psi, g)
    m = (g['solid'] == 0)
    rows.append(dict(
        it=it, x_vol=xv,
        rho_mid=rho[:, 1 + g['hy'] // 2, nz // 2].copy(),
        rho_col=rho[:, y0:y1, :].mean(axis=(1, 2)).copy(),
        psi_col=psi[:, y0:y1, :].mean(axis=(1, 2)).copy(),
        vm_mid=np.linalg.norm(v, axis=3)[:, 1 + g['hy'] // 2, nz // 2].copy(),
        vx_col=v[:, y0:y1, :, 0].mean(axis=(1, 2)).copy()))
    print(f'  it={it} x_vol={xv:.1f}', flush=True)

np.savez_compressed(os.path.join(OUT, 'diag_full.npz'),
                    rows=np.array(rows, dtype=object))

r = rows[-1]
xk = int(round(r['x_vol']))
xs = np.arange(nx)
rc, rm = r['rho_col'], r['rho_mid']
print(f'\nfinal x_vol={xk}')
print('densities: reservoir(liq) rho=%.6f   gas res rho=%.6f'
      % (rc[L.X_RES0:L.X_RES1].mean(), rc[g['xout'] + 1:g['xout'] + 4].mean()))
for lab, lo, hi in (('liquid 30..x-25', L.X_IN + 20, max(L.X_IN + 40, xk - 25)),
                    ('gas x+25..250', min(xk + 25, 250), 255)):
    m = (xs >= lo) & (xs <= hi) & (xs >= L.X_IN) & (xs < g['xout'])
    if m.sum() > 10:
        p = np.polyfit(xs[m], rc[m], 1)
        print(f'{lab}: rho = {p[0]:+.3e}*x + {p[1]:.6f}  -> dp/dx = '
              f'{p[0]/3:+.3e} /lu   (x {lo}..{hi}, n={m.sum()})')
print('mean rho: liquid[%d:%d]=%.6f  gas[%d:%d]=%.6f'
      % (L.X_IN + 20, xk - 25, rc[L.X_IN + 20:xk - 25].mean(),
         xk + 25, 254, rc[xk + 25:254].mean()))
print('cross-section vs midline rho diff (liquid):',
      np.round((rc - rm)[L.X_IN + 20:xk - 25].mean(), 8))
print('cross-section vs midline rho diff (gas):',
      np.round((rc - rm)[xk + 25:254].mean(), 8))
print('\nx    rho_col   rho_mid   psi_col   vx_col    |v|mid')
for x in list(range(L.X_IN + 10, xk - 20, 15)) + list(range(xk - 8, xk + 9, 4)) \
        + list(range(xk + 20, 255, 30)):
    print('%4d  %.7f %.7f  %+.3f  %+.3e  %.3e'
          % (x, rc[x], rm[x], r['psi_col'][x], r['vx_col'][x], r['vm_mid'][x]))
