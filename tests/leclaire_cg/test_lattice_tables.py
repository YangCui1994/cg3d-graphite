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
    A = 1.5 * om * 0.05
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
