# TASK

## ID

`CG3D-PERIODIC-CONN-002`

## Objective

Fix and validate periodic connected-component labeling in `cg3d.diagnostics.label_periodic` for neighbour relations that cross more than one periodic axis simultaneously.

The function must reproduce the intended 3D 6/18/26-connectivity topology on a periodic domain, including wrapped edge and corner neighbours. This task is topology/post-processing correctness only; do not change trapped-gas physical semantics or any LBM solver numerics.

## Scope

### Allowed

- `cg3d/diagnostics.py`
- `run_common.py`
- `tests/test_postprocessing.py`
- `tests/test_periodic_connectivity.py`

### Do not modify

- `lbm_solver_cg3d.py`
- `cg3d/protocol.py`
- `run_ir_cg3d.py`
- `run_pcs_cg3d.py`
- solver physics, BC/IC, convergence rules, pressure-ladder logic, saturation definitions, or trapped-gas interpretation
- controller / agent infrastructure

## Problem Statement

The current `label_periodic(mask, conn, periodic_axes)` labels the volume non-periodically and then merges component labels across each periodic seam independently.

For a seam along one axis, the current code slices the remaining in-plane axes without wrapping them. Therefore a valid neighbour relation that requires wrapping two periodic axes at once can be missed.

Examples of intended topology:

- With y and z periodic, cells `(x, 0, 0)` and `(x, Ny-1, Nz-1)` are a wrapped edge-diagonal pair:
  - disconnected for `conn=6`;
  - connected for `conn=18`;
  - connected for `conn=26`.
- With x, y and z periodic, cells `(0, 0, 0)` and `(Nx-1, Ny-1, Nz-1)` are a wrapped 3-axis corner pair:
  - disconnected for `conn=6`;
  - disconnected for `conn=18`;
  - connected for `conn=26`.

The implementation must handle these cases without introducing false merges when one of the relevant axes is non-periodic.

## Requirements

1. Correct `label_periodic` so periodic neighbour equivalence is consistent with the selected SciPy-style 3D connectivity:
   - `conn=6`: face neighbours only;
   - `conn=18`: face + edge neighbours, but not 3-axis corners;
   - `conn=26`: face + edge + 3-axis corner neighbours.
2. Support arbitrary subsets of `periodic_axes` among axes 0, 1, 2; preserve the current default `(1, 2)`.
3. Preserve existing return semantics:
   - first return: relabeled component array;
   - second return: component sizes sorted descending;
   - sizes count each interior voxel exactly once.
4. Preserve existing non-periodic connected-component semantics from `scipy.ndimage.label`.
5. Add deterministic tests that cover at minimum:
   - existing single-axis seam merge;
   - existing multi-seam ring behavior;
   - y+z simultaneous wrapped edge pair for `conn=6/18/26`;
   - x+y simultaneous wrapped edge pair for `conn=18` when both axes are periodic;
   - same geometric pair does **not** merge when only one of those axes is periodic;
   - x+y+z simultaneous wrapped corner pair for `conn=6/18/26`, with merge only for `conn=26`;
   - component size remains exact after wrapped merges;
   - a control case of two genuinely separate clusters remains separate.
6. The fix must be deterministic and pure NumPy/SciPy host-side logic. Do not introduce Taichi or solver dependencies.
7. Do not change the meaning of `periodic_axes`, connectivity numbers, or trapped-gas classification.
8. Keep the implementation reasonably small and readable. Prefer a topology-correct neighbour/union strategy over special-casing individual tests.
9. If inspection shows the stated bug is not reproducible, do not force a code change; demonstrate that with deterministic tests and report the evidence.

## Constraints

- No LBM simulation is required or authorized.
- No GPU work.
- Do not redefine what phase is considered trapped.
- Do not change the default periodic axes of production callers.
- Do not optimize prematurely; correctness and explicit tests are the priority.
- Avoid depending on component label numeric identity; tests should assert connectivity equivalence, component count, and sizes rather than arbitrary label numbers.

## Scientific / Modeling Assumptions

- **Accepted:** Periodicity here is a topological boundary condition on a binary voxel mask.
- **Accepted:** 6/18/26 connectivity follows the same neighbourhood definition used by `scipy.ndimage.generate_binary_structure(3, 1/2/3)`.
- **Accepted:** This task validates topology only. Whether a gas cluster is physically "trapped" depends on additional boundary/reservoir semantics and is outside scope.
- **Unresolved:** None. If existing production use relies on behavior inconsistent with the topology above, stop and report it rather than preserving a known bug silently.

## Validation Requested

Primary:

```text
python tests/test_postprocessing.py
```

If a focused new test file is added:

```text
python tests/test_periodic_connectivity.py
```

All tests must run without importing or initializing the LBM solver.

Also provide a small explicit before/after reproducer for at least:

```text
y+z wrapped edge, conn=18
x+y+z wrapped corner, conn=26
```

and state whether the pre-change implementation fails those cases.

## Evidence Requested

Include directly in `execution_report.md`:

- exact changed files;
- concise description of the root cause;
- exact validation commands and exit codes;
- PASS/FAIL lines for the new periodic edge/corner cases;
- pre-change reproducer result for the two key bug cases;
- post-change component counts/sizes for those same cases;
- confirmation that no solver/physics files changed;
- candidate commit SHA.

Because the current Controller does not yet publish arbitrary executor-local custom validation logs, reproduce the decisive test results directly in the execution report rather than referring only to local log paths.

## Git Policy

- commit allowed on the task branch;
- push allowed;
- do not merge to `master`;
- do not modify the control branch directly from the executor.

## Human Decisions Reserved

- Any change to trapped-gas physical definition.
- Any change to production periodic-axis defaults.
- Any solver/numerical/BC change.
- Any decision to merge this candidate into another task branch or master.

## Notes / References

- Current implementation: `cg3d/diagnostics.py::label_periodic`.
- Compatibility re-export: `run_common.py`.
- Existing pure host-side tests: `tests/test_postprocessing.py`.
- This is the second real V1 task and is intentionally independent of LBM runtime/simulation work.
