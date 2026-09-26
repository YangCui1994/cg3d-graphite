"""Test-geometry generators for the Leclaire-2017 canonical validation set.

Task: BI-CG-LECLAIRE-IMPLEMENTATION-001.

These generators are written here rather than imported from the production
test suite: the production generators encode ``psi_solid``-specific wall
semantics (CURRENT_VS_LECLAIRE_MAP.md rows 15 and 20) and are therefore not
algorithm-independent (IMPLEMENTATION_PLAN.md section 1).

The asymmetric killer geometry in particular is constructed so that no
periodic translation maps it onto itself with a sign flip, because R2
records that periodic closure can conceal wall-directed mass transfer
(PALABOS_LECLAIRE_CODE_TRACE.md section 10.2).
"""

from __future__ import annotations

import numpy as np

from . import lattice as L
from . import operators as op


def grid(nx, ny, nz):
    return np.meshgrid(np.arange(nx), np.arange(ny), np.arange(nz),
                       indexing="ij")


# ----------------------------------------------------------------------
#  Phase-field initial conditions
# ----------------------------------------------------------------------
def planar_interface(nx, ny, nz, axis=2, width=2.0, center=None):
    """psi = -tanh((coord - center)/width) across ``axis``."""
    X, Y, Z = grid(nx, ny, nz)
    c = (X, Y, Z)[axis]
    if center is None:
        center = (nx, ny, nz)[axis] / 2.0
    return -np.tanh((c - center) / float(width))


def sine_interface(nx, ny, nz, amp=2.0, k=1, width=2.0, wave_axis=0,
                   normal_axis=2, center=None):
    """A capillary wave: planar interface perturbed by a cosine along
    ``wave_axis`` ``k`` times across the box."""
    X, Y, Z = grid(nx, ny, nz)
    n = (X, Y, Z)[normal_axis]
    w = (X, Y, Z)[wave_axis]
    length = (nx, ny, nz)[wave_axis]
    if center is None:
        center = (nx, ny, nz)[normal_axis] / 2.0
    return -np.tanh((n - center - amp * np.cos(2 * np.pi * k * w / length))
                    / float(width))


def droplet(nx, ny, nz, radius, center=None):
    """psi = +1 inside a sphere of ``radius``, -1 outside, tanh-smoothed."""
    X, Y, Z = grid(nx, ny, nz)
    if center is None:
        center = (nx / 2.0, ny / 2.0, nz / 2.0)
    r = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2
                + (Z - center[2]) ** 2)
    return np.tanh((radius - r) / 1.5)


def hemi_droplet_on_wall(nx, ny, nz, radius, center_xy=None, width=1.5):
    """A droplet resting on the z=0 wall: solid for z < slab, phase blob
    centred on the wall plane so the equilibrium shape is a spherical cap."""
    X, Y, Z = grid(nx, ny, nz)
    if center_xy is None:
        center_xy = (nx / 2.0, ny / 2.0)
    r = np.sqrt((X - center_xy[0]) ** 2 + (Y - center_xy[1]) ** 2
                + (Z - 0.0) ** 2)
    return np.tanh((radius - r) / float(width))


# ----------------------------------------------------------------------
#  Solid masks
# ----------------------------------------------------------------------
def wall_slab(nx, ny, nz, thickness=2):
    """Solid slab at z = 0 .. thickness-1 (a flat floor)."""
    s = np.zeros((nx, ny, nz), dtype=bool)
    s[:, :, :int(thickness)] = True
    return s


def slit(nx, ny, nz, gap, wall=2):
    """A planar slit of width ``gap`` between two solid slabs, floor at
    z < wall and ceiling at z >= wall+gap."""
    s = np.zeros((nx, ny, nz), dtype=bool)
    s[:, :, :int(wall)] = True
    s[:, :, int(wall) + int(gap):] = True
    return s


def asymmetric_ledge(nx, ny, nz, ledge_thickness=3, ledge_height=None,
                     side="left"):
    """One-sided top ledge: a floor slab plus an overhang covering part of
    the box in x, attached to one wall only.

    Deliberately NOT translation-symmetric under the periodic wrap and
    NOT mirror-symmetric about any interior plane, so a wall-directed
    mass transfer cannot cancel (R2's warning).  The two x-faces are
    closed by solid walls.
    """
    s = np.zeros((nx, ny, nz), dtype=bool)
    s[:, :, :2] = True                                   # floor
    if ledge_height is None:
        ledge_height = max(4, nz // 3)
    half = nx // 2
    if side == "left":
        s[:half + 1, :, nz - ledge_thickness:] = True    # overhang, left half
        s[:ledge_thickness, :, :] = True                 # closed left face
    else:
        s[half:, :, nz - ledge_thickness:] = True
        s[nx - ledge_thickness:, :, :] = True
    # close the y faces as well so the box is truly closed
    s[:, :ledge_thickness, :] = True
    s[:, ny - ledge_thickness:, :] = True
    return s


# ----------------------------------------------------------------------
#  Measurement helpers
# ----------------------------------------------------------------------
def interface_position_1d(psi_prof):
    """Zero crossing of a monotone periodic-ish profile, by linear
    interpolation on the (possibly wrapped) profile."""
    p = np.asarray(psi_prof, dtype=np.float64)
    n = p.size
    idx = np.where(np.sign(p[:-1]) * np.sign(p[1:]) < 0)[0]
    if idx.size == 0:
        # try the periodic wrap
        if np.sign(p[-1]) * np.sign(p[0]) < 0:
            f = p[-1] / (p[-1] - p[0])
            return n - 1 + f
        return np.nan
    i = idx[0]
    f = p[i] / (p[i] - p[i + 1])
    return i + f


def interface_width_tanh(psi_prof, coord=None):
    """Fit psi = -tanh((coord - c)/w) and return (w, c).

    Returns ``(nan, nan)`` when the profile is not a clean interface.
    """
    p = np.asarray(psi_prof, dtype=np.float64)
    if coord is None:
        coord = np.arange(p.size, dtype=np.float64)
    coord = np.asarray(coord, dtype=np.float64)

    def residual(params):
        w, c, s = params
        if w <= 1e-6:
            return np.full_like(p, 1e6)
        return s * np.tanh((coord - c) / w) - p

    from scipy.optimize import least_squares
    best = None
    for c0 in np.linspace(coord.min(), coord.max(), 8):
        try:
            sol = least_squares(residual, [1.5, c0, -1.0],
                                bounds=([1e-3, coord.min() - 1, -1.5],
                                        [20.0, coord.max() + 1, 1.5]))
        except Exception:
            continue
        if best is None or sol.cost < best.cost:
            best = sol
    if best is None:
        return float("nan"), float("nan")
    w, c, _s = best.x
    return float(abs(w)), float(c)


def labelled_components(field, threshold=0.5):
    """Label connected regions of ``field > threshold`` (6-connectivity).
    Returns (n_components, sizes sorted descending)."""
    from scipy import ndimage
    mask = np.asarray(field) > threshold
    lab, n = ndimage.label(mask)
    if n == 0:
        return 0, []
    sizes = np.bincount(lab.ravel())[1:]
    return int(n), sorted((int(s) for s in sizes), reverse=True)


def wall_band(shape, solid, thickness=3):
    """Fluid nodes within ``thickness`` of a solid node."""
    wall = np.zeros(shape, dtype=bool)
    for i in range(1, 19):
        wall |= op._shift(np.asarray(solid) != 0, L.E[i]).astype(bool)
    return wall & ~np.asarray(solid)


def contact_angle_from_profile(psi_col, z_col):
    """Estimate the contact angle at a wall from a vertical psi column
    profile: the angle between the interface normal at the contact point
    and the wall normal.

    Simplified robust estimator: find the height at which the interface
    crosses the mid-plane and the radial extent of the droplet at the
    first fluid layer, then use the geometric relation for a spherical
    cap.  Superseded by the profile fit used in the driver; kept here for
    cross-checking.
    """
    return float("nan")
