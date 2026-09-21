"""CG3D-IMB-001 direct-imbibition runtime tests (run from repo root):

  python tests/test_direct_imbibition_runtime.py   (exit 0 = pass)

CPU arch (LBM_ARCH=cpu), ONE solver instance total (JIT rule): case
order re-initialises the same instance via set_* + init.

Parts:
  A  OpenSystem(orientation='imbibition') end-to-end construction:
     V4 — constructor pins the reservoirs at delta=0: left psi=-1
     rho=1.0, right psi=+1 rho=1.0 (equal nominal densities); solver
     psi after init == build_layout psi0; membrane masks land on the
     solver as placed by build_layout.
  B  Optional smoke (task §6.E): 60 steps from the fresh direct-
     imbibition IC — no NaN / structural blow-up.  NOT physical
     validation.
  A2 set_ladder(d!=0) probe: densities split symmetrically (documents
     that the delta=0 baseline is the zero-bias point); restored to 0.
  C1 V2 behavioural, left membrane: with reservoirs OFF, blue (liquid)
     left of the inlet membrane ENTERS the domain through mem_r while
     red (gas) never crosses to the inlet side.
  C2 V2 behavioural, right membrane: red (gas) left of the outlet
     membrane EXITS through mem_b into the right side while blue
     (liquid) never crosses to the interior side.
"""
import os
import sys

os.environ.setdefault('LBM_ARCH', 'cpu')   # precede the solver import

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
os.chdir(REPO)

import numpy as np                                          # noqa: E402
from cg3d import OpenSystem, checkpoint                     # noqa: E402
from cg3d.protocol import build_layout                      # noqa: E402

FAIL = []


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name
          + ('  ' + detail if detail else ''), flush=True)
    if not cond:
        FAIL.append(name)


def make_synth_geo(nx=48, ny=24, nz=24):
    """Same synthetic buffered geometry as the layout test."""
    solid = np.zeros((nx, ny, nz), dtype=np.int8)
    y, z = np.meshgrid(np.arange(ny), np.arange(nz), indexing='ij')
    solid[16:32, (y % 6 < 2) & (z % 6 < 2)] = 1
    return solid


os.makedirs('tests_output', exist_ok=True)
geo_path = os.path.join('tests_output', 'imb_synth_geo_48.npz')
solid_in = make_synth_geo()
np.savez(geo_path, solid=solid_in,
         meta=np.array(['synthetic buffered pillar geo for CG3D-IMB-001 '
                        'tests: real structure x=[16,32)']))

X_IN, X_OUT = 11, 37

# ---- A: construction end-to-end --------------------------------------
sys_ = OpenSystem(geo_path, capa=0.06, psi_solid=-0.68,
                  orientation='imbibition', prewet_layers=4)
s = sys_.s

res_psi = s.res_psi.to_numpy()
res_rho = s.res_rho.to_numpy()
rin, rout = sys_.res_in.astype(bool), sys_.res_out.astype(bool)
check('A1 V4 left reservoir pins psi=-1 (liquid) at rho=1.0',
      bool((res_psi[rin] == -1.0).all()) and np.allclose(res_rho[rin], 1.0))
check('A2 V4 right reservoir pins psi=+1 (gas) at rho=1.0 (EQUAL '
      'nominal densities -> zero-bias baseline)',
      bool((res_psi[rout] == +1.0).all()) and np.allclose(res_rho[rout], 1.0))
check('A3 V4 no other reservoir cells', float((s.res_mask.to_numpy()
      .astype(bool)).sum()) == float(rin.sum() + rout.sum()))

lay = build_layout(solid_in, orientation='imbibition', prewet_layers=4)
check('A4 solver psi after init == build_layout psi0 (IC fidelity)',
      np.array_equal(s.psi_snapshot(), lay['psi0']))
check('A5 membranes on solver: mem_r only at x=11, mem_b only at x=37',
      np.array_equal(np.unique(np.nonzero(s.mem_r.to_numpy())[0]), [X_IN])
      and np.array_equal(np.unique(np.nonzero(s.mem_b.to_numpy())[0]),
                         [X_OUT]))

# ---- B: 60-step smoke from the fresh direct-imbibition IC -------------
ok_smoke, psi_min, psi_max = True, 0.0, 0.0
for it in range(1, 61):
    s.step()
    if it % 10 == 0:
        rho, _ = s.macro_snapshot()
        psi = s.psi_snapshot()
        psi_min, psi_max = float(psi.min()), float(psi.max())
        if not (np.isfinite(rho).all() and np.isfinite(psi).all()):
            ok_smoke = False
            break
psi_dom = s.psi_snapshot()[sys_.dom]
m = sys_.measure()
check('B1 smoke 60 steps: rho/psi finite, no structural failure',
      ok_smoke, f'psi range [{psi_min:.3f},{psi_max:.3f}] '
                f's_nw={m["s_nw"]:.4f} umax={m["umax"]:.5f}')
check('B2 smoke: psi bounded (|psi| <= 1.3)', psi_min > -1.3 and psi_max < 1.3)
check('B3 smoke: left reservoir region still liquid-dominant (capillary '
      'drive acts on the pre-wet front, not the pinned source)',
      float((psi_dom[0] < 0).mean()) > 0.9)

# ---- A2: set_ladder(d) probe (documents the zero-bias point) ---------
sys_.set_ladder(0.06)
res_rho = s.res_rho.to_numpy()
check('A6 set_ladder(0.06): left 1.03 / right 0.97 (d=0 is the equal-'
      'density point; d>0 = pressure-assisted, future work)',
      np.allclose(res_rho[rin], 1.03) and np.allclose(res_rho[rout], 0.97))
sys_.set_ladder(0.0)

# ---- C: membrane transport behaviour (reservoirs OFF) ----------------
# Re-initialise the SAME instance (JIT rule): keep solid/membranes, turn
# reservoirs off, re-seed psi per case.
solidL = sys_.solid
nx, ny, nz = sys_.shape
s.res_mask.from_numpy(np.zeros((nx, ny, nz), np.int8))
s.use_reservoirs = False
checkpoint.zero_counters(s)

# C1: LEFT membrane (mem_r at x=11): blue left of it, red right of it.
#   mem_r on the plane blocks RED: red packets targeting x=11 bounce
#   (lbm_solver_cg3d.py streaming1 / colour-stream branches), blue
#   packets land freely -> liquid crosses INTO the domain, gas cannot.
psi_c1 = np.where(solidL == 0, 1.0, 0.0).astype(np.float32)   # all gas
psi_c1[:X_IN + 1] = np.where(                    # [3,11] liquid pores
    (solidL == 0)[:X_IN + 1], -1.0, 0.0).astype(np.float32)
s.init(psi_c1, solidL)
for _ in range(40):
    s.step()
rho_r = s.rho_r.to_numpy()
rho_b = s.rho_b.to_numpy()
check('C1a red (gas) NEVER crossed the left membrane (rho_r mass on the '
      'inlet side ~ 0)',
      float(rho_r[:X_IN + 1].sum()) < 1e-6,
      f'mass={float(rho_r[:X_IN + 1].sum()):.3e}')
check('C1b blue (liquid) entered the domain through mem_r',
      float(rho_b[X_IN + 1].sum()) > 5.0,
      f'blue mass at x=12: {float(rho_b[X_IN + 1].sum()):.1f}')

# C2: RIGHT membrane (mem_b at x=37): red (gas) in the interior, blue
#   (liquid) beyond it.  mem_b on the plane blocks BLUE: blue packets
#   targeting x=37 bounce, red packets land freely -> gas crosses OUT
#   to the right side (mirrors the real setup: gas exits to the gas
#   reservoir), liquid cannot cross back into the interior.
psi_c2 = np.where(solidL == 0, 1.0, 0.0).astype(np.float32)    # all gas
psi_c2[X_OUT + 1:] = np.where(                  # (38,45) liquid pores
    (solidL == 0)[X_OUT + 1:], -1.0, 0.0).astype(np.float32)
s.init(psi_c2, solidL)
for _ in range(40):
    s.step()
rho_b = s.rho_b.to_numpy()
rho_r = s.rho_r.to_numpy()
check('C2a blue (liquid) NEVER crossed the right membrane into the '
      'interior (rho_b mass on the interior side ~ 0)',
      float(rho_b[:X_OUT].sum()) < 1e-6,
      f'mass={float(rho_b[:X_OUT].sum()):.3e}')
check('C2b red (gas) crossed mem_b into the outlet side -> gas can exit',
      float(rho_r[X_OUT + 1:].sum()) > 5.0,
      f'red mass x>=38: {float(rho_r[X_OUT + 1:].sum()):.1f}')

print(('ALL PASS' if not FAIL else f'FAILURES: {FAIL}'))
sys.exit(1 if FAIL else 0)
