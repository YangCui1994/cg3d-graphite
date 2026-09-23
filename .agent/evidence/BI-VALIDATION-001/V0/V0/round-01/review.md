stage: V0
attempt: 1
candidate: 280a46fed488b12975c3de96b5493362942822ec
execution_report: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/real/V0/round-01/execution_report.md

# REVIEW — BI-VALIDATION-001 / stage V0 / attempt 1

Reviewer: independent ZCode session, fresh context. Write restriction respected: this
review file plus `reviewer_evidence/` only; no product file, commit, branch, test or
executor artifact was modified.

## binding

The review binds to candidate `280a46fed488b12975c3de96b5493362942822ec`.

| Binding item | Value | Verification |
|---|---|---|
| HEAD in reviewer worktree | `280a46fed488b12975c3de96b5493362942822ec` | `git rev-parse HEAD` — identical to the frozen candidate |
| Worktree state | clean | `git status --porcelain` and `git diff HEAD --stat` both empty |
| Declared product base | `9ede55c8ef7589b61606e11c033c84d9bcd1de94` | control plane `episode_state.json:5`; matches the execution report's base |
| Commits base..candidate | exactly one | `git log --oneline 9ede55c..HEAD` |
| Diff at the candidate | `tests/levelb_laplace.py`, 4 insertions / 4 deletions | `git show 280a46f`; whole-tree `git diff --stat 9ede55c 280a46f` shows the same single file |
| Contract snapshot | sha256 `b87368bca1ab70ca6f92206d04cae8be89b43c6517fe0d88b6ee893fc2be5d64` | measured against the snapshot file named in this round's brief |
| Evidence integrity | 21/21 harness files listed in `MANIFEST.txt` verify by `sha256sum -c` | plus both `tests_output/` scratch hashes, checked before the reviewer re-run |

Candidate identity is certain: the source tree matches the reviewed SHA, and the SHA is
the declared candidate. No provenance question arises.

## coverage

### Requirement table (frozen V0 Stage Contract)

| # | Requirement | Status | Evidence |
|---|---|---|---|
| R1 | Prefer no product changes; environment/runner fixes only if they do not alter solver numerics; a solver-physics change requires HUMAN_REQUIRED | Satisfied under ruling R-A1 below | one product file changed (test-file epilogue, one token); see findings |
| R2 | Run the six required validations (`run_level_a.py`, `test_compute_c_bulk.py`, `test_poiseuille_cg3d.py`, `levelb_laplace.py`, `levelb_contact_angle.py`, `test_postprocessing.py`) | Met — 6/6, twice | executor logs + reviewer re-run (`reviewer_evidence/rerun_*.log`) |
| R3 | Use the documented GPU/JIT execution rules | Met | one solver instance per process, separate processes, sequential, cwd = worktree root; every log shows `arch=cuda` |
| R4 | Hard gate: every required test exits successfully | Met | 6/6 exit 0 in both runs |
| R5 | Hard gate: Laplace regression meets its existing thresholds (`rel < 0.03`, `R2 >= 0.999`) | Met | executor rel 0.29 %, R2 1.00000; reviewer rel 0.49 %, R2 1.00000 |
| R6 | Hard gate: contact-angle regression meets its thresholds (`30 ± 6°`) | Met | executor 30.3°, reviewer 30.8° |
| R7 | Hard gate: Poiseuille/forcing regression meets its thresholds (`eff ∈ [0.97, 1.03]`, `L2 < 5 %`) | Met | eff 0.9933, L2 0.0075 in both runs |
| R8 | Hard gate: no NaN/Inf or unexplained crash | Met | no NaN/Inf anywhere; the single base-SHA crash is fully explained and independently reproduced |
| R9 | Hard gate: product source scientifically identical to the declared base unless an authorized fix was required | Met | whole-tree diff is one test file; solver/BC/IC/wettability/convergence files byte-identical to base |
| R10 | Capture the required diagnostics (GPU/backend, versions, per-test wall time, JIT behaviour, nondeterministic spread) | Met | `environment.txt`, `jit_probe.json`, per-test logs, §6 of the report; one documentation staleness note (F1) |

### Validation table

| Validation | Executor result | Reviewer re-run | Agreement |
|---|---|---|---|
| `tests/run_level_a.py` | exit 0, 9.6 s, "LEVEL A: ALL PASS" | exit 0, 10 s, same five checks | yes |
| `tests/test_compute_c_bulk.py` | exit 0, 2.3 s | exit 0, 2 s | yes |
| `tests/test_poiseuille_cg3d.py` | exit 0, 15.8 s, eff 0.9933, L2 0.0075 | exit 0, 16 s, identical | yes |
| `tests/levelb_laplace.py` | exit 0, 196.0 s, σ rel 0.29 %, R² 1.00000 | exit 0, 196 s, σ rel 0.49 %, R² 1.00000 | yes (spread inside band) |
| `tests/levelb_contact_angle.py` | exit 0, 18.0 s, θ = 30.3° | exit 0, 18 s, θ = 30.8° | yes |
| `tests/test_postprocessing.py` | exit 0, 0.6 s | exit 0, 0 s | yes |
| Base-SHA reference run | test 4 exits 1 with `TypeError` | not re-run (reviewer may not check out a different source state); base diagnosis verified by other means, see §5 of the evidence file | n/a |

The reviewer re-run used the same production entry points as the executor and as
`tests/README.md` — the test files themselves, one process each, from the worktree root.
No test logic was reimplemented for the verification.

## findings

### Blocking findings

None.

### Non-blocking findings

**F1 — `tests/README.md` JIT guidance is quantitatively stale.**
The file states "Every `ColorGradientSolver3D` instance pays ~5.5 min JIT on this machine"
(`tests/README.md:28`). The executor's probe measured ≈ 7 s for the first instance in a
fresh process and 362.9 s for a second instance in the same process. Six independent test
processes each paid only ≈ 7 s, which is consistent with their total wall times, and my
own re-run reproduces the same pattern (test 3 = 16 s total for 20 000 steps; test 4 = 196 s
for three converged cases). The rule the README derives is still correct and still worth
following — the expensive case is the second instance in one process — but the "~5.5 min
per instance" figure is wrong and should be corrected in a later documentation pass.
This is a documentation claim; it changes no gate.

**F2 — The recorded PR-4 Laplace result overstates the health at the base SHA.**
`docs/CHANGELOG_NUMERICS.md:80-81` records the Laplace quick sweep as
"sigma = 0.0609 … 0.32% rel, R^2 = 1.00000". Those numbers are real — they were printed
before the crash — but the process that produced them always exited 1 because of the
`np.save` epilogue, and no verdict was ever emitted. So the changelog's implied suite
status was never backed by a clean exit until this candidate. Worth a one-line note when
the changelog is next touched; it does not change the V0 result, and the candidate now
reproduces the recorded calibration (0.0609/0.0610 across runs).

**F3 — Run-to-run spread and a non-reproducible termination rule (diagnostics, no threshold challenged).**
Two spreads are visible across the three runs of this configuration available to me
(base, executor candidate, reviewer candidate): Laplace σ relative error 0.25 % / 0.29 % /
0.49 % (threshold 3 %) with R_eff differing in the 2nd decimal (22.04 / 22.05 / 22.03),
and contact angle 32.1° / 30.3° / 30.8° (band 30 ± 6°). The contact-angle test's early-exit
stability rule fired at 8250 steps in the base run but ran to the 12 000-step cap in both
candidate runs. This matches the repository's own statement that GPU f32 atomics make
accumulation order nondeterministic, and every value stays several times inside its band,
so nothing here challenges a gate. Flagged because it is exactly the behaviour the V0
diagnostics are asked to surface, and because a later stage that depends on contact-angle
reproducibility would need to look at the stability detector rather than at the physics.

**F4 — A seventh test file exists that the contract's list of six omits.**
`tests/test_checkpoint_resume.py` (PR-7 checkpoint/resume, commit `d8ebde3`) sits in
`tests/` but is not in the Stage Contract's enumeration and is not in the documented
suite in `tests/README.md:14-21`, which lists exactly the six tests that were run. The
executor's coverage therefore matches both the contract and the repository's own
documented suite, and this is not an executor gap. I did not run it as an extra check:
it forces `LBM_ARCH=cpu` and drives real `run_pcs_cg3d`/`run_ir_cg3d` subprocesses that
write into run output directories, and the project guardrails forbid reusing an existing
simulation directory without explicit authorization. Recorded so the omission is a
recorded decision rather than an unnoticed one. If a later stage depends on
checkpoint/resume, its contract should name that test explicitly.

**F5 — Taichi offline-cache location could not be determined** (executor §6.1). No gate
depends on it; the wall-time evidence is reported directly instead of being attributed to
a cache hit. Not blocking.

### Scientific / modeling review

- **Does the candidate still represent the intended physical problem?** V0 introduces no
  new physics; it re-runs the existing Level A/B regressions. The candidate's one change
  does not touch any solver input. Solver, boundary, initial-condition, wettability,
  surface-tension, viscosity and convergence defaults are byte-identical to the declared
  base (whole-tree diff = one test file; module hashes verified against the manifest).
- **Are BCs and initial conditions what the contract says?** V0 asserts this by proxy:
  Level A checks the MRT matrix inverse, uniform-phase stationarity (max|v| = 0, ψ deviation 0),
  colour-mass conservation (3.58e-07 against a 5e-6 threshold), reservoir pinning
  (ρ = 1.05000, ψ = 1.0000) and membrane blocking. All pass at the candidate and at base.
- **Are dimensions and phase semantics correct?** Unchanged by this candidate; the Laplace
  sweep reproduces the parent calibration σ = 1.012·CapA within 0.5 %, which is the
  dimensional consistency check this suite provides.
- **Is the claimed observable defined unambiguously?** The changed line writes an archive;
  it defines no observable. The written archive is valid and readable, which the base
  version could never produce.
- **Is convergence established where required?** Laplace converged in all three radii via
  the test's own rule (|ΔdP|/|dP| < 0.004 sustained for 1500 steps) at 7500 / 8500 / 9500
  steps — reproduced in both runs. Poiseuille samples from a fixed 20 000-step cap by
  design. Contact angle reached the step cap in the two candidate runs (F3). No run
  diverged and no run hit a timeout.
- **Is mass-conservation evidence consistent with the model?** Level A A3 colour-mass
  relative drift 3.58e-07, an order of magnitude inside its threshold, reproduced exactly
  at both SHAs and in my re-run.
- **Are diagnostic anomalies explained before promotion?** Yes. The only anomaly is the
  base-SHA crash, and it is fully explained: `np.save` has never accepted named arrays
  (I confirmed the `TypeError` directly under numpy 2.2.6), the call site is a write-only
  epilogue after the verdict computation, and the parent driver it was ported from calls
  `np.savez` with an identical argument list. The base run printed the same physics values
  as the candidate before dying.
- **Has a code change invalidated existing validation evidence?** No. Nothing reads the
  written archive, nothing imports the changed test as a module, and the changed line
  executes after the acceptance computation. Every prior numerical statement in
  `docs/CHANGELOG_NUMERICS.md` about the Laplace calibration is reproduced by the candidate.

### Ruling on the single deviation (R-A1) — the explicit question the executor referred to review

The executor disclosed and asked for a ruling on one thing: whether repairing
`np.save` → `np.savez` in `tests/levelb_laplace.py` counts under the V0 clause
"Any proposed solver-physics or existing regression change requires HUMAN_REQUIRED".

Reviewer ruling: it does not. The repair falls under the permitted category
"Environment/runner fixes may be made only if they do not alter solver numerics".
The basis for this reading, in order of weight:

1. Hard gate 9's operative requirement is that the product source "remains scientifically
   identical to the declared base". It does — the changed line is a post-verdict,
   write-only artifact dump that no code path reads. The following "unless" clause is a
   carve-out that excuses a byte difference; it is not a second, independent requirement,
   and it is not needed here because the scientific identity holds.
2. The clause's evident purpose is to stop an executor from editing the science or from
   weakening a regression to make it pass. This repair does the opposite: at the base SHA
   the test could not emit a verdict at all (it always exited 1 regardless of the physics),
   so the repair *increases* the regression's discriminating power. Every threshold, case,
   reference value and the acceptance expression itself are verified unchanged.
3. The repair is provenance-correct rather than invented: it restores the parent driver's
   own call (`validation_cg3d_laplace.py` uses `np.savez` with the identical argument list).
   Among the ways to handle a broken epilogue, this is the minimal restoration and is
   consistent with "prefer no product changes".
4. The strict alternative reading makes the stage unsatisfiable. Under it, the base SHA
   fails hard gate 1 and the only corrective action (revert) restores that same failure —
   no candidate could satisfy every gate and no in-scope rework could produce one. V0
   would be a permanent dead end for a purely non-scientific reason.
5. No enumerated HUMAN_REQUIRED trigger fires. The fix changes no scientific assumption,
   BC meaning or interpretation boundary; no hard gate fails for a reason suggesting a
   solver or model limitation (the physics regression itself produced its calibration
   values at base); no diagnostic anomaly requires a new acceptance rule; provenance and
   candidate identity are certain; this is attempt 1 of 3.

This is a ruling on a genuinely ambiguous contract line, and it is recorded as such rather
than presented as settled fact. The human may override it; the override path is a one-token
revert of `280a46f`, which returns the stage to a base-SHA hard-gate failure needing a human
decision on how to proceed.

### Missing evidence

- No pre-authorization for reviewer GPU execution exists in the V0 Stage Contract; I
  performed the re-run under the reviewer allowance for authorized checks, at a cost of
  about four minutes of GPU on an otherwise idle machine, because hard gate R4 is the
  central claim of this stage and the reviewer emphasis asks that test outputs be tied to
  the reviewed candidate.
- The claim that no two GPU simulations overlapped cannot be proven from logs alone; the
  evidence is consistent with it (sequential ordering, per-test wall times, 15 % idle GPU
  utilisation recorded between runs).
- The JIT probe measured one shape (N = 32), not the shape of every test; adequate for the
  diagnostic purpose, not a systematic JIT model.
- The reviewer re-run regenerated the two gitignored `tests_output/` scratch artifacts; the
  executor's originals are preserved verbatim under `reviewer_evidence/pre_rerun_scratch/`
  with manifest-verified hashes, so the manifest stays checkable. This is the only state
  change this review made anywhere.

## decision

Decision: PASS

## rationale

Every hard gate in the frozen V0 Stage Contract is satisfied at the candidate, and the
satisfaction is established independently rather than taken from the execution report:
I re-ran all six required validations at `280a46f` through the documented production entry
points and obtained 6/6 exit 0 with the Laplace, contact-angle and Poiseuille metrics all
several times inside their existing repository bands. Candidate identity is certain
(HEAD equals the declared candidate; the declared base equals the runner's recorded
`product_base`), the diff is exactly the one file and four lines the report claims, and
every non-scratch evidence hash in the manifest verifies.

The one deviation is disclosed, minimal, and scientifically inert: a porting typo in a
write-only artifact epilogue that crashed after the verdict had already been computed.
It touches no solver, boundary condition, initial condition, threshold, case or reference
value, it is not read by any code path, and it restores the parent driver's own call. Its
practical effect is that the Laplace regression can report a verdict for the first time
since it was written, which strengthens rather than weakens the suite. I therefore rule it
a permitted harness repair (ruling R-A1) rather than an existing-regression change, and no
HUMAN_REQUIRED trigger in the Episode Contract applies.

No blocking finding remains, no diagnostic anomaly changes the meaning of the next stage,
and no unresolved decision would require changing a fixed assumption. The residual items
(F1–F5) are documentation and diagnostic notes; none of them alters a gate or a scientific
statement, and F2 is resolved in practice by this candidate. This acceptance means the
declared baseline is healthy on this machine as reviewed; it is not a statement that the
model is validated.

## next action

Promote V0 → V1 per the stage contract's promotion clause, with these carry-forwards:

1. Write the R-A1 ruling into the stage record so the interpretation is durable: the
   candidate's single-line harness repair was reviewed and accepted, not overlooked.
2. Add the F1 documentation correction (stale JIT figure in `tests/README.md`) and the F2
   changelog note to the next documentation pass; neither is worth a rework round of its own.
3. Have the V1 Stage Contract state whether any contact-angle reproducibility requirement
   is carried forward; if it is, F3's stability-detector behaviour needs attention before
   V1 relies on θ stability.
4. If a later stage depends on checkpoint/resume, name `tests/test_checkpoint_resume.py`
   explicitly in that stage's contract (F4).

If the human rejects the R-A1 ruling, the recovery is to revert `280a46f`; that returns
the stage to a base-SHA hard-gate failure on the Laplace test, at which point the stage
should be routed to HUMAN_REQUIRED, because the remaining cause is a test-harness defect
that the frozen contract does not authorize fixing without human sign-off.
