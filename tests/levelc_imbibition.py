"""Level C — V1 single-front spontaneous capillary filling (Lucas-Washburn).

Stage BI-VALIDATION-001 / V1 ("dynamic wetting").  One wetting phase
(psi = -1, "electrolyte") spontaneously invades a straight, resolved slit
that initially contains the non-wetting phase (psi = +1, "gas").  There is
NO externally imposed pressure difference: the liquid and gas reservoirs
are both pinned at rho = 1 (delta = 0) through this repo's standard
rho-prescribed / psi-Dirichlet reservoir + semi-permeable-membrane
infrastructure, i.e. an open system with two equal-pressure baths.  No
solver code is touched.

CONFIGURATION
-------------
x : 0,1 solid | [2,12) liquid reservoir (psi=-1, rho=1) | x=11 inlet
    membrane (mem_r=1: blocks gas, passes liquid) | [12, XOUT) slit |
    XOUT outlet membrane (mem_b=1: blocks liquid, passes gas) |
    gas reservoir (psi=+1, rho=1) | solid far wall
y : 0 solid | [1, 27) slit, h_y = 26 lu, walls psi_solid = -0.68
    (theta_liq = 30 deg) | 27 solid
z : periodic, 6 layers -- the meniscus is therefore exactly two
    dimensional (no z-curvature, no side walls), so
        Pc = 2*sigma*cos(theta)/h_y = sigma*cos(theta)/b,  b = h_y/2
    holds without any duct/aspect-ratio ambiguity.

DECLARED ANALYTIC RELATION (fixed before any run; not fitted)
-------------------------------------------------------------
This solver runs both phases at MATCHED viscosity (nu = 0.1, unit density
ratio) -- an episode-level fixed assumption.  For a meniscus inside a
uniform channel whose two ends are equal-pressure baths, the displaced
phase carries a viscous load and the two columns are in series:

    Pc = 12*mu*(l_liq + l_gas)*xdot/h_y^2 ,   l_liq + l_gas = L_tot = const

so the correct Lucas-Washburn relation *for this configuration* is the
constant-velocity (generalized Washburn) law

    x(t) = x0 + V*t ,        V = Pc*h_y^2/(12*mu*L_tot)
    equivalently  d(x^2)/dt = 2*V*x   (NOT constant)

L_tot = the distance between the two membrane planes.  The naive
gas-negligible Washburn form (x^2 = K*t, K = 2*Pc*b^2/(3*mu)) is reported
as a diagnostic; it is the wrong relation for this configuration and the
data are expected to show it (a constant-velocity front gives
K_fit/K_naive = (x1+x2)/(2*L_tot) over a window [x1,x2], and a linear fit
to x^2 vs t has R^2 < 0.98 once the front advances by more than ~3.5x).
Both forms are therefore fitted and both slope comparisons are reported;
the chosen (configuration-appropriate) relation is the constant-velocity
one.

DECLARED FIT-WINDOW RULE (mechanical, fixed before any run)
-----------------------------------------------------------
The primary front series x(t) is the volumetric front (see extract_front).
  trajectory := all samples with x >= x0 + 5*h_y   (out of the IC region)
  window     := samples of the trajectory with t >= T_TRANSIENT, where
                T_TRANSIENT = 5000 steps is declared a priori as ~3x the
                duct's viscous diffusion time h_y^2/(4*nu) ~ 1690 steps,
                and with x <= x_stop (a clearance from the outlet
                membrane).
No window choice depends on the fit result; the rule is applied
mechanically and the alternative (non-discriminating) narrow windows are
reported only as diagnostics.

GATES (V1 stage contract, provisional v0.1 engineering gates)
-------------------------------------------------------------
 1 no NaN/Inf, u_max <= 0.12 (drivers' operational stability cap)
 2 zero imposed pressure difference (both reservoir densities 1 +- 1e-3)
 3 monotonic front advance after initialization
 4 window >= 40% of the usable pre-boundary-interaction trajectory
 5 on the window, x^2 vs t has R^2 >= 0.98
 6 measured slope vs the chosen analytic relation within 10%
 7 colour-mass accounting closes against the pinned-region injection
   counters, no systematic drift
 8 same case at a larger resolved channel size: normalized slope reported

Run:  python tests/levelc_imbibition.py --tag v1_h26
      python tests/levelc_imbibition.py --hy 40 --tag v1_h40
Outputs -> tests_output/levelc_imbibition/<tag>/
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

OUTROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'tests_output', 'levelc_imbibition')

CAPA = 0.06
SIGMA = 1.012 * CAPA          # repo calibration sigma = 1.012 * CapA
NU = 0.1                      # matched viscosity, both phases
RHO0 = 1.0
UMAX_CAP = 0.12               # operational cap used by the drivers
PSI_WALL = -0.68              # theta_liq = 30 deg (registry)
THETA_WALL = 30.0
X_RES0, X_RES1 = 2, 12        # liquid reservoir slab [2, 12)
X_MEM_IN = X_RES1 - 1         # inlet membrane plane (x = 11)
X_IN = X_RES1                 # first slit column (x = 12)
T_TRANSIENT = 5000            # declared a priori (see header)


def build(nx, hy, x0, xout, nz=6):
    """Geometry, membranes, reservoirs, psi_solid field and initial psi."""
    ny = hy + 2                     # 1 solid + hy slit + 1 solid
    y0, y1 = 1, 1 + hy
    x_gas0, x_gas1 = xout + 1, nx - 2

    solid = np.ones((nx, ny, nz), dtype=np.int8)   # sealed by default
    solid[X_IN:xout + 1, y0:y1, :] = 0             # slit + outlet plane
    solid[X_RES0:X_RES1, y0:y1, :] = 0             # liquid reservoir
    solid[x_gas0:x_gas1, y0:y1, :] = 0             # gas reservoir

    mem_r = np.zeros((nx, ny, nz), dtype=np.int8)
    mem_b = np.zeros((nx, ny, nz), dtype=np.int8)
    mem_r[X_MEM_IN, :, :] = 1        # inlet : blocks gas  (liquid passes)
    mem_b[xout, :, :] = 1            # outlet: blocks liquid (gas passes)

    liq_res = np.zeros((nx, ny, nz), dtype=np.int8)
    liq_res[X_RES0:X_RES1, y0:y1, :] = 1
    gas_res = np.zeros((nx, ny, nz), dtype=np.int8)
    gas_res[x_gas0:x_gas1, y0:y1, :] = 1

    psi_solid = np.full((nx, ny, nz), PSI_WALL, dtype=np.float32)

    psi0 = np.full((nx, ny, nz), 1.0, dtype=np.float32)     # non-wetting
    psi0[solid != 0] = 0.0
    psi0[X_IN:x0, y0:y1, :] = -1.0                          # wetting slug
    psi0[X_RES0:X_RES1, y0:y1, :] = -1.0                    # reservoir

    return dict(nx=nx, ny=ny, nz=nz, hy=hy, y0=y0, y1=y1, x0=x0,
                xout=xout, solid=solid, mem_r=mem_r, mem_b=mem_b,
                liq_res=liq_res, gas_res=gas_res, psi_solid=psi_solid,
                psi0=psi0, lt=float(xout - X_MEM_IN))


def _cross(column):
    """Last index of the contiguous liquid (column mean < 0) run from 0."""
    below = column < 0.0
    if not below[0]:
        return -1
    nz = np.where(~below)[0]
    return int(nz[0] - 1) if len(nz) else len(below) - 1


def extract_front(psi, g, layers=False):
    """Front-position definitions (recorded verbatim in the report).

    slit(x) = psi[x, y0:y1, :]; A = h_y*nz is the slit cross-section.
    Two independent definitions are always both recorded:

    x_vol   (primary)  : x_in + sum_x sum_yz (1 - psi)/2 / A
        -- the swept length, i.e. the liquid volume in the slit divided by
        the cross-section; an integral, hence robust against the
        interface's diffuseness (~2.2 lu) and against local roughness.
    x_cross (secondary): last x of the contiguous run from x_in along which
        the column mean psi(x) < 0.  The two differ by (approximately) a
        constant offset, so fitted slopes are insensitive to the choice.

    layers=True also returns xf_y, the y-layer-resolved front position
    (meniscus-shape / contact-angle proxy diagnostic).
    """
    y0, y1 = g['y0'], g['y1']
    slit = psi[g['x0q']:g['x1q'], y0:y1, :]
    liq = (1.0 - slit) * 0.5
    x_vol = g['x0q'] + float(liq.sum()) / (liq.shape[1] * liq.shape[2])
    x_cross = float(g['x0q'] + _cross(slit.mean(axis=(1, 2))))
    if not layers:
        return x_vol, x_cross
    xf_y = np.array([g['x0q'] + _cross(slit[:, j, :].mean(axis=1))
                     for j in range(slit.shape[1])], dtype=float)
    return x_vol, x_cross, xf_y


def run(args):
    g = build(args.nx, args.hy, args.x0, args.xout)
    nx, ny, nz = g['nx'], g['ny'], g['nz']
    y0, y1 = g['y0'], g['y1']
    xout = g['xout']
    g['x0q'], g['x1q'] = X_IN, xout
    b = g['hy'] / 2.0
    L = g['lt']

    pc = SIGMA * np.cos(np.radians(THETA_WALL)) / b
    v_pred = pc * g['hy'] ** 2 / (12.0 * NU * L)     # chosen relation
    k_naive = 2.0 * pc * b * b / (3.0 * NU)          # gas-negligible form

    s = ColorGradientSolver3D(nx, ny, nz, niu_l=NU, niu_g=NU, CapA=CAPA)
    s.set_psi_solid_field(g['psi_solid'])
    s.set_membranes(g['mem_r'], g['mem_b'])
    s.set_reservoirs(g['liq_res'], -1.0, RHO0)
    s.set_reservoirs(g['gas_res'], 1.0, RHO0)
    s.init(g['psi0'], g['solid'])

    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)
    print(f'[{args.tag}] nx={nx} ny={ny} nz={nz} h_y={g["hy"]} b={b:.1f} '
          f'x0={args.x0} xout={xout} L_tot={L:.1f} steps={args.steps}',
          flush=True)
    print(f'[{args.tag}] DECLARED: Pc={pc:.6e}  V_pred={v_pred:.6e} '
          f'K_naive={k_naive:.4f}  (x<=x_stop={args.x_stop})', flush=True)

    t_s, xv_s, xc_s = [], [], []
    rho_liq_s, rho_gas_s, p_liq_s, p_gas_s, pc_s = [], [], [], [], []
    m_r_s, m_b_s, inj_r_s, inj_b_s = [], [], [], []
    umax_s, urms_s = [], []
    xf_y_last = None
    nan_at, umax_break = None, None
    m0 = s.color_masses()
    t0 = time.time()
    it = 0

    for it in range(1, args.steps + 1):
        s.step()
        if it % args.every:
            continue
        psi = s.psi_snapshot()
        if not np.isfinite(psi).all():
            nan_at = it
            print(f'[{args.tag}] NaN/Inf at step {it}', flush=True)
            break
        x_vol, x_cross = extract_front(psi, g)
        t_s.append(it)
        xv_s.append(x_vol)
        xc_s.append(x_cross)
        if it % (args.every * 10) == 0:
            xf_y_last = extract_front(psi, g, layers=True)[2]

        if it % args.every_v == 0 or it == args.every:
            rho, v = s.macro_snapshot()
            fluid = (g['solid'] == 0)
            vm = np.linalg.norm(v, axis=3)
            umax = float(vm[fluid].max())
            urms = float(np.sqrt((vm[fluid] ** 2).mean()))
            umax_s.append((it, umax))
            urms_s.append((it, urms))
            if umax > UMAX_CAP and umax_break is None:
                umax_break = it
                print(f'[{args.tag}] u_max={umax:.4f} > cap {UMAX_CAP} at '
                      f'step {it}', flush=True)
            sl = rho[:, y0:y1, :]
            rho_liq_s.append(float(rho[X_RES0:X_RES1, y0:y1, :].mean()))
            rho_gas_s.append(float(rho[xout + 1:nx - 2, y0:y1, :].mean()))
            xc = int(min(max(x_cross, X_IN + 10), xout - 12))
            p_liq = float(sl[xc - 9:xc - 3].mean()) / 3.0
            p_gas = float(sl[xc + 3:xc + 9].mean()) / 3.0
            p_liq_s.append(p_liq)
            p_gas_s.append(p_gas)
            pc_s.append(p_gas - p_liq)
            mm = s.color_masses()
            m_r_s.append(mm[0])
            m_b_s.append(mm[1])
            fl = s.reservoir_fluxes()
            inj_r_s.append(fl['inj_r'])
            inj_b_s.append(fl['inj_b'])

        if it % (args.every * 20) == 0:
            el = time.time() - t0
            print(f'[{args.tag}] {it:6d}/{args.steps}  x_vol={x_vol:7.2f} '
                  f'x_cross={x_cross:7.2f}  ({el:5.0f}s, {it/el:7.1f} '
                  f'steps/s)', flush=True)
        if it >= args.steps_min and x_vol >= args.x_stop:
            print(f'[{args.tag}] front reached x_stop={args.x_stop} at step '
                  f'{it}', flush=True)
            break

    wall = time.time() - t0
    pm = s.psi_snapshot()
    rho_f, v_f = s.macro_snapshot()
    mm_fin = s.color_masses()
    fl_fin = s.reservoir_fluxes()
    np.savez_compressed(
        os.path.join(out, 'series.npz'),
        t=np.array(t_s), x_vol=np.array(xv_s), x_cross=np.array(xc_s),
        rho_liq=np.array(rho_liq_s), rho_gas=np.array(rho_gas_s),
        p_liq=np.array(p_liq_s), p_gas=np.array(p_gas_s),
        pc=np.array(pc_s), m_r=np.array(m_r_s), m_b=np.array(m_b_s),
        inj_r=np.array(inj_r_s), inj_b=np.array(inj_b_s),
        umax=np.array(umax_s), urms=np.array(urms_s), xf_y=xf_y_last,
        t_v=np.array([i for i, _ in umax_s], dtype=float),
        psi_final=pm.astype(np.float32))
    a = analyze(np.array(t_s, float), np.array(xv_s, float), b, L, v_pred,
                k_naive, args)
    a.update(
        tag=args.tag, nx=nx, ny=ny, nz=nz, hy=g['hy'], hz_periodic=True,
        b=b, x0=args.x0, xout=xout, L_tot=L, steps_run=it, wall_s=wall,
        sigma=SIGMA, capa=CAPA, nu=NU, psi_wall=PSI_WALL,
        theta_wall=THETA_WALL, pc_nominal=pc, pc_measured_last=(
            float(pc_s[-1]) if pc_s else None),
        v_pred=v_pred, k_naive=k_naive, t_transient=T_TRANSIENT,
        nan_at=nan_at, umax_break=umax_break,
        umax_peak=float(max([u for _, u in umax_s], default=float('nan'))),
        urms_last=float(urms_s[-1][1]) if urms_s else None,
        rho_liq_mean=float(np.mean(rho_liq_s)) if rho_liq_s else None,
        rho_gas_mean=float(np.mean(rho_gas_s)) if rho_gas_s else None,
        m_r_final=mm_fin[0], m_b_final=mm_fin[1],
        inj_r_final=fl_fin['inj_r'], inj_b_final=fl_fin['inj_b'],
        inj_m_final=fl_fin['inj_m'],
        inj_r_plus_dMr=fl_fin['inj_r'] - (mm_fin[0] - m0[0]),
        inj_b_plus_dMb=fl_fin['inj_b'] - (mm_fin[1] - m0[1]))
    if xf_y_last is not None:
        a['xf_y'] = [float(v) for v in xf_y_last]
        a['sag_y_wall_minus_centre'] = float(xf_y_last[0]
                                             - xf_y_last[len(xf_y_last) // 2])
    with open(os.path.join(out, 'report.json'), 'w') as f:
        json.dump(a, f, indent=1)

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        t = np.array(t_s, float)
        xv = np.array(xv_s, float)
        w = a.get('window_idx') or [0, len(t) - 1]
        i0, i1 = w
        fig, axs = plt.subplots(2, 2, figsize=(11, 8))
        axs[0, 0].plot(t, xv, '.', ms=2, label='x_vol')
        axs[0, 0].plot(t, xc_s, '-', lw=0.7, label='x_cross')
        fl = a['fit_x_linear']
        axs[0, 0].plot(t[i0:i1 + 1], fl['V'] * t[i0:i1 + 1] + fl['c'], 'r-',
                       lw=1, label='x = x0 + V t (chosen relation)')
        axs[0, 0].set_xlabel('step'); axs[0, 0].set_ylabel('front x (lu)')
        axs[0, 0].legend(); axs[0, 0].set_title('front position')
        axs[0, 1].plot(t, xv ** 2, '.', ms=2, label='x^2 data')
        f2 = a['fit_x2']
        axs[0, 1].plot(t[i0:i1 + 1], f2['K'] * t[i0:i1 + 1] + f2['c'], 'r-',
                       lw=1, label=f"R2={f2['r2']:.4f}")
        axs[0, 1].set_xlabel('step'); axs[0, 1].set_ylabel('x^2 (lu^2)')
        axs[0, 1].legend(); axs[0, 1].set_title('naive Washburn form')
        um = np.array(umax_s)
        if len(um):
            axs[1, 0].plot(um[:, 0], um[:, 1], '-')
            axs[1, 0].axhline(UMAX_CAP, color='r', ls='--')
        axs[1, 0].set_xlabel('step'); axs[1, 0].set_ylabel('u_max')
        axs[1, 0].set_title('kinetic diagnostic')
        axs[1, 1].imshow(pm[:, :, nz // 2].T, origin='lower', cmap='RdBu',
                         vmin=-1, vmax=1, aspect='auto')
        axs[1, 1].set_title('final psi (mid z)')
        plt.tight_layout()
        plt.savefig(os.path.join(out, 'levelc.png'), dpi=130)
    except Exception as e:                                   # pragma: no cover
        print('figure failed:', e, flush=True)

    print(f'[{args.tag}] done in {wall:.0f}s ({it} steps). '
          f'x_vol {xv_s[0]:.1f} -> {xv_s[-1]:.1f}', flush=True)
    print(json.dumps({k: v for k, v in a.items()
                      if k.startswith(('gate', 'slope', 'window', 'fit_',
                                       'V_'))}, indent=1), flush=True)
    return a


def _linfit(t, y, i0, i1):
    A = np.polyfit(t[i0:i1 + 1], y[i0:i1 + 1], 1)
    pred = np.polyval(A, t[i0:i1 + 1])
    ss = ((y[i0:i1 + 1] - pred) ** 2).sum()
    tot = ((y[i0:i1 + 1] - y[i0:i1 + 1].mean()) ** 2).sum()
    return float(A[0]), float(A[1]), float(1.0 - ss / tot)


def analyze(t, x, b, L, v_pred, k_naive, args):
    n = len(t)
    res = dict(n_samples=n)
    if n < 40:
        res['error'] = 'too few samples'
        return res
    u = np.gradient(x, t)
    x_lo = args.x0 + 5.0 * (2 * b)
    i_lo = int(np.argmax(x >= x_lo))
    i_hi = n - 1
    i0 = int(np.argmax(t >= T_TRANSIENT))
    i0 = max(i0, i_lo)
    if i0 >= i_hi - 10:
        i0 = i_lo
        res['window_note'] = 'T_TRANSIENT beyond trajectory; using x_lo cut'
    res['trajectory_idx'] = [i_lo, i_hi]
    res['window_idx'] = [i0, i_hi]
    res['gate3_monotonic'] = bool(np.all(np.diff(x[i_lo:]) >= -0.5))
    res['gate4_window_frac'] = float((i_hi - i0) / max(i_hi - i_lo, 1))

    # chosen relation: x = x0 + V t
    v_fit, c_lin, r2_lin = _linfit(t, x, i0, i_hi)
    res['fit_x_linear'] = dict(V=v_fit, c=c_lin, r2=r2_lin)
    res['V_fit'] = v_fit
    res['V_pred'] = v_pred
    res['gate6_rel_chosen'] = float(v_fit / v_pred - 1.0)

    # naive L-W form: x^2 = K t + c
    k_fit, c_x2, r2_x2 = _linfit(t, x ** 2, i0, i_hi)
    res['fit_x2'] = dict(K=k_fit, c=c_x2, r2=r2_x2)
    res['gate5_r2'] = r2_x2
    res['slope_x2_fit'] = k_fit
    res['slope_x2_pred_chosen'] = 2.0 * v_pred * float(np.mean(x[i0:i_hi + 1]))
    res['slope_x2_pred_naive'] = k_naive
    res['gate6_rel_naive'] = float(k_fit / k_naive - 1.0)
    res['gate6_rel_chosen_form'] = float(
        k_fit / res['slope_x2_pred_chosen'] - 1.0)
    res['ratio_expected_Kfit_over_Knaive'] = float(
        np.mean(x[i0:i_hi + 1]) / L)

    # local speed profile: is x*u constant (Washburn) or does u stay ~V
    for j, lab in ((0, 'first_quarter'), (1, 'last_quarter')):
        a0 = i0 + (i_hi - i0) * j // 4
        a1 = i0 + (i_hi - i0) * (j + 1) // 4
        if a1 - a0 > 5:
            res[f'V_{lab}'] = float(
                (x[a1] - x[a0]) / (t[a1] - t[a0]))
            res[f'xu_{lab}'] = float(np.mean((x * u)[a0:a1]))
    # non-discriminating narrow-window diagnostic (late window, r<=1.5)
    try:
        tgt = x[i_hi] / 1.5
        j0 = int(np.argmax(x >= tgt))
        if i_hi - j0 > 10:
            kk, _, rr = _linfit(t, x ** 2, j0, i_hi)
            res['diag_narrow_window'] = dict(
                x_from=float(x[j0]), x_to=float(x[i_hi]), K=kk, r2=rr,
                K_over_Knaive=float(kk / k_naive),
                note='late-window x^2 fit; r=x2/x1<=1.5 is NOT discriminating '
                     'between the constant-velocity and Washburn laws')
    except Exception:
        pass
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='v1_h26')
    ap.add_argument('--nx', type=int, default=262)
    ap.add_argument('--hy', type=int, default=26)
    ap.add_argument('--x0', type=int, default=40)
    ap.add_argument('--xout', type=int, default=257)
    ap.add_argument('--x-stop', type=int, default=240)
    ap.add_argument('--steps', type=int, default=40000)
    ap.add_argument('--steps-min', type=int, default=2000)
    ap.add_argument('--every', type=int, default=250)
    ap.add_argument('--every-v', type=int, default=1000)
    args = ap.parse_args()
    os.makedirs(OUTROOT, exist_ok=True)
    run(args)


if __name__ == '__main__':
    main()
