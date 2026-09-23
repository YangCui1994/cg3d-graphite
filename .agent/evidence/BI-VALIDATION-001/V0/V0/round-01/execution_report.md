# Execution Report — V0 Baseline on the Windows GPU Machine

**Episode:** BI-VALIDATION-001
**Stage / attempt:** V0 / attempt 1
**Branch:** `agent-episode/BI-VALIDATION-001`
**Base SHA:** `9ede55c8ef7589b61606e11c033c84d9bcd1de94` (tree clean at start)
**Candidate SHA:** `280a46fed488b12975c3de96b5493362942822ec`
**Stage Contract snapshot sha256:** `b87368bca1ab70ca6f92206d04cae8be89b43c6517fe0d88b6ee893fc2be5d64` (verified locally, matches)
**Date:** 2026-09-23, ≈21:34–21:57 (+08:00)

---

## 1. Outcome

**All V0 hard gates are satisfied at the candidate.** All six required tests exit 0 and
the Laplace, contact-angle and Poiseuille regressions satisfy their existing repository
thresholds.

One change was required to reach that state, and it is the **only** deviation in this
round: `tests/levelb_laplace.py` called `np.save(...)` with named arrays, which is not a
valid `np.save` signature, so every run of the Laplace regression died with a `TypeError`
*after* the acceptance fit had already been computed and printed — and therefore always
exited 1. The line is a transcription error from the parent driver, which calls `np.savez`
with the identical argument list; the candidate restores `np.savez`.

**This change does not touch solver code, any threshold, any reference value, any case
definition, or the acceptance expression.** `lbm_solver_cg3d.py`, `run_common.py` and the
drivers are byte-identical to the base. See §5 for the full justification and §9 for why
this is called out explicitly for the reviewer.

---

## 2. Changed files

```
 tests/levelb_laplace.py | 8 ++++----
 1 file changed, 4 insertions(+), 4 deletions(-)
```

```diff
@@ -129,10 +129,10 @@ def main():
               f'rel {rel*100:.2f}%), R2={r2:.5f}, intercept={b:.5f}')
         ok_all &= (rel < 0.03) and (r2 >= 0.999)

-    np.save(os.path.join(OUTROOT, 'laplace_data.npz'),
-            rows=np.array(rows, dtype=object),
-            sigma=np.array([results[c]['sigma'] for c in capas]),
-            capa=np.array(capas))
+    np.savez(os.path.join(OUTROOT, 'laplace_data.npz'),
+             rows=np.array(rows, dtype=object),
+             sigma=np.array([results[c]['sigma'] for c in capas]),
+             capa=np.array(capas))
     if not ok_all:
         print('FAIL: sigma deviates >3% from 1.012*CapA or R2 < 0.999')
         sys.exit(1)
```

sha256 of the changed file at the candidate:
`fcb03472b8f6f650c52fe53a70cc643053159e4f8df897ae7efa70329d136efc`

Unchanged at the candidate (sha256): `lbm_solver_cg3d.py`
`5dad458ff69517a37955fade467a585d2d7837af4343ebbf96500d7cfadf226b`, `run_common.py`
`9ef08b9e1ddbb9c57c6fac9c7683783ef823aef0e9255a052f12ef838c7f4c8a`, plus all five other
test files. Full list in `evidence/MANIFEST.txt`.

No commit was made to any other branch. No merge, no force-push, no history rewrite.

---

## 3. Commands run and exit codes

Run environment (from `evidence/environment.txt`):

- Windows 11 10.0.26200; NVIDIA GeForce RTX 5080, 16303 MiB, driver 595.95, CUDA 13.2.
- conda env `lbm`: Python 3.10.21, **taichi 1.7.4** (llvm 15.0.1, commit b4b956fd),
  numpy 2.2.6, scipy 1.15.3. `requirements.txt` pins `taichi==1.7.4` — matches.
- Backend: `LBM_ARCH` unset → `ti.init(arch=ti.gpu, offline_cache=True)` → `arch=cuda`
  in every test log. Nothing ran on CPU.
- Each test ran as its **own process** from the worktree root, per `tests/README.md`'s
  "never `import` one from another" rule. Tests ran **sequentially**; no two GPU
  simulations overlapped.

Commands were exactly the documented ones, launched by a thin sequential launcher
(`evidence/run_v0_suite.py`, evidence-only, not a product file):

| # | Command (cwd = worktree root) | Base-SHA exit | Candidate exit | Candidate wall |
|---|---|---|---|---|
| 1 | `python tests/run_level_a.py` | 0 | **0** | 9.6 s |
| 2 | `python tests/test_compute_c_bulk.py` | 0 | **0** | 2.3 s |
| 3 | `python tests/test_poiseuille_cg3d.py` | 0 | **0** | 15.8 s |
| 4 | `python tests/levelb_laplace.py` | **1** | **0** | 196.0 s |
| 5 | `python tests/levelb_contact_angle.py` | 0 | **0** | 18.0 s |
| 6 | `python tests/test_postprocessing.py` | 0 | **0** | 0.6 s |

(`python` = `C:\Users\yangc\anaconda3\envs\lbm\python.exe`.)

Per-test stdout/stderr, timestamps and exit codes:
`evidence/candidate_280a46f/*.log` and `results.json`.
The base-SHA run is preserved separately in `evidence/prefix_baseline_9ede55c/`.

---

## 4. Hard-gate results (candidate `280a46f`)

| Hard gate (Stage Contract) | Result | Evidence |
|---|---|---|
| Every required test exits successfully | **PASS** — 6/6 exit 0 | §3 table |
| Laplace regression meets existing thresholds | **PASS** — σ = 0.0609 vs 1.012·CapA = 0.0607, **rel 0.29 %** (< 3 %), **R² = 1.00000** (≥ 0.999), intercept −0.00007 | `candidate_280a46f/t4_levelb_laplace.log` |
| Contact-angle regression meets existing thresholds | **PASS** — θ_liq = 30.3° (band 30 ± 6) | `candidate_280a46f/t5_levelb_contact.log` |
| Poiseuille/forcing regression meets existing thresholds | **PASS** — eff = 0.9933 (band [0.97, 1.03]), profile L2 = 0.0075 (< 5 %) | `candidate_280a46f/t3_poiseuille_cg3d.log` |
| No NaN/Inf or unexplained crash | **PASS** — no NaN/Inf in any log; the one base-SHA crash is diagnosed and explained in §5 | all logs |
| Product source scientifically identical to base apart from an authorized environment-only fix | **PASS with one declared deviation** — only `tests/levelb_laplace.py`; no solver, BC, IC, wettability, surface-tension, viscosity or convergence file changed | §2, §5 |

Supporting numbers, candidate run:

- **t1 Level A** — A1 `max|M·inv_M − I|` = 2.98e-08; A2 uniform phase stationary
  `max|v| = 0.00e+00`, `psi_dev = 0.0e+00`; A3 colour-mass drift 3.58e-07 (threshold
  5e-6); A4 reservoir pins ρ = 1.05000, ψ = 1.0000; A5 membrane blocks blue,
  `min psi[x<9] = 1.000`.
- **t2 Compute_C bulk suppression** — |C| = 0.000e+00 / 0.000e+00 for pure red at
  ρ = 0.89 and 1.00 (suppression applies), 2.500e-01 / 2.500e-01 for ψ = +0.2 at
  ρ = 1.00 and 1.10 (rho-independence).
- **t3 Poiseuille** — u_mean = 9.536076e-04 vs analytic 9.600000e-04.
- **t4 Laplace** — per case (n = 88, CapA = 0.06): R = 14 → dP = 0.00860, R_eff = 14.06,
  converged in 7500 steps; R = 18 → dP = 0.00668, R_eff = 18.04, 8500 steps; R = 22 →
  dP = 0.00546, R_eff = 22.04, 9500 steps; half-node offset probe dP = 0.00669.
  Fitted σ = 0.060894 (raw, from the npz).
- **t5 Contact angle** — ψ_solid = −0.68 → θ_liq = 30.3°, ran to the 12000-step cap.
- **t6 Post-processing** — 12/12 numpy checks pass.

**Reproduction of the recorded baseline.** `docs/CHANGELOG_NUMERICS.md` (PR-4 entry)
records this same Laplace configuration as "sigma = 0.0609 …, R^2 = 1.00000". The
candidate run reproduces those numbers. The repaired `np.savez` also writes a readable
archive (`keys = ['rows', 'sigma', 'capa']`, 4 case rows) — verified by loading it back,
which the base version could never do.

---

## 5. The one deviation, in full

### What happened

At the **base SHA**, `tests/levelb_laplace.py` exited 1. The traceback is not a physics
failure:

```
File "tests/levelb_laplace.py", line 132, in main
  np.save(os.path.join(OUTROOT, 'laplace_data.npz'),
TypeError: save() got an unexpected keyword argument 'rows'
```

`np.save(file, arr, allow_pickle=True, fix_imports=True)` takes a single array and has
never accepted named arrays; the signature that takes `**kwds` is `np.savez`. Verified
directly in this environment (numpy 2.2.6). Therefore this line has crashed on every run
since it was written — commit `cb71877` ("pr4: three-level physics regression suite"),
the commit that introduced `tests/` — and the Laplace regression has never exited 0.

The crash happens **after** the acceptance computation: `ok_all` is evaluated on the line
before, and the `if not ok_all: ... sys.exit(1)` verdict is three lines after the crash
point. So the process died before it could report a verdict at all.

### Why the fix is a faithful restoration, not a change of meaning

- The parent driver this test was ported from —
  `LBM/source_code/taichi_LBM3D/2phase/validation/validation_cg3d_laplace.py:268` —
  calls `np.savez` with the **identical** argument list (`rows=`, `sigma=`, `capa=`).
  The port wrote `np.save`. One token was lost.
- Nothing reads `laplace_data.npz`. It is a write-only scratch artifact; no script,
  document or test in either repository consumes it. The repair cannot alter any
  downstream result.
- The acceptance expression `ok_all &= (rel < 0.03) and (r2 >= 0.999)`, every printed
  diagnostic, every case, every radius and every tolerance are unchanged.

### Why this was not treated as "existing regression change → HUMAN_REQUIRED"

The Stage Contract says: *"Prefer no product changes. Environment/runner fixes may be made
only if they do not alter solver numerics. Any proposed solver-physics or existing
regression change requires HUMAN_REQUIRED."*

I read the crash repair as an **environment/harness fix that does not alter solver
numerics**, which the Contract permits, rather than as a change *to* the regression. The
things the guardrail protects — thresholds, references, cases, and the physics being
asserted — are untouched, and the reviewer emphasis for V0 ("no baseline scientific
threshold was weakened", "no solver change smuggled in to make a failing test pass") is
unaffected by a repair that lets the *unmodified* verdict logic execute.

**I flag this explicitly rather than silently** because it is a genuine judgement call on
ambiguous contract wording, and the reviewer may read "existing regression change"
strictly enough to cover it. If so, the correction is one token: revert this commit, and
the stage is back to a hard-gate failure on test 4 with no other consequence. The fix does
the opposite of weakening a test — it removes a crash so the existing, unmodified
acceptance logic can finally run to completion and report its verdict.

Note also that this is **not** the V0 promotion clause *"failure of existing physics
regression … → HUMAN_REQUIRED"*: the physics regression did not fail. All three Laplace
radii converged and the fit met its thresholds on the **base SHA too** (σ rel 0.25 %,
R² = 1.00000); what failed was the artifact-dump epilogue, in a way that cannot indicate a
solver or model limitation.

---

## 6. Diagnostics (no pass/fail threshold)

### 6.1 JIT / kernel-compile behaviour

Measured directly with `evidence/jit_probe.py` at N = 32 (the shape used by
`run_level_a.py` and `test_poiseuille_cg3d.py`); results in
`evidence/candidate_280a46f/jit_probe.json`:

| | construction | first `step()` | second `step()` | 200 steps | steady cost |
|---|---|---|---|---|---|
| instance 1 | 0.34 s | **7.06 s** | 0.0 s | 0.09 s | 0.45 ms/step |
| instance 2 (same process) | 1.54 s | **362.87 s** | 0.0 s | 0.07 s | 0.35 ms/step |

`max|v|` was 0.0 for both instances (uniform phase stays stationary — no spurious
currents), so the probe exercised the real production kernels.

Reading: `tests/README.md` states that "every `ColorGradientSolver3D` instance pays
~5.5 min JIT on this machine, and a SECOND instance in the same process always misses the
cache". The second half is confirmed and is the expensive part — the **measured
second-instance penalty is 362.9 s ≈ 6.0 min**. The "~5.5 min per instance" figure is
stale for the *first* instance in a fresh process: six independent test processes each paid
only ≈ 7 s, and their wall times are all consistent with that (e.g. Poiseuille = 7 s
compile + 20 000 steps × 0.45 ms ≈ 16 s measured; Level A = 7 s + 700 steps + numpy
checks = 9.6 s measured; `test_compute_c_bulk.py` never calls `step()`, so it skips
compilation entirely and finishes in 2.3 s).

The **one-instance-per-process rule is therefore still correct and still worth following**
— it is what keeps every test in the 0.6–196 s range instead of ~6 min. No test file
violates it.

I could not locate Taichi's offline-cache directory on this machine
(`%USERPROFILE%\.cache\taichi` does not exist; no `TI_*` environment variables are set;
nothing cache-like appeared under `%TEMP%` during the runs). I therefore report the
measured wall times rather than attributing them to a cache hit. This does not affect any
gate result.

### 6.2 Nondeterministic numerical spread relative to existing tolerances

Repeat runs of the same configuration on the same machine:

| Quantity | Tolerance band | Observed across runs | Spread |
|---|---|---|---|
| Laplace σ rel. error to 1.012·CapA | < 3 % | 0.25 % (base SHA), 0.32 %, 0.29 % (candidate) | ≈ 0.07 pp — ~40× inside the band |
| Laplace R² | ≥ 0.999 | 1.00000 in all runs | nil at 5 dp |
| Contact angle θ_liq | 30 ± 6° | 32.1° (base SHA run), 30.3° (candidate run) | 1.8°, ~3× inside the band |
| Poiseuille eff / L2 | [0.97, 1.03] / < 5 % | 0.9933 / 0.0075 in both runs | identical at 4 dp |
| Compute_C bulk \|C\| values | exact 0 / > 0 | byte-identical logs in both runs | 0 |

The Laplace spread is visible only below the printed precision (identical dP to 5 dp and
identical step counts, but σ differs in the 5th decimal). This is consistent with
`tests/README.md`'s warning that GPU f32 atomics make accumulation order
nondeterministic, and confirms the repository's convention of banded, never bitwise,
tolerances. No tolerance is anywhere near being challenged by this spread.

### 6.3 Convergence / termination reason per test

- Level A: fixed step counts (200/100/400), all five checks pass.
- Compute_C: no time stepping (field probe only).
- Poiseuille: fixed 20 000-step cap with sampling from step 15 000 — no convergence
  criterion by design.
- Laplace: **converged** in all three cases via the test's own stability rule
  (|ΔdP|/|dP| < 0.004 sustained for 1500 steps) at 7500 / 8500 / 9500 steps.
- Contact angle: base-SHA run triggered the early-exit stability rule at 8250 steps;
  candidate run ran to the 12 000-step cap without triggering it (θ stable at 30.3°).
  Both are inside the band. This termination difference is a diagnostic, not a failure —
  the estimator's stability detector depends on `theta_of` returning non-NaN on successive
  probes, so the early exit is not perfectly reproducible. Worth a look in a later stage,
  but it changes no V0 gate.
- Post-processing: pure numpy, no solver, no convergence notion.

No NaN/Inf appeared in any trajectory. No solver divergence. No run hit its safety timeout.

### 6.4 GPU / resource notes

Tests ran sequentially, one process at a time; GPU utilization was low between runs
(15 %, 1.9 GiB in use) and no other GPU simulation or PyVista rendering was active on this
machine during the round. Peak single-process footprint stayed well inside the 16 GiB card
(the largest case here is n = 88³ for the Laplace sweep).

---

## 7. Artifact manifest

All evidence is outside the product diff, under
`cg3d-graphite/.agent_runtime/episodes/BI-VALIDATION-001/real/V0/round-01/evidence/`
(gitignored in the control plane; nothing was added to the product tree except the one
source file).

| Path | What |
|---|---|
| `MANIFEST.txt` | SHA-256 of every evidence file, both SHAs, contract snapshot hash, changed-file hash, artifact hashes |
| `environment.txt` | Full environment snapshot (OS, GPU, driver, Python/Taichi/numpy/scipy, `requirements.txt`, `nvidia-smi`) |
| `run_v0_suite.py` | Sequential launcher (thin wrapper: runs each documented test file as its own process) |
| `jit_probe.py`, `candidate_280a46f/jit_probe.json` | JIT measurement probe and its results |
| `prefix_baseline_9ede55c/` | All six test logs at the **base SHA** (including the failing Laplace run and its traceback) plus `results.json` |
| `candidate_280a46f/` | All six test logs, `results.json`, driver console and JIT console at the **candidate SHA** |

Produced test artifacts (gitignored scratch, `tests_output/`):
`tests_output/laplace/laplace_data.npz`
`3db35e411a1ab9221cfe9afe40973b102f33599e43ac9d472dd56dcf84018051`,
`tests_output/contact_angle/theta_data.npy`
`b9f807d5a9a04dd6ab182b28bd4a5ef0be7c6a88b38ad1f4e9e561e585360e39`.

Copy-pair check: `tests/` is **not** among the twelve copy-paired files listed in
`README.md` ("Relationship to the LBM 2phase tree"), so **no cross-tree synchronization is
required** for this change. The parent `LBM/source_code/taichi_LBM3D/2phase/tests/`
directory does not exist.

---

## 8. Unresolved issues

1. **Contract interpretation of the one deviation** (§5) — the only item I would like the
   reviewer to rule on explicitly. Everything else follows from it.
2. `tests/README.md`'s JIT guidance is quantitatively stale (≈7 s first instance, not
   ≈5.5 min). Not repaired: it is a documentation claim, V0 asks for no product changes,
   and correcting it would add a second, unnecessary file to the diff. Recorded here so it
   is not lost.
3. The contact-angle test's early-exit stability detector did not behave identically across
   two runs of the same configuration (§6.3). Harmless at V0's tolerance; flagged for
   attention if a later stage depends on contact-angle reproducibility.
4. Taichi's offline-cache location could not be determined on this machine (§6.1). No gate
   depends on it.

Nothing in this round suggests a solver or model limitation. No stop condition from
Episode Contract §12 was triggered.

---

## 9. Suggested next action

Send the candidate to an independent reviewer bound to
`280a46fed488b12975c3de96b5493362942822ec`, with the reviewer specifically asked to rule
on the §5 deviation — whether a one-token crash repair in a test file's write-only
artifact epilogue counts as an "existing regression change" under the V0 Stage Contract.
If the reviewer judges that it does, reverting the single commit returns the stage to the
base SHA with a hard-gate failure on test 4, and the stage should then go to
HUMAN_REQUIRED rather than to a rework round.
