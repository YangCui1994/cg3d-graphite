# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `CG3D-PERIODIC-CONN-002`
- **Status:** `COMPLETED`

## Summary

`cg3d.diagnostics.label_periodic` was fixed and validated for neighbour relations that cross
more than one periodic axis at once. The stated bug **is reproducible** (proof below); the
implementation now reproduces the intended 3D 6/18/26 torus topology, including wrapped edge
(2 seams) and wrapped corner (3 seams) relations, with no false merges when one of the
relevant axes is non-periodic.

Only the three files in the allowed scope were touched. No LBM simulation, GPU work, or
solver import was involved: all validation is deterministic, host-side numpy/scipy.

## Executor Claims — Changes

- `cg3d/diagnostics.py`:
  - change: replaced `_seam_offsets()` (per-seam, "+1 step along one axis") and the
    per-seam merge loop with `_wrapped_offsets()`, which returns every offset of the
    selected connectivity structure that is non-zero on at least one periodic axis. For each
    such offset the neighbour pair `(A, B = A + off)` is built as: on a **non-periodic**
    axis the step only narrows both sides (`slice(0, d-1)` / `slice(1, d)`); on a
    **periodic** axis `B` is the `np.roll(B, -off, axis)` view, so any number of axes can
    wrap simultaneously. Matching label pairs are de-duplicated with `np.unique` before the
    existing union-find step. Signature, return semantics, and default `periodic_axes=(1, 2)`
    are unchanged.
  - reason: the old code took the `ax = 0` plane against the `ax = -1` plane and sliced the
    **remaining two axes without wrapping them**, so a relation requiring two (or three)
    simultaneous wraps was never formed.
- `tests/test_periodic_connectivity.py` (new):
  - change: new focused test file. Covers single-seam merge, multi-seam ring, y+z wrapped
    edge for conn 6/18/26, x+y wrapped edge for conn=18, x+y+z wrapped corner for conn
    6/18/26, negative controls with a non-periodic axis, size exactness, separate-cluster
    control, `periodic_axes=()` vs plain `scipy.ndimage.label`, and an exhaustive comparison
    against an independent brute-force torus oracle (252 mask x axis-subset x conn combos).
    It also prints the explicit `REPRO ...` lines quoted in this report.
  - reason: requirement 5 of the task; the oracle shares no code with the implementation, so
    it can fail independently.
- `tests/test_postprocessing.py`:
  - change: added `test_periodic_wrapped_neighbours()` (wrapped edge conn=6/18, wrapped
    corner conn=18/26, two non-periodic negative controls, size exactness after a wrapped
    merge) and registered it in `main()`.
  - reason: `python tests/test_postprocessing.py` is the primary validation command, so the
    decisive new cases must be inside it, not only in the new file.

**Root cause (concise):** the merge step treated each periodic axis in isolation and
enumerated only in-plane shifts that stay inside the array. A wrapped neighbour whose
displacement is `(0,-1,-1)` (edge over the y and z seams) or `(-1,-1,-1)` (corner over all
three) needs a shift on an in-plane axis that leaves the array, so the slice simply dropped
that pair. Result: `n_clusters` too large / `largest` too small for `conn=18/26` — the same
bias direction the docs already describe for `conn=6`, but not covered by the old fix.

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| R1 conn=6/18/26 topology consistent (faces / +edges / +3-axis corners) | PASS | `test_wrapped_edge_yz`, `test_wrapped_corner_xyz`, 252-combo oracle test |
| R2 arbitrary `periodic_axes` subsets; keep default `(1, 2)` | PASS | signature unchanged; all 7 non-empty subsets + `()` tested via the oracle matrix |
| R3 return semantics unchanged (labels; sizes desc; each voxel once) | PASS | sizes exactness + `sum(sizes) == mask.sum()` checks; existing size test still passes |
| R4 non-periodic CC semantics preserved | PASS | same `ndimage.label` base call; `periodic_axes=()` matches plain scipy label for 6/18/26 |
| R5 deterministic tests for the listed cases | PASS | see `tests/test_periodic_connectivity.py` (34 checks) and `test_postprocessing.py` (20 checks) |
| R6 deterministic, pure NumPy/SciPy, no Taichi/solver | PASS | imports `numpy` + `scipy.ndimage` only; `taichi`/`lbm_solver_cg3d` absent from `sys.modules` in the test process |
| R7 meaning of `periodic_axes`, conn numbers, trapped-gas classification unchanged | PASS | no semantics changed; only previously-missed relations are added |
| R8 small, readable, topology-first (no per-test special cases) | PASS | one general wrapped-offset union; ~30-line core loop; `_seam_offsets` removed |
| R9 if not reproducible, do not force a change | N/A | bug **is** reproducible — change was justified by the evidence below |

## Validation

### Primary — `python tests/test_postprocessing.py`

- **Command:** `python tests/test_postprocessing.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `ALL PASS`; 20 PASS / 0 FAIL (was 12 PASS / 0 FAIL at the base commit;
  the 8 new checks are `y+z wrapped edge split for conn=6`, `y+z wrapped edge merges for conn=18`,
  `x+y+z wrapped corner split for conn=18`, `x+y+z wrapped corner merges for conn=26`,
  `x+y wrapped edge merges for conn=18`, `wrapped edge pair stays split with x non-periodic`,
  `wrapped edge pair stays split with y non-periodic`, `sizes exact after wrapped merge`).
  Run at commit `6221927` with a clean tree.
- **Output / artifact reference:** `.agent_runtime/logs/atcommit_test_postprocessing.txt`

### Focused — `python tests/test_periodic_connectivity.py`

- **Command:** `python tests/test_periodic_connectivity.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `ALL PASS`; 34 PASS / 0 FAIL, including
  `brute-force oracle agreement over 252 mask/axis/conn combos`.
- **Output / artifact reference:** `.agent_runtime/logs/atcommit_test_periodic_connectivity.txt`

### PASS/FAIL lines for the new periodic edge / corner cases (post-change, at commit `6221927`)

```text
PASS y+z wrapped edge stays split for conn=6
PASS y+z wrapped edge merges for conn=18
PASS y+z wrapped edge merges for conn=26
PASS x+y wrapped edge merges for conn=18 (both axes periodic)
PASS x+y wrapped edge stays split for conn=6
PASS x+y wrapped edge stays split for conn=18 axes=(0, 2)      <- x periodic, y not
PASS x+y wrapped edge stays split for conn=18 axes=(1, 2)      <- y periodic, x not
PASS x+y wrapped edge stays split for conn=18 axes=(0,) / (1,) / ()
PASS x+y wrapped edge stays split for conn=26 axes=(0, 2) / (1, 2) / (0,) / (1,) / ()
PASS x+y+z wrapped corner stays split for conn=6
PASS x+y+z wrapped corner stays split for conn=18
PASS x+y+z wrapped corner merges for conn=26
PASS x+y+z wrapped corner stays split for axes=(0, 1) / (1, 2) / (0, 2) at conn=26
PASS single y seam face pair merges (conn=6 / 18 / 26)
PASS y+z ring through two seams is one cluster (conn=6)
PASS sizes exact after wrapped merge (3 + 1)
PASS sizes sum to the occupied voxel count
PASS separate clusters stay separate (conn=6 / 18 / 26)
PASS empty periodic_axes == plain scipy label (conn=6 / 18 / 26)
PASS brute-force oracle agreement over 252 mask/axis/conn combos
```

Note on the fourth group: `x+y+z wrapped corner stays split for axes=(0,1) / (1,2) / (0,2)`
is a *negative* control — the same geometric corner pair must NOT merge when the third axis
is non-periodic, and the PASS confirms it does not.

### Pre-change reproducer result (unmodified code at base `dc67945`)

The same test file was run **before** any edit, so the `REPRO ...` lines below are the
pre-change behaviour of `label_periodic`; the exit code of that run was `1` (6 FAILs).

```text
BEFORE (base dc67945)                      AFTER (commit 6221927)
REPRO y+z wrapped edge   conn=6  axes=(1,2): n=2 sizes=[1, 1]   n=2 sizes=[1, 1]
REPRO y+z wrapped edge   conn=18 axes=(1,2): n=2 sizes=[1, 1]   n=1 sizes=[2]      <- FIXED
REPRO y+z wrapped edge   conn=26 axes=(1,2): n=2 sizes=[1, 1]   n=1 sizes=[2]      <- FIXED
REPRO x+y+z wrapped corner conn=6  axes=(0,1,2): n=2 sizes=[1, 1]   n=2 sizes=[1, 1]
REPRO x+y+z wrapped corner conn=18 axes=(0,1,2): n=2 sizes=[1, 1]   n=2 sizes=[1, 1]
REPRO x+y+z wrapped corner conn=26 axes=(0,1,2): n=2 sizes=[1, 1]   n=1 sizes=[2]  <- FIXED
```

**The pre-change implementation fails both key cases**: at `conn=18` with `(1,2)` periodic it
reports the y+z wrapped edge pair as 2 clusters of size 1 instead of 1 cluster of size 2, and
at `conn=26` with `(0,1,2)` periodic it reports the x+y+z wrapped corner pair as 2 clusters
of size 1 instead of 1 cluster of size 2. The pre-change run also failed
`x+y wrapped edge merges for conn=18`, `sizes exact after wrapped merge (3 + 1)`, and
mismatched the brute-force oracle in **5 of 252** combos.

- **Output / artifact reference:** `.agent_runtime/logs/pre_change_new_tests.txt` (pre),
  `.agent_runtime/logs/atcommit_test_periodic_connectivity.txt` (post).

### Regression check — pre-change vs post-change on production-like masks

The pre-change implementation was loaded from `git show HEAD:cg3d/diagnostics.py` before the
edit and compared against the new one on the real `data/geo_graphite_200.npz` pore mask
(200³) and on random masks: partition equality, coarsening direction, size sums, runtime.

- **Status:** `PASS`
- **Key result (production default `conn=6`, `periodic_axes=(1, 2)`, real 200³ pore mask):**
  old `n_clusters=451 largest=3499465 sizes_sum=3579836`, new `n_clusters=451
  largest=3499465 sizes_sum=3579836` — **partitions identical**. Also identical for
  `per=(0,1,2)` and `per=(0,)` on the same mask, and for every random mask at `conn=6` over
  all tested axis subsets. This is expected by construction: `conn=6` has only
  single-non-zero-component (face) offsets, hence no in-plane offset, hence no wrap was ever
  needed — **the production default is provably unaffected**.
- **Key result (`conn=18/26`):** every new partition is a **coarsening** of the old one
  (components only merge, never split) with equal size sums. Measured differences on
  production-scale masks: sparse trapped-gas-like mask on 200³ at `conn=26`, `per=(0,1,2)` →
  `95076 → 95075` clusters (one extra merge); real pore crop 120³ at `conn=18`, `per=(1,2)` →
  `112 → 111`; at `conn=26`, `per=(0,1,2)` → `77 → 76`. With `per=(1,2)` (the production
  setting) the sparse 200³ mask gave identical results at conn=18 and conn=26; the
  disagreement appears only where a two/three-seam coincidence actually occurs.
- **Runtime (host, 200³ = 8·10⁶ cells):** `conn=6,(1,2)` 0.41 s new vs 0.10 s old;
  `conn=26,(0,1,2)` 0.96 s new vs 0.10 s old. Once-per-run post-processing; no GPU involved.
- **Output / artifact reference:** `.agent_runtime/logs/old_vs_new_equivalence.txt`

### Test isolation check

- **Command:** import the focused test module and inspect `sys.modules`
- **Status:** `PASS`
- **Key result:** `solver imported: False`, `taichi imported: False`

## Git / Source State

- base: `dc67945876e5970b67884e70c271f830024ff489` (`agent-task/CG3D-PERIODIC-CONN-002`, — the task branch head before this work)
- head / commit: `62219270d5d3c29dc522103e262718c77332b233` ("CG3D-PERIODIC-CONN-002: fix wrapped multi-axis neighbours in label_periodic")
- branch: `agent-task/CG3D-PERIODIC-CONN-002` (pushed to `origin`; remote head verified equal to `6221927`)
- dirty files remaining: none (`git status --porcelain` empty; worktree file bytes identical to the committed blobs)
- files in the commit: `cg3d/diagnostics.py`, `tests/test_periodic_connectivity.py`,
  `tests/test_postprocessing.py` — 3 files, +393 / −43
- **No solver/physics file changed:** `lbm_solver_cg3d.py`, `cg3d/protocol.py`,
  `run_ir_cg3d.py`, `run_pcs_cg3d.py` do not appear in the commit. `run_common.py` needed no
  change (compatibility re-export already present) and was not modified.
- The validation runs quoted above were made with the worktree byte-identical to commit
  `6221927` (verified via `git diff`/blob comparison).

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| Fixed implementation | `cg3d/diagnostics.py::label_periodic` (+ `_wrapped_offsets`) | torus-correct CC labelling |
| Focused tests | `tests/test_periodic_connectivity.py` | required cases + oracle matrix |
| Primary tests | `tests/test_postprocessing.py::test_periodic_wrapped_neighbours` | primary validation command coverage |
| Logs (gitignored scratch) | `.agent_runtime/logs/pre_change_new_tests.txt`, `atcommit_test_postprocessing.txt`, `atcommit_test_periodic_connectivity.txt`, `old_vs_new_equivalence.txt` | raw command output quoted above |

## Deviations

- The task's allowed scope listed `run_common.py` and `tests/test_postprocessing.py` as
  modifiable; `run_common.py` was **not** modified (nothing needed changing there).
- No documentation file was modified, because `docs/*.md` is outside the allowed scope —
  see "Unresolved Issues" for the resulting stale doc line.
- The candidate was committed and pushed on the task branch (allowed by the task's Git
  Policy). No merge to `master`, no force-push, no history rewrite, no branch/worktree
  deletion.

## Assumption / Modeling Impact

None. No physical model, boundary-condition meaning, initial condition, convergence rule,
contact angle / wettability interpretation, default physical parameter, saturation
definition, or trapped-gas interpretation was changed. `periodic_axes` keeps its meaning and
its production default `(1, 2)`; `conn` keeps its SciPy definition. The change only adds
adjacency relations that the declared topology already implied, so a cluster can now be
larger (never smaller) and `n_clusters` can only decrease.

Explicitly **not** claimed: whether a given gas cluster is physically trapped. That depends
on reservoir/boundary semantics and remains out of scope, as the task states.

## Existing Evidence Potentially Affected

- **`conn=6` results (the legacy default, incl. the archived X3 `n_clusters=38 / largest=309314`
  numbers in `docs/NUMERICAL_AUDIT_2026_09.md`): unaffected** — verified partition-identical
  on the real 200³ pore mask and argued structurally (face offsets have no in-plane offset).
- **`conn=18/26` cluster reports (post-processing observables only): may change slightly.**
  Any such number can only move in the direction "fewer, larger clusters" (one extra merge
  measured on a sparse production-scale mask at `conn=26`, `per=(0,1,2)`). No stored
  `conn=18/26` results are in the repository, and no trapped-gas volume `S_nr` changes, since
  that metric does not use `label_periodic`.
- `docs/BC_IC_OUTPUT.md` line 78 and `docs/CHANGELOG_NUMERICS.md` line 91 describe the old
  implementation ("非周期 label + 缝平面 union-find" / per-seam merge). The described
  *behaviour* still holds; the *implementation description* is now stale.
- `tests/README.md` was not updated (outside allowed scope): its numpy row lists only
  `test_postprocessing.py` and says "11 numpy checks", which was already stale at the base
  commit (12 checks) and is now 20; the new focused file is not listed either.

## Unresolved Issues / Human Decisions

- **Stale implementation note in `docs/BC_IC_OUTPUT.md` (§ cluster topology)** — it says the
  implementation is a per-seam plane union-find; it is now a general wrapped-offset union.
  Behaviour claims (periodic y/z merge always on, `n_clusters` over-counted without it)
  remain correct. Doc files were outside the allowed scope, so this is reported, not fixed.
- **Whether to refresh any reported `conn=18/26` numbers** is a human/controller decision;
  the production/legacy `conn=6` numbers do not need refreshing.
- No change was made to `run_ir_cg3d.py` (forbidden) — it calls
  `label_periodic(red_dom, conn=args.conn)` and therefore picks up the fix with its default
  `periodic_axes=(1, 2)`.

## Suggested Next Action

Open a small follow-up task (docs scope) to update the one stale sentence in
`docs/BC_IC_OUTPUT.md` line 78 so the documented implementation matches the new
wrapped-offset union, then have the controller/reviewer validate this candidate at commit
`6221927`.
