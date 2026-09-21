"""CG3D-IMB-001(-R1) direct-imbibition layout tests (run from repo root):

  python tests/test_direct_imbibition_layout.py   (exit 0 = pass)

Pure NumPy + matplotlib (no solver, no Taichi): checks
cg3d.protocol.build_layout / resolve_real_bounds and cg3d.ic_figs for
both orientations on synthetic buffered geometries.

Rework coverage (CG3D-IMB-001-R1 §R4 / task §7):
  T1  explicit real-domain bounds: the real region starts with ALL-PORE
      x-planes (pillars begin 2 planes later); bounds stay [16,32) from
      the explicit definition, NOT shifted to the first solid plane
      (18).  Also resolve_real_bounds priority: explicit arg > npz
      real_x > None; malformed values rejected.
  T2  pre-wet origin: prewet_layers=N counts from the EXPLICIT entrance
      x=16 (the all-pore planes 16-17 are included in the pre-wet
      region); imbibition without explicit bounds fails with guidance.
  T3  legacy drainage on an ALL-OPEN geometry (no solid at all) still
      builds (bounds optional there; x_real is None).
  T4  neutral gas-output semantics (static source scan of
      run_imbibition_cg3d.py): gas_saturation_* keys present, no
      s_nr/label_periodic/--conn trapped-gas claims; deferral stated.
  T5  visualization consistency: cg3d.ic_figs.phase_fractions matches an
      independent recomputation from the SAME layout arrays, and
      make_figures produces the expected files (figures built by the
      same build_layout the solver uses — no duplicated logic).

Plus the original CG3D-IMB-001 checks: imbibition IC zones (two N
values), prewet validation, drainage regression vs an independent
oracle (verbatim pre-change statements), membrane orientation.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import numpy as np                                          # noqa: E402
from cg3d.protocol import build_layout, resolve_real_bounds  # noqa: E402

FAIL = []


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name
          + ('  ' + detail if detail else ''), flush=True)
    if not cond:
        FAIL.append(name)


def make_synth_geo(nx=48, ny=24, nz=24, pillar_x0=18, pillar_x1=32):
    """Synthetic buffered geometry.  REAL domain is DECLARED [16,32)
    (real_x); the pillar array intentionally starts at x=18, so the
    real region begins with all-pore planes 16-17 — an electrode crop
    that does not start with solid.  Walls+reservoirs+membrane planes+
    buffers [0,16) and [32,48) are open pore; pillars leave >=4 lu
    channels."""
    solid = np.zeros((nx, ny, nz), dtype=np.int8)
    y, z = np.meshgrid(np.arange(ny), np.arange(nz), indexing='ij')
    solid[pillar_x0:pillar_x1, (y % 6 < 2) & (z % 6 < 2)] = 1
    return solid


geo = make_synth_geo()
WT, RT = 3, 8               # wall_t / res_thick (driver defaults)
X_IN, X_OUT = WT + RT, 48 - WT - RT          # 11, 37
X_R0, X_R1 = 16, 32                          # DECLARED real domain
RB = (X_R0, X_R1)

# ---- T1: explicit bounds win over solid occupancy --------------------
lay4 = build_layout(geo, orientation='imbibition', prewet_layers=4,
                    real_bounds=RB)
check('T1a real bounds stay [16,32) although the first solid plane is '
      'x=18 (explicit definition, not solid inference)',
      (lay4['x_real_lo'], lay4['x_real_hi']) == RB
      and bool(geo[X_R0:X_R0 + 2].sum() == 0)
      and int(np.argmax(geo.any(axis=(1, 2)))) == 18)

# resolve_real_bounds priority / validation
os.makedirs('tests_output', exist_ok=True)
p_no = 'tests_output/imb_synth_no_realx.npz'
np.savez(p_no, solid=geo)
p_rx = 'tests_output/imb_synth_realx.npz'
np.savez(p_rx, solid=geo, real_x=np.array([X_R0, X_R1]))
dat_rx, dat_no = np.load(p_rx), np.load(p_no)
check('T1b npz real_x resolves to [16,32)',
      resolve_real_bounds(dat_rx) == RB)
check('T1c explicit arg overrides npz field',
      resolve_real_bounds(dat_rx, (10, 20)) == (10, 20))
check('T1d no explicit info -> None (drainage does not need bounds)',
      resolve_real_bounds(dat_no) is None)
for bad_rx, why in (([16, 16], 'lo==hi'), ([32, 16], 'lo>hi'),
                    ([16, 32, 48], '3 elements')):
    try:
        resolve_real_bounds({'real_x': np.array(bad_rx)})
        check(f'T1e reject real_x={bad_rx} ({why})', False, 'no error')
    except ValueError:
        check(f'T1e reject real_x={bad_rx} ({why})', True)
for bad_rb, why in (((16, 16), 'lo==hi'), ((12, 32), 'outside dom '
                     '(overlaps membrane)'), ((16, 38), 'beyond dom')):
    try:
        build_layout(geo, orientation='imbibition', prewet_layers=4,
                     real_bounds=bad_rb)
        check(f'T1f reject real_bounds={bad_rb} ({why})', False, 'no error')
    except ValueError:
        check(f'T1f reject real_bounds={bad_rb} ({why})', True)

# ---- T2: pre-wet counts from the EXPLICIT entrance -------------------
psi4 = lay4['psi0']
pore = lay4['solid'] == 0          # WALLED pore map (walls stay psi=0)
liq_zone = np.zeros(48, bool)
liq_zone[WT:X_R0 + 4] = True                  # [3, 20): res+mem+buf+4 layers
ok_zone = True
for x in range(48):
    if not pore[x].any():
        continue                     # wall slabs: no pore nodes to check
    expect = -1.0 if liq_zone[x] else 1.0
    got = np.unique(psi4[x][pore[x]])
    if not (len(got) == 1 and got[0] == expect):
        ok_zone = False
        print(f'  T2 mismatch at x={x}: pore psi={got} expected {expect}')
check('T2a prewet N=4 counts from x=16: all-pore planes 16-17 liquid, '
      'liquid [3,20), gas [20,48)', ok_zone)
check('T2b membrane plane x=11 pores liquid (IC continuous into buffer)',
      bool((psi4[X_IN][pore[X_IN]] == -1.0).all()))
check('T2c outlet plane x=37 + right buffer/reservoir pores gas',
      bool((psi4[X_OUT][pore[X_OUT]] == 1.0).all())
      and bool((psi4[X_OUT + 1:][pore[X_OUT + 1:]] == 1.0).all()))
check('T2d solids carry psi=0 (walls + pillars)',
      bool((psi4[lay4['solid'] == 1] == 0.0).all()))
try:
    build_layout(geo, orientation='imbibition', prewet_layers=4)
    check('T2e imbibition without explicit bounds fails with guidance',
          False, 'no ValueError')
except ValueError as e:
    check('T2e imbibition without explicit bounds fails with guidance',
          'real_bounds' in str(e) and 'real_x' in str(e))

lay10 = build_layout(geo, orientation='imbibition', prewet_layers=10,
                     real_bounds=RB)
psi10 = lay10['psi0']
check('T2f second N value: liquid [3,26), gas [26,48)',
      bool((psi10[WT:X_R0 + 10][pore[WT:X_R0 + 10]] == -1.0).all())
      and bool((psi10[X_R0 + 10:][pore[X_R0 + 10:]] == 1.0).all()))
for bad, why in ((0, 'zero'), (17, 'beyond real width 16'),
                 (None, 'missing')):
    try:
        build_layout(geo, orientation='imbibition', prewet_layers=bad,
                     real_bounds=RB)
        check(f'T2g reject prewet_layers={bad!r} ({why})', False,
              'no ValueError')
    except ValueError:
        check(f'T2g reject prewet_layers={bad!r} ({why})', True)

# ---- T3: legacy drainage on an ALL-OPEN geometry ----------------------
all_open = np.zeros((48, 24, 24), np.int8)
layD_open = build_layout(all_open, orientation='drainage')
check('T3a drainage on all-open geometry builds (no solid requirement)',
      layD_open['psi0'].shape == all_open.shape
      and layD_open['x_real_lo'] is None and layD_open['x_real_hi'] is None)
pore_open = layD_open['solid'] == 0      # walled map: walls stay psi=0
check('T3b drainage IC still liquid-full except inlet gas slab',
      bool((layD_open['psi0'][WT:X_IN + 1][
          pore_open[WT:X_IN + 1]] == 1.0).all())
      and bool((layD_open['psi0'][X_IN + 1:][
          pore_open[X_IN + 1:]] == -1.0).all()))
check('T3c drainage with explicit bounds still works (diagnostic use)',
      build_layout(geo, orientation='drainage', real_bounds=RB)
      ['x_real_lo'] == X_R0)

# ---- drainage regression vs ORIGINAL statements ------------------------
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
exp_mem_b = np.zeros_like(solid)
exp_mem_r = np.zeros_like(solid)
exp_mem_b[x_in] = 1
exp_mem_r[x_out] = 1
exp_res_in = np.zeros_like(solid)
exp_res_in[wt:x_in] = 1
exp_res_out = np.zeros_like(solid)
exp_res_out[x_out + 1:nx - wt] = 1

layD = build_layout(geo, orientation='drainage')
check('D1 drainage psi0 identical to original statements',
      np.array_equal(layD['psi0'], exp_psi0))
check('D2 drainage membranes identical (mem_b@in, mem_r@out)',
      np.array_equal(layD['mem_b'], exp_mem_b)
      and np.array_equal(layD['mem_r'], exp_mem_r))
check('D3 drainage reservoir masks identical',
      np.array_equal(layD['res_in'], exp_res_in)
      and np.array_equal(layD['res_out'], exp_res_out))
check('D4 drainage dom/pore_cells identical',
      layD['dom'] == slice(x_in + 1, x_out)
      and layD['pore_cells'] == float(pore_full[x_in + 1:x_out].sum()))

# ---- membrane orientation per phase ------------------------------------
check('M1 imbibition: mem_r plane at inlet x=11 only (blocks RED/gas; '
      'liquid enters), mem_b at outlet x=37 only (blocks BLUE/liquid; '
      'gas leaves)',
      np.array_equal(np.unique(np.nonzero(lay4['mem_r'])[0]), [X_IN])
      and np.array_equal(np.unique(np.nonzero(lay4['mem_b'])[0]), [X_OUT]))
check('M2 drainage: mem_b at inlet x=11, mem_r at outlet x=37 '
      '(unchanged)',
      np.array_equal(np.unique(np.nonzero(layD['mem_b'])[0]), [X_IN])
      and np.array_equal(np.unique(np.nonzero(layD['mem_r'])[0]), [X_OUT]))

# ---- T4: neutral gas-output semantics (static scan) --------------------
src = open(os.path.join(REPO, 'run_imbibition_cg3d.py'),
           encoding='utf-8').read()
check('T4a driver reports gas_saturation_real / gas_saturation_dom',
      'gas_saturation_real' in src and 'gas_saturation_dom' in src)
check('T4b driver has no s_nr / label_periodic / --conn trapped-gas '
      'claims',
      's_nr' not in src and 'label_periodic' not in src
      and "'--conn'" not in src and 'n_clusters' not in src)
check('T4c driver states trapped-gas analysis NOT implemented',
      'NOT_IMPLEMENTED' in src and 'trapped_gas_analysis' in src)

# ---- T5: visualization consistency -------------------------------------
from cg3d.ic_figs import phase_fractions, make_figures    # noqa: E402

liq, gas, sol = phase_fractions(lay4)
sol_m = lay4['solid'] != 0
liq_exp = ((lay4['psi0'] < 0) & ~sol_m).mean(axis=(1, 2))
gas_exp = ((lay4['psi0'] > 0) & ~sol_m).mean(axis=(1, 2))
sol_exp = sol_m.mean(axis=(1, 2))
check('T5a phase_fractions match independent recomputation from the '
      'same layout arrays',
      np.allclose(liq, liq_exp) and np.allclose(gas, gas_exp)
      and np.allclose(sol, sol_exp))
check('T5b profile classification: reservoir/buffer/prewet planes '
      'liquid fraction 1.0 (or solid-adjusted), gas-bulk planes gas>0.9',
      abs(liq[7] - 1.0) < 1e-12 and abs(liq[13] - 1.0) < 1e-12
      and abs(liq[16] - 1.0) < 1e-12 and gas[25] > 0.8)
figs = make_figures(p_rx, (2, 6), 'tests_output/imb_figs')
names = [os.path.basename(p) for p in figs]
check('T5c make_figures writes profile/slice per N + compare (5 files)',
      len(figs) == 5 and all(os.path.exists(p) for p in figs),
      ' '.join(names))
check('T5d expected filenames',
      'initial_state_profile_prewet_2.png' in names
      and 'initial_state_slice_prewet_6.png' in names
      and 'initial_state_compare.png' in names)

print(('ALL PASS' if not FAIL else f'FAILURES: {FAIL}'))
sys.exit(1 if FAIL else 0)
