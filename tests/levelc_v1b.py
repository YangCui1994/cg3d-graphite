"""V1b diagnostic — boundary / static Pc / dynamic Pc separation.

Task BI-V1B-DIAGNOSTIC-001 (V1B_DIAGNOSTIC_CONTRACT.md).  Separates the
three contributions the V1 review could not: bulk slit hydraulic
resistance, reservoir/membrane/open-buffer boundary resistance, and the
moving-meniscus capillary pressure vs the static slit value.

NO solver modification.  New V1b files only (this driver +
results/levelc_v1b/**).  Fixed assumptions (contract section 3):
CapA=0.06, nu_l=nu_g=0.1, unit density ratio, psi=-1 wetting,
psi_solid=-0.68, z-periodic slit, no imposed pressure difference.

MODES
-----
static   V1b-B: same-slit static capillary calibration.  A liquid plug
         [60,100) inside gas, in a fully periodic slit (x periodic by
         the lattice, z periodic, y walls psi_solid=-0.68) -- no
         reservoirs, no membranes, no forcing.  Pc_static from bulk
         phase pressures far from both menisci.
dynamic  V1b-A/C/D: separated open-boundary layout
             [0,3) wall | [3,11) pinned liquid reservoir (rho=1,psi=-1)
             | x=11 inlet membrane (mem_r: blocks gas, passes liquid)
             | [12,14) open buffer | [14,14+L) active slit
             | [14+L,16+L) open buffer | x=16+L outlet membrane
             (mem_b: blocks liquid, passes gas)
             | [17+L,25+L) pinned gas reservoir (rho=1,psi=+1)
             | [25+L,28+L) wall
         NO overlap between any reservoir mask and a membrane plane;
         buffers are ordinary same-cross-section slit nodes.  Both
         reservoirs pinned rho=1 -> imposed pressure difference zero.
collect  assembles results/levelc_v1b/summary.json +
         pressure_budget.csv + gates.csv + MANIFEST.json from the run
         reports and logs.

DECLARED ANALYSIS RULES (fixed before any run; mechanical)
----------------------------------------------------------
front (primary)   x_vol  : 12 + sum(psi<0 liquid fraction over [12,16+L))/A
front (secondary) x_cross: last x of the contiguous liquid run from x=12
fit window  : samples with t >= T_TRANS and x_vol >= x_ic_exit and
              x_vol <= x_stop, where
              T_TRANS  = ceil(3*hy^2/(4*nu))   (3x duct diffusion time)
              x_ic_exit= x0 + 2*hy             (meniscus 2 slit heights
                                                 beyond the IC position)
              x_stop   = 14 + L - 12            (12 lu outlet clearance)
              If NO sample satisfies the window rule the run FAILS
              explicitly (gate window_valid); argmax-of-empty can never
              silently return 0.
V_meas      : linear fit x_vol(t) on the window (chosen relation
              x = x0 + V t for this matched-viscosity two-bath case).
Pc_dynamic  : far-field linear pressure fits (liquid band
              [max(16,x_m-45), x_m-12]; gas band [x_m+12,
              min(14+L-3,x_m+45)]) extrapolated to x_m = x_vol; the
              median over window samples is used.
V_hyd       : Pc_dynamic * hy^2 / (12*mu*L_hyd), mu = nu*rho0 = 0.1,
              L_hyd = distance between the two membrane planes
              (includes the same-cross-section open buffers).
Poiseuille : |dp/dx| in both far-field columns vs 12*mu*V_meas/hy^2,
              each within 10%.
near-interface slab diagnostic from the V1 driver is NOT used; any
residual mention is labelled INVALID_NEAR_INTERFACE_DIAGNOSTIC.

Usage (from the product worktree root):
  python tests/levelc_v1b.py static  --hy 26 --tag static_h26
  python tests/levelc_v1b.py static  --hy 40 --tag static_h40
  python tests/levelc_v1b.py dynamic --hy 26 --tag dyn_h26
  python tests/levelc_v1b.py dynamic --hy 40 --tag dyn_h40
  python tests/levelc_v1b.py dynamic --hy 26 --L 472 --tag dyn_h26_2L
  python tests/levelc_v1b.py collect
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from lbm_solver_cg3d import ColorGradientSolver3D   # noqa: E402

OUTROOT = os.path.join(REPO, 'results', 'levelc_v1b')

CAPA = 0.06
SIGMA = 1.012 * CAPA          # repo calibration (ALGORITHM.md section 4)
NU = 0.1                      # matched viscosity both phases
RHO0 = 1.0
MU = NU * RHO0                # unit density ratio -> mu = nu
UMAX_CAP = 0.12               # operational stability cap (drivers' rule)
PSI_WALL = -0.68              # registry theta_liq ~ 30 deg (diagnostic)
THETA_REGISTRY = 30.0

WALL_T, RES_T, MEM_T, BUF_T = 3, 8, 1, 2
X_RES0, X_RES1 = 3, 11        # pinned liquid reservoir
X_MEM_IN = 11                 # inlet membrane plane (mem_r)
X_IN = 14                     # first active slit column (buffer [12,14))

STATIC_NX = 160
STATIC_SLAB = (60, 100)       # liquid plug
STATIC_CORE_LIQ = (68, 92)
STATIC_CORE_GAS = (110, 150)
STATIC_MIN, STATIC_CAP, STATIC_BLK = 8000, 60000, 250
STATIC_DRIFT_TOL, STATIC_UMAX_TOL = 1e-3, 5e-6
STATIC_PSI_TOL = 0.90         # bulk-phase node filter |psi| threshold

T0_WALL = None                # filled by prov()


# ---------------------------------------------------------------- provenance
def prov(cmd_argv):
    script = os.path.abspath(__file__)
    with open(script, 'rb') as f:
        psha = hashlib.sha256(f.read()).hexdigest()

    def gitq(*a):
        return subprocess.run(['git', '-C', REPO, *a], text=True,
                              capture_output=True).stdout.strip()
    return dict(
        producer_script='tests/levelc_v1b.py',
        producer_sha256=psha,
        run_head=gitq('rev-parse', 'HEAD'),
        worktree_dirty=bool(gitq('status', '--porcelain')),
        command=' '.join(['python'] + list(cmd_argv)),
        started_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        finished_at=None, exit_code=None)


def prov_finish(p, exit_code):
    p['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    p['exit_code'] = int(exit_code)


def write_csv(path, header, rows, p):
    path = os.path.abspath(path)
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    side = os.path.splitext(path)[0] + '.prov.json'
    with open(side, 'w') as f:
        json.dump({**p, 'artifact': os.path.basename(path),
                   'artifact_sha256': hashlib.sha256(
                       open(path, 'rb').read()).hexdigest()}, f, indent=1)


def write_json(path, obj):
    with open(os.path.abspath(path), 'w') as f:
        json.dump(obj, f, indent=1, sort_keys=False)


# ------------------------------------------------------------------ layout
def layout(L, hy, x0):
    buf0 = X_IN + L                    # outlet buffer start
    x_mem_out = buf0 + BUF_T
    gas0, gas1 = x_mem_out + 1, x_mem_out + 1 + RES_T
    nx = gas1 + WALL_T
    return dict(
        nx=nx, hy=hy, nz=6, L_slit=L, x0=x0,
        wall_in=[0, 3], liq_res=[X_RES0, X_RES1], mem_in=X_MEM_IN,
        in_buffer=[X_MEM_IN + 1, X_IN], slit=[X_IN, buf0],
        out_buffer=[buf0, x_mem_out], mem_out=x_mem_out,
        gas_res=[gas0, gas1], wall_out=[gas1, nx],
        L_hyd=float(x_mem_out - X_MEM_IN),
        note='membrane planes are ordinary fluid nodes outside both '
             'reservoir masks; buffers are same-cross-section fluid')


def t_trans(hy):
    return int(np.ceil(3.0 * hy * hy / (4.0 * NU)))


# ------------------------------------------------------------- static (B)
def run_static(args):
    p = prov(sys.argv)
    hy = args.hy
    nx, nz = STATIC_NX, 6
    ny = hy + 2
    y0, y1 = 1, 1 + hy
    s0, s1 = STATIC_SLAB

    solid = np.ones((nx, ny, nz), dtype=np.int8)
    solid[:, y0:y1, :] = 0                    # slit, x-periodic, no ends
    psi_solid = np.full((nx, ny, nz), PSI_WALL, dtype=np.float32)
    psi0 = np.ones((nx, ny, nz), dtype=np.float32)
    psi0[solid != 0] = 0.0
    psi0[s0:s1, y0:y1, :] = -1.0

    s = ColorGradientSolver3D(nx, ny, nz, niu_l=NU, niu_g=NU, CapA=CAPA)
    s.set_psi_solid_field(psi_solid)
    # no membranes, no reservoirs, no forcing (contract V1b-B)
    s.init(psi0, solid)

    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)
    lay = dict(nx=nx, ny=ny, nz=nz, hy=hy, slab=[s0, s1],
               core_liq=STATIC_CORE_LIQ, core_gas=STATIC_CORE_GAS,
               boundary='x periodic (lattice wrap), z periodic, '
                        'y walls psi_solid=-0.68; no reservoirs/'
                        'membranes/forcing')
    print(f'[{args.tag}] static slit nx={nx} ny={ny} nz={nz} '
          f'slab=[{s0},{s1})', flush=True)

    l0, l1 = STATIC_CORE_LIQ
    g0, g1 = STATIC_CORE_GAS
    rows = []
    umax_hist, pc_hist = [], []
    it = 0
    exit_reason = 'steps_cap'
    t_start = time.time()
    while it < STATIC_CAP:
        for _ in range(STATIC_BLK):
            it += 1
            s.step()
        psi = s.psi_snapshot()
        rho, v = s.macro_snapshot()
        if not (np.isfinite(psi).all() and np.isfinite(rho).all()):
            exit_reason = f'NaN/Inf at step {it}'
            print(f'[{args.tag}] {exit_reason}', flush=True)
            break
        vm = np.linalg.norm(v, axis=3)
        umax = float(vm[solid == 0].max())
        pl_nodes = rho[l0:l1, y0:y1, :]
        pg_nodes = rho[g0:g1, y0:y1, :]
        pl = float(pl_nodes.mean()) / 3.0
        pg = float(pg_nodes.mean()) / 3.0
        pc = pg - pl
        rows.append((it, umax, pl, pg, pc,
                     float(psi[l0:l1, y0:y1, :].mean()),
                     float(psi[g0:g1, y0:y1, :].mean())))
        umax_hist.append(umax)
        pc_hist.append(pc)
        if it % (STATIC_BLK * 10) == 0:
            print(f'[{args.tag}] {it:6d} umax={umax:.2e} Pc={pc:.6e}',
                  flush=True)
        if it >= STATIC_MIN and len(pc_hist) >= 10:
            w = pc_hist[-10:]
            drift = (w[-1] - w[0]) / max(abs(np.mean(w)), 1e-30)
            if abs(drift) < STATIC_DRIFT_TOL \
                    and umax < STATIC_UMAX_TOL:
                exit_reason = (f'converged at {it} '
                               f'(umax={umax:.2e} < {STATIC_UMAX_TOL}, '
                               f'Pc rel drift {drift:.1e} < '
                               f'{STATIC_DRIFT_TOL} over last 10 blocks)')
                break

    psi_f = s.psi_snapshot()
    rho_f, v_f = s.macro_snapshot()
    # bulk bands filtered by |psi| (defensive; bands are pure phase by
    # construction after relaxation)
    m_l = (psi_f[l0:l1, y0:y1, :] < -STATIC_PSI_TOL)
    m_g = (psi_f[g0:g1, y0:y1, :] > STATIC_PSI_TOL)
    p_liq = float(rho_f[l0:l1, y0:y1, :][m_l].mean()) / 3.0
    p_gas = float(rho_f[g0:g1, y0:y1, :][m_g].mean()) / 3.0
    pc_static = p_gas - p_liq
    c_static = pc_static * hy / (2.0 * SIGMA)
    theta = float(np.degrees(np.arccos(np.clip(c_static, -1.0, 1.0))))

    write_csv(os.path.join(out, 'static_series.csv'),
              ['step', 'umax', 'p_liq', 'p_gas', 'Pc',
               'psi_mean_liq_band', 'psi_mean_gas_band'], rows, p)
    axial = [(x, float(psi_f[x, y0:y1, :].mean()),
              float(rho_f[x, y0:y1, :].mean()) / 3.0)
             for x in range(nx)]
    write_csv(os.path.join(out, 'axial_static.csv'),
              ['x', 'psi_mean', 'p_mean'], axial, p)
    np.savez_compressed(os.path.join(out, 'fields_final.npz'),
                        psi=psi_f.astype(np.float32),
                        rho=rho_f.astype(np.float32))

    rep = dict(
        mode='static', tag=args.tag,
        Pc_static=pc_static, p_liq=p_liq, p_gas=p_gas,
        C_static=c_static, theta_static_slit_deg=theta,
        registry_theta_deg=THETA_REGISTRY,
        registry_C=np.cos(np.radians(THETA_REGISTRY)),
        C_static_over_registry=float(c_static
                                     / np.cos(np.radians(THETA_REGISTRY))),
        convergence=dict(exit_reason=exit_reason, steps_run=it,
                         umax_final=float(umax_hist[-1]),
                         umax_min=float(min(umax_hist)),
                         Pc_last10_rel_drift=float(
                             (pc_hist[-1] - pc_hist[-10])
                             / max(abs(np.mean(pc_hist[-10:])), 1e-30)),
                         drift_tol=STATIC_DRIFT_TOL,
                         umax_tol=STATIC_UMAX_TOL,
                         note='convergence judged on umax decay + Pc '
                              'drift; process completion != convergence'),
        layout=lay, wall_s=time.time() - t_start,
        nan=(exit_reason.startswith('NaN')),
        prov=p)
    write_json(os.path.join(out, 'report.json'), rep)
    prov_finish(p, 0)
    print(f'[{args.tag}] Pc_static={pc_static:.6e} C={c_static:.4f} '
          f'theta_slit={theta:.2f} deg ({exit_reason})', flush=True)
    return 0


# ------------------------------------------------------------ dynamic (A/C/D)
def run_dynamic(args):
    p = prov(sys.argv)
    hy = args.hy
    lay = layout(args.L, hy, args.x0)
    nx, ny, nz = lay['nx'], hy + 2, 6
    y0, y1 = 1, 1 + hy
    buf0 = lay['out_buffer'][0]
    x_mem_out = lay['mem_out']
    L_hyd = lay['L_hyd']

    solid = np.ones((nx, ny, nz), dtype=np.int8)
    solid[X_RES0:lay['wall_out'][0], y0:y1, :] = 0   # fluid corridor:
    # reservoirs + membrane planes + buffers + slit share the slit
    # cross-section; everything else is wall.
    mem_r = np.zeros((nx, ny, nz), dtype=np.int8)
    mem_b = np.zeros((nx, ny, nz), dtype=np.int8)
    mem_r[X_MEM_IN, :, :] = 1     # inlet : blocks gas, passes liquid
    mem_b[x_mem_out, :, :] = 1    # outlet: blocks liquid, passes gas
    liq_res = np.zeros((nx, ny, nz), dtype=np.int8)
    liq_res[X_RES0:X_RES1, y0:y1, :] = 1
    gas_res = np.zeros((nx, ny, nz), dtype=np.int8)
    gas_res[lay['gas_res'][0]:lay['gas_res'][1], y0:y1, :] = 1
    assert not (liq_res & mem_r).any() and not (gas_res & mem_b).any()
    assert not ((liq_res | gas_res) & (mem_r | mem_b)).any(), \
        'reservoir/membrane overlap'

    psi_solid = np.full((nx, ny, nz), PSI_WALL, dtype=np.float32)
    psi0 = np.ones((nx, ny, nz), dtype=np.float32)
    psi0[solid != 0] = 0.0
    psi0[X_RES0:args.x0, y0:y1, :] = -1.0    # reservoir+mem plane+buffer+slug

    s = ColorGradientSolver3D(nx, ny, nz, niu_l=NU, niu_g=NU, CapA=CAPA)
    s.set_psi_solid_field(psi_solid)
    s.set_membranes(mem_r, mem_b)
    s.set_reservoirs(liq_res, -1.0, RHO0)    # both pinned rho=1: imposed
    s.set_reservoirs(gas_res, +1.0, RHO0)    # pressure difference = 0
    s.init(psi0, solid)

    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)
    t_tr = t_trans(hy)
    x_ic_exit = args.x0 + 2.0 * hy
    x_stop = float(X_IN + args.L - 12)
    print(f'[{args.tag}] dynamic nx={nx} ny={ny} L_hyd={L_hyd:.0f} '
          f'T_TRANS={t_tr} x_ic_exit={x_ic_exit:.0f} x_stop={x_stop:.0f}',
          flush=True)

    m0 = s.color_masses()
    t_s, xv_s, xc_s = [], [], []
    probe_s = []
    axial_mid = None
    nan_at, umax_break = None, None
    it = 0
    t_start = time.time()
    exit_reason = 'steps_cap'
    while it < args.steps:
        it += 1
        s.step()
        if it % args.every == 0:
            psi = s.psi_snapshot()
            if not np.isfinite(psi).all():
                nan_at = it
                exit_reason = f'NaN/Inf at step {it}'
                print(f'[{args.tag}] {exit_reason}', flush=True)
                break
            liq = (1.0 - psi[12:buf0, y0:y1, :]) * 0.5
            x_vol = 12.0 + float(liq.sum()) / (hy * nz)
            colm = psi[12:buf0, y0:y1, :].mean(axis=(1, 2))
            below = colm < 0.0
            x_cross = 11.0
            if below[0]:
                idx = np.where(~below)[0]
                x_cross = 11.0 + (idx[0] - 1 if len(idx) else len(below) - 1)
            t_s.append(it)
            xv_s.append(x_vol)
            xc_s.append(x_cross)
        if it % args.every_v == 0:
            rho, v = s.macro_snapshot()
            if not np.isfinite(rho).all():
                nan_at = it
                exit_reason = f'NaN/Inf (rho) at step {it}'
                break
            vm = np.linalg.norm(v, axis=3)
            fl = solid == 0
            umax = float(vm[fl].max())
            urms = float(np.sqrt((vm[fl] ** 2).mean()))
            if umax > UMAX_CAP and umax_break is None:
                umax_break = it
            prof_p = rho[:, y0:y1, :].mean(axis=(1, 2)) / 3.0
            xm = float(xv_s[-1]) if xv_s else float(args.x0)
            la, lb = max(16, int(xm) - 45), int(xm) - 12
            ga, gb = int(xm) + 12, min(buf0 - 3, int(xm) + 45)
            row = dict(t=it, umax=umax, urms=urms)
            if lb - la >= 8 and gb - ga >= 8:
                gl, cl = np.polyfit(np.arange(la, lb), prof_p[la:lb], 1)
                gg, cg = np.polyfit(np.arange(ga, gb), prof_p[ga:gb], 1)
                xm_f = float(xm)
                p_at = lambda g_, c_, x: c_ + g_ * x
                pc_dyn = p_at(gg, cg, xm_f) - p_at(gl, cl, xm_f)
                r2l = _r2(np.arange(la, lb), prof_p[la:lb], gl, cl)
                r2g = _r2(np.arange(ga, gb), prof_p[ga:gb], gg, cg)
                row.update(dpdx_liq=float(gl), dpdx_gas=float(gg),
                           r2_liq=r2l, r2_gas=r2g, Pc_dynamic=float(pc_dyn),
                           jump_in=float(rho[X_RES0 + 1:X_RES1 - 1,
                                             y0:y1, :].mean() / 3.0
                                         - p_at(gl, cl, float(X_IN))),
                           jump_out=float(
                               p_at(gg, cg, float(buf0 - 1))
                               - rho[lay['gas_res'][0] + 1:
                                     lay['gas_res'][1] - 1,
                                     y0:y1, :].mean() / 3.0))
            row['rho_res_liq'] = float(
                rho[X_RES0 + 1:X_RES1 - 1, y0:y1, :].mean())
            row['rho_res_gas'] = float(
                rho[lay['gas_res'][0] + 1:lay['gas_res'][1] - 1,
                    y0:y1, :].mean())
            bm = np.arange(max(X_IN, int(xm) - 6),
                           min(buf0, int(xm) + 6))
            u_band = v[bm, y0:y1, :, :]
            row['u_band_max'] = float(np.linalg.norm(
                u_band, axis=3).max())
            row['u_band_ux'] = float(u_band[..., 0].mean())
            row['u_band_ut_rms'] = float(np.sqrt(
                (u_band[..., 1] ** 2 + u_band[..., 2] ** 2).mean()))
            mm = s.color_masses()
            flx = s.reservoir_fluxes()
            row['m_r'], row['m_b'] = mm
            row['inj_r'], row['inj_b'], row['inj_m'] = (
                flx['inj_r'], flx['inj_b'], flx['inj_m'])
            row['closure_r'] = flx['inj_r'] - (mm[0] - m0[0])
            row['closure_b'] = flx['inj_b'] - (mm[1] - m0[1])
            probe_s.append(row)
            if axial_mid is None and x_vol >= (x_ic_exit + x_stop) / 2:
                axial_mid = [(x, float(psi[x, y0:y1, :].mean()),
                              float(prof_p[x])) for x in range(12, buf0)]
        if it % (args.every * 40) == 0:
            el = time.time() - t_start
            print(f'[{args.tag}] {it:6d}/{args.steps} '
                  f'x_vol={xv_s[-1]:7.2f} ({el:.0f}s, {it / el:.0f} st/s)',
                  flush=True)
        if it >= 1000 and xv_s and xv_s[-1] >= x_stop:
            exit_reason = f'front reached x_stop at step {it}'
            print(f'[{args.tag}] {exit_reason}', flush=True)
            break

    wall = time.time() - t_start
    psi_f = s.psi_snapshot()
    rho_f, v_f = s.macro_snapshot()
    mm_fin = s.color_masses()
    fl_fin = s.reservoir_fluxes()

    write_csv(os.path.join(out, 'front.csv'),
              ['t', 'x_vol', 'x_cross'],
              list(zip(t_s, xv_s, xc_s)), p)
    keys = ['t', 'umax', 'urms', 'dpdx_liq', 'dpdx_gas', 'r2_liq',
            'r2_gas', 'Pc_dynamic', 'jump_in', 'jump_out', 'rho_res_liq',
            'rho_res_gas', 'u_band_max', 'u_band_ux', 'u_band_ut_rms',
            'm_r', 'm_b', 'inj_r', 'inj_b', 'inj_m', 'closure_r',
            'closure_b']
    write_csv(os.path.join(out, 'probes.csv'), keys,
              [[r.get(k) for k in keys] for r in probe_s], p)
    axial_f = [(x, float(psi_f[x, y0:y1, :].mean()),
                float(rho_f[x, y0:y1, :].mean() / 3.0))
               for x in range(12, buf0)]
    write_csv(os.path.join(out, 'axial_final.csv'),
              ['x', 'psi_mean', 'p_mean'], axial_f, p)
    if axial_mid:
        write_csv(os.path.join(out, 'axial_mid.csv'),
                  ['x', 'psi_mean', 'p_mean'], axial_mid, p)
    np.savez_compressed(os.path.join(out, 'fields_final.npz'),
                        psi=psi_f.astype(np.float32),
                        rho=rho_f.astype(np.float32))

    a = analyze_dynamic(np.array(t_s, float), np.array(xv_s, float),
                        np.array(xc_s, float), probe_s, hy, L_hyd,
                        t_tr, x_ic_exit, x_stop)
    a.update(mode='dynamic', tag=args.tag, layout=lay, steps_run=it,
             wall_s=wall, exit_reason=exit_reason, nan_at=nan_at,
             umax_break=umax_break, x_stop=x_stop, T_TRANS=t_tr,
             x_ic_exit=x_ic_exit, sigma=SIGMA, capa=CAPA, nu=NU, mu=MU,
             psi_wall=PSI_WALL, prov=p,
             m_r_final=mm_fin[0], m_b_final=mm_fin[1],
             inj_r_final=fl_fin['inj_r'], inj_b_final=fl_fin['inj_b'],
             closure_r_final=fl_fin['inj_r'] - (mm_fin[0] - m0[0]),
             closure_b_final=fl_fin['inj_b'] - (mm_fin[1] - m0[1]),
             INVALID_NEAR_INTERFACE_DIAGNOSTIC=None)
    write_json(os.path.join(out, 'report.json'), a)
    prov_finish(p, 0)
    print(f'[{args.tag}] {exit_reason}; V_meas='
          f'{a.get("V_meas", float("nan")):.4e} R2='
          f'{a.get("R2_x_linear", float("nan")):.5f}', flush=True)
    return 0


def _r2(x, y, g, c):
    pred = c + g * x
    ss = float(((y - pred) ** 2).sum())
    tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss / tot if tot > 0 else float('nan')


def analyze_dynamic(t, xv, xc, probes, hy, L_hyd, t_tr, x_ic_exit,
                    x_stop):
    """Declared mechanical rule; explicit failure when the window
    threshold is never reached (V1b contract gate 5)."""
    res = dict(n_samples=len(t))
    win = np.where((t >= t_tr) & (xv >= x_ic_exit)
                   & (xv <= x_stop))[0]
    if len(win) < 20:
        res['window_valid'] = False
        res['window_fail_reason'] = (
            f'threshold never reached: only {len(win)} samples satisfy '
            f't>= {t_tr}, x>={x_ic_exit:.0f}, x<={x_stop:.0f} '
            f'(>=20 required) -- explicit FAIL, no argmax-of-empty')
        res['gates'] = dict(g1_no_nan=None, g2_umax_cap=None,
                            g3_zero_dp=None, g4_monotonic=None,
                            g5_window_valid=False, g6_r2=None,
                            g7_vhyd=None, g8_poiseuille=None)
        return res
    i0, i_hi = int(win[0]), int(win[-1])
    res['window_valid'] = True
    res['window_idx'] = [i0, i_hi]
    res['window_t'] = [float(t[i0]), float(t[i_hi])]
    res['window_x'] = [float(xv[i0]), float(xv[i_hi])]

    A = np.polyfit(t[i0:i_hi + 1], xv[i0:i_hi + 1], 1)
    r2 = _r2(t[i0:i_hi + 1], xv[i0:i_hi + 1], A[0], A[1])
    A2 = np.polyfit(t[i0:i_hi + 1], xc[i0:i_hi + 1], 1)
    r2c = _r2(t[i0:i_hi + 1], xc[i0:i_hi + 1], A2[0], A2[1])
    v_meas = float(A[0])
    res['V_meas'] = v_meas
    res['R2_x_linear'] = float(r2)
    res['V_meas_secondary'] = float(A2[0])
    res['R2_x_secondary'] = float(r2c)
    res['monotonic_window'] = bool(
        np.all(np.diff(xv[i0:i_hi + 1]) >= -0.5))

    wp = [r for r in probes
          if t_tr <= r['t'] <= t[i_hi] and 'Pc_dynamic' in r]
    if not wp:
        res['window_valid'] = False
        res['window_fail_reason'] = 'no pressure probes inside window'
        return res
    pc_med = float(np.median([r['Pc_dynamic'] for r in wp]))
    pc_mean = float(np.mean([r['Pc_dynamic'] for r in wp]))
    res['Pc_dynamic_median'] = pc_med
    res['Pc_dynamic_mean'] = pc_mean
    res['n_window_probes'] = len(wp)
    res['jump_in_median'] = float(np.median([r['jump_in'] for r in wp]))
    res['jump_out_median'] = float(
        np.median([r['jump_out'] for r in wp]))
    res['dpdx_liq_median'] = float(
        np.median([r['dpdx_liq'] for r in wp]))
    res['dpdx_gas_median'] = float(
        np.median([r['dpdx_gas'] for r in wp]))

    v_hyd = pc_med * hy * hy / (12.0 * MU * L_hyd)
    res['V_hyd'] = float(v_hyd)
    res['V_meas_over_V_hyd'] = float(v_meas / v_hyd)
    res['Ca'] = float(MU * v_meas / SIGMA)
    g_analytic = 12.0 * MU * v_meas / (hy * hy)
    res['G_poiseuille_analytic'] = float(g_analytic)
    res['dpdx_liq_over_G'] = float(abs(res['dpdx_liq_median'])
                                   / g_analytic)
    res['dpdx_gas_over_G'] = float(abs(res['dpdx_gas_median'])
                                   / g_analytic)
    res['jump_sum_over_Pc'] = float((res['jump_in_median']
                                     + res['jump_out_median']) / pc_med)
    res['rho_res_liq_dev_max'] = float(max(
        abs(r['rho_res_liq'] - 1.0) for r in wp))
    res['rho_res_gas_dev_max'] = float(max(
        abs(r['rho_res_gas'] - 1.0) for r in wp))
    res['closure_r_last'] = float(wp[-1]['closure_r'])
    res['closure_b_last'] = float(wp[-1]['closure_b'])
    res['u_band_max_max'] = float(max(r['u_band_max'] for r in wp))
    res['u_band_ut_rms_max'] = float(
        max(r['u_band_ut_rms'] for r in wp))
    res['umax_peak_window'] = float(max(r['umax'] for r in wp))

    res['gates'] = dict(
        g1_no_nan=True,
        g2_umax_cap=res['umax_peak_window'] <= UMAX_CAP,
        g3_zero_dp=(res['rho_res_liq_dev_max'] <= 1e-3
                    and res['rho_res_gas_dev_max'] <= 1e-3),
        g4_monotonic=res['monotonic_window'],
        g5_window_valid=True,
        g6_r2=float(r2) >= 0.995,
        g7_vhyd=abs(res['V_meas_over_V_hyd'] - 1.0) <= 0.10,
        g8_poiseuille=(abs(res['dpdx_liq_over_G'] - 1.0) <= 0.10
                       and abs(res['dpdx_gas_over_G'] - 1.0) <= 0.10),
        g9_mass_closure=None,   # reported numerically; no numeric gate
    )
    res['gates']['all_hard'] = all(
        v is True for k, v in res['gates'].items()
        if k not in ('g9_mass_closure', 'all_hard'))
    return res


# ---------------------------------------------------------------- collect
def collect(args):
    p = prov(sys.argv)
    tags = dict(static_h26=None, static_h40=None, dyn_h26=None,
                dyn_h40=None, dyn_h26_2L=None)
    for tag in tags:
        rp = os.path.join(OUTROOT, tag, 'report.json')
        if os.path.exists(rp):
            tags[tag] = json.load(open(rp))
    missing = [k for k, v in tags.items() if v is None]
    if missing:
        print('missing run reports:', missing)
        return 1

    s26, s40 = tags['static_h26'], tags['static_h40']
    c26, c40 = s26['C_static'], s40['C_static']
    static_rel = abs(c26 - c40) / (0.5 * (abs(c26) + abs(c40)))
    d26, d40, d2l = tags['dyn_h26'], tags['dyn_h40'], tags['dyn_h26_2L']
    L1 = d26['layout']['L_hyd']
    L2 = d2l['layout']['L_hyd']
    v1, v2 = d26['V_meas'], d2l['V_meas']
    l_eq = (v2 * L2 - v1 * L1) / (v1 - v2) if v1 != v2 else float('nan')
    # V2/V1 = (L1+Leq)/(L2+Leq)  ->  Leq = (V2*L2 - V1*L1)/(V1 - V2)

    def e(tag, key):
        r = tags[tag]
        return r.get(key)

    summary = dict(
        task='BI-V1B-DIAGNOSTIC-001',
        fixed=dict(CapA=CAPA, sigma=SIGMA, nu=NU, mu=MU,
                   psi_wall=PSI_WALL, rho0=RHO0,
                   theta_registry_deg=THETA_REGISTRY),
        static=dict(
            h26=dict(Pc_static=s26['Pc_static'], C_static=c26,
                     theta_slit_deg=s26['theta_static_slit_deg'],
                     convergence=s26['convergence']['exit_reason']),
            h40=dict(Pc_static=s40['Pc_static'], C_static=c40,
                     theta_slit_deg=s40['theta_static_slit_deg'],
                     convergence=s40['convergence']['exit_reason']),
            C_rel_diff=float(static_rel),
            gate_static_scaling=static_rel <= 0.10,
            C_over_registry=dict(
                h26=s26['C_static_over_registry'],
                h40=s40['C_static_over_registry'])),
        dynamic={t: dict(
            L_hyd=e(t, 'layout')['L_hyd'], V_meas=e(t, 'V_meas'),
            R2=e(t, 'R2_x_linear'), Pc_dynamic=e(t, 'Pc_dynamic_median'),
            V_hyd=e(t, 'V_hyd'),
            V_meas_over_V_hyd=e(t, 'V_meas_over_V_hyd'),
            dpdx_liq_over_G=e(t, 'dpdx_liq_over_G'),
            dpdx_gas_over_G=e(t, 'dpdx_gas_over_G'),
            jump_in=e(t, 'jump_in_median'), jump_out=e(t, 'jump_out_median'),
            jump_sum_over_Pc=e(t, 'jump_sum_over_Pc'),
            Ca=e(t, 'Ca'), gates=e(t, 'gates'),
            exit_reason=e(t, 'exit_reason'))
            for t in ('dyn_h26', 'dyn_h40', 'dyn_h26_2L')},
        length_scan=dict(L1=L1, L2=L2, V1=v1, V2=v2, L_eq=float(l_eq),
                         L_eq_over_L1=float(l_eq / L1),
                         old_V1_L_eq_over_L1=0.78,
                         note='diagnostic only (no numeric gate in V1b); '
                              'order-one value blocks V2 recommendation'),
        dynamic_static=dict(
            h26=dict(Pc_static=s26['Pc_static'],
                     Pc_dynamic=d26['Pc_dynamic_median'],
                     ratio=d26['Pc_dynamic_median'] / s26['Pc_static'],
                     theta_apparent_deg=float(np.degrees(np.arccos(
                         np.clip(d26['Pc_dynamic_median']
                                 * 26 / (2 * SIGMA), -1, 1)))),
                     Ca=d26['Ca']),
            h40=dict(Pc_static=s40['Pc_static'],
                     Pc_dynamic=d40['Pc_dynamic_median'],
                     ratio=d40['Pc_dynamic_median'] / s40['Pc_static'],
                     theta_apparent_deg=float(np.degrees(np.arccos(
                         np.clip(d40['Pc_dynamic_median']
                                 * 40 / (2 * SIGMA), -1, 1)))),
                     Ca=d40['Ca']),
            note='Pc_dynamic/Pc_static difference is a declared '
                 'moving-contact-line/model characteristic if the '
                 'hydraulic consistency gates pass; not a solver bug'),
        prov=p)
    write_json(os.path.join(OUTROOT, 'summary.json'), summary)

    rows = []
    for t in ('dyn_h26', 'dyn_h40', 'dyn_h26_2L'):
        r = summary['dynamic'][t]
        rows.append([t, r['L_hyd'], r['V_meas'], r['Pc_dynamic'],
                     r['V_hyd'], r['V_meas_over_V_hyd'],
                     r['dpdx_liq_over_G'], r['dpdx_gas_over_G'],
                     r['jump_in'], r['jump_out'], r['jump_sum_over_Pc'],
                     r['Ca']])
    write_csv(os.path.join(OUTROOT, 'pressure_budget.csv'),
              ['tag', 'L_hyd', 'V_meas', 'Pc_dynamic', 'V_hyd',
               'V_meas/V_hyd', 'dpdx_liq/G', 'dpdx_gas/G', 'jump_in',
               'jump_out', '(jump_in+jump_out)/Pc', 'Ca'], rows, p)
    grows = []
    for t in ('static_h26', 'static_h40', 'dyn_h26', 'dyn_h40',
              'dyn_h26_2L'):
        r = tags[t]
        g = r.get('gates')
        if g:
            grows.append([t] + [g.get(k) for k in (
                'g1_no_nan', 'g2_umax_cap', 'g3_zero_dp', 'g4_monotonic',
                'g5_window_valid', 'g6_r2', 'g7_vhyd', 'g8_poiseuille',
                'g9_mass_closure', 'all_hard')])
        else:
            grows.append([t, 'static run', '', '', '', '', '', '', '',
                          '', ''])
    grows.append(['static_scaling_gate', summary['static']
                  ['gate_static_scaling'], '', '', '', '', '', '', '',
                  '', ''])
    write_csv(os.path.join(OUTROOT, 'gates.csv'),
              ['tag', 'g1_no_nan', 'g2_umax', 'g3_zero_dp',
               'g4_monotonic', 'g5_window', 'g6_r2>=0.995',
               'g7_|V/Vhyd-1|<=0.1', 'g8_poiseuille<=0.1',
               'g9_mass_reported', 'all_hard'], grows, p)

    manifest = dict(producer='tests/levelc_v1b.py',
                    producer_sha256=p['producer_sha256'],
                    runs={})
    for tag in ('static_h26', 'static_h40', 'dyn_h26', 'dyn_h40',
                'dyn_h26_2L'):
        rp = tags[tag]['prov']
        entry = dict(command=rp['command'], run_head=rp['run_head'],
                     producer_sha256=rp['producer_sha256'],
                     started_at=rp['started_at'],
                     exit_code=rp['exit_code'])
        lg = os.path.join(OUTROOT, 'logs', tag + '.log')
        ex = os.path.join(OUTROOT, 'logs', tag + '.exit')
        if os.path.exists(ex):
            entry['shell_exit_code'] = int(open(ex).read().strip())
        if os.path.exists(lg):
            entry['console_log'] = os.path.relpath(lg, REPO)
        entry['artifacts'] = {}
        d = os.path.join(OUTROOT, tag)
        for fn in sorted(os.listdir(d)):
            fp = os.path.join(d, fn)
            entry['artifacts'][fn] = hashlib.sha256(
                open(fp, 'rb').read()).hexdigest()
        manifest['runs'][tag] = entry
    manifest['summary'] = 'see summary.json / EXECUTION_REPORT.md / ' \
                          'PROVENANCE.md in this directory'
    write_json(os.path.join(OUTROOT, 'MANIFEST.json'), manifest)
    prov_finish(p, 0)
    print(json.dumps(dict(static_C_rel_diff=static_rel,
                          L_eq_over_L1=float(l_eq / L1),
                          gates={t: summary['dynamic'][t]['gates']
                                 for t in summary['dynamic']}), indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='mode', required=True)
    ps = sub.add_parser('static')
    ps.add_argument('--hy', type=int, default=26)
    ps.add_argument('--tag', default='static_h26')
    pd = sub.add_parser('dynamic')
    pd.add_argument('--hy', type=int, default=26)
    pd.add_argument('--L', type=int, default=236)
    pd.add_argument('--x0', type=int, default=42)
    pd.add_argument('--steps', type=int, default=60000)
    pd.add_argument('--every', type=int, default=250)
    pd.add_argument('--every-v', dest='every_v', type=int, default=1000)
    pd.add_argument('--tag', default='dyn_h26')
    sub.add_parser('collect')
    args = ap.parse_args()
    os.makedirs(os.path.join(OUTROOT, 'logs'), exist_ok=True)
    rc = dict(static=run_static, dynamic=run_dynamic,
              collect=collect)[args.mode](args)
    sys.exit(rc)


if __name__ == '__main__':
    main()
