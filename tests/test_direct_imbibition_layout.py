"""CG3D-IMB-001 direct-imbibition layout tests (run from repo root):

  python tests/test_direct_imbibition_layout.py   (exit 0 = pass)

Pure NumPy (no solver, no Taichi): checks cg3d.protocol.build_layout
for both orientations on a synthetic buffered geometry.

Parts:
  L1  V1 — imbibition IC layout, N=4 (left reservoir/membrane/buffer +
      first 4 real pore layers liquid, rest gas, solids untouched)
  L2  V1 — imbibition IC layout, N=10 (second N value)
  L3  R5 — prewet-layers validation (0 / too-large / None rejected)
  L4  V3 — drainage regression: the drainage branch reproduces the
      ORIGINAL OpenSystem.__init__ layout statements verbatim (expected
      arrays recomputed below from the pre-change code, independent of
      build_layout)
  L5  V2 (structural half) — membrane orientation per phase: imbibition
      places mem_r at the inlet (blocks gas, liquid enters) and mem_b at
      the outlet (blocks liquid, gas leaves); drainage the opposite.
      Behavioural confirmation runs in test_direct_imbibition_runtime.py.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import numpy as np                                          # noqa: E402
from cg3d.protocol import build_layout                      # noqa: E402

FAIL = []


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name
          + ('  ' + detail if detail else ''), flush=True)
    if not cond:
        FAIL.append(name)


def make_synth_geo(nx=48, ny=24, nz=24):
    """Synthetic buffered geometry mirroring geo_graphite_228b14's
    structure: walls+reservoir bands+membrane planes+left buffer open
    pore [0,16), pillar array (real structure) x=[16,32), right buffer
    open pore [32,48).  Pillars leave >=4 lu channels (smoke-safe)."""
    solid = np.zeros((nx, ny, nz), dtype=np.int8)
    y, z = np.meshgrid(np.arange(ny), np.arange(nz), indexing='ij')
    pillars = solid[16:32].copy()
    pillars[:, (y % 6 < 2) & (z % 6 < 2)] = 1
    solid[16:32] = pillars
    return solid


geo = make_synth_geo()
WT, RT = 3, 8               # wall_t / res_thick (driver defaults)
X_IN, X_OUT = WT + RT, 48 - WT - RT          # 11, 37
X_R0, X_R1 = 16, 32                          # real structure (from solid)

# ---- L1: imbibition IC, N=4 -----------------------------------------
lay4 = build_layout(geo, orientation='imbibition', prewet_layers=4)
psi4 = lay4['psi0']
pore = lay4['solid'] == 0          # WALLED pore map (walls must stay psi=0)
solidL = lay4['solid']
liq_zone = np.zeros(48, bool)
liq_zone[WT:X_R0 + 4] = True                  # [3, 20): res+mem+buffer+4 layers
ok_zone = True
for x in range(48):
    if not pore[x].any():
        continue                     # wall slabs: no pore nodes to check
    expect = -1.0 if liq_zone[x] else 1.0
    got = np.unique(psi4[x][pore[x]])
    if not (len(got) == 1 and got[0] == expect):
        ok_zone = False
        print(f'  L1 mismatch at x={x}: pore psi={got} expected {expect}')
check('L1a liquid zones (res+mem+buffer+prewet N=4) / gas elsewhere',
      ok_zone)
check('L1b membrane plane x=11 pores liquid (IC continuous into buffer)',
      bool((psi4[X_IN][pore[X_IN]] == -1.0).all()))
check('L1c outlet plane x=37 + right buffer/reservoir pores gas',
      bool((psi4[X_OUT][pore[X_OUT]] == 1.0).all())
      and bool((psi4[X_OUT + 1:][pore[X_OUT + 1:]] == 1.0).all()))
check('L1d solids carry psi=0 (walls + pillars)',
      bool((psi4[solidL == 1] == 0.0).all()))
check('L1e real-domain bounds derived from solid field',
      (lay4['x_real_lo'], lay4['x_real_hi']) == (X_R0, X_R1))
check('L1f walls rewritten solid in returned solid map',
      bool((solidL[:WT] == 1).all() and (solidL[-WT:] == 1).all()))

# ---- L2: imbibition IC, N=10 ----------------------------------------
lay10 = build_layout(geo, orientation='imbibition', prewet_layers=10)
psi10 = lay10['psi0']
pore10 = lay10['solid'] == 0
ok10 = (bool((psi10[WT:X_R0 + 10][pore10[WT:X_R0 + 10]] == -1.0).all())
        and bool((psi10[X_R0 + 10:][pore10[X_R0 + 10:]] == 1.0).all()))
check('L2 second N value: liquid [3,26), gas [26,48)', ok10)

# ---- L3: prewet validation ------------------------------------------
for bad, why in ((0, 'zero'), (17, 'beyond real width 16'),
                 (None, 'missing')):
    try:
        build_layout(geo, orientation='imbibition', prewet_layers=bad)
        check(f'L3 reject prewet_layers={bad!r}', False, 'no ValueError')
    except ValueError:
        check(f'L3 reject prewet_layers={bad!r} ({why})', True)
try:
    build_layout(geo, orientation='sideways')
    check('L3 reject unknown orientation', False, 'no ValueError')
except ValueError:
    check('L3 reject unknown orientation', True)
try:
    build_layout(np.zeros((48, 24, 24), np.int8),
                 orientation='imbibition', prewet_layers=4)
    check('L3 reject all-open geometry (no real structure)', False)
except ValueError:
    check('L3 reject all-open geometry (no real structure)', True)

# ---- L4: drainage regression vs ORIGINAL statements ------------------
# Expected arrays recomputed here from the pre-CG3D-IMB-001
# OpenSystem.__init__ (git: origin/master cg3d/protocol.py), i.e. an
# oracle independent of build_layout.
solid_full = geo
nx = solid_full.shape[0]
pore_full = solid_full == 0
wt, rt = WT, RT
x_in, x_out = wt + rt, nx - wt - rt
solid = solid_full.copy()
solid[:wt] = 1
solid[nx - wt:] = 1
exp_psi0 = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
exp_psi0[wt:x_in + 1] = np.where(
    pore_full[wt:x_in + 1], 1.0, 0.0).astype(np.float32)
exp_mem_r = np.zeros_like(solid)
exp_mem_b = np.zeros_like(solid)
exp_mem_b[x_in] = 1
exp_mem_r[x_out] = 1
exp_res_in = np.zeros_like(solid)
exp_res_in[wt:x_in] = 1
exp_res_out = np.zeros_like(solid)
exp_res_out[x_out + 1:nx - wt] = 1

layD = build_layout(geo, orientation='drainage')
check('L4a drainage psi0 identical to original statements',
      np.array_equal(layD['psi0'], exp_psi0))
check('L4b drainage membranes identical (mem_b@in, mem_r@out)',
      np.array_equal(layD['mem_b'], exp_mem_b)
      and np.array_equal(layD['mem_r'], exp_mem_r))
check('L4c drainage reservoir masks identical',
      np.array_equal(layD['res_in'], exp_res_in)
      and np.array_equal(layD['res_out'], exp_res_out))
check('L4d drainage dom/pore_cells identical',
      layD['dom'] == slice(x_in + 1, x_out)
      and layD['pore_cells'] == float(pore_full[x_in + 1:x_out].sum()))
check('L4e drainage ignores prewet_layers (kwarg accepted, unused)',
      build_layout(geo, orientation='drainage',
                   prewet_layers=7)['psi0'].shape == exp_psi0.shape
      and np.array_equal(build_layout(geo, orientation='drainage',
                                      prewet_layers=7)['psi0'], exp_psi0))

# ---- L5: membrane orientation per phase ------------------------------
imb_mems = (lay4['mem_r'], lay4['mem_b'])
drn_mems = (layD['mem_r'], layD['mem_b'])
check('L5a imbibition: mem_r plane at inlet x=11 only (blocks RED/gas; '
      'liquid enters), mem_b at outlet x=37 only (blocks BLUE/liquid; '
      'gas leaves)',
      np.array_equal(np.unique(np.nonzero(lay4['mem_r'])[0]), [X_IN])
      and np.array_equal(np.unique(np.nonzero(lay4['mem_b'])[0]), [X_OUT]))
check('L5b drainage: mem_b at inlet x=11, mem_r at outlet x=37 '
      '(unchanged)',
      np.array_equal(np.unique(np.nonzero(drn_mems[1])[0]), [X_IN])
      and np.array_equal(np.unique(np.nonzero(drn_mems[0])[0]), [X_OUT]))

print(('ALL PASS' if not FAIL else f'FAILURES: {FAIL}'))
sys.exit(1 if FAIL else 0)
