"""D3Q19 lattice tables for the Leclaire-2017 colour-gradient model.

Task: BI-CG-LECLAIRE-IMPLEMENTATION-001
Source of every table: Leclaire et al., Phys. Rev. E 95, 033306 (2017),
Appendix, Tables IV / VI / VII / VIII / XI.  See
``docs/research/leclaire_cg/PAPER_FORMULATION.md`` sections 0.1-0.2, 0.3,
2.5, 2.6 for the derivations that pin the values used here.

This module is deliberately self-contained: it imports nothing from the
production solver line (see IMPLEMENTATION_PLAN.md section 1).

Velocity ordering is R1's Table IV ordering and MUST NOT be reordered --
Tables VII, VIII and XI are only valid in this ordering (R1, journal
033306-5: "all the matrices and indexes are presented here with the same
ordering of the lattice connectivity vectors").
"""

from __future__ import annotations

import numpy as np

# ----------------------------------------------------------------------
# Table IV -- D3Q19 connectivity vectors, R1 ordering.
#
# IMPORTANT: R1's Table IV ordering is NOT shell-major.  Indices 10, 11, 12
# are the POSITIVE axis directions, so the shells are
#     shell 0 (|c|^2 = 0): {0}
#     shell 1 (|c|^2 = 1): {1, 2, 3, 10, 11, 12}
#     shell 2 (|c|^2 = 2): {4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18}
# This is confirmed independently by Table XI row 1, whose 19 entries are
# constant within each shell only under this grouping (-30 / -11 x6 / 8 x12).
# (The production solver uses a different, shell-major ordering; do not
# assume the two index spaces coincide.)
# ----------------------------------------------------------------------
E = np.array(
    [
        [0, 0, 0],
        [-1, 0, 0],
        [0, -1, 0],
        [0, 0, -1],
        [-1, -1, 0],
        [-1, 1, 0],
        [-1, 0, -1],
        [-1, 0, 1],
        [0, -1, -1],
        [0, -1, 1],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 0],
        [1, -1, 0],
        [1, 0, 1],
        [1, 0, -1],
        [0, 1, 1],
        [0, 1, -1],
    ],
    dtype=np.int64,
)

# shell index per direction, in R1's Table IV ordering
_SHELL1 = (1, 2, 3, 10, 11, 12)
SHELL = np.full(19, 2, dtype=np.int64)
SHELL[0] = 0
SHELL[list(_SHELL1)] = 1
SHELL_MASK = {0: SHELL == 0, 1: SHELL == 1, 2: SHELL == 2}

# Opposite direction map, R1 step (6) "opp(i)".
OPP = np.zeros(19, dtype=np.int64)
for _i in range(1, 10):
    OPP[_i] = _i + 9
    OPP[_i + 9] = _i

# ----------------------------------------------------------------------
# Table IV -- weights.  Indexed [shell] -> value.
#   W_i standard D3Q19 weights
#   phi_i, phii_i (R1's \phi_i and \varphi_i) polynomial collapse weights
#   psi_i, xi_i density-gradient weights
#   B_i perturbation weights
# ----------------------------------------------------------------------
W = np.array([1.0 / 3.0, 1.0 / 18.0, 1.0 / 36.0])
PHI = np.array([0.0, 1.0 / 12.0, 1.0 / 24.0])
PHII = np.array([1.0, -1.0 / 12.0, -1.0 / 24.0])
PSI = np.array([-5.0 / 2.0, -1.0 / 6.0, 1.0 / 24.0])
XI = np.array([0.0, 1.0 / 4.0, 1.0 / 8.0])
BCOEF = np.array([-2.0 / 9.0, 1.0 / 54.0, 1.0 / 27.0])

# per-direction vectors
W_I = W[SHELL]
PHI_I = PHI[SHELL]
PHII_I = PHII[SHELL]
PSI_I = PSI[SHELL]
XI_I = XI[SHELL]
B_I = BCOEF[SHELL]

# ----------------------------------------------------------------------
# Table VI -- sound-speed weight zeta, D3Q19 = 1/2.
#   Derivation (PAPER_FORMULATION.md section 0.3): zeta (1 - W0) = 1/3.
# ----------------------------------------------------------------------
ZETA = 0.5

# Unit density ratio => alpha_r = alpha_b = W0 (R1 Eq. 10 with gamma = 1).
W0 = W[0]
ALPHA_UNIT = W0

# Table VII -- momentum moment indexes, D3Q19.
MOMENTUM_INDEXES = (3, 5, 7)

# Table VIII -- kinematic-viscosity (stress) moment indexes, D3Q19.
VISCOSITY_INDEXES = (9, 11, 13, 14, 15)

# ----------------------------------------------------------------------
# Table XI -- MRT D3Q19 matrix M (integer basis).
# Transcribed from the published table; see PAPER_FORMULATION.md section
# 2.5 for the two independent extraction cross-checks.
# ----------------------------------------------------------------------
M = np.array(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [-30, -11, -11, -11, 8, 8, 8, 8, 8, 8, -11, -11, -11, 8, 8, 8, 8, 8, 8],
        [12, -4, -4, -4, 1, 1, 1, 1, 1, 1, -4, -4, -4, 1, 1, 1, 1, 1, 1],
        [0, -1, 0, 0, -1, -1, -1, -1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0],
        [0, 4, 0, 0, -1, -1, -1, -1, 0, 0, -4, 0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, -1, 0, -1, 1, 0, 0, -1, -1, 0, 1, 0, 1, -1, 0, 0, 1, 1],
        [0, 0, 4, 0, -1, 1, 0, 0, -1, -1, 0, -4, 0, 1, -1, 0, 0, 1, 1],
        [0, 0, 0, -1, 0, 0, -1, 1, -1, 1, 0, 0, 1, 0, 0, 1, -1, 1, -1],
        [0, 0, 0, 4, 0, 0, -1, 1, -1, 1, 0, 0, -4, 0, 0, 1, -1, 1, -1],
        [0, 2, -1, -1, 1, 1, 1, 1, -2, -2, 2, -1, -1, 1, 1, 1, 1, -2, -2],
        [0, -4, 2, 2, 1, 1, 1, 1, -2, -2, -4, 2, 2, 1, 1, 1, 1, -2, -2],
        [0, 0, 1, -1, 1, 1, -1, -1, 0, 0, 0, 1, -1, 1, 1, -1, -1, 0, 0],
        [0, 0, -2, 2, 1, 1, -1, -1, 0, 0, 0, -2, 2, 1, 1, -1, -1, 0, 0],
        [0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 1, -1],
        [0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0, 0],
        [0, 0, 0, 0, -1, -1, 1, 1, 0, 0, 0, 0, 0, 1, 1, -1, -1, 0, 0],
        [0, 0, 0, 0, 1, -1, 0, 0, -1, -1, 0, 0, 0, -1, 1, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 0, -1, 1, 1, -1, 0, 0, 0, 0, 0, 1, -1, -1, 1],
    ],
    dtype=np.float64,
)

M_INV = np.linalg.inv(M)

# ----------------------------------------------------------------------
# D3Q27 smoothing weights for the wall-normal preprocessing (R1 Eqs.34-38).
# ----------------------------------------------------------------------
SMOOTH_W = {0: 8.0 / 27.0, 1: 2.0 / 27.0, 2: 1.0 / 54.0, 3: 1.0 / 216.0}
SMOOTH_PASSES = 3


def smoothing_kernel():
    """3x3x3 D3Q27-weighted smoothing stencil (R1 Eqs. 34-38)."""
    k = np.zeros((3, 3, 3), dtype=np.float64)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for kk in (-1, 0, 1):
                k[i + 1, j + 1, kk + 1] = SMOOTH_W[i * i + j * j + kk * kk]
    return k


# ----------------------------------------------------------------------
# Verification helpers -- used by tests/leclaire_cg/test_lattice_tables.py
# ----------------------------------------------------------------------
def check_weights(tol=1e-14):
    """Return a dict of lattice-consistency residuals."""
    out = {}
    out["sum_W"] = abs(W_I.sum() - 1.0)
    mom2 = np.einsum("i,ia,ib->ab", W_I, E.astype(float), E.astype(float))
    out["mom2_W"] = np.max(np.abs(mom2 - np.eye(3) / 3.0))
    # phi_i + phii_i * alpha == W_i at alpha = W0
    out["phi_collapse"] = np.max(np.abs(PHI_I + PHII_I * W0 - W_I))
    # sum of perturbation weights B_i must be 1/3
    out["sum_B"] = abs(B_I.sum() - 1.0 / 3.0)
    # zeta * (1 - W0) == 1/3
    out["zeta_cs2"] = abs(ZETA * (1.0 - W0) - 1.0 / 3.0)
    # opposite map is an involution and flips c
    out["opp_involution"] = float(np.max(np.abs(E[OPP] + E)))
    return out


def check_mrt_matrix(tol=1e-9):
    """Row-identification checks for the transcribed Table XI matrix.

    Rows 3/5/7 must be c_x, c_y, c_z; row 0 the density; rows 9, 11, 13, 14,
    15 the five stress components.  A failure here means the transcription
    of Table XI is wrong, not that the physics is wrong.
    """
    Ef = E.astype(np.float64)
    out = {}
    out["row0_density"] = np.max(np.abs(M[0] - 1.0))
    out["row3_cx"] = np.max(np.abs(M[3] - Ef[:, 0]))
    out["row5_cy"] = np.max(np.abs(M[5] - Ef[:, 1]))
    out["row7_cz"] = np.max(np.abs(M[7] - Ef[:, 2]))
    out["row9_2xx_yy_zz"] = np.max(
        np.abs(M[9] - (2 * Ef[:, 0] ** 2 - Ef[:, 1] ** 2 - Ef[:, 2] ** 2)))
    out["row11_yy_zz"] = np.max(np.abs(M[11] - (Ef[:, 1] ** 2 - Ef[:, 2] ** 2)))
    out["row13_xy"] = np.max(np.abs(M[13] - Ef[:, 0] * Ef[:, 1]))
    out["row14_yz"] = np.max(np.abs(M[14] - Ef[:, 1] * Ef[:, 2]))
    out["row15_xz"] = np.max(np.abs(M[15] - Ef[:, 0] * Ef[:, 2]))
    out["invertible"] = float(np.max(np.abs(M @ M_INV - np.eye(19))))
    # Table XI rows 1 and 2 must be constant within each Table IV shell.
    # This is the cross-check that pins the shell grouping of SHELL.
    out["rows_shell_constant"] = max(
        float(max(np.ptp(M[r][SHELL == s]) for s in (0, 1, 2))) for r in (1, 2)
    )
    return out


def equilibrium(shape_or_none=None):
    """Placeholder kept out of this module: the equilibrium lives in
    operators.py so that this module stays a pure table module."""
    raise NotImplementedError("see operators.equilibrium")


if __name__ == "__main__":  # pragma: no cover - manual diagnostic
    print("weights:", check_weights())
    print("matrix :", check_mrt_matrix())
