# TASK

## ID

`CG3D-TAICHI-INIT-001`

## Objective

Remove Taichi runtime initialization as an import-time side effect of `lbm_solver_cg3d.py`.

A fresh Python process must be able to import `lbm_solver_cg3d` without calling `ti.init()` and without allocating/initializing the Taichi runtime merely because the module was imported. Solver execution must instead pass through one explicit project runtime-initialization boundary before Taichi fields/kernels are used.

This is an engineering/runtime-lifecycle cleanup only. Preserve all numerical and physical behavior.

## Scope

### Allowed

- `lbm_solver_cg3d.py`
- `cg3d/runtime.py`
- `cg3d/__init__.py`
- `cg3d/protocol.py`
- `probe_gx1_nan.py`
- `tests/`

### Do not modify

- `run_ir_cg3d.py`
- `run_pcs_cg3d.py`
- numerical formulations, kernels, lattice constants, MRT tables, forcing, recoloring, boundary conditions, initial-condition meaning, convergence criteria, or physical parameters
- controller / agent infrastructure
- documentation unrelated to this runtime-lifecycle change

## Requirements

1. Importing `lbm_solver_cg3d` must not call `ti.init()`.
2. Importing `lbm_solver_cg3d` in a fresh Python process must succeed without a prior project call to `ti.init()`. If current module-level Taichi field allocation prevents this, move only the minimum required runtime-dependent allocation behind the explicit initialization boundary.
3. Provide one clear project-level explicit Taichi runtime initialization path used before solver execution. Keep the implementation small; do not introduce a general backend framework.
4. Preserve the existing backend contract:
   - `LBM_ARCH=cpu` selects CPU;
   - otherwise the existing default remains GPU;
   - preserve `offline_cache=True`.
5. Existing high-level workflows through `cg3d.OpenSystem` must still initialize the runtime correctly without changing the scientific/numerical setup.
6. Direct solver users in the allowed scope (tests / probe) must be updated where necessary to use the explicit initialization path.
7. Add a deterministic regression test proving that a plain module import does not invoke `ti.init()`. The test must fail if import-time initialization is reintroduced.
8. Run one short CPU-only solver smoke/regression check after explicit initialization. Do not run a long validation suite.
9. Do not silently change numerical behavior to make the tests pass.

## Constraints

- Preserve the public solver class `ColorGradientSolver3D` unless a minimal compatibility change is unavoidable.
- Preserve current lattice-table values and initialization content exactly.
- Preserve current default scientific parameters and solver step ordering.
- Do not launch CUDA/GPU work for this task.
- Do not run Poiseuille 20k-step, Level B Laplace/contact-angle, full geometry, pressure-ladder, or other expensive simulations.
- Avoid a broad refactor. This task is about runtime initialization lifecycle only.
- If satisfying "import succeeds without runtime initialization" requires a change that would alter Taichi field ownership, kernel semantics, or numerical results in a way that cannot be shown to be behavior-preserving, stop and report the issue rather than expanding scope.

## Scientific / Modeling Assumptions

- **Accepted:** This task must be numerics-neutral and physics-neutral.
- **Accepted:** Existing `LBM_ARCH` backend selection semantics are part of the compatibility contract.
- **Unresolved:** None. If an unexpected Taichi lifecycle constraint creates a numerical/architecture tradeoff, report it instead of choosing silently.

## Validation Requested

### A. Import-side-effect regression

Create and run a deterministic test that imports `lbm_solver_cg3d` in a fresh subprocess/process context while making any call to `taichi.init` fail the test. The module import itself must succeed.

Suggested intent (implementation may differ if the test is clearer):

```text
python tests/test_import_no_taichi_init.py
```

The test must not require GPU availability.

### B. CPU-only solver smoke/regression

Run a short existing or newly focused solver check with `LBM_ARCH=cpu`, after the new explicit initialization path is invoked. Prefer the smallest deterministic check that exercises solver construction plus existing lattice/field initialization.

A suitable existing regression is `tests/test_compute_c_bulk.py` if it can be run CPU-only without broadening this task.

Do not run expensive GPU or long-duration validations.

### C. Static scope check

Confirm that no import-time `ti.init(...)` remains in `lbm_solver_cg3d.py`, and report every project call site of the explicit runtime initialization function added/used by this task.

## Evidence Requested

- candidate commit SHA and changed-file list;
- diff for all modified files;
- exact validation commands and exit codes;
- stdout/stderr for the import-side-effect regression;
- stdout/stderr for the CPU-only smoke/regression;
- brief explanation of the new initialization lifecycle:
  - import;
  - explicit runtime init;
  - runtime-dependent field/table allocation;
  - solver construction;
- confirmation that no numerical/physical formulas or parameters were changed;
- any existing tests/scripts in the repository that still assume import-time initialization but were outside the allowed scope.

## Git Policy

- commit allowed on the task branch;
- push allowed;
- do not merge to `master`;
- do not modify the control branch directly from the executor.

## Human Decisions Reserved

- Any change to physical/numerical formulation.
- Any decision to change the default backend away from the current GPU default.
- Any broader solver architecture redesign beyond what is minimally necessary to remove import-time runtime initialization.
- Any decision to change long-run validation criteria or rerun expensive scientific simulations.

## Notes / References

- Current observed import-time behavior is at the top of `lbm_solver_cg3d.py`: backend selection from `LBM_ARCH` immediately calls `ti.init(...)`.
- `cg3d.protocol.OpenSystem` currently imports `ColorGradientSolver3D` lazily inside `OpenSystem.__init__`; preserve this high-level workflow.
- Several regression scripts import `ColorGradientSolver3D` directly. Update only those necessary within the allowed `tests/` scope.
- The purpose of this task is also to exercise the V1 ChatGPT -> GitHub -> Controller -> Z Code -> GitHub path on a real but bounded engineering task.
