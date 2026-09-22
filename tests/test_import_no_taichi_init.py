"""Import-side-effect regression (CG3D-TAICHI-INIT-001, validation A).

Importing ``lbm_solver_cg3d`` must not initialize the Taichi runtime.  The
module used to call ``ti.init()`` and allocate + fill its lattice/MRT
fields at import time; this test imports it in fresh child processes where
``taichi.init`` is replaced by a trap that raises, so a reintroduced
import-time initialization fails the import itself instead of passing
silently.

Child 1 (plain import) — must succeed and leave the runtime alone:
  * ``lbm_solver_cg3d`` imports with ``ti.init`` booby-trapped;
  * the six module tables (``e``, ``e_f``, ``w``, ``LR``, ``M``, ``inv_M``)
    are still unallocated — no runtime-dependent allocation at import;
  * no Taichi program is materialized (checked through Taichi's runtime
    object when that internal is available, reported otherwise).
Child 2 (boundary) — after the same clean import, the project's explicit
  boundary ``cg3d.runtime.init_runtime()`` DOES reach ``ti.init``: the
  runtime is started by the project call, not by the import.

The trap fires before any backend is selected, so neither child initializes
a backend; ``LBM_ARCH=cpu`` is set anyway and no GPU is required.

Run:  python tests/test_import_no_taichi_init.py   (exit 0 = pass)
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRAP = '''
import taichi


def _forbidden(*args, **kwargs):
    raise AssertionError('ti.init() was called during import of '
                         'lbm_solver_cg3d')


taichi.init = _forbidden
'''

CHILD_IMPORT = TRAP + '''
import lbm_solver_cg3d

for name in ('e', 'e_f', 'w', 'LR', 'M', 'inv_M'):
    assert getattr(lbm_solver_cg3d, name) is None, (
        'import allocated the module table ' + name)

try:
    from taichi.lang.impl import get_runtime
    assert get_runtime().prog is None, (
        'import materialized the Taichi program')
    state = 'no Taichi program (prog is None)'
except ImportError:                     # taichi internals moved: best effort
    state = 'UNCHECKED (taichi.lang.impl.get_runtime unavailable)'

print('IMPORT_OK: lbm_solver_cg3d imported with ti.init trapped; ' + state)
'''

CHILD_BOUNDARY = TRAP + '''
import lbm_solver_cg3d

from cg3d import runtime

try:
    runtime.init_runtime()
except AssertionError as exc:           # the trap fired: correct owner
    print('BOUNDARY_OK: init_runtime() reaches ti.init (' + str(exc) + ')')
else:
    raise AssertionError('init_runtime() did not call ti.init()')
'''

FAIL = []


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name
          + ('  ' + detail if detail else ''), flush=True)
    if not cond:
        FAIL.append(name)


def run_child(label, code):
    env = dict(os.environ)
    env['LBM_ARCH'] = 'cpu'             # belt and braces: never a GPU backend
    env['PYTHONPATH'] = REPO + os.pathsep + env.get('PYTHONPATH', '')
    proc = subprocess.run([sys.executable, '-c', code], cwd=REPO, env=env,
                          capture_output=True, text=True)
    print(f'--- {label} (exit {proc.returncode}) ---', flush=True)
    print(proc.stdout.rstrip(), flush=True)
    if proc.stderr.strip():
        print('stderr:', proc.stderr.rstrip(), flush=True)
    return proc


def main():
    p1 = run_child('child 1: plain import, ti.init trapped', CHILD_IMPORT)
    check('import lbm_solver_cg3d does not call ti.init()',
          p1.returncode == 0 and 'IMPORT_OK' in p1.stdout,
          f'exit={p1.returncode}')

    p2 = run_child('child 2: explicit boundary', CHILD_BOUNDARY)
    check('cg3d.runtime.init_runtime() is the path that calls ti.init()',
          p2.returncode == 0 and 'BOUNDARY_OK' in p2.stdout,
          f'exit={p2.returncode}')

    if FAIL:
        print(f'FAIL: {FAIL}')
        sys.exit(1)
    print('PASS: module import is free of Taichi runtime side effects')


if __name__ == '__main__':
    main()
