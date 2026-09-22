"""cg3d.runtime — the explicit Taichi runtime initialization boundary.

Importing ``lbm_solver_cg3d`` must not touch the Taichi runtime
(CG3D-TAICHI-INIT-001).  Module import used to call ``ti.init()`` and
allocate the shared lattice/MRT fields as a side effect, which pinned
every importer — test collection, tooling, probes — to a live Taichi
program.  The runtime is now started by exactly one call,
:func:`init_runtime`, on the path that is about to use Taichi fields or
kernels (``ColorGradientSolver3D.__init__`` -> ``ensure_lattice_tables``,
or any script that calls it directly).

Backend contract unchanged: ``LBM_ARCH=cpu`` selects CPU, anything else
keeps the historical GPU default, ``offline_cache=True`` is preserved.
"""
import os

import taichi as ti

_INITIALIZED = False


def select_arch():
    """LBM_ARCH contract: 'cpu' -> CPU, otherwise the existing GPU default."""
    return ti.cpu if os.environ.get('LBM_ARCH', 'gpu') == 'cpu' else ti.gpu


def init_runtime():
    """Start the Taichi runtime — the project's one explicit init path.

    Idempotent; returns True only for the call that actually ran
    ``ti.init``.  Later calls must be no-ops: a second ``ti.init``
    silently re-creates the program and invalidates the fields of the
    first one.  The runtime is therefore owned by this module — do not
    call ``ti.init``/``ti.reset`` around a live solver.
    """
    global _INITIALIZED
    if _INITIALIZED:
        return False
    ti.init(arch=select_arch(), offline_cache=True)
    _INITIALIZED = True
    return True


def is_runtime_initialized():
    """True once this module started the runtime in this process."""
    return _INITIALIZED
