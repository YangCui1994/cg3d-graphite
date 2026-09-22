"""cg3d package — experiment-protocol layer (Plan_20260919_v2 Phase 4).

Hosts configuration / protocol / diagnostics / post-processing modules and
the explicit Taichi runtime boundary (``init_runtime``, CG3D-TAICHI-INIT-001).
The Taichi solver itself stays in the root-level ``lbm_solver_cg3d.py``
(single module holding the hot kernels — the plan explicitly warns
against fragmenting them; a file move is deferred until after the
numerical-audit reruns so PR-6 compares against a frozen code layout).
"""
from .diagnostics import (region_stats, eval_convergence, label_periodic)
from .protocol import OpenSystem, run_hold, run_equil
from .runtime import init_runtime, is_runtime_initialized
from . import checkpoint

__all__ = ['region_stats', 'eval_convergence', 'label_periodic',
           'OpenSystem', 'run_hold', 'run_equil', 'checkpoint',
           'init_runtime', 'is_runtime_initialized']
