"""BI-COLOUR-CLOSURE-001 — colour-channel residual localization driver.

Subcommands
  reproduce : contract A — recompute the external-review blocker numbers
              from the committed BI-SOLVER-CONSERVATION-FIX-001 evidence
              (results/conservation_fix/f0_T3C1s/f0_report.json and
              f1_T3C1s_60k/long_horizon_mass.csv).  No GPU.
  diagnose  : contract B — per-node-class local colour residual partition
              for the periodic-C1 and C3-slit geometries under the current
              T3 + scoped-C1 (or --cf override), with the
              equilibrium -> recoloring -> correction three-stage split,
              the streaming/accumulate residual attribution, x-slab
              profiles and a one-step per-node npz snapshot.
  accum     : contract C — long-horizon mass series on a chosen geometry
              (default periodic C1), horizon_every<=200 sampling.
  budget    : late-window global closure budget on C3: per-step
              Delta M_colour == sum(local R) + sum(accumulate rounding),
              attributed by node class.

All simulation paths call the production kernels in the production step()
order (decomposed probed steps exactly as tests/conservation_fix.py;
non-probed steps call step() itself; use_reservoirs asserted False).

Run examples (repo root, lbm env):
  python tests/colour_closure.py reproduce
  python tests/colour_closure.py diagnose --geom C1 --tag dx_C1_T3C1s
  python tests/colour_closure.py accum --geom C1 --steps 20000 --tag ac_C1_T3C1s_20k
  python tests/colour_closure.py budget --geom C3 --pre-steps 20000 \
      --probe-steps 200 --tag bg_C3_T3C1s
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
sys.path.insert(0, os.path.join(REPO_ROOT, 'tests'))

from conservation_fix import (  # noqa: E402
    build_C1, build_C3, make_solver, measure, git_state, write_json)

E_TABLE = np.array(
    [[0, 0, 0],
     [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1],
     [1, 1, 0], [-1, -1, 0], [1, -1, 0], [-1, 1, 0],
     [1, 0, 1], [-1, 0, -1], [1, 0, -1], [-1, 0, 1],
     [0, 1, 1], [0, -1, -1], [0, 1, -1], [0, -1, 1]], dtype=np.int64)

CHI_PRIMARY = 1e-6
CHI_SENS = (1e-7, 1e-5)


# ---------------------------------------------------------------- shared
def write_csv(path, header, rows):
    with open(path, 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(header)
        for r in rows:
            wr.writerow(['%.12e' % v if isinstance(v, float) else v
                         for v in r])


def gather_incoming(gr, solid):
    """Host replication of the collision-kernel colour scatter (pure
    periodic wrap; bounce-back-to-source when the target is solid;
    membranes asserted zero by the caller).  gr: (nx,ny,nz,19) f32.
    Returns the f64 exact sum, per receiving node, of the incoming
    post-correction populations."""
    nx, ny, nz, _ = gr.shape
    out = np.zeros((nx, ny, nz), dtype=np.float64)
    for s in range(19):
        ex, ey, ez = E_TABLE[s]
        g = gr[..., s]
        # incoming to ip from source ip - e_s: roll(g, +e)[ip] = g[ip - e]
        shifted = np.roll(np.roll(np.roll(g, ex, 0), ey, 1), ez, 2)
        # bounce-back adds the source's own population ON TOP of the
        # stream when its target (i + e_s) is solid: the node keeps g
        # AND still receives whatever the fluid side sends
        # (solid[i + e_s] == roll(solid, -e)[i])
        tgt_solid = np.roll(np.roll(np.roll(solid, -ex, 0), -ey, 1),
                            -ez, 2).astype(bool)
        out += shifted.astype(np.float64)
        out += np.where(tgt_solid, g, 0.0).astype(np.float64)
    return out


def wall_adjacent(solid):
    """Fluid nodes with >=1 solid node among the 19 streaming targets
    (periodic wrap)."""
    adj = np.zeros(solid.shape, dtype=bool)
    for s in range(19):
        ex, ey, ez = E_TABLE[s]
        adj |= np.roll(np.roll(np.roll(solid.astype(bool), -ex, 0),
                               -ey, 1), -ez, 2)
    return adj


def class_masks(solid, fluid, cc, rho_r, rho_b, chi_tau=CHI_PRIMARY):
    """Node-class masks on the fluid set.  Returns dict name->bool array."""
    chi = np.minimum(rho_r, rho_b) / (rho_r + rho_b)
    cc = cc.copy()
    cc[~fluid] = 0.0
    chi = np.where(fluid, chi, 0.0)
    wall = wall_adjacent(solid) & fluid
    ccpos = (cc > 0) & fluid
    cczero = (cc == 0) & fluid
    mixed = (chi > chi_tau) & fluid
    pure = (chi <= chi_tau) & fluid
    out = {
        'ALL': fluid,
        'cc>0': ccpos, 'cc==0': cczero,
        'mixed': mixed, 'pure': pure,
        'wall_adj': wall, 'non_wall': fluid & ~wall,
    }
    for tau in CHI_SENS:
        out['mixed_tau=%g' % tau] = (chi > tau) & fluid
        out['pure_tau=%g' % tau] = (chi <= tau) & fluid
    for a, an in ((ccpos, 'ccpos'), (cczero, 'cczero')):
        for b, bn in ((mixed, 'mixed'), (pure, 'pure')):
            for c, cn in ((wall, 'wall'), (fluid & ~wall, 'nonwall')):
                out['%s/%s/%s' % (an, bn, cn)] = a & b & c
    return out


class StatAcc:
    """Streaming per-class statistics accumulator."""

    def __init__(self):
        self.data = {}

    def add(self, cls, key, values):
        d = self.data.setdefault((cls, key),
                                 dict(n=0, s=0.0, s2=0.0, npos=0,
                                      maxabs=0.0))
        v = np.asarray(values, dtype=np.float64)
        n = v.size
        if n == 0:
            return
        d['n'] += n
        d['s'] += v.sum()
        d['s2'] += float((v ** 2).sum())
        d['npos'] += int((v > 0).sum())
        d['maxabs'] = max(d['maxabs'], float(np.abs(v).max()))

    def rows(self):
        out = []
        for (cls, key), d in sorted(self.data.items()):
            if d['n'] == 0:
                continue
            mean = d['s'] / d['n']
            var = max(d['s2'] / d['n'] - mean * mean, 0.0)
            out.append([cls, key, d['n'], mean, np.sqrt(var),
                        d['npos'] / d['n'], d['maxabs']])
        return out


# ---------------------------------------------------------------- A
def cmd_reproduce(args):
    root = os.path.join(REPO_ROOT, 'results', 'conservation_fix')
    f0 = json.load(open(os.path.join(root, 'f0_T3C1s', 'f0_report.json')))
    rows = list(csv.DictReader(
        open(os.path.join(root, 'f1_T3C1s_60k', 'long_horizon_mass.csv'))))
    t = np.array([float(r['step']) for r in rows])
    Mr = np.array([float(r['Mr']) for r in rows])
    Mb = np.array([float(r['Mb']) for r in rows])
    Mff = np.array([float(r['Mff']) for r in rows])
    Mc = Mr + Mb
    M0 = Mff[0]

    def fit(y, lo, hi):
        m = (t >= lo) & (t <= hi)
        p = np.polyfit(t[m], y[m], 1)
        yh = np.polyval(p, t[m])
        r2 = 1 - np.sum((y[m] - yh) ** 2) / np.sum((y[m] - y[m].mean()) ** 2)
        inc = np.diff(y[m])
        return p[0], r2, float((inc > 0).mean())

    c60 = fit(Mc / M0, 1, 60000)
    segs = [fit(Mc / M0, a, b) for a, b in
            [(1, 20000), (20000, 40000), (40000, 60000)]]
    tot = fit(Mff / M0, 1, 60000)
    c1 = f0['geoms']['C1']['probe']
    c3 = f0['geoms']['C3']['probe']

    def close(x, ref, rtol=0.05):
        return bool(abs(x - ref) <= rtol * abs(ref))

    checks = {
        'B2_C1_Rr_mean': dict(value=c1['R_r']['mean'], ref=3.88e-9,
                              ok=close(c1['R_r']['mean'], 3.88e-9)),
        'B2_C1_Rr_fracpos': dict(value=c1['R_r']['frac_pos'], ref=0.758,
                                 ok=close(c1['R_r']['frac_pos'], 0.758)),
        'B2_C1_Rb_mean': dict(value=c1['R_b']['mean'], ref=3.10e-9,
                              ok=close(c1['R_b']['mean'], 3.10e-9)),
        'B2_C1_Rb_fracpos': dict(value=c1['R_b']['frac_pos'], ref=0.761,
                                 ok=close(c1['R_b']['frac_pos'], 0.761)),
        'B2_C3_Rr_mean': dict(value=c3['R_r']['mean'], ref=9.76e-11,
                              ok=abs(c3['R_r']['mean']) < 2e-10),
        'B2_C3_Rb_mean': dict(value=c3['R_b']['mean'], ref=1.96e-10,
                              ok=abs(c3['R_b']['mean']) < 2e-10),
        'B2_C3_Rr_fracpos': dict(value=c3['R_r']['frac_pos'], ref=0.51,
                                 ok=abs(c3['R_r']['frac_pos'] - 0.5) < 0.05),
        'B1_colour_slope_60k': dict(value=c60[0], ref=-6.43e-10,
                                    ok=close(c60[0], -6.43e-10)),
        'B1_colour_R2_60k': dict(value=c60[1], ref=0.9827,
                                 ok=close(c60[1], 0.9827, 0.01)),
        'B1_seg1': dict(value=segs[0][0], ref=-9.56e-10,
                        ok=close(segs[0][0], -9.56e-10)),
        'B1_seg2': dict(value=segs[1][0], ref=-5.77e-10,
                        ok=close(segs[1][0], -5.77e-10)),
        'B1_seg3': dict(value=segs[2][0], ref=-5.22e-10,
                        ok=close(segs[2][0], -5.22e-10)),
        'total_slope_60k': dict(value=tot[0], ref=1.19e-11,
                                ok=close(tot[0], 1.19e-11, 0.1)),
    }
    rep = dict(task='BI-COLOUR-CLOSURE-001', stage='A_reproduce',
               source_f0='results/conservation_fix/f0_T3C1s/f0_report.json',
               source_f1='results/conservation_fix/f1_T3C1s_60k/'
                         'long_horizon_mass.csv',
               fits=dict(colour_60k=dict(slope=c60[0], r2=c60[1],
                                         frac_pos=c60[2]),
                         segments=[dict(lo=a, hi=b, slope=s[0], r2=s[1],
                                        frac_pos=s[2]) for (a, b), s in
                                   zip([(1, 20000), (20000, 40000),
                                        (40000, 60000)], segs)],
                         total_60k=dict(slope=tot[0], r2=tot[1],
                                        frac_pos=tot[2])),
               checks=checks,
               all_ok=all(c['ok'] for c in checks.values()),
               git=git_state(), started=time.strftime('%Y-%m-%dT%H:%M:%S'))
    out = os.path.join(args.results_root, args.tag)
    os.makedirs(out, exist_ok=True)
    write_json(os.path.join(out, 'reproduce_report.json'), rep)
    print('[%s] all_ok=%s' % (args.tag, rep['all_ok']))
    for k, c in checks.items():
        print('  %-24s %.6e (ref %.3e) ok=%s' % (k, c['value'], c['ref'],
                                                 c['ok']))
    return 0 if rep['all_ok'] else 2


# ------------------------------------------------- decomposed probe step
def probe_step(s):
    """One decomposed production step with dbg capture; returns dict of
    host arrays.  rho_r/rho_b pre-collision values are captured first."""
    pre = dict(rho_r=s.rho_r.to_numpy().astype(np.float64),
               rho_b=s.rho_b.to_numpy().astype(np.float64),
               psi=s.psi.to_numpy().astype(np.float64))
    s.collision()
    s.F.fill(0.0)
    s.streaming1()
    s.Boundary_condition()
    rhor = s.rhor.to_numpy().astype(np.float64)
    rhob = s.rhob.to_numpy().astype(np.float64)
    s.streaming3()
    s.Boundary_condition_psi()
    d = dict(
        rho_r_pre=pre['rho_r'], rho_b_pre=pre['rho_b'], psi_pre=pre['psi'],
        cc=s.dbg_cc.to_numpy(),
        eq_r=s.dbg_sumgr_eq.to_numpy(), eq_b=s.dbg_sumb_eq.to_numpy(),
        rc_r=s.dbg_sumgr_rc.to_numpy(), rc_b=s.dbg_sumb_rc.to_numpy(),
        fin_r=s.dbg_sumgr.to_numpy(), fin_b=s.dbg_sumb.to_numpy(),
        gr=s.dbg_gr.to_numpy(), gb=s.dbg_gb.to_numpy(),
        rhor=rhor, rhob=rhob,
        rho_r_new=s.rho_r.to_numpy().astype(np.float64),
        rho_b_new=s.rho_b.to_numpy().astype(np.float64),
    )
    return d


# ---------------------------------------------------------------- B
def cmd_diagnose(args, Solver):
    solid, psi = build_C1() if args.geom == 'C1' else build_C3()
    fluid = solid == 0
    out = os.path.join(args.results_root, args.tag)
    os.makedirs(out, exist_ok=True)
    rep = dict(task='BI-COLOUR-CLOSURE-001', stage='B_diagnose',
               geom=args.geom, fix=args.fix, cf=args.cf, acc=args.acc,
               dims=list(solid.shape), nfluid=int(fluid.sum()),
               pre_steps=args.pre_steps, probe_steps=args.probe_steps,
               chi_primary=CHI_PRIMARY, chi_sensitivity=list(CHI_SENS),
               arch=os.environ.get('LBM_ARCH', 'gpu'),
               git=git_state(), started=time.strftime('%Y-%m-%dT%H:%M:%S'))

    s = make_solver(Solver, solid, psi, args.fix, args.cf, dbg=True,
                    acc=args.acc)
    assert not s.use_reservoirs
    assert s.mem_r.to_numpy().max() == 0 and s.mem_b.to_numpy().max() == 0

    t0 = time.time()
    for _ in range(args.pre_steps):
        s.step()
    rep['pre_wall_s'] = time.time() - t0

    acc = StatAcc()
    prof = {q: np.zeros(solid.shape[0]) for q in
            ('Req_r', 'R_r', 'dacc_r', 'net_r', 'cc', 'chi')}
    prof_n = 0
    snap = None
    identity_err = []
    for it in range(args.probe_steps):
        d = probe_step(s)
        fin_r, fin_b = d['fin_r'], d['fin_b']
        R_r = fin_r - d['rho_r_pre']
        R_b = fin_b - d['rho_b_pre']
        Req_r = d['eq_r'] - d['rho_r_pre']
        Req_b = d['eq_b'] - d['rho_b_pre']
        Rrec_r = d['rc_r'] - d['eq_r']
        Rrec_b = d['rc_b'] - d['eq_b']
        Rc1_r = fin_r - d['rc_r']
        Rc1_b = fin_b - d['rc_b']
        gin_r = gather_incoming(d['gr'], solid)
        gin_b = gather_incoming(d['gb'], solid)
        # scatter permutation identity (f64 exact): incoming sums == sent
        identity_err.append(
            [abs(gin_r[fluid].sum() - fin_r[fluid].sum()),
             abs(gin_b[fluid].sum() - fin_b[fluid].sum())])
        dacc_r = d['rhor'] - gin_r
        dacc_b = d['rhob'] - gin_b
        net_r = d['rho_r_new'] - d['rho_r_pre']
        net_b = d['rho_b_new'] - d['rho_b_pre']

        masks = class_masks(solid, fluid, d['cc'].copy(),
                            d['rho_r_pre'].copy(), d['rho_b_pre'].copy())
        for cls, m in masks.items():
            acc.add(cls, 'R_r', R_r[m]); acc.add(cls, 'R_b', R_b[m])
            acc.add(cls, 'Req_r', Req_r[m]); acc.add(cls, 'Req_b', Req_b[m])
            acc.add(cls, 'Rrec_r', Rrec_r[m])
            acc.add(cls, 'Rrec_b', Rrec_b[m])
            acc.add(cls, 'Rc1_r', Rc1_r[m]); acc.add(cls, 'Rc1_b', Rc1_b[m])
            acc.add(cls, 'dacc_r', dacc_r[m])
            acc.add(cls, 'dacc_b', dacc_b[m])
            acc.add(cls, 'net_r', net_r[m]); acc.add(cls, 'net_b', net_b[m])
            acc.add(cls, 'cc', d['cc'][m])
        chi = np.minimum(d['rho_r_pre'], d['rho_b_pre']) / \
            (d['rho_r_pre'] + d['rho_b_pre'])
        for q, a in (('Req_r', Req_r), ('R_r', R_r), ('dacc_r', dacc_r),
                     ('net_r', net_r), ('cc', d['cc']), ('chi', chi)):
            prof[q] += np.where(fluid, a, 0.0).mean(axis=(1, 2))
        prof_n += 1
        if it == args.probe_steps - 1:
            snap = {k: v for k, v in d.items()}
            snap['solid'] = solid
            snap['fluid'] = fluid

    write_csv(os.path.join(out, 'class_stats.csv'),
              ['class', 'quantity', 'n', 'mean', 'std', 'frac_pos',
               'max_abs'], acc.rows())
    write_csv(os.path.join(out, 'x_profile.csv'),
              ['x'] + list(prof.keys()),
              [[x] + [prof[q][x] / prof_n for q in prof]
               for x in range(solid.shape[0])])
    np.savez_compressed(
        os.path.join(out, 'snapshot_last_step.npz'), **snap)
    ie = np.array(identity_err)
    rep['scatter_identity_max_abs'] = dict(
        r=float(ie[:, 0].max()), b=float(ie[:, 1].max()))
    write_json(os.path.join(out, 'diagnose_report.json'), rep)
    print('[%s] done; class_stats rows=%d identity_err max %.3e'
          % (args.tag, len(acc.rows()), ie.max()), flush=True)
    return 0


# ---------------------------------------------------------------- C
def cmd_accum(args, Solver):
    solid, psi = build_C1() if args.geom == 'C1' else build_C3()
    fluid = solid == 0
    out = os.path.join(args.results_root, args.tag)
    os.makedirs(out, exist_ok=True)
    rep = dict(task='BI-COLOUR-CLOSURE-001', stage='C_accum',
               geom=args.geom, fix=args.fix, cf=args.cf, acc=args.acc, steps=args.steps,
               horizon_every=args.every, dims=list(solid.shape),
               nfluid=int(fluid.sum()), arch=os.environ.get('LBM_ARCH',
                                                            'gpu'),
               git=git_state(), started=time.strftime('%Y-%m-%dT%H:%M:%S'))
    s = make_solver(Solver, solid, psi, args.fix, args.cf, acc=args.acc)
    assert not s.use_reservoirs
    m0 = measure(s, fluid)
    M0 = m0['Mff']
    rep['M0'] = M0
    rows = []
    t_start = time.time()
    for it in range(1, args.steps + 1):
        s.step()
        if it == 1:
            rep['jit_first_step_s'] = time.time() - t_start
            t_steady = time.time()
        if (it % args.every == 0) or (it == args.steps):
            d = measure(s, fluid)
            rows.append([it, d['Mff'], d['Mr'], d['Mb'], d['Mrho'],
                         d['Mff'] - d['Mr'] - d['Mb']])
    rep['steady_steps_per_s'] = (args.steps - 1) / (time.time() - t_steady)
    rep['mlups'] = (args.steps - 1) * int(fluid.sum())         / (time.time() - t_steady) / 1e6
    write_csv(os.path.join(out, 'mass_series.csv'),
              ['step', 'Mff', 'Mr', 'Mb', 'Mrho', 'd_fc'], rows)
    t = np.array([r[0] for r in rows], dtype=np.float64)

    def fit(y):
        p = np.polyfit(t, y, 1)
        yh = np.polyval(p, t)
        r2 = 1 - np.sum((y - yh) ** 2) / np.sum((y - y.mean()) ** 2)
        inc = np.diff(y)
        return dict(slope_per_step=float(p[0]), r2=float(r2),
                    frac_pos=float((inc > 0).mean()))

    Mrv = np.array([r[2] for r in rows], dtype=np.float64)
    Mbv = np.array([r[3] for r in rows], dtype=np.float64)
    Mffv = np.array([r[1] for r in rows], dtype=np.float64)
    Mr = Mrv / M0 - 1.0
    Mb = Mbv / M0 - 1.0
    Mc = (Mrv + Mbv) / M0 - 1.0
    Mff = Mffv / M0 - 1.0
    rep['drift_fits'] = dict(
        Mr=fit(Mr), Mb=fit(Mb), Mc=fit(Mc), Mff=fit(Mff))
    rep['final_views'] = measure(s, fluid)
    write_json(os.path.join(out, 'accum_report.json'), rep)
    f = rep['drift_fits']
    print('[%s] Mr %.3e (R2 %.4f) Mb %.3e (R2 %.4f) Mc %.3e (R2 %.4f) '
          'Mff %.3e (R2 %.4f)'
          % (args.tag, f['Mr']['slope_per_step'], f['Mr']['r2'],
             f['Mb']['slope_per_step'], f['Mb']['r2'],
             f['Mc']['slope_per_step'], f['Mc']['r2'],
             f['Mff']['slope_per_step'], f['Mff']['r2']), flush=True)
    return 0


# ---------------------------------------------------------------- budget
def cmd_budget(args, Solver):
    solid, psi = build_C1() if args.geom == 'C1' else build_C3()
    fluid = solid == 0
    out = os.path.join(args.results_root, args.tag)
    os.makedirs(out, exist_ok=True)
    rep = dict(task='BI-COLOUR-CLOSURE-001', stage='budget',
               geom=args.geom, fix=args.fix, cf=args.cf, acc=args.acc,
               pre_steps=args.pre_steps, probe_steps=args.probe_steps,
               dims=list(solid.shape), nfluid=int(fluid.sum()),
               arch=os.environ.get('LBM_ARCH', 'gpu'),
               git=git_state(), started=time.strftime('%Y-%m-%dT%H:%M:%S'))
    s = make_solver(Solver, solid, psi, args.fix, args.cf, dbg=True,
                    acc=args.acc)
    assert not s.use_reservoirs
    for _ in range(args.pre_steps):
        s.step()
    rows = []
    acc = StatAcc()
    for it in range(args.probe_steps):
        Mr0 = float(s.rho_r.to_numpy()[fluid].sum(dtype=np.float64))
        Mb0 = float(s.rho_b.to_numpy()[fluid].sum(dtype=np.float64))
        d = probe_step(s)
        R_r = d['fin_r'] - d['rho_r_pre']
        R_b = d['fin_b'] - d['rho_b_pre']
        gin_r = gather_incoming(d['gr'], solid)
        gin_b = gather_incoming(d['gb'], solid)
        dacc_r = d['rhor'] - gin_r
        dacc_b = d['rhob'] - gin_b
        Mr1 = float(d['rho_r_new'][fluid].sum(dtype=np.float64))
        Mb1 = float(d['rho_b_new'][fluid].sum(dtype=np.float64))
        sRr, sRb = R_r[fluid].sum(), R_b[fluid].sum()
        sAr, sAb = dacc_r[fluid].sum(), dacc_b[fluid].sum()
        rows.append([it, Mr1 - Mr0, Mb1 - Mb0, sRr, sRb, sAr, sAb,
                     (Mr1 - Mr0) - (sRr + sAr),
                     (Mb1 - Mb0) - (sRb + sAb)])
        masks = class_masks(solid, fluid, d['cc'].copy(),
                            d['rho_r_pre'].copy(), d['rho_b_pre'].copy())
        for cls in ('cc>0', 'cc==0', 'mixed', 'pure', 'wall_adj',
                    'non_wall'):
            m = masks[cls]
            acc.add(cls, 'sum_R_r', R_r[m])
            acc.add(cls, 'sum_R_b', R_b[m])
            acc.add(cls, 'sum_dacc_r', dacc_r[m])
            acc.add(cls, 'sum_dacc_b', dacc_b[m])
    write_csv(os.path.join(out, 'budget_steps.csv'),
              ['iter', 'dMr', 'dMb', 'sumR_r', 'sumR_b', 'sumdacc_r',
               'sumdacc_b', 'resid_r', 'resid_b'], rows)
    write_csv(os.path.join(out, 'budget_class.csv'),
              ['class', 'quantity', 'n', 'mean', 'std', 'frac_pos',
               'max_abs'], acc.rows())
    arr = np.array(rows, dtype=np.float64)
    rep['means'] = dict(
        dMr=float(arr[:, 1].mean()), dMb=float(arr[:, 2].mean()),
        sumR_r=float(arr[:, 3].mean()), sumR_b=float(arr[:, 4].mean()),
        sumdacc_r=float(arr[:, 5].mean()),
        sumdacc_b=float(arr[:, 6].mean()),
        identity_resid_r=float(np.abs(arr[:, 7]).max()),
        identity_resid_b=float(np.abs(arr[:, 8]).max()))
    write_json(os.path.join(out, 'budget_report.json'), rep)
    m = rep['means']
    print('[%s] dMr %.4e = sumR %.4e + dacc %.4e (resid %.2e) | '
          'dMb %.4e = sumR %.4e + dacc %.4e (resid %.2e)'
          % (args.tag, m['dMr'], m['sumR_r'], m['sumdacc_r'],
             m['identity_resid_r'], m['dMb'], m['sumR_b'],
             m['sumdacc_b'], m['identity_resid_b']), flush=True)
    return 0


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    rp = sub.add_parser('reproduce')
    rp.add_argument('--tag', default='A_reproduce')
    rp.add_argument('--results-root', dest='results_root',
                    default=os.path.join(REPO_ROOT, 'results',
                                         'colour_closure'))

    dg = sub.add_parser('diagnose')
    dg.add_argument('--geom', default='C1', choices=['C1', 'C3'])
    dg.add_argument('--fix', default='T3', choices=['T0', 'T3'])
    dg.add_argument('--cf', default=None,
                    choices=['C0', 'C1', 'C1R', 'C1X'])
    dg.add_argument('--acc', default=None, choices=['A0', 'A1', 'A2'])
    dg.add_argument('--tag', required=True)
    dg.add_argument('--pre-steps', dest='pre_steps', type=int, default=1500)
    dg.add_argument('--probe-steps', dest='probe_steps', type=int,
                    default=40)

    ac = sub.add_parser('accum')
    ac.add_argument('--geom', default='C1', choices=['C1', 'C3'])
    ac.add_argument('--fix', default='T3', choices=['T0', 'T3'])
    ac.add_argument('--cf', default=None,
                    choices=['C0', 'C1', 'C1R', 'C1X'])
    ac.add_argument('--acc', default=None, choices=['A0', 'A1', 'A2'])
    ac.add_argument('--tag', required=True)
    ac.add_argument('--steps', type=int, default=20000)
    ac.add_argument('--every', type=int, default=200)

    bg = sub.add_parser('budget')
    bg.add_argument('--geom', default='C3', choices=['C1', 'C3'])
    bg.add_argument('--fix', default='T3', choices=['T0', 'T3'])
    bg.add_argument('--cf', default=None,
                    choices=['C0', 'C1', 'C1R', 'C1X'])
    bg.add_argument('--acc', default=None, choices=['A0', 'A1', 'A2'])
    bg.add_argument('--tag', required=True)
    bg.add_argument('--pre-steps', dest='pre_steps', type=int, default=20000)
    bg.add_argument('--probe-steps', dest='probe_steps', type=int,
                    default=200)

    for p in (dg, ac, bg):
        p.add_argument('--arch', default='gpu', choices=['gpu', 'cpu'])
        p.add_argument('--results-root', dest='results_root',
                       default=os.path.join(REPO_ROOT, 'results',
                                            'colour_closure'))

    args = ap.parse_args()
    if args.cmd != 'reproduce':
        os.environ['LBM_ARCH'] = args.arch
    if args.cmd == 'reproduce':
        sys.exit(cmd_reproduce(args))
    sys.path.insert(0, REPO_ROOT)
    from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402
    fn = dict(diagnose=cmd_diagnose, accum=cmd_accum, budget=cmd_budget)
    sys.exit(fn[args.cmd](args, ColorGradientSolver3D))


if __name__ == '__main__':
    main()
