"""viz3dlib.runio — Run loading (final.npz) and array-level domain helpers."""
from __future__ import annotations

import os
import json
import numpy as np

from .style_env import WALL_T


# ----------------------------------------------------------------- run I/O
def load_run(path):
    """Load a run directory (or a .npz) into a dict of fields + metadata.

    Returns dict with psi, solid, geo_meta, res_thick, dom (x slice of the
    pore domain, reservoir/membrane slabs excluded), R_lu, tag.
    """
    d = path if os.path.isdir(path) else os.path.dirname(path)
    npz = os.path.join(path, 'final.npz') if os.path.isdir(path) else path
    if not os.path.exists(npz):
        raise SystemExit(f'no final.npz under {path}')
    z = np.load(npz)
    out = {k: z[k] for k in z.files}
    if 'psi' not in out or 'solid' not in out:
        raise SystemExit(f'{npz} needs psi and solid (got {list(out)})')

    meta, res_thick, r_lu = {}, 8, None
    rj = os.path.join(d, 'report.json')
    if os.path.exists(rj):
        with open(rj, encoding='utf-8') as f:
            rep = json.load(f)
        meta = rep
        res_thick = int(rep.get('args', {}).get('res_thick', 8))
        g = rep.get('geo')
        if isinstance(g, str):
            try:
                g = json.loads(g.replace("'", '"'))
            except Exception:                                    # noqa: BLE001
                g = None
        if isinstance(g, dict):
            r_lu = g.get('R_lu')

    nx = out['psi'].shape[0]
    x_in = WALL_T + res_thick + 1              # first pore-domain plane
    x_out = nx - WALL_T - res_thick            # last pore-domain plane + 1
    out.update(tag=os.path.basename(d.rstrip('/\\')), npz=npz,
               meta=meta, res_thick=res_thick, R_lu=r_lu,
               dom=slice(x_in, x_out))
    return out


def pore_domain(run, full=False):
    """(psi, solid) restricted to the pore domain unless full=True."""
    if full:
        return run['psi'], run['solid']
    return run['psi'][run['dom']], run['solid'][run['dom']]


def _smooth_binary(a, sigma=0.8):
    """Gaussian-blurred binary field for a smoother 0.5 level set.

    Opt-in only: the solver sees voxelised spheres, so the default renders
    the staircase honestly.  Blurring pulls the surface slightly inward.
    """
    from scipy import ndimage

    return ndimage.gaussian_filter(np.asarray(a, dtype=np.float32), sigma)


def _domain_bounds(run, psi, full, spacing=(1, 1, 1)):
    x0 = 0.0 if full else float(run['dom'].start)
    n = psi.shape
    return (x0 * spacing[0], x0 * spacing[0] + (n[0] - 1) * spacing[0],
            0.0, (n[1] - 1) * spacing[1],
            0.0, (n[2] - 1) * spacing[2])
