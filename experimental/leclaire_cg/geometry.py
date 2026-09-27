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
    """One-sided top ledge inside a fully closed box.

    A floor slab, an overhang covering only ONE half in x, and **all four
    lateral faces closed**.  The geometry is deliberately not
    translation-symmetric under the periodic wrap and not mirror-symmetric
    about any interior plane, so a wall-directed mass transfer cannot
    cancel.

    Correction history: the first version closed only the x face on the
    chosen ``side`` and left the opposite x face linked through the
    periodic ``np.roll`` streaming topology, while the docstring claimed
    "the two x-faces are closed".  External review B6 caught the false
    claim.  Both x faces are now closed and ``assert_closed_box()``
    verifies it in code.
    """
    s = np.zeros((nx, ny, nz), dtype=bool)
    t = int(ledge_thickness)
    s[:, :, :2] = True                                    # floor
    if ledge_height is None:
        ledge_height = max(4, nz // 3)
    half = nx // 2
    if side == "left":
        s[:half + 1, :, nz - t:] = True                   # overhang, left half
    else:
        s[half:, :, nz - t:] = True
    s[:t, :, :] = True                                    # close -x face
    s[nx - t:, :, :] = True                               # close +x face
    s[:, :t, :] = True                                    # close -y face
    s[:, ny - t:, :] = True                               # close +y face
    return s


def assert_closed_box(solid):
    """Verify no fluid site can wrap around through the periodic streaming
    topology in any lateral direction."""
    solid = np.asarray(solid).astype(bool)
    out = {}
    out["x_minus"] = bool(solid[0].all())
    out["x_plus"] = bool(solid[-1].all())
    out["y_minus"] = bool(solid[:, 0].all())
    out["y_plus"] = bool(solid[:, -1].all())
    out["all_closed"] = all(out.values())
    return out


def tube(nx, ny, nz, wall=1):
    """A vertical square capillary: solid everywhere except the interior
    column, closed (non-periodic) laterally."""
    s = np.ones((nx, ny, nz), dtype=bool)
    s[wall:nx - wall, wall:ny - wall, :] = False
    return s


# ----------------------------------------------------------------------
#  Measurement helpers
# ----------------------------------------------------------------------
def interface_position_1d(psi_prof):
    """Locate a single interface in a 1D profile.

    Precision matters here, so the location is taken from the interior
    node whose |psi| is smallest, with a linear interpolation to the
    neighbour of opposite sign.  A plain sign-change search fails on a
    symmetric tanh profile because psi is exactly 0 at the midpoint (so
    neither adjacent product is negative), and the periodic-wrap branch
    would then report the *other* interface implied by the wrap -- an
    artefact that made a perfectly stationary interface look as though it
    had jumped half a box.

    Limitation, stated rather than hidden: this assumes a single
    interface.  On a profile that has already broken up it reports the
    location of the smallest |psi|, which is a diagnostic and not a
    physical interface position.
    """
    p = np.asarray(psi_prof, dtype=np.float64)
    n = p.size
    if n < 3:
        return float("nan")
    i = int(np.argmin(np.abs(p[1:-1]))) + 1
    if abs(p[i]) < 1e-12:
        return float(i)
    for j in (i - 1, i + 1):
        if np.sign(p[j]) * np.sign(p[i]) < 0:
            f = p[i] / (p[i] - p[j])
            return float(i + f * (j - i))
    return float(i)


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


def interface_radius_profile(psi, solid):
    """Interface geometry of an axisymmetric blob sitting on a wall.

    Returns ``(zs, rs)``: for each fluid layer height ``z``, the radius at
    which the polar-averaged phase field crosses zero.  Layers whose
    crossing is not interior to the box are omitted.
    """
    psi = np.asarray(psi)
    solid = np.asarray(solid)
    nx, ny, nz = psi.shape
    cx, cy = (nx - 1) / 2.0, (ny - 1) / 2.0
    X, Y = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    rr = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    rmax = 0.5 * min(nx, ny) - 1.0
    bins = np.linspace(0.0, rmax, 24)
    centres = 0.5 * (bins[1:] + bins[:-1])
    zs, rs = [], []
    for k in range(nz):
        if solid[:, :, k].mean() > 0.5:
            continue
        layer = psi[:, :, k]
        prof = []
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = (rr >= lo) & (rr < hi)
            prof.append(layer[m].mean() if m.any() else np.nan)
        prof = np.asarray(prof)
        ok = np.isfinite(prof)
        if ok.sum() < 4:
            continue
        c = centres[ok]
        p = prof[ok]
        idx = np.where(np.sign(p[:-1]) * np.sign(p[1:]) < 0)[0]
        if idx.size == 0:
            continue
        i = idx[0]
        f = p[i] / (p[i] - p[i + 1])
        zs.append(float(k))
        rs.append(float(c[i] + f * (c[i + 1] - c[i])))
    return np.asarray(zs), np.asarray(rs)


def contact_angle_circle_fit(zs, rs, z_wall):
    """Contact angle from a circle fitted to the interface contour.

    Replaces the earlier spherical-cap estimate
    ``theta = 2 atan(apex / r_b)``, which external review B6/C2 flagged as
    unreliable: its error changed sign between validation passes for the
    same prescribed angle, and it returned NaN whenever the cap did not
    reach the first fluid layer.

    A sessile blob of circular cross-section has centre ``(0, z_c)`` and
    radius ``R``, so its contour satisfies ``r^2 + (z - z_c)^2 = R^2``.
    A least-squares fit gives

        cos(theta) = (z_c - z_wall) / R

    with ``theta`` measured **through the psi > 0 (red) phase**.  That
    convention is stated wherever an angle is reported from this function.

    Returns ``(theta_deg, R, z_c, rms)``; ``theta_deg`` is NaN when the fit
    fails or the fitted circle does not meet the wall plane.
    """
    zs = np.asarray(zs, dtype=float)
    rs = np.asarray(rs, dtype=float)
    if zs.size < 5:
        return float("nan"), float("nan"), float("nan"), float("nan")
    A = np.stack([2.0 * zs, np.ones_like(zs)], axis=1)
    b = rs ** 2 + zs ** 2
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    z_c, c0 = sol
    R2 = c0 + z_c ** 2
    if R2 <= 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    R = float(np.sqrt(R2))
    rms = float(np.sqrt(np.mean((A @ sol - b) ** 2)))
    cos_t = (z_c - z_wall) / R
    if cos_t < -1.0 or cos_t > 1.0:
        return float("nan"), R, float(z_c), rms
    return float(np.degrees(np.arccos(cos_t))), R, float(z_c), rms


def interface_height_field(psi, normal_axis=2):
    """z location of the psi = 0 crossing for every column along the other
    two axes."""
    p = np.moveaxis(np.asarray(psi), normal_axis, -1)
    flat = p.reshape(-1, p.shape[-1])
    out = np.full(flat.shape[0], np.nan)
    for j in range(flat.shape[0]):
        col = flat[j]
        idx = np.where(np.sign(col[:-1]) * np.sign(col[1:]) < 0)[0]
        if idx.size:
            i = idx[0]
            f = col[i] / (col[i] - col[i + 1])
            out[j] = i + f
    return out.reshape(p.shape[:-1])


def fourier_mode_amplitude(psi, wave_axis=0, normal_axis=2, k=1):
    """Amplitude of mode ``k`` of the interface height along ``wave_axis``.

    Replaces the earlier ``max|psi|`` comparison, which external review B7
    correctly identified as not a wave amplitude.
    """
    h = interface_height_field(psi, normal_axis=normal_axis)
    h = np.moveaxis(h, wave_axis, -1) if h.ndim > 1 else h
    line = h.reshape(-1, h.shape[-1]).mean(axis=0)
    n = line.size
    line = np.where(np.isfinite(line), line, np.nanmean(line))
    spec = np.fft.rfft(line - line.mean())
    if k >= spec.size:
        return float("nan")
    return float(2.0 * np.abs(spec[k]) / n)


def equivalent_radius(psi, threshold=0.0):
    """Equivalent-sphere radius of the psi > threshold region.

    Used as the *measured* equilibrium radius in the Laplace test, rather
    than the nominal initial radius that external review B8 flagged.
    """
    m = np.asarray(psi) > threshold
    V = float(m.sum())
    if V <= 0:
        return float("nan")
    return float((3.0 * V / (4.0 * np.pi)) ** (1.0 / 3.0))


def max_abs_over_time(trace, key):
    """Largest excursion (not merely the final value) of a tracked
    quantity.  External review B6 requires the maximum time-history
    excursion rather than an initial-to-final difference."""
    vals = [abs(t[key]) for t in trace if key in t and np.isfinite(t[key])]
    return float(max(vals)) if vals else float("nan")


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
