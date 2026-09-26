"""L17_CORE: paper-faithful Leclaire-2017 D3Q19 colour-gradient solver.

Task: BI-CG-LECLAIRE-IMPLEMENTATION-001.

Implements the seven-step update of R1 (Phys. Rev. E 95, 033306), in the
order R1 states it:

    (1) external boundary condition          (not implemented; see below)
    (2) single-phase MRT collision           R1 Eq. (1), (4)-(9)
    (3) wetting boundary condition           R1 Eqs. (30)-(33)
    (4) perturbation (interfacial tension)   R1 Eqs. (15)-(18)
    (5) recoloring                           R1 Eqs. (19)-(20)
    (6) full-way bounce-back on solid nodes  R1 step (6)
    (7) streaming                            R1 step (7)

Step (1) is deliberately NOT implemented: R1's regularized density/velocity
boundaries (Eqs. 21-29) are out of scope for this task
(IMPLEMENTATION_PLAN.md section 2, FOLLOWUP_OPTIMIZATION_MAP.md F4).
No silent fallback exists: ``external_bc`` must stay ``None``.

Deliberate non-inheritance (LECLAIRE_IMPLEMENTATION_CONTRACT.md section 1):
no production calibration constant, no production recoloring semantics, no
production wetting semantics and no conservation correction is enabled here
by default.  The two switches that exist are OFF and are named
``conservation_overlay`` and the follow-up variants.

Backend note: this is a NumPy reference implementation, chosen because the
canonical test matrix is small and the machine carries a ~5.5 min Taichi JIT
compile tax per solver instance (IMPLEMENTATION_PLAN.md section 3).  It is
NOT performance-comparable with the production Taichi solver, and the report
says so.
"""

from __future__ import annotations

import numpy as np

from . import lattice as L
from . import operators as op


class LeclaireCG3D:
    """Leclaire-2017 D3Q19 colour-gradient solver (isolated research line)."""

    def __init__(
        self,
        nx,
        ny,
        nz,
        nu_r=1.0 / 6.0,
        nu_b=1.0 / 6.0,
        sigma=0.02,
        beta=0.7,
        chi=1.0,
        theta_c=np.pi / 2,
        wetting="leclaire",
        wetting_sign=+1.0,
        recolor_form="paper",
        perturbation_coeff="paper",
        grad_renormalize=True,
        conservation_overlay=None,
        fx=0.0,
        fy=0.0,
        fz=0.0,
        external_bc=None,
    ):
        if external_bc is not None:
            raise NotImplementedError(
                "R1 Eqs. (21)-(29) regularized open boundaries are out of "
                "scope for this task; see FOLLOWUP_OPTIMIZATION_MAP.md F4."
            )
        self.nx, self.ny, self.nz = int(nx), int(ny), int(nz)
        self.nu_r = float(nu_r)
        self.nu_b = float(nu_b)
        self.sigma = float(sigma)
        self.beta = float(beta)
        self.chi = float(chi)
        self.theta_c = float(theta_c)
        self.wetting = wetting
        self.wetting_sign = float(wetting_sign)
        self.recolor_form = recolor_form
        self.perturbation_coeff = perturbation_coeff
        self.grad_renormalize = bool(grad_renormalize)
        self.conservation_overlay = conservation_overlay
        self.force = np.array([fx, fy, fz], dtype=np.float64)

        shape = (self.nx, self.ny, self.nz)
        self.solid = np.zeros(shape, dtype=bool)
        self.Nr = np.zeros(shape + (19,), dtype=np.float64)
        self.Nb = np.zeros(shape + (19,), dtype=np.float64)
        self.rho_r = np.zeros(shape, dtype=np.float64)
        self.rho_b = np.zeros(shape, dtype=np.float64)
        self.nw = np.zeros(shape + (3,), dtype=np.float64)
        self._wall = np.zeros(shape, dtype=bool)
        self._prepared = False
        self.time = 0

    # ------------------------------------------------------------------
    #  Setup
    # ------------------------------------------------------------------
    def set_solid(self, solid):
        self.solid = np.asarray(solid) != 0
        self.fluid = ~self.solid
        # X_W: fluid sites with at least one solid neighbour (R1 section II)
        wall = np.zeros_like(self.solid)
        for i in range(1, 19):
            nb = op._shift(self.solid, L.E[i]).astype(bool)
            wall |= nb
        self._wall = wall & self.fluid
        self.nw = op.wall_normals(self.solid, sign=self.wetting_sign)
        self._prepared = True

    def init_uniform(self, psi=1.0, rho=1.0):
        """Uniform phase field: rho_k = (rho/2)(1 +/- psi), u = 0."""
        shape = (self.nx, self.ny, self.nz)
        p = np.full(shape, float(psi))
        r = np.full(shape, float(rho))
        self._init_from(r, p)

    def init_psi(self, psi, rho=1.0):
        """Initialise from a phase-field array psi (rho = const)."""
        psi = np.asarray(psi, dtype=np.float64)
        r = np.full(psi.shape, float(rho))
        self._init_from(r, psi)

    def _init_from(self, rho, psi):
        if not self._prepared:
            self.set_solid(np.zeros((self.nx, self.ny, self.nz), dtype=bool))
        self.rho_r = 0.5 * rho * (1.0 + psi)
        self.rho_b = 0.5 * rho * (1.0 - psi)
        self.Nr = op.equilibrium_zero_velocity(self.rho_r)
        self.Nb = op.equilibrium_zero_velocity(self.rho_b)
        self.Nr[self.solid] = 0.0
        self.Nb[self.solid] = 0.0
        self.rho_r[self.solid] = 0.0
        self.rho_b[self.solid] = 0.0
        self.time = 0

    # ------------------------------------------------------------------
    #  Diagnostics
    # ------------------------------------------------------------------
    def macroscopic(self):
        N = self.Nr + self.Nb
        rho, u = op.macroscopic(N)
        return rho, u

    def psi(self):
        rho, _ = self.macroscopic()
        out = np.zeros_like(rho)
        safe = np.abs(rho) > op.EPS
        out[safe] = (self.rho_r[safe] - self.rho_b[safe]) / rho[safe]
        return out

    def component_masses(self):
        return float(self.rho_r.sum()), float(self.rho_b.sum())

    # ------------------------------------------------------------------
    #  One timestep, R1 steps (1)-(7)
    # ------------------------------------------------------------------
    def step(self):
        if not self._prepared:
            self.set_solid(np.zeros((self.nx, self.ny, self.nz), dtype=bool))
        fluid = self.fluid

        # ---- step (2): single-phase MRT collision on the colour-blind N
        N = self.Nr + self.Nb
        rho, u = op.macroscopic(N)
        grad_rho = op.gradient_isotropic(rho, fluid,
                                         renormalize=self.grad_renormalize)
        nu = op.viscosity_harmonic(self.rho_r, self.rho_b,
                                   self.nu_r, self.nu_b)
        nu = np.where(np.isfinite(nu), nu, 0.5 * (self.nu_r + self.nu_b))
        omega = op.omega_eff(nu)

        Neq = op.equilibrium(rho, u, grad_rho, nu)
        m = N @ L.M.T
        meq = Neq @ L.M.T

        K = np.where(
            np.isin(np.arange(19), L.VISCOSITY_INDEXES),
            omega[..., None],
            self.chi * omega[..., None],
        )
        m = m - K * (m - meq)

        if np.any(self.force != 0.0):
            # R1 Eqs. (6)-(9): plain momentum source in moment space.
            for a, idx in enumerate(L.MOMENTUM_INDEXES):
                m[..., idx] += rho * self.force[a]

        N = m @ L.M_INV.T

        # ---- step (3): wetting boundary condition
        F = op.gradient_isotropic(self.psi(), fluid,
                                  renormalize=self.grad_renormalize)
        if self.wetting == "leclaire":
            F = op.secant_contact_angle(F, self._wall, self.nw, self.theta_c)
        elif self.wetting == "akai":
            F = op.wetting_akai(F, self._wall, self.nw, self.theta_c)
        elif self.wetting == "none":
            pass
        else:
            raise ValueError(f"unknown wetting mode {self.wetting!r}")

        # ---- step (4): perturbation, added to N directly (unrelaxed)
        N = N + op.perturbation(F, omega, self.sigma,
                                coeff_mode=self.perturbation_coeff)

        # ---- step (5): recoloring
        Nr, Nb = op.recolor(N, self.rho_r, self.rho_b, F, self.beta, u=u,
                            form=self.recolor_form)

        if self.conservation_overlay == "f64_arithmetic":
            # Optional project-style closure: force the per-node colour sums
            # back onto the intended rho_r / rho_b with a W-weighted spread.
            # Labelled an OVERLAY: an arm that enables it is not
            # paper-faithful (LECLAIRE_IMPLEMENTATION_CONTRACT.md section 5).
            dr = self.rho_r - Nr.sum(axis=-1)
            db = self.rho_b - Nb.sum(axis=-1)
            Nr = Nr + dr[..., None] * L.W_I
            Nb = Nb + db[..., None] * L.W_I
        elif self.conservation_overlay is not None:
            raise ValueError(
                f"unknown conservation_overlay {self.conservation_overlay!r}")

        # ---- step (6): full-way bounce-back on solid nodes
        Nr = op.bounce_back_fullway(Nr, self.solid)
        Nb = op.bounce_back_fullway(Nb, self.solid)

        # ---- step (7): streaming
        self.Nr = op.stream(Nr)
        self.Nb = op.stream(Nb)

        # colour densities of the streamed state
        self.rho_r = self.Nr.sum(axis=-1)
        self.rho_b = self.Nb.sum(axis=-1)
        self.time += 1

    # ------------------------------------------------------------------
    def run(self, steps, callback=None, every=1):
        for _ in range(int(steps)):
            self.step()
            if callback is not None and (self.time % every == 0):
                callback(self)
        return self
