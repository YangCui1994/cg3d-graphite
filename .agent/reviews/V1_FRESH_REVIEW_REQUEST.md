# V1 Fresh-Session Independent Review Request

## Purpose

Perform an independent repository review of the cumulative V1 candidate **without relying on the prior ChatGPT conversation**.

This is a reviewer task, not an executor task. Do not run Z Code and do not modify the repository unless the user explicitly asks after the review.

## Fixed Revisions

- Repository: `YangCui1994/cg3d-graphite`
- Baseline / current `master`: `9ede55c8ef7589b61606e11c033c84d9bcd1de94`
- Cumulative integration branch: `agent-dev/cg3d-v1-integration`
- Candidate to review: `645479e00217b1b50f6cd4ae5d833eda1661e84c`
- Control/evidence branch: `agent-dev/step0-protocol`

Review the fixed SHA, not a moving branch tip.

## Important Branch-Composition Note

The cumulative integration branch was originally created from the control/infrastructure branch and later accumulated the accepted scientific-code candidates.

Therefore `master..645479e` contains two logically different categories:

1. **Agent Development System / Controller infrastructure**
   - `.agent/**`
   - `AGENTS.md`
   - related control/evidence protocol files
2. **CG3D product/scientific-code changes from Tasks 1–4**
   - runtime lifecycle
   - periodic connected-component topology
   - convergence/termination diagnostics
   - cumulative integration test

Review and report these categories separately. Do not treat control/evidence files as if they were scientific-code modifications.

## Independent-Review Ordering

To reduce anchoring bias:

1. Read this request.
2. Inspect the candidate source and `master..candidate` diff.
3. Read each TASK contract.
4. Form your own findings.
5. Inspect controller/executor evidence.
6. **Only after you have your own preliminary findings**, read the existing `REVIEW.md` files and compare your conclusions.

Do not start by trusting or summarizing previous reviewer conclusions.

## Task Contracts to Inspect

On `agent-dev/step0-protocol`:

### Task 1 — runtime lifecycle

- `.agent/tasks/CG3D-TAICHI-INIT-001/round-01/TASK.md`
- `.agent/tasks/CG3D-TAICHI-INIT-001/round-02/TASK.md`

Accepted candidate:
`05de9981a9d671c866ec2135e7a470d48752f79c`

Primary questions:

- Is import-time `ti.init()` genuinely removed?
- Is runtime initialization explicit and idempotent?
- Are shared Taichi lattice tables initialized safely and in the correct order?
- Are there hidden import-order or multi-instance hazards?
- Did the change alter solver numerics or only lifecycle?
- Does the public API remain coherent?

### Task 2 — periodic connected-component topology

- `.agent/tasks/CG3D-PERIODIC-CONN-002/round-01/TASK.md`

Accepted candidate:
`62219270d5d3c29dc522103e262718c77332b233`

Primary questions:

- Is `label_periodic` topologically correct for 6/18/26 connectivity?
- Are simultaneous two-axis and three-axis wrapped neighbours handled correctly?
- Can non-periodic axes be wrapped accidentally?
- Are component sizes/relabeling semantics preserved?
- Look for edge cases not covered by the provided oracle, including very small domain dimensions.

### Task 3 — termination / numerical-health reporting

- `.agent/tasks/CG3D-CONVERGENCE-DIAG-003/round-01/TASK.md`

Accepted candidate:
`3e49087e195ac98b41000bc647b115c685daa71b`

Primary questions:

- Are `termination` and `numerical_health` genuinely additive?
- Is the existing stopping policy untouched?
- Is `converged` defined only by the existing quasi-steady reason?
- Are max-step and finite umax-cap exits classified correctly?
- Can the health tracker itself alter control flow or raise unexpectedly on realistic values?
- Are historical rows/backward compatibility handled reasonably?

### Task 4 — cumulative integration validation

- `.agent/tasks/CG3D-V1-INTEGRATION-004/round-01/TASK.md`

Accepted candidate:
`645479e00217b1b50f6cd4ae5d833eda1661e84c`

Primary questions:

- Is `tests/test_v1_integration.py` a meaningful integration test rather than a self-confirming test?
- Does it invoke accepted public paths rather than duplicate implementation logic?
- Does it cover import order, runtime boundary, solver construction, checkpoint, topology, and run_hold compatibility appropriately?
- Are there important integration interactions it fails to cover?

## Controller / Evidence Infrastructure

Also review the V1 evidence trust boundary at a high level.

Relevant files on the candidate/control branch include:

- `.agent/controller/controller.py`
- `.agent/prompts/ZCODE_EXECUTOR.md`
- `.agent/state.json`
- `.agent/README.md`

Check especially:

- controller-observed evidence vs executor-published evidence separation;
- manifest/path/size/symlink constraints;
- candidate SHA binding;
- Controller-generated SHA-256 provenance;
- whether executor evidence could be confused with independently observed proof;
- state-machine behavior around evidence-publication failure;
- cumulative integration-base handling.

Known architectural issue to assess independently:

> New parent tasks do not yet have a first-class Controller field for an accepted cumulative base. The current V1 used a manually prepared `agent-dev/cg3d-v1-integration` branch.

Determine whether this is merely a workflow inconvenience or a correctness/reproducibility risk for continued development.

## Evidence to Inspect

On `agent-dev/step0-protocol`, inspect each task's:

- `EXECUTION_REPORT.md`
- `evidence/controller/**`
- `evidence/executor/**` when present

Task 4 is the strongest cumulative bundle:

`.agent/tasks/CG3D-V1-INTEGRATION-004/round-01/evidence/`

It includes:

- cumulative integration log;
- import-lifecycle regression;
- Level A;
- post-processing;
- periodic topology;
- termination diagnostics;
- checkpoint/resume;
- machine-readable integration summary;
- Controller-generated provenance.

Treat executor logs as executor evidence, not as equivalent to an independently rerun command.

## Scientific Scope

Do **not** claim that these V1 tasks validate the full physical fidelity of the two-phase color-gradient LBM model.

The current review should distinguish:

1. software correctness;
2. numerical/integration regression evidence;
3. topology/post-processing correctness;
4. convergence-reporting semantics;
5. physical-model validation that remains untested.

Do not infer physical equilibrium merely from `termination.converged=true`.

Do not treat Level A or checkpoint/resume as a substitute for Laplace-law, contact-angle, displacement, or real-geometry scientific validation.

## Review Questions

At minimum answer:

1. Are there any **blocking correctness defects** in the cumulative candidate?
2. Are there any **non-blocking design/code-quality risks** worth fixing before further scientific validation?
3. Are the existing validations sufficient for the claims they actually make?
4. What important claim is currently **not** supported by evidence?
5. Is the evidence/provenance architecture trustworthy enough for V1 use?
6. Does the cumulative integration-base workflow need to be fixed before starting more tasks?
7. What should the **next validation layer** be:
   - more software regression,
   - fresh numerical benchmark,
   - physical/scientific validation,
   - or infrastructure repair first?

## Output Format

Use:

### Scope reviewed

### Blocking findings
For each finding:
- severity;
- file/function;
- concrete mechanism;
- why it matters;
- evidence.

### Non-blocking findings

### Evidence gaps

### Scientific-validation boundary

### Infrastructure assessment

### Independent verdict

Use exactly one of:

- `PASS`
- `PASS WITH FOLLOW-UPS`
- `CHANGES REQUESTED`

Then give the smallest justified next action.

Do not merge branches or modify code during this review.
