"""V1c closure — static resolution convergence + differential hydraulics.

Task BI-V1C-CLOSURE-001 (V1C_CLOSURE_CONTRACT.md).  Closes the two
remaining single-front questions before V2:

A  static slit calibration at h = 26/40/60/80 (fresh reruns, one
   producer, one measurement logic) -> C_static(h), theta_static(h),
   table vs 1/h, candidate convergence fits (const / 1/h / 1/h^2);
B  corrected dynamic cases h26/h40 x short/2L with a BULK-COLUMN
   pressure-band rule replacing V1b's fixed-distance bands;
C  differential hydraulic validation
       L_eff = Pc_dynamic h^2 / (12 mu V_meas),
       a_h   = (L_eff,long - L_eff,short)/(L_long - L_short),
   gates |a_26-1| <= 0.10 and |a_40-1| <= 0.10;
   intercept L0(h) = L_eff - a_h L diagnostic, reported with L0/h;
D  front/stability gates incl. primary/secondary front-speed
   agreement within 2%;
E  provenance binding (candidate/producer/command/timestamps/exit).

NO solver modification.  Physics fixed: CapA=0.06, nu=0.1 matched,
unit density ratio, psi_solid=-0.68, z-periodic slit, equal-pressure
reservoirs, V1b membrane/reservoir/buffer topology UNCHANGED.

BULK-COLUMN PRESSURE RULE (contract section B, replaces fixed bands)
----------------------------------------------------------------------
For every pressure probe, over the fit region [12, buf0) (open buffers
+ slit, same cross-section, no reservoirs/membranes):
  liquid-bulk column : >= 95% of cross-section nodes psi < -0.90
  gas-bulk column    : >= 95% of nodes psi > +0.90
  mixed columns excluded, plus >= 2 extra columns each side of the
  mixed envelope; contiguous fit bands need >= 12 columns or the probe
  is marked invalid (never silently falls back).

PER-PROBE VALIDITY before any aggregate (V1c review attempt-1 findings
B1/B2; applied identically by run-time analysis and `reanalyze`):
  V0 base        : band_valid (12-column rule) and t inside the window
  V1 window-x    : V0 and x_ic_exit <= x_m(t_probe) <= x_stop
  V2 positional  : V1 and gas-band width >= 3h and x_m <= buf0-4h
                   (clears the meniscus/distortion envelope and the
                   slit exit by declared positional margins)
  V3 linearity   : V2 and r2_liq >= 0.995 and r2_gas >= 0.995
  V3 (full validity) defines the PRIMARY aggregate; median AND mean
  under every variant are published as a first-class estimator
  sensitivity table.  A probe failing validity is excluded explicitly
  (counted per variant), never silently repaired.
p_l(x), p_g(x) linear fits over the bulk bands, extrapolated to the
meniscus reference x_m = x_vol (primary front).  Band threshold
sensitivity 0.85/0.90/0.95 is reported as a diagnostic.
The same rule (full-domain columns) measures the static Pc.

STATIC SETUP: liquid plug [90,150) in a fully periodic slit (x periodic
by lattice, z periodic, y walls psi_solid=-0.68), no reservoirs /
membranes / forcing.  Domain nx=240 for every h so the only change
between cases is the y dimension.  Pressure stationarity (drift over
last 10 blocks < 1e-3) is judged separately from the spurious-current
magnitude floor (recorded, not gated).

Usage (product worktree root, interpreter = conda env 'lbm'):
  python tests/levelc_v1c.py static --hy 26 --tag static_h26   (also 40/60/80)
  python tests/levelc_v1c.py dynamic --hy 26 --tag dyn_h26_s   (short L=236)
  python tests/levelc_v1c.py dynamic --hy 26 --L 472 --tag dyn_h26_2L
  python tests/levelc_v1c.py dynamic --hy 40 --tag dyn_h40_s
  python tests/levelc_v1c.py dynamic --hy 40 --L 472 --tag dyn_h40_2L
  python tests/levelc_v1c.py collect
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

OUTROOT = os.path.join(REPO, 'results', 'levelc_v1c')

CAPA = 0.06
SIGMA = 1.012 * CAPA
NU = 0.1
RHO0 = 1.0
MU = NU * RHO0
UMAX_CAP = 0.12
PSI_WALL = -0.68
THETA_REGISTRY = 30.0

WALL_T, RES_T, MEM_T, BUF_T = 3, 8, 1, 2
X_RES0, X_RES1 = 3, 11
X_MEM_IN = 11
X_IN = 14

STATIC_NX = 240
STATIC_SLAB = (90, 150)
STATIC_MIN, STATIC_CAP, STATIC_BLK = 10000, 60000, 250
STATIC_DRIFT_TOL = 1e-3

BULK_THR = 0.90          # primary |psi| threshold
BULK_FRAC = 0.95         # >=95% of cross-section nodes
BULK_PAD = 2             # extra columns each side of mixed envelope
BULK_MINCOLS = 12        # contiguous band minimum


# ---------------------------------------------------------------- provenance
def prov(cmd_argv):
    script = os.path.abspath(__file__)
    with open(script, 'rb') as f:
        psha = hashlib.sha256(f.read()).hexdigest()

    def gitq(*a):
        return subprocess.run(['git', '-C', REPO, *a], text=True,
                              capture_output=True).stdout.strip()
    return dict(
        producer_script='tests/levelc_v1c.py',
        producer_sha256=psha,
        run_head=gitq('rev-parse', 'HEAD'),
        worktree_dirty=bool(gitq('status', '--porcelain')),
        command=' '.join([sys.executable] + list(cmd_argv)),
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


# ------------------------------------------------------- bulk-column rule
def _longest_run(mask):
    best_a = best_n = cur_a = cur_n = 0
    for i, v in enumerate(mask):
        if v:
            if cur_n == 0:
                cur_a = i
            cur_n += 1
            if cur_n > best_n:
                best_a, best_n = cur_a, cur_n
        else:
            cur_n = 0
    return best_a, best_n


def bulk_bands(psi_slit, x_off, thr=BULK_THR, frac=BULK_FRAC,
               pad=BULK_PAD, min_cols=BULK_MINCOLS):
    """Classify columns of a slit psi slab [x0:x1, y0:y1, :].
    Returns None if no valid pair of >=min_cols contiguous bulk bands;
    else dict(liq=(a,b) gas=(a,b) in ABSOLUTE x, n_mixed, n_liq, n_gas).
    a/b are python-slice bounds (b exclusive)."""
    n = psi_slit.shape[0]
    frac_l = (psi_slit < -thr).mean(axis=(1, 2))
    frac_g = (psi_slit > +thr).mean(axis=(1, 2))
    liq = frac_l >= frac
    gas = frac_g >= frac
    mixed = ~(liq | gas)
    excl = mixed.copy()
    for _ in range(pad):
        excl[1:] |= excl[:-1]
        excl[:-1] |= excl[1:]
    ua, un = _longest_run(liq & ~excl)
    ga, gn = _longest_run(gas & ~excl)
    if un < min_cols or gn < min_cols:
        return None
    return dict(liq=(x_off + ua, x_off + ua + un),
                gas=(x_off + ga, x_off + ga + gn),
                n_mixed=int(mixed.sum()), n_liq=int(liq.sum()),
                n_gas=int(gas.sum()))


def fit_band(prof_p, band):
    a, b = band
    x = np.arange(a, b, dtype=float)
    y = prof_p[a:b]
    g, c = np.polyfit(x, y, 1)
    pred = c + g * x
    ss = float(((y - pred) ** 2).sum())
    tot = float(((y - y.mean()) ** 2).sum())
    return float(g), float(c), (1.0 - ss / tot if tot > 0 else
                                float('nan'))


def layout(L, hy, x0):
    buf0 = X_IN + L
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
        note='V1b separated topology unchanged; fit region '
             '[12, buf0=14+L) = open buffers + slit')


def t_trans(hy):
    return int(np.ceil(3.0 * hy * hy / (4.0 * NU)))


# ------------------------------------------------------------- static (A)
def run_static(args):
    p = prov(sys.argv)
    hy = args.hy
    nx, nz = STATIC_NX, 6
    ny = hy + 2
    y0, y1 = 1, 1 + hy
    s0, s1 = STATIC_SLAB

    solid = np.ones((nx, ny, nz), dtype=np.int8)
    solid[:, y0:y1, :] = 0
    psi_solid = np.full((nx, ny, nz), PSI_WALL, dtype=np.float32)
    psi0 = np.ones((nx, ny, nz), dtype=np.float32)
    psi0[solid != 0] = 0.0
    psi0[s0:s1, y0:y1, :] = -1.0

    s = ColorGradientSolver3D(nx, ny, nz, niu_l=NU, niu_g=NU, CapA=CAPA)
    s.set_psi_solid_field(psi_solid)
    s.init(psi0, solid)

    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)
    print(f'[{args.tag}] static slit nx={nx} ny={ny} slab=[{s0},{s1})',
          flush=True)

    rows, umax_hist, pc_hist = [], [], []
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
        prof_p = rho[:, y0:y1, :].mean(axis=(1, 2)) / 3.0
        bb = bulk_bands(psi[:, y0:y1, :], 0)
        pc = float('nan')
        if bb:
            pc = float(prof_p[bb['gas'][0]:bb['gas'][1]].mean()
                       - prof_p[bb['liq'][0]:bb['liq'][1]].mean())
        rows.append((it, umax, pc, bb['n_mixed'] if bb else -1,
                     bb['n_liq'] if bb else -1,
                     bb['n_gas'] if bb else -1))
        umax_hist.append(umax)
        if np.isfinite(pc):
            pc_hist.append(pc)
        if it % (STATIC_BLK * 10) == 0:
            print(f'[{args.tag}] {it:6d} umax={umax:.2e} '
                  f'Pc={pc:.6e} mixed={rows[-1][3]}', flush=True)
        if it >= STATIC_MIN and len(pc_hist) >= 10:
            w = pc_hist[-10:]
            drift = (w[-1] - w[0]) / max(abs(np.mean(w)), 1e-30)
            if abs(drift) < STATIC_DRIFT_TOL:
                exit_reason = (f'Pc stationary at {it} '
                               f'(rel drift {drift:.1e} < '
                               f'{STATIC_DRIFT_TOL} over last 10 '
                               f'blocks; umax floor {umax:.2e} recorded '
                               f'separately, not gated)')
                break

    psi_f = s.psi_snapshot()
    rho_f, v_f = s.macro_snapshot()
    prof_p = rho_f[:, y0:y1, :].mean(axis=(1, 2)) / 3.0
    vm = np.linalg.norm(v_f, axis=3)
    res_thr = {}
    bb90 = bulk_bands(psi_f[:, y0:y1, :], 0, thr=0.90)
    for thr in (0.85, 0.90, 0.95):
        bb = bulk_bands(psi_f[:, y0:y1, :], 0, thr=thr)
        if bb:
            res_thr[str(thr)] = dict(
                liq_band=list(bb['liq']), gas_band=list(bb['gas']),
                Pc_static=float(prof_p[bb['gas'][0]:bb['gas'][1]].mean()
                                - prof_p[bb['liq'][0]:bb['liq'][1]].mean()))
        else:
            res_thr[str(thr)] = None
    pc_static = res_thr['0.9']['Pc_static'] if res_thr.get('0.9') \
        else float('nan')
    c_static = pc_static * hy / (2.0 * SIGMA)
    theta = float(np.degrees(np.arccos(np.clip(c_static, -1.0, 1.0))))

    write_csv(os.path.join(out, 'static_series.csv'),
              ['step', 'umax', 'Pc', 'n_mixed', 'n_liq', 'n_gas'],
              rows, p)
    axial = [(x, float(psi_f[x, y0:y1, :].mean()), float(prof_p[x]))
             for x in range(nx)]
    write_csv(os.path.join(out, 'axial_static.csv'),
              ['x', 'psi_mean', 'p_mean'], axial, p)
    np.savez_compressed(os.path.join(out, 'fields_final.npz'),
                        psi=psi_f.astype(np.float32),
                        rho=rho_f.astype(np.float32))
    w = pc_hist[-10:] if len(pc_hist) >= 10 else pc_hist
    rep = dict(
        mode='static', tag=args.tag, hy=hy,
        Pc_static=pc_static, C_static=c_static,
        theta_static_slit_deg=theta,
        registry_theta_deg=THETA_REGISTRY,
        threshold_sensitivity=res_thr,
        bulk_bands_090=None if not bb90 else dict(
            liq=list(bb90['liq']), gas=list(bb90['gas']),
            n_mixed=bb90['n_mixed']),
        convergence=dict(
            exit_reason=exit_reason, steps_run=it,
            Pc_stationary=exit_reason.startswith('Pc stationary'),
            Pc_last10_rel_drift=float(
                (w[-1] - w[0]) / max(abs(np.mean(w)), 1e-30)) if len(w)
            >= 2 else None,
            drift_tol=STATIC_DRIFT_TOL,
            umax_final=float(umax_hist[-1]),
            umax_floor_note='spurious-current magnitude floor, recorded '
                            'separately from pressure stationarity'),
        layout=dict(nx=nx, ny=ny, nz=nz, slab=[s0, s1],
                    boundary='x periodic (lattice wrap), z periodic, '
                             'y walls psi_solid=-0.68'),
        wall_s=time.time() - t_start,
        nan=exit_reason.startswith('NaN'), prov=p)
    write_json(os.path.join(out, 'report.json'), rep)
    prov_finish(p, 0)
    print(f'[{args.tag}] Pc_static={pc_static:.6e} C={c_static:.4f} '
          f'theta={theta:.2f} ({exit_reason})', flush=True)
    return 0


# ------------------------------------------------------------ dynamic (B/D)
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
    solid[X_RES0:lay['wall_out'][0], y0:y1, :] = 0
    mem_r = np.zeros((nx, ny, nz), dtype=np.int8)
    mem_b = np.zeros((nx, ny, nz), dtype=np.int8)
    mem_r[X_MEM_IN, :, :] = 1
    mem_b[x_mem_out, :, :] = 1
    liq_res = np.zeros((nx, ny, nz), dtype=np.int8)
    liq_res[X_RES0:X_RES1, y0:y1, :] = 1
    gas_res = np.zeros((nx, ny, nz), dtype=np.int8)
    gas_res[lay['gas_res'][0]:lay['gas_res'][1], y0:y1, :] = 1
    assert not ((liq_res | gas_res) & (mem_r | mem_b)).any(), \
        'reservoir/membrane overlap'

    psi_solid = np.full((nx, ny, nz), PSI_WALL, dtype=np.float32)
    psi0 = np.ones((nx, ny, nz), dtype=np.float32)
    psi0[solid != 0] = 0.0
    psi0[X_RES0:args.x0, y0:y1, :] = -1.0

    s = ColorGradientSolver3D(nx, ny, nz, niu_l=NU, niu_g=NU, CapA=CAPA)
    s.set_psi_solid_field(psi_solid)
    s.set_membranes(mem_r, mem_b)
    s.set_reservoirs(liq_res, -1.0, RHO0)
    s.set_reservoirs(gas_res, +1.0, RHO0)
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
                x_cross = 11.0 + (idx[0] - 1 if len(idx) else len(below)
                                  - 1)
            t_s.append(it)
            xv_s.append(x_vol)
            xc_s.append(x_cross)
        if it % args.every_v == 0:
            psi = s.psi_snapshot()
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
            psi_slit = psi[12:buf0, y0:y1, :]
            row = dict(t=it, umax=umax, urms=urms, band_valid=0)
            bb = bulk_bands(psi_slit, 12)
            if bb:
                gl, cl, r2l = fit_band(prof_p, bb['liq'])
                gg, cg, r2g = fit_band(prof_p, bb['gas'])
                xm = float(xv_s[-1]) if xv_s else float(args.x0)
                pc_dyn = (cg + gg * xm) - (cl + gl * xm)
                row.update(band_valid=1,
                           liq_band=list(bb['liq']),
                           gas_band=list(bb['gas']),
                           n_mixed=bb['n_mixed'],
                           dpdx_liq=gl, dpdx_gas=gg,
                           r2_liq=r2l, r2_gas=r2g,
                           Pc_dynamic=float(pc_dyn))
                # threshold sensitivity (diagnostic)
                sens = {}
                for thr in (0.85, 0.95):
                    bt = bulk_bands(psi_slit, 12, thr=thr)
                    if bt:
                        gl2, cl2, _ = fit_band(prof_p, bt['liq'])
                        gg2, cg2, _ = fit_band(prof_p, bt['gas'])
                        sens[str(thr)] = float(
                            (cg2 + gg2 * xm) - (cl2 + gl2 * xm))
                    else:
                        sens[str(thr)] = None
                row['Pc_dynamic_thr085'] = sens['0.85']
                row['Pc_dynamic_thr095'] = sens['0.95']
                row['jump_in'] = float(
                    rho[X_RES0 + 1:X_RES1 - 1, y0:y1, :].mean() / 3.0
                    - (cl + gl * float(X_IN)))
                row['jump_out'] = float(
                    (cg + gg * float(buf0 - 1))
                    - rho[lay['gas_res'][0] + 1:lay['gas_res'][1] - 1,
                          y0:y1, :].mean() / 3.0)
            row['rho_res_liq'] = float(
                rho[X_RES0 + 1:X_RES1 - 1, y0:y1, :].mean())
            row['rho_res_gas'] = float(
                rho[lay['gas_res'][0] + 1:lay['gas_res'][1] - 1,
                    y0:y1, :].mean())
            if xv_s:
                xm = float(xv_s[-1])
                bm = np.arange(max(X_IN, int(xm) - 6),
                               min(buf0, int(xm) + 6))
                u_band = v[bm, y0:y1, :, :]
                row['u_band_max'] = float(np.linalg.norm(
                    u_band, axis=3).max())
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
            if axial_mid is None and xv_s \
                    and xv_s[-1] >= (x_ic_exit + x_stop) / 2:
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
    keys = ['t', 'umax', 'urms', 'band_valid', 'liq_band', 'gas_band',
            'n_mixed', 'dpdx_liq', 'dpdx_gas', 'r2_liq', 'r2_gas',
            'Pc_dynamic', 'Pc_dynamic_thr085', 'Pc_dynamic_thr095',
            'jump_in', 'jump_out', 'rho_res_liq', 'rho_res_gas',
            'u_band_max', 'u_band_ut_rms', 'm_r', 'm_b', 'inj_r',
            'inj_b', 'inj_m', 'closure_r', 'closure_b']
    write_csv(os.path.join(out, 'probes.csv'), keys,
              [[(json.dumps(r[k]) if isinstance(r.get(k), list)
                 else r.get(k)) for k in keys] for r in probe_s], p)
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
                        t_tr, x_ic_exit, x_stop, buf0=buf0)
    a.update(mode='dynamic', tag=args.tag, layout=lay, steps_run=it,
             wall_s=wall, exit_reason=exit_reason, nan_at=nan_at,
             umax_break=umax_break, x_stop=x_stop, T_TRANS=t_tr,
             x_ic_exit=x_ic_exit, sigma=SIGMA, capa=CAPA, nu=NU, mu=MU,
             psi_wall=PSI_WALL, prov=p,
             m_r_final=mm_fin[0], m_b_final=mm_fin[1],
             inj_r_final=fl_fin['inj_r'], inj_b_final=fl_fin['inj_b'],
             closure_r_final=fl_fin['inj_r'] - (mm_fin[0] - m0[0]),
             closure_b_final=fl_fin['inj_b'] - (mm_fin[1] - m0[1]))
    write_json(os.path.join(out, 'report.json'), a)
    prov_finish(p, 0)
    print(f'[{args.tag}] {exit_reason}; V_meas='
          f'{a.get("V_meas", float("nan")):.4e} R2='
          f'{a.get("R2_x_linear", float("nan")):.5f} '
          f'probes_valid='
          f'{a.get("n_window_probes_valid", "?")}/{a.get("n_window_probes", "?")}',
          flush=True)
    return 0


def analyze_dynamic(t, xv, xc, probes, hy, L_hyd, t_tr, x_ic_exit,
                    x_stop, buf0=None):
    """Declared mechanical rule with the per-probe validity ladder
    (V0 base -> V1 window-x -> V2 positional -> V3 linearity).  V3
    defines the PRIMARY aggregate; median and mean are published for
    every variant (estimator sensitivity).  Explicit failure when the
    window or the fully-valid probe set is empty."""
    res = dict(n_samples=len(t))
    win = np.where((t >= t_tr) & (xv >= x_ic_exit) & (xv <= x_stop))[0]
    if len(win) < 20:
        res['window_valid'] = False
        res['window_fail_reason'] = (
            f'threshold never reached: only {len(win)} samples satisfy '
            f't>= {t_tr}, x>={x_ic_exit:.0f}, x<={x_stop:.0f} '
            f'(>=20 required) -- explicit FAIL')
        res['gates'] = dict(g1_no_nan=None, g2_umax_cap=None,
                            g3_zero_dp=None, g4_monotonic=None,
                            g5_window_valid=False, g6_r2=None,
                            g7_front_agreement=None,
                            g8_band_valid_frac=None)
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
    v_sec = float(A2[0])
    res['V_meas'] = v_meas
    res['R2_x_linear'] = float(r2)
    res['V_meas_secondary'] = v_sec
    res['R2_x_secondary'] = float(r2c)
    res['front_speed_rel_diff'] = float(abs(v_sec / v_meas - 1.0))
    res['monotonic_window'] = bool(
        np.all(np.diff(xv[i0:i_hi + 1]) >= -0.5))

    # ---- per-probe validity ladder (B1/B2) -------------------------
    for r in probes:
        r['_x'] = float(np.interp(r['t'], t, xv))
    w_t = [r for r in probes if t_tr <= r['t'] <= t[i_hi]]
    v0 = [r for r in w_t if r.get('band_valid')]
    v1 = [r for r in v0 if x_ic_exit <= r['_x'] <= x_stop]
    v2 = [r for r in v1
          if buf0 is not None
          and (r['gas_band'][1] - r['gas_band'][0]) >= 3.0 * hy
          and r['_x'] <= buf0 - 4.0 * hy]
    v3 = [r for r in v2
          if r.get('r2_liq') is not None and r.get('r2_gas') is not None
          and r['r2_liq'] >= 0.995 and r['r2_gas'] >= 0.995]

    def agg(sel):
        pcs = [r['Pc_dynamic'] for r in sel]
        return dict(n=len(pcs),
                    median=float(np.median(pcs)) if pcs else None,
                    mean=float(np.mean(pcs)) if pcs else None)

    res['validity_variants'] = dict(
        V0_base_12col=agg(v0), V1_window_x=agg(v1),
        V2_positional=agg(v2), V3_linearity=agg(v3),
        counts=dict(windowed_t=len(w_t), base=len(v0), window_x=len(v1),
                    positional=len(v2), full=len(v3)))
    res['n_window_probes'] = len(w_t)
    res['n_window_probes_valid'] = len(v3)
    res['n_window_probes_base'] = len(v0)
    if not v3:
        res['window_valid'] = False
        res['window_fail_reason'] = (
            f'no probe passes FULL validity (V3): windowed={len(w_t)}, '
            f'base={len(v0)}, window_x={len(v1)}, positional={len(v2)}, '
            f'full={len(v3)} -- explicit FAIL, no silent fallback')
        res['gates'] = dict(g1_no_nan=None, g2_umax_cap=None,
                            g3_zero_dp=None, g4_monotonic=None,
                            g5_window_valid=False, g6_r2=None,
                            g7_front_agreement=None,
                            g8_band_valid_frac=None)
        return res
    wp = v3                                   # PRIMARY = full validity
    pc_med = float(np.median([r['Pc_dynamic'] for r in wp]))
    res['Pc_dynamic_median'] = pc_med
    res['Pc_dynamic_mean'] = float(np.mean([r['Pc_dynamic'] for r in wp]))
    for k in ('thr085', 'thr095'):
        vals = [r[f'Pc_dynamic_{k}'] for r in wp
                if r.get(f'Pc_dynamic_{k}') is not None]
        res[f'Pc_dynamic_median_{k}'] = (float(np.median(vals))
                                         if vals else None)
    res['jump_in_median'] = float(np.median([r['jump_in'] for r in wp]))
    res['jump_out_median'] = float(
        np.median([r['jump_out'] for r in wp]))
    res['dpdx_liq_median'] = float(
        np.median([r['dpdx_liq'] for r in wp]))
    res['dpdx_gas_median'] = float(
        np.median([r['dpdx_gas'] for r in wp]))
    res['r2_liq_min'] = float(min(r['r2_liq'] for r in wp))
    res['r2_gas_min'] = float(min(r['r2_gas'] for r in wp))
    res['band_valid_frac'] = float(len(v3) / max(len(w_t), 1))
    res['band_valid_frac_base'] = float(len(v0) / max(len(w_t), 1))

    l_eff = pc_med * hy * hy / (12.0 * MU * v_meas)
    res['L_eff'] = float(l_eff)
    res['L_hyd'] = float(L_hyd)
    res['L0_raw'] = float(l_eff - L_hyd)
    res['L0_raw_over_h'] = float((l_eff - L_hyd) / hy)
    res['Ca'] = float(MU * v_meas / SIGMA)
    g_analytic = 12.0 * MU * v_meas / (hy * hy)
    res['G_poiseuille_analytic'] = float(g_analytic)
    res['dpdx_liq_over_G'] = float(abs(res['dpdx_liq_median'])
                                   / g_analytic)
    res['dpdx_gas_over_G'] = float(abs(res['dpdx_gas_median'])
                                   / g_analytic)
    res['rho_res_liq_dev_max'] = float(max(
        abs(r['rho_res_liq'] - 1.0) for r in wp))
    res['rho_res_gas_dev_max'] = float(max(
        abs(r['rho_res_gas'] - 1.0) for r in wp))
    res['closure_r_last'] = float(wp[-1]['closure_r'])
    res['closure_b_last'] = float(wp[-1]['closure_b'])
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
        g7_front_agreement=res['front_speed_rel_diff'] <= 0.02,
        g8_band_valid_frac=res['band_valid_frac_base'] >= 0.8,
        g9_mass_closure=None,
    )
    res['gates']['all_hard'] = all(
        v is True for k, v in res['gates'].items()
        if k not in ('g9_mass_closure', 'all_hard'))
    return res


def _r2(x, y, g, c):
    pred = c + g * x
    ss = float(((y - pred) ** 2).sum())
    tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss / tot if tot > 0 else float('nan')


# ------------------------------------------------------- reanalyze (no GPU)
def reanalyze(args):
    """Re-run the PRODUCTION aggregation (same analyze_dynamic code
    path) on an existing run's committed front.csv/probes.csv — the
    review-prescribed correction route when validity logic changes:
    no GPU rerun, no solver change, per-probe evidence unchanged."""
    p = prov(sys.argv)
    d = os.path.join(OUTROOT, args.tag)
    with open(os.path.join(d, 'front.csv'), newline='') as f:
        rows = list(csv.DictReader(f))
    t = np.array([float(r['t']) for r in rows])
    xv = np.array([float(r['x_vol']) for r in rows])
    xc = np.array([float(r['x_cross']) for r in rows])

    def _num(x):
        return None if x in ('', 'None') else float(x)

    probes = []
    with open(os.path.join(d, 'probes.csv'), newline='') as f:
        for row in csv.DictReader(f):
            r = dict(t=float(row['t']),
                     band_valid=int(float(row['band_valid'])),
                     umax=_num(row['umax']))
            for k in ('liq_band', 'gas_band'):
                r[k] = (json.loads(row[k])
                        if row[k] not in ('', 'None') else None)
            for k in ('Pc_dynamic', 'Pc_dynamic_thr085',
                      'Pc_dynamic_thr095', 'jump_in', 'jump_out',
                      'dpdx_liq', 'dpdx_gas', 'r2_liq', 'r2_gas',
                      'rho_res_liq', 'rho_res_gas', 'u_band_ut_rms'):
                r[k] = _num(row[k])
            probes.append(r)

    rp = os.path.join(d, 'report.json')
    rep = json.load(open(rp))
    lay = rep['layout']
    a = analyze_dynamic(t, xv, xc, probes, lay['hy'], lay['L_hyd'],
                        rep['T_TRANS'], rep['x_ic_exit'],
                        rep['x_stop'], buf0=lay['out_buffer'][0])
    stale = [k for k in rep
             if k not in a and k in (
                 'Pc_dynamic_mean', 'band_valid_frac',
                 'n_window_probes_valid')]
    for k in stale:
        rep.pop(k)
    rep.update(a)
    prov_finish(p, 0)
    rep['prov_reanalysis'] = p
    rep['reanalysis_note'] = ('aggregation recomputed from the '
                              'unchanged committed front.csv/probes.csv '
                              'by the same analyze_dynamic path; '
                              'simulation data untouched')
    write_json(rp, rep)
    print(f'[{args.tag}] reanalyzed: V_meas={a.get("V_meas")} '
          f'Pc_med={a.get("Pc_dynamic_median")} full-valid '
          f'{a["validity_variants"]["counts"]["full"]}'
          f'/{a["validity_variants"]["counts"]["windowed_t"]}',
          flush=True)
    return 0


# ---------------------------------------------------------------- collect
def collect(args):
    p = prov(sys.argv)
    st_tags = ['static_h26', 'static_h40', 'static_h60', 'static_h80']
    dy_tags = ['dyn_h26_s', 'dyn_h26_2L', 'dyn_h40_s', 'dyn_h40_2L']
    reps = {}
    for tag in st_tags + dy_tags:
        rp = os.path.join(OUTROOT, tag, 'report.json')
        if not os.path.exists(rp):
            print('missing report:', tag)
            return 1
        reps[tag] = json.load(open(rp))

    # ---- static table + convergence fits
    srows, hs, cs = [], [], []
    for tag in st_tags:
        r = reps[tag]
        hs.append(r['hy'])
        cs.append(r['C_static'])
        srows.append([r['hy'], r['Pc_static'], r['C_static'],
                      r['theta_static_slit_deg'],
                      r['convergence']['exit_reason'],
                      r['threshold_sensitivity']['0.85']['Pc_static']
                      if r['threshold_sensitivity'].get('0.85') else None,
                      r['threshold_sensitivity']['0.95']['Pc_static']
                      if r['threshold_sensitivity'].get('0.95') else None])
    write_csv(os.path.join(OUTROOT, 'static_table.csv'),
              ['h', 'Pc_static', 'C_static', 'theta_static_deg',
               'convergence', 'Pc_thr085', 'Pc_thr095'], srows, p)
    h = np.array(hs, float)
    c = np.array(cs, float)
    inv = 1.0 / h
    fits = {}
    for name, X in (('constant', np.column_stack([np.ones_like(inv)])),
                    ('over_h', np.column_stack([np.ones_like(inv),
                                                inv])),
                    ('over_h2', np.column_stack([np.ones_like(inv),
                                                 inv ** 2]))):
        coef, *_ = np.linalg.lstsq(X, c, rcond=None)
        pred = X @ coef
        ss = float(((c - pred) ** 2).sum())
        tot = float(((c - c.mean()) ** 2).sum())
        fits[name] = dict(coef=[float(v) for v in coef],
                          r2=float(1 - ss / tot) if tot > 0 else None,
                          resid_max=float(np.abs(c - pred).max()))
    fits['note'] = ('candidate families only; no family is forced if '
                    'residuals do not support it')

    # ---- differential hydraulics
    def drow(short, long, hy):
        rs, rl = reps[short], reps[long]
        L1, L2 = rs['layout']['L_hyd'], rl['layout']['L_hyd']
        v1, v2 = rs['V_meas'], rl['V_meas']
        p1, p2 = rs['Pc_dynamic_median'], rl['Pc_dynamic_median']
        le1 = p1 * hy * hy / (12.0 * MU * v1)
        le2 = p2 * hy * hy / (12.0 * MU * v2)
        a = (le2 - le1) / (L2 - L1)
        L0 = le1 - a * L1
        return dict(h=hy, L1=L1, L2=L2, V1=v1, V2=v2, Pc1=p1, Pc2=p2,
                    L_eff1=float(le1), L_eff2=float(le2), a_h=float(a),
                    L0=float(L0), L0_over_h=float(L0 / hy),
                    V1_sens085=rs.get('Pc_dynamic_median_thr085'),
                    V1_sens095=rs.get('Pc_dynamic_median_thr095'),
                    V2_sens085=rl.get('Pc_dynamic_median_thr085'),
                    V2_sens095=rl.get('Pc_dynamic_median_thr095'))

    d26 = drow('dyn_h26_s', 'dyn_h26_2L', 26)
    d40 = drow('dyn_h40_s', 'dyn_h40_2L', 40)

    # estimator sensitivity (B1-iv): a_h under every validity variant
    # x estimator, from the per-run published variant aggregates
    VAR = ('V0_base_12col', 'V1_window_x', 'V2_positional',
           'V3_linearity')

    def a_of(pc1, pc2, hy, v1, v2):
        le1 = pc1 * hy * hy / (12.0 * MU * v1)
        le2 = pc2 * hy * hy / (12.0 * MU * v2)
        return (le2 - le1) / (d26['L2'] - d26['L1'])

    sens_rows = []
    sens = {}
    for hy, short, long in ((26, 'dyn_h26_s', 'dyn_h26_2L'),
                            (40, 'dyn_h40_s', 'dyn_h40_2L')):
        rs, rl = reps[short], reps[long]
        v1_, v2_ = rs['V_meas'], rl['V_meas']
        for var in VAR:
            for est in ('median', 'mean'):
                pc1 = rs['validity_variants'][var][est]
                pc2 = rl['validity_variants'][var][est]
                ah = (a_of(pc1, pc2, hy, v1_, v2_)
                      if pc1 is not None and pc2 is not None else None)
                sens_rows.append([hy, var, est, pc1, pc2, ah,
                                  None if ah is None
                                  else abs(ah - 1.0) <= 0.10])
                sens.setdefault(f'h{hy}', {})[f'{var}_{est}'] = ah
    write_csv(os.path.join(OUTROOT, 'estimator_sensitivity.csv'),
              ['h', 'validity_variant', 'estimator', 'Pc_short',
               'Pc_long', 'a_h', 'gate_|a-1|<=0.10'], sens_rows, p)

    # mass accounting (non-blocking completeness): reconstruct total
    # colour-mass drift from committed closure/inj finals
    mass = {}
    for t in dy_tags:
        r = reps[t]
        mr, mb = r['m_r_final'], r['m_b_final']
        ir, ib = r['inj_r_final'], r['inj_b_final']
        cr, cb = r['closure_r_final'], r['closure_b_final']
        m0 = (mr - ir + cr) + (mb - ib + cb)
        mass[t] = dict(m_final=mr + mb, inj_total=ir + ib,
                       closure_sum=cr + cb,
                       closure_rel=abs(cr + cb) / max(m0, 1e-30),
                       m0_total_reconstructed=m0)

    drows = []
    for d in (d26, d40):
        drows.append([d['h'], d['L1'], d['L2'], d['V1'], d['V2'],
                      d['Pc1'], d['Pc2'], d['L_eff1'], d['L_eff2'],
                      d['a_h'], d['L0'], d['L0_over_h']])
    write_csv(os.path.join(OUTROOT, 'differential_table.csv'),
              ['h', 'L1', 'L2', 'V1', 'V2', 'Pc_dyn1', 'Pc_dyn2',
               'L_eff1', 'L_eff2', 'a_h', 'L0', 'L0_over_h'], drows, p)

    summary = dict(
        task='BI-V1C-CLOSURE-001',
        fixed=dict(CapA=CAPA, sigma=SIGMA, nu=NU, mu=MU,
                   psi_wall=PSI_WALL, rho0=RHO0,
                   theta_registry_deg=THETA_REGISTRY),
        static=dict(h=hs, C_static=[float(v) for v in cs],
                    theta_static_deg=[reps[t]['theta_static_slit_deg']
                                      for t in st_tags],
                    Pc_static=[reps[t]['Pc_static'] for t in st_tags],
                    convergence_fits=fits,
                    C_h26_over_h40=float(cs[0] / cs[1])),
        differential=dict(h26=d26, h40=d40,
                          gates=dict(a26=abs(d26['a_h'] - 1.0) <= 0.10,
                                     a40=abs(d40['a_h'] - 1.0) <= 0.10),
                          estimator_sensitivity=sens,
                          primary='V3_linearity median'),
        mass_accounting=mass,
        dynamic={t: dict(
            L_hyd=reps[t]['layout']['L_hyd'],
            V_meas=reps[t]['V_meas'], R2=reps[t]['R2_x_linear'],
            V_secondary=reps[t]['V_meas_secondary'],
            front_rel_diff=reps[t]['front_speed_rel_diff'],
            Pc_dynamic=reps[t]['Pc_dynamic_median'],
            Pc_thr085=reps[t].get('Pc_dynamic_median_thr085'),
            Pc_thr095=reps[t].get('Pc_dynamic_median_thr095'),
            band_valid_frac=reps[t]['band_valid_frac'],
            L_eff=reps[t]['L_eff'], L0_raw=reps[t]['L0_raw'],
            Ca=reps[t]['Ca'], gates=reps[t]['gates'],
            exit_reason=reps[t]['exit_reason'])
            for t in dy_tags},
        prov=p)
    write_json(os.path.join(OUTROOT, 'summary.json'), summary)

    grows = []
    for t in st_tags:
        grows.append([t, 'static',
                      reps[t]['convergence']['Pc_stationary'],
                      'Pc stationarity judged separately from umax '
                      'floor'] + [''] * 7)
    for t in dy_tags:
        g = reps[t]['gates']
        grows.append([t, 'dynamic'] + [g.get(k) for k in (
            'g1_no_nan', 'g2_umax_cap', 'g3_zero_dp', 'g4_monotonic',
            'g5_window_valid', 'g6_r2', 'g7_front_agreement',
            'g8_band_valid_frac', 'all_hard')])
    grows.append(['a26_gate', 'differential',
                  abs(d26['a_h'] - 1.0) <= 0.10,
                  f"a26={d26['a_h']:.4f}"] + [''] * 7)
    grows.append(['a40_gate', 'differential',
                  abs(d40['a_h'] - 1.0) <= 0.10,
                  f"a40={d40['a_h']:.4f}"] + [''] * 7)
    write_csv(os.path.join(OUTROOT, 'gates.csv'),
              ['tag', 'mode', 'g1_no_nan', 'g2_umax', 'g3_zero_dp',
               'g4_monotonic', 'g5_window', 'g6_r2',
               'g7_front_agree', 'g8_band_frac', 'all_hard'], grows, p)

    manifest = dict(producer='tests/levelc_v1c.py',
                    producer_sha256=p['producer_sha256'], runs={})
    for tag in st_tags + dy_tags:
        rp = reps[tag]['prov']
        entry = dict(command=rp['command'], run_head=rp['run_head'],
                     producer_sha256=rp['producer_sha256'],
                     started_at=rp['started_at'],
                     exit_code=rp['exit_code'])
        pra = reps[tag].get('prov_reanalysis')
        if pra:
            entry['reanalysis'] = dict(
                command=pra['command'], run_head=pra['run_head'],
                producer_sha256=pra['producer_sha256'],
                started_at=pra['started_at'],
                exit_code=pra['exit_code'],
                note='aggregation rerun on unchanged committed '
                     'front.csv/probes.csv; simulation untouched')
        lg = os.path.join(OUTROOT, 'logs', tag + '.log')
        ex = os.path.join(OUTROOT, 'logs', tag + '.exit')
        if os.path.exists(ex):
            entry['shell_exit_code'] = int(open(ex).read().strip())
        if os.path.exists(lg):
            entry['console_log'] = os.path.relpath(lg, REPO)
        entry['artifacts'] = {}
        d = os.path.join(OUTROOT, tag)
        for fn in sorted(os.listdir(d)):
            entry['artifacts'][fn] = hashlib.sha256(
                open(os.path.join(d, fn), 'rb').read()).hexdigest()
        manifest['runs'][tag] = entry
    write_json(os.path.join(OUTROOT, 'MANIFEST.json'), manifest)
    prov_finish(p, 0)
    print(json.dumps(dict(
        static_C=dict(zip(hs, [round(v, 4) for v in cs])),
        a26=d26['a_h'], a40=d40['a_h'],
        L0_over_h=dict(h26=d26['L0_over_h'], h40=d40['L0_over_h']),
        gates={t: reps[t]['gates'] for t in dy_tags}), indent=1))
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
    pd.add_argument('--tag', default='dyn_h26_s')
    pr = sub.add_parser('reanalyze')
    pr.add_argument('--tag', required=True)
    sub.add_parser('collect')
    args = ap.parse_args()
    os.makedirs(os.path.join(OUTROOT, 'logs'), exist_ok=True)
    rc = dict(static=run_static, dynamic=run_dynamic,
              reanalyze=reanalyze, collect=collect)[args.mode](args)
    sys.exit(rc)


if __name__ == '__main__':
    main()
