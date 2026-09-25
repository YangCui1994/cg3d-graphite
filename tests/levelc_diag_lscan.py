"""Diagnostic (evidence script) 3: does the front speed scale as 1/L_tot (pure column
resistance) or saturate (a fixed extra resistance)?

Runs the SAME geometry/parameters as the production case but with a doubled
slit length (nx 262 -> 508, L_tot 246 -> 492) and reports the steady front
speed.  Pure plane-Poiseuille columns with the declared Pc predict V ~ 1/L;
a fixed extra resistance predicts V -> const.
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

NX = int(os.environ.get('DIAG_NX', '508'))
STEPS = int(os.environ.get('DIAG_STEPS', '16000'))
EVERY = 500
XOUT = NX - 5
g = L.build(NX, 26, 40, XOUT)
nx, ny, nz = g['nx'], g['ny'], g['nz']
g['x0q'], g['x1q'] = L.X_IN, XOUT
b, Ltot = 13.0, g['lt']
pc = L.SIGMA * np.cos(np.radians(30.0)) / b
v_pred = pc * 26 ** 2 / (12.0 * L.NU * Ltot)
print(f'nx={nx} L_tot={Ltot} Pc={pc:.5e} V_pred(1/L scaling)='
      f'{pc*26**2/(12*0.1*Ltot):.5e}', flush=True)

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
    xv, xc = L.extract_front(psi, g)
    rows.append((it, xv))
    if it % 4000 == 0:
        print(f'  it={it} x_vol={xv:.2f}', flush=True)

a = np.array(rows, float)
V_all = (a[-1, 1] - a[0, 1]) / (a[-1, 0] - a[0, 0])
m = a[:, 0] >= 8000
V_late = (a[-1, 1] - a[m][0, 1]) / (a[-1, 0] - a[m][0, 0])
print(f'\nV (whole) = {V_all:.5e}   V (t>8000) = {V_late:.5e}')
print(f'V_pred for this L     = {v_pred:.5e}   ratio = {V_late/v_pred:.3f}')
print(f'ratio to the L=246 case (V=3.857e-3): {V_late/3.857e-3:.3f}')
print('   pure-column prediction for doubling L: 0.500')
print('   fixed-extra-resistance prediction    : 0.4368/(0.8737+0.3538)'
      f' = {0.4368/(0.8737+0.3538):.3f}')
np.savez_compressed(os.path.join(OUT, 'diag_Lscan.npz'),
                    rows=a, V_late=[V_late], V_pred=[v_pred], Ltot=[Ltot])
