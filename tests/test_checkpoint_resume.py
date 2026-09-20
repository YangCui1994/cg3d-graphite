"""PR-7 checkpoint/resume validation (run from repo root):

  python tests/test_checkpoint_resume.py        (exit 0 = pass)

CPU arch (LBM_ARCH=cpu) so it never touches the GPU a batch run is
using.  JIT RULE respected: the in-process part uses ONE solver
instance; the cross-process parts run the real drivers as subprocesses
(one fresh instance each, exactly like a production resume).

Parts:
  A  roundtrip fidelity + same-instance trajectory equivalence with a
     run-to-run jitter control (restore t=0 checkpoint, rerun, compare)
  B  driver end-to-end: full 2-rung pcs run vs resume-from-rung0-end
     into the SAME output dir; final psi + ladder rows must match the
     uninterrupted trajectory up to atomics jitter
  B2 mid-rung crash recovery: resume from live.npz, run completes
  C  cross-driver branch: ir --resume-plan new from a pcs checkpoint
"""
import os
import subprocess
import sys

os.environ.setdefault('LBM_ARCH', 'cpu')   # precede the solver import;
                                            # LBM_ARCH=gpu for GPU validation

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
os.chdir(REPO)

import numpy as np                                          # noqa: E402
from cg3d import OpenSystem, checkpoint                     # noqa: E402

FAIL = []


def check(name, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + name
          + ('  ' + detail if detail else ''), flush=True)
    if not cond:
        FAIL.append(name)


def maxabs(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def make_geo(path, nx=36, ny=26, nz=26, seed=0):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rng = np.random.default_rng(seed)
    solid = np.zeros((nx, ny, nz), dtype=np.int8)
    for _ in range(10):
        c = rng.integers([13, 4, 4], [nx - 12, ny - 4, nz - 4])
        r = rng.uniform(2.0, 3.5)
        ii, jj, kk = np.ogrid[:nx, :ny, :nz]
        solid[(ii - c[0])**2 + (jj - c[1])**2 + (kk - c[2])**2 < r**2] = 1
    np.savez(path, solid=solid,
             meta=np.array([f'synthetic seed={seed}']))
    return solid


# ------------------------------------------------------------------
# A: in-process, ONE instance
# ------------------------------------------------------------------
def part_a():
    geo_path = 'results_pcs_cg3d/ck_selftest_geo.npz'
    solid = make_geo(geo_path)
    print(f'[A] geo porosity (interior) '
          f'{1.0 - solid[12:-12].mean():.3f}', flush=True)
    os.makedirs('results_pcs_cg3d/ck_selftest', exist_ok=True)
    ck0 = 'results_pcs_cg3d/ck_selftest/ck_a_it0.npz'
    ck100 = 'results_pcs_cg3d/ck_selftest/ck_a_it100.npz'

    sys_ = OpenSystem(geo_path, 0.06, -0.75, res_thick=3, pc_band=2)
    s = sys_.s
    # equilibrate the initial sharp interface at d=0 first (the real
    # protocol's run_equil) — driving an unrelaxed interface NaNs fast
    sys_.set_ladder(0.0)
    for _ in range(150):
        s.step()
    print(f'[A] post-equil max|v|={np.abs(s.v.to_numpy()).max():.2e}',
          flush=True)
    sys_.set_ladder(0.05)

    checkpoint.save_state(s, ck0, dict(driver='pcs', tag='ck_selftest',
                                       state='equil_end', it_total=150))
    meta0 = checkpoint.read_meta(ck0)
    check('A meta roundtrip', meta0['state'] == 'equil_end'
          and meta0['format'] == 'cg3d-ckpt-v1')

    def snap():
        return dict(f=s.f.to_numpy(), psi=s.psi.to_numpy(),
                    rho_r=s.rho_r.to_numpy(), rho_b=s.rho_b.to_numpy(),
                    rho=s.rho.to_numpy(), v=s.v.to_numpy(),
                    inj=(float(s.inj_r[None]), float(s.inj_b[None]),
                         float(s.inj_m[None])))

    for it in range(1, 201):
        s.step()
        if it == 100:
            checkpoint.save_state(s, ck100, dict(
                driver='pcs', tag='ck_selftest', state='mid_rung',
                it_total=100, it_rung=100, d=0.05))
            print(f'[A] drive it=100 max|v|='
                  f'{np.abs(s.v.to_numpy()).max():.2e}', flush=True)
    A = snap()
    check('A trajectory stays finite',
          all(np.isfinite(A[k]).all() for k in
              ('f', 'psi', 'rho_r', 'rho_b', 'rho', 'v')))

    # jitter control: restore the t=0 state, rerun 200 steps
    checkpoint.restore_state(s, ck0)
    for _ in range(200):
        s.step()
    A2 = snap()
    J = {k: maxabs(A[k], A2[k]) for k in
         ('f', 'psi', 'rho_r', 'rho_b', 'rho', 'v')}
    print(f'[A] run-to-run jitter (atomics): '
          + ', '.join(f'{k}={v:.2e}' for k, v in J.items()), flush=True)

    # resumed trajectory: restore the t=100 state, run the last 100
    meta100 = checkpoint.restore_state(s, ck100)
    check('A restore returns meta', meta100['it_total'] == 100)
    dat = np.load(ck100)
    check('A roundtrip fidelity f',
          np.array_equal(s.f.to_numpy(), dat['f']))
    check('A roundtrip fidelity counters',
          (float(s.inj_r[None]), float(s.inj_b[None]),
           float(s.inj_m[None])) == (float(dat['inj_r']),
                                     float(dat['inj_b']),
                                     float(dat['inj_m'])))
    for _ in range(100):
        s.step()
    B = snap()

    for k in ('f', 'psi', 'rho_r', 'rho_b', 'rho', 'v'):
        d = maxabs(A[k], B[k])
        tol = max(3.0 * J[k], 1e-6)
        check(f'A trajectory {k}', d <= tol,
              f'|A-B|={d:.2e} tol={tol:.2e} (jitter {J[k]:.2e})')
    # counters accumulate via f64 atomics (order-dependent); compare
    # against the jitter-control difference, not an absolute threshold
    d_ab = [abs(a - b) / max(abs(a), 1e-30)
            for a, b in zip(A['inj'], B['inj'])]
    d_aa = [abs(a - b) / max(abs(a), 1e-30)
            for a, b in zip(A['inj'], A2['inj'])]
    check('A counters continue', all(x <= max(3 * y, 1e-12)
                                     for x, y in zip(d_ab, d_aa)),
          f'|A-B|={["%.2e" % v for v in d_ab]} '
          f'jitter={["%.2e" % v for v in d_aa]}')
    del s


# ------------------------------------------------------------------
# B / B2 / C: real drivers as subprocesses
# ------------------------------------------------------------------
def run_driver(args, timeout=1200):
    env = dict(os.environ)                  # inherit LBM_ARCH override
    p = subprocess.run([sys.executable] + args, cwd=REPO, env=env,
                       capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        print('--- driver stdout ---\n' + p.stdout[-3000:])
        print('--- driver stderr ---\n' + p.stderr[-3000:], flush=True)
    return p


def truncate_to_crash(tag, n_rows, keep_rungs):
    """Rebuild on disk the state a real crash leaves: report_partial
    holding only the completed rungs' rows, no final outputs, no
    checkpoints beyond the crash point (live.npz is kept)."""
    import json
    out = os.path.join('results_pcs_cg3d', tag)
    with open(os.path.join(out, 'report_partial.json'),
              encoding='utf-8') as f:
        rep = json.load(f)
    rep['ladder'] = rep['ladder'][:n_rows]
    with open(os.path.join(out, 'report_partial.json'), 'w',
              encoding='utf-8') as f:
        json.dump(rep, f)
    for fn in ('final.npz', 'report.json'):
        p = os.path.join(out, fn)
        if os.path.exists(p):
            os.remove(p)
    ck = os.path.join(out, 'ckpt')
    for fn in os.listdir(ck):
        if fn.startswith('rung') and int(fn[4:6]) >= keep_rungs:
            os.remove(os.path.join(ck, fn))


def part_b():
    geo = 'results_pcs_cg3d/ck_selftest_geo.npz'
    common = ['--geo', geo, '--res-thick', '3', '--equil-steps', '60',
              '--min-steps', '30', '--max-steps', '80', '--qs-window',
              '30', '--qs-tol', '0', '--every', '10', '--dump-every',
              '40', '--ckpt-every', '40']
    ds = ['--ds', '0.03', '0.05']

    p = run_driver(['run_pcs_cg3d.py', '--tag', 'ck_selftest']
                   + common + ds)
    check('B full run exit 0', p.returncode == 0)
    if p.returncode != 0:
        return
    import json
    psi_full = np.load('results_pcs_cg3d/ck_selftest/final.npz')['psi']
    with open('results_pcs_cg3d/ck_selftest/report.json',
              encoding='utf-8') as f:
        rep_full = json.load(f)

    ck_dir = 'results_pcs_cg3d/ck_selftest/ckpt'
    rung0 = sorted(x for x in os.listdir(ck_dir) if x.startswith('rung00'))
    check('B rung00 ckpt exists', len(rung0) == 1, str(rung0))
    check('B live ckpt exists', os.path.exists(os.path.join(ck_dir,
                                                            'live.npz')))

    # crash after rung 0 completed: keep row 0 + rung00 ckpt only
    truncate_to_crash('ck_selftest', n_rows=1, keep_rungs=1)
    p = run_driver(['run_pcs_cg3d.py', '--tag', 'ck_selftest',
                    '--resume', os.path.join(ck_dir, rung0[0])]
                   + common + ds)
    check('B resume exit 0', p.returncode == 0)
    if p.returncode != 0:
        return
    psi_res = np.load('results_pcs_cg3d/ck_selftest/final.npz')['psi']
    d = maxabs(psi_full, psi_res)
    check('B resumed final psi matches', d < 1e-4, f'max|d|={d:.2e}')
    with open('results_pcs_cg3d/ck_selftest/report.json',
              encoding='utf-8') as f:
        rep_res = json.load(f)
    check('B ladder has 2 rows', len(rep_res['ladder']) == 2)
    d1 = abs(rep_full['ladder'][1]['s_nw'] - rep_res['ladder'][1]['s_nw'])
    check('B rung1 s_nw matches', d1 < 1e-7, f'|d|={d1:.2e}')
    check('B resumed_from recorded', rep_res.get('resumed_from')
          is not None)

    # B2: crash DURING rung 1 -> live.npz is mid-rung-1, row 0 on disk
    truncate_to_crash('ck_selftest', n_rows=1, keep_rungs=1)
    p = run_driver(['run_pcs_cg3d.py', '--tag', 'ck_selftest',
                    '--resume', os.path.join(ck_dir, 'live.npz')]
                   + common + ds)
    check('B2 live resume exit 0', p.returncode == 0)
    if p.returncode == 0:
        with open('results_pcs_cg3d/ck_selftest/report.json',
                  encoding='utf-8') as f:
            rep_live = json.load(f)
        check('B2 ladder has 2 rows', len(rep_live['ladder']) == 2)
        d = maxabs(psi_full,
                   np.load('results_pcs_cg3d/ck_selftest/final.npz')['psi'])
        check('B2 final psi matches', d < 1e-4, f'max|d|={d:.2e}')


def part_c():
    geo = 'results_pcs_cg3d/ck_selftest_geo.npz'
    ck = 'results_pcs_cg3d/ck_selftest/ckpt'
    rung0 = sorted(x for x in os.listdir(ck) if x.startswith('rung00'))[0]
    p = run_driver(['run_ir_cg3d.py', '--tag', 'ck_selftest_branch',
                    '--geo', geo, '--res-thick', '3',
                    '--min-steps', '30', '--max-steps', '80',
                    '--qs-window', '30', '--qs-tol', '0', '--every',
                    '10', '--dump-every', '0',
                    '--resume', os.path.join(ck, rung0),
                    '--resume-plan', 'new',
                    '--ds-drain', '0.05', '--ds-imbibe', '0.025', '0.0'])
    check('C ir branch exit 0', p.returncode == 0)
    if p.returncode != 0:
        return
    import json
    with open('results_pcs_cg3d/ck_selftest_branch/report.json',
              encoding='utf-8') as f:
        rep = json.load(f)
    phases = [r.get('phase') for r in rep['ladder']]
    check('C branch plan ran', phases == ['drain', 'imbibe', 'imbibe'],
          str(phases))
    check('C s_nr computed', 's_nr' in rep)


if __name__ == '__main__':
    part_a()
    part_b()
    part_c()
    print(f'\n{"ALL PASS" if not FAIL else "FAILURES: " + ", ".join(FAIL)}',
          flush=True)
    sys.exit(1 if FAIL else 0)
