"""cg3d package — experiment-protocol layer (Plan_20260919_v2 Phase 4).

Hosts configuration / protocol / diagnostics / post-processing modules.
The Taichi solver itself stays in the root-level ``lbm_solver_cg3d.py``
(single module holding the hot kernels — the plan explicitly warns
against fragmenting them; a file move is deferred until after the
numerical-audit reruns so PR-6 compares against a frozen code layout).
"""
from .diagnostics import (region_stats, eval_convergence, label_periodic)
from .protocol import OpenSystem, run_hold, run_equil

__all__ = ['region_stats', 'eval_convergence', 'label_periodic',
           'OpenSystem', 'run_hold', 'run_equil']
