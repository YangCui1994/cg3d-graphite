"""Unit checks for the L17_CORE lattice tables and operators.

These run without any simulation.  They are the table-level fidelity gate:
if any of them fails, the candidate is not a Leclaire-2017 D3Q19
implementation regardless of what the canonical simulation matrix says.

Run:  python tests/leclaire_cg/test_lattice_tables.py
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "experimental"))

from leclaire_cg import lattice as L          # noqa: E402
from leclaire_cg import geometry as G_geom    # noqa: E402
from leclaire_cg import operators as op       # noqa: E402

TOL = 1e-12


def check(name, value, tol=TOL):
    ok = bool(np.all(np.abs(np.asarray(value, dtype=float)) <= tol))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: residual {value}")
    return ok


def main():
    results = []

    # ---- R1 Table IV / Table VI / Table VIII consistency --------------
    w = L.check_weights()
    for k, v in w.items():
        results.append(check(f"table.weights.{k}", v))

    m = L.check_mrt_matrix()
    for k, v in m.items():
        results.append(check(f"table.matrix.{k}", v))

    # Table XI rows 1 and 2 constant within each Table IV shell.  This is
    # the check that pins the (non-shell-major) Table IV grouping.
    results.append(check("table.shell_grouping", m["rows_shell_constant"], 0.0))

    # ---- shell structure ---------------------------------------------
    results.append(check("shell.counts",
                         [abs((L.SHELL == s).sum() - n)
                          for s, n in ((0, 1), (1, 6), (2, 12))], 0.0))
    results.append(check("shell.norms",
                         [abs(np.linalg.norm(L.E[L.SHELL == s], axis=-1).max()
                              - np.sqrt(s)) for s in (0, 1, 2)], 0.0))

    # ---- equilibrium reduction at alpha = W0 --------------------------
    # N^(e) must reduce to rho * W_i at u = 0, grad rho = 0 (R1 Eq.4).
    rho = np.full((2, 2, 2), 1.3)
    u = np.zeros(rho.shape + (3,))
    gr = np.zeros(rho.shape + (3,))
    nu = np.full(rho.shape, 0.1)
    neq = op.equilibrium(rho, u, gr, nu)
    results.append(check("equilibrium.zero_state_equals_rho_W",
                         np.abs(neq - rho[..., None] * L.W_I).max(), 1e-14))
    results.append(check("equilibrium.mass",
                         np.abs(neq.sum(axis=-1) - rho).max(), 1e-14))

    # ---- gradient sign and linear exactness ---------------------------
    # The gradient stencil samples field(x + c_i) while streaming moves
    # field(x) to x + c_i.  Confusing the two silently flips the sign of
    # the whole colour gradient, which inverts the recolouring's
    # segregation direction.  This check exists because that bug was made
    # once and must not come back.
    #
    # Evaluated on INTERIOR nodes only: the boxes are periodic, so a
    # globally linear test field is not linear across the wrap.
    n = 16
    X, Y, Z = np.meshgrid(np.arange(n), np.arange(n), np.arange(n),
                          indexing="ij")
    fluid = np.ones((n, n, n), dtype=bool)
    interior = np.zeros((n, n, n), dtype=bool)
    interior[2:-2, 2:-2, 2:-2] = True
    for axis, coef in ((0, 0.7), (1, -1.3), (2, 0.25)):
        lin = coef * (X, Y, Z)[axis].astype(float)
        g = op.gradient_isotropic(lin, fluid)
        want = np.zeros((n, n, n, 3))
        want[..., axis] = coef
        results.append(check(f"gradient.linear_exact_axis{axis}",
                             np.abs((g - want)[interior]).max(), 1e-12))

    # a monotonically DECREASING profile must give a negative gradient
    prof = -np.tanh((Z - n / 2.0) / 2.5)
    g = op.gradient_isotropic(prof, fluid)
    gz = g[..., 2][interior]
    results.append(check("gradient.sign_is_physical",
                         0.0 if gz.max() < 0 else 1.0, 0.0))
    # and it must match the analytic derivative to the stencil's own
    # truncation order.  The D3Q19 isotropic operator is exact for linear
    # fields and has a leading isotropic O(grad^3) error of (1/6)d^3/dz^3,
    # which for tanh(z/2.5) is ~0.011; the tolerance below reflects that
    # truncation, not an implementation defect.
    analytic = -(1.0 / 2.5) * (1.0 - np.tanh((Z - n / 2.0) / 2.5) ** 2)
    results.append(check("gradient.matches_analytic_tanh",
                         np.abs(g[..., 2][interior]
                                - analytic[interior]).max(), 5e-2))
    results.append(check("gradient.off_axis_is_zero",
                         np.abs(np.concatenate([g[..., 0][interior],
                                                g[..., 1][interior]])).max(),
                         1e-12))


    rng = np.random.default_rng(0)
    F = rng.normal(size=(3, 3, 3, 3))
    om = np.full((3, 3, 3), 1.0 / 3.0)
    dN = op.perturbation(F, om, 0.05)
    results.append(check("perturbation.mass", np.abs(dN.sum(axis=-1)).max(),
                         1e-14))
    mom = np.einsum("...i,ia->...a", dN, L.E.astype(float))
    results.append(check("perturbation.momentum", np.abs(mom).max(), 1e-14))

    # second moment must equal (2/9) A |F| (n n - delta), derived in
    # PAPER_FORMULATION.md section 5.2
    A = 2.25 * om * 0.05          # R1 Eq. (18): (9/4) omega sigma
    Fmag = np.linalg.norm(F, axis=-1)
    cumsum = dN.sum(axis=-1)
    Pi = np.einsum("...i,ia,ib->...ab", dN, L.E.astype(float),
                   L.E.astype(float))
    nn = F / Fmag[..., None]
    pred = (2.0 / 9.0) * (A * Fmag)[..., None, None] * (
        nn[..., :, None] * nn[..., None, :] - np.eye(3))
    results.append(check("perturbation.second_moment_vs_derivation",
                         np.abs(Pi - pred).max(), 1e-13))
    results.append(check("perturbation.mass_vs_derivation",
                         np.abs(cumsum).max(), 1e-14))

    # ---- R1 Eq. (18) constant ----------------------------------------
    # A = (9/4) omega_eff sigma = 2.25 omega sigma, NOT 1.5 omega sigma.
    # The 1.5 slip scales the delivered surface tension by 2/3 and is
    # invisible to every check that does not look at the amplitude, so it
    # is asserted here directly.
    F3 = np.zeros((2, 2, 2, 3))
    F3[..., 2] = 1.0
    om3 = np.full((2, 2, 2), 1.0)
    sig3 = 0.02
    dN3 = op.perturbation(F3, om3, sig3)
    # invert for A from the known bracket: with F = (0,0,|F|), the i = 3
    # direction (c = (0,0,-1)) has (F.c)^2/|F|^2 = 1 and W_3 = 1/18,
    # B_3 = 1/54, so dN_3 = A * 1 * (1/18 - 1/54) = A * 1/27
    A_impl = dN3[0, 0, 0, 3] * 27.0
    results.append(check("perturbation.A_equals_9over4_omega_sigma",
                         [abs(A_impl - 2.25 * sig3),
                          0.0 if abs(A_impl - 1.5 * sig3) > 1e-6 else 1.0],
                         1e-12))

    # ---- R1 X_W gradient rule (blocker B2) -----------------------------
    # R1: isotropic in the bulk, standard 1D forward/backward/centred
    # Cartesian differences at X_W.  Checked on an explicit staggered
    # configuration so each of the three one-sided branches is exercised.
    n = 12
    fluid = np.ones((n, n, n), dtype=bool)
    wall = np.zeros((n, n, n), dtype=bool)
    Xa, Ya, Za = np.meshgrid(np.arange(n), np.arange(n), np.arange(n),
                             indexing="ij")
    interior = np.zeros((n, n, n), dtype=bool)
    interior[2:-2, 2:-2, 2:-2] = True
    lin = 0.7 * Xa - 1.3 * Ya + 0.25 * Za
    g = op.gradient(lin.astype(float), fluid, wall)
    results.append(check("grad_l17.bulk_linear_exact_x",
                         np.abs(g[..., 0][interior] - 0.7).max(), 1e-12))
    results.append(check("grad_l17.bulk_linear_exact_y",
                         np.abs(g[..., 1][interior] + 1.3).max(), 1e-12))

    # a wall site: fluid in +x and -x, solid in +y -> centred x, one-sided y
    fld = fluid.copy()
    wall2 = np.zeros_like(fluid)
    fld[6, 6, 6] = True
    fld[5, 6, 6] = True
    fld[7, 6, 6] = True
    fld[6, 5, 6] = True            # -y fluid
    fld[6, 7, 6] = False           # +y solid
    fld[6, 6, 5] = False           # -z solid
    fld[6, 6, 7] = False           # +z solid  -> both z neighbours missing
    wall2[6, 6, 6] = True
    lin2 = 2.0 * Xa + 3.0 * Ya + 5.0 * Za
    g2 = op.gradient(lin2.astype(float), fld, wall2)
    results.append(check("grad_l17.wall_centred_available_axis",
                         abs(g2[6, 6, 6, 0] - 2.0), 1e-12))
    results.append(check("grad_l17.wall_backward_when_plus_missing",
                         abs(g2[6, 6, 6, 1] - 3.0), 1e-12))
    results.append(check("grad_l17.wall_zero_when_both_missing",
                         abs(g2[6, 6, 6, 2] - 0.0), 1e-12))

    # the retained experimental variant must be reachable and labelled
    gv = op.gradient(lin.astype(float), fluid, wall,
                     variant="isotropic_renormalised")
    results.append(check("grad_variant.experimental_reachable",
                         np.abs(gv[..., 0][interior] - 0.7).max(), 1e-12))
    try:
        op.gradient(lin.astype(float), fluid, wall, variant="nonsense")
        results.append(check("grad_variant.rejects_unknown", 1.0, 0.0))
    except ValueError:
        results.append(check("grad_variant.rejects_unknown", 0.0, 0.0))

    # ---- R1 Appendix (A1)-(A4) at NON-ZERO u and grad rho --------------
    # These are the identities the Table IV weights were derived from, and
    # they are the gate that catches the B1 defect: at u = 0 or grad rho = 0
    # the correct and incorrect forms of the psi_i term collapse to the same
    # value, so a zero-state check cannot see it.  Evaluated on random fields.
    rng2 = np.random.default_rng(20260927)
    shape = (4, 3, 2)
    rho_r = 0.8 + 0.6 * rng2.random(shape)
    u_r = 0.25 * (rng2.random(shape + (3,)) - 0.5)
    g_r = 2.0 * (rng2.random(shape + (3,)) - 0.5)
    nu_r = 0.05 + 0.2 * rng2.random(shape)
    ne = op.equilibrium(rho_r, u_r, g_r, nu_r)
    Ef = L.E.astype(float)
    ud = np.einsum("...a,...a->...", u_r, g_r)

    m0 = ne.sum(axis=-1)
    results.append(check("A1_mass", np.abs(m0 - rho_r).max(), 1e-14))

    m1 = np.einsum("...i,ia->...a", ne, Ef)
    results.append(check("A2_momentum", np.abs(m1 - rho_r[..., None] * u_r).max(),
                         1e-14))

    m2 = np.einsum("...i,ia,ib->...ab", ne, Ef, Ef)
    P = rho_r[..., None, None] / 3.0 * np.eye(3)
    rr = rho_r[..., None, None] * (u_r[..., :, None] * u_r[..., None, :])
    visc = nu_r[..., None, None] * (
        u_r[..., :, None] * g_r[..., None, :]
        + g_r[..., :, None] * u_r[..., None, :]
        + ud[..., None, None] * np.eye(3))
    results.append(check("A3_second_moment", np.abs(m2 - P - rr - visc).max(), 1e-14))

    m3 = np.einsum("...i,ia,ib,ic->...abc", ne, Ef, Ef, Ef)
    I3 = np.eye(3)
    # T_mno = (rho/3) ( u_m delta_no + u_n delta_mo + u_o delta_mn )
    want3 = (rho_r[..., None, None, None] / 3.0) * (
        np.einsum("...m,no->...mno", u_r, I3)
        + np.einsum("...n,mo->...mno", u_r, I3)
        + np.einsum("...o,mn->...mno", u_r, I3))
    results.append(check("A4_third_moment", np.abs(m3 - want3).max(), 1e-13))

    # the B1 defect would break A1 and A3; assert that explicitly so a
    # regression cannot re-introduce it silently
    bad = ne.copy()
    bad += (nu_r[..., None] * (L.PSI_I.astype(float) * np.einsum(
        "ia,...a->...i", Ef, g_r) - L.PSI_I.astype(float) * ud[..., None]))
    results.append(check("A1_would_fail_with_c_i_dot_grad_rho_form",
                         [0.0 if np.abs(bad.sum(axis=-1) - rho_r).max() > 1e-6
                          else 1.0], 0.0))

    # ---- WETTING CONVENTION LOCK (normative, geometric, non-LBM) -------
    # Authority: docs/research/leclaire_cg/WETTING_PHASE_CONVENTION.md.
    #     g     = 1 solid, 0 fluid
    #     n_w   = -grad(g)/|grad(g)|      -> solid into fluid
    #     F     = grad(psi)               -> gas(blue) toward liquid(red)
    #     theta = angle(F, n_w)           -> measured through LIQUID/red
    # A sessile droplet must never be used to pick this sign; this block is
    # the authority and the droplet test only consumes it.
    n_c = 24
    solid_w = np.zeros((n_c, n_c, n_c), dtype=bool)
    solid_w[:, :, :3] = True                      # floor: solid for z < 3
    fluid_w = ~solid_w
    nw_w = op.wall_normals(solid_w, sign=-1.0)    # canonical
    wall_nodes = np.zeros_like(solid_w)
    for _i in range(1, 19):
        wall_nodes |= op._shift_fwd(solid_w, L.E[_i]).astype(bool)
    wall_nodes &= fluid_w
    # The box is periodic, so the wrap makes the topmost layer adjacent to
    # the solid at z = 0 as well.  Restrict to the floor band so the
    # assertion tests the floor normal and not the wrap-implied one.
    band = np.zeros_like(solid_w)
    band[:, :, 3:8] = True
    wall_nodes &= band
    nw_at_wall = nw_w[wall_nodes]
    # for a flat floor the canonical normal must point solid -> fluid (+z)
    results.append(check("convention.nw_points_solid_to_fluid",
                         [np.abs(nw_at_wall[:, 0]).max(),
                          np.abs(nw_at_wall[:, 1]).max(),
                          np.abs(nw_at_wall[:, 2] - 1.0).max()], 1e-9))

    # the specified analytic branch: F = (-sin t, 0, cos t) with n_w = +z
    # gives angle(F, n_w) = t, which is the angle through the liquid
    # R1's secant is deliberately stopped at n = 2 because in a simulation it
    # is re-applied every step from a good initial guess.  A single
    # application is therefore a partial step, not a solver; the analytic
    # test must verify that its FIXED POINT is the requested branch, i.e.
    # that iterating it converges to theta and not to the complementary one.
    for t_deg in (60.0, 90.0, 120.0):
        t = np.deg2rad(t_deg)
        for start_deg in (t_deg, 180.0 - t_deg, 90.0):
            sd = np.deg2rad(start_deg)
            Fx = np.zeros((n_c, n_c, n_c, 3))
            Fx[..., 0] = -np.sin(sd)
            Fx[..., 2] = np.cos(sd)
            for _ in range(40):
                Fx = op.secant_contact_angle(Fx, wall_nodes, nw_w, t)
                Fx = Fx / np.maximum(np.linalg.norm(Fx, axis=-1,
                                                    keepdims=True), 1e-30)
            ang = np.degrees(np.arccos(np.clip(
                np.einsum("...a,...a->...", Fx[wall_nodes], nw_w[wall_nodes]),
                -1.0, 1.0)))
            results.append(check(
                f"convention.secant_fixed_point_{int(t_deg)}"
                f"_from_{int(start_deg)}",
                np.abs(ang - t_deg).max(), 1e-6))

    # flipping n_w must produce the COMPLEMENTARY branch (180 - theta) and
    # must therefore be rejected by the canonical convention
    nw_flip = op.wall_normals(solid_w, sign=+1.0)
    t60 = np.deg2rad(60.0)
    F_analytic = np.zeros((n_c, n_c, n_c, 3))
    F_analytic[..., 0] = -np.sin(t60)
    F_analytic[..., 2] = np.cos(t60)
    F_bad = op.secant_contact_angle(F_analytic.copy(), wall_nodes, nw_flip, t60)
    ang_bad = np.degrees(np.arccos(np.clip(
        np.einsum("...a,...a->...", F_bad[wall_nodes], nw_w[wall_nodes]),
        -1.0, 1.0)))
    results.append(check("convention.flipped_nw_is_complementary",
                         0.0 if np.abs(ang_bad.mean() - (180.0 - 60.0)) < 25.0
                         else 1.0, 0.0))
    results.append(check("convention.flipped_nw_fails_canonical_gate",
                         0.0 if np.abs(ang_bad.mean() - 60.0) > 15.0 else 1.0,
                         0.0))

    # the canonical sign is derived, not defaulted: the solver must expose
    # -1 and must mark any override non-canonical
    import inspect as _ins
    from leclaire_cg.solver import LeclaireCG3D as _S
    _sig = _ins.signature(_S.__init__).parameters
    results.append(check("convention.no_physical_wetting_sign_parameter",
                         0.0 if "wetting_sign" not in _sig else 1.0, 0.0))
    results.append(check("convention.override_is_labelled_debug",
                         0.0 if "nw_sign_override" in _sig else 1.0, 0.0))

    # ---- contact-angle instrument validated on a synthetic contour -----
    # The circle-fit instrument replaced a spherical-cap estimate whose
    # error changed sign between passes.  Before it is trusted on a
    # simulation it must recover a known angle from an exact circle.
    import math as _m
    for ang in (30.0, 60.0, 90.0, 120.0, 150.0):
        R_t = 8.0
        zc_t = R_t * _m.cos(_m.radians(ang))
        z_top = zc_t + R_t          # apex of the cap; contour stops here
        zs_t = np.linspace(0.5, max(z_top - 0.5, 1.0), 24)
        rs_t = np.sqrt(np.maximum(R_t ** 2 - (zs_t - zc_t) ** 2, 0.0))
        th, Rf, zcf, rms = G_geom.contact_angle_circle_fit(zs_t, rs_t, 0.0)
        results.append(check(f"instrument.circle_fit_recovers_{int(ang)}deg",
                             abs(th - ang), 0.05))

    # ---- recolouring conserves both components exactly ----------------
    Nr = rng.random((3, 3, 3, 19))
    fr = rng.random((3, 3, 3))
    rho_r = 0.4 + 0.2 * fr
    rho_b = 1.0 - rho_r
    N = Nr / Nr.sum(axis=-1, keepdims=True) * (rho_r + rho_b)[..., None]
    F2 = rng.normal(size=(3, 3, 3, 3))
    Nr2, Nb2 = op.recolor(N, rho_r, rho_b, F2, beta=0.7)
    results.append(check("recolor.red_sum_equals_rho_r",
                         np.abs(Nr2.sum(axis=-1) - rho_r).max(), 1e-14))
    results.append(check("recolor.blue_sum_equals_rho_b",
                         np.abs(Nb2.sum(axis=-1) - rho_b).max(), 1e-14))
    results.append(check("recolor.total_is_colour_blind",
                         np.abs(Nr2 + Nb2 - N).max(), 1e-14))

    # ---- bounce-back is an involution on the opposite map -------------
    # BB(BB(x)) == x, and fluid entries are never written.
    arr = rng.random((2, 2, 2, 19))
    solid = np.zeros((2, 2, 2), dtype=bool)
    solid[0, 0, 0] = True
    fluid = ~solid
    b1 = op.bounce_back_fullway(arr.copy(), solid)
    b2 = op.bounce_back_fullway(b1.copy(), solid)
    results.append(check("bounceback.double_application_is_identity",
                         np.abs(b2 - arr).max(), 0.0))
    results.append(check("bounceback.untouched_fluid",
                         np.abs(b1[fluid] - arr[fluid]).max(), 0.0))
    results.append(check("bounceback.solid_is_opposite_permuted",
                         np.abs(b1[solid] - arr[solid][:, L.OPP]).max(), 0.0))

    # ---- streaming is a pure shift -----------------------------------
    # st[x + c_i, i] == a[x, i].  For the step from x=0 to x=1 along the
    # x axis that is every direction with c_x = +1 (five of them in the
    # R1 Table IV ordering), and no others.
    a = rng.random((4, 1, 1, 19))
    st = op.stream(a)
    fwd = [int(j) for j in range(19) if L.E[j][0] == 1]
    oth = [int(j) for j in range(19) if L.E[j][0] != 1 and j != 0]
    results.append(check("stream.forward_shift_x",
                         np.abs(st[1, 0, 0, fwd] - a[0, 0, 0, fwd]).max(), 0.0))
    results.append(check("stream.non_forward_directions_differ",
                         0.0 if np.abs(st[1, 0, 0, oth]
                                       - a[0, 0, 0, oth]).max() > 1e-6
                         else 1.0, 0.0))
    results.append(check("stream.total_mass_preserved",
                         abs(st.sum() - a.sum()), 1e-14))

    print()
    n_pass = int(np.sum(results))
    print(f"{n_pass}/{len(results)} checks passed")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
