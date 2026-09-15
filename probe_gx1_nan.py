"""Probe WHERE/WHY the graphite 200^3 equil goes NaN (X1 gate tripped).

Replicates run_pcs_cg3d.py layout exactly, then runs a short equil with
frequent diagnostics.  Modes isolate the trigger:

  A  exact driver equil (res_in psi=+1: a red/blue interface sits at the
     inlet membrane even at delta=0)
  B  all-wetting start (res_in psi=-1: NO interface anywhere) -- if NaN
     persists, single-phase flow through sub-resolution pores is unstable
     by itself; if it disappears, the capillary interface is the trigger
  C  = A but psi_solid=-0.75 (P3b value; rules the -0.68 wettability out)
  D  = B but psi_solid=-1.0 (wall colour == fluid colour: no wall colour
       flux at all; discriminates wall-colour-flux vs pure narrow-gap
       hydro instability)
  E  = D minus membranes/reservoirs: plain bounce-back walls, uniform
       psi=-1, no semi-permeable machinery at all (discriminates the
       membrane coupling)

Run from 2phase/:  python probe_gx1_nan.py --mode A
Stops at first NaN or --steps (default 3000).  Prints one line per --every
(50) steps: step, S_nw, umax, rho min/max, mass drift; on blowup, the
x/y/z of umax and rho extremes + their distance to the membrane planes and
the local pore radius (EDT).  Bounded output.
"""
import argparse
import os
import time

import numpy as np
from scipy import ndimage

from lbm_solver_cg3d import ColorGradientSolver3D

GEO = 'geo_graphite_200.npz'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['A', 'B', 'C', 'D', 'E'], default='A')
    ap.add_argument('--steps', type=int, default=3000)
    ap.add_argument('--every', type=int, default=50)
    ap.add_argument('--capa', type=float, default=0.06)
    ap.add_argument('--buffer', type=int, default=0,
                    help='pad k OPEN pore layers at both x faces of the '
                         'geo: decouples the membrane plane from the rough '
                         'graphite face (geometry-side fix; driver layout '
                         'formulas are unchanged, nx grows by 2k)')
    args = ap.parse_args()
    psi_solid = {'A': -0.68, 'B': -0.68, 'C': -0.75, 'D': -1.0,
                 'E': -1.0}[args.mode]
    res_in_psi = +1.0 if args.mode in ('A', 'C') else -1.0

    solid_full = np.load(GEO)['solid'].astype(np.int8)
    if args.buffer > 0:
        k = args.buffer
        pad = np.zeros((solid_full.shape[0] + 2 * k,) + solid_full.shape[1:],
                       dtype=np.int8)
        pad[k:k + solid_full.shape[0]] = solid_full
        solid_full = pad
        print(f'[probe {args.mode}] buffer={k} lu open pore at both x faces '
              f'(nx -> {solid_full.shape[0]})', flush=True)
    nx, ny, nz = solid_full.shape
    wt, rt = 3, 8
    x_imem_in, x_imem_out = wt + rt, nx - wt - rt
    pore_full = solid_full == 0
    solid = solid_full.copy()
    solid[:wt] = 1
    solid[nx - wt:] = 1
    dom = slice(x_imem_in + 1, x_imem_out)
    dom_pore = pore_full[dom]

    edt = ndimage.distance_transform_edt(solid == 0)

    psi0 = np.where(solid == 0, -1.0, 0.0).astype(np.float32)
    psi0[wt:x_imem_in + 1] = np.where(
        pore_full[wt:x_imem_in + 1], 1.0, 0.0).astype(np.float32)
    psi0[x_imem_in] = np.where(pore_full[x_imem_in], 1.0,
                               0.0).astype(np.float32)
    if args.mode == 'B':
        psi0[wt:x_imem_in + 1] = np.where(
            pore_full[wt:x_imem_in + 1], -1.0, 0.0).astype(np.float32)
    mem_r = np.zeros_like(solid)
    mem_b = np.zeros_like(solid)
    mem_b[x_imem_in] = 1
    mem_r[x_imem_out] = 1
    res_in = np.zeros_like(solid)
    res_in[wt:x_imem_in] = 1
    res_out = np.zeros_like(solid)
    res_out[x_imem_out + 1:nx - wt] = 1

    s = ColorGradientSolver3D(nx, ny, nz, CapA=args.capa)
    s.set_psi_solid(psi_solid)
    if args.mode != 'E':
        s.set_membranes(mem_r, mem_b)
        s.set_reservoirs(res_in, res_in_psi, 1.0)
        s.set_reservoirs(res_out, -1.0, 1.0)
    s.init(psi0, solid)
    m0 = s.total_mass()
    pore_cells = float(dom_pore.sum())
    print(f'[probe {args.mode}] psi_solid={psi_solid} res_in_psi='
          f'{res_in_psi:+.0f} capa={args.capa}', flush=True)

    t0 = time.time()
    for it in range(1, args.steps + 1):
        s.step()
        if it % args.every:
            continue
        psi = s.psi_snapshot()
        rho, v = s.macro_snapshot()
        um = np.sqrt(v[..., 0]**2 + v[..., 1]**2 + v[..., 2]**2)
        red = np.where(dom_pore, (psi[dom] + 1.0) / 2.0, 0.0)
        s_nw = red.sum() / pore_cells
        bad = not np.isfinite(um).all() or not np.isfinite(rho).all()
        umax = float(np.nanmax(um)) if np.isfinite(um).any() else float('nan')
        rmin = float(np.nanmin(rho)) if np.isfinite(rho).any() else float('nan')
        rmax = float(np.nanmax(rho)) if np.isfinite(rho).any() else float('nan')
        drift = (s.total_mass() - m0) / m0
        print(f'[probe {args.mode}] {it:5d} S_nw={s_nw:+.4f} umax={umax:.4f} '
              f'rho=[{rmin:.4f},{rmax:.4f}] drift={drift:+.2e} '
              f'({time.time() - t0:.0f}s)', flush=True)
        if bad:
            fin = np.isfinite(um)
            umc = np.where(fin, um, 0.0)
            loc = np.unravel_index(np.argmax(umc), um.shape)
            print(f'[probe {args.mode}] NaN at step {it}; hotspot {loc} '
                  f'(x,y,z), x rel: imem_in={x_imem_in} dom=[{dom.start},'
                  f'{dom.stop}) imem_out={x_imem_out}', flush=True)
            print(f'  local pore radius (EDT) at hotspot: '
                  f'{edt[loc]:.2f} lu; psi={psi[loc]:+.2f}; '
                  f'solid={solid[loc]}', flush=True)
            rho_f = np.where(np.isfinite(rho), rho, 0.0)
            lo = np.unravel_index(np.argmin(rho_f), rho.shape)
            hi = np.unravel_index(np.argmax(rho_f), rho.shape)
            print(f'  rho extremes: min {rho_f[lo]:.3f} at {lo} '
                  f'(edt {edt[lo]:.2f}), max {rho_f[hi]:.3f} at {hi} '
                  f'(edt {edt[hi]:.2f})', flush=True)
            # how localized is the blowup?
            hot = (umc > 0.1 * umax) & fin
            xs = np.unique(np.where(hot)[0])
            print(f'  cells with umax>0.1*max: {hot.sum()} ; affected x '
                  f'slabs: {xs.min()}..{xs.max()} (n={len(xs)}); '
                  f'frac in domain={hot[dom].mean():.4f}', flush=True)
            return
    print(f'[probe {args.mode}] survived {args.steps} steps, no NaN',
          flush=True)


if __name__ == '__main__':
    main()
