"""
3D Color-Gradient (Rothman-Keller) two-phase LBM solver, D3Q19 MRT
===================================================================

Class-based 3D port of the canonical 2D solver ``lbm_solver_cg.py``
(ColorGradientSolver2D) — milestone P1 of PLAN_3d_cg_granular_v1.md.
Port contract (plan §4): class structure / CG2 infrastructure / kernel
order come from the 2D canonical; the upstream module-level
``lbm_solver_3d_2phase.py`` contributes NUMERICAL TABLES ONLY:

  * M_np 19x19 moment matrix          (upstream :124-142, CG-standard
    D3Q19 Lallemand-Luo-type basis; cond(M)=4.3)
  * LR bounce-back opposite map       (upstream :145)
  * surface-tension injection into meq moments 1,9,11,13,14,15
    (upstream :322-327 — the five deviatoric/trace stress moments)
  * recoloring pairs kk=1,3,5,7,9,11,13,15,17   (upstream :358)
  * viscosity interpolation wl/wg/lg0/l1/l2/g1/g2 (upstream :106-114,
    identical formulas to 2D)
  * S relaxation layout: conserved 0,3,5,7; sv on 1,2,9-15; sother on
    4,6,8,16,17,18 (upstream :299-302)

Four known upstream defects are NOT inherited (plan §4 table):
  1. meq without rho factors (upstream :257-262 sets out[1]=u.u,
     out[3]=u[0], ...).  This file uses the FULL 19-moment polynomial
     equilibrium meq = M @ feq(rho, u), derived once and verified to
     4.4e-16 against direct M@feq (200 random rho/u points, f64).  The
     rho-pressure drive (rho_res 1.30-1.38) requires it: at rho=1 the
     upstream form is invisibly wrong, at rho != 1 it breaks.
     Closed form (this M's rows are normalised to integer coefficients):

       m0  = rho
       m1  = rho * u^2                    (energy)
       m2  = 0                            (eps)
       m3  = rho*ux, m5 = rho*uy, m7 = rho*uz        (momenta j)
       m4  = m6 = m8 = 0                  (energy fluxes q)
       m9  = rho*(2ux^2-uy^2-uz^2)        (pxx)
       m10 = 0                            (pixx)
       m11 = rho*(uy^2-uz^2)              (pww)
       m12 = 0                            (piww)
       m13 = rho*ux*uy, m14 = rho*uy*uz, m15 = rho*ux*uz  (shears)
       m16 = m17 = m18 = 0                (third order)

  2. psi parenthesisation bug (upstream :612,
     ``rho_r - rho_b/(rho_r+rho_b)``) — the 2D fixed form is ported.
  3. scalar psi_solid — the per-node field psi_solid_f is ported.
  4. module-level nx/ny/nz without infrastructure — class-based, with
     the CG2 set: race-free per-colour membranes, density-prescribed
     psi-Dirichlet reservoirs with f64 flux counters, colour-weighted
     body force.

Timestep (identical order to 2D):
  collision(+recolour) -> F.fill(0) -> streaming1 (atomic accumulate,
  psi-conditional membrane bounce-back) -> Boundary_condition ->
  streaming3 -> Boundary_condition_psi -> apply_reservoirs.

Backend: LBM_ARCH env var — default ti.gpu (CUDA), 'cpu' forces CPU.
The runtime itself is started by the explicit boundary in
``cg3d.runtime``; importing this module does not call ``ti.init()``.
"""
import os

import numpy as np
import taichi as ti

from cg3d.runtime import init_runtime

# ============================================================
#  Shared D3Q19 lattice tables + MRT matrix (module level)
# ============================================================
# Taichi fields cannot be created before ti.init() (1.7.4 raises
# "Cannont create field, maybe you forgot to call ti.init() first?"), so
# the tables are allocated lazily by ensure_lattice_tables() instead of
# at import.  Same names, same contents, only the creation time moved.

e   = None    # ti.Vector.field(3, ti.i32, shape=(19,))
e_f = None    # ti.Vector.field(3, ti.f32, shape=(19,))
w   = None    # ti.field(ti.f32, shape=(19,))
LR  = None    # ti.field(ti.i32, shape=(19,))     # bounce-back opposite map
M   = None    # ti.field(ti.f32, shape=(19, 19))  # upstream :124-142
inv_M = None  # ti.field(ti.f32, shape=(19, 19))


def _init_lattice_tables():
    """Create + fill the shared tables; the runtime must be up already."""
    global e, e_f, w, LR, M, inv_M
    e   = ti.Vector.field(3, ti.i32, shape=(19,))
    e_f = ti.Vector.field(3, ti.f32, shape=(19,))
    w   = ti.field(ti.f32, shape=(19,))
    LR  = ti.field(ti.i32, shape=(19,))
    M   = ti.field(ti.f32, shape=(19, 19))
    inv_M = ti.field(ti.f32, shape=(19, 19))
    e_np = np.array(
        [[0, 0, 0],
         [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
         [1, 1, 0], [-1, -1, 0], [1, -1, 0], [-1, 1, 0],
         [1, 0, 1], [-1, 0, -1], [1, 0, -1], [-1, 0, 1],
         [0, 1, 1], [0, -1, -1], [0, 1, -1], [0, -1, 1]], dtype=np.int32)
    e.from_numpy(e_np)
    e_f.from_numpy(e_np.astype(np.float32))
    w.from_numpy(np.array(
        [1.0 / 3.0] + [1.0 / 18.0] * 6 + [1.0 / 36.0] * 12, dtype=np.float32))
    # k=0 rest; pairs (1,2)(3,4)(5,6)(7,8)(9,10)(11,12)(13,14)(15,16)(17,18)
    LR.from_numpy(np.array(
        [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15, 18, 17],
        dtype=np.int32))
    M_np = np.array([[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [-1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,-2,-2,-2,-2,-2,-2,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,-1,0,0,0,0,1,-1,1,-1,1,-1,1,-1,0,0,0,0],
    [0,-2,2,0,0,0,0,1,-1,1,-1,1,-1,1,-1,0,0,0,0],
    [0,0,0,1,-1,0,0,1,-1,-1,1,0,0,0,0,1,-1,1,-1],
    [0,0,0,-2,2,0,0,1,-1,-1,1,0,0,0,0,1,-1,1,-1],
    [0,0,0,0,0,1,-1,0,0,0,0,1,-1,-1,1,1,-1,-1,1],
    [0,0,0,0,0,-2,2,0,0,0,0,1,-1,-1,1,1,-1,-1,1],
    [0,2,2,-1,-1,-1,-1,1,1,1,1,1,1,1,1,-2,-2,-2,-2],
    [0,-2,-2,1,1,1,1,1,1,1,1,1,1,1,1,-2,-2,-2,-2],
    [0,0,0,1,1,-1,-1,1,1,1,1,-1,-1,-1,-1,0,0,0,0],
    [0,0,0,-1,-1,1,1,1,1,1,1,-1,-1,-1,-1,0,0,0,0],
    [0,0,0,0,0,0,0,1,1,-1,-1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,-1,-1],
    [0,0,0,0,0,0,0,0,0,0,0,1,1,-1,-1,0,0,0,0],
    [0,0,0,0,0,0,0,1,-1,1,-1,-1,1,-1,1,0,0,0,0],
    [0,0,0,0,0,0,0,-1,1,1,-1,0,0,0,0,1,-1,1,-1],
    [0,0,0,0,0,0,0,0,0,0,0,1,-1,-1,1,-1,1,1,-1]], dtype=np.float64)
    M.from_numpy(M_np.astype(np.float32))
    inv_M.from_numpy(np.linalg.inv(M_np).astype(np.float32))


_TABLES_READY = False


def ensure_lattice_tables():
    """Explicit initialization boundary for the shared module tables.

    Starts the Taichi runtime (``cg3d.runtime.init_runtime``) and then
    creates and fills the D3Q19/MRT tables — the order the old import-time
    code used.  Idempotent.  ``ColorGradientSolver3D.__init__`` calls it,
    so any solver use passes through here; call it directly before reading
    the module-level tables (``mod.M``, ``mod.inv_M``, ...) without
    constructing a solver.
    """
    global _TABLES_READY
    if _TABLES_READY:
        return
    init_runtime()
    _init_lattice_tables()
    _TABLES_READY = True


# ============================================================
#  Module-level device functions (shared tables / pure args only)
# ============================================================

@ti.func
def feq(k: ti.i32, rho_local: ti.f32, u: ti.template()) -> ti.f32:
    eu = e[k].dot(u)
    uv = u.dot(u)
    return w[k] * rho_local * (1.0 + 3.0 * eu + 4.5 * eu * eu - 1.5 * uv)


@ti.func
def periodic_index(i: ti.template(), nx: ti.i32, ny: ti.i32,
                   nz: ti.i32) -> ti.template():
    iout = i
    if i[0] < 0:       iout[0] = nx - 1
    if i[0] > nx - 1:  iout[0] = 0
    if i[1] < 0:       iout[1] = ny - 1
    if i[1] > ny - 1:  iout[1] = 0
    if i[2] < 0:       iout[2] = nz - 1
    if i[2] > nz - 1:  iout[2] = 0
    return iout


@ti.func
def meq_vec(rho_local: ti.f32, u: ti.template()):
    """Full 19-moment equilibrium meq = M @ feq(rho, u) in closed form
    (see module docstring; verified vs direct matvec to 4.4e-16)."""
    out = ti.Vector([0.0] * 19)
    usq = u.dot(u)
    out[0] = rho_local                          # rho
    out[1] = rho_local * usq                    # e
    out[2] = 0.0                                # eps
    out[3] = rho_local * u[0]                   # jx
    out[4] = 0.0                                # qx
    out[5] = rho_local * u[1]                   # jy
    out[6] = 0.0                                # qy
    out[7] = rho_local * u[2]                   # jz
    out[8] = 0.0                                # qz
    out[9] = rho_local * (2.0 * u[0] * u[0] - u[1] * u[1] - u[2] * u[2])  # pxx
    out[10] = 0.0                               # pixx
    out[11] = rho_local * (u[1] * u[1] - u[2] * u[2])                     # pww
    out[12] = 0.0                               # piww
    out[13] = rho_local * u[0] * u[1]           # pxy
    out[14] = rho_local * u[1] * u[2]           # pyz
    out[15] = rho_local * u[0] * u[2]           # pxz
    out[16] = 0.0                               # mx
    out[17] = 0.0                               # my
    out[18] = 0.0                               # mz
    return out


@ti.data_oriented
class ColorGradientSolver3D:
    """Two-phase color-gradient (Rothman-Keller) solver, D3Q19 MRT.

    3D sibling of ColorGradientSolver2D — same parameter semantics:

    nx, ny, nz : grid dimensions.
    niu_l, niu_g : viscosities of psi>0 ("liquid"/red) and psi<0
        ("gas"/blue) phases.  Constructor-time constants.
    CapA : surface-tension GAIN (NOT sigma itself; calibrate sigma(CapA)
        with the 3D Laplace test, dP = 2 sigma / R).  0-d field.
    psi_solid : wall "colour" in [-1,1]; +1 red-liking, -1 blue-liking.
        Calibrate theta(psi_solid) with validation_cg3d_contact_angle.py.
    fx, fy, fz : body force (Guo).  0-d fields.
    bc_* : flow BC per domain end: 0 periodic, 1 fixed pressure (rho_bc*),
        2 fixed velocity (v_bc*).  Compile-time constants.
    bc_psi_* : phase-field BC per end: 0 periodic, 1 Dirichlet psi_*.

        s = ColorGradientSolver3D(96, 96, 96, CapA=0.136)
        s.set_surface_tension(0.02)
        s.set_psi_solid(-0.75)
        s.set_body_force(1e-5, 0.0, 0.0)
    """

    def __init__(self, nx, ny, nz, niu_l=0.1, niu_g=0.1, CapA=0.005,
                 psi_solid=0.7, fx=0.0, fy=0.0, fz=0.0,
                 bc_x_left=0, bc_x_right=0, bc_y_left=0, bc_y_right=0,
                 bc_z_left=0, bc_z_right=0,
                 rho_bcxl=1.0, rho_bcxr=0.995, rho_bcyl=1.0, rho_bcyr=1.0,
                 rho_bczl=1.0, rho_bczr=1.0,
                 vx_bcxl=0.0, vy_bcxl=0.0, vz_bcxl=0.0,
                 vx_bcxr=0.0, vy_bcxr=0.0, vz_bcxr=0.0,
                 vx_bcyl=0.0, vy_bcyl=0.0, vz_bcyl=0.0,
                 vx_bcyr=0.0, vy_bcyr=0.0, vz_bcyr=0.0,
                 vx_bczl=0.0, vy_bczl=0.0, vz_bczl=0.0,
                 vx_bczr=0.0, vy_bczr=0.0, vz_bczr=0.0,
                 bc_psi_x_left=0, bc_psi_x_right=0,
                 bc_psi_y_left=0, bc_psi_y_right=0,
                 bc_psi_z_left=0, bc_psi_z_right=0,
                 psi_x_left=-1.0, psi_x_right=1.0,
                 psi_y_left=1.0, psi_y_right=1.0,
                 psi_z_left=1.0, psi_z_right=1.0):
        ensure_lattice_tables()
        self.nx, self.ny, self.nz = int(nx), int(ny), int(nz)

        # ---- runtime-tunable physics scalars (0-d fields) ----
        self.CapA = ti.field(ti.f32, shape=());      self.CapA[None] = CapA
        self.psi_solid = ti.field(ti.f32, shape=()); self.psi_solid[None] = psi_solid
        self.ext_f = ti.Vector.field(3, ti.f32, shape=())
        self.ext_f[None] = ti.Vector([fx, fy, fz])

        # ---- viscosity interpolation coefficients (compile-time) ----
        self.niu_l, self.niu_g = niu_l, niu_g
        self.wl = 1.0 / (niu_l / (1.0 / 3.0) + 0.5)
        self.wg = 1.0 / (niu_g / (1.0 / 3.0) + 0.5)
        self.lg0 = 2 * self.wl * self.wg / (self.wl + self.wg)
        self.l1 = 2 * (self.wl - self.lg0) * 10
        self.l2 = -self.l1 / 0.2
        self.g1 = 2 * (self.lg0 - self.wg) * 10
        self.g2 = self.g1 / 0.2

        # ---- BC configuration (compile-time constants) ----
        self.bc_x_left,  self.bc_x_right = bc_x_left,  bc_x_right
        self.bc_y_left,  self.bc_y_right = bc_y_left,  bc_y_right
        self.bc_z_left,  self.bc_z_right = bc_z_left,  bc_z_right
        self.rho_bcxl, self.rho_bcxr = rho_bcxl, rho_bcxr
        self.rho_bcyl, self.rho_bcyr = rho_bcyl, rho_bcyr
        self.rho_bczl, self.rho_bczr = rho_bczl, rho_bczr
        self.bc_psi_x_left,  self.bc_psi_x_right = bc_psi_x_left,  bc_psi_x_right
        self.bc_psi_y_left,  self.bc_psi_y_right = bc_psi_y_left,  bc_psi_y_right
        self.bc_psi_z_left,  self.bc_psi_z_right = bc_psi_z_left,  bc_psi_z_right
        self.psi_x_left, self.psi_x_right = psi_x_left, psi_x_right
        self.psi_y_left, self.psi_y_right = psi_y_left, psi_y_right
        self.psi_z_left, self.psi_z_right = psi_z_left, psi_z_right

        self.bc_vel_x_left  = ti.Vector.field(3, ti.f32, shape=())
        self.bc_vel_x_right = ti.Vector.field(3, ti.f32, shape=())
        self.bc_vel_y_left  = ti.Vector.field(3, ti.f32, shape=())
        self.bc_vel_y_right = ti.Vector.field(3, ti.f32, shape=())
        self.bc_vel_z_left  = ti.Vector.field(3, ti.f32, shape=())
        self.bc_vel_z_right = ti.Vector.field(3, ti.f32, shape=())
        self.bc_vel_x_left[None]  = ti.Vector([vx_bcxl, vy_bcxl, vz_bcxl])
        self.bc_vel_x_right[None] = ti.Vector([vx_bcxr, vy_bcxr, vz_bcxr])
        self.bc_vel_y_left[None]  = ti.Vector([vx_bcyl, vy_bcyl, vz_bcyl])
        self.bc_vel_y_right[None] = ti.Vector([vx_bcyr, vy_bcyr, vz_bcyr])
        self.bc_vel_z_left[None]  = ti.Vector([vx_bczl, vy_bczl, vz_bczl])
        self.bc_vel_z_right[None] = ti.Vector([vx_bczr, vy_bczr, vz_bczr])

        # ---- per-instance fields ----
        self.f     = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz, 19))
        self.F     = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz, 19))
        self.rho   = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.v     = ti.Vector.field(3, ti.f32, shape=(self.nx, self.ny, self.nz))
        self.psi   = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.rho_r = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.rho_b = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.rhor  = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.rhob  = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.solid = ti.field(ti.i8, shape=(self.nx, self.ny, self.nz))

        # ---- CG2 infrastructure (2D mirror; zero masks == original
        # arithmetic — see streaming1 docstring) ----
        self.mem_r = ti.field(ti.i8, shape=(self.nx, self.ny, self.nz))
        self.mem_b = ti.field(ti.i8, shape=(self.nx, self.ny, self.nz))
        self.res_mask = ti.field(ti.i8, shape=(self.nx, self.ny, self.nz))
        self.res_psi = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.res_rho = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.use_reservoirs = False
        # f64 MANDATORY (SC G6 lesson): f32 atomic accumulation loses
        # increments once the counters reach 1e5+ magnitude.
        self.inj_r = ti.field(ti.f64, shape=()); self.inj_r[None] = 0.0
        self.inj_b = ti.field(ti.f64, shape=()); self.inj_b[None] = 0.0
        self.inj_m = ti.field(ti.f64, shape=()); self.inj_m[None] = 0.0
        self.psi_solid_f = ti.field(ti.f32, shape=(self.nx, self.ny, self.nz))
        self.psi_solid_f.from_numpy(
            np.full((self.nx, self.ny, self.nz), psi_solid, dtype=np.float32))
        self.force_mode = ti.field(ti.i8, shape=())
        self.force_mode[None] = 0
        self.ext_fb = ti.Vector.field(3, ti.f32, shape=())
        self.ext_fr = ti.Vector.field(3, ti.f32, shape=())
        self.ext_fb[None] = ti.Vector([0.0, 0.0, 0.0])
        self.ext_fr[None] = ti.Vector([0.0, 0.0, 0.0])

    # --------------------------------------------------------
    #  Runtime parameter setters (2D API mirror)
    # --------------------------------------------------------

    def set_surface_tension(self, CapA):
        self.CapA[None] = CapA

    def set_psi_solid(self, psi_solid):
        self.psi_solid[None] = psi_solid
        self.psi_solid_f.from_numpy(
            np.full((self.nx, self.ny, self.nz), psi_solid, dtype=np.float32))

    def set_psi_solid_field(self, psi_solid_np):
        self.psi_solid_f.from_numpy(
            np.ascontiguousarray(psi_solid_np, dtype=np.float32))

    def set_body_force(self, fx, fy, fz):
        self.ext_f[None] = ti.Vector([fx, fy, fz])
        self.force_mode[None] = 0

    def set_body_force_comp(self, fx_b, fy_b, fz_b, fx_r, fy_r, fz_r):
        """Per-colour body force: local force = w_b*(fx_b,fy_b,fz_b) +
        (1-w_b)*(fx_r,fy_r,fz_r), w_b = rho_b/(rho_r+rho_b)."""
        self.force_mode[None] = 1
        self.ext_fb[None] = ti.Vector([fx_b, fy_b, fz_b])
        self.ext_fr[None] = ti.Vector([fx_r, fy_r, fz_r])

    def set_membranes(self, mem_r_np, mem_b_np):
        self.mem_r.from_numpy(np.asarray(mem_r_np, dtype=np.int8))
        self.mem_b.from_numpy(np.asarray(mem_b_np, dtype=np.int8))

    def set_reservoirs(self, res_np, psi_target, rho_res=1.0):
        """Density-prescribed reservoir region(s): psi / rho_r / rho_b
        pinned to (psi_target, rho_res), f re-equilibrated each step.
        Call once per region; regions accumulate."""
        mask = np.asarray(res_np, dtype=np.int8)
        if np.isscalar(psi_target):
            psi_np = np.full((self.nx, self.ny, self.nz), float(psi_target),
                             dtype=np.float32)
        else:
            psi_np = np.asarray(psi_target, dtype=np.float32)
        m = (self.res_mask.to_numpy() | mask).astype(np.int8)
        self.res_mask.from_numpy(m)
        sel = mask != 0
        psis = self.res_psi.to_numpy()
        psis[sel] = psi_np[sel]
        self.res_psi.from_numpy(np.ascontiguousarray(psis, dtype=np.float32))
        rhos = self.res_rho.to_numpy()
        rhos[sel] = float(rho_res)
        self.res_rho.from_numpy(np.ascontiguousarray(rhos, dtype=np.float32))
        self.use_reservoirs = bool(m.any())

    def reservoir_fluxes(self):
        return dict(inj_r=float(self.inj_r[None]),
                    inj_b=float(self.inj_b[None]),
                    inj_m=float(self.inj_m[None]))

    # --------------------------------------------------------
    #  Initialisation
    # --------------------------------------------------------

    @ti.kernel
    def init(self, psi_np: ti.types.ndarray(), solid_np: ti.types.ndarray()):
        """Phase field psi in [-1,1] + solid map -> equilibrium fill:
        rho = 1, rho_r = (psi+1)/2.  Fluid nodes only."""
        for i, j, k in self.solid:
            self.solid[i, j, k] = solid_np[i, j, k]
            self.psi[i, j, k] = psi_np[i, j, k]
            if self.solid[i, j, k] == 0:
                self.rho[i, j, k] = 1.0
                self.v[i, j, k] = ti.Vector([0.0, 0.0, 0.0])
                self.rho_r[i, j, k] = (self.psi[i, j, k] + 1.0) / 2.0
                self.rho_b[i, j, k] = 1.0 - self.rho_r[i, j, k]
                self.rhor[i, j, k] = 0.0
                self.rhob[i, j, k] = 0.0
                for s in ti.static(range(19)):
                    self.f[i, j, k, s] = feq(s, 1.0, self.v[i, j, k])
                    self.F[i, j, k, s] = feq(s, 1.0, self.v[i, j, k])
            else:
                # match a freshly allocated instance (fields start zeroed)
                # so re-init on a REUSED instance is exactly equivalent
                self.rho[i, j, k] = 0.0
                self.v[i, j, k] = ti.Vector([0.0, 0.0, 0.0])
                self.rho_r[i, j, k] = 0.0
                self.rho_b[i, j, k] = 0.0
                self.rhor[i, j, k] = 0.0
                self.rhob[i, j, k] = 0.0
                for s in ti.static(range(19)):
                    self.f[i, j, k, s] = 0.0
                    self.F[i, j, k, s] = 0.0

    # --------------------------------------------------------
    #  Device functions
    # --------------------------------------------------------

    @ti.func
    def periodic_index_for_psi(self, i: ti.template()) -> ti.template():
        """Periodic wrap, or clamp to the boundary layer when the matching
        bc_psi flag is Dirichlet (1)."""
        iout = i
        if i[0] < 0:
            if ti.static(self.bc_psi_x_left == 0):
                iout[0] = self.nx - 1
            else:
                iout[0] = 0
        if i[0] > self.nx - 1:
            if ti.static(self.bc_psi_x_right == 0):
                iout[0] = 0
            else:
                iout[0] = self.nx - 1
        if i[1] < 0:
            if ti.static(self.bc_psi_y_left == 0):
                iout[1] = self.ny - 1
            else:
                iout[1] = 0
        if i[1] > self.ny - 1:
            if ti.static(self.bc_psi_y_right == 0):
                iout[1] = 0
            else:
                iout[1] = self.ny - 1
        if i[2] < 0:
            if ti.static(self.bc_psi_z_left == 0):
                iout[2] = self.nz - 1
            else:
                iout[2] = 0
        if i[2] > self.nz - 1:
            if ti.static(self.bc_psi_z_right == 0):
                iout[2] = 0
            else:
                iout[2] = self.nz - 1
        return iout

    @ti.func
    def Compute_C(self, i: ti.template()):
        """Colour gradient C = sum_k 3 w_k e_k psi(x+e_k); solid
        neighbours contribute the per-node psi_solid_f.  Zeroed in
        single-phase bulk next to solid (guards spurious wall forces)."""
        C = ti.Vector([0.0, 0.0, 0.0])
        ind_S = 0
        for s in ti.static(range(19)):
            ip = self.periodic_index_for_psi(i + e[s])
            if self.solid[ip] == 0:
                C += 3.0 * w[s] * e_f[s] * self.psi[ip]
            else:
                ind_S = 1
                C += 3.0 * w[s] * e_f[s] * self.psi_solid_f[ip]

        # Bulk suppression next to solid: normalised criterion |psi| > 0.9
        # (PR-2 fix). The raw form abs(rho_r - rho_b) > 0.9 is density-
        # dependent: under rho-pressure driving the outlet sits at
        # rho = 1 - d/2 (0.89 at the d = 0.22 rung) where pure red fails
        # the threshold and spurious wall forces reappear.
        if (ti.abs(self.rho_r[i] - self.rho_b[i])
                > 0.9 * (self.rho_r[i] + self.rho_b[i])) and (ind_S == 1):
            C = ti.Vector([0.0, 0.0, 0.0])

        return C

    @ti.func
    def Compute_S_local(self, id: ti.template()):
        """Per-node MRT relaxation rates: phase viscosities with a
        quadratic blend across the interface band (|psi| <= 0.1)."""
        sv = 0.0
        if self.psi[id] > 0:
            if self.psi[id] > 0.1:
                sv = self.wl
            else:
                sv = self.lg0 + self.l1 * self.psi[id] + self.l2 * self.psi[id] * self.psi[id]
        else:
            if self.psi[id] < -0.1:
                sv = self.wg
            else:
                sv = self.lg0 + self.g1 * self.psi[id] + self.g2 * self.psi[id] * self.psi[id]
        sother = 8.0 * (2.0 - sv) / (8.0 - sv)

        # D3Q19 MRT relaxation: conserved 0,3,5,7 (upstream :299-302)
        S = ti.Vector([0.0] * 19)
        S[1] = sv;      S[2] = sv
        S[4] = sother;  S[6] = sother;  S[8] = sother
        S[9] = sv;      S[10] = sv;     S[11] = sv
        S[12] = sv;     S[13] = sv;     S[14] = sv
        S[15] = sv
        S[16] = sother; S[17] = sother; S[18] = sother
        return S

    @ti.func
    def multiply_M(self, i: ti.i32, j: ti.i32, k: ti.i32):
        out = ti.Vector([0.0] * 19)
        for index in ti.static(range(19)):
            for s in ti.static(range(19)):
                out[index] += M[index, s] * self.F[i, j, k, s]
        return out

    @ti.func
    def force_at(self, i: ti.i32, j: ti.i32, k: ti.i32):
        """Local body force: uniform ext_f (mode 0) or the colour-weighted
        blend (mode 1)."""
        out = self.ext_f[None]
        if self.force_mode[None] == 1:
            tot = self.rho_r[i, j, k] + self.rho_b[i, j, k]
            wb = 0.0
            if tot > 1e-12:
                wb = self.rho_b[i, j, k] / tot
            out = wb * self.ext_fb[None] + (1.0 - wb) * self.ext_fr[None]
        return out

    @ti.func
    def GuoF(self, i: ti.i32, j: ti.i32, k: ti.i32, s: ti.i32,
             u: ti.template()):
        # Guo (2002) force in moment space with the full 1/cs^2 (3) and
        # 1/cs^4 (9) weights (PR-2 fix). The original omitted both, so the
        # momentum actually injected per step was F/3 while streaming3's
        # half-force correction assumed F — measured eff=0.332 on this
        # solver (2D P2 calibration: 0.330). Reservoir-driven runs are
        # unaffected (F = 0).
        fvec = self.force_at(i, j, k)
        out = 0.0
        for l in ti.static(range(19)):
            out += w[l] * (3.0 * (e_f[l] - u).dot(fvec)
                   + 9.0 * (e_f[l].dot(u)) * (e_f[l].dot(fvec))) * M[s, l]
        return out

    # --------------------------------------------------------
    #  Kernels
    # --------------------------------------------------------

    @ti.kernel
    def collision(self):
        for i, j, k in self.rho:
            if i < self.nx and j < self.ny and k < self.nz and self.solid[i, j, k] == 0:
                C = self.Compute_C(ti.Vector([i, j, k]))
                cc = C.norm()
                normal = ti.Vector([0.0, 0.0, 0.0])
                if cc > 0:
                    normal = C / cc

                m_temp = self.multiply_M(i, j, k)
                meq = meq_vec(self.rho[i, j, k], self.v[i, j, k])

                # Surface tension into the stress-moment equilibria
                # (upstream :322-327; moments 9/11/13/14/15 are the
                # trace/deviatoric + shear stress components of this M)
                meq[1]  += self.CapA[None] * cc
                meq[9]  += 0.5 * self.CapA[None] * cc * (2.0 * normal.x * normal.x - normal.y * normal.y - normal.z * normal.z)
                meq[11] += 0.5 * self.CapA[None] * cc * (normal.y * normal.y - normal.z * normal.z)
                meq[13] += 0.5 * self.CapA[None] * cc * (normal.x * normal.y)
                meq[14] += 0.5 * self.CapA[None] * cc * (normal.y * normal.z)
                meq[15] += 0.5 * self.CapA[None] * cc * (normal.x * normal.z)

                S_local = self.Compute_S_local(ti.Vector([i, j, k]))

                for s in ti.static(range(19)):
                    m_temp[s] -= S_local[s] * (m_temp[s] - meq[s])
                    m_temp[s] += (1 - 0.5 * S_local[s]) * self.GuoF(i, j, k, s, self.v[i, j, k])

                # Inverse transform: moment space -> distribution space
                g_r = ti.Vector([0.0] * 19)
                g_b = ti.Vector([0.0] * 19)

                for s in ti.static(range(19)):
                    self.f[i, j, k, s] = 0
                    for l in ti.static(range(19)):
                        self.f[i, j, k, s] += inv_M[s, l] * m_temp[l]
                    g_r[s] = feq(s, self.rho_r[i, j, k], self.v[i, j, k])
                    g_b[s] = feq(s, self.rho_b[i, j, k], self.v[i, j, k])

                # Recoloring (Latva-Kokko); 9 opposite pairs (upstream :358)
                if cc > 0:
                    for kk in ti.static([1, 3, 5, 7, 9, 11, 13, 15, 17]):
                        ef = e[kk].dot(C)
                        cospsi = g_r[kk] if (g_r[kk] < g_r[kk + 1]) else g_r[kk + 1]
                        cospsi = cospsi if (cospsi < g_b[kk]) else g_b[kk]
                        cospsi = cospsi if (cospsi < g_b[kk + 1]) else g_b[kk + 1]
                        cospsi *= ef / cc

                        g_r[kk] += cospsi
                        g_r[kk + 1] -= cospsi
                        g_b[kk] -= cospsi
                        g_b[kk + 1] += cospsi

                # Stream colour densities; half-way bounce-back at
                # solids; membrane nodes bounce only the blocked colour.
                # All paths atomic-accumulate -> race-free.
                for s in ti.static(range(19)):
                    ip = periodic_index(ti.Vector([i, j, k]) + e[s],
                                        self.nx, self.ny, self.nz)
                    if self.solid[ip] == 0 and self.mem_r[ip] == 0:
                        self.rhor[ip] += g_r[s]
                    else:
                        self.rhor[i, j, k] += g_r[s]
                    if self.solid[ip] == 0 and self.mem_b[ip] == 0:
                        self.rhob[ip] += g_b[s]
                    else:
                        self.rhob[i, j, k] += g_b[s]

    @ti.kernel
    def streaming1(self):
        # F is zeroed in step() before this kernel; every write below is
        # an atomic accumulate.  With no membranes each slot receives
        # exactly ONE contribution (forward packet or bounced packet —
        # mutually exclusive), reproducing the upstream plain assignment.
        # At membrane nodes the packet is split by the source node's
        # colour fractions wr = rho_r/(rho_r+rho_b); fred + fblu = f.
        for i, j, k in self.rho:
            if i < self.nx and j < self.ny and k < self.nz and self.solid[i, j, k] == 0:
                ci = ti.Vector([i, j, k])
                for s in ti.static(range(19)):
                    ip = periodic_index(ci + e[s], self.nx, self.ny, self.nz)
                    if self.solid[ip] != 0:
                        self.F[ci, LR[s]] += self.f[ci, s]
                    elif self.mem_r[ip] == 0 and self.mem_b[ip] == 0:
                        self.F[ip, s] += self.f[ci, s]
                    else:
                        tot = self.rho_r[i, j, k] + self.rho_b[i, j, k]
                        wr = 0.0
                        if tot > 1e-12:
                            wr = self.rho_r[i, j, k] / tot
                        fred = self.f[i, j, k, s] * wr
                        fblu = self.f[i, j, k, s] - fred
                        if self.mem_r[ip] == 0:
                            self.F[ip, s] += fred
                        else:
                            self.F[ci, LR[s]] += fred
                        if self.mem_b[ip] == 0:
                            self.F[ip, s] += fblu
                        else:
                            self.F[ci, LR[s]] += fblu

    @ti.kernel
    def Boundary_condition(self):
        # X-left / X-right
        if ti.static(self.bc_x_left == 1):
            for j, k in ti.ndrange((0, self.ny), (0, self.nz)):
                if self.solid[0, j, k] == 0:
                    for s in ti.static(range(19)):
                        if self.solid[1, j, k] > 0:
                            self.F[0, j, k, s] = feq(s, self.rho_bcxl, self.v[1, j, k])
                        else:
                            self.F[0, j, k, s] = feq(s, self.rho_bcxl, self.v[0, j, k])
        if ti.static(self.bc_x_left == 2):
            for j, k in ti.ndrange((0, self.ny), (0, self.nz)):
                if self.solid[0, j, k] == 0:
                    for s in ti.static(range(19)):
                        self.F[0, j, k, s] = feq(LR[s], 1.0, self.bc_vel_x_left[None]) \
                                          - self.F[0, j, k, LR[s]] \
                                          + feq(s, 1.0, self.bc_vel_x_left[None])
        if ti.static(self.bc_x_right == 1):
            for j, k in ti.ndrange((0, self.ny), (0, self.nz)):
                if self.solid[self.nx - 1, j, k] == 0:
                    for s in ti.static(range(19)):
                        if self.solid[self.nx - 2, j, k] > 0:
                            self.F[self.nx - 1, j, k, s] = feq(s, self.rho_bcxr, self.v[self.nx - 2, j, k])
                        else:
                            self.F[self.nx - 1, j, k, s] = feq(s, self.rho_bcxr, self.v[self.nx - 1, j, k])
        if ti.static(self.bc_x_right == 2):
            for j, k in ti.ndrange((0, self.ny), (0, self.nz)):
                if self.solid[self.nx - 1, j, k] == 0:
                    for s in ti.static(range(19)):
                        self.F[self.nx - 1, j, k, s] = feq(LR[s], 1.0, self.bc_vel_x_right[None]) \
                                                    - self.F[self.nx - 1, j, k, LR[s]] \
                                                    + feq(s, 1.0, self.bc_vel_x_right[None])

        # Y-left / Y-right
        if ti.static(self.bc_y_left == 1):
            for i, k in ti.ndrange((0, self.nx), (0, self.nz)):
                if self.solid[i, 0, k] == 0:
                    for s in ti.static(range(19)):
                        if self.solid[i, 1, k] > 0:
                            self.F[i, 0, k, s] = feq(s, self.rho_bcyl, self.v[i, 1, k])
                        else:
                            self.F[i, 0, k, s] = feq(s, self.rho_bcyl, self.v[i, 0, k])
        if ti.static(self.bc_y_left == 2):
            for i, k in ti.ndrange((0, self.nx), (0, self.nz)):
                if self.solid[i, 0, k] == 0:
                    for s in ti.static(range(19)):
                        self.F[i, 0, k, s] = feq(LR[s], 1.0, self.bc_vel_y_left[None]) \
                                          - self.F[i, 0, k, LR[s]] \
                                          + feq(s, 1.0, self.bc_vel_y_left[None])
        if ti.static(self.bc_y_right == 1):
            for i, k in ti.ndrange((0, self.nx), (0, self.nz)):
                if self.solid[i, self.ny - 1, k] == 0:
                    for s in ti.static(range(19)):
                        if self.solid[i, self.ny - 2, k] > 0:
                            self.F[i, self.ny - 1, k, s] = feq(s, self.rho_bcyr, self.v[i, self.ny - 2, k])
                        else:
                            self.F[i, self.ny - 1, k, s] = feq(s, self.rho_bcyr, self.v[i, self.ny - 1, k])
        if ti.static(self.bc_y_right == 2):
            for i, k in ti.ndrange((0, self.nx), (0, self.nz)):
                if self.solid[i, self.ny - 1, k] == 0:
                    for s in ti.static(range(19)):
                        self.F[i, self.ny - 1, k, s] = feq(LR[s], 1.0, self.bc_vel_y_right[None]) \
                                                    - self.F[i, self.ny - 1, k, LR[s]] \
                                                    + feq(s, 1.0, self.bc_vel_y_right[None])

        # Z-left / Z-right
        if ti.static(self.bc_z_left == 1):
            for i, j in ti.ndrange((0, self.nx), (0, self.ny)):
                if self.solid[i, j, 0] == 0:
                    for s in ti.static(range(19)):
                        if self.solid[i, j, 1] > 0:
                            self.F[i, j, 0, s] = feq(s, self.rho_bczl, self.v[i, j, 1])
                        else:
                            self.F[i, j, 0, s] = feq(s, self.rho_bczl, self.v[i, j, 0])
        if ti.static(self.bc_z_left == 2):
            for i, j in ti.ndrange((0, self.nx), (0, self.ny)):
                if self.solid[i, j, 0] == 0:
                    for s in ti.static(range(19)):
                        self.F[i, j, 0, s] = feq(LR[s], 1.0, self.bc_vel_z_left[None]) \
                                          - self.F[i, j, 0, LR[s]] \
                                          + feq(s, 1.0, self.bc_vel_z_left[None])
        if ti.static(self.bc_z_right == 1):
            for i, j in ti.ndrange((0, self.nx), (0, self.ny)):
                if self.solid[i, j, self.nz - 1] == 0:
                    for s in ti.static(range(19)):
                        if self.solid[i, j, self.nz - 2] > 0:
                            self.F[i, j, self.nz - 1, s] = feq(s, self.rho_bczr, self.v[i, j, self.nz - 2])
                        else:
                            self.F[i, j, self.nz - 1, s] = feq(s, self.rho_bczr, self.v[i, j, self.nz - 1])
        if ti.static(self.bc_z_right == 2):
            for i, j in ti.ndrange((0, self.nx), (0, self.ny)):
                if self.solid[i, j, self.nz - 1] == 0:
                    for s in ti.static(range(19)):
                        self.F[i, j, self.nz - 1, s] = feq(LR[s], 1.0, self.bc_vel_z_right[None]) \
                                                    - self.F[i, j, self.nz - 1, LR[s]] \
                                                    + feq(s, 1.0, self.bc_vel_z_right[None])

    @ti.kernel
    def Boundary_condition_psi(self):
        if ti.static(self.bc_psi_x_left == 1):
            for j, k in ti.ndrange((0, self.ny), (0, self.nz)):
                if self.solid[0, j, k] == 0:
                    self.psi[0, j, k] = self.psi_x_left
                    self.rho_r[0, j, k] = (self.psi_x_left + 1.0) / 2.0
                    self.rho_b[0, j, k] = 1.0 - self.rho_r[0, j, k]
        if ti.static(self.bc_psi_x_right == 1):
            for j, k in ti.ndrange((0, self.ny), (0, self.nz)):
                if self.solid[self.nx - 1, j, k] == 0:
                    self.psi[self.nx - 1, j, k] = self.psi_x_right
                    self.rho_r[self.nx - 1, j, k] = (self.psi_x_right + 1.0) / 2.0
                    self.rho_b[self.nx - 1, j, k] = 1.0 - self.rho_r[self.nx - 1, j, k]
        if ti.static(self.bc_psi_y_left == 1):
            for i, k in ti.ndrange((0, self.nx), (0, self.nz)):
                if self.solid[i, 0, k] == 0:
                    self.psi[i, 0, k] = self.psi_y_left
                    self.rho_r[i, 0, k] = (self.psi_y_left + 1.0) / 2.0
                    self.rho_b[i, 0, k] = 1.0 - self.rho_r[i, 0, k]
        if ti.static(self.bc_psi_y_right == 1):
            for i, k in ti.ndrange((0, self.nx), (0, self.nz)):
                if self.solid[i, self.ny - 1, k] == 0:
                    self.psi[i, self.ny - 1, k] = self.psi_y_right
                    self.rho_r[i, self.ny - 1, k] = (self.psi_y_right + 1.0) / 2.0
                    self.rho_b[i, self.ny - 1, k] = 1.0 - self.rho_r[i, self.ny - 1, k]
        if ti.static(self.bc_psi_z_left == 1):
            for i, j in ti.ndrange((0, self.nx), (0, self.ny)):
                if self.solid[i, j, 0] == 0:
                    self.psi[i, j, 0] = self.psi_z_left
                    self.rho_r[i, j, 0] = (self.psi_z_left + 1.0) / 2.0
                    self.rho_b[i, j, 0] = 1.0 - self.rho_r[i, j, 0]
        if ti.static(self.bc_psi_z_right == 1):
            for i, j in ti.ndrange((0, self.nx), (0, self.ny)):
                if self.solid[i, j, self.nz - 1] == 0:
                    self.psi[i, j, self.nz - 1] = self.psi_z_right
                    self.rho_r[i, j, self.nz - 1] = (self.psi_z_right + 1.0) / 2.0
                    self.rho_b[i, j, self.nz - 1] = 1.0 - self.rho_r[i, j, self.nz - 1]

    @ti.kernel
    def apply_reservoirs(self):
        """Density-prescribed reservoirs (2D CG2 mirror): pin psi and the
        colour masses at (res_psi, res_rho) and re-equilibrate f at the
        local velocity.  f64 counters record every change applied (mass
        sentinel).  End-of-step hook, active only when use_reservoirs."""
        for i, j, k in self.res_mask:
            if self.res_mask[i, j, k] != 0 and self.solid[i, j, k] == 0:
                ps = self.res_psi[i, j, k]
                rr = self.res_rho[i, j, k]
                uloc = self.v[i, j, k]
                rr_new = rr * (ps + 1.0) / 2.0
                rb_new = rr - rr_new
                self.inj_r[None] += rr_new - self.rho_r[i, j, k]
                self.inj_b[None] += rb_new - self.rho_b[i, j, k]
                self.inj_m[None] += rr - self.rho[i, j, k]
                self.rho_r[i, j, k] = rr_new
                self.rho_b[i, j, k] = rb_new
                self.psi[i, j, k] = ps
                self.rho[i, j, k] = rr
                for s in ti.static(range(19)):
                    fe = feq(s, rr, uloc)
                    self.f[i, j, k, s] = fe
                    self.F[i, j, k, s] = fe

    @ti.kernel
    def streaming3(self):
        for i, j, k in self.rho:
            if i < self.nx and j < self.ny and k < self.nz and self.solid[i, j, k] == 0:
                self.rho[i, j, k] = 0.0
                self.v[i, j, k] = ti.Vector([0.0, 0.0, 0.0])

                self.rho_r[i, j, k] = self.rhor[i, j, k]
                self.rho_b[i, j, k] = self.rhob[i, j, k]
                self.rhor[i, j, k] = 0.0
                self.rhob[i, j, k] = 0.0

                for s in ti.static(range(19)):
                    self.f[i, j, k, s] = self.F[i, j, k, s]
                    self.rho[i, j, k] += self.f[i, j, k, s]
                    self.v[i, j, k] += e_f[s] * self.f[i, j, k, s]

                self.v[i, j, k] /= self.rho[i, j, k]
                self.v[i, j, k] += (self.force_at(i, j, k) / 2) / self.rho[i, j, k]
                # FIXED parenthesisation (3D upstream :612 bug NOT inherited)
                self.psi[i, j, k] = (self.rho_r[i, j, k] - self.rho_b[i, j, k]) / (self.rho_r[i, j, k] + self.rho_b[i, j, k])

    @ti.kernel
    def color_gradient_probe(self, out: ti.types.ndarray()):
        """Read-only diagnostic: raw Compute_C colour-gradient vectors on
        fluid nodes (audit / wettability-diagnosis use; nothing in step()
        calls this)."""
        for i, j, k in self.rho:
            if i < self.nx and j < self.ny and k < self.nz and self.solid[i, j, k] == 0:
                C = self.Compute_C(ti.Vector([i, j, k]))
                out[i, j, k, 0] = C[0]
                out[i, j, k, 1] = C[1]
                out[i, j, k, 2] = C[2]

    def step(self):
        """Advance one timestep."""
        self.collision()
        self.F.fill(0.0)   # streaming1 accumulates (see its docstring)
        self.streaming1()
        self.Boundary_condition()
        self.streaming3()
        self.Boundary_condition_psi()
        if self.use_reservoirs:
            self.apply_reservoirs()

    # --------------------------------------------------------
    #  Host-side helpers (call OUTSIDE the timestep loop only)
    # --------------------------------------------------------

    def psi_snapshot(self):
        return self.psi.to_numpy()

    def color_gradient_snapshot(self):
        """Host wrapper for color_gradient_probe (PR-2 instrument)."""
        out = np.zeros((self.nx, self.ny, self.nz, 3), dtype=np.float32)
        self.color_gradient_probe(out)
        return out

    def macro_snapshot(self):
        return self.rho.to_numpy(), self.v.to_numpy()

    def color_masses(self):
        """(sum rho_r, sum rho_b) over all nodes — colour-mass sentinel
        (f64 accumulation)."""
        return (float(self.rho_r.to_numpy().sum(dtype=np.float64)),
                float(self.rho_b.to_numpy().sum(dtype=np.float64)))

    def total_mass(self):
        return float(self.rho.to_numpy().sum(dtype=np.float64))


if __name__ == '__main__':
    # First-compile smoke: single-phase periodic cube (psi=-1 uniform),
    # report colour-mass drift + timing.  Physics validations live in
    # validation_cg3d_*.py.
    import time
    n = int(os.environ.get('LBM_SMOKE_N', '64'))
    steps = int(os.environ.get('LBM_SMOKE_STEPS', '500'))
    s = ColorGradientSolver3D(n, n, n, CapA=0.02)
    psi0 = -np.ones((n, n, n), dtype=np.float32)
    solid = np.zeros((n, n, n), dtype=np.int8)
    s.init(psi0, solid)
    m0 = s.color_masses()
    t0 = time.time()
    for it in range(steps):
        s.step()
    wall = time.time() - t0
    m1 = s.color_masses()
    v = s.v.to_numpy()
    print('smoke %d^3 x %d steps: wall=%.1fs, %.1f steps/s, %.1f MLUPS'
          % (n, steps, wall, steps / wall, n**3 * steps / wall / 1e6))
    print('colour-mass drift: r %.3e, b %.3e'
          % ((m1[0] - m0[0]) / max(m0[0], 1e-30),
             (m1[1] - m0[1]) / max(m0[1], 1e-30)))
    print('max|v| = %.3e (single phase, zero force -> ~0)' % np.abs(v).max())
