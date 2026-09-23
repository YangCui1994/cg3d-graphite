"""Diagnostic (evidence script): axial profiles of rho / psi / |v| in the V1 slab.

Same production code path as tests/levelc_imbibition.py (same geometry, same
solver call sequence) -- only extra read-only field dumps.
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

STEPS = int(os.environ.get('DIAG_STEPS', '8000'))
EVERY = int(os.environ.get('DIAG_EVERY', '1000'))
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
    vm = np.linalg.norm(v, axis=3)
    xv, xc = L.extract_front(psi, g)
    my, mz = y0 + (y1 - y0) // 2, nz // 2
    rows.append(dict(it=it, x_vol=xv, x_cross=xc,
                     psi=psi[:, my, mz].copy(), rho=rho[:, my, mz].copy(),
                     vx=v[:, my, mz, 0].copy(), vm=vm[:, my, mz].copy(),
                     psi_row=psi[:, y0, mz].copy(),
                     rho_liq=float(rho[L.X_RES0:L.X_RES1, y0:y1, :].mean()),
                     rho_gas=float(rho[g['xout'] + 1:nx - 2, y0:y1, :].mean())))
    print(f'  it={it} x_vol={xv:.1f} x_cross={xc:.1f}', flush=True)

out = os.path.join(OUT, 'diag_profiles.npz')
np.savez_compressed(out, rows=np.array(rows, dtype=object))
it = rows[-1]
print('\nfinal x_vol=%.1f' % it['x_vol'])
xf = int(round(it['x_vol']))
print('x     psi     rho      vx       |v|')
for x in range(max(L.X_IN, xf - 45), min(g['xout'], xf + 25), 2):
    print('%4d  %6.3f  %.7f  %9.2e  %9.2e'
          % (x, it['psi'][x], it['rho'][x], it['vx'][x], it['vm'][x]))
print('\nreservoir rho: liq=%.6f gas=%.6f' % (it['rho_liq'], it['rho_gas']))
print('wall-layer psi at x=xf-6..xf+6 (contact-angle proxy):',
      np.round(it['psi_row'][xf - 6:xf + 7], 3))
