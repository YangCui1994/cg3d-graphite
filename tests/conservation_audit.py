"""BI-CONSERVATION-AUDIT-001 — solver conservation audit (diagnostic only).

Locates and classifies the monotone closed-system mass drift observed in
V1c/V2 (colour channel ~5.5e-4, population channel ~9.2e-4 over 60k steps)
WITHOUT modifying the solver.

Method: reproduce the production timestep exactly by calling the public
kernels in the same order as ColorGradientSolver3D.step():

    collision -> F.fill(0) -> streaming1 -> Boundary_condition
              -> streaming3 -> Boundary_condition_psi [-> apply_reservoirs]

with mass measurements (float64 host reductions over fluid nodes) taken at
checkpoints S0..S6 between kernels.  Host reads do not mutate field state;
the audited decomposed step is kernel-for-kernel identical to step() for
the reservoir-free cases used here (asserted: use_reservoirs == False).

Mass views at every checkpoint:
    Mff   = sum_fluid sum_s f      (total-distribution channel, field f)
    MFF   = sum_fluid sum_s F      (streaming accumulator / pre-collision
                                    total state; authoritative at S0/S3/S4)
    Mr,Mb = sum_fluid rho_r,rho_b  (macro colour masses)
    Mracc,Mbacc = sum_fluid rhor,rhob (colour-in-flight accumulators,
                                    nonzero between collision and streaming3)
    Mrho  = sum_fluid rho          (macro density = on-device f32 sum of f)

Cross-representation residuals (primary diagnostics, normalized by M0):
    d_fc = (Mff - (Mr+Mb))/M0      total channel vs colour channel
    d_frho = (Mff - Mrho)/M0       total channel vs macro density
    d_crho = ((Mr+Mb) - Mrho)/M0   colour channel vs macro density

Per-step sub-step identities (localization):
    J0  S0 bit-invariant f == F                    (expect exactly 0)
    J1  collision total conservation: Mff(S1)-MFF(S0)
    J2  F.fill(0) exact: MFF(S2)                   (expect exactly 0)
    J3  streaming1 conservation: MFF(S3)-Mff(S1)
    J4  Boundary_condition inactive: MFF(S4)-MFF(S3)   (expect exactly 0)
    J5  streaming3 copy exact: Mff(S5)-MFF(S4)     (expect exactly 0)
    J6  macro reconstruction: Mrho(S5)-Mff(S5)     (device f32 19-term sum)
    J7  colour transport conservation:
        (Mracc+Mbacc)(S4) - (Mr+Mb)(S0)
    J8  colour consume exact: (Mr+Mb)(S5)-(Mracc+Mbacc)(S4)  (expect 0)
    J9  closure S6(n) == S0(n+1) for every view, consecutive traced steps

Cases (contract section 5):
    C0 periodic single phase, no solid   (pure collision/streaming floor)
    C1 periodic two phase, no solid      (+ interface/recoloring)
    C2 single-phase slit, bounce-back walls (+ wall bookkeeping)
    C3 two-phase slit, bounce-back walls (minimal V2 analogue, mirror IC)

Backends: --arch gpu|cpu (sets LBM_ARCH before importing the solver, which
initialises taichi at module import).

Outputs under <results-root>/<tag>/: substep_mass_trace.csv,
identities.csv, long_horizon_mass.csv, spatial_budget.csv (C3),
fields_t0.npz / fields_ref.npz, case_report.json, prov.json.  The analyze
subcommand aggregates case reports into summary.json /
backend_comparison.csv / scaling_results.csv.

Exit codes: 0 ok, 2 setup/verification failure.
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

CASE_DEFAULTS = {
    # case: (dims, steps, horizon_every, trace_first, late_start,
    #        late_count, budget_ref_step)
    'C0': ((24, 24, 24), 5000, 100, 20, 4900, 20, None),
    'C1': ((64, 24, 24), 10000, 200, 20, 9000, 20, None),
    'C2': ((32, 46, 6), 10000, 200, 20, 9000, 20, None),
    'C3': ((126, 46, 6), 20000, 200, 20, 19000, 20, 1000),
}

MATERIAL_REL = 1e-6   # "materially nonzero" threshold for cumulative deltas

VIEW_KEYS = ['Mff', 'MFF', 'Mr', 'Mb', 'Mracc', 'Mbacc', 'Mrho']
J_NAMES = ['J0_fF_bitdiff', 'J1_collision', 'J2_fill', 'J3_stream1',
           'J4_bc', 'J5_stream3copy', 'J6_macro', 'J7_colortrans',
           'J8_colconsume', 'J9_closure_max']


# ---------------------------------------------------------------- geometry
def build_case(case, nx, ny, nz):
    """Return (solid, psi0, psi_solid_field or None, layout_info).

    Fixed physics everywhere: niu_l=niu_g=0.1, CapA=0.06, no force, no
    membranes, no reservoirs, all bc_* flags left at the periodic default.
    """
    solid = np.zeros((nx, ny, nz), dtype=np.int8)
    psi = -np.ones((nx, ny, nz), dtype=np.float32)
    psi_solid = None
    info = {}
    if case == 'C1':
        psi[nx // 2:, :, :] = 1.0
        info = dict(layout='periodic slabs: psi=-1 x<[nx/2], +1 otherwise;'
                    ' two interfaces separated by nx/2 lu')
    elif case == 'C2':
        solid[:, :3, :] = 1
        solid[:, ny - 3:, :] = 1
        psi_solid = np.full((nx, ny, nz), -0.68, dtype=np.float32)
        info = dict(layout='y walls 3 lu (solid [0,3) and [ny-3,ny)); '
                    'fluid slit h=%d; x/z periodic' % (ny - 6))
    elif case == 'C3':
        W, B, G0 = 3, 20, 80
        if nx != 2 * W + 2 * B + G0 or ny != 46:
            raise SystemExit('C3 requires nx=%d ny=46' % (2 * W + 2 * B + G0))
        solid[:W, :, :] = 1
        solid[nx - W:, :, :] = 1
        solid[:, :3, :] = 1
        solid[:, ny - 3:, :] = 1
        psi[:] = -1.0
        psi[W + B:W + B + G0, :, :] = 1.0
        psi_solid = np.full((nx, ny, nz), -0.68, dtype=np.float32)
        info = dict(layout='mirror closed slit W=3 B=20 G0=80 h=40 nz=6; '
                    'fluid x in [3,%d), gas x in [%d,%d)'
                    % (nx - W, W + B, W + B + G0))
    elif case != 'C0':
        raise SystemExit('unknown case ' + case)
    return solid, psi, psi_solid, info


def verify_mirror(solid, psi, psi_solid):
    m = {}
    m['solid_mirror_equal'] = bool(np.array_equal(solid, solid[::-1, :, :]))
    m['psi_mirror_equal'] = bool(np.array_equal(psi, psi[::-1, :, :]))
    if psi_solid is not None:
        m['psi_solid_mirror_equal'] = bool(
            np.array_equal(psi_solid, psi_solid[::-1, :, :]))
    m['all_pass'] = all(m.values())
    return m


# ---------------------------------------------------------------- measure
def measure(s, fluid):
    """All mass views + representation invariant, f64 host reductions."""
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
        fF_maxdiff=float(np.abs(f[fl] - F[fl]).max()),
    )


def umax_of(s):
    return float(np.abs(s.v.to_numpy()).max())


def snapshot_fields(s, fluid):
    """Per-node mass fields for the spatial budget (f64 f-sums)."""
    return dict(psi=s.psi.to_numpy().astype(np.float32),
                rho_r=s.rho_r.to_numpy().astype(np.float64),
                rho_b=s.rho_b.to_numpy().astype(np.float64),
                rho=s.rho.to_numpy().astype(np.float64),
                fsum=s.f.to_numpy().sum(axis=3, dtype=np.float64))


# ---------------------------------------------------------------- csv utils
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


def git_state():
    def g(*a):
        return subprocess.run(['git'] + list(a), cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    return dict(head=g('rev-parse', 'HEAD'),
                branch=g('rev-parse', '--abbrev-ref', 'HEAD'),
                dirty=g('status', '--porcelain'))


def prov(argv):
    import taichi
    return dict(argv=[str(a) for a in argv],
                cwd=os.getcwd(),
                env_arch=os.environ.get('LBM_ARCH'),
                python=sys.version.split()[0],
                taichi=taichi.__version__,
                numpy=np.__version__,
                started=time.strftime('%Y-%m-%dT%H:%M:%S'),
                git=git_state())


# ---------------------------------------------------------------- one case
def run_case(args, Solver):
    dims = args.dims or CASE_DEFAULTS[args.case][0]
    nx, ny, nz = dims
    (_, d_steps, d_h, d_tf, d_ls, d_lc, d_ref) = CASE_DEFAULTS[args.case]
    steps = args.steps if args.steps is not None else d_steps
    horizon = args.horizon_every or d_h
    trace_first = args.trace_first if args.trace_first is not None else d_tf
    late_start, late_count = (args.late_trace if args.late_trace
                              else (d_ls, d_lc))
    ref_step = args.budget_ref_step if args.budget_ref_step is not None \
        else d_ref

    out = os.path.join(args.results_root, args.tag)
    os.makedirs(out, exist_ok=True)
    p = prov(sys.argv)
    write_json(os.path.join(out, 'prov.json'), p)

    solid, psi0, psi_solid, info = build_case(args.case, nx, ny, nz)
    fluid = solid == 0
    nfluid = int(fluid.sum())
    report = dict(case=args.case, arch=args.arch, tag=args.tag,
                  dims=[nx, ny, nz], steps=steps, nfluid=nfluid,
                  horizon_every=horizon, trace_first=trace_first,
                  late_window=[late_start, late_count],
                  budget_ref_step=ref_step, layout=info)
    if args.case == 'C3':
        sym = verify_mirror(solid, psi0, psi_solid)
        write_json(os.path.join(out, 'symmetry_check.json'), sym)
        report['mirror_check'] = sym
        if not sym['all_pass']:
            print('C3 MIRROR CHECK FAILED:', sym, flush=True)
            return 2

    s = Solver(nx, ny, nz, niu_l=0.1, niu_g=0.1, CapA=0.06)
    if psi_solid is not None:
        s.set_psi_solid_field(psi_solid)
    assert not s.use_reservoirs, 'audit cases must be reservoir-free'
    t_init0 = time.time()
    s.init(psi0, solid)

    # static sanity: nothing may live on solid nodes
    f0 = s.f.to_numpy()
    rho0 = s.rho.to_numpy()
    report['solid_residue'] = dict(
        f_abs_sum=float(np.abs(f0[~fluid]).sum(dtype=np.float64)),
        rho_abs_sum=float(np.abs(rho0[~fluid]).sum(dtype=np.float64)))

    snap_t0 = snapshot_fields(s, fluid)
    np.savez_compressed(os.path.join(out, 'fields_t0.npz'), **snap_t0)

    m0 = measure(s, fluid)
    M0 = m0['Mff']
    report['M0'] = M0
    report['M0_views'] = m0
    print('[%s] M0=%g nfluid=%d init+first-compile %.1fs'
          % (args.tag, M0, nfluid, time.time() - t_init0), flush=True)

    traced = sorted(set(range(0, min(trace_first, steps)))
                    | set(range(late_start,
                                min(late_start + late_count, steps))))
    traced_set = set(traced)

    trace_rows = []       # (step, ckpt, views...)
    ident_rows = []       # (step, d_fc, d_frho, d_crho, J0..J9)
    horizon_rows = []     # end-of-step views every `horizon` steps
    prev_s6 = None
    prev_s6_step = -10
    closure_fail = 0
    snap_ref = None

    def take(step, ckpt, d):
        trace_rows.append([step, ckpt] + [d[k] for k in VIEW_KEYS]
                          + [d['fF_maxdiff']])

    def cross_deltas(d):
        fc = d['Mff'] - (d['Mr'] + d['Mb'])
        fr = d['Mff'] - d['Mrho']
        cr = (d['Mr'] + d['Mb']) - d['Mrho']
        return fc, fr, cr

    t_run0 = time.time()
    for it in range(steps):
        if it in traced_set:
            rec = {}
            d = measure(s, fluid)
            rec['S0'] = d
            take(it, 'S0', d)
            s.collision()
            d = measure(s, fluid); rec['S1'] = d; take(it, 'S1', d)
            s.F.fill(0.0)
            d = measure(s, fluid); rec['S2'] = d; take(it, 'S2', d)
            s.streaming1()
            d = measure(s, fluid); rec['S3'] = d; take(it, 'S3', d)
            s.Boundary_condition()
            d = measure(s, fluid); rec['S4'] = d; take(it, 'S4', d)
            s.streaming3()
            d = measure(s, fluid); rec['S5'] = d; take(it, 'S5', d)
            s.Boundary_condition_psi()
            d = measure(s, fluid); rec['S6'] = d; take(it, 'S6', d)

            fc, fr, cr = cross_deltas(rec['S0'])
            J = dict(
                J0_fF_bitdiff=rec['S0']['fF_maxdiff'],
                J1_collision=rec['S1']['Mff'] - rec['S0']['MFF'],
                J2_fill=rec['S2']['MFF'],
                J3_stream1=rec['S3']['MFF'] - rec['S1']['Mff'],
                J4_bc=rec['S4']['MFF'] - rec['S3']['MFF'],
                J5_stream3copy=rec['S5']['Mff'] - rec['S4']['MFF'],
                J6_macro=rec['S5']['Mrho'] - rec['S5']['Mff'],
                J7_colortrans=(rec['S4']['Mracc'] + rec['S4']['Mbacc'])
                - (rec['S0']['Mr'] + rec['S0']['Mb']),
                J8_colconsume=(rec['S5']['Mr'] + rec['S5']['Mb'])
                - (rec['S4']['Mracc'] + rec['S4']['Mbacc']),
            )
            if prev_s6_step == it - 1 and prev_s6 is not None:
                closure = max(abs(rec['S0'][k] - prev_s6[k])
                              for k in VIEW_KEYS)
                J['J9_closure_max'] = closure
                if closure != 0.0:
                    closure_fail += 1
            else:
                J['J9_closure_max'] = float('nan')
            prev_s6 = rec['S6']
            prev_s6_step = it
            ident_rows.append(
                [it, fc, fr, cr] + [J[k] for k in J_NAMES])
        else:
            s.step()          # production path (identical kernel order)

        if ref_step is not None and (it + 1) == ref_step:
            snap_ref = snapshot_fields(s, fluid)
            np.savez_compressed(os.path.join(out, 'fields_ref.npz'),
                                **snap_ref)

        if ((it + 1) % horizon == 0) or (it == steps - 1):
            d = measure(s, fluid)
            fc, fr, cr = cross_deltas(d)
            horizon_rows.append([it + 1] + [d[k] for k in VIEW_KEYS]
                                + [d['fF_maxdiff'], fc, fr, cr,
                                   umax_of(s)])
    wall = time.time() - t_run0
    report['wall_s'] = wall
    report['steps_per_s'] = steps / wall
    print('[%s] run done %.1fs (%.0f steps/s)'
          % (args.tag, wall, steps / wall), flush=True)

    # ---- spatial budget (C3): regions from FINAL psi, deltas vs t0/ref
    if args.case == 'C3':
        refs = {'t0': snap_t0}
        if snap_ref is not None:
            refs['ref%d' % ref_step] = snap_ref
        budget_rows, budget_summary = spatial_budget(s, fluid, refs)
        write_csv(os.path.join(out, 'spatial_budget.csv'),
                  ['region', 'ref', 'nodes', 'Mr_ref', 'Mr_fin', 'dMr',
                   'Mb_ref', 'Mb_fin', 'dMb', 'Mc_ref', 'Mc_fin', 'dMc',
                   'Mrho_ref', 'Mrho_fin', 'dMrho', 'Mf_ref', 'Mf_fin',
                   'dMf'], budget_rows)
        report['spatial_budget'] = budget_summary

    # ---- write raw csvs
    write_csv(os.path.join(out, 'substep_mass_trace.csv'),
              ['step', 'ckpt'] + VIEW_KEYS + ['fF_maxdiff'], trace_rows)
    write_csv(os.path.join(out, 'identities.csv'),
              ['step', 'd_fc_abs', 'd_frho_abs', 'd_crho_abs'] + J_NAMES,
              ident_rows)
    write_csv(os.path.join(out, 'long_horizon_mass.csv'),
              ['step'] + VIEW_KEYS + ['fF_maxdiff', 'd_fc_abs',
                                      'd_frho_abs', 'd_crho_abs', 'umax'],
              horizon_rows)

    # ---- derived statistics
    report['closure_fail_steps'] = closure_fail
    ident_stats = {}
    for idx, nm in enumerate(J_NAMES):
        col = np.array([r[4 + idx] for r in ident_rows], dtype=np.float64)
        col = col[~np.isnan(col)]
        if col.size == 0:
            ident_stats[nm] = None
            continue
        ident_stats[nm] = dict(
            n=int(col.size),
            mean=float(col.mean()),
            std=float(col.std()),
            max_abs=float(np.abs(col).max()),
            frac_pos=float((col > 0).mean()),
            mean_rel_M0=float(col.mean() / M0),
            max_abs_rel_M0=float(np.abs(col).max() / M0))
    report['identity_stats'] = ident_stats

    # horizon drift series (relative) + linear fits
    # horizon row layout: step(0) Mff(1) MFF(2) Mr(3) Mb(4) Mracc(5)
    #                     Mbacc(6) Mrho(7) fF_maxdiff(8) d_fc(9)
    #                     d_frho(10) d_crho(11) umax(12)
    hr = np.array([[r[0], r[1], r[3] + r[4], r[7]] for r in horizon_rows],
                  dtype=np.float64)   # step, Mff, Mc=Mr+Mb, Mrho
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
    report['drift_fits'] = fits

    # first materially-nonzero cross-representation residual (horizon)
    firsts = {}
    for k, nm in enumerate(['d_fc', 'd_frho', 'd_crho']):
        col = np.array([r[9 + k] for r in horizon_rows], dtype=np.float64)
        rel = np.abs(col) / M0
        hit = np.nonzero(rel > MATERIAL_REL)[0]
        firsts[nm] = int(horizon_rows[hit[0]][0]) if hit.size else None
    report['first_material_residual_horizon'] = firsts

    report['final_views'] = measure(s, fluid)
    report['final_umax'] = umax_of(s)
    report['nan_check'] = dict(
        f=bool(np.isnan(s.f.to_numpy()).any()),
        rho=bool(np.isnan(s.rho.to_numpy()).any()))
    write_json(os.path.join(out, 'case_report.json'), report)
    fin = report['final_views']
    print('[%s] FINAL rel: d_fc=%.3e d_frho=%.3e d_crho=%.3e | '
          'slopes: Mff %.3e (R2 %.4f) Mc %.3e (R2 %.4f) Mrho %.3e (R2 %.4f)'
          % (args.tag,
             (fin['Mff'] - fin['Mr'] - fin['Mb']) / M0,
             (fin['Mff'] - fin['Mrho']) / M0,
             (fin['Mr'] + fin['Mb'] - fin['Mrho']) / M0,
             fits['Mff']['slope_per_step'], fits['Mff']['r2'],
             fits['Mc']['slope_per_step'], fits['Mc']['r2'],
             fits['Mrho']['slope_per_step'], fits['Mrho']['r2']),
          flush=True)
    return 0


def spatial_budget(s, fluid, refs):
    """Regions defined mechanically from the FINAL psi snapshot.

    wall_rows : fluid nodes adjacent along y to a solid node
    interface : remaining nodes with |psi_final| <= 0.9
    gas_bulk  : remaining nodes with psi_final > 0.9
    liq_bulk  : remaining nodes with psi_final < -0.9

    Every fluid node belongs to exactly one region (wall rows are carved
    out first, so the bulk/interface classes are interior-only).
    Deltas are reported against each provided reference snapshot.
    """
    psi_f = s.psi.to_numpy()
    wall_rows = np.zeros_like(fluid)
    wall_rows[:, 1:-1, :] = fluid[:, 1:-1, :] & (
        ~fluid[:, :-2, :] | ~fluid[:, 2:, :])
    regions = dict(
        wall_rows=wall_rows & fluid,
        interface=fluid & ~wall_rows & (np.abs(psi_f) <= 0.9),
        gas_bulk=fluid & ~wall_rows & (psi_f > 0.9),
        liq_bulk=fluid & ~wall_rows & (psi_f < -0.9))
    assert all(int((regions[a] & regions[b]).sum()) == 0
               for i, a in enumerate(regions) for b in list(regions)[i + 1:])
    assert int(sum(int(v.sum()) for v in regions.values())) == int(fluid.sum())

    fin = snapshot_fields(s, fluid)
    rows = []
    summary = {}
    for nm, sel in regions.items():
        summary[nm] = dict(nodes=int(sel.sum()))
        for refnm, ref in refs.items():
            mr0 = float(ref['rho_r'][sel].sum(dtype=np.float64))
            mb0 = float(ref['rho_b'][sel].sum(dtype=np.float64))
            mrho0 = float(ref['rho'][sel].sum(dtype=np.float64))
            mf0 = float(ref['fsum'][sel].sum(dtype=np.float64))
            mr1 = float(fin['rho_r'][sel].sum(dtype=np.float64))
            mb1 = float(fin['rho_b'][sel].sum(dtype=np.float64))
            mrho1 = float(fin['rho'][sel].sum(dtype=np.float64))
            mf1 = float(fin['fsum'][sel].sum(dtype=np.float64))
            rows.append([nm, refnm, int(sel.sum()),
                         mr0, mr1, mr1 - mr0,
                         mb0, mb1, mb1 - mb0,
                         mr0 + mb0, mr1 + mb1, (mr1 + mb1) - (mr0 + mb0),
                         mrho0, mrho1, mrho1 - mrho0,
                         mf0, mf1, mf1 - mf0])
            summary[nm][refnm] = dict(
                dMr=mr1 - mr0, dMb=mb1 - mb0,
                dMc=(mr1 + mb1) - (mr0 + mb0),
                dMrho=mrho1 - mrho0, dMf=mf1 - mf0)
    return rows, summary


# ---------------------------------------------------------------- analyze
def cmd_analyze(args):
    root = args.results_root
    reports = {}
    for tag in sorted(os.listdir(root)):
        rp = os.path.join(root, tag, 'case_report.json')
        if os.path.isfile(rp):
            with open(rp) as fh:
                reports[tag] = json.load(fh)

    be_rows = []
    for tag, r in sorted(reports.items()):
        f = r['drift_fits']
        be_rows.append([r['case'], r['arch'], tag, r['dims'][0],
                        r['steps'], r['nfluid'],
                        f['Mff']['slope_per_step'], f['Mff']['r2'],
                        f['Mc']['slope_per_step'], f['Mc']['r2'],
                        f['Mrho']['slope_per_step'], f['Mrho']['r2'],
                        f['Mff']['final_rel'], f['Mc']['final_rel'],
                        f['Mrho']['final_rel']])
    write_csv(os.path.join(root, 'backend_comparison.csv'),
              ['case', 'arch', 'tag', 'nx', 'steps', 'nfluid',
               'rate_Mff_per_step', 'r2_Mff', 'rate_Mc_per_step', 'r2_Mc',
               'rate_Mrho_per_step', 'r2_Mrho', 'final_rel_Mff',
               'final_rel_Mc', 'final_rel_Mrho'], be_rows)

    sc_rows = []
    for tag, r in sorted(reports.items()):
        if r['case'] == 'C0':
            f = r['drift_fits']
            sc_rows.append(['domain', tag, r['dims'][0], r['nfluid'],
                            f['Mc']['slope_per_step'],
                            f['Mrho']['slope_per_step'],
                            f['Mc']['final_rel'], f['Mrho']['final_rel']])
    for tag, r in sorted(reports.items()):
        if r['case'] == 'C3' and r['steps'] >= 20000:
            f = r['drift_fits']
            for st in ['5000', '10000', '20000']:
                if st in f['Mc']['drift_at']:
                    sc_rows.append(['horizon', tag, int(st), r['nfluid'],
                                    f['Mc']['slope_per_step'],
                                    f['Mrho']['slope_per_step'],
                                    f['Mc']['drift_at'][st],
                                    f['Mrho']['drift_at'][st]])
    write_csv(os.path.join(root, 'scaling_results.csv'),
              ['probe', 'tag', 'value', 'nfluid', 'rate_Mc_per_step',
               'rate_Mrho_per_step', 'Mc_at', 'Mrho_at'], sc_rows)

    # mechanism evidence block (facts only; the executor classification
    # lives in EXECUTION_REPORT.md, derived from these numbers)
    ev = {}
    for tag, r in sorted(reports.items()):
        ident = r.get('identity_stats') or {}

        def jget(nm, key):
            return (ident.get(nm) or {}).get(key)
        ev[tag] = dict(
            case=r['case'], arch=r['arch'], steps=r['steps'],
            J1=dict(mean_rel_M0=jget('J1_collision', 'mean_rel_M0'),
                    frac_pos=jget('J1_collision', 'frac_pos'),
                    max_abs_rel_M0=jget('J1_collision', 'max_abs_rel_M0')),
            J3=dict(mean_rel_M0=jget('J3_stream1', 'mean_rel_M0'),
                    frac_pos=jget('J3_stream1', 'frac_pos')),
            J6=dict(mean_rel_M0=jget('J6_macro', 'mean_rel_M0'),
                    frac_pos=jget('J6_macro', 'frac_pos')),
            J7=dict(mean_rel_M0=jget('J7_colortrans', 'mean_rel_M0'),
                    frac_pos=jget('J7_colortrans', 'frac_pos'),
                    max_abs_rel_M0=jget('J7_colortrans', 'max_abs_rel_M0')),
            exact_checks=dict(
                J0_fF_bitdiff=jget('J0_fF_bitdiff', 'max_abs'),
                J2_fill=jget('J2_fill', 'max_abs'),
                J4_bc=jget('J4_bc', 'max_abs'),
                J5_stream3copy=jget('J5_stream3copy', 'max_abs'),
                J8_colconsume=jget('J8_colconsume', 'max_abs'),
                J9_closure=jget('J9_closure_max', 'max_abs')),
            closure_fail_steps=r.get('closure_fail_steps'),
            fits=r['drift_fits'],
            final_deltas_rel=dict(
                d_fc=(r['final_views']['Mff'] - r['final_views']['Mr']
                      - r['final_views']['Mb']) / r['M0'],
                d_frho=(r['final_views']['Mff']
                        - r['final_views']['Mrho']) / r['M0'],
                d_crho=(r['final_views']['Mr'] + r['final_views']['Mb']
                        - r['final_views']['Mrho']) / r['M0']),
            first_material=r.get('first_material_residual_horizon'))
    write_json(os.path.join(root, 'summary.json'),
               dict(material_rel_threshold=MATERIAL_REL,
                    runs=sorted(reports.keys()), mechanism_evidence=ev))
    print('analyze: %d runs -> summary.json / backend_comparison.csv / '
          'scaling_results.csv' % len(reports), flush=True)
    return 0


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    r = sub.add_parser('run', help='run one audit case')
    r.add_argument('--case', required=True, choices=list(CASE_DEFAULTS))
    r.add_argument('--arch', default='gpu', choices=['gpu', 'cpu'])
    r.add_argument('--tag', required=True)
    r.add_argument('--dims', default=None,
                   help='nx,ny,nz override (C0 scaling probes)')
    r.add_argument('--steps', type=int, default=None)
    r.add_argument('--horizon-every', dest='horizon_every', type=int,
                   default=None)
    r.add_argument('--trace-first', dest='trace_first', type=int,
                   default=None)
    r.add_argument('--late-trace', dest='late_trace', default=None,
                   help='start:count, e.g. 9000:20')
    r.add_argument('--budget-ref-step', dest='budget_ref_step', type=int,
                   default=None)
    r.add_argument('--results-root', dest='results_root',
                   default=os.path.join(REPO_ROOT, 'results',
                                        'conservation_audit'))

    a = sub.add_parser('analyze', help='aggregate case reports')
    a.add_argument('--results-root', dest='results_root',
                   default=os.path.join(REPO_ROOT, 'results',
                                        'conservation_audit'))

    args = ap.parse_args()
    if args.cmd == 'analyze':
        sys.exit(cmd_analyze(args))

    # backend selection must precede solver import (module-level ti.init)
    os.environ['LBM_ARCH'] = args.arch
    sys.path.insert(0, REPO_ROOT)
    from lbm_solver_cg3d import ColorGradientSolver3D  # noqa: E402

    if args.late_trace:
        a, b = args.late_trace.split(':')
        args.late_trace = (int(a), int(b))
    if args.dims:
        args.dims = tuple(int(v) for v in args.dims.split(','))
    sys.exit(run_case(args, ColorGradientSolver3D))


if __name__ == '__main__':
    main()
