# REVIEW

## Binding

- **Task ID:** `ADS-EXECUTION-BASE-005`
- **Candidate / commit:** `bdf0ad5bc267e905b751f18b3f81205cef1e9073`
- **Execution report:** `.agent/tasks/ADS-EXECUTION-BASE-005/round-01/EXECUTION_REPORT.md`

## Coverage

Inspected:

- task contract and live state;
- candidate diff and changed-file scope;
- `validate_state`, `_round_start_head`, `_prepare_worktree`, `_execute_claimed`;
- process/provenance generation;
- Controller test changes;
- durable executor evidence, including base-semantics summary and pre-repair negative control.

Not independently rerun:

- the Controller test suite on the Windows worker.

## Requirement Review

| Requirement | Status | Review |
|---|---|---|
| First-class `execution_base_commit` | PASS | Required in state; active states require a full lowercase 40-char SHA, DRAFT may use null. |
| Round 1 starts from declared base | PASS | Fresh branch creation uses `execution_base_commit`, not control READY SHA. Existing local/remote Round-1 branches must already equal the declared base. |
| Pre-execution head assertion | PASS | `_execute_claimed` recomputes actual worktree HEAD and rejects any mismatch before invoking Z Code. |
| Later rounds continue from candidate | PASS | `_round_start_head` returns `candidate_commit` for round > 1; remote branch and actual worktree HEAD are checked. |
| Base immutable across rounds | PASS | State transitions copy the field unchanged; two-round fixture verifies this end to end. |
| Process evidence includes base | PASS | Repaired Controller writes both `before_head` and `execution_base_commit`. |
| Executor provenance includes base | PASS | Repaired Controller-generated provenance binds execution base alongside candidate/session/worker. |
| Existing evidence/scope/timeout/session/max-round behavior retained | PASS | 28-test suite passes; relevant existing tests remain present. |
| Docs/template updated | PASS | README and TASK template explain the new field and semantics. |
| No CG3D product-code changes | PASS | Controller evidence shows only the four allowed `.agent/` files changed. |

## Key End-to-End Invariant

The strongest fixture deliberately makes:

- control READY SHA != execution base;
- Round 1 before_head == execution base;
- Round 1 candidate parent == execution base;
- a file existing only on the control READY commit is absent from the Round-1 candidate;
- Round 2 before_head == Round-1 candidate;
- execution base remains unchanged across rounds.

This directly tests the bug class identified by the fresh V1 review rather than merely unit-testing helper functions.

## Findings

### Blocking

None.

### Non-blocking

1. **Bootstrap provenance limitation.** This task itself was executed/published by the pre-repair Controller, so this round's own top-level `provenance.json` cannot contain `execution_base_commit`. This is expected bootstrap behavior. The repaired behavior is demonstrated by the Controller integration tests and published probe.
2. **Windows timeout-test noise.** The 28-test log contains one background `UnicodeDecodeError` from a Windows subprocess reader during the timeout scenario. The suite still completes 28/28 OK and the timeout assertion verifies the executor process is gone. The decoding path is pre-existing Controller code and was not changed by this task. It should be cleaned up separately if recurrent, but it does not invalidate execution-base semantics.
3. **Dummy example documentation.** `.agent/examples/dummy/README.md` is now slightly stale because it does not mention `execution_base_commit`; it was outside this task's allowed scope.

## Test-Quality Review

The new base-selection tests are not vacuous:

- post-repair tests against the pre-repair Controller fail materially;
- the negative control reports 13 failures / errors where the old Controller lacks or violates the new semantics;
- unrelated tests continue to pass in that control run.

The main two-round fixture is especially useful because it proves both halves of the protocol: a distinct parent-task starting revision for Round 1 and candidate continuation for Round 2.

The two platform-specific test repairs are acceptable:

- replacing `os.kill(pid, 0)` with an explicit Windows liveness probe preserves the intended timeout assertion;
- comparing evidence hashes against the published bytes rather than Git's line-ending-normalized blob better matches what provenance is intended to describe.

## Architecture Assessment

This repair resolves the fresh-review finding that cumulative-base selection was procedural rather than enforced.

After acceptance, the intended invariant is machine-checkable:

```text
Round 1:
  before_head == execution_base_commit

Round N > 1:
  before_head == prior reviewed candidate_commit

execution_base_commit:
  unchanged for the parent task
```

This is sufficient for V1. A DAG, merge manager, automatic integration graph, or dependency resolver is not required to close the identified reproducibility risk.

## Decision

PASS

## Decision Rationale

The candidate implements the requested first-class execution-base semantics with explicit state validation, Round-1 branch creation from the declared product revision, pre-execution head verification, later-round continuation from the reviewed candidate, and durable provenance. The test suite directly exercises the previously unsafe case where the control READY revision differs from the intended product base. No blocking defect was found.

## Next Action

CLOSE `ADS-EXECUTION-BASE-005`.

After closure, integrate/deploy this accepted Controller candidate onto the control branch before queueing the next parent task. The next new scientific task should then use the repaired protocol with an explicit `execution_base_commit` and can move into the scientific/numerical validation layer.
