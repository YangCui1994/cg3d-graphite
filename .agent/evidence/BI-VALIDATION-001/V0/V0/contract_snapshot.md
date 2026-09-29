# V0 — Existing CG3D Baseline on the Execution Machine

## Objective

Establish that the declared product base is healthy on the actual Windows GPU machine before adding any new validation code.

## Authorized changes

Prefer no product changes.

Environment/runner fixes may be made only if they do not alter solver numerics.

Any proposed solver-physics or existing regression change requires HUMAN_REQUIRED.

## Required validations

Run the existing repository suite appropriate to the current base:

1. tests/run_level_a.py
2. tests/test_compute_c_bulk.py
3. tests/test_poiseuille_cg3d.py
4. tests/levelb_laplace.py
5. tests/levelb_contact_angle.py
6. tests/test_postprocessing.py

Use the documented GPU/JIT execution rules.

## Hard gates

- Every required test exits successfully.
- Laplace regression satisfies its existing repository thresholds.
- Contact-angle regression satisfies its existing repository thresholds.
- Poiseuille/forcing regression satisfies its existing repository thresholds.
- No NaN/Inf or unexplained crash.
- Candidate/product source remains scientifically identical to the declared base unless an explicitly authorized environment-only fix was required.

## Diagnostics to capture

- GPU/backend identification;
- Python/Taichi versions;
- per-test wall time;
- JIT compile behaviour;
- any nondeterministic numerical spread visible relative to existing tolerances.

## Reviewer emphasis

- Verify no baseline scientific threshold was weakened.
- Verify no solver change was smuggled in to make a failing test pass.
- Verify the test outputs correspond to the candidate/base being reviewed.

## Promotion

PASS -> V1.

Failure of existing physics regression without a clearly external environment cause -> HUMAN_REQUIRED.
