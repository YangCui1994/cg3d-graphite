"""Cumulative V1 integration validation (CG3D-V1-INTEGRATION-004).

Thin cross-module test over the accepted cumulative base (CG3D-TAICHI-INIT-001
+ CG3D-PERIODIC-CONN-002 + CG3D-CONVERGENCE-DIAG-003): the three tasks' public
paths have to keep working *together* in one codebase — including the lifecycle
order (import -> explicit runtime boundary -> shared tables -> solver) and the
checkpoint layer that crosses all of them.

This is deliberately NOT a re-run of the dedicated suites; deep coverage stays
in tests/test_import_no_taichi_init.py, tests/test_periodic_connectivity.py and
tests/test_termination_diagnostics.py.  One representative case per area:

  A  runtime lifecycle    plain import has no side effect; cg3d.init_runtime()
                          is the boundary that starts the runtime; the shared
                          D3Q19/MRT tables materialize; a tiny 8^3 solver
                          constructs and round-trips through cg3d.checkpoint.
  B  periodic topology    one wrapped y+z edge pair (conn=18, axes=(1,2)) is a
                          single component; the identical geometric pair stays
                          split as soon as a required axis is not periodic.
  C  termination report   the real cg3d.protocol.run_hold driving a fake
                          non-LBM system: legacy reason / convergence["exit"]
                          are unchanged, termination + numerical_health are
                          additive and consistent, the row stays strict JSON.
  D  combined API/import  the four accepted public paths coexist, and a fresh
                          process importing them in reverse order reaches the
                          same lifecycle state.

CPU only: LBM_ARCH is forced to 'cpu' before any runtime initialization (no GPU
work is authorized for this validation).  The tiny instance is constructed and
checkpointed but never stepped, so no solver kernel is JIT-compiled here — the
only kernels that run are the field fills inside cg3d.checkpoint.restore_state.

Run:  python tests/test_v1_integration.py   (exit 0 = pass)
"""
import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
SCRATCH = os.path.join(REPO, 'tests_output')      # gitignored

# Before any explicit initialization: cg3d.runtime.init_runtime() reads
# LBM_ARCH, and nothing imported below starts the runtime on its own.
os.environ['LBM_ARCH'] = 'cpu'

import numpy as np                                       # noqa: E402
import taichi as ti                                      # noqa: E402

import cg3d                                               # noqa: E402
import cg3d.checkpoint                                    # noqa: E402
import cg3d.diagnostics                                   # noqa: E402
import cg3d.protocol                                      # noqa: E402
import cg3d.runtime                                       # noqa: E402
import lbm_solver_cg3d as mod                             # noqa: E402

TABLE_NAMES = ('e', 'e_f', 'w', 'LR', 'M', 'inv_M')
QUASI_STEADY = 'quasi-steady'                 # legacy reason string, verbatim

FAIL = []


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name
          + ('  ' + detail if detail else ''), flush=True)
    if not cond:
        FAIL.append(name)


def repro(tag, text):
    print(f'REPRO {tag}: {text}', flush=True)


def _taichi_prog_state():
    """'absent' when no Taichi program has been materialized, 'live' when one
    exists, UNCHECKED when the taichi internal moved (best effort, as in
    tests/test_import_no_taichi_init.py)."""
    try:
        from taichi.lang.impl import get_runtime
    except ImportError:
        return 'UNCHECKED'
    return 'absent' if get_runtime().prog is None else 'live'


# Captured where the imports above happen, i.e. before this process starts
# anything: section A reads this instead of re-deriving it later.
POST_IMPORT = dict(
    runtime_initialized=cg3d.is_runtime_initialized(),
    tables_allocated=[n for n in TABLE_NAMES if getattr(mod, n) is not None],
    taichi_prog=_taichi_prog_state())


# --------------------------------------------------------------------------
# A. runtime-lifecycle integration

def test_a_runtime_lifecycle():
    # --- the plain imports left the runtime alone -------------------------
    check('A1 plain import leaves the project runtime uninitialized',
          POST_IMPORT['runtime_initialized'] is False)
    check('A2 plain import allocates no shared lattice table',
          POST_IMPORT['tables_allocated'] == [],
          'allocated=' + str(POST_IMPORT['tables_allocated']))
    if POST_IMPORT['taichi_prog'] == 'UNCHECKED':
        print('NOTE A3 UNCHECKED: taichi.lang.impl.get_runtime unavailable')
    else:
        check('A3 plain import materializes no Taichi program',
              POST_IMPORT['taichi_prog'] == 'absent',
              POST_IMPORT['taichi_prog'])

    # --- the accepted explicit boundary ----------------------------------
    # taichi's Arch is a pybind11 enum: compare with == (attribute access
    # wraps a fresh object, so `is` is not stable).
    check('A4 LBM_ARCH=cpu selects the CPU backend',
          cg3d.runtime.select_arch() == ti.cpu)
    first = cg3d.init_runtime()
    second = cg3d.init_runtime()
    check('A5 cg3d.init_runtime() is the call that starts the runtime',
          first is True and cg3d.is_runtime_initialized() is True,
          f'first call returned {first}')
    check('A6 a second init_runtime() is a no-op (runtime not re-created)',
          second is False, f'second call returned {second}')
    try:
        from taichi.lang.impl import current_cfg
        arch_ok = current_cfg().arch == ti.cpu
        live_arch = str(current_cfg().arch)
    except Exception as exc:                          # internal moved: report
        arch_ok, live_arch = None, f'UNCHECKED ({type(exc).__name__})'
    if arch_ok is None:
        print(f'NOTE A7 {live_arch}')
    else:
        check('A7 the live Taichi program is the CPU backend', arch_ok,
              live_arch)

    # --- shared lattice tables -------------------------------------------
    mod.ensure_lattice_tables()
    missing = [n for n in TABLE_NAMES if getattr(mod, n) is None]
    check('A8 ensure_lattice_tables() materializes all six shared tables',
          missing == [], 'missing=' + str(missing))
    check('A9 materialized tables have the D3Q19/MRT shapes',
          tuple(mod.e.shape) == (19,) and tuple(mod.w.shape) == (19,)
          and tuple(mod.M.shape) == (19, 19)
          and tuple(mod.inv_M.shape) == (19, 19))
    m_np = mod.M.to_numpy().astype(np.float64)
    im_np = mod.inv_M.to_numpy().astype(np.float64)
    err = float(np.abs(m_np @ im_np - np.eye(19)).max())
    check('A10 materialized M @ inv_M == I', err < 1e-5, f'max|err|={err:.2e}')
    table_id = id(mod.M)
    mod.ensure_lattice_tables()
    check('A11 ensure_lattice_tables() is idempotent (no re-allocation)',
          id(mod.M) == table_id)

    # --- a tiny solver instance through the accepted lifecycle -----------
    t0 = time.time()
    s = mod.ColorGradientSolver3D(8, 8, 8, CapA=0.02, psi_solid=-0.75)
    build_s = time.time() - t0
    check('A12 a small ColorGradientSolver3D constructs through the lifecycle',
          (s.nx, s.ny, s.nz) == (8, 8, 8)
          and tuple(s.psi.shape) == (8, 8, 8)
          and tuple(s.f.shape) == (8, 8, 8, 19)
          and tuple(s.v.shape) == (8, 8, 8),
          f'{build_s:.2f}s, no solver kernel compiled')
    check('A13 the constructed instance carries its runtime parameters',
          abs(float(s.CapA[None]) - 0.02) < 1e-6
          and abs(float(s.psi_solid[None]) + 0.75) < 1e-6)

    # --- the same instance round-trips through the checkpoint layer ------
    rng = np.random.default_rng(0)
    psi_pat = rng.uniform(-1.0, 1.0, (8, 8, 8)).astype(np.float32)
    f_pat = rng.uniform(0.0, 0.1, (8, 8, 8, 19)).astype(np.float32)
    s.psi.from_numpy(psi_pat)
    s.f.from_numpy(f_pat)
    os.makedirs(SCRATCH, exist_ok=True)
    ck = os.path.join(SCRATCH, 'v1_integration_tiny.npz')
    cg3d.checkpoint.save_state(s, ck, dict(driver='v1_integration', tag='tiny',
                                           it_total=0))
    meta = cg3d.checkpoint.restore_state(s, ck)
    check('A14 checkpoint meta round-trips the accepted format and shape',
          meta['format'] == 'cg3d-ckpt-v1' and meta['shape'] == [8, 8, 8],
          f'format={meta["format"]} shape={meta["shape"]}')
    check('A15 restored psi and f match the saved state exactly',
          np.array_equal(s.psi.to_numpy(), psi_pat)
          and np.array_equal(s.f.to_numpy(), f_pat))
    check('A16 checkpoint.read_meta() reads the same meta back',
          cg3d.checkpoint.read_meta(ck)['tag'] == 'tiny')
    os.remove(ck)                        # scratch file, tree stays clean

    repro('A lifecycle',
          f'import->init_runtime={first}/{second}->tables(missing={missing}, '
          f'M@inv_M err={err:.1e})->solver 8^3 in {build_s:.2f}s->'
          f'checkpoint round-trip exact')


# --------------------------------------------------------------------------
# B. periodic-topology integration

def wrapped_edge_mask():
    """(2,0,0) vs (2,5,5) on a 4x6x6 grid: their wrapped displacement is
    (0,-1,-1) — an 18-neighbour relation that needs the y AND the z seam at
    once, and is not a neighbour at all without wrapping."""
    m = np.zeros((4, 6, 6), bool)
    m[2, 0, 0] = True
    m[2, 5, 5] = True
    return m


def test_b_periodic_topology():
    m = wrapped_edge_mask()
    _, sizes = cg3d.label_periodic(m, conn=18, periodic_axes=(1, 2))
    n, sz = len(sizes), sorted((int(v) for v in sizes), reverse=True)
    repro('B y+z wrapped edge conn=18 axes=(1,2)', f'n={n} sizes={sz}')
    check('B1 y+z wrapped edge pair is ONE component of size 2 (conn=18)',
          n == 1 and sz == [2], f'n={n} sizes={sz}')
    for axes in ((1,), (2,), ()):
        _, neg = cg3d.label_periodic(m, conn=18, periodic_axes=axes)
        n_neg = len(neg)
        check(f'B2 negative control axes={axes}: same pair stays split '
              f'(required axis not periodic)', n_neg == 2, f'n={n_neg}')


# --------------------------------------------------------------------------
# C. termination-diagnostics integration

def _sample_flat(_step, _n):
    """All-finite, all-flat diagnostics in OpenSystem.measure()'s shape,
    carrying every field run_hold / eval_convergence / the health tracker
    read.  Flat saturation satisfies the accepted sat-mode criterion."""
    return dict(s_nw=0.42, s_nw_binary=0.40, umax=1e-3,
                rho_in_mean=1.0, rho_out_mean=1.0,
                p_in_mean=1.0 / 3.0, p_out_mean=1.0 / 3.0,
                pc_band_in=0.35, pc_band_out=0.32, pc_measured=0.03,
                u_rms=1e-3, u_bulk_x=0.0, inj_r=0.0, inj_b=0.0, inj_m=0.0)


class _FakeSolver:
    """run_hold only ever calls step() on the solver."""

    def __init__(self):
        self.n = 0

    def step(self):
        self.n += 1


class _FakeSystem:
    """The four OpenSystem members run_hold touches — no LBM, no Taichi."""

    def __init__(self, sample_fn):
        self.s = _FakeSolver()
        self.pore_cells = 1000.0
        self._sample_fn = sample_fn

    def set_ladder(self, _d):
        pass

    def measure(self):
        return self._sample_fn(self.s.n, 0)


def _rung_ns(**over):
    """Config namespace with run_hold's fields, at the accepted defaults."""
    cfg = dict(every=1, min_steps=5, max_steps=30, qs_window=10, qs_tol=1e-3,
               qs_mode='sat', pc_drift_tol=0.01, flux_tol=1e-6,
               u_rel_tol=0.05, umax_cap=0.1, dump_every=0)
    cfg.update(over)
    return SimpleNamespace(**cfg)


def test_c_termination_reports():
    row = cg3d.protocol.run_hold(_rung_ns(), _FakeSystem(_sample_flat), 0.06,
                                 'v1_integration')
    term, health = row['termination'], row['numerical_health']
    repro('C run_hold (fake system, sat mode)',
          f'reason={row["reason"]} steps={row["steps"]} '
          f'termination={term} health_finite={health["finite"]} '
          f'health_samples={health["sample_count"]}')
    check('C1 legacy reason is still on the returned row',
          row.get('reason') == QUASI_STEADY, str(row.get('reason')))
    check('C2 legacy convergence["exit"] is still present and agrees with '
          'the reason',
          row['convergence']['exit'] == dict(mode='sat', reason=row['reason']),
          str(row['convergence']['exit']))
    check('C3 termination is present and consistent with the legacy reason',
          isinstance(term, dict) and term['process_completed'] is True
          and term['reason'] == row['reason'] and term['converged'] is True
          and term['step_limit_reached'] is False
          and term['safety_limit_triggered'] is False
          and term['qs_mode'] == 'sat')
    check('C4 numerical_health is present and finite for the all-finite case',
          isinstance(health, dict) and health['finite'] is True
          and health['nonfinite_fields'] == []
          and health['first_nonfinite_step'] is None,
          str(health.get('nonfinite_fields')))
    try:
        blob = json.dumps(row)
        ok = True
    except (TypeError, ValueError) as exc:
        blob, ok = str(exc), False
    check('C5 the returned row is strictly JSON-serializable', ok,
          f'{len(blob)} bytes' if ok else blob)


# --------------------------------------------------------------------------
# D. combined-import / API sanity

CHILD_REVERSE_ORDER = '''
import os
os.environ['LBM_ARCH'] = 'cpu'
import lbm_solver_cg3d as mod     # solver module first: reverse of section A
import cg3d
import cg3d.protocol
assert cg3d.is_runtime_initialized() is False, 'import started the runtime'
assert all(getattr(mod, n) is None for n in
           ('e', 'e_f', 'w', 'LR', 'M', 'inv_M')), 'import allocated a table'
assert cg3d.protocol.run_hold is cg3d.run_hold
assert callable(cg3d.init_runtime) and callable(cg3d.label_periodic)
s = mod.ColorGradientSolver3D(6, 6, 6, CapA=0.02)
assert cg3d.is_runtime_initialized() is True, 'solver left the runtime down'
assert mod.M is not None, 'solver left the tables unallocated'
print('CHILD_OK: reverse-order import reached the same lifecycle state')
'''


def test_d_combined_api():
    check('D1 cg3d.init_runtime is the accepted runtime boundary',
          callable(cg3d.init_runtime))
    check('D2 cg3d.label_periodic is the accepted periodic labeller',
          callable(cg3d.label_periodic)
          and cg3d.label_periodic is cg3d.diagnostics.label_periodic)
    check('D3 cg3d.protocol.run_hold is the accepted rung loop',
          callable(cg3d.protocol.run_hold)
          and cg3d.protocol.run_hold is cg3d.run_hold)
    check('D4 lbm_solver_cg3d.ColorGradientSolver3D is the accepted solver',
          isinstance(mod.ColorGradientSolver3D, type))

    env = dict(os.environ)
    env['LBM_ARCH'] = 'cpu'
    env['PYTHONPATH'] = REPO + os.pathsep + env.get('PYTHONPATH', '')
    proc = subprocess.run([sys.executable, '-c', CHILD_REVERSE_ORDER],
                          cwd=REPO, env=env, capture_output=True, text=True)
    ok = proc.returncode == 0 and 'CHILD_OK' in proc.stdout
    check('D5 a fresh process with reverse import order reaches the same '
          'lifecycle', ok, f'exit={proc.returncode}')
    for stream, text in (('stdout', proc.stdout), ('stderr', proc.stderr)):
        if text.strip():
            print(f'--- child {stream} ---\n{text.rstrip()}', flush=True)


def main():
    t0 = time.time()
    print(f'interpreter: {sys.executable}', flush=True)
    print(f'cwd: {os.getcwd()}  LBM_ARCH forced to cpu', flush=True)
    test_a_runtime_lifecycle()
    test_b_periodic_topology()
    test_c_termination_reports()
    test_d_combined_api()
    print(f'integration wall time {time.time() - t0:.1f}s', flush=True)
    if FAIL:
        print(f'FAIL: {FAIL}')
        sys.exit(1)
    print('ALL PASS')


if __name__ == '__main__':
    main()
