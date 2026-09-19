"""cg3d.checkpoint — full-state save / restore for the 3D CG solver (PR-7).

A checkpoint is the complete end-of-step state of ColorGradientSolver3D
plus a JSON meta block recording how to rebuild the surrounding
OpenSystem and where the run stood (driver, rung index, remaining plan,
global step count).

State saved (26 f32 per node + 3 f64 scalars, ~0.85 GB at 200^3 /
~1.2 GB at 228^3, uncompressed npz for write speed):

  f (nx,ny,nz,19)  distribution populations — the full microstate
  psi, rho_r, rho_b, rho (nx,ny,nz)  colour / mass fields
  v (nx,ny,nz,3)  macroscopic velocity (collision reads it directly)
  inj_r, inj_b, inj_m ()  cumulative reservoir flux counters (f64)

Deliberately NOT saved:
  F  redundant at end-of-step (streaming3 copies F -> f on every fluid
    node; apply_reservoirs writes both; both are 0 on solid nodes), so
    restore reconstructs it from the saved f.  NOTE: F is NOT scratch —
    collision's multiply_M reads F, zeroing it corrupts the first
    post-restore step (caught by tests/test_checkpoint_resume.py).
  rhor, rhob  per-step colour-mass accumulators, zeroed at restore
    (zero at end-of-step for every fluid node; solid-node values are
    write-only dead weight).
  solid / mem_r / mem_b / res_mask / res_psi / res_rho / psi_solid_f —
    rebuilt deterministically by OpenSystem from (geo npz, capa,
    psi_solid, res_thick, pc_band); res_rho targets are re-pinned by
    set_ladder(d) at the head of run_hold.

step() has no RNG and no hidden history, so a restored run continues
the interrupted trajectory up to floating-point atomics ordering in
streaming1 (tests/test_checkpoint_resume.py quantifies this against a
run-to-run control).
"""
import datetime
import json

import numpy as np

FORMAT = 'cg3d-ckpt-v1'
_STATE_ARRAYS = ('f', 'psi', 'rho_r', 'rho_b', 'rho', 'v')


def save_state(s, path, meta):
    """Dump the solver's end-of-step state + meta dict to `path` (npz).
    Host-side; call OUTSIDE the timestep loop (it pulls ~26 f32/node
    off the device)."""
    m = dict(meta)
    m['format'] = FORMAT
    m['saved_utc'] = datetime.datetime.utcnow().isoformat(
        timespec='seconds')
    m['shape'] = [s.nx, s.ny, s.nz]
    np.savez(
        path,
        f=s.f.to_numpy(),
        psi=s.psi.to_numpy(),
        rho_r=s.rho_r.to_numpy(),
        rho_b=s.rho_b.to_numpy(),
        rho=s.rho.to_numpy(),
        v=s.v.to_numpy(),
        inj_r=np.float64(float(s.inj_r[None])),
        inj_b=np.float64(float(s.inj_b[None])),
        inj_m=np.float64(float(s.inj_m[None])),
        meta_json=np.array(json.dumps(m)))


def restore_state(s, path):
    """Restore a saved state into an ALREADY-CONFIGURED solver instance
    (matching shape; geometry/membranes/reservoirs as built by
    OpenSystem).  Returns the meta dict.  Scratch fields are zeroed to
    the post-init state; reservoir density targets are NOT touched —
    call set_ladder(d) (run_hold does) before stepping."""
    dat = np.load(path, allow_pickle=False)
    meta = json.loads(str(dat['meta_json']))
    if meta.get('format') != FORMAT:
        raise ValueError(f'{path}: format {meta.get("format")!r} != '
                         f'{FORMAT!r}')
    shape = tuple(meta['shape'])
    if shape != (s.nx, s.ny, s.nz):
        raise ValueError(f'{path}: checkpoint shape {shape} != solver '
                         f'{(s.nx, s.ny, s.nz)}')
    with dat:
        f_np = np.ascontiguousarray(dat['f'], dtype=np.float32)
        s.f.from_numpy(f_np)
        # collision reads F (multiply_M); at end-of-step F == f, so the
        # saved f doubles as the restored F
        s.F.from_numpy(f_np)
        s.psi.from_numpy(
            np.ascontiguousarray(dat['psi'], dtype=np.float32))
        s.rho_r.from_numpy(
            np.ascontiguousarray(dat['rho_r'], dtype=np.float32))
        s.rho_b.from_numpy(
            np.ascontiguousarray(dat['rho_b'], dtype=np.float32))
        s.rho.from_numpy(
            np.ascontiguousarray(dat['rho'], dtype=np.float32))
        s.v.from_numpy(
            np.ascontiguousarray(dat['v'], dtype=np.float32))
        s.inj_r[None] = float(dat['inj_r'])
        s.inj_b[None] = float(dat['inj_b'])
        s.inj_m[None] = float(dat['inj_m'])
    s.rhor.fill(0.0)
    s.rhob.fill(0.0)
    return meta


def read_meta(path):
    """Meta-only read (cheap: npz member access is lazy)."""
    with np.load(path, allow_pickle=False) as dat:
        return json.loads(str(dat['meta_json']))


def zero_counters(s):
    """Reset the cumulative reservoir counters (branch runs: report
    fluxes relative to the branch point instead of the original t=0)."""
    s.inj_r[None] = 0.0
    s.inj_b[None] = 0.0
    s.inj_m[None] = 0.0


def check_continue(args, meta, driver):
    """'continue'-mode resume validation: this invocation must reproduce
    the checkpointed run's config exactly (same tag / geo / parameters);
    a mismatch is almost certainly a mistake — branching with different
    parameters is what --resume-plan new is for.  The ladder (plan)
    itself is checked by the driver (flat ds vs phase-tagged)."""
    if meta.get('driver') != driver:
        raise SystemExit(f'checkpoint was written by driver '
                         f'{meta.get("driver")!r}, not {driver!r}')
    if args.tag != meta['tag']:
        raise SystemExit(f'--tag {args.tag!r} != checkpoint tag '
                         f'{meta["tag"]!r}: continue-mode resumes write '
                         f'into the ORIGINAL run\'s output dir; use '
                         f'--resume-plan new to start a different run')
    for key in ('geo', 'capa', 'psi_solid', 'res_thick', 'pc_band'):
        cli, ck = getattr(args, key), meta[key]
        if cli != ck:
            raise SystemExit(
                f'--{key.replace("_", "-")} {cli!r} != checkpoint '
                f'{ck!r} — a continue-mode resume must match the '
                f'checkpointed config; use --resume-plan new to branch '
                f'with different parameters')
