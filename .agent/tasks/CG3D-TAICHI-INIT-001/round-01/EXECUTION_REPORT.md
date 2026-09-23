# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `CG3D-TAICHI-INIT-001`
- **Status:** `COMPLETED`

## Summary

Importing `lbm_solver_cg3d` no longer initializes the Taichi runtime: the
import-time `ti.init(...)` block and the import-time allocation of the six
shared lattice/MRT fields are gone. Both now happen behind one explicit
project boundary, `cg3d.runtime.init_runtime()`, which the solver reaches
through `lbm_solver_cg3d.ensure_lattice_tables()` called from
`ColorGradientSolver3D.__init__`. Everything downstream (direct solver
users, `cg3d.OpenSystem`, the two drivers) therefore passes through the
boundary before any field or kernel is used, and no caller needed a
scientific/numerical change.

The work is limited to lifting runtime initialization out of import: no
kernel, formula, lattice constant, table value, default parameter, or step
order was touched. All requested validations ran CPU-only and passed; the
requested CPU smoke produced values bit-identical to the same test run
against the pre-change solver on this machine.

## Executor Claims — Changes

- `cg3d/runtime.py` (new, 46 lines):
  - change: `init_runtime()` — idempotent, explicit start of the Taichi
    runtime; `select_arch()` reproduces the `LBM_ARCH` contract ('cpu' →
    CPU, anything else → GPU default); `ti.init(..., offline_cache=True)`;
    plus `is_runtime_initialized()` for observability.
  - reason: requirement 3 asks for one clear project-level explicit
    initialization path. Idempotence is not decoration: on Taichi 1.7.4 a
    second `ti.init()` returns normally but re-creates the program, after
    which fields of the first program raise
    `AttributeError: 'NoneType' object has no attribute '_snode'`
    (measured, see Artifacts/`probe-duplicate-ti-init.txt`). Without the
    guard, a second solver in the same process would silently break the
    first one's fields.
- `lbm_solver_cg3d.py`:
  - change: removed the module-level `ti.init(...)` block; added
    `from cg3d.runtime import init_runtime`; the six shared tables
    (`e`, `e_f`, `w`, `LR`, `M`, `inv_M`) are now `None` placeholders,
    created and filled inside `_init_lattice_tables()`; new
    `ensure_lattice_tables()` calls `init_runtime()` and then
    `_init_lattice_tables()`; `ColorGradientSolver3D.__init__` calls
    `ensure_lattice_tables()` as its first statement
    (`lbm_solver_cg3d.py:244`).
  - reason: requirements 1–4. Field creation cannot be left at import:
    Taichi 1.7.4 raises `TaichiRuntimeError: Cannont create field, maybe
    you forgot to call ti.init() first?` for `ti.field()` before
    `ti.init()` (measured), so the tables are exactly the "minimum
    required runtime-dependent allocation" requirement 2 anticipates.
    Creating them inside the boundary after `ti.init()` keeps the original
    order of Taichi operations (`ti.init` → create fields → `from_numpy`)
    and the table contents byte-identical.
- `cg3d/__init__.py`:
  - change: export `init_runtime`, `is_runtime_initialized`; docstring
    notes the package now also hosts the runtime boundary.
  - reason: make the boundary reachable as `cg3d.init_runtime()` for
    high-level users; no behavioural change.
- `tests/test_import_no_taichi_init.py` (new):
  - change: regression test (validation A) — imports the module in fresh
    child processes with `taichi.init` replaced by a raising trap.
  - reason: requirement 7 (deterministic, fails if import-time init
    returns; needs no GPU).
- `tests/run_level_a.py`:
  - change: A1 now calls `mod.ensure_lattice_tables()` before reading
    `mod.M` / `mod.inv_M` (`tests/run_level_a.py:52`).
  - reason: requirement 6 — A1 read the module tables before the solver
    was constructed, i.e. it implicitly relied on import-time allocation.
- `tests/README.md`:
  - change: one line in the run list for the new test.
  - reason: keep the suite's documented commands complete.
- `cg3d/protocol.py`: **not modified** (0 lines). `OpenSystem.__init__`
  constructs `ColorGradientSolver3D`, which reaches the boundary on its
  own; adding a second init call there would be redundant.

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| R1 import does not call `ti.init()` | PASS | Validation A child 1; `grep` in validation C shows no call in the module. |
| R2 import succeeds in a fresh process without prior `ti.init()` | PASS | Validation A child 1 (fresh subprocess, no project init). Module tables are `None` after import — no runtime-dependent allocation at import. |
| R3 one clear explicit project init path, small implementation | PASS | `cg3d.runtime.init_runtime()` (`cg3d/runtime.py:27`); 3 small functions, no backend framework. |
| R4 backend contract preserved | PASS | `select_arch()` keeps `LBM_ARCH=cpu` → CPU, otherwise GPU default; `offline_cache=True` preserved. Not exercised on GPU (no GPU work allowed). |
| R5 `cg3d.OpenSystem` workflows still initialize correctly | PASS (lifecycle only) | `cg3d/protocol.py` unchanged; scratch check built a tiny synthetic OpenSystem, confirmed runtime `prog is None` before construction and initialized after, 10 steps ran with finite diagnostics. No physics validation claimed. |
| R6 direct solver users in scope updated where necessary | PASS | `tests/run_level_a.py` needed the explicit call; `probe_gx1_nan.py` and the other tests construct a solver, so they already pass through the boundary — left untouched on purpose. |
| R7 deterministic regression test for import-time init | PASS | `tests/test_import_no_taichi_init.py`: exit 0 on the candidate; a negative control (base-style module) shows the trap trips when init returns at import. |
| R8 one short CPU-only smoke after explicit init | PASS | `LBM_ARCH=cpu python tests/test_compute_c_bulk.py`, exit 0, values identical to the pre-change run. |
| R9 no silent numerical change to make tests pass | PASS | Diff touches no arithmetic; six module tables byte-identical base vs candidate; smoke values identical base vs candidate. |

Constraints check: `ColorGradientSolver3D` name and signature unchanged;
lattice tables unchanged (byte-compared); default parameters unchanged;
kernel/step order unchanged; no GPU work; no expensive simulation run; no
broad refactor — the commit is 6 files / 212 insertions / 14 deletions, of
which the two new files account for 161 of the insertions; the four
*modified* files change +51/−14 lines (`.agent_runtime/evidence/candidate-show.txt`).

## Validation

All commands run from the repository root
`D:\2026_agent_work\09_cg3d_controller\worktrees\CG3D-TAICHI-INIT-001`
with the project environment `C:\Users\yangc\anaconda3\envs\lbm\python.exe`
(Python 3.10.21, taichi 1.7.4, numpy 2.2.6). Evidence files are under
`.agent_runtime/evidence/` (gitignored scratch).

### A. Import-side-effect regression

- **Command:** `python tests/test_import_no_taichi_init.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** child 1 (import with `ti.init` trapped) →
  `IMPORT_OK: lbm_solver_cg3d imported with ti.init trapped; no Taichi
  program (prog is None)`, and all six module tables still `None`. Child 2
  → `BOUNDARY_OK: init_runtime() reaches ti.init`. Both children exit 0.
- **Output / artifact reference:** `.agent_runtime/evidence/validation_a_import_no_taichi_init.log`

### A′. Negative control for the trap (ad hoc, not part of the candidate)

- **Command:** patch `taichi.init` to raise, then import a temp-dir module
  that calls `ti.init(...)` at import (copy of the removed base block).
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `NEGATIVE CONTROL OK: trap trips on an import-time
  ti.init`. This shows validation A would fail if import-time
  initialization were reintroduced, rather than passing vacuously.

### B. CPU-only solver smoke

- **Command:** `LBM_ARCH=cpu python tests/test_compute_c_bulk.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `A |C|=0.000e+00`, `B |C|=0.000e+00`, `C |C|=2.500e-01`,
  `D |C|=2.500e-01`, `PASS: bulk suppression is density-independent;
  interface behaviour unchanged`.
- **Output / artifact reference:** `.agent_runtime/evidence/validation_b_cpu_smoke.log`
- **Scope note:** this is a construction + field-initialization + probe
  regression, not a convergence test. No time-stepping convergence claim
  is made; process exit 0 is not reported as physical convergence.

### B′. Same smoke against the pre-change solver (numerics-neutrality comparison)

- **Command:** `LBM_ARCH=cpu python <tmp>/test_compute_c_bulk.py` with
  `<tmp>/lbm_solver_cg3d.py` = `git show 6d4a442:lbm_solver_cg3d.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** identical values to B: `0.000e+00 / 0.000e+00 /
  2.500e-01 / 2.500e-01`.
- **Output / artifact reference:** in report (temp-dir run; the candidate
  run in B is the captured log).

### B″. Shared table values, base vs candidate

- **Command:** dump `e, e_f, w, LR, M, inv_M` from each revision (CPU, no
  kernels) and compare arrays.
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `TABLE_VALUES_IDENTICAL: True` — all six arrays equal
  including dtype and shape (`e int32 (19,3)`, `M float32 (19,19)`, ...).
- **Output / artifact reference:** `.agent_runtime/evidence/validation_b2_table_values.txt`

### B‴. High-level `cg3d.OpenSystem` lifecycle (ad hoc scratch, R5)

- **Command:** `LBM_ARCH=cpu python .agent_runtime/evidence/opensystem_init_check.py`
- **Status:** `PASS` (lifecycle only; the script is gitignored scratch, not
  part of the candidate)
- **Exit code:** `0`
- **Key result:** before construction `prog=None`,
  `is_runtime_initialized=False`; after `OpenSystem(...)`
  `is_runtime_initialized=True`, `prog is not None`; a second
  `init_runtime()` returned `False` (no re-init); 10 steps ran,
  `s_nw=0.5791`, `umax=1.09e-02`, finite.
- **Caveat:** geometry is a fabricated 24×12×12 box; nothing here is a
  physical or numerical validation of the open-system protocol.

### C. Static scope check

- **Command:** `grep -n "ti\.init" lbm_solver_cg3d.py`;
  `grep -rn "ti\.init" --include=*.py .`;
  `grep -rn "init_runtime(\|ensure_lattice_tables(" --include=*.py .`
- **Status:** `PASS`
- **Exit code:** `0` (grep matches only comments/docstrings — see artifact)
- **Key result:** no import-time `ti.init(...)` remains in
  `lbm_solver_cg3d.py`; the only executable `ti.init` call in the
  repository is `cg3d/runtime.py:39` inside `init_runtime()`. Project call
  sites of the boundary: `lbm_solver_cg3d.py:244`
  (`ColorGradientSolver3D.__init__` → `ensure_lattice_tables()`,
  `lbm_solver_cg3d.py:132`, which calls `init_runtime()` at line 145) and
  `tests/run_level_a.py:52`.
- **Output / artifact reference:** `.agent_runtime/evidence/validation_c_static_scope.txt`

### Initialization lifecycle (as implemented)

1. **import** — `lbm_solver_cg3d` imports `os`, `numpy`, `taichi`, and
   `cg3d.runtime`; it calls no Taichi API. The six table names are `None`.
   `prog` stays `None`; no field, no program, no backend.
2. **explicit runtime init** — `cg3d.runtime.init_runtime()` (idempotent,
   flag-guarded) runs `ti.init(arch=select_arch(), offline_cache=True)`
   once per process.
3. **runtime-dependent allocation** — `_init_lattice_tables()` creates the
   six fields and fills them with `from_numpy`, exactly the numpy literals
   used before; `ensure_lattice_tables()` sequences 2 → 3 and is
   idempotent.
4. **solver construction** — `ColorGradientSolver3D.__init__` calls
   `ensure_lattice_tables()` first, then allocates its instance fields and
   0-d parameter fields; kernels resolve the module tables from module
   globals at compile time (first `step()`/`init()` call), i.e. after
   step 3.

## Git / Source State

- base: `6d4a442` (`agent(CG3D-TAICHI-INIT-001): queue round 1`)
- head / commit: `05de9981a9d671c866ec2135e7a470d48752f79c`
- branch: `agent-task/CG3D-TAICHI-INIT-001` (pushed to
  `origin/agent-task/CG3D-TAICHI-INIT-001`, upstream tracking set; PR URL
  offered by GitHub:
  https://github.com/YangCui1994/cg3d-graphite/pull/new/agent-task/CG3D-TAICHI-INIT-001)
- dirty files remaining: none — `git status --porcelain` empty after the
  validations, so the validated tree is the committed tree
  (`.agent_runtime/evidence/git-status-after.txt` is 0 bytes).
- not merged, not force-pushed, `master` untouched; `.agent_runtime/` is
  gitignored so the report and evidence are not part of the commit.

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| candidate diff | `.agent_runtime/evidence/git-diff.patch` | full diff base → candidate |
| changed-file list | `.agent_runtime/evidence/validation_c_static_scope.txt` | scope confirmation |
| commit stat | `.agent_runtime/evidence/candidate-show.txt` | commit identity + stat |
| validation A log | `.agent_runtime/evidence/validation_a_import_no_taichi_init.log` | import regression stdout |
| validation B log | `.agent_runtime/evidence/validation_b_cpu_smoke.log` | CPU smoke stdout |
| table comparison | `.agent_runtime/evidence/validation_b2_table_values.txt` | base vs candidate table values |
| OpenSystem check | `.agent_runtime/evidence/opensystem_init_check.py` | R5 scratch script (not in the commit) |
| Taichi probes | `.agent_runtime/evidence/probe-taichi-1.7.4-lifecycle.txt` | measured Taichi 1.7.4 lifecycle behaviour (field-before-init raises; duplicate `ti.init` invalidates fields; lazy module global in `@ti.func` works) |

## Deviations

- Added two ad hoc checks beyond the requested A/B/C: a negative control
  for the `ti.init` trap (A′), and the `cg3d.OpenSystem` lifecycle check
  (B‴) written as gitignored scratch rather than a new tracked test, so the
  candidate stays minimal. The base-vs-candidate table and smoke
  comparisons (B′, B″) are extra evidence for R9, not new scope.
- `tests/README.md` was edited (one line) to list the new test; it is a
  documentation line inside the allowed `tests/` scope.
- Validation A's "no Taichi program materialized" sub-check reads
  `taichi.lang.impl.get_runtime()` — a Taichi internal. If that internal
  disappears the child prints `UNCHECKED` instead of failing, so the
  primary guarantee stays the `ti.init` trap; the tables-are-`None` check
  is public-API only.

## Assumption / Modeling Impact

None. No physical model, boundary/initial-condition meaning, convergence
or stopping rule, wettability interpretation, claim scope, or default
parameter was changed; no scientific assumption had to be resolved. The
task's "Accepted" assumptions (numerics-neutral, `LBM_ARCH` semantics part
of the contract) were honoured: `LBM_ARCH` selection logic is byte-for-byte
the same decision, only moved.

One lifecycle semantic worth stating: the runtime is now owned by
`cg3d.runtime`. A user who calls `ti.init()`/`ti.reset()` outside that
boundary around a live solver can still break their own fields — exactly
as before this change, when import-time init made a second `ti.init()`
equally destructive. It is documented in `cg3d/runtime.py`.

## Existing Evidence Potentially Affected

- `tests/run_level_a.py` (A1) previously depended on import-time table
  allocation; updated in scope and **NOT_RUN** in this session (32³ solver
  suite, outside the "one short smoke" budget) — it should be run by
  whoever next runs Level A.
- No previous results or published numbers are affected: table values,
  formulas, defaults, and step order are unchanged, and the one solver
  regression run reproduces pre-change values exactly.
- Repository scripts that still assume import-time initialization
  **outside** the allowed scope: none found. Only three files touch Taichi
  directly (`lbm_solver_cg3d.py`, the new `cg3d/runtime.py`, the new
  test); every other solver user (`cg3d/protocol.py` `OpenSystem`,
  `probe_gx1_nan.py`, `tests/levelb_*.py`, `tests/test_poiseuille_cg3d.py`,
  `tests/test_compute_c_bulk.py`, `tests/test_checkpoint_resume.py`)
  constructs a solver and therefore reaches the boundary; the two drivers
  `run_pcs_cg3d.py` / `run_ir_cg3d.py` import `cg3d` only, and the
  visualisation/geometry scripts do not import the solver at all.
- **Copy-paired tree:** `/d/2026_agent_work/01_GLM_LBM3D_porous_media/LBM/source_code/taichi_LBM3D/2phase/lbm_solver_cg3d.py`
  exists, still has an import-time `ti.init` block (its CPU branch even
  lacks `offline_cache=True`), and that tree has **no** `cg3d/` package.
  It was not modified (outside this repository, not authorised). If this
  change is ever synchronised there, `cg3d/runtime.py` must go with it or
  the import must be adjusted first; the two copies have already diverged.

## Unresolved Issues / Human Decisions

- Whether to synchronise the paired LBM tree (and how to handle its missing
  `cg3d` package) is a human/controller decision; nothing was done there.
- The default backend stays the GPU default (`LBM_ARCH` unset → `ti.gpu`),
  unchanged, per the contract — no decision was taken on it.
- The `ti.init`/`ti.reset` ownership note above is a documented limitation,
  not a silent choice: if a future task wants `init_runtime()` to adopt an
  already-initialized, foreign Taichi runtime instead of skipping, that is
  a deliberate design change.

## Suggested Next Action

Run the full Level A suite CPU-only
(`LBM_ARCH=cpu python tests/run_level_a.py`) to confirm the A1 table access
via `ensure_lattice_tables()` and A2–A5 still pass on the candidate commit.
