# Scientific Development Episode Contract v0.1

Episode ID: BI-VALIDATION-001

## 1. Goal

Establish whether the current CG3D solver and a lightweight local executor/reviewer loop can support closed bilateral spontaneous imbibition without immediately introducing a large real-electrode domain.

The episode answers four questions in order:

1. Is the current repository baseline healthy on the Windows GPU execution machine?
2. Does the existing wall-colour wetting implementation reproduce resolved spontaneous capillary filling dynamics?
3. Can two symmetric wetting fronts advance toward each other without unacceptable asymmetry, mass loss, instability, or opaque interface-collision artefacts?
4. Are the intended finite liquid buffers and closed outer walls sufficiently insensitive to buffer size to justify moving to a complex porous geometry?

The episode ends after V3. It does not automatically enter the real graphite/PCS problem.

## 2. Scientific scope

### Fixed for this episode

- Solver family: current D3Q19 MRT color-gradient CG3D implementation.
- Existing calibrated surface tension and wall-colour wettability infrastructure are reused.
- Baseline phase-density ratio remains the current unit-ratio formulation.
- Baseline viscosities remain the currently validated matched-viscosity configuration unless a stage explicitly says otherwise.
- No externally imposed pressure difference in V2/V3.
- Outer finite-buffer ends in V2/V3 are explicit solid/bounce-back walls.
- Synthetic geometries must be comfortably resolved relative to the approximately 2.2 lu interface width.
- Real graphite, separator morphology, Cu geometry, interface-gap sweep, and PCS particles are excluded from this episode.

### Scientific interpretation boundary

The enclosed non-wetting phase is a second weakly-compressible CG phase. Pocket pressure/density/volume are numerical diagnostics of model admissibility and topology. They must not be presented as a quantitatively validated real-air compression law.

A two-front collision is not assumed physically correct merely because the solver remains stable. Interaction-distance, coalescence, and local-current behaviour must be reported.

## 3. Orchestration model

The Windows machine hosts one lightweight Episode Runner and two role types:

- ZCode Executor: implementation and authorized runs.
- ZCode Reviewer: independent fresh-context inspection and authorized verification.

Both may use the same underlying GLM model and machine. Independence is created by role separation, fresh reviewer sessions, candidate binding, and restricted reviewer write permissions.

### Executor context

Round 1 of a stage starts in a fresh executor session.
A rework round may resume the stage executor session to preserve implementation context.
If the reviewer requests RESET_CONTEXT, or if the runner detects a corrupted/overgrown executor context, rework starts in a fresh executor session.

### Reviewer context

Every review round starts in a fresh ZCode session.

The reviewer receives only:
- the global Episode Contract;
- the current Stage Contract;
- the candidate commit SHA;
- the relevant source/diff;
- the execution report;
- raw or summarized validation evidence;
- previous REVIEW.md only when reviewing a rework round.

The reviewer must not receive the executor conversation transcript or executor chain-of-thought.

## 4. Candidate binding

Every executor round must end at a Git commit before review.

The review must bind to exactly one candidate SHA.

A reviewer may inspect or execute against that candidate, but may not modify production code.

A later code change creates a new candidate and invalidates the previous PASS decision.

## 5. Stage state

Each stage uses:

READY
-> EXECUTING
-> CANDIDATE_READY
-> REVIEWING
-> PASS | CHANGES_REQUESTED | HUMAN_REQUIRED

PASS promotes to the next stage.
CHANGES_REQUESTED starts a bounded rework round.
HUMAN_REQUIRED stops the episode.

Maximum candidate attempts per stage: 3.

After the third non-PASS review, the stage becomes HUMAN_REQUIRED even if the remaining issue appears fixable. The goal is to prevent indefinite self-iteration.

## 6. Decision semantics

### PASS

PASS means:
- all hard gates in the Stage Contract are satisfied;
- required evidence exists and is bound to the reviewed candidate;
- no blocking reviewer finding remains;
- diagnostics contain no unexplained anomaly that changes the scientific meaning of the next stage;
- no unresolved decision requires changing a fixed assumption.

PASS does not mean the model is universally validated.

### CHANGES_REQUESTED

Use only when:
- a requirement is unmet;
- the fix stays inside the current stage scope;
- the scientific assumptions remain unchanged;
- the reviewer can state a finite corrective action.

### HUMAN_REQUIRED

Mandatory when:
- the proposed fix changes a scientific assumption, BC meaning, or interpretation boundary;
- two materially different implementations are both defensible and the contract does not choose;
- a hard gate fails for a reason that may reveal a solver/model limitation;
- a diagnostic anomaly is large enough that promotion would require a new acceptance rule;
- the stage exceeds three candidate attempts;
- provenance/candidate identity is uncertain.

## 7. Git model for the first episode

The planning documents live on agent-dev/bilateral-episode-v0.1.

When execution is authorized, the Episode Runner creates one product branch from the declared product execution base, suggested name:

agent-episode/BI-VALIDATION-001

Executor candidate commits accumulate on that branch.

Reviewer reports and runtime evidence are kept outside the product diff during a running round. At every stage PASS, HUMAN_REQUIRED, crash-recovery checkpoint, and final V3 checkpoint, the runner publishes durable stage records to the control/evidence plane and pushes the product branch.

No automatic merge to master.
No force-push.
No history rewrite.

## 8. Evidence model

Every stage must preserve:

- STAGE_CONTRACT.md snapshot or content hash;
- candidate SHA;
- EXECUTION_REPORT.md;
- REVIEW.md;
- exact validation commands;
- exit codes;
- key numerical metrics;
- artifact manifest;
- relevant plots/data summaries;
- known diagnostics without pass/fail thresholds;
- changed-files and diff summary.

Large raw simulation data may remain on the Windows machine if the manifest records its location and hashes. Small reviewer-facing summaries should be durable in GitHub.

## 9. Stage sequence

### A0 — runner bootstrap

Implement only the minimal local orchestration needed for role isolation, candidate binding, bounded rework, and stage promotion. See RUNNER_BOOTSTRAP.md.

A0 is infrastructure, not scientific validation.

### V0 — baseline

Run the existing regression suite on the actual Windows/GPU environment. No solver scientific change is authorized merely to make the baseline pass.

### V1 — dynamic wetting

Add a resolved synthetic single-front spontaneous-filling verification. Compare the post-transient front trajectory with the appropriate Lucas-Washburn relation.

### V2 — bilateral front interaction

Use a deliberately simple symmetric channel/slit. Two finite liquid regions drive capillary filling from opposite ends toward a central non-wetting phase. Record pre-interaction symmetry and post-isolation/collision diagnostics.

### V3 — buffer sensitivity

Repeat the bilateral synthetic case with multiple finite liquid-buffer thicknesses. Determine whether front dynamics and trapped-phase/topology observables are materially controlled by the outer closed boundaries.

### Mandatory checkpoint

Stop after V3 even if all stages pass.

ChatGPT + user review:
- V1 dynamic-wetting quality;
- V2 collision behaviour;
- V3 buffer dependence;
- unit-density trapped-phase interpretation;
- readiness to design the porous-media episode.

## 10. Post-checkpoint porous-media roadmap — not authorized by this contract

A future Episode v0.2 may contain:

P0. geometry/material infrastructure:
- material_id field in geometry artifact;
- graphite;
- Cu hard solid;
- unresolved separator hard BB;
- configurable interface gap;
- PCS optional.

P1. real graphite + gap, PCS off.
P2. same with artificial PCS annular/hollow-disk geometry.
P3. configurable gap capability, nominal 5 / 10 / 20 micrometres.
P4. bounded production simulation matrix.
P5. trapped-gas/topology/interface-location post-processing.
P6. visualization and scientific checkpoint report.

No P-stage should run before the V3 human checkpoint.

## 11. Fixed first-version design decisions

- Reviewer is ZCode/GLM but always fresh-context.
- Executor and reviewer are not the same session.
- Reviewer cannot edit product code.
- Reviewer can run authorized checks.
- Reviewer decisions bind to commit SHA.
- Three candidate attempts maximum per stage.
- Stage PASS may auto-promote through V0-V3.
- V3 PASS cannot auto-promote to porous-media work.
- Scientific thresholds not supported by the evidence package must be labelled project engineering gates or remain diagnostics.
- The later GPT-6 Pro review is a framework audit after real execution evidence exists, not a prerequisite for this first episode.

## 12. Stop conditions

Stop immediately and publish HUMAN_REQUIRED if any of the following occurs:

- NaN/Inf in a scientific validation trajectory;
- repeated density collapse or solver divergence;
- candidate/evidence mismatch;
- reviewer cannot reproduce or trace a claimed hard-gate result;
- V1 cannot establish a defensible post-transient capillary-filling regime;
- V2 exhibits unexplained large left/right asymmetry in an exactly symmetric setup;
- V2/V3 require redefining the physical boundary conditions to continue;
- trapped-phase behaviour clearly exceeds the declared weak-compressibility interpretation boundary;
- runner cannot guarantee fresh reviewer isolation;
- stage attempt count exceeds 3.

## 13. Success state

The episode is successful when V0, V1, V2, and V3 have PASS reviews and the final checkpoint package is published.

Success means the project has enough controlled evidence to design the real porous-media/PCS episode. It does not mean the final battery-filling model is validated.
