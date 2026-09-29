# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `CG3D-TAICHI-INIT-001-R2`
- **Status:** `COMPLETED`

## Summary

Round 2 was a bounded validation round. The complete existing Level A
regression suite was run CPU-only against the frozen Round 1 candidate
`05de9981a9d671c866ec2135e7a470d48752f79c`, and **A1–A5 all PASS** (exit 0,
13 s in-process / 14 s wall). **No candidate source was changed in Round 2
— the reviewed Round 1 candidate remains exactly as reviewed.**

Requirement 2 was confirmed with two deterministic controls rather than by
inspection alone: A1 reads the module tables only after
`mod.ensure_lattice_tables()`, and with that one line removed the suite dies
at that same line (`AttributeError: 'NoneType' object has no attribute
'to_numpy'`, exit 1). A1 therefore cannot pass through import-time
allocation; it exercises the new explicit/lazy path by construction.

As extra (cheap) evidence, Level A was also run against the pre-change
revision `6d4a442` in a temp directory: its output is byte-identical to the
candidate's, line for line, including A2–A5 which step the solver.

## Executor Claims — Changes

- **No source change in Round 2.** Allowed-scope files are untouched; the
  Round 1 candidate (`05de998`) is the validated artifact.
  - `git status --porcelain` empty; `HEAD` = `origin/agent-task/CG3D-TAICHI-INIT-001`
    = `05de9981a9d671c866ec2135e7a470d48752f79c`; no Round 2 commit was
    created and nothing needed pushing.
  - Tracked object hashes of the six candidate paths (unchanged from the
    Round 1 commit): `cg3d/__init__.py 608c5b0`, `cg3d/runtime.py 2a574f3`,
    `lbm_solver_cg3d.py 4036565`, `tests/README.md 1f05fde`,
    `tests/run_level_a.py e0c0602`, `tests/test_import_no_taichi_init.py e35452a`.
- Nothing outside the allowed scope was touched (no `run_ir_cg3d.py`,
  `run_pcs_cg3d.py`, docs, or controller/agent infrastructure edits).

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| R1 run complete Level A CPU-only | PASS | `LBM_ARCH=cpu python tests/run_level_a.py`, exit 0, all five checks PASS (verbatim lines below). |
| R2 confirm A1 uses the explicit/lazy path and A1–A5 pass | PASS | A1–A5 PASS; two controls show A1 depends on `ensure_lattice_tables()` and cannot read the tables from import. |
| R3 no gratuitous source changes if Level A passes | PASS | Zero source changes in Round 2; validated commit is the Round 1 candidate. |
| R4 fix only lifecycle defects if Level A fails | NOT_APPLICABLE | Level A passed; no defect surfaced. |
| R5 rerun import regression + Level A if source changed | NOT_APPLICABLE (source unchanged); import regression rerun anyway as a sanity check | `tests/test_import_no_taichi_init.py` → exit 0 on the unchanged candidate. |
| R6 no numerical/physical change to make Level A pass | PASS | No source change at all; Level A output identical to the pre-change revision. |
| R7 no GPU / Level B / full geometry / pressure ladder runs | PASS | Every command in this round used `LBM_ARCH=cpu`; no GPU, no Level B, no drivers. |

Constraints check: runtime abstraction not redesigned (nothing edited);
`LBM_ARCH=cpu` / default-GPU semantics and `offline_cache=True` untouched;
all Round 1 guardrails intact.

## Validation

Environment: `C:\Users\yangc\anaconda3\envs\lbm\python.exe` (Python 3.10.21,
taichi 1.7.4, numpy 2.2.6), repository root
`D:\2026_agent_work\09_cg3d_controller\worktrees\CG3D-TAICHI-INIT-001`.
All runs CPU-only. Taichi's offline cache was warm from Round 1, so the CPU
(x64) runs are fast; the numeric values below show the checks executed.

### Primary — Level A on the candidate (verbatim output)

- **Command:** `LBM_ARCH=cpu python tests/run_level_a.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Elapsed:** `13 s` in-process (the suite's own line) / `14 s` wall including interpreter start
- **Per-check result lines (A1–A5), copied from the run:**

```text
PASS A1 M @ inv_M == I  max|err|=2.98e-08
PASS A2 uniform phase stationary  max|v|=0.00e+00 psi_dev=0.0e+00
PASS A3 colour-mass conservation  rel drift=3.58e-07
PASS A4 reservoir pins rho/psi  rho=1.05000 psi=1.0000
PASS A5 membrane blocks blue (psi_left stays red)  min psi[x<9]=1.000
level A done in 13s
LEVEL A: ALL PASS
```

- **Output / artifact reference:** `.agent_runtime/evidence/round2_level_a.log`

### R2 confirmation — A1 uses the explicit/lazy table path

Two controls, both CPU-only and seconds long:

1. **Boundary dependency (code path).** A fresh process: after plain import
   `mod.M is None` and `is_runtime_initialized() == False`; reading
   `mod.M` raises `AttributeError: 'NoneType' object has no attribute
   'to_numpy'`; after `mod.ensure_lattice_tables()` the table is a
   materialized `ScalarField (19, 19)` and the runtime is initialized.
   Verbatim:
   ```text
   after plain import: M is None | runtime initialized: False
   CONTROL-1 OK: A1 table read is impossible before the boundary call -> 'NoneType' object has no attribute 'to_numpy'
   CONTROL-1 after ensure_lattice_tables(): M ScalarField (19, 19) | runtime initialized: True
   ```
   Artifact: `.agent_runtime/evidence/round2_control_a1_boundary.txt`
2. **Suite-level dependency.** `tests/run_level_a.py` copied to a temp dir
   with the single line `mod.ensure_lattice_tables()` removed: the suite
   fails at exactly that table read with
   `AttributeError: 'NoneType' object has no attribute 'to_numpy'` (file
   line 52, exit 1). So the PASS in the primary run is attributable to the
   new boundary, not to import-time allocation.
   Artifact: `.agent_runtime/evidence/round2_control_level_a_without_boundary.txt`

Code positions involved: `tests/run_level_a.py:52` (explicit call before the
A1 read) → `lbm_solver_cg3d.py:132` `ensure_lattice_tables()` → `:145`
`init_runtime()` → `:244` the same call from `ColorGradientSolver3D.__init__`
for every solver user.

### Extra — Level A on the pre-change revision (numerics-neutrality)

- **Command:** `LBM_ARCH=cpu python run_level_a.py` with the temp copy
  `lbm_solver_cg3d.py` = `git show 6d4a442:lbm_solver_cg3d.py` and
  `run_level_a.py` = `git show 6d4a442:tests/run_level_a.py`
- **Status:** `PASS`
- **Exit code:** `0`, `13 s` / `14 s` wall
- **Key result:** `diff` of the two Level A logs (Taichi banner lines
  excluded) reports **no differences** — A1 `2.98e-08`, A2 `0.00e+00` /
  `0.0e+00`, A3 `3.58e-07`, A4 `1.05000` / `1.0000`, A5 `1.000` are
  identical, as are both timing lines. A2–A5 execute the full timestep, so
  this covers the step path, not just construction.
- **Output / artifact reference:**
  `.agent_runtime/evidence/round2_level_a_base_revision.log`,
  `.agent_runtime/evidence/round2_level_a_diff_vs_base.txt`

### Supplementary — Round 1 import regression re-run (not triggered by R5)

- **Command:** `python tests/test_import_no_taichi_init.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** module import still free of Taichi runtime side effects;
  `init_runtime()` remains the call that reaches `ti.init`.
- **Output / artifact reference:** `.agent_runtime/evidence/round2_import_regression.log`

### Scientific-run reporting (per template)

Level A is a structural/numerical regression suite, not a scientific
simulation: no convergence or termination criteria are involved, and
"exit 0" is reported only as the suite's pass signal. No stability or
convergence claim is made here, and no physics conclusion is drawn.

## Git / Source State

- base (Round 2 start): `05de9981a9d671c866ec2135e7a470d48752f79c`
  (Round 1 candidate)
- head / commit: `05de9981a9d671c866ec2135e7a470d48752f79c` — **unchanged**
- upstream: `origin/agent-task/CG3D-TAICHI-INIT-001` == HEAD (no Round 2
  commit, nothing new to push)
- branch: `agent-task/CG3D-TAICHI-INIT-001`
- dirty files remaining: none — `git status --porcelain` empty
  (`.agent_runtime/evidence/round2_source_state.txt`); report and logs live
  in gitignored `.agent_runtime/`, so the committed tree equals the
  validated tree
- not merged, not force-pushed, `master` and the control branch untouched

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| Level A log (candidate) | `.agent_runtime/evidence/round2_level_a.log` | primary validation, A1–A5 lines + exit/elapsed |
| Level A log (pre-change) | `.agent_runtime/evidence/round2_level_a_base_revision.log` | same suite on `6d4a442` |
| Log diff | `.agent_runtime/evidence/round2_level_a_diff_vs_base.txt` | candidate vs base: no differences |
| A1 boundary control | `.agent_runtime/evidence/round2_control_a1_boundary.txt` | tables unusable before the boundary; usable after |
| No-boundary control | `.agent_runtime/evidence/round2_control_level_a_without_boundary.txt` | suite fails at line 52 without the call |
| Source-state check | `.agent_runtime/evidence/round2_source_state.txt` | HEAD, upstream, clean tree, object hashes |
| Import regression re-run | `.agent_runtime/evidence/round2_import_regression.log` | Round 1 guarantee still holds |

## Deviations

- Ran two extra cheap controls (A1 boundary dependency, suite without the
  boundary call) and one extra base-revision Level A comparison beyond the
  requested primary validation. All are CPU-only, seconds-to-tens-of-seconds
  long, and none changes source; they exist to satisfy R2 with evidence and
  to support the R6 guardrail.
- Re-ran the Round 1 import regression although R5 only requires it if
  source changed; recorded as supplementary.
- No source file was edited in Round 2, so no commit was created.

## Assumption / Modeling Impact

None. Nothing was changed, so no assumption, boundary/initial-condition
meaning, convergence rule, contact-angle interpretation, claim scope, or
default parameter was affected. The Round 1 "Accepted" assumptions stand:
the candidate is numerics-neutral and physics-neutral, and Level A here is
runtime-integration evidence, not proof of scientific validity.

## Existing Evidence Potentially Affected

- The Round 1 report listed Level A as **NOT_RUN**; it is now **PASS** on
  the identical candidate, so that open item is closed. The suggested next
  action from Round 1 is discharged.
- Round 1 evidence (import regression, `test_compute_c_bulk.py`, table-value
  comparison, OpenSystem lifecycle check) remains valid and was not
  invalidated by this round.
- The copy-paired external LBM tree still carries its own import-time
  `ti.init` and has no `cg3d/` package; it was not touched and will not be
  touched without a human decision.

## Unresolved Issues / Human Decisions

- Synchronization with the paired external LBM tree remains a human
  decision (unchanged from Round 1); nothing was done there.
- No other issue is open: Level A exposed no lifecycle defect and required
  no fix, so no `HUMAN_REQUIRED` escalation is raised.

## Suggested Next Action

Have the controller close `CG3D-TAICHI-INIT-001` (Round 2 passed with the
candidate unchanged), leaving the paired-tree synchronization question to
the human.
