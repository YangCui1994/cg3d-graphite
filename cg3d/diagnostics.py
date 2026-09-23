"""cg3d.diagnostics — host-side measurement / post-processing (PR-1/PR-3
instruments, moved here from run_common.py in PR-5; run_common re-exports
for compatibility).

CG3D-CONVERGENCE-DIAG-003 adds a reporting layer on top of the rung exit:
`termination_record` (why the rung stopped, as three independent flags) and
`NumericalHealthTracker` (observed finite/non-finite sampled diagnostics).
Both are observational — they decide nothing, add no stop condition and no
new threshold, and leave every existing convergence calculation untouched.
"""
import math

import numpy as np
from scipy import ndimage

QUASI_STEADY = 'quasi-steady'
MAX_STEPS = 'max-steps'
UMAX_CAP = 'umax-cap'

_CONN_STRUCT = {6: ndimage.generate_binary_structure(3, 1),
                18: ndimage.generate_binary_structure(3, 2),
                26: ndimage.generate_binary_structure(3, 3)}


def _wrapped_offsets(struct, periodic_axes):
    """Structure offsets that can reach across a periodic seam.

    An offset qualifies when it is non-zero on at least one periodic axis:
    offsets whose non-zero components all sit on non-periodic axes are already
    resolved by the plain non-periodic labelling and need no wrap.
    """
    per = set(int(a) for a in periodic_axes)
    offs = []
    for cell in np.argwhere(np.asarray(struct)):
        off = tuple(int(v) - 1 for v in cell)
        if any(off[a] for a in per):
            offs.append(off)
    return offs


def label_periodic(mask, conn=6, periodic_axes=(1, 2)):
    """Connected components with wrap-around merging (PR-3, tasks
    2.6/2.7; torus topology fixed in CG3D-PERIODIC-CONN-002).  The solver
    is y/z-periodic, so a phase cluster touching both ends of a periodic
    axis is ONE cluster; plain ndimage.label splits it.

    Implementation: label non-periodically with the requested connectivity
    structure, then union-find merge the label pairs that are neighbours
    through EVERY wrapped offset of that structure.  A neighbour may cross
    one, two or three seams at once, which is what the connectivity means:
    a face crossing one seam, an edge wrapping two axes simultaneously, a
    corner wrapping all three.  Wrapping is applied only on the axes listed
    in `periodic_axes`, so a relation that would have to wrap a
    non-periodic axis is never merged.

    `periodic_axes` is any subset of (0, 1, 2); the default (y, z) matches
    the production solver.  NOTE: padding with one wrapped layer does NOT
    work — the pad copy and the original cell get different labels.
    Returns (labels, sizes_sorted_desc); sizes count interior cells only.
    """
    m = np.asarray(mask, dtype=bool)
    S = _CONN_STRUCT[conn]
    lab, n = ndimage.label(m, structure=S)
    if n == 0:
        return lab, np.array([], dtype=np.int64)
    dims = m.shape
    per = tuple(sorted({int(a) for a in periodic_axes}))
    parent = list(range(n + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for off in _wrapped_offsets(S, per):
        # Neighbour pair (A, B = A + off).  On a non-periodic axis the step
        # merely narrows both sides; on a periodic axis B is the rolled view,
        # so the wrap comes for free and several axes can wrap at once.
        slA = [slice(None)] * 3
        slB = [slice(None)] * 3
        for a in range(3):
            o = off[a]
            if o == 0 or a in per:
                continue
            if o > 0:
                slA[a], slB[a] = slice(0, dims[a] - 1), slice(1, dims[a])
            else:
                slA[a], slB[a] = slice(1, dims[a]), slice(0, dims[a] - 1)
        a_lab = lab[tuple(slA)]
        b_lab = lab[tuple(slB)]
        for a in range(3):
            if off[a] and a in per:
                b_lab = np.roll(b_lab, -off[a], axis=a)
        both = (a_lab > 0) & (b_lab > 0)
        if not both.any():
            continue
        # one entry per distinct label pair, not per voxel pair
        keys = np.unique(a_lab[both].astype(np.int64) * (n + 1)
                         + b_lab[both].astype(np.int64))
        for key in keys.tolist():
            x, y = divmod(key, n + 1)
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[max(rx, ry)] = min(rx, ry)

    roots = np.array([find(i) for i in range(n + 1)])
    _, inv = np.unique(roots[1:], return_inverse=True)
    relabel = np.zeros(n + 1, dtype=lab.dtype)
    relabel[1:] = inv + 1
    lab2 = relabel[lab]
    sizes = np.sort(np.bincount(lab2.ravel())[1:])[::-1]
    return lab2, sizes


def eval_convergence(win, pore_cells, qs_tol, pc_drift_tol=0.01,
                     flux_tol=1e-6, u_rel_tol=0.05):
    """Multi-indicator quasi-steady record (PR-3, task 2.4; structure per
    Plan_20260919_v2 §Phase 2).  win = trailing window of (it, dict)
    sample pairs carrying s_nw / pc_measured / inj_r / inj_b / u_rms
    (PR-1 instruments).  Returns a JSON-ready dict answering "why did
    this rung exit"; thresholds live in the driver's config layer."""
    out = dict(criteria_passed=[], thresholds=dict(
        saturation_slope=qs_tol, pc_drift=pc_drift_tol,
        phase_flux=flux_tol, u_rms_rel=u_rel_tol))
    if len(win) < 2:
        return out
    its = [i for i, _ in win]
    ms = [m for _, m in win]
    span = its[-1] - its[0]
    if span <= 0:
        return out
    out['saturation_slope'] = (ms[-1]['s_nw'] - ms[0]['s_nw']) / span
    pcs = [m['pc_measured'] for m in ms]
    pc_scale = max(abs(float(np.mean(pcs))), 1e-12)
    out['pc_drift'] = (max(pcs) - min(pcs)) / pc_scale
    fr = (ms[-1]['inj_r'] - ms[0]['inj_r']) / span / pore_cells
    fb = (ms[-1]['inj_b'] - ms[0]['inj_b']) / span / pore_cells
    out['phase_flux'] = abs(fr) + abs(fb)
    us = [m['u_rms'] for m in ms]
    out['u_rms_rel'] = (max(us) - min(us)) / max(float(np.mean(us)), 1e-30)
    if abs(out['saturation_slope']) < qs_tol:
        out['criteria_passed'].append('saturation')
    if out['pc_drift'] < pc_drift_tol:
        out['criteria_passed'].append('pressure')
    if out['phase_flux'] < flux_tol:
        out['criteria_passed'].append('flux')
    if out['u_rms_rel'] < u_rel_tol:
        out['criteria_passed'].append('kinetic')
    return out


def termination_record(reason, qs_mode):
    """Additive termination record for a normal `run_hold` return
    (CG3D-CONVERGENCE-DIAG-003).  Splits the single legacy `reason`
    string into the three independent statements it conflates, without
    touching any stopping rule: `converged` is true only for the
    configured quasi-steady exit, `step_limit_reached` only for the
    step-budget exit, `safety_limit_triggered` only for the umax-cap
    exit.  All three flags are read off `reason`; nothing is recomputed
    and no decision is taken here.

    `process_completed` is always True by construction: this record is
    built only where `run_hold` returned normally.  Abnormal process
    exits (exception, interrupt, external stop) never reach it and are
    deliberately outside the record.  `reason` is echoed verbatim, so an
    unrecognised future reason reports three False flags instead of
    raising inside a running simulation.

    \"converged\" here means only that the configured numerical stopping
    criteria were satisfied; it is not a claim of physical equilibrium.
    """
    return dict(process_completed=True,
                reason=str(reason),
                converged=reason == QUASI_STEADY,
                step_limit_reached=reason == MAX_STEPS,
                safety_limit_triggered=reason == UMAX_CAP,
                qs_mode=str(qs_mode))


def _finite_or_none(value):
    """float(value) for a real scalar, else None (value unavailable).

    None, strings and anything that is not castable to a single real
    number (e.g. a multi-element array) count as unavailable and are
    ignored rather than reported as non-finite.
    """
    if value is None or isinstance(value, str):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class NumericalHealthTracker:
    """Observed finite/non-finite state of the sampled diagnostics
    (CG3D-CONVERGENCE-DIAG-003).  Purely observational: it holds no
    threshold, adds no stop condition, and cannot alter the trajectory —
    a large but finite umax is finite here, and its umax-cap exit is a
    safety limit, not a numerical failure.

    `observe(step, sample)` takes one `OpenSystem.measure()` dict and
    records every scalar field observed as NaN/Inf.  `record()` returns a
    JSON-ready dict: `finite` is true only when no observed scalar was
    non-finite (vacuously true when nothing was sampled, with
    `sample_count = 0` recording that fact), `nonfinite_fields` lists the
    offending field names sorted, `first_nonfinite_step` is the first
    sampled step carrying any of them, and `first_nonfinite_fields` says
    which fields were already bad at that step.
    """

    def __init__(self):
        self.sample_count = 0
        self.fields_observed = set()
        self.nonfinite_counts = {}
        self.first_nonfinite_step = None
        self.first_nonfinite_fields = []

    def observe(self, step, sample):
        """One sampling point.  Never raises on odd values: a field that
        is not a real scalar is skipped, not failed."""
        self.sample_count += 1
        if not isinstance(sample, dict):
            return
        first_here = []
        for name, value in sample.items():
            v = _finite_or_none(value)
            if v is None:
                continue
            key = str(name)
            self.fields_observed.add(key)
            if math.isfinite(v):
                continue
            self.nonfinite_counts[key] = self.nonfinite_counts.get(key, 0) + 1
            first_here.append(key)
        if first_here and self.first_nonfinite_step is None:
            self.first_nonfinite_step = int(step)
            self.first_nonfinite_fields = first_here

    def record(self):
        return dict(finite=not self.nonfinite_counts,
                    nonfinite_fields=sorted(self.nonfinite_counts),
                    first_nonfinite_step=self.first_nonfinite_step,
                    sample_count=int(self.sample_count),
                    nonfinite_counts={k: self.nonfinite_counts[k]
                                      for k in sorted(self.nonfinite_counts)},
                    first_nonfinite_fields=list(self.first_nonfinite_fields),
                    fields_observed=sorted(self.fields_observed))


def region_stats(rho, psi, v, mask):
    """PR-1 instrument (Plan_20260919_v2, tasks 2.1-2.3): host-side
    regional diagnostics from snapshot arrays.

    rho, psi: (nx, ny, nz) float; v: (nx, ny, nz, 3); mask: boolean array
    of the same shape.  Pressure uses the ideal LBM relation p = cs^2 rho
    with cs^2 = 1/3 (incompressible limit; this solver has no bulk free
    energy).  Pure numpy, no solver state touched."""
    m = np.asarray(mask, dtype=bool)
    n = int(m.sum())
    if n == 0:
        return dict(n=0, rho_mean=None, p_mean=None, psi_mean=None,
                    v_rms=None, v_bulk=(None, None, None))
    rho_m = float(rho[m].mean(dtype=np.float64))
    vmag2 = (v[..., 0]**2 + v[..., 1]**2 + v[..., 2]**2)[m]
    vb = v[m]
    return dict(n=n,
                rho_mean=rho_m,
                p_mean=rho_m / 3.0,
                psi_mean=float(psi[m].mean(dtype=np.float64)),
                v_rms=float(np.sqrt(vmag2.mean(dtype=np.float64))),
                v_bulk=(float(vb[:, 0].mean(dtype=np.float64)),
                        float(vb[:, 1].mean(dtype=np.float64)),
                        float(vb[:, 2].mean(dtype=np.float64))))
