# EXECUTION REPORT

> This document contains the executor's report. It is not, by itself, proof that commands ran or that the reported source state is correct. A controller/reviewer may independently capture Git and process evidence.

## Task

- **Task ID:** `ADS-EXECUTION-BASE-005`
- **Status:** `COMPLETED`

## Summary

The cumulative execution base is now a declared, machine-validated part of the
V1 protocol. The repair is deliberately small: one new state field, one
round-start rule, one pre-execution assertion, and two provenance fields.

- `.agent/state.json` carries `execution_base_commit`. Active non-draft states
  must hold a full 40-character lowercase hex SHA; only `DRAFT` may hold `null`.
- Round 1 creates the task branch from `execution_base_commit`, never from the
  control `ready_sha`, and then asserts `before_head == execution_base_commit`
  after preparing the worktree and before invoking Z Code.
- A pre-existing local or remote Round-1 branch must already resolve to the
  declared base. A mismatch is published as `ERROR` before Z Code runs, and the
  branch is never reset, rebased, or force-updated.
- Round 2/3 keep the same base and continue from the reviewed `candidate_commit`.
- `process.json` records `before_head` next to `execution_base_commit`, and the
  generated executor `provenance.json` records `execution_base_commit` next to
  `candidate_commit`, so both invariants are checkable from evidence alone.
- `.agent/templates/TASK.md` gained an `## Execution Base` section and
  `.agent/README.md` documents the field, Round-1 base selection, later-round
  continuation, control-revision vs. execution-base difference, and provenance.

No DAG, merge manager, dependency graph, or Markdown task parser was added. No
CG3D product code, scientific test, or earlier task record was touched.

## Executor Claims — Changes

- file: `.agent/controller/controller.py`
  - change: added `GIT_SHA_RE`; `execution_base_commit` added to the required
    state fields, format-validated, and required non-null for active states; new
    `_round_start_head()` returns the revision a round must start from (base on
    Round 1, reviewed candidate afterwards) plus the declaring field name; new
    `_local_branch_sha()` helper; `_prepare_worktree()` now applies the Round-1
    base rules for local/remote branches and creates a fresh branch from the
    expected head instead of `ready_sha`; `_execute_claimed()` asserts the
    observed `before_head` against that expected head before invoking the
    executor; `_capture_process()` records `execution_base_commit` in
    `process.json`; `_stage_executor_evidence()` records it in `provenance.json`.
  - reason: these are the exact points where a round could previously start from
    the wrong source revision while still satisfying every Controller check.
- file: `.agent/controller/tests/test_controller.py`
  - change: fixture split into an accepted-base commit and a later control READY
    commit so `control ready_sha != execution_base_commit` in every integration
    test; the two-round test now asserts the base invariants end to end and emits
    `base_semantics_summary.json`; new state-validation tests for missing, null,
    malformed and DRAFT base values; four new Round-1 integration tests; two
    pre-existing assertions repaired for Windows (see Deviations).
  - reason: the task asked for deterministic coverage of twelve specific
    behaviours, including one fixture that proves Round 1 starts at the declared
    base while the control READY commit differs.
- file: `.agent/README.md`
  - change: new `execution_base_commit` row in the state-field table, a new
    "Execution base and round starting revisions" section, provenance notes in
    the evidence section, and one new operational-boundary bullet.
  - reason: the protocol documentation is the planner's and reviewer's contract.
- file: `.agent/templates/TASK.md`
  - change: new `## Execution Base` section after `## ID`.
  - reason: new parent tasks must declare the base they build on.

## Requirements

| Requirement | Claimed status | Notes |
|---|---|---|
| R1 add and validate `execution_base_commit` in state handling | PASS | `validate_state()` requires the key, rejects non-40-char/non-lowercase-hex values, and rejects `null` for active states |
| R2 fresh Round 1 worktrees come from that SHA, not `ready_sha` | PASS | `_prepare_worktree()` uses `_round_start_head()`, which returns the base on Round 1; `ready_sha` is no longer a parameter |
| R3 Round-1 branch/head mismatch rejected before executor invocation | PASS | branch checks raise inside `_prepare_worktree()`; the head assertion runs before `_invoke_executor()`; both take the existing ERROR path |
| R4 later rounds resume from `candidate_commit` | PASS | Round ≥ 2 still requires the remote branch to equal the reviewed candidate and is resumed with `--resume` |
| R5 same `execution_base_commit` preserved across transitions | PASS | claim/publish/stop copy the state dict; asserted across Round 1 → Round 2 in the fixture |
| R6 base SHA in Controller process evidence and executor provenance | PASS | `process.json.execution_base_commit`, `provenance.json.execution_base_commit`, `before_head` unchanged |
| R7 existing evidence-publication constraints unchanged | PASS | limits, extensions, symlink/traversal rules, staged-copy verification and error semantics untouched |
| R8 existing allowed-path enforcement unchanged | PASS | `parse_allowed_paths`/`path_is_allowed`/`_enforce_allowed_paths` untouched |
| R9 max-round/session-resume/error behaviour unchanged | PASS | `HARD_MAX_ROUNDS`, `STOPPED_MAX_ROUNDS`, session-id checks and `_resume` handling untouched; those tests still pass |
| R10 update tests and protocol docs | PASS | 22 → 28 tests; README and TASK template updated |

## Validation

### Controller test suite (requested validation)

- **Command:** `python .agent/controller/tests/test_controller.py`
- **Status:** `PASS`
- **Exit code:** `0`
- **Key result:** `Ran 28 tests ... OK` (22 pre-existing tests, 6 net new; see the
  deviation list for the one replaced test). Python 3.13.9 on Windows; the suite
  uses only the standard library and the fake Z Code stand-in, so no Taichi, GPU,
  or CG3D dependency is involved.
- **Output / artifact reference:** `.agent_runtime/controller_tests.log`
  (published as `controller_tests.log`).

### Requested deterministic coverage

| # | Requested case | Where |
|---|---|---|
| 1 | active state missing the base is rejected | `test_active_state_missing_execution_base_commit_is_rejected` |
| 2 | malformed active base SHA is rejected | `test_active_state_null_and_malformed_execution_base_commit_is_rejected` (`None`, `""`, 39/41 chars, uppercase, non-hex, short SHA) |
| 3 | DRAFT may use null base | `test_draft_state_may_use_null_execution_base_commit` |
| 4 | Round 1 with no branch starts from the base even when `ready_sha` differs | fixture split + `test_two_rounds_claim_execute_resume_and_publish` |
| 5 | Round 1 `before_head` equals the declared base | same test, via `process.json` |
| 6 | pre-existing Round-1 branch at the wrong SHA is rejected before execution | `test_round1_preexisting_branch_at_wrong_base_fails_before_executor` |
| 7 | Round 2 continues from the Round-1 candidate, not the base | `test_two_rounds_claim_execute_resume_and_publish` (parent check) |
| 8 | base unchanged across Round 1 → Round 2 | same test, state and both `process.json` records |
| 9 | `process.json` holds `before_head` and `execution_base_commit` | same test, both rounds |
| 10 | executor `provenance.json` holds `execution_base_commit` | `test_executor_evidence_end_to_end_publication_and_provenance` |
| 11 | existing evidence-publication success/failure tests still pass | 12 `PublishedEvidenceValidationTests` + both integration evidence tests |
| 12 | existing timeout, scope, candidate/session and max-round tests still pass | `test_timeout_...`, `test_out_of_scope_...`, `test_missing_session_id_...`, `test_ready_round_above_cap_...`, plus the two new Round-1 state/branch tests that replaced the old candidate-mismatch test |

Two additional Round-1 tests cover accepted neighbouring states: a pre-existing
branch already at the declared base continues from it
(`test_round1_preexisting_branch_at_declared_base_continues_from_base`), and a
state that names a candidate with no branch is still refused
(`test_round1_candidate_at_base_without_branch_publishes_error`).

### End-to-end example: control READY SHA differs from the execution base

From the published run (`.agent_runtime/base_semantics_summary.json`, same run as
`controller_tests.log`; these are throwaway fixture repositories, so the SHAs
differ per run):

```text
execution_base_commit (declared)      6525c5845650407ed002eb00ba58ea8cb4934108
control ready_sha                     5873d47d4135bfb024e18580c4c8d6bfd9ca373b   (different)
Round 1 before_head                   6525c5845650407ed002eb00ba58ea8cb4934108   (== base)
Round 1 candidate                     c46ef433188c542ecb94267acb8aed8c3fb42825   (child of the base)
Round 2 before_head                   c46ef433188c542ecb94267acb8aed8c3fb42825   (== Round-1 candidate)
Round 2 candidate                     376ca8156c6dc268c1fb5507d89f16358dde36ee
```

The fixture also adds `ready_only_marker.txt` in the control READY commit only:
the test asserts that blob is absent from the Round-1 task branch, so the
candidate provably did not start from the control revision. Round 2 is proven to
continue from the Round-1 candidate by `<round2-candidate>^ == <round1-candidate>`
and by `dummy.txt` reading `round 1\nround 2\n`.

A second, independent single-round probe
(`base_probe.log`, `base_probe_script.txt`) shows the same behaviour and prints
the published records verbatim:

```text
execution_base_commit : d75fc3007fe24aa375f30720599e71ece432a679
control ready_sha     : 489b40dc168c8bc8409e8f9c2e2a669d85b7d000   (different)

process.json
  "before_head": "d75fc3007fe24aa375f30720599e71ece432a679"
  "execution_base_commit": "d75fc3007fe24aa375f30720599e71ece432a679"

provenance.json
  "candidate_commit": "45ce9ab586420eacfb99acff5ce394941827883a",
  "execution_base_commit": "d75fc3007fe24aa375f30720599e71ece432a679",
```

### Negative control (are the new tests vacuous?)

- **Command:** `PYTHONPATH=.agent/controller/tests python -m unittest -v test_controller` in a scratch tree where `.agent/controller/controller.py` is `git show dbecc71898131cc6545bf314dc2f7ba56d1df337:.agent/controller/controller.py` (pre-repair) and the tests are the post-repair file.
- **Status:** `PASS` (the control behaved as required: the new tests fail against the old code)
- **Key result:** `Ran 28 tests ... FAILED (failures=12, errors=1)`. The
  two-round test fails at `before_head != execution_base_commit` because the old
  controller started Round 1 at the control READY commit; the 15 tests unrelated
  to base selection still pass, so the repair did not change existing behaviour.
- **Output / artifact reference:** `prerepair_negative_control.log`.

### Evidence bundle

`validate_published_evidence()` (the Controller's own validator) accepts the
bundle: 5 files, 32,205 bytes total including the manifest, every file listed
exactly once, all extensions allowed. The limit, symlink, traversal, and digest
rules were not modified, so this is the same validation the Controller will run.

## Git / Source State

- base: `dbecc71898131cc6545bf314dc2f7ba56d1df337` (bootstrap base, manually
  pre-created branch; the queued control state carries it as both
  `execution_base_commit` and `candidate_commit`)
- head / commit: `bdf0ad5bc267e905b751f18b3f81205cef1e9073`
- branch: `agent-task/ADS-EXECUTION-BASE-005` (pushed as a fast-forward from the
  bootstrap SHA; no force-push, no history rewrite)
- dirty files remaining: none (`.agent_runtime/` is git-ignored scratch)

## Artifacts

| Artifact | Path / reference | Purpose |
|---|---|---|
| Candidate commit | `bdf0ad5bc267e905b751f18b3f81205cef1e9073` | Round-1 candidate reviewed by the Controller |
| Controller test log | `.agent_runtime/published_evidence/controller_tests.log` | Full suite output, exit code 0 |
| Base semantics summary | `.agent_runtime/published_evidence/base_semantics_summary.json` | Round-1/Round-2 base facts from the passing run |
| Negative control log | `.agent_runtime/published_evidence/prerepair_negative_control.log` | New tests vs. pre-repair controller |
| Evidence-shape probe | `.agent_runtime/published_evidence/base_probe.log`, `base_probe_script.txt` | Published `process.json` / `provenance.json` verbatim |
| Evidence manifest | `.agent_runtime/published_evidence/manifest.json` | Bundle index (schema `v1`) |

## Deviations

1. **Two pre-existing test assertions were platform-incorrect on Windows and had
   to be repaired to satisfy R10/validation item 12.** Both failed on the
   untouched bootstrap source before any change of mine (baseline: `Ran 22 tests
   ... FAILED (failures=1, errors=1)`):
   - `test_timeout_terminates_executor_before_publishing_error` used
     `os.kill(pid, 0)` + `assertRaises(ProcessLookupError)`. On Windows a dead PID
     raises `OSError` (WinError 87) instead, so the assertion never ran. It now
     uses a `process_is_alive()` helper (`tasklist /FI "PID eq <pid>"` on
     Windows) and asserts the timed-out executor is gone. The check is the same
     one, expressed portably; the assertion is not weakened.
   - `test_executor_evidence_end_to_end_publication_and_provenance` compared
     `provenance.json` size/sha256 against the committed blob. This machine has
     `core.autocrlf=true`, so `git add` stores LF where the published file has
     CRLF (15 vs. 14 bytes). The digest is now compared against the published
     bytes in the Controller clone, with a byte-equality check against the source
     evidence file; the property being verified (provenance describes the
     published bytes) is unchanged.
2. **One test was replaced.** `test_candidate_mismatch_publishes_error_without_execution`
   asserted a Round-1 message keyed to `candidate_commit`. Round 1 is now governed
   by `execution_base_commit`, so it was replaced by three sharper tests (wrong
   branch SHA, candidate outside the base, candidate declared without a branch).
3. **`_prepare_worktree()` and `_execute_claimed()` no longer take `ready_sha`.**
   Keeping an unused parameter would have implied the control revision still
   selects the product starting revision. `ready_sha` is still used by
   `_claim()`/`_stop_at_round_limit()` to sync the control branch.
4. **Test-side evidence emission.** The two-round test writes
   `.agent_runtime/base_semantics_summary.json` (git-ignored) and prints a
   `BASE_SEMANTICS_SUMMARY` line, because the requested summary must contain
   Round-1/Round-2 SHAs that only exist inside a run. The file is written only
   after every assertion in that scenario has passed.
5. **Out-of-scope observation, not modified.** `.agent/examples/dummy/README.md`
   (outside the Allowed list) describes the planner's state edits and now omits
   `execution_base_commit`. It is a one-line documentation follow-up.
6. **This task's own Round-1 `provenance.json` will not carry the new field.** The
   Controller that publishes this round is the still-deployed pre-repair one (see
   the task's Bootstrap Note), so its `provenance.json` is generated by the old
   code. The evidence for `execution_base_commit` in `provenance.json` is the
   fixture test and `base_probe.log`; every provenance written by the repaired
   Controller contains the field. This is expected, not a defect of the repair.

## Assumption / Modeling Impact

None. The change is Controller infrastructure only: no LBM solver, boundary
condition, initial condition, convergence rule, wettability interpretation, or
scientific claim scope is touched, and no default physical parameter changes.
No file outside `.agent/` was modified, and `git show --stat` on the candidate
commit lists exactly the four allowed paths. No GPU work, no simulation, and no
Taichi dependency was involved.

## Existing Evidence Potentially Affected

- Earlier task/review/evidence records under `.agent/tasks/` are untouched and
  remain readable. The new schema requirement does apply to the *live*
  `.agent/state.json`: a planner must now write `execution_base_commit` when
  queueing any non-draft state, or the Controller refuses to run. The queued
  state for this task already satisfies it.
- The Controller clone executes whatever `.agent/controller/controller.py` the
  control branch holds. Until this candidate is merged/accepted there, the
  deployed Controller keeps the old behaviour; the fix takes effect for the
  Controller that has the new file. This is a policy decision, not a defect.
- `.agent/examples/dummy/README.md` documentation is now slightly stale (see
  Deviation 5).
- No CG3D scientific result, benchmark, or validation becomes stale.

## Unresolved Issues / Human Decisions

- Whether and when to merge these Controller changes (reserved to the human).
- Future integration-branch policy and any automatic merge/DAG/dependency design
  (explicitly out of scope, unchanged).
- `## Execution Base` in `TASK.md` remains documentation for planners; the state
  field stays authoritative and no Markdown parser was introduced, as instructed.

## Suggested Next Action

Run the fresh independent review of candidate
`bdf0ad5bc267e905b751f18b3f81205cef1e9073` (Round-1 execution-base enforcement);
on `PASS`, the next parent task can declare its `execution_base_commit` in state
and no longer needs a manually pre-created task branch.
