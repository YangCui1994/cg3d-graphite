"""BI-SOLVER-CONSERVATION-FIX-001 — F0/F1 driver.

F0 (local identities): run a C3 (two-phase slit) and C1 (periodic
two-phase slab) geometry past the IC transient, then probe a window of
decomposed collisions (production kernel order, dbg_local=True) and
report per-node closure statistics:

    R_f = sum_q f_q(post) - m0(pre)            (device arithmetic)
    R_r = sum_q g_r,q(post) - rho_r(pre)
    R_b = sum_q g_b,q(post) - rho_b(pre)
    colour three-stage split: equilibrium-sum residual / recoloring
    contribution / post-correction residual
    momentum: sum_q e_q (f_post - F_pre) per component (full collision);
    correction-specific residuals from delta_f / dr / db times the f32
    weight-vector first moments.

F1 (long horizon): C3 minimal analogue identical to the audit driver
(checkpoints, f64 host reductions, linear drift fits) with the candidate
fix active, plus JIT/steady performance split.

Both use the PRODUCTION kernels: the decomposed audited step calls
collision / F.fill(0) / streaming1 / Boundary_condition / streaming3 /
Boundary_condition_psi in the exact step() order (reservoir-free cases;
use_reservoirs asserted False); non-probed steps call step() itself.

Run examples (repo root):
  python tests/conservation_fix.py f0 --fix T2 --cf C1 --tag f0_T2C1
  python tests/conservation_fix.py f1 --fix T2 --cf C1 --steps 20000 \
      --tag f1_T2C1C3_20k_gpu
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MATERIAL_REL = 1e-6


# ---------------------------------------------------------------- geometry
def build_C3(nx=126, ny=46, nz=6):
    W, B, G0 = 3, 20, 80
    solid = np.zeros((nx, ny, nz), dtype=np.int8)
    psi = -np.ones((nx, ny, nz), dtype=np.float32)
    solid[:W, :, :] = 1
    solid[nx - W:, :, :] = 1
    solid[:, :3, :] = 1
    solid[:, ny - 3:, :] = 1
    psi[W + B:W + B + G0, :, :] = 1.0
    return solid, psi


def build_C1(nx=64, ny=24, nz=24):
    solid = np.zeros((nx, ny, nz), dtype=np.int8)
    psi = -np.ones((nx, ny, nz), dtype=np.float32)
    psi[nx // 2:, :, :] = 1.0
    return solid, psi


def make_solver(Solver, solid, psi, fix, cf, dbg=False, acc='A0'):
    s = Solver(*solid.shape, niu_l=0.1, niu_g=0.1, CapA=0.06,
               total_fix=fix, colour_fix=cf, dbg_local=dbg, acc_fix=acc)
    if solid[:, :3, :].all():      # C3-like wall geometry
        s.set_psi_solid(-0.68)
    s.init(psi, solid)
    assert not s.use_reservoirs
    return s


def git_state():
    def g(*a):
        return subprocess.run(['git'] + list(a), cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    return dict(head=g('rev-parse', 'HEAD'),
                dirty=g('status', '--porcelain'))


def write_csv(path, header, rows):
    with open(path, 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(header)
        for r in rows:
            wr.writerow(['%.12e' % v if isinstance(v, float) else v
                         for v in r])


def write_json(path, obj):
    with open(path, 'w') as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)


# ---------------------------------------------------------------- F0
def cmd_f0(args, Solver):
    out = os.path.join(args.results_root, args.tag)
    os.makedirs(out, exist_ok=True)
    w_np = None

    geom_specs = [('C3', build_C3()), ('C1', build_C1())]
    summary = dict(tag=args.tag, fix=args.fix, cf=args.cf,
                   arch=os.environ.get('LBM_ARCH', 'gpu'),
                   pre_steps=args.pre_steps, probe_steps=args.probe_steps,
                   geoms={}, git=git_state(),
                   started=time.strftime('%Y-%m-%dT%H:%M:%S'))
    rows = []
    for gname, (solid, psi) in geom_specs:
        s = make_solver(Solver, solid, psi, args.fix, args.cf, dbg=True)
        fluid = solid == 0
        fl = fluid
        t0 = time.time()
        for _ in range(args.pre_steps):
            s.step()
        summary['geoms'][gname] = dict(dims=list(solid.shape),
                                       nfluid=int(fl.sum()),
                                       pre_wall_s=time.time() - t0)

        # probe window: decomposed steps, dbg captured in collision
        m0 = s.dbg_m0pre.to_numpy()
        acc = dict(Rf=[], Rr=[], Rb=[], Req_r=[], Req_b=[],
                   momx=[], momy=[], momz=[],
                   delta=[], dr=[], db=[])
        for it in range(args.probe_steps):
            rho_r_pre = s.rho_r.to_numpy()
            rho_b_pre = s.rho_b.to_numpy()
            s.collision()
            s.F.fill(0.0)
            s.streaming1()
            s.Boundary_condition()
            s.streaming3()
            s.Boundary_condition_psi()
            m0 = s.dbg_m0pre.to_numpy()
            sp = s.dbg_sumpost.to_numpy()
            gr = s.dbg_sumgr.to_numpy()
            gb = s.dbg_sumb.to_numpy()
            greq = s.dbg_sumgr_eq.to_numpy()
            gbeq = s.dbg_sumb_eq.to_numpy()
            mom = s.dbg_mom.to_numpy()
            dl = s.dbg_delta.to_numpy()
            drr = s.dbg_dr.to_numpy()
            dbb = s.dbg_db.to_numpy()
            acc['Rf'].append((sp - m0)[fl])
            acc['Rr'].append((gr - rho_r_pre)[fl])
            acc['Rb'].append((gb - rho_b_pre)[fl])
            acc['Req_r'].append((greq - rho_r_pre)[fl])
            acc['Req_b'].append((gbeq - rho_b_pre)[fl])
            acc['momx'].append(mom[..., 0][fl])
            acc['momy'].append(mom[..., 1][fl])
            acc['momz'].append(mom[..., 2][fl])
            acc['delta'].append(dl[fl])
            acc['dr'].append(drr[fl])
            acc['db'].append(dbb[fl])

        def stats(key):
            v = np.concatenate(acc[key])
            return dict(mean=float(v.mean()), std=float(v.std()),
                        frac_pos=float((v > 0).mean()),
                        max_abs=float(np.abs(v).max()))

        g = dict(
            R_f=stats('Rf'), R_r=stats('Rr'), R_b=stats('Rb'),
            Req_r=stats('Req_r'), Req_b=stats('Req_b'),
            mom_x=stats('momx'), mom_y=stats('momy'), mom_z=stats('momz'),
            delta_f=stats('delta'), dr=stats('dr'), db=stats('db'),
            n_samples=int(np.concatenate(acc['Rf']).size))
        # recoloring contribution = post-recolor pre-correction residual
        # (captured as dbg_sumgr at eq stage ONLY when no C1? no: sumgr
        # is post-recolor+post-C1; recolor contribution estimated as
        # (R_r + Req_r) difference; reported via both entries)
        summary['geoms'][gname]['probe'] = g
        for key in ['R_f', 'R_r', 'R_b', 'Req_r', 'Req_b', 'mom_x',
                    'mom_y', 'mom_z', 'delta_f', 'dr', 'db']:
            st = g[key]
            rows.append([gname, key, st['mean'], st['std'],
                         st['frac_pos'], st['max_abs'], g['n_samples']])
        print('[%s/%s] R_f mean %+.3e frac_pos %.3f | R_r mean %+.3e '
              'fp %.3f | R_b mean %+.3e fp %.3f'
              % (args.tag, gname, g['R_f']['mean'], g['R_f']['frac_pos'],
                 g['R_r']['mean'], g['R_r']['frac_pos'],
                 g['R_b']['mean'], g['R_b']['frac_pos']), flush=True)

    write_csv(os.path.join(out, 'f0_local_identities.csv'),
              ['geom', 'quantity', 'mean', 'std', 'frac_pos', 'max_abs',
               'n_samples'], rows)
    write_json(os.path.join(out, 'f0_report.json'), summary)
    return 0


# ---------------------------------------------------------------- F1
VIEW_KEYS = ['Mff', 'MFF', 'Mr', 'Mb', 'Mracc', 'Mbacc', 'Mrho']


def measure(s, fluid):
    fl = fluid
    f = s.f.to_numpy()
    F = s.F.to_numpy()
    rr = s.rho_r.to_numpy()
    bb = s.rho_b.to_numpy()
    ra = s.rhor.to_numpy()
    ba = s.rhob.to_numpy()
    rho = s.rho.to_numpy()
    return dict(
        Mff=float(f[fl].sum(dtype=np.float64)),
        MFF=float(F[fl].sum(dtype=np.float64)),
        Mr=float(rr[fl].sum(dtype=np.float64)),
        Mb=float(bb[fl].sum(dtype=np.float64)),
        Mracc=float(ra[fl].sum(dtype=np.float64)),
        Mbacc=float(ba[fl].sum(dtype=np.float64)),
        Mrho=float(rho[fl].sum(dtype=np.float64)),
        fF_maxdiff=float(np.abs(f[fl] - F[fl]).max()))


def cmd_f1(args, Solver):
    solid, psi = build_C3()
    fluid = solid == 0
    out = os.path.join(args.results_root, args.tag)
    os.makedirs(out, exist_ok=True)
    rep = dict(tag=args.tag, fix=args.fix, cf=args.cf,
               arch=os.environ.get('LBM_ARCH', 'gpu'), steps=args.steps,
               horizon_every=args.horizon_every,
               dims=list(solid.shape), nfluid=int(fluid.sum()),
               git=git_state(), started=time.strftime('%Y-%m-%dT%H:%M:%S'))

    s = make_solver(Solver, solid, psi, args.fix, args.cf)

    m0 = measure(s, fluid)
    M0 = m0['Mff']
    rep['M0'] = M0
    rep['M0_views'] = m0

    t0 = time.time()
    s.step()                       # first step includes JIT compile
    jit_s = time.time() - t0
    t1 = time.time()
    rows = []
    # step 1 done above; record it
    d = measure(s, fluid)
    rows.append([1] + [d[k] for k in VIEW_KEYS]
                + [d['fF_maxdiff'],
                   d['Mff'] - d['Mr'] - d['Mb'],
                   d['Mff'] - d['Mrho'],
                   d['Mr'] + d['Mb'] - d['Mrho']])
    for it in range(2, args.steps + 1):
        s.step()
        if (it % args.horizon_every == 0) or (it == args.steps):
            d = measure(s, fluid)
            rows.append([it] + [d[k] for k in VIEW_KEYS]
                        + [d['fF_maxdiff'],
                           d['Mff'] - d['Mr'] - d['Mb'],
                           d['Mff'] - d['Mrho'],
                           d['Mr'] + d['Mb'] - d['Mrho']])
    steady_s = time.time() - t1
    rep['jit_first_step_s'] = jit_s
    rep['steady_wall_s'] = steady_s
    rep['steady_steps_per_s'] = (args.steps - 1) / steady_s
    rep['mlups'] = (args.steps - 1) * int(fluid.sum()) / steady_s / 1e6

    write_csv(os.path.join(out, 'long_horizon_mass.csv'),
              ['step'] + VIEW_KEYS + ['fF_maxdiff', 'd_fc_abs',
                                      'd_frho_abs', 'd_crho_abs'], rows)

    hr = np.array([[r[0], r[1], r[3] + r[4], r[7]] for r in rows],
                  dtype=np.float64)
    drift = hr[:, 1:] / M0 - 1.0
    fits = {}
    for k, nm in enumerate(['Mff', 'Mc', 'Mrho']):
        y = drift[:, k]
        A = np.column_stack([hr[:, 0], np.ones_like(hr[:, 0])])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ coef
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        fits[nm] = dict(slope_per_step=float(coef[0]),
                        r2=float(1 - ss_res / ss_tot) if ss_tot > 0 else 1.0,
                        final_rel=float(y[-1]),
                        drift_at={str(int(hr[i, 0])): float(y[i])
                                  for i in range(len(y))})
    rep['drift_fits'] = fits
    rep['final_views'] = measure(s, fluid)
    rep['final_umax'] = float(np.abs(s.v.to_numpy()).max())
    rep['nan'] = bool(np.isnan(s.f.to_numpy()).any()
                      or np.isnan(s.rho.to_numpy()).any())
    write_json(os.path.join(out, 'f1_report.json'), rep)
    print('[%s] slopes: Mff %.3e (R2 %.4f) Mc %.3e (R2 %.4f) Mrho %.3e '
          '(R2 %.4f) | jit %.1fs steady %.0f steps/s (%.1f MLUPS)'
          % (args.tag, fits['Mff']['slope_per_step'], fits['Mff']['r2'],
             fits['Mc']['slope_per_step'], fits['Mc']['r2'],
             fits['Mrho']['slope_per_step'], fits['Mrho']['r2'],
             jit_s, rep['steady_steps_per_s'], rep['mlups']), flush=True)
    return 0


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    f0 = sub.add_parser('f0')
    f0.add_argument('--fix', required=True,
                    choices=['T0', 'T1', 'T2', 'T3', 'T4'])
    f0.add_argument('--cf', default='C0', choices=['C0', 'C1'])
    f0.add_argument('--tag', required=True)
    f0.add_argument('--pre-steps', dest='pre_steps', type=int, default=1500)
    f0.add_argument('--probe-steps', dest='probe_steps', type=int,
                    default=40)

    f1 = sub.add_parser('f1')
    f1.add_argument('--fix', required=True,
                    choices=['T0', 'T1', 'T2', 'T3', 'T4'])
    f1.add_argument('--cf', default='C0', choices=['C0', 'C1'])
    f1.add_argument('--tag', required=True)
    f1.add_argument('--steps', type=int, default=20000)
    f1.add_argument('--horizon-every', dest='horizon_every', type=int,
                    default=200)

    for p in (f0, f1):
        p.add_argument('--arch', default='gpu', choices=['gpu', 'cpu'])
        p.add_argument('--results-root', dest='results_root',
                       default=os.path.join(REPO_ROOT, 'results',
                                            'conservation_fix'))

    args = ap.parse_args()
    os.environ['LBM_ARCH'] = args.arch
    sys.path.insert(0, REPO_ROOT)
    from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402
    if args.cmd == 'f0':
        sys.exit(cmd_f0(args, ColorGradientSolver3D))
    sys.exit(cmd_f1(args, ColorGradientSolver3D))


if __name__ == '__main__':
    main()
