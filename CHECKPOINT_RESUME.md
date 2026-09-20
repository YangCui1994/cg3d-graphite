# cg3d checkpoint / resume (PR-7, 2026-09-19)

Full-state save/restore for the 3D colour-gradient solver, layered on
the PR-5 protocol split: `cg3d/checkpoint.py` (format + restore),
`run_hold` resume bookkeeping, `--resume` / `--resume-plan` in
`run_pcs_cg3d.py` and `run_ir_cg3d.py`.  **No kernel is touched**;
`step()` has no RNG and no hidden history, so the only change to any
trajectory is floating-point atomics ordering (quantified below).

## What a checkpoint is

End-of-step solver state + a JSON meta block (how to rebuild the
system and where the run stood), one uncompressed npz (~0.85 GB at
200^3, ~1.2 GB at 228^3; write is a few seconds of GPU->host copy):

| saved                              | rebuilt instead                      |
|------------------------------------|--------------------------------------|
| `f (nx,ny,nz,19)`, `psi`, `rho_r`, `rho_b`, `rho`, `v`, `inj_r/b/m` (f64) | geometry, `mem_r/b`, `res_mask/psi/rho`, `psi_solid_f` — deterministic from (geo npz, capa, psi_solid, res_thick, pc_band) via `OpenSystem` |
| meta: driver/tag/config, `state`, `rung_idx`, `it_rung`, `it_total`, `plan_full`, `plan_remaining`, `m0`, `equil_s` | reservoir density targets — re-pinned by `set_ladder(d)` at the head of `run_hold` |

**The `F` trap** (bit us once, see tests): collision's `multiply_M`
reads `F`, NOT `f` (`lbm_solver_cg3d.py` `multiply_M`).  At end-of-step
`F == f` everywhere (streaming3 copies per fluid node; apply_reservoirs
writes both; both 0 on solids), so `F` is not stored — `restore_state`
refills it from the saved `f`.  Zeroing it corrupts the first
post-restore step (NaN within ~100 steps).

## Files written (always, both drivers)

```
<out>/ckpt/equil_end_it0000060.npz        after run_equil
<out>/ckpt/rung00_d0.0300_it0000140.npz   after each rung (index = global rung no.)
<out>/ckpt/rung01_...                     ...one per rung, NOT auto-pruned
<out>/ckpt/live.npz                       rolling mid-rung snapshot, --ckpt-every N
                                           (default 20000, 0 = off; N % --every == 0)
```

## Usage

```bash
# crash recovery — same config, same output dir, remaining rungs only:
python run_pcs_cg3d.py --geo ... --tag gx2c --ds ... \
    --resume results_pcs_cg3d/gx2c/ckpt/rung03_d0.0550_it0012340.npz
# (or --resume .../ckpt/live.npz for a mid-rung restart)

# branch / process switch — restored state as the STARTING configuration:
python run_ir_cg3d.py --geo ... --tag my_imbibe_branch \
    --ds-drain 0.074 --ds-imbibe 0.055 0.04 0.025 0.012 0.0 \
    --resume results_pcs_cg3d/gx2c/ckpt/rung03_....npz --resume-plan new
```

- `continue` (default): tag/geo/capa/psi-solid/res-thick/pc-band/ds
  must match the checkpoint exactly (mismatch = hard error — use `new`);
  `report_partial.json` rows for completed rungs are reloaded so the
  final report covers the whole ladder; the sentry baseline `m0` and
  `equil_s` come from the checkpoint meta.  Refuses to resume from a
  checkpoint OLDER than the on-disk report progress (silent rewind is
  exactly the mistake this guards against — rewind-and-redo goes
  through `new` with a fresh tag, or manual cleanup).
- `new`: build the system from THIS invocation's CLI args (geo shape
  must match the checkpoint; `capa`/`psi-solid` may legitimately differ
  — that is the sensitivity-branch use case), skip equilibration,
  zero the flux counters (report fluxes are relative to the branch
  point), run the CLI plan from the restored state.  Resuming an ir
  run from a **pcs** checkpoint this way is the supported
  "drain elsewhere, imbibe here" pattern.
- Mid-rung resume replays the interrupted rung from `it_rung`:
  convergence windows start empty, so the replayed rung exits no
  EARLIER than the uninterrupted one would have (bias is toward longer
  rungs, never premature quasi-steady).
- Frame naming: fresh runs keep the legacy per-rung-local numbering;
  resumed runs switch to global step numbers (rung offset added), so
  replayed rungs never overwrite pre-crash frames.

## Validation (2026-09-19, LBM_ARCH=cpu, 36x26x26 synthetic geo)

`python tests/test_checkpoint_resume.py` — all pass:

- **A same-instance**: save->restore roundtrip bitwise-exact
  (fields + f64 counters).  Trajectory equivalence: restored 100-step
  continuation vs uninterrupted run, against a run-to-run control
  (same state rerun twice): `|A-B|` for every field is BELOW the
  control's own atomics jitter (e.g. psi 3.6e-07 vs jitter 8.5e-06).
  Counter continuation within the control's f64-atomics spread.
- **B cross-process, rung-end**: full 2-rung run vs
  resume-from-rung00-end: final psi max|d| = 2.8e-07, rung-1 `s_nw`
  row matches to <1e-09 (often 0.0).
- **B2 cross-process, mid-rung**: resume from `live.npz` after a
  simulated crash during rung 1: completes, final psi max|d| = 3.3e-07.
- **C cross-driver branch**: ir `--resume-plan new` from a pcs
  rung00 checkpoint: plan `[drain, imbibe, imbibe]` runs, `s_nr` and
  cluster analysis produced.
- Regression: `tests/run_level_a.py` ALL PASS (solver untouched apart
  from enabling Taichi `offline_cache` for the cpu branch).

## GPU validation (2026-09-20, arch=cuda, after the PR-6 full-scale
## rerun pair completed)

Same suite, `LBM_ARCH=gpu` — ALL PASS:

- **A**: restored 100-step continuation vs uninterrupted run: every
  field `|A-B| <= 4.2e-07`, again BELOW the GPU run-to-run atomics
  jitter (f 4.8e-07, psi 1.8e-05).  Roundtrip bitwise-exact.
- **B cross-process, rung-end**: final psi max|d| = 7.2e-07; rung-1
  `s_nw` row identical (0.0).
- **B2 cross-process, mid-rung** (`live.npz`): final psi
  max|d| = 7.2e-07.
- **C cross-driver branch** (ir `--resume-plan new` from a pcs
  checkpoint): plan `[drain, imbibe, imbibe]` ran, `s_nr` produced.

GPU/CPU conclusions agree: resume reproduces the uninterrupted
trajectory to the reproducibility limit of the arch (f32 atomics
ordering in streaming1), with no arch-specific behaviour.

## Limitations / notes

- Cross-ARCH resume (checkpoint written on cpu, restored on cuda, or
  vice versa) is not validated; stay on one arch per run chain.
- Rung-end checkpoints accumulate (~1.2 GB each at 228^3); delete old
  ones manually — nothing auto-prunes.  `live.npz` is self-bounded.
- A checkpoint is only as good as its trajectory context: resuming
  with `continue` assumes the geo npz file at the recorded path is
  unchanged (byte-identical rebuild of masks/membranes).
- GPU runs pay one device->host copy per checkpoint write (~1.2 GB,
  seconds at PCIe speeds) — cadence `--ckpt-every` is the knob.
