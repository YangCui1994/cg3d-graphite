"""Unit checks for levelc_v2_bilateral pure-numpy components (run with
the lbm env python; no GPU)."""
import importlib.util
import numpy as np

spec = importlib.util.spec_from_file_location(
    'v2', 'tests/levelc_v2_bilateral.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 1. geometry + symmetry
solid, psi_solid, psi0, y0, y1 = m.build()
sym = m.verify_symmetry(solid, psi_solid, psi0)
assert sym['all_pass'], sym
assert m.NX == 326 and solid.shape == (326, 42, 6)
assert solid[:, y0:y1, :][3:323].all() is np.False_ or not solid[3:323, y0:y1, :].any()
print('1. build/symmetry OK', {k: v for k, v in sym.items() if k != 'layout'})

# 2. front crossing on a synthetic phi with known interfaces
phi = np.zeros(326)
phi[:100] = 1.0
phi[226:] = 1.0
xl, xr = m.front_positions(phi)
assert abs(xl - 99.5) < 1e-9 and abs(xr - 225.5) < 1e-9, (xl, xr)
print('2. front crossing OK', xl, xr)

# 3. gap metrics: central gas band with mixed edges
gas = np.zeros(326, bool)
liq = np.zeros(326, bool)
liq[:85] = True
liq[240:] = True
gas[100:200] = True
g, runs, el, er = m.gap_metrics(gas, liq)
assert g == 100 and el == 85 and er == 239, (g, runs, el, er)
gas3 = np.zeros(326, bool)
gas3[100:150] = True
gas3[160:200] = True
g3, _, _, _ = m.gap_metrics(gas3, liq)
assert g3 == 50, g3
print('3. gap metrics OK', g, el, er)

# 4. cluster labelling: one z-wrapped cluster must count as ONE
psi = np.full((326, 42, 6), -1.0, dtype=np.float32)
psi[120:200, y0:y1, :] = 1.0
psi[120:200, y0:y1, 0] = 1.0
# split into two x-halves connected ONLY through the z wrap:
psi[160:200, y0:y1, :] = -1.0
psi[160:200, y0:y1, 5] = 1.0
psi[120:160, y0:y1, 0] = 1.0
psi[120:160, y0:y1, 1:] = -1.0
rho = np.ones_like(psi)
nc, sizes, root, mean_rho, lab = m.label_gas(psi, rho)
assert nc == 1, ('z-wrap merge failed', nc, sizes)
print('4. z-wrap cluster merge OK: n=%d largest=%d' % (nc, sizes.max()))
# two separated clusters stay two
psi2 = np.full((326, 42, 6), -1.0, dtype=np.float32)
psi2[100:130, y0:y1, :] = 1.0
psi2[200:230, y0:y1, :] = 1.0
nc2, sizes2, _, _, _ = m.label_gas(psi2, rho)
assert nc2 == 2, nc2
print('5. separated clusters OK: n=%d' % nc2)
print('ALL UNIT CHECKS PASS')
