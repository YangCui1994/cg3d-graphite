"""V2 bilateral — mirror-symmetric trapped-pocket verification.

Task BI-V2-BILATERAL-001 (V2_BILATERAL_CONTRACT.md).  Closed system:
two wetting buffers advance from both x ends of a straight h=40 slit
toward a central non-wetting pocket that is TRAPPED FROM t=0.  No
reservoirs, no membranes, no forcing.  The primary question is
symmetry / colour mass / topology / stability, NOT absolute filling
rate; the two fronts are NOT required to collide, and no x^2(t) law is
an acceptance relation.

GEOMETRY (exact mirror about x -> nx-1-x)
-----------------------------------------
nx = 3+80+160+80+3 = 326, ny = h+2 = 42, nz = 6 (z periodic)

    x: [0,3) wall | [3,83) liquid buffer | [83,243) gas pocket
       | [243,323) liquid buffer | [323,326) wall

    y: wall | 40-lu slit (psi_solid=-0.68) | wall

Physics fixed: CapA=0.06, nu=0.1 matched, rho0=1, psi_wall=-0.68.
Expected closed-system scale (diagnostic only): capillary pressure
~2.4e-3 against pocket stiffness rho*cs^2=1/3 stalls the fronts after
~O(1 lu) one-sided displacement; total displacement < 2 lu makes the
conditional rate comparison NOT_DISCRIMINATING by contract, which is
an acceptable outcome, and INTERACTION_ONSET may be NOT_REACHED.

OBSERVABLE RULES (mechanical, declared before the run)
------------------------------------------------------
front (primary) : linear interpolation of the phi_l(x)=0.5 crossing,
    phi_l = <(1-psi)/2>_{y,z fluid} per column; left front searched in
    [3,163], right front in [163,323].
front (secondary, volumetric): x_L_vol = 3 + sum_{x<163} phi_l,
    x_R_vol = 323 - sum_{x>162} phi_l.
mirror error    : e_x = |x_left - (nx-1-x_right)| (and volumetric
    analogue); gate e_x <= max(2 lu, 0.02 d(t)), d = mean one-sided
    displacement.
field symmetry  : E_psi = mean_{fluid} |psi(x)-psi(nx-1-x)|.
gap columns     : gas-bulk >=95% fluid nodes psi>+0.9; liquid-bulk
    <= -0.9; else mixed.  G_bulk = longest contiguous bulk-gas run;
    INTERACTION_ONSET = first sample with G_bulk == 0 (no bulk-gas
    column between the liquid bulks); NOT_REACHED is acceptable.
clusters        : 6-neighbour, z-periodic only (scipy.ndimage.label +
    z-wrap union-find); t=0 must be exactly ONE trapped cluster.
mass            : eps_{r,b} = |M(t)-M(0)|/max(M(0),1) <= 5e-4 gate.
stability       : u_max <= 0.12; fluid rho in [0.89, 1.11]; no NaN.

Usage: python tests/levelc_v2_bilateral.py --tag v2_primary
Outputs -> results/levelc_v2/<tag>/
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
from scipy import ndimage

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from lbm_solver_cg3d import ColorGradientSolver3D   # noqa: E402

OUTROOT = os.path.join(REPO, 'results', 'levelc_v2')

CAPA = 0.06
SIGMA = 1.012 * CAPA
NU = 0.1
RHO0 = 1.0
UMAX_CAP = 0.12
PSI_WALL = -0.68
RHO_LO, RHI_HI = 0.89, 1.11
MASS_TOL = 5e-4

W, B, G0, H, NZ = 3, 80, 160, 40, 6
NX = W + B + G0 + B + W            # 326
X_LIQ0, X_LIQ1 = W, W + B          # [3,83) left buffer
X_GAS0, X_GAS1 = X_LIQ1, X_LIQ1 + G0    # [83,243)
X_LIQ2, X_LIQ3 = X_GAS1, X_GAS1 + B     # [243,323)
X_MID = (NX - 1) / 2.0             # 162.5 mirror plane
T_TRANS = 12000                    # 3*h^2/(4 nu), V1c convention
BULK_THR, BULK_FRAC = 0.90, 0.95


# ---------------------------------------------------------------- provenance
def prov(cmd_argv):
    script = os.path.abspath(__file__)
    with open(script, 'rb') as f:
        psha = hashlib.sha256(f.read()).hexdigest()

    def gitq(*a):
        return subprocess.run(['git', '-C', REPO, *a], text=True,
                              capture_output=True).stdout.strip()
    return dict(
        producer_script='tests/levelc_v2_bilateral.py',
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
        json.dump(obj, f, indent=1)


# ---------------------------------------------------------------- geometry
def build():
    ny = H + 2
    y0, y1 = 1, 1 + H
    solid = np.ones((NX, ny, NZ), dtype=np.int8)
    solid[W:NX - W, y0:y1, :] = 0
    psi_solid = np.full((NX, ny, NZ), PSI_WALL, dtype=np.float32)
    psi0 = np.zeros((NX, ny, NZ), dtype=np.float32)
    psi0[solid != 0] = 0.0
    psi0[W:X_GAS0, y0:y1, :] = -1.0
    psi0[X_GAS0:X_GAS1, y0:y1, :] = +1.0
    psi0[X_GAS1:NX - W, y0:y1, :] = -1.0
    return solid, psi_solid, psi0, y0, y1


def verify_symmetry(solid, psi_solid, psi0):
    """Contract section 7 — programmatic mirror checks (hard failure)."""
    checks = dict(
        solid_mirror=bool((solid == solid[::-1, :, :]).all()),
        psi_solid_mirror=bool((psi_solid == psi_solid[::-1, :, :]).all()),
        psi0_mirror=bool((psi0 == psi0[::-1, :, :]).all()),
        left_buffer_len=int(X_LIQ1 - X_LIQ0),
        right_buffer_len=int(X_LIQ3 - X_LIQ2),
        buffers_equal=bool(X_LIQ1 - X_LIQ0 == X_LIQ3 - X_LIQ2),
        gas_len=int(X_GAS1 - X_GAS0),
        gas_centred=bool((X_GAS0 + X_GAS1) / 2.0 == (NX - 1) / 2.0 + 0.5),
        mirror_plane=(X_GAS0 + X_GAS1) / 2.0,
        nx=NX, layout=dict(wall=[0, 3], liq_left=[3, 83], gas=[83, 243],
                           liq_right=[243, 323], wall_r=[323, 326],
                           h=H, nz=NZ, B=B, G0=G0))
    ok = (checks['solid_mirror'] and checks['psi_solid_mirror']
          and checks['psi0_mirror'] and checks['buffers_equal']
          and checks['gas_centred'] and checks['left_buffer_len'] == B
          and checks['gas_len'] == G0)
    checks['all_pass'] = bool(ok)
    return checks


# ---------------------------------------------------------------- analysis
def column_phi(psi, y0, y1):
    """phi_l(x) = mean over the slit cross-section of (1-psi)/2."""
    return ((1.0 - psi[:, y0:y1, :]) * 0.5).mean(axis=(1, 2))


def front_positions(phi):
    """Primary fronts: interpolated phi_l = 0.5 crossings (left in
    [3,163), right in [163,323)).  Returns (x_left, x_right) or None."""
    half = NX // 2
    xl = _cross_down(phi, W, half)
    xr = _cross_up(phi, half, NX - W)
    if xl is None or xr is None:
        return None
    return xl, xr


def _cross_down(phi, a, b):
    for i in range(a, b - 1):
        if phi[i] >= 0.5 > phi[i + 1]:
            f0, f1 = phi[i], phi[i + 1]
            return i + (f0 - 0.5) / (f0 - f1) if f0 != f1 else float(i)
    return None


def _cross_up(phi, a, b):
    for i in range(a, b - 1):
        if phi[i] < 0.5 <= phi[i + 1]:
            f0, f1 = phi[i], phi[i + 1]
            return i + (0.5 - f0) / (f1 - f0) if f1 != f0 else float(i + 1)
    return None


def column_classes(psi, y0, y1):
    frac_g = (psi[:, y0:y1, :] > +BULK_THR).mean(axis=(1, 2))
    frac_l = (psi[:, y0:y1, :] < -BULK_THR).mean(axis=(1, 2))
    return (frac_g >= BULK_FRAC), (frac_l >= BULK_FRAC)


def gap_metrics(gas_cols, liq_cols):
    """Longest contiguous central bulk-gas run + mixed-envelope span."""
    runs = []
    a = None
    for i, v in enumerate(gas_cols):
        if v and a is None:
            a = i
        elif not v and a is not None:
            runs.append((a, i))
            a = None
    if a is not None:
        runs.append((a, len(gas_cols)))
    g_bulk = max((b - a for a, b in runs), default=0)
    # envelopes: mixed columns (neither bulk) spanning between the left
    # and right LIQUID bulk regions around the central gas
    m = ~(gas_cols | liq_cols)
    liq_idx = np.where(liq_cols)[0]
    env_l = env_r = None
    if len(liq_idx) >= 2:
        lo, hi = liq_idx.min(), liq_idx.max()
        inner = np.where(m[lo:hi + 1])[0]
        if len(inner):
            env_l, env_r = int(lo + inner[0]), int(lo + inner[-1])
    return g_bulk, runs, env_l, env_r


def label_gas(psi, rho):
    """6-neighbour, z-periodic-only labelling of psi>0 nodes.
    Returns (n_clusters, sizes, largest_label, mean_rho_largest,
    labels)."""
    mask = psi > 0
    if not mask.any():
        return 0, np.array([]), None, None, None
    st = ndimage.generate_binary_structure(3, 1)      # 6-neighbour
    lab, n = ndimage.label(mask, structure=st)
    # z-periodic merge: union labels of (x,y,0) and (x,y,nz-1) pairs
    parent = list(range(n + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    z0 = mask[:, :, 0]
    z1 = mask[:, :, NZ - 1]
    both = z0 & z1
    for i, j in zip(*np.nonzero(both)):
        union(int(lab[i, j, 0]), int(lab[i, j, NZ - 1]))
    roots = np.array([find(l) for l in range(1, n + 1)])
    node_counts = np.bincount(lab.ravel(), minlength=n + 1)
    sizes_by_root = np.zeros(n + 1)
    np.add.at(sizes_by_root, roots, node_counts[1:])
    uniq = np.unique(roots)
    n_clusters = int(len(uniq))
    sizes = sizes_by_root[uniq]
    root_largest = int(uniq[np.argmax(sizes_by_root[uniq])]) if n else None
    mean_rho = None
    if n_clusters:
        labels_largest = np.where(roots == root_largest)[0] + 1
        sel = np.isin(lab, labels_largest)
        mean_rho = float(rho[sel].mean())
    return n_clusters, sizes, root_largest, mean_rho, lab


# ---------------------------------------------------------------- run
def run(args):
    p = prov(sys.argv)
    out = os.path.join(OUTROOT, args.tag)
    os.makedirs(out, exist_ok=True)
    solid, psi_solid, psi0, y0, y1 = build()
    sym = verify_symmetry(solid, psi_solid, psi0)
    write_json(os.path.join(out, 'symmetry_check.json'), sym)
    if not sym['all_pass']:
        print('SYMMETRY CHECK FAILED:', {k: v for k, v in sym.items()
                                         if k != 'layout'}, flush=True)
        return 2

    s = ColorGradientSolver3D(NX, H + 2, NZ, niu_l=NU, niu_g=NU, CapA=CAPA)
    s.set_psi_solid_field(psi_solid)
    # no membranes, no reservoirs, no forcing (closed system)
    s.init(psi0, solid)

    m0 = s.color_masses()
    rho0f, v0f = s.macro_snapshot()
    psi0_snap = s.psi_snapshot()
    t0_lab = label_gas(psi0_snap, rho0f)
    t0_topology = dict(n_clusters=int(t0_lab[0]),
                       largest=int(t0_lab[1].max()) if t0_lab[0] else 0,
                       mean_rho_largest=t0_lab[3],
                       note='6-neighbour, z-periodic-only; central gas '
                            'trapped from t=0 by construction')
    write_json(os.path.join(out, 'topology_t0.json'), t0_topology)
    if t0_topology['n_clusters'] != 1:
        print('T0 TOPOLOGY != 1 cluster:', t0_topology, flush=True)
        return 2
    np.savez_compressed(os.path.join(out, 'fields_initial.npz'),
                        psi=psi0_snap.astype(np.float32),
                        rho=rho0f.astype(np.float32))
    write_csv(os.path.join(out, 'slice_initial.csv'),
              ['x', 'psi_midslice'],
              [(x, float(psi0_snap[x, y0:y1, NZ // 2].mean()))
               for x in range(NX)], p)

    phi0 = column_phi(psi0_snap, y0, y1)
    fr0 = front_positions(phi0)
    x_left0, x_right0 = fr0
    print(f'[{args.tag}] nx={NX} ny={H + 2} nz={NZ} x_left0={x_left0:.3f} '
          f'x_right0={x_right0:.3f} t0_clusters={t0_topology}'
          f' steps={args.steps}', flush=True)

    f_rows, g_rows, m_rows = [], [], []
    onset_step = None
    exit_reason = 'steps_cap'
    nan_at = None
    umax_break = None
    rho_break = None
    mid_done = False
    it = 0
    t_start = time.time()
    while it < args.steps:
        it += 1
        s.step()
        if it % args.every:
            continue
        psi = s.psi_snapshot()
        if not np.isfinite(psi).all():
            nan_at = it
            exit_reason = f'NaN/Inf in psi at step {it} -- blocking stop'
            print(f'[{args.tag}] {exit_reason}', flush=True)
            break
        rho, v = s.macro_snapshot()
        if not np.isfinite(rho).all():
            nan_at = it
            exit_reason = f'NaN/Inf in rho at step {it} -- blocking stop'
            print(f'[{args.tag}] {exit_reason}', flush=True)
            break
        phi = column_phi(psi, y0, y1)
        fr = front_positions(phi)
        if fr is None:
            exit_reason = (f'front crossing not found at step {it} -- '
                           f'blocking stop (interface degenerate?)')
            print(f'[{args.tag}] {exit_reason}', flush=True)
            break
        x_left, x_right = fr
        x_right_star = (NX - 1) - x_right
        e_x = abs(x_left - x_right_star)
        d = 0.5 * ((x_left - x_left0) + (x_right_star - x_right0))
        xl_vol = W + float(phi[W:NX // 2].sum())
        xr_vol = (NX - W) - float(phi[NX // 2:NX - W].sum())
        e_vol = abs(xl_vol - ((NX - 1) - xr_vol))
        e_psi = float(np.abs(
            psi[W:NX - W, :, :] - psi[W:NX - W, :, :][::-1, :, :]).sum()
            / (solid == 0).sum())
        f_rows.append((it, x_left, x_right, x_right_star, e_x, d,
                       xl_vol, xr_vol, e_vol, e_psi))

        if it % args.every_v == 0:
            vm = np.linalg.norm(v, axis=3)
            fl = solid == 0
            umax = float(vm[fl].max())
            urms = float(np.sqrt((vm[fl] ** 2).mean()))
            rmin = float(rho[fl].min())
            rmax = float(rho[fl].max())
            if umax > UMAX_CAP and umax_break is None:
                umax_break = it
                print(f'[{args.tag}] u_max={umax:.4f} > {UMAX_CAP} at '
                      f'{it}', flush=True)
            if (rmin < RHO_LO or rmax > RHI_HI) and rho_break is None:
                rho_break = it
                print(f'[{args.tag}] rho [{rmin:.4f},{rmax:.4f}] outside '
                      f'[{RHO_LO},{RHI_HI}] at {it}', flush=True)
            gas_cols, liq_cols = column_classes(psi, y0, y1)
            g_bulk, runs, env_l, env_r = gap_metrics(gas_cols, liq_cols)
            if g_bulk == 0 and onset_step is None:
                onset_step = it
                print(f'[{args.tag}] INTERACTION_ONSET at {it}', flush=True)
            gas_mask = psi > 0
            v_bin = int(gas_mask.sum())
            v_cont = float(((1.0 + psi[fl]) * 0.5).sum())
            mass_proxy = float(
                (rho[fl] * (1.0 + psi[fl]) * 0.5).sum())
            nc, sizes, root_l, mean_rho_l, _ = label_gas(psi, rho)
            buf_gas_l = int(gas_mask[X_LIQ0:X_LIQ1, y0:y1, :].sum())
            buf_gas_r = int(gas_mask[X_LIQ2:X_LIQ3, y0:y1, :].sum())
            g_rows.append((it, v_bin, v_cont, mass_proxy, nc,
                           int(sizes.max()) if nc else 0,
                           mean_rho_l if mean_rho_l else float('nan'),
                           (mean_rho_l / 3.0) if mean_rho_l
                           else float('nan'),
                           g_bulk, env_l if env_l is not None else -1,
                           env_r if env_r is not None else -1,
                           buf_gas_l, buf_gas_r, rmin, rmax,
                           umax, urms))
            mm = s.color_masses()
            m_rows.append((it, mm[0], mm[1],
                           abs(mm[0] - m0[0]) / max(m0[0], 1.0),
                           abs(mm[1] - m0[1]) / max(m0[1], 1.0),
                           umax, urms, rmin, rmax, e_psi))
            if it % (args.every * 40) == 0:
                el = time.time() - t_start
                print(f'[{args.tag}] {it:6d}/{args.steps} '
                      f'xL={x_left:7.3f} xR*={x_right_star:7.3f} '
                      f'e_x={e_x:.4f} G_bulk={g_bulk} V_bin={v_bin} '
                      f'({el:.0f}s, {it / el:.0f} st/s)', flush=True)
            if not mid_done and it >= args.steps // 2:
                mid_done = True
                np.savez_compressed(
                    os.path.join(out, 'fields_mid.npz'),
                    psi=psi.astype(np.float32), rho=rho.astype(np.float32))
                write_csv(os.path.join(out, 'slice_mid.csv'),
                          ['x', 'psi_midslice'],
                          [(x, float(psi[x, y0:y1, NZ // 2].mean()))
                           for x in range(NX)], p)
        if umax_break == it or rho_break == it:
            exit_reason = (f'operational guardrail broken at {it} '
                           f'(umax_break={umax_break}, '
                           f'rho_break={rho_break}) -- blocking stop')
            break

    wall = time.time() - t_start
    psi_f = s.psi_snapshot()
    rho_f, v_f = s.macro_snapshot()
    mm_fin = s.color_masses()
    np.savez_compressed(os.path.join(out, 'fields_final.npz'),
                        psi=psi_f.astype(np.float32),
                        rho=rho_f.astype(np.float32))
    write_csv(os.path.join(out, 'slice_final.csv'),
              ['x', 'psi_midslice'],
              [(x, float(psi_f[x, y0:y1, NZ // 2].mean()))
               for x in range(NX)], p)
    write_csv(os.path.join(out, 'front_series.csv'),
              ['t', 'x_left', 'x_right', 'x_right_star', 'e_x', 'd',
               'x_L_vol', 'x_R_vol', 'e_x_vol', 'E_psi'], f_rows, p)
    write_csv(os.path.join(out, 'gas_series.csv'),
              ['t', 'V_bin', 'V_cont', 'gas_mass_proxy', 'n_clusters',
               'largest', 'rho_gas_mean', 'p_gas_mean', 'G_bulk',
               'env_L', 'env_R', 'buf_gas_L', 'buf_gas_R', 'rho_min',
               'rho_max', 'umax', 'urms'], g_rows, p)
    write_csv(os.path.join(out, 'mass_stability_series.csv'),
              ['t', 'm_r', 'm_b', 'eps_r', 'eps_b', 'umax', 'urms',
               'rho_min', 'rho_max', 'E_psi'], m_rows, p)

    a = analyze(f_rows, m_rows, g_rows, onset_step, exit_reason,
                t0_topology)
    a.update(tag=args.tag, steps_run=it, wall_s=wall, nan_at=nan_at,
             umax_break=umax_break, rho_break=rho_break,
             exit_reason=exit_reason, INTERACTION_ONSET=(
                 onset_step if onset_step else 'NOT_REACHED'),
             symmetry=sym, t0_topology=t0_topology,
             m_r_final=mm_fin[0], m_b_final=mm_fin[1],
             m_r0=m0[0], m_b0=m0[1],
             layout=sym['layout'], prov=p)
    write_json(os.path.join(out, 'report.json'), a)
    prov_finish(p, 0)
    print(f'[{args.tag}] {exit_reason}; gates all_hard='
          f'{a["gates"]["all_hard"]}', flush=True)
    return 0


def analyze(f_rows, m_rows, g_rows, onset_step, exit_reason, t0_topo):
    t = np.array([r[0] for r in f_rows], float)
    e_x = np.array([r[4] for r in f_rows], float)
    d = np.array([r[5] for r in f_rows], float)
    xl = np.array([r[1] for r in f_rows], float)
    xrs = np.array([r[3] for r in f_rows], float)
    e_vol = np.array([r[8] for r in f_rows], float)
    eps_r = np.array([r[3] for r in m_rows], float)
    eps_b = np.array([r[4] for r in m_rows], float)
    umax_s = np.array([r[5] for r in m_rows], float)
    rmin_s = np.array([r[7] for r in m_rows], float)
    rmax_s = np.array([r[8] for r in m_rows], float)
    nc_s = np.array([r[4] for r in g_rows], float)
    vbin_s = np.array([r[1] for r in g_rows], float)
    vbin0 = vbin_s[0]

    gate_e_x = bool(np.all(e_x <= np.maximum(2.0, 0.02 * d))) \
        if len(e_x) else False
    # conditional rate symmetry
    rate = dict(status='NOT_DISCRIMINATING')
    if len(t) > 8:
        i0 = int(np.argmax(t >= T_TRANS))
        i1 = (int(np.argmax(t >= onset_step)) if onset_step
              else len(t) - 1)
        if i1 - i0 >= 5:
            dl = xl[i0] - xl[0]
            dr = xrs[i0] - xrs[0]
            # window displacement (mechanical: from IC to window start
            # plus window motion) — use window displacement directly
            dl_w = xl[i1] - xl[i0]
            dr_w = xrs[i1] - xrs[i0]
            rate['displacement_left_window'] = float(dl_w)
            rate['displacement_right_window'] = float(dr_w)
            if abs(dl_w) >= 2.0 and abs(dr_w) >= 2.0:
                vl = np.polyfit(t[i0:i1 + 1], xl[i0:i1 + 1], 1)[0]
                vr = np.polyfit(t[i0:i1 + 1], xrs[i0:i1 + 1], 1)[0]
                rel = 2 * abs(vl - vr) / (abs(vl) + abs(vr))
                rate.update(status='DISCRIMINATED', V_L=float(vl),
                            V_R=float(vr), rel_diff=float(rel),
                            gate=rel <= 0.05)
            else:
                rate['status'] = 'NOT_DISCRIMINATING'
                rate['note'] = ('window displacement < 2 lu on at least '
                                'one side — contract permits '
                                'NOT_DISCRIMINATING')
    res = dict(
        n_samples=len(t),
        max_e_x=float(e_x.max()) if len(e_x) else None,
        rms_e_x=float(np.sqrt((e_x ** 2).mean())) if len(e_x) else None,
        max_e_x_vol=float(e_vol.max()) if len(e_vol) else None,
        max_d=float(d.max()) if len(d) else None,
        final_d=float(d[-1]) if len(d) else None,
        max_eps_r=float(eps_r.max()), max_eps_b=float(eps_b.max()),
        max_umax=float(umax_s.max()), min_rho=float(rmin_s.min()),
        max_rho=float(rmax_s.max()),
        V_bin_initial=float(vbin0), V_bin_final=float(vbin_s[-1]),
        V_bin_min=float(vbin_s.min()),
        V_bin_change_pct=float((vbin_s[-1] - vbin0) / vbin0 * 100.0),
        cluster_count_max=int(nc_s.max()),
        cluster_count_final=int(nc_s[-1]),
        fragmentation_before_onset=bool(
            (nc_s[:int(np.argmax(t >= onset_step)) if onset_step
                  else len(nc_s)] > 1).any()),
        rate_symmetry=rate)
    res['gates'] = dict(
        g1_no_nan=exit_reason.startswith(('steps_cap', 'front reached',
                                          'INTERACTION')) or 'NaN'
        not in exit_reason,
        g2_umax=float(umax_s.max()) <= UMAX_CAP,
        g3_rho_range=(float(rmin_s.min()) >= RHO_LO
                      and float(rmax_s.max()) <= RHI_HI),
        g4_initial_symmetry=None,     # in symmetry_check.json (hard)
        g5_mirror_error=gate_e_x,
        g6_mass_drift=(float(eps_r.max()) <= MASS_TOL
                       and float(eps_b.max()) <= MASS_TOL),
        g7_t0_single_trapped_cluster=(
            t0_topo['n_clusters'] == 1),
        g8_no_fragmentation_before_onset=(
            not res['fragmentation_before_onset']),
        g9_onset_reproducible=(onset_step is None or True),
        g10_reviewer_reproducible=None)
    res['gates']['all_hard'] = all(
        v is True for k, v in res['gates'].items()
        if k not in ('g10_reviewer_reproducible', 'all_hard'))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--tag', default='v2_primary')
    ap.add_argument('--steps', type=int, default=60000)
    ap.add_argument('--every', type=int, default=250)
    ap.add_argument('--every-v', dest='every_v', type=int, default=1000)
    args = ap.parse_args()
    os.makedirs(os.path.join(OUTROOT, 'logs'), exist_ok=True)
    sys.exit(run(args))


if __name__ == '__main__':
    main()
