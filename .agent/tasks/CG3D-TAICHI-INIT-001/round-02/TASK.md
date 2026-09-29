# TASK

## ID

`CG3D-TAICHI-INIT-001-R2`

## Objective

Validate the Round 1 Taichi runtime-lifecycle candidate with the complete existing Level A regression suite on CPU.

Round 1 is already reviewed as PASS for its stated implementation requirements. This round is a bounded validation continuation, not a request for broader refactoring.

Use the existing candidate:

`05de9981a9d671c866ec2135e7a470d48752f79c`

and resume the existing Z Code task session.

## Scope

### Allowed

- `lbm_solver_cg3d.py`
- `cg3d/runtime.py`
- `cg3d/__init__.py`
- `cg3d/protocol.py`
- `tests/`

### Do not modify

- `run_ir_cg3d.py`
- `run_pcs_cg3d.py`
- numerical formulations, kernels, lattice constants, MRT tables, forcing, recoloring, BC/IC meaning, convergence criteria, or physical parameters
- controller / agent infrastructure
- unrelated documentation

## Requirements

1. Run the complete existing Level A suite CPU-only:
   ```text
   LBM_ARCH=cpu python tests/run_level_a.py
   ```
2. Confirm A1 exercises the new explicit/lazy table initialization path and that A1–A5 all pass.
3. If Level A passes, do not make gratuitous source changes. A validation-only round with the candidate unchanged is acceptable.
4. If Level A fails because of the Round 1 runtime-lifecycle change, fix only the lifecycle defect within the allowed scope.
5. If any source is changed in Round 2, rerun both:
   ```text
   python tests/test_import_no_taichi_init.py
   LBM_ARCH=cpu python tests/run_level_a.py
   ```
6. Do not change numerical/physical behavior to make Level A pass.
7. Do not run GPU, Level B, full geometry, pressure ladder, or other expensive scientific simulations.

## Constraints

- This round validates integration; it must not redesign the runtime abstraction.
- Preserve `LBM_ARCH=cpu` / default GPU semantics and `offline_cache=True`.
- Preserve all Round 1 numerical and physical guardrails.
- If Level A exposes a problem that requires numerical/modeling changes rather than runtime-lifecycle changes, stop and report it as HUMAN_REQUIRED instead of fixing it.

## Scientific / Modeling Assumptions

- **Accepted:** Round 1 is intended to be numerics-neutral and physics-neutral.
- **Accepted:** Level A is regression evidence for runtime integration, not proof of full scientific validity.
- **Unresolved:** None unless Level A reveals an issue outside runtime lifecycle.

## Validation Requested

Primary:

```text
LBM_ARCH=cpu python tests/run_level_a.py
```

If Round 2 modifies candidate source, additionally rerun:

```text
python tests/test_import_no_taichi_init.py
```

Do not launch GPU work.

## Evidence Requested

In `execution_report.md`, include:

- exact Level A command;
- exit code;
- elapsed time;
- the PASS/FAIL line for each A1–A5 check;
- whether the candidate source changed in Round 2;
- final candidate commit;
- if no source change occurred, state explicitly that the reviewed Round 1 candidate remained unchanged;
- if a source change occurred, provide the reason and diff summary.

Do not reference only unpublished local validation-log paths; include the concise Level A result directly in the execution report so it is visible to the remote reviewer.

## Git Policy

- commit/push allowed on the existing task branch if a fix is required;
- no source change is preferred if validation passes;
- do not merge to `master`;
- do not modify the control branch directly from the executor.

## Human Decisions Reserved

- Any numerical/physical formulation change.
- Any expansion beyond runtime lifecycle.
- Any synchronization with the paired external LBM tree.

## Notes / References

- Round 1 review: `.agent/tasks/CG3D-TAICHI-INIT-001/round-01/REVIEW.md`.
- Round 1 candidate: `05de9981a9d671c866ec2135e7a470d48752f79c`.
- The Controller currently does not publish arbitrary executor-local custom validation logs; therefore place concise Level A outcomes directly in the execution report.
