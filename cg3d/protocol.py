"""cg3d.protocol — shared open-system pressure ladder (PR-5, Phase 4).

Extracted from run_pcs_cg3d.py / run_ir_cg3d.py, which were mirror copies
of the same geometry setup + rung loop (Plan_20260919_v2: drainage /
imbibition are protocol configurations, not two infrastructures).
Numerics-neutral by construction: identical statements in identical
order.  One deliberate unification: the umax guard is checked at EVERY
sampling point (the drainage driver used to check it only at
10000-step print points); umax-cap never fired in any baseline run, so
no trajectory changes.
"""
import time

import numpy as np

from .diagnostics import region_stats, eval_convergence


class OpenSystem:
    """wall | res_in | mem_b (passes red) | DOMAIN | mem_r (passes blue)
    | res_out | wall slab; y/z periodic.  Density-prescribed reservoirs
    drive Pc = cs^2 * d."""

    def __init__(self, geo_path, capa, psi_solid, res_thick=8, pc_band=4,
                 wall_t=3):
        from lbm_solver_cg3d import ColorGradientSolver3D
        dat = np.load(geo_path)
        self.geo_meta = str(dat['meta'][0]) if 'meta' in dat else '{}'
        solid_full = dat['solid'].astype(np.int8)
        nx, ny, nz = solid_full.shape
        pore_full = solid_full == 0
        wt, rt = wall_t, res_thick
        x_in, x_out = wt + rt, nx - wt - rt
        solid = solid_full.copy()
        solid[:wt, :, :] = 1
        solid[nx - wt:, :, :] = 1
        self.dom = slice(x_in + 1, x_out)
        self.dom_pore = pore_full[self.dom, :, :]
        self.pore_cells = float(self.dom_pore.sum())

        psi0 = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
        psi0[wt:x_in + 1, :, :] = np.where(
            pore_full[wt:x_in + 1, :, :], 1.0, 0.0).astype(np.float32)
        # outlet membrane stays blue-pre-wet
        mem_r = np.zeros_like(solid)
        mem_b = np.zeros_like(solid)
        mem_b[x_in, :, :] = 1             # inlet: blocks blue, red enters
        mem_r[x_out, :, :] = 1            # outlet: blocks red, blue leaves
        self.res_in = np.zeros_like(solid)
        self.res_in[wt:x_in, :, :] = 1
        self.res_out = np.zeros_like(solid)
        self.res_out[x_out + 1:nx - wt, :, :] = 1

        self.s = ColorGradientSolver3D(nx, ny, nz, CapA=capa)
        self.s.set_psi_solid(psi_solid)
        self.s.set_membranes(mem_r, mem_b)
        self.set_ladder(0.0)
        self.s.init(psi0, solid)
        self.pc_band = pc_band
        self.solid = solid
        self.shape = (nx, ny, nz)

    def set_ladder(self, d):
        """rho_in = 1+d/2, rho_out = 1-d/2 -> Pc = cs^2 d."""
        self.s.set_reservoirs(self.res_in, 1.0, 1.0 + d / 2.0)
        self.s.set_reservoirs(self.res_out, -1.0, 1.0 - d / 2.0)

    def measure(self):
        """PR-1 instruments (2.1-2.3): reservoir / band / domain-flow
        diagnostics on top of s_nw & umax."""
        s = self.s
        dom, dom_pore = self.dom, self.dom_pore
        pore_cells = self.pore_cells
        psi = s.psi_snapshot()
        rho, v = s.macro_snapshot()
        red = np.where(dom_pore, (psi[dom, :, :] + 1.0) / 2.0, 0.0)
        rho_c, psi_c, v_c = rho[dom, :, :], psi[dom, :, :], v[dom, :, :, :]
        u_mag = np.sqrt(v_c[..., 0]**2 + v_c[..., 1]**2 + v_c[..., 2]**2)
        rs_in = region_stats(rho, psi, v, self.res_in.astype(bool))
        rs_out = region_stats(rho, psi, v, self.res_out.astype(bool))
        band_in_m = np.zeros_like(dom_pore)
        band_in_m[:self.pc_band] = dom_pore[:self.pc_band]
        band_out_m = np.zeros_like(dom_pore)
        band_out_m[-self.pc_band:] = dom_pore[-self.pc_band:]
        band_in = region_stats(rho_c, psi_c, v_c, band_in_m)
        band_out = region_stats(rho_c, psi_c, v_c, band_out_m)
        fd = region_stats(rho_c, psi_c, v_c, dom_pore)
        fl = s.reservoir_fluxes()
        return dict(s_nw=float(red.sum() / pore_cells),
                    s_nw_binary=float(((psi_c > 0.0) & dom_pore).sum()
                                      / pore_cells),
                    umax=float(u_mag.max()),
                    rho_in_mean=rs_in['rho_mean'],
                    rho_out_mean=rs_out['rho_mean'],
                    p_in_mean=rs_in['p_mean'], p_out_mean=rs_out['p_mean'],
                    pc_band_in=band_in['p_mean'],
                    pc_band_out=band_out['p_mean'],
                    pc_measured=band_in['p_mean'] - band_out['p_mean'],
                    u_rms=fd['v_rms'], u_bulk_x=fd['v_bulk'][0],
                    inj_r=fl['inj_r'], inj_b=fl['inj_b'], inj_m=fl['inj_m'])


def run_equil(ns, sys_, sample=False):
    """Equilibration at d = 0.  Returns the last s_nw sample (or None)."""
    last = None
    for it in range(1, ns.equil_steps + 1):
        sys_.s.step()
        if sample and it % ns.every == 0:
            last = sys_.measure()['s_nw']
    return last


def run_hold(ns, sys_, d, label, phase=None, dump_frame=None,
             rung_end_frame=False):
    """One pressure rung.  `ns` is the driver's argparse namespace
    (fields: every, min_steps, max_steps, qs_window, qs_tol, qs_mode,
    pc_drift_tol, flux_tol, u_rel_tol, umax_cap).  `dump_frame(it)` is an
    optional per-driver frame callback (drivers keep their own frame
    naming); rung_end_frame asks for an extra call at rung exit.
    Returns the ladder row dict."""
    s = sys_.s
    sys_.set_ladder(d)
    t0 = time.time()
    hist = []      # (it, s_nw): quasi-steady slope
    samples = []   # (it, full diagnostic dict): rung-tail means
    it = 0
    reason = 'max-steps'
    while it < ns.max_steps:
        it += 1
        s.step()
        if dump_frame is not None and ns.dump_every and it % ns.dump_every == 0:
            dump_frame(it)
        if it % ns.every == 0:
            m = sys_.measure()
            hist.append((it, m['s_nw']))
            samples.append((it, m))
            w = [(i, sv) for i, sv in hist
                 if i > it - ns.qs_window]
            if (it >= ns.min_steps and len(w) >= 4
                    and w[-1][0] - w[0][0] >= ns.qs_window * 0.8):
                slope = (w[-1][1] - w[0][1]) / (w[-1][0] - w[0][0])
                if abs(slope) < ns.qs_tol:
                    win = [(a2, dm) for a2, dm in samples
                           if a2 > it - ns.qs_window]
                    conv = eval_convergence(
                        win, sys_.pore_cells, ns.qs_tol,
                        ns.pc_drift_tol, ns.flux_tol, ns.u_rel_tol)
                    needed = (['saturation'] if ns.qs_mode == 'sat'
                              else ('saturation', 'pressure', 'flux',
                                    'kinetic'))
                    if all(c in conv['criteria_passed'] for c in needed):
                        reason = 'quasi-steady'
                        break
            if it % 10000 == 0:
                print(f'  {label} {it} S_nw={hist[-1][1]:.4f} '
                      f'umax={m["umax"]:.3f}', flush=True)
            if m['umax'] > ns.umax_cap:
                reason = 'umax-cap'
                break
    if rung_end_frame and dump_frame is not None and ns.dump_every:
        dump_frame(it)
    tail = [sv for _, sv in hist[-20:]]
    diag = [dm for _, dm in samples[-20:]]
    tmean = lambda k: (float(np.mean([dm[k] for dm in diag]))
                       if diag else None)
    # net colour flux rate over the same trailing window as the
    # slope test (mass/step through the reservoirs)
    win = [(i, dm) for i, dm in samples if i > it - ns.qs_window]
    if len(win) >= 2 and win[-1][0] > win[0][0]:
        span = win[-1][0] - win[0][0]
        flux_r_rate = (win[-1][1]['inj_r'] - win[0][1]['inj_r']) / span
        flux_b_rate = (win[-1][1]['inj_b'] - win[0][1]['inj_b']) / span
    else:
        flux_r_rate = flux_b_rate = None
    conv = eval_convergence(win, sys_.pore_cells, ns.qs_tol,
                            ns.pc_drift_tol, ns.flux_tol, ns.u_rel_tol)
    conv['exit'] = dict(mode=ns.qs_mode, reason=reason)
    m_last = samples[-1][1] if samples else {}
    row = dict(d=d, pc_nominal=d / 3.0, pc_measured=tmean('pc_measured'),
               rho_in_mean=tmean('rho_in_mean'),
               rho_out_mean=tmean('rho_out_mean'),
               p_in_mean=tmean('p_in_mean'), p_out_mean=tmean('p_out_mean'),
               u_rms=tmean('u_rms'), u_bulk_x=tmean('u_bulk_x'),
               flux_r_rate=flux_r_rate, flux_b_rate=flux_b_rate,
               steps=it, reason=reason,
               s_nw=float(np.mean(tail)) if tail else None,
               s_nw_binary=tmean('s_nw_binary'),
               convergence=conv,
               umax_last=m_last.get('umax'),
               wall_s=round(time.time() - t0, 1))
    if phase is not None:
        row['phase'] = phase
    print(f'[{label}] d={d:.4f} -> {reason} steps={it} '
          f'S_nw={row["s_nw"]} wall={row["wall_s"]}s', flush=True)
    return row
