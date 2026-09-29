# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `CG3D-V1-INTEGRATION-004`
- **Status:** `COMPLETED`

## Summary

A thin cumulative V1 integration test was added at `tests/test_v1_integration.py`
and the seven requested validations were run on the frozen cumulative candidate.
All seven exited 0.

The new test answers the task's single question — whether the accepted Task 1–3
changes still work together on one codebase, including checkpoint/resume — with
one representative case per area instead of a copy of the three dedicated suites:

- **A. Runtime lifecycle.** Plain `import cg3d` / `import lbm_solver_cg3d`
  initialized nothing (no runtime, none of the six shared tables, no Taichi
  program); `cg3d.init_runtime()` is the call that starts the CPU runtime and is
  a no-op on the second call; `ensure_lattice_tables()` materialized all six
  tables with `M @ inv_M == I` (max |err| 3.0e-08) and is idempotent; a tiny
  8³ `ColorGradientSolver3D` constructed through that lifecycle in 0.14 s; the
  same instance round-tripped exactly through `cg3d.checkpoint`
  (`save_state`/`restore_state`/`read_meta`). No solver trajectory was run.
- **B. Periodic topology.** Via the accepted public `cg3d.label_periodic`: a
  wrapped y+z edge pair (cells (2,0,0)/(2,5,5) on 4×6×6) is **one component of
  size 2** at `conn=18, periodic_axes=(1,2)`, and stays **split** as soon as a
  required axis is not periodic (axes `(1,)`, `(2,)`, `()`).
- **C. Termination diagnostics.** The real `cg3d.protocol.run_hold` driving a
  small fake system (no LBM, no Taichi): legacy `reason` and
  `convergence["exit"]` are unchanged and mutually consistent, `termination`
  and `numerical_health` are present and consistent with the legacy reason, and
  the returned row is strictly JSON-serializable.
- **D. Combined API / import order.** The four accepted public paths coexist
  (`cg3d.init_runtime`, `cg3d.label_periodic`, `cg3d.protocol.run_hold`,
  `lbm_solver_cg3d.ColorGradientSolver3D`), and a **fresh process importing them
  in reverse order** (solver module first) reaches the same lifecycle state with
  no circular-import or runtime-order failure.

**As a whole: the cumulative Task 1–3 integration PASSED.** All seven requested
validations exited 0, including the pre-existing Task 1, Task 2, Task 3 and
checkpoint/resume regressions, which were re-run unmodified on the cumulative
base. No accepted interface regressed, so no failure has to be attributed to any
accepted task.

`LBM_ARCH=cpu` was used for every validation that touches Taichi; no GPU work
was performed.

## Executor Claims — Changes

- file / module: `tests/test_v1_integration.py` (new, 367 lines)
  - change: new cumulative integration test with sections A–D described above;
    CPU forced (`os.environ['LBM_ARCH'] = 'cpu'` set before any runtime
    initialization); one tiny 8³ solver instance is constructed, checkpointed
    and never stepped; a 6³ instance is constructed in a child process.
  - reason: the task asked for a thin cross-module validation of the accepted
    cumulative base, not for new production code and not for a duplicate of the
    Task 1–3 suites.

No other file was created, modified or deleted. `lbm_solver_cg3d.py`, `cg3d/`,
the existing tests, the drivers, documentation and controller/agent
infrastructure are untouched.

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| R1 add only `tests/test_v1_integration.py` | PASS | `git status` clean after commit; final commit touches exactly one file |
| R2 small and representative, existing tests keep deep coverage | PASS | 4 sections, 30 passing checks; new file 367 lines vs. the 115 / 283 / 363-line Task 1–3 suites; never imports or duplicates their suites or oracles |
| R3 no production code modified to make it pass | PASS | no production file in the commit; the only fix during authoring was inside the new test file (see Deviations) |
| R4 full cumulative command set run | PASS | all seven commands, see Validation |
| R5 project `lbm` environment used | PASS | `C:\Users\yangc\anaconda3\envs\lbm\python.exe` (3.10.21) invoked explicitly; the shell default `python` is the anaconda base env and was not used |
| R6 no GPU work | PASS | `LBM_ARCH=cpu` for all Taichi-touching commands; the new test forces it and asserts `current_cfg().arch == ti.cpu` |
| R7 no Level B Laplace / contact-angle validation | PASS | not run |
| R8 no full real-geometry pressure ladder | PASS | not run |
| R9 no scientific reinterpretation | PASS | report makes no physical claim; the `run_hold` case is a fake non-LBM system |
| R10 no accepted regression hidden by narrowing the command set | PASS | all seven requested commands run exactly as specified; all exit 0 |

Requested test-file content (task section "New Validation File"):
A runtime lifecycle PASS · B periodic topology (+ negative control) PASS ·
C termination diagnostics PASS · D combined-import / API sanity PASS.

## Validation

Environment for every command (recorded in each log's header):

- interpreter: `C:\Users\yangc\anaconda3\envs\lbm\python.exe`, Python 3.10.21
  (Anaconda), taichi 1.7.4, numpy 2.2.6, scipy 1.15.3 — matches
  `requirements.txt` pins.
- working directory: repository root of this worktree.
- `python` as spelled in the task's command list was resolved to the `lbm`
  interpreter above; the shell's default `python`
  (`C:\Users\yangc\anaconda3\python.exe`, the anaconda base env, where
  `import taichi` fails with `ModuleNotFoundError`) was therefore not used.
- the validation runner is `.agent_runtime/run_logs/run_validations.py`
  (scratch, gitignored); the seven commands were run sequentially, unmodified,
  and the published log of each is that run's stdout+stderr, verbatim.

### 1. New cumulative V1 integration test

- **Command:** `"C:\Users\yangc\anaconda3\envs\lbm\python.exe" tests/test_v1_integration.py`
  (task spelling: `python tests/test_v1_integration.py`)
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `ALL PASS`, 1.8 s of test wall time (2.5 s process elapsed).
  A1–A16, B1, B2(×3), C1–C5,
  D1–D5 all PASS. Decisive values: import side-effect free (`runtime_initialized
  False`, all six tables `None`, `prog is None`); `init_runtime` → `True` then
  `False`; live arch `Arch.x64` = CPU; tables shape-valid with `M @ inv_M` max
  |err| 2.98e-08; 8³ solver built in 0.14 s; checkpoint round-trip exact for
  `psi` and `f`; wrapped y+z edge → 1 component of size 2 at
  `conn=18, axes=(1,2)` and 2 components for axes `(1,)`, `(2,)`, `()`;
  `run_hold` → `reason=quasi-steady`, `steps=9`, `convergence['exit'] =
  {mode: sat, reason: quasi-steady}`, `termination.process_completed=True`,
  `numerical_health.finite=True` over 9 samples, row JSON-serializable
  (1206 bytes); reverse-order child process exit 0 and `CHILD_OK`.
- **Output / artifact reference:** `.agent_runtime/published_evidence/v1_integration.log`

### 2. Task 1 import-lifecycle regression (unchanged)

- **Command:** `"C:\Users\yangc\anaconda3\envs\lbm\python.exe" tests/test_import_no_taichi_init.py`
  (task spelling: `python tests/test_import_no_taichi_init.py`)
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** child 1 `IMPORT_OK` (import with `ti.init` trapped; `prog is
  None`), child 2 `BOUNDARY_OK` (`cg3d.runtime.init_runtime()` is the path that
  reaches `ti.init`). Elapsed 1.2 s.
- **Output / artifact reference:** `.agent_runtime/published_evidence/import_lifecycle.log`

### 3. Level A on the cumulative base

- **Command:** `LBM_ARCH=cpu "C:\Users\yangc\anaconda3\envs\lbm\python.exe" tests/run_level_a.py`
  (task spelling: `LBM_ARCH=cpu python tests/run_level_a.py`)
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** A1 `M @ inv_M == I` max |err| 2.98e-08; A2 uniform phase
  stationary (max |v| 0.0, psi deviation 0.0); A3 colour-mass conservation rel.
  drift 3.58e-07; A4 reservoir pins rho=1.05000 / psi=1.0000; A5 membrane
  blocks blue (min psi[x<9] = 1.000). `LEVEL A: ALL PASS`, 13 s (one 32³
  instance, CPU).
- **Output / artifact reference:** `.agent_runtime/published_evidence/level_a.log`

### 4. Post-processing / host-side logic regression

- **Command:** `"C:\Users\yangc\anaconda3\envs\lbm\python.exe" tests/test_postprocessing.py`
  (task spelling: `python tests/test_postprocessing.py`)
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `ALL PASS` (20 checks: 14 periodic-labelling cases incl. the
  conn=6/18/26 seam cases and non-periodic controls, 6 convergence-window
  cases, threshold recording). Elapsed 0.9 s.
- **Output / artifact reference:** `.agent_runtime/published_evidence/postprocessing.log`

### 5. Task 2 periodic-connectivity regression (unchanged)

- **Command:** `"C:\Users\yangc\anaconda3\envs\lbm\python.exe" tests/test_periodic_connectivity.py`
  (task spelling: `python tests/test_periodic_connectivity.py`)
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `ALL PASS`, including brute-force torus oracle agreement over
  252 mask × periodic-axis × connectivity combinations; wrapped edge/corner
  cases reproduce the accepted conn=6/18/26 semantics. Elapsed 1.2 s.
- **Output / artifact reference:** `.agent_runtime/published_evidence/periodic_connectivity.log`

### 6. Task 3 termination-diagnostics regression (unchanged)

- **Command:** `"C:\Users\yangc\anaconda3\envs\lbm\python.exe" tests/test_termination_diagnostics.py`
  (task spelling: `python tests/test_termination_diagnostics.py`)
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `ALL PASS` over the four accepted scenarios (quasi_steady,
  max_steps, umax_cap, nonfinite_observation): the legacy reason/convergence
  fields and the additive `termination` / `numerical_health` records stay
  consistent, and the row keeps exactly the legacy key set plus the two new
  records. Elapsed 0.6 s.
- **Output / artifact reference:** `.agent_runtime/published_evidence/termination_diagnostics.log`

### 7. Checkpoint / resume regression

- **Command:** `LBM_ARCH=cpu "C:\Users\yangc\anaconda3\envs\lbm\python.exe" tests/test_checkpoint_resume.py`
  (task spelling: `LBM_ARCH=cpu python tests/test_checkpoint_resume.py`)
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `ALL PASS`, 50.6 s. Part A (in-process, one 36×26×26
  instance): run-to-run atomics jitter up to 6.14e-06 in `psi`; interrupted vs.
  resumed trajectory differences 6.10e-08 … 3.58e-07, each within the test's
  tolerance `max(3× jitter, 1e-6)`; checkpoint round-trip exact for `f` and
  counters. Part B (real
  `run_pcs_cg3d.py` subprocesses, CPU): full 2-rung run vs. resume-from-rung0
  final `psi` max |Δ| 4.47e-07, rung-1 `s_nw` identical (|Δ| 0.00e+00),
  `resumed_from` recorded; B2 mid-rung `live.npz` resume max |Δ| 5.07e-07.
  Part C: cross-driver `ir --resume-plan new` branch ran phases
  `['drain', 'imbibe', 'imbibe']` and computed `s_nr`.
  Numerical stability: all reported trajectories stayed finite (part A
  explicitly asserts finiteness of f/psi/rho_r/rho_b/rho/v).
  Convergence status: this test is a trajectory-equivalence regression, not a
  convergence study — no rung in it claims physical convergence
  (`--qs-tol 0` cannot satisfy `abs(slope) < qs_tol`, so those rungs end on the
  step budget); process completion is not treated as convergence here either.
  Termination reason: the published log does not print per-rung reasons — by
  construction (`--qs-tol 0`) they are step-budget exits, but that is read off
  the test's arguments, not off the log. Physical metrics: none claimed.
- **Output / artifact reference:** `.agent_runtime/published_evidence/checkpoint_resume.log`

### Freeze confirmation

The validation run used the exact bytes that were committed: worktree blob and
`HEAD:tests/test_v1_integration.py` blob are both
`363e3b15ebe112bd5c8c262191f9bc60e3de88b1` (SHA-256 of the file,
`31043983a63f7a10d7a0c16f1ad9c6f0307d116fabdc0d6d028ad9f7655f2ef5`). The test
file was not edited after the validation run; the commit was created from the
tested working tree unchanged.

## Git / Source State

- base: `3e49087e195ac98b41000bc647b115c685daa71b` (accepted cumulative base
  containing CG3D-TAICHI-INIT-001, CG3D-PERIODIC-CONN-002,
  CG3D-CONVERGENCE-DIAG-003)
- head / commit: `645479e00217b1b50f6cd4ae5d833eda1661e84c`
  ("agent(CG3D-V1-INTEGRATION-004): add cumulative V1 integration test")
- branch: `agent-task/CG3D-V1-INTEGRATION-004`, pushed to `origin` as
  `3e49087..645479e` (no force-push, no history rewrite)
- changed-file list: `tests/test_v1_integration.py` (added). **Only that file
  changed** — confirmed by `git show --stat HEAD` / `git status --short` (clean
  after the commit).
- dirty files remaining: none tracked. Untracked-but-ignored scratch left by the
  requested validations: `results_pcs_cg3d/` (checkpoint/resume test outputs,
  ~22 MB, matches `.gitignore`; inspected — it holds only that test's own
  `ck_selftest/`, `ck_selftest_branch/` and `ck_selftest_geo.npz`, all created by
  this run, so no pre-existing or long-running simulation directory was reused,
  reset or overwritten), `tests_output/` (empty; the integration test deletes
  its scratch checkpoint), `.agent_runtime/`, `__pycache__/`.
- no merge was performed; `master` and the integration/control branches were not
  touched.

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| New integration test | `tests/test_v1_integration.py` (commit `645479e`) | cumulative Task 1–3 cross-module validation, sections A–D |
| Evidence bundle | `.agent_runtime/published_evidence/` (+ `manifest.json`, schema `v1`) | 7 validation logs + `integration_summary.json`, 8 files / 17,787 B total |
| Validation runner (scratch) | `.agent_runtime/run_logs/run_validations.py` | ran the seven commands, recorded exit codes and elapsed times |
| Machine-readable results | `.agent_runtime/published_evidence/integration_summary.json` | per-validation command, interpreter, exit code, elapsed s, PASS/FAIL; `all_passed: true` |

The published evidence bundle was created and self-checked: every file other
than `manifest.json` is listed exactly once with non-empty `path`, `kind` and
`description`; all files ≤ 1 MiB (largest 4,674 B) and the bundle ≤ 5 MiB; only
relative paths, no symlinks, no binary/simulation outputs. `provenance.json` was
not created (Controller-owned).

## Deviations

1. The test forces `os.environ['LBM_ARCH'] = 'cpu'` unconditionally (not
   `setdefault`), because this validation is CPU-only by task definition; the
   task explicitly asked for `LBM_ARCH=cpu` to be set before runtime
   initialization. A reviewer running the file with `LBM_ARCH=gpu` would still
   get a CPU run.
2. During authoring the new test was executed three times: (i) a first run whose
   log went to `.agent_runtime/run_logs/v1_integration.log`, which **failed one
   check** (A7) — the file used `current_cfg().arch is ti.cpu`, and Taichi's
   `Arch` is a pybind11 enum whose attribute access returns a new wrapper
   object, so identity is not stable; (ii) a run after changing that comparison
   (and A4's) to `==` (equality), which passed — that run printed to the console
   and was not kept as a log; (iii) the recorded run inside the validation set,
   whose log replaced the failed first one. The A7 failure was a defect in the
   new test file, not in production code; no production file was touched. The
   failed log was not retained — it is described here rather than published.
3. Before writing the test, two throwaway probe scripts were run from the OS
   temp directory (outside the repository, since only
   `tests/test_v1_integration.py` may change) to size the validation: one timed
   the import → `init_runtime` → `ensure_lattice_tables` → 8³-construct →
   checkpoint round-trip path (1.1 s total), the other printed Taichi's `Arch`
   identity semantics. They produced no repository artifact and were deleted;
   they are not part of the evidence bundle.
4. No other deviation from the requested command set, scope or evidence list.
   No passing command was re-run and no accepted regression was re-run to chase
   a passing result: each of the seven commands was executed once in the
   validation set, and its published log is that execution's verbatim output.
   The only repetition was the test-authoring iteration in (2), which happened
   before the candidate file was frozen and before any regression was run.

## Assumption / Modeling Impact

None. No physical model, numerical formulation, boundary or initial condition,
convergence/stopping criterion, contact-angle or wettability interpretation,
scientific claim scope or default physical parameter was changed. The `run_hold`
exercise in section C drives a fake, non-LBM system and asserts only the shape
and internal consistency of the reporting records; it makes no physical claim.
The "converged" flag it observes is the configured numerical stopping criterion
for that fake system, not physical equilibrium. The checkpoint/resume test is a
trajectory-equivalence regression, not a convergence study.

## Existing Evidence Potentially Affected

None. Production behaviour is byte-identical to the accepted base `3e49087`:
the only changed file is a new test, and all pre-existing regressions
(import lifecycle, Level A, post-processing, periodic connectivity, termination
diagnostics, checkpoint/resume) were re-run on the cumulative base and passed
unchanged. `results/baseline/` and the reported simulation results are
unaffected. No shared/copy-paired file was modified, so no synchronization with
the separate `LBM/source_code/taichi_LBM3D/2phase/` tree is required.

## Unresolved Issues / Human Decisions

- Whether the accepted Task 1–3 code is merged to `master` remains a human
  decision; this task only validated the cumulative candidate.
- Whether the pre-existing JIT-warm assumption recorded in `tests/README.md`
  (~5.5 min per solver instance) still describes this machine was not
  investigated: the two solver suites completed far faster than that (Level A
  13 s, checkpoint/resume 51 s), consistent with a warm Taichi offline cache
  from earlier accepted-task runs. This did not affect any verdict, and no
  cache-clearing or timing experiment was performed.
- Section C covers one representative quasi-steady case by task instruction;
  the full Task 3 semantic suite remains the source of deep coverage and was
  re-run as validation 6.

## Suggested Next Action

Controller/reviewer: review the frozen candidate `645479e` against
`tests/test_v1_integration.py` and the published evidence bundle
(`.agent_runtime/published_evidence/manifest.json`), then accept or reject
`CG3D-V1-INTEGRATION-004` for integration.
