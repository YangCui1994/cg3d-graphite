"""Operators for the Leclaire-2017 D3Q19 colour-gradient model.

Task: BI-CG-LECLAIRE-IMPLEMENTATION-001.

Every operator names its source equation.  Sources:
  R1 = Leclaire et al., Phys. Rev. E 95, 033306 (2017)
       (canonical; see docs/research/leclaire_cg/PAPER_FORMULATION.md)
  R3 = Akai, Bijeljic, Blunt, Adv. Water Resour. 116, 56 (2018)
       (later wetting variant; switchable, default off)

Conventions, all stated rather than assumed:

* ``shape`` of a distribution array is ``(nx, ny, nz, 19)``; axis 3 is the
  R1 Table IV velocity index.
* ``solid`` is an integer mask, non-zero == solid.
* The wall-normal sign and the contact-angle phase convention are NOT
  fixed by R1 (PAPER_FORMULATION.md section 11, item 2).  Both are exposed
  as explicit switches so the validation can report which convention the
  measured angles are consistent with.
"""

from __future__ import annotations

import numpy as np

from . import lattice as L

EPS = 1e-30


# ======================================================================
#  Macro quantities
# ======================================================================
def macroscopic(N):
    """rho = sum_i N_i ; rho*u = sum_i N_i c_i      (R1 Eqs. 2-3)."""
    rho = N.sum(axis=-1)
    mom = np.einsum("...i,ia->...a", N, L.E.astype(N.dtype))
    u = np.zeros_like(mom)
    safe = np.abs(rho) > EPS
    u[safe] = mom[safe] / rho[safe, None]
    return rho, u


# ======================================================================
#  Equilibrium, R1 Eq. (4)
# ======================================================================
def equilibrium(rho, u, grad_rho, nu, alpha=L.ALPHA_UNIT):
    """Colour-blind equilibrium N^(e), R1 Eq. (4) + Eq. (5).

        N^(e)_i = nu [ psi_i (u . grad rho) + xi_i (G : c_i x c_i) ]
                  + rho [ phi_i + phii_i * alpha
                          + W_i (3 c_i.u + 4.5 (c_i.u)^2 - 1.5 u.u) ]

    with G = u x grad(rho) + (u x grad(rho))^T, so that

        G : c_i x c_i = 2 (c_i . u) (c_i . grad rho).

    Implemented directly in distribution space and *not* in closed moment
    form: IMPLEMENTATION_PLAN.md section 2.  The psi_i / xi_i terms are the
    paper's density-gradient contribution and are structurally impossible
    to drop here.
    """
    rho = np.asarray(rho)
    shape = rho.shape + (19,)
    ci = L.E.astype(rho.dtype)
    cu = np.einsum("ia,...a->...i", ci, u)                 # c_i . u
    cd = np.einsum("ia,...a->...i", ci, grad_rho)          # c_i . grad rho
    uu = np.einsum("...a,...a->...", u, u)

    rho_e = np.asarray(rho)[..., None]
    nu_e = np.asarray(nu)[..., None]

    out = np.zeros(shape, dtype=rho.dtype)
    out += rho_e * (
        L.PHI_I.astype(rho.dtype)
        + L.PHII_I.astype(rho.dtype) * alpha
        + L.W_I.astype(rho.dtype) * (3.0 * cu + 4.5 * cu * cu - 1.5 * uu[..., None])
    )
    out += nu_e * (
        L.PSI_I.astype(rho.dtype) * cd
        + L.XI_I.astype(rho.dtype) * 2.0 * cu * cd
    )
    return out


def equilibrium_zero_velocity(rho, alpha=L.ALPHA_UNIT):
    """N^(e)(rho, 0) used by the recoloring operator (R1 Eqs. 19-20).

    At u = 0 both the psi_i and xi_i terms of Eq. (4) vanish (both are
    linear in u), leaving rho (phi_i + phii_i * alpha), which equals
    rho * W_i at alpha = W0.  Derived in PAPER_FORMULATION.md section 6.1.
    """
    rho = np.asarray(rho)
    return np.asarray(rho)[..., None] * (
        L.PHI_I.astype(rho.dtype) + L.PHII_I.astype(rho.dtype) * alpha
    )


# ======================================================================
#  Viscosity, R1 Eqs. (13)-(14)
# ======================================================================
def viscosity_harmonic(rho_r, rho_b, nu_r, nu_b):
    """1/nu = (rho_r/rho)/nu_r + (rho_b/rho)/nu_b        (R1 Eq. 13)."""
    rho = rho_r + rho_b
    inv = np.zeros_like(rho)
    safe = np.abs(rho) > EPS
    inv[safe] = ((rho_r[safe] / rho[safe]) / nu_r
                 + (rho_b[safe] / rho[safe]) / nu_b)
    nu = np.full_like(rho, np.nan)
    ok = safe & (np.abs(inv) > EPS)
    nu[ok] = 1.0 / inv[ok]
    return nu


def omega_eff(nu):
    """omega_eff = 2 / (6 nu + 1)                         (R1 Eq. 14)."""
    return 2.0 / (6.0 * np.asarray(nu) + 1.0)


# ======================================================================
#  Colour gradient, R1 Eq. (17) with the fourth-order isotropic stencil
# ======================================================================
def _shift(arr, c):
    """``out[x] = arr[x - c]`` -- the STREAMING direction convention."""
    return np.roll(arr, shift=(int(c[0]), int(c[1]), int(c[2])), axis=(0, 1, 2))


def _shift_fwd(arr, c):
    """``out[x] = arr[x + c]`` -- the GRADIENT-sampling convention.

    These two are easy to confuse and the consequence is a silent sign
    flip of the whole colour gradient, which inverts the recoloring's
    segregation direction.  ``test_lattice_tables.py`` therefore asserts
    the gradient sign explicitly.
    """
    return np.roll(arr, shift=(-int(c[0]), -int(c[1]), -int(c[2])),
                   axis=(0, 1, 2))


def gradient_isotropic(field, fluid, renormalize=True):
    """F = grad(field) with the D3Q19 fourth-order isotropic operator

        F_a = 3 sum_i W_i c_ia field(x + c_i)

    sampled over FLUID neighbours only.  R1 section II.E states the
    gradient is built "using only the currently known information from the
    bulk fluid lattice sites", i.e. solid neighbours carry no phase-field
    value.  Whether the stencil is then renormalised is NOT stated by R1;
    ``renormalize=True`` (the default) divides by the trace factor

        (1/3) sum_i 3 W_i |c_i|^2 = sum_i W_i |c_i|^2

    which is exactly 1 for the complete D3Q19 stencil (so the operator is
    unchanged in the bulk) and restores the leading-order gradient at a
    partially truncated wall stencil.  Dividing by ``sum_i 3 W_i``
    instead would be wrong: that sum is 2, not 1, and would scale every
    gradient by 0.5 -- which is a real error, because the perturbation
    uses |F| (PAPER_FORMULATION.md Eq. 16) while the recolouring uses
    only the orientation.

    Isotropy of this operator on D3Q19 is derived in PAPER_FORMULATION.md
    section 4.3 (identity second-rank sum, isotropic fourth-rank sum).
    """
    field = np.asarray(field)
    fluid = np.asarray(fluid)
    out = np.zeros(field.shape + (3,), dtype=field.dtype)
    wsum = np.zeros(field.shape, dtype=field.dtype)
    ci = L.E.astype(field.dtype)
    for i in range(19):
        if i == 0:
            continue
        fs = _shift_fwd(field, L.E[i])
        ms = _shift_fwd(fluid, L.E[i]).astype(bool)
        coeff = 3.0 * L.W_I[i]
        out += ms[..., None] * coeff * ci[i][None, None, None, :] * fs[..., None]
        wsum += ms * coeff * float(np.dot(L.E[i], L.E[i])) / 3.0
    if renormalize:
        ok = wsum > EPS
        out[ok] /= wsum[ok, None]
    return out


# ======================================================================
#  Wall normals, R1 Eqs. (34)-(38)
# ======================================================================
def smooth_solid(solid, passes=L.SMOOTH_PASSES):
    """Three passes of the D3Q27-weighted 3x3x3 smoothing (R1 Eqs. 34-38).

    Periodic wrap is used at the box faces; wall preprocessing is
    therefore only physical where the solid mask is not touching a
    periodic pair, which every wall-bounded test in this task satisfies.
    """
    g = (np.asarray(solid) != 0).astype(np.float64)
    k = L.smoothing_kernel()
    for _ in range(passes):
        acc = np.zeros_like(g)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for kk in (-1, 0, 1):
                    acc += k[i + 1, j + 1, kk + 1] * np.roll(
                        g, shift=(i, j, kk), axis=(0, 1, 2))
        g = acc
    return g


def wall_normals(solid, sign=+1.0):
    """n_w = grad(g_smoothed) at fluid sites (R1 Eqs. 34-38).

    R1 does not fix whether ``n_w`` points into the fluid or into the
    solid; ``sign`` selects the convention and the validation reports
    which one reproduces the prescribed contact angle.
    """
    g = smooth_solid(solid)
    fluid = (np.asarray(solid) == 0)
    nw = gradient_isotropic(g, fluid, renormalize=False)
    nrm = np.linalg.norm(nw, axis=-1, keepdims=True)
    ok = nrm[..., 0] > EPS
    nw = np.zeros_like(nw)
    nw[ok] = sign * nw[ok] / nrm[ok]
    return nw


# ======================================================================
#  Wetting boundary condition, R1 Eqs. (30)-(33)
# ======================================================================
def secant_contact_angle(F, wall_mask, nw, theta_c, lam=0.5):
    """Rotate the colour-gradient orientation at X_W so that it forms
    ``theta_c`` with ``n_w``, preserving |F|.

    R1 Eqs. (30)-(33):
        f(v)   = v.n_w - |v| cos(theta_c)
        v0     = n_c
        v1     = n_c - lam (n_c + n_w)
        v2     = (v0 f(v1) - v1 f(v0)) / (f(v1) - f(v0))
    R1 uses lam = 1/2 and always stops at n = 2; v2 is then normalised.
    """
    F = np.array(F, dtype=F.dtype, copy=True)
    mag = np.linalg.norm(F, axis=-1)
    sel = wall_mask & (mag > EPS)
    if not np.any(sel):
        return F
    nc = F[sel] / mag[sel, None]
    w = nw[sel]
    cos_t = np.cos(theta_c)

    def f(v):
        return np.einsum("...a,...a->...", v, w) - np.linalg.norm(v, axis=-1) * cos_t

    v0 = nc
    v1 = nc - lam * (nc + w)
    f0 = f(v0)
    f1 = f(v1)
    den = f1 - f0
    v2 = np.array(v0, copy=True)
    good = np.abs(den) > 1e-14
    v2[good] = (v0[good] * f1[good, None] - v1[good] * f0[good, None]) / den[good, None]
    nrm = np.linalg.norm(v2, axis=-1, keepdims=True)
    nrm_ok = nrm[..., 0] > 1e-14
    out = nc.copy()
    out[nrm_ok] = v2[nrm_ok] / nrm[nrm_ok]
    F[sel] = out * mag[sel, None]
    return F


def wetting_akai(F, wall_mask, nw, theta_c, solid_extrap=None):
    """Later wetting variant (R3 Eqs. 2-4), switchable.

    R3 replaces R1's degenerate secant with a closed-form rotation:
        n* = -grad(rho_N*)/|grad(rho_N*)|
        n+/- = [(cos t -/+ sin t cos t')/sin t'] n_s + [sin t/sin t'] n*
        t'   = arccos(n_s . n*)
        n* <- whichever of n+/- is closer to the original n*
    R3 also extrapolates the colour function onto the solid-boundary
    nodes by a lattice-weighted average over adjacent boundary-fluid
    nodes (its Eq. 2).  ``solid_extrap`` carries that estimate; it is
    supplied by the caller because it needs the C_SB / C_FB site classes.
    """
    F = np.array(F, dtype=F.dtype, copy=True)
    mag = np.linalg.norm(F, axis=-1)
    sel = wall_mask & (mag > EPS)
    if not np.any(sel):
        return F
    ns = nw[sel]
    nstar = -F[sel] / mag[sel, None]          # R3 Eq. (3)
    cos_tp = np.clip(np.einsum("...a,...a->...", ns, nstar), -1.0, 1.0)
    tp = np.arccos(cos_tp)
    sin_tp = np.sin(tp)
    ok = np.abs(sin_tp) > 1e-8
    st = np.sin(theta_c)
    ct = np.cos(theta_c)
    other = np.array(nstar, copy=True)
    if np.any(ok):
        csp = np.cos(tp[ok])
        a = (ct - st * csp) / sin_tp[ok]
        b = st / sin_tp[ok]
        n_plus = a[..., None] * ns[ok] + b[..., None] * nstar[ok]
        a2 = (ct + st * csp) / sin_tp[ok]
        n_minus = a2[..., None] * ns[ok] + b[..., None] * nstar[ok]
        for arr in (n_plus, n_minus):
            nn = np.linalg.norm(arr, axis=-1, keepdims=True)
            bad = nn[..., 0] <= 1e-14
            if np.any(bad):
                arr[bad] = nstar[ok][bad]
            else:
                arr /= nn
        d_p = np.linalg.norm(n_plus - nstar[ok], axis=-1)
        d_m = np.linalg.norm(n_minus - nstar[ok], axis=-1)
        pick_plus = d_p <= d_m
        chosen = np.where(pick_plus[..., None], n_plus, n_minus)
        other[ok] = chosen
    F[sel] = other * mag[sel, None]
    return F


# ======================================================================
#  Perturbation operator, R1 Eqs. (15)-(18)
# ======================================================================
def perturbation(F, omega, sigma, coeff_mode="paper"):
    """dN_i = A |F| [ W_i (F.c_i)^2/|F|^2 - B_i ]       (R1 Eq. 16)

    A = (9/4) omega_eff sigma                          (R1 Eq. 18)

    Added to the POST-collision colour-blind N_i directly (R1 step 4),
    i.e. NOT relaxed -- this is the structural difference recorded in
    CURRENT_VS_LECLAIRE_MAP.md section A.8.

    ``coeff_mode='capA'`` reproduces the current production calibration
    A |F| -> CapA |F| so the two can be compared under one solver.
    """
    mag = np.linalg.norm(F, axis=-1)
    ok = mag > EPS
    ci = L.E.astype(F.dtype)
    Fc = np.einsum("ia,...a->...i", ci, F)
    out = np.zeros(F.shape[:-1] + (19,), dtype=F.dtype)
    if not np.any(ok):
        return out
    m = mag[ok]
    if coeff_mode == "paper":
        A = 1.5 * omega[ok] * sigma        # (9/4) * omega * sigma
    elif coeff_mode == "capA":
        A = sigma                          # production-style, no omega
    else:
        raise ValueError(f"unknown coeff_mode {coeff_mode!r}")
    fc = Fc[ok]
    out_ok = (
        (fc * fc / (m * m)[..., None]) * L.W_I.astype(F.dtype)
        - L.B_I.astype(F.dtype)
    ) * (A * m)[..., None]
    out[ok] = out_ok
    return out


# ======================================================================
#  Recoloring, R1 Eqs. (19)-(20)
# ======================================================================
# R1 opposite pairs under Table IV ordering: (1,10) (2,11) (3,12) (4,13)
# (5,14) (6,15) (7,16) (8,17) (9,18).
PAIRS = [(i, int(L.OPP[i])) for i in range(1, 10)]


def recolor(N, rho_r, rho_b, F, beta, u=None, alpha=L.ALPHA_UNIT,
            form="paper", fluid=None, prev=None):
    """Split the colour-blind N into (N_r, N_b).

    R1 Eqs. (19)-(20), pairwise form derived in PAPER_FORMULATION.md
    section 6.2 (the two members of an opposite pair receive equal and
    opposite increments because cos(theta_opp(i)) = -cos(theta_i)):

        dN_i = +beta (rho_r rho_b / rho) (phi_i + phii_i alpha) cos(theta_i)
        dN_opp(i) = -dN_i
        N_r,i += dN_i ; N_b,i -= dN_i

    The rest population i = 0 is untouched (c_0 = 0 => cos(theta_0) := 0),
    which is the convention that makes sum_i N_r,i == rho_r exactly.

    ``fluid`` restricts the recolouring to x in X_F as R1 step (5) states.
    It is not cosmetic: at a solid node the colour fractions are
    meaningless (rho can be at the f64 floor) and an unmasked evaluation
    both overflows and injects non-R1 colour arithmetic into the
    bounce-back.

    ``form='min_variant'`` replaces the amplitude with the current
    production law ``min(g_r[i], g_r[j], g_b[i], g_b[j])`` evaluated from
    the equilibrium colour split at (rho_r, u) / (rho_b, u).  It exists
    only for the attribution ablation in FOLLOWUP_OPTIMIZATION_MAP.md F1
    and is never a paper-faithful arm.
    """
    rho = rho_r + rho_b
    safe = np.abs(rho) > 1e-12
    fr = np.zeros_like(rho)
    fb = np.zeros_like(rho)
    fr[safe] = rho_r[safe] / rho[safe]
    fb[safe] = rho_b[safe] / rho[safe]
    Nr_new = fr[..., None] * N
    Nb_new = fb[..., None] * N
    if fluid is None:
        Nr, Nb = Nr_new, Nb_new
    else:
        if prev is None:
            raise ValueError("fluid mask given without the incoming colour fields")

        # R1 step (5) acts on x in X_F only.  At a solid node the streamed
        # colour populations must pass through UNCHANGED; recomputing them
        # as (rho_k/rho) N there would divide by a rho that is at the f64
        # floor and silently destroy the colour mass the streaming
        # delivered.  ``prev`` supplies those untouched values.
        Nr = np.where(fluid[..., None], Nr_new, prev[0])
        Nb = np.where(fluid[..., None], Nb_new, prev[1])

    mag = np.linalg.norm(F, axis=-1)
    live = safe & (mag > EPS)
    if fluid is not None:
        live = live & np.asarray(fluid)
    if not np.any(live):
        return Nr, Nb

    ci = L.E.astype(F.dtype)
    cnorm = np.linalg.norm(ci, axis=-1)

    if form == "paper":
        N0 = equilibrium_zero_velocity(rho, alpha)
        # written as (rho_r/rho)(rho_b/rho) rather than
        # (rho_r rho_b)/rho^2 so that a small-but-finite rho cannot
        # underflow the denominator and produce inf/NaN
        pref = np.zeros_like(rho)
        pref[live] = beta * fr[live] * fb[live]
    elif form == "min_variant":
        if u is None:
            raise ValueError("min_variant needs the local velocity u")
        gr = equilibrium(rho_r, u, np.zeros_like(F), np.zeros_like(rho), alpha)
        gb = equilibrium(rho_b, u, np.zeros_like(F), np.zeros_like(rho), alpha)
        pref = None
    else:
        raise ValueError(f"unknown recolor form {form!r}")

    for i, j in PAIRS:
        cos_i = np.zeros_like(rho)
        cos_i[live] = np.einsum("a,...a->...", ci[i], F[live]) / (
            cnorm[i] * mag[live])
        if form == "paper":
            amp = pref * cos_i * N0[..., i]
        else:
            amp = np.minimum(np.minimum(gr[..., i], gr[..., j]),
                             np.minimum(gb[..., i], gb[..., j])) * cos_i
            amp[~live] = 0.0
        Nr[..., i] += amp
        Nr[..., j] -= amp
        Nb[..., i] -= amp
        Nb[..., j] += amp
    return Nr, Nb


# ======================================================================
#  Solid handling, R1 step (6): full-way bounce-back on solid nodes
# ======================================================================
def bounce_back_fullway(arr, solid):
    """N_i(x) = N_opp(i)(x) for x in X_S, applied per colour."""
    out = arr
    mask = np.asarray(solid) != 0
    if not np.any(mask):
        return out
    out[mask] = out[mask][:, L.OPP]
    return out


# ======================================================================
#  Streaming, R1 step (7)
# ======================================================================
def stream(arr, out=None):
    """N_i(x + c_i) = N_i(x), periodic wrap."""
    if out is None:
        out = np.empty_like(arr)
    for i in range(19):
        out[..., i] = _shift(arr[..., i], L.E[i])
    return out
