# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `CG3D-CONVERGENCE-DIAG-003`
- **Status:** `COMPLETED`

## Summary

`run_hold` now returns two additive records next to its unchanged legacy fields:

- `row["termination"]` — process completion, the legacy reason, and the
  `converged` / `step_limit_reached` / `safety_limit_triggered` statements as
  three independent flags plus the echoed `qs_mode`;
- `row["numerical_health"]` — which sampled `OpenSystem.measure()` scalars were
  ever NaN/Inf, from which sampled step, and how often.

Both are observational. No stopping rule, threshold, window rule,
minimum-step rule, `qs_mode` meaning, `umax_cap` check or loop ordering was
changed: `cg3d/diagnostics.py` is a pure addition (111 insertions, 0 deletions,
so `eval_convergence` is byte-identical), and the only deletions anywhere are
one import line and one docstring line in `cg3d/protocol.py` — no executable
line was removed or modified.

The strongest evidence is an A/B replay of 16 scripted cases through the
pre-change `run_hold` (loaded from base commit `0ca191c`) and the candidate:
every legacy row field and both callback sequences (`dump_frame`, `live_ckpt`)
compare identical in all 16 cases, including the cases that exercise
`every`/`qs_window`/`min_steps`, both `qs_mode` values, resume bookkeeping
(`it_start`/`it_offset`) and the two non-finite variants.

No LBM simulation, GPU work, Taichi kernel, Level B validation, geometry run or
pressure ladder was launched.

## Executor Claims — Changes

- `cg3d/diagnostics.py`:
  - change: added `QUASI_STEADY`/`MAX_STEPS`/`UMAX_CAP` reason constants,
    `termination_record(reason, qs_mode)`, `_finite_or_none(value)` and
    `NumericalHealthTracker` (`observe`/`record`). Purely additive — the file
    has no deleted or modified line.
  - reason: the task requires a small, testable host-side helper set rather than
    an inlined reporting block, and the legacy `reason` string conflates
    "criterion satisfied", "step budget spent" and "safety cap hit".
- `cg3d/protocol.py`:
  - change: import the two new helpers; in `run_hold`, create the tracker before
    the loop, call `health.observe(it, m)` at the existing sampling point right
    after `m = sys_.measure()`, and add `termination=` / `numerical_health=` to
    the returned row. Docstring extended to describe the additive records.
  - reason: report the new records where the rung exit is decided, without
    touching any decision.
- `tests/test_termination_diagnostics.py`:
  - change: new deterministic test file (363 lines) with a fake system that
    implements only the members `run_hold` touches (`s.step`, `set_ladder`,
    `measure`, `pore_cells`), four scripted scenarios kept as data, the required
    semantic assertions, helper unit tests, and an `example_records()` generator
    used for the published schema example.
  - reason: the task requires the semantic cases to be exercised through the
    real `run_hold` loop without Taichi/GPU.

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| R1 preserve quasi-steady algorithm, thresholds, min-step rules, window rules, `qs_mode` selection, `umax_cap` check, loop ordering | PASS | `cg3d/protocol.py` has 16 insertions and 2 deletions; the deletions are one import line and one docstring line. A/B replay of 16 cases vs `run_hold` at base `0ca191c`: every legacy row field and both callback sequences identical. |
| R2 small testable host-side helper in `cg3d.diagnostics` (no state-machine framework) | PASS | `termination_record` (pure function) + `NumericalHealthTracker` (30-line observe-only accumulator). No framework, no new dependency. |
| R3 additive `termination` / `numerical_health` records preserving existing fields | PASS | Test asserts `set(row) == legacy_18_keys \| {termination, numerical_health}`, and that `row["reason"]` / `row["convergence"]` are unchanged in meaning and value. |
| R4 do not change `eval_convergence` definitions | PASS | `git diff 0ca191c..HEAD -- cg3d/diagnostics.py` shows 111 insertions / 0 deletions; `eval_convergence` and `region_stats` are untouched. |
| R5 deterministic pure-Python tests with a fake system, exercising `run_hold` without Taichi/GPU | PASS | `python tests/test_termination_diagnostics.py` → 62 checks, 0 failures, exit 0. No solver step, no kernel, no GPU (the test only imports the package, which loads Taichi as a module without `ti.init`). |
| R6 test the six required semantics | PASS | All six covered and PASS (see Validation). |
| R7 rerun the accepted Task 2 periodic-connectivity tests | PASS | `python tests/test_periodic_connectivity.py` → 34 checks, 0 failures, exit 0, including the brute-force oracle over 252 mask/axis/connectivity combos. |
| R8 no LBM / GPU / Level B / geometry run / pressure ladder | PASS | Only the three requested test files were executed. |

## Validation

All three requested commands were run from the repository root against the
frozen candidate commit `3e49087` (working tree clean, no edit afterwards).

**Interpreter note (environment, not a code issue):** the requested commands are
`python tests/...`. On the default shell PATH `python` is
`C:\Users\yangc\anaconda3\python.exe` (Anaconda base, Python 3.13.9), which has
numpy/scipy but **no taichi**; with it, all three commands fail at
`import cg3d` → `cg3d/runtime.py` → `import taichi`. This is pre-existing and
identical before and after the change (verified on the untouched base tree at
the start of the session). The commands below were therefore executed with the
project environment `C:\Users\yangc\anaconda3\envs\lbm\python.exe`
(taichi 1.7.4, numpy 2.2.6, scipy 1.15.3) placed first on `PATH`, so the command
line itself is exactly the requested one.

### `python tests/test_termination_diagnostics.py` (new)

- **Command:** `PATH=<anaconda3/envs/lbm first> python tests/test_termination_diagnostics.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** 62 checks, 0 failures, `ALL PASS`.
- **Output / artifact reference:** `.agent_runtime/published_evidence/termination_diagnostics.log`

Per-case result:

| Required semantic case | Result | Reported record |
|---|---|---|
| quasi-steady exit → `converged=true`, no step/safety limit (checked in `qs_mode="sat"` **and** `"multi"`) | PASS | exit at step 9, `converged=true`, both limit flags false, `numerical_health.finite=true` |
| max-step exit → `converged=false`, `step_limit_reached=true` | PASS | exit at step 25 (`max_steps=25`), `converged=false`, `step_limit_reached=true`, `safety_limit_triggered=false`, `finite=true` |
| `umax-cap` with finite metrics → `converged=false`, `safety_limit_triggered=true`, `finite=true` | PASS | exit at step 3 (`umax=0.5 > umax_cap=0.1`), `safety_limit_triggered=true`, `converged=false`, `finite=true`, `nonfinite_fields=[]` |
| non-finite sampled diagnostic reported with field name and first step | PASS | `finite=false`, `nonfinite_fields=["pc_measured","u_bulk_x"]`, `first_nonfinite_step=2`, `first_nonfinite_fields=["pc_measured"]`, `nonfinite_counts={"pc_measured":8,"u_bulk_x":6}` |
| selected convergence and numerical health stay independent | PASS | same record shows `converged=true` **and** `finite=false`; the max-steps record shows the opposite combination `converged=false`, `finite=true` |
| legacy `row["reason"]` and `convergence["exit"]` consistent with the new record | PASS | for all four cases `row["reason"] == convergence["exit"]["reason"] == termination["reason"]` and `convergence["exit"]["mode"] == termination["qs_mode"]`; at most one stopping flag is true |

Additional checks in the same run: the row key set is exactly the legacy set plus
the two new keys; `convergence` keeps `criteria_passed` / `thresholds` / `exit`;
both new records are strict JSON; the helper units handle `None`, strings,
non-scalar arrays and `np.float32` values (unavailable values ignored, NaN/Inf
caught, first bad step preserved); an unknown reason yields three false flags
rather than raising.

### `python tests/test_postprocessing.py`

- **Command:** `PATH=<anaconda3/envs/lbm first> python tests/test_postprocessing.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** 20 checks, 0 failures, `ALL PASS` (label_periodic connectivity/periodic merge + `eval_convergence` records).
- **Output / artifact reference:** `.agent_runtime/published_evidence/postprocessing.log`

### `python tests/test_periodic_connectivity.py`

- **Command:** `PATH=<anaconda3/envs/lbm first> python tests/test_periodic_connectivity.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** 34 checks, 0 failures, `ALL PASS`, including `brute-force oracle agreement over 252 mask/axis/conn combos`.
- **Output / artifact reference:** `.agent_runtime/published_evidence/periodic_connectivity.log`
- **Explicit confirmation:** the accepted `CG3D-PERIODIC-CONN-002` topology fix is **retained** after this task's edits to the same file (`cg3d/diagnostics.py`); no `label_periodic` line was touched (0 deletions in that file).

### Additional evidence: stopping-behaviour A/B replay (not requested; supports R1)

- **Command:** `PATH=<anaconda3/envs/lbm first> python .agent_runtime/published_evidence/stopping_equivalence_script.txt`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** 16 scripted cases, 0 mismatches → `IDENTICAL`. For every case the legacy row fields equal those of `run_hold` at base `0ca191c7cd6f8970fc8af7e20261f4d7f246fda0`, the `dump_frame` / `live_ckpt` call sequences are equal, the only added keys are `numerical_health` and `termination`, and the derived flags match the legacy reason. Cases cover flat/drifting/spiking/non-finite samplers, both `qs_mode` values, `every`/`qs_window`/`min_steps` variation, a tight `umax_cap`, and resume bookkeeping with `it_start`/`it_offset`.
- **Output / artifact reference:** `stopping_equivalence.log` and its source `stopping_equivalence_script.txt` in the evidence bundle.

## Representative records

Values below are the exact records asserted by the new test. `fields_observed`
(15 sampled scalar names: `inj_b`, `inj_m`, `inj_r`, `p_in_mean`, `p_out_mean`,
`pc_band_in`, `pc_band_out`, `pc_measured`, `rho_in_mean`, `rho_out_mean`,
`s_nw`, `s_nw_binary`, `u_bulk_x`, `u_rms`, `umax`) is elided here for brevity;
the complete records are in `published_evidence/termination_examples.json`.

**quasi-steady** (flat saturation, `qs_mode="sat"`, exit at step 9)

```json
{"reason": "quasi-steady", "steps": 9,
 "convergence_exit": {"mode": "sat", "reason": "quasi-steady"},
 "termination": {"process_completed": true, "reason": "quasi-steady", "converged": true,
                 "step_limit_reached": false, "safety_limit_triggered": false, "qs_mode": "sat"},
 "numerical_health": {"finite": true, "nonfinite_fields": [], "first_nonfinite_step": null,
                      "sample_count": 9, "nonfinite_counts": {}, "first_nonfinite_fields": []}}
```

**max-steps** (`s_nw` drifts 1e-2/step, `max_steps=25`)

```json
{"reason": "max-steps", "steps": 25,
 "convergence_exit": {"mode": "sat", "reason": "max-steps"},
 "termination": {"process_completed": true, "reason": "max-steps", "converged": false,
                 "step_limit_reached": true, "safety_limit_triggered": false, "qs_mode": "sat"},
 "numerical_health": {"finite": true, "nonfinite_fields": [], "first_nonfinite_step": null,
                      "sample_count": 25, "nonfinite_counts": {}, "first_nonfinite_fields": []}}
```

**umax-cap** (finite `umax=0.5` crosses `umax_cap=0.1` at step 3)

```json
{"reason": "umax-cap", "steps": 3,
 "convergence_exit": {"mode": "sat", "reason": "umax-cap"},
 "termination": {"process_completed": true, "reason": "umax-cap", "converged": false,
                 "step_limit_reached": false, "safety_limit_triggered": true, "qs_mode": "sat"},
 "numerical_health": {"finite": true, "nonfinite_fields": [], "first_nonfinite_step": null,
                      "sample_count": 3, "nonfinite_counts": {}, "first_nonfinite_fields": []}}
```

**non-finite observation** (`pc_measured=NaN` from step 2, `u_bulk_x=Inf` from step 4; the sat-mode criterion is still satisfied)

```json
{"reason": "quasi-steady", "steps": 9,
 "convergence_exit": {"mode": "sat", "reason": "quasi-steady"},
 "termination": {"process_completed": true, "reason": "quasi-steady", "converged": true,
                 "step_limit_reached": false, "safety_limit_triggered": false, "qs_mode": "sat"},
 "numerical_health": {"finite": false, "nonfinite_fields": ["pc_measured", "u_bulk_x"],
                      "first_nonfinite_step": 2, "sample_count": 9,
                      "nonfinite_counts": {"pc_measured": 8, "u_bulk_x": 6},
                      "first_nonfinite_fields": ["pc_measured"]}}
```

## Explicit statement on stopping criteria

**No existing convergence criterion, threshold or stopping behaviour was
changed.** Not one of `qs_tol`, `pc_drift_tol`, `flux_tol`, `u_rel_tol`,
`qs_window`, `min_steps`, `max_steps`, `umax_cap`, the `qs_mode` selection, the
`eval_convergence` arithmetic, or the relative order of the quasi-steady and
`umax_cap` checks was modified, and no new threshold or stop condition was
introduced. `numerical_health` **reports** non-finite observations only; it
cannot influence the trajectory or the exit, and no non-finite stopping policy
was added. This is supported by the 0-deletion diff of `cg3d/diagnostics.py`
and by the 16-case A/B replay.

## Git / Source State

- base: `0ca191c7cd6f8970fc8af7e20261f4d7f246fda0` (matches the task's starting base)
- head / commit: `3e49087e195ac98b41000bc647b115c685daa71b` — `agent(CG3D-CONVERGENCE-DIAG-003): report termination and numerical health`
- branch: `agent-task/CG3D-CONVERGENCE-DIAG-003` (pushed: `0ca191c..3e49087`; the push updated that one ref only). No merge was performed, no force-push, and no commit was made to the default branch (`origin/master`, which is not checked out in this worktree).
- dirty files remaining: none (`git status --porcelain` empty; `.agent_runtime/` is gitignored)
- changed files vs base: `cg3d/diagnostics.py` (+111/-0), `cg3d/protocol.py` (+16/-2), `tests/test_termination_diagnostics.py` (+363/-0)

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| termination record + tracker | `cg3d/diagnostics.py` (`termination_record`, `NumericalHealthTracker`) | host-side additive reporting helpers |
| additive row records | `cg3d/protocol.py` (`run_hold`) | `row["termination"]`, `row["numerical_health"]` |
| new test | `tests/test_termination_diagnostics.py` | required semantics, fake system, no Taichi/GPU |
| published evidence bundle | `.agent_runtime/published_evidence/` (6 files + `manifest.json`, schema `v1`, validated against the Controller's `validate_published_evidence`) | logs, schema example, A/B log and script |

**Published evidence confirmed:** the bundle was created under
`.agent_runtime/published_evidence/` and is handed to the Controller. It
contains the three requested validation logs, the requested
`termination_examples.json` (`kind: schema_example`), plus the extra
`stopping_equivalence.log` and its reproduction script. It was checked with the
Controller's own validator: 6 files, 25 231 bytes total, all paths relative,
no symlinks, every non-manifest file listed exactly once. `provenance.json` was
deliberately **not** created (the Controller owns it).

## Deviations

- The three requested commands were run with the project's `lbm` conda
  environment first on `PATH` (see the interpreter note above) rather than with
  the default-PATH `python`, which cannot import the package at all. This is an
  environment condition of the machine, not of this change.
- Two extra evidence files (`stopping_equivalence.log`,
  `stopping_equivalence_script.txt`) were added beyond the four requested, to
  give the reviewer a re-runnable check that the stopping logic is untouched.
- `row["numerical_health"]` carries three extra observational keys
  (`nonfinite_counts`, `first_nonfinite_fields`, `fields_observed`) beyond the
  four required ("at minimum") keys. They report the same observed facts and add
  no bound.
- No other deviation.

## Assumption / Modeling Impact

No scientific assumption, boundary/initial-condition meaning, convergence
criterion, contact-angle/wettability semantics, physical parameter, pressure
ladder, or claim scope was changed or challenged.

The records are descriptive only: `termination.converged=true` means the
configured numerical criterion was satisfied — **not** physical equilibrium;
`max-steps` means the criterion was not reached within the step budget — not
that convergence is impossible; `umax-cap` with finite metrics is a safety-limit
exit — not a numerical-health failure. `numerical_health` covers finite /
non-finite observations only; it deliberately presents no density, velocity,
pressure, mass-balance or physical-plausibility bound, and it does not collapse
into a single "status" with `termination`.

## Existing Evidence Potentially Affected

- Nothing is invalidated. Downstream consumers of `row` see two extra keys; the
  two drivers (`run_pcs_cg3d.py`, `run_ir_cg3d.py`) read only legacy keys
  (`steps`, `s_nw`, `reason`, `d`), and the ladder JSON they write
  (`report_partial.json` / the final summary) simply gains the new records.
- Resumed runs reload ladder rows written by a previous version, so those older
  rows will lack the two new keys. Any consumer must treat them as optional —
  no consumer in this repository reads them yet.
- Existing convergence reports and quotas remain valid; no acceptance run was
  rerun or reinterpreted.

## Unresolved Issues / Human Decisions

- Broader convergence-policy redesign remains deferred (per the task).
- Whether any non-finite observation should ever affect stopping is explicitly
  left as a human/modeling decision; this task reports it and stops.
- Whether to surface the new records in the drivers' console summary / final
  report JSON is undecided; they are currently only in the row.

## Suggested Next Action

Have the reviewer inspect the evidence bundle (in particular
`stopping_equivalence.log`) and, if satisfied, accept
`agent-task/CG3D-CONVERGENCE-DIAG-003` at commit `3e49087`.
