# PROVENANCE — BI-CONSERVATION-AUDIT-001

## Binding

- **Task:** BI-CONSERVATION-AUDIT-001 (diagnostic solver conservation
  audit; contract
  `.agent/episodes/bilateral-imbibition-v0.1/CONSERVATION_AUDIT_CONTRACT.md`)
- **Product base:** `5e679d8d99d338f9ab28565c636f021a0f9211b2` (V2
  candidate, externally PASSed with mandatory-audit condition R-V2-3)
- **Product branch:** `agent-task/BI-CONSERVATION-AUDIT-001`
- **Final candidate:** see `git rev-parse HEAD` of this branch (recorded
  in REVIEW_REQUEST.md; all artifacts in this directory are committed on
  that branch and hashed in MANIFEST.json)

## Producer

- **Driver:** `tests/conservation_audit.py`
  - SHA256 at run time == SHA256 in the final candidate (verified via
    `MANIFEST.json:driver`; the file was not edited after the runs)
  - Runs the production kernels (`collision`, `F.fill(0)`, `streaming1`,
    `Boundary_condition`, `streaming3`, `Boundary_condition_psi`) of
    `lbm_solver_cg3d.py` **unmodified** (base blob identity; the solver
    file is byte-identical to the V2 candidate), in the exact `step()`
    order, with float64 host reductions between kernels. Non-traced
    steps call the production `step()` itself.
- **Batch driver:** `results/conservation_audit/run_batch.sh` (exact
  per-run command lines, sequential, one process per case/backend).

## Environment

- Windows 11, conda env `lbm`: python 3.10.21, taichi 1.7.4, numpy 2.2.6
  (per-run detail in each `<tag>/prov.json`)
- Backends: `LBM_ARCH=gpu` -> taichi cuda (RTX 5080); `LBM_ARCH=cpu` ->
  taichi cpu. Set before solver import (module-level `ti.init`).
- No solver physics parameters were changed relative to V2:
  `niu_l=niu_g=0.1`, `CapA=0.06`, `psi_solid=-0.68` (C2/C3 via
  `set_psi_solid_field`), no force, no membranes, no reservoirs, all
  `bc_*` flags at the periodic default.

## Runs (all exit code 0; per-run argv/env/timing in `<tag>/prov.json`)

| tag | case | arch | dims | steps | command (from repo root) |
|---|---|---|---|---|---|
| C0_24_gpu | C0 | gpu | 24,24,24 | 5000 | `python tests/conservation_audit.py run --case C0 --arch gpu --tag C0_24_gpu` |
| C0_16_gpu | C0 | gpu | 16,16,16 | 5000 | same + `--dims 16,16,16` |
| C0_32_gpu | C0 | gpu | 32,32,32 | 5000 | same + `--dims 32,32,32` |
| C1_gpu | C1 | gpu | 64,24,24 | 10000 | `--case C1 --arch gpu` |
| C2_gpu | C2 | gpu | 32,46,6 | 10000 | `--case C2 --arch gpu` |
| C3_gpu | C3 | gpu | 126,46,6 | 20000 | `--case C3 --arch gpu` |
| C0_24_cpu | C0 | cpu | 24,24,24 | 5000 | `--case C0 --arch cpu` |
| C1_cpu | C1 | cpu | 64,24,24 | 5000 | `--case C1 --arch cpu --steps 5000 --late-trace 4900:20` |
| C2_cpu | C2 | cpu | 32,46,6 | 5000 | `--case C2 --arch cpu --steps 5000 --late-trace 4900:20` |
| C3_cpu | C3 | cpu | 126,46,6 | 10000 | `--case C3 --arch cpu --steps 10000 --late-trace 9000:20 --budget-ref-step 1000` |

Aggregate: `python tests/conservation_audit.py analyze` (writes
`summary.json`, `backend_comparison.csv`, `scaling_results.csv`).
Console logs: `logs/<tag>.log`, `logs/analyze.log`; shell-level exit
codes of every batch member: `logs/batch_exit_codes.log` (all exit=0).

## Revision 2 (attempt-2 candidate)

Attempt-1 fresh review returned CHANGES_REQUESTED (findings B1-B5,
N1-N8; `.agent_runtime/BI-CONSERVATION-AUDIT-001/REVIEW.md`, archived as
`REVIEW_ATTEMPT_1.md` in the evidence publication). The revision commit
on this branch changes text and derived artifacts only:
`EXECUTION_REPORT.md` / `PROVENANCE.md` rewrites, regenerated
`late_window_identities.json` (all 10 runs, committed generator
`make_late_window.py`), new `inv_m_colsum_check.py/.json` (executor-side
reproduction of the attempt-1 reviewer's `inv_M` zeroth-column defect),
`logs/batch_exit_codes.log`, `figures/` (script + 4 SVGs), regenerated
`MANIFEST.json`. **No simulation was re-run; no raw evidence file
(per-run CSVs/npz/prov.json/logs) was modified.**

## Derived-artifact generators (attempt-1 review N3/N8)

- `results/conservation_audit/make_late_window.py`
  -> `late_window_identities.json` (10 runs)
- `results/conservation_audit/inv_m_colsum_check.py`
  -> `inv_m_colsum_check.json`
- `results/conservation_audit/figures/ca_make_figs.py` -> 4 SVGs
- `tests/conservation_audit.py` (driver; run producer)
- `results/conservation_audit/run_batch.sh` (batch sequence)
Their SHA256s are recorded in `MANIFEST.json:files`; the run producer
hash is additionally bound in `MANIFEST.json:driver`.

## Audit-only changes relative to base `5e679d8`

- added `tests/conservation_audit.py`
- added `results/conservation_audit/**` (this evidence tree)
- no other file touched; `lbm_solver_cg3d.py`, `cg3d/**`, V1/V1b/V1c/V2
  sources and results, and the episode runner are byte-identical to the
  base (reviewer to verify via `git diff --stat 5e679d8 <candidate>`).

## Caveats

- GPU runs use taichi atomic float adds in `streaming1`/colour
  accumulation; run-to-run bit-exact reproducibility is not guaranteed
  (production property). All identities reported here are from the
  committed single runs; the backend matrix (CPU vs GPU) bounds the
  realization dependence.
- The per-run `prov.json` `git.head` records `5e679d8` with the then
  uncommitted driver (`git.dirty` lists `tests/conservation_audit.py`,
  `results/conservation_audit/`); the driver bytes are identical to the
  final candidate by SHA256 (see MANIFEST.json), satisfying contract
  section 18's producer-ancestor clause.
