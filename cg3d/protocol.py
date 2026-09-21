"""cg3d.protocol — shared open-system pressure ladder (PR-5, Phase 4).

Extracted from run_pcs_cg3d.py / run_ir_cg3d.py, which were mirror copies
of the same geometry setup + rung loop (Plan_20260919_v2: drainage /
imbibition are protocol configurations, not two infrastructures).
Numerics-neutral by construction: identical statements in identical
order.  One deliberate unification: the umax guard is checked at EVERY
sampling point (the drainage driver used to check it only at
10000-step print points); umax-cap never fired in any baseline run, so
no trajectory changes.

CG3D-IMB-001 (direct imbibition): build_layout() is the pure-NumPy
layout/initial-condition constructor shared by both orientations;
OpenSystem(orientation='imbibition', prewet_layers=N) swaps the phase
roles of the two reservoir/membrane sides while keeping the drainage
path (and both existing drivers) byte-equivalent in behaviour.
"""
import time

import numpy as np

from .diagnostics import region_stats, eval_convergence


def build_layout(solid_full, orientation='drainage', prewet_layers=None,
                 wall_t=3, res_thick=8):
    """Pure-NumPy open-system layout + initial phase field (CG3D-IMB-001).

    Slab along x: [wall wt | reservoir rt | membrane plane | open-pore
    buffers + real structure | membrane plane | reservoir rt | wall wt];
    y/z periodic.  Every x index derives from wall_t / res_thick and the
    geometry's own solid field — no hard-coded positions.

    orientation='drainage' (legacy; verbatim extraction of the original
    OpenSystem.__init__ layout statements): pores start liquid-full
    (psi=-1); the inlet reservoir slab [wt, x_in+1) — including the inlet
    membrane plane — is pre-seeded gas (psi=+1); mem_b sits at x_in
    (blocks blue -> red/gas enters), mem_r at x_out (blocks red ->
    blue/liquid leaves).

    orientation='imbibition' (direct imbibition; requires prewet_layers
    N in [1, real-structure width]): the LEFT side is the liquid
    contact — inlet reservoir, inlet membrane plane, left open buffer
    and the first N real-structure pore layers start liquid (psi=-1);
    all pore cells from x_real_lo+N to the right wall start gas
    (psi=+1), including the right buffer, outlet membrane plane and
    outlet reservoir; mem_r sits at x_in (blocks red -> liquid enters),
    mem_b at x_out (blocks blue -> gas leaves).  The real-structure x
    extent [x_real_lo, x_real_hi) is located from the solid field
    (first/last membrane-interior slab containing solid — the
    make_geo_buffer pads are pure open pore), so the buffer geometry is
    consumed exactly as generated.

    Returns dict(solid, pore_full, psi0, mem_r, mem_b, res_in, res_out,
    dom, dom_pore, pore_cells, x_real_lo, x_real_hi, shape).
    """
    solid_full = np.asarray(solid_full)
    nx = solid_full.shape[0]
    wt, rt = wall_t, res_thick
    x_in, x_out = wt + rt, nx - wt - rt
    solid = solid_full.copy()
    solid[:wt, :, :] = 1
    solid[nx - wt:, :, :] = 1
    pore_full = solid_full == 0
    dom = slice(x_in + 1, x_out)
    dom_pore = pore_full[dom, :, :]

    has_solid = solid[dom, :, :].any(axis=(1, 2))
    if not has_solid.any():
        raise ValueError(
            'no solid between the membranes; cannot locate the real '
            'structure (a pure open-pore slab is not a valid direct-'
            'imbibition geometry)')
    off = x_in + 1
    x_real_lo = off + int(np.argmax(has_solid))
    x_real_hi = off + len(has_solid) - int(np.argmax(has_solid[::-1]))

    mem_r = np.zeros_like(solid)
    mem_b = np.zeros_like(solid)
    res_in = np.zeros_like(solid)
    res_in[wt:x_in, :, :] = 1
    res_out = np.zeros_like(solid)
    res_out[x_out + 1:nx - wt, :, :] = 1

    if orientation == 'drainage':
        psi0 = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
        psi0[wt:x_in + 1, :, :] = np.where(
            pore_full[wt:x_in + 1, :, :], 1.0, 0.0).astype(np.float32)
        # outlet membrane stays blue-pre-wet
        mem_b[x_in, :, :] = 1             # inlet: blocks blue, red enters
        mem_r[x_out, :, :] = 1            # outlet: blocks red, blue leaves
    elif orientation == 'imbibition':
        n_real = x_real_hi - x_real_lo
        if prewet_layers is None:
            raise ValueError('direct imbibition requires prewet_layers')
        if not 1 <= prewet_layers <= n_real:
            raise ValueError(
                f'prewet_layers={prewet_layers} outside the real-structure '
                f'width [1, {n_real}] (real domain x=[{x_real_lo},'
                f'{x_real_hi}))')
        # bulk pore space starts gas; the liquid contact side (reservoir,
        # membrane plane, open buffer, first N real pore layers) is liquid;
        # the walled solid map decides pore-ness so walls stay psi=0
        psi0 = np.where(solid == 0, 1.0, 0.0).astype(np.float32)
        x_liq = x_real_lo + prewet_layers
        psi0[:x_liq, :, :] = np.where(
            solid[:x_liq, :, :] == 0, -1.0, 0.0).astype(np.float32)
        mem_r[x_in, :, :] = 1             # inlet: blocks red, liquid enters
        mem_b[x_out, :, :] = 1            # outlet: blocks blue, gas leaves
    else:
        raise ValueError(f'unknown orientation {orientation!r}')

    return dict(solid=solid, pore_full=pore_full, psi0=psi0,
                mem_r=mem_r, mem_b=mem_b, res_in=res_in, res_out=res_out,
                dom=dom, dom_pore=dom_pore,
                pore_cells=float(dom_pore.sum()),
                x_real_lo=x_real_lo, x_real_hi=x_real_hi,
                shape=solid.shape)


class OpenSystem:
    """wall | res_in | membrane | DOMAIN (open-pore buffers + real
    structure between the two membrane planes) | membrane | res_out
    | wall slab; y/z periodic.  Density-prescribed reservoirs drive
    Pc = cs^2 * d.

    orientation='drainage' (default; the run_pcs_cg3d.py / run_ir_cg3d.py
    configuration): res_in pins psi=+1 (gas source, rho=1+d/2) behind
    mem_b (passes red); res_out pins psi=-1 (liquid sink, rho=1-d/2)
    behind mem_r (passes blue).

    orientation='imbibition' (direct imbibition, CG3D-IMB-001; see
    .agent/decisions/DIRECT_IMBIBITION_BASELINE.md): res_in pins psi=-1
    (liquid source) behind mem_r (passes blue); res_out pins psi=+1
    (gas sink) behind mem_b (passes red); the initial phase field comes
    from build_layout('imbibition', prewet_layers=N).  Only d=0 (equal
    reservoir densities, spontaneous/capillary-driven imbibition) is a
    validated baseline; d>0 would be pressure-assisted imbibition
    (future work, not validated)."""

    def __init__(self, geo_path, capa, psi_solid, res_thick=8, pc_band=4,
                 wall_t=3, orientation='drainage', prewet_layers=None):
        from lbm_solver_cg3d import ColorGradientSolver3D
        dat = np.load(geo_path)
        self.geo_meta = str(dat['meta'][0]) if 'meta' in dat else '{}'
        lay = build_layout(dat['solid'].astype(np.int8),
                           orientation=orientation,
                           prewet_layers=prewet_layers, wall_t=wall_t,
                           res_thick=res_thick)
        self.orientation = orientation
        self.prewet_layers = prewet_layers
        self.dom = lay['dom']
        self.dom_pore = lay['dom_pore']
        self.pore_cells = lay['pore_cells']
        self.x_real = slice(lay['x_real_lo'], lay['x_real_hi'])
        self.real_pore = lay['pore_full'][self.x_real, :, :]
        self.res_in = lay['res_in']
        self.res_out = lay['res_out']
        self.solid = lay['solid']
        self.shape = lay['shape']

        nx, ny, nz = self.shape
        self.s = ColorGradientSolver3D(nx, ny, nz, CapA=capa)
        self.s.set_psi_solid(psi_solid)
        self.s.set_membranes(lay['mem_r'], lay['mem_b'])
        self.set_ladder(0.0)
        self.s.init(lay['psi0'], self.solid)
        self.pc_band = pc_band

    def set_ladder(self, d):
        """rho_in = 1+d/2, rho_out = 1-d/2 -> Pc = cs^2 d (both
        orientations).  Drainage: res_in is the gas side.  Direct
        imbibition: res_in is the liquid side, so d>0 would assist
        imbibition (unvalidated future use)."""
        psi_in, psi_out = ((1.0, -1.0) if self.orientation == 'drainage'
                           else (-1.0, 1.0))
        self.s.set_reservoirs(self.res_in, psi_in, 1.0 + d / 2.0)
        self.s.set_reservoirs(self.res_out, psi_out, 1.0 - d / 2.0)

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
             rung_end_frame=False, it_start=0, it_offset=0,
             live_ckpt=None, ckpt_every=0):
    """One pressure rung.  `ns` is the driver's argparse namespace
    (fields: every, min_steps, max_steps, qs_window, qs_tol, qs_mode,
    pc_drift_tol, flux_tol, u_rel_tol, umax_cap).  `dump_frame(it)` is an
    optional per-driver frame callback (drivers keep their own frame
    naming); rung_end_frame asks for an extra call at rung exit.

    Resume bookkeeping (PR-7, loop logic only — kernels and the exit
    rules are untouched): `it_start` counts the rung's steps from a
    mid-rung checkpoint (convergence windows start empty on replay, so a
    resumed rung runs AT LEAST as long as the uninterrupted one, never
    shorter); `it_offset` shifts only the step numbers handed to
    dump_frame/live_ckpt so frames keep unique global names in a
    resumed output dir; `live_ckpt(it_global)` is called at sampling
    points whenever `ckpt_every` (multiple of ns.every) divides the
    global step.  Returns the ladder row dict."""
    s = sys_.s
    sys_.set_ladder(d)
    t0 = time.time()
    hist = []      # (it, s_nw): quasi-steady slope
    samples = []   # (it, full diagnostic dict): rung-tail means
    it = it_start
    reason = 'max-steps'
    while it < ns.max_steps:
        it += 1
        s.step()
        if dump_frame is not None and ns.dump_every and it % ns.dump_every == 0:
            dump_frame(it + it_offset)
        if it % ns.every == 0:
            if (live_ckpt is not None and ckpt_every
                    and (it + it_offset) % ckpt_every == 0):
                live_ckpt(it + it_offset)
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
        dump_frame(it + it_offset)
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
