# REVIEW_REQUEST — BI-DEEPSEEK-TRANSITION-001

Executor: DeepSeek (session `9631892d-…`), 2026-09-26.
Reviewer contract:
`.agent/episodes/bilateral-imbibition-v0.1/DEEPSEEK_TRANSITION_REVIEWER_CONTRACT.md`.
Executor report: `results/model_transition/EXECUTION_REPORT.md`.
Provenance: `results/model_transition/PROVENANCE.md`.

## 1. Binding

| item | value |
|---|---|
| product branch | `agent-task/BI-DEEPSEEK-TRANSITION-001` |
| **base (exact)** | `6c30260dfe0c8b61ea9609e6bffa5c487312cf06` |
| **candidate (exact)** | `c12e2fc4f0c756dec9c93fc71d508e95d283485b` |
| commit chain | `6c30260` (base) -> `235bb86` -> `c12e2fc` (candidate, HEAD) |
| base is an ancestor of candidate | yes (`git merge-base --is-ancestor`) |
| remote | `origin/agent-task/BI-DEEPSEEK-TRANSITION-001` = candidate (pushed, verified by `git ls-remote`) |
| worktree path | `D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-episode-worktrees\BI-DEEPSEEK-TRANSITION-001` |

Two commits, both additive documentation/scripts:

| commit | content |
|---|---|
| `235bb86` | Part A recomputation script + JSON, Part B audit, seam probe, execution report, provenance |
| `c12e2fc` | one addition to the audit document: an explicit caveat that the closed-system balance explains the pocket *density* jump but not the subsequent slow expansion of the `psi > 0` region. Documentation only; no number changed. |

## 2. Changed files (complete)

```text
A  results/model_transition/EXECUTION_REPORT.md
A  results/model_transition/PROVENANCE.md
A  results/model_transition/V3_READINESS_AND_PERIODIC_BC_AUDIT.md
A  results/model_transition/periodic_seam_probe.json
A  results/model_transition/periodic_seam_probe.py
A  results/model_transition/recompute_metrics.py
A  results/model_transition/recomputed_metrics.json
```

`git diff --name-status 6c30260 HEAD` returns exactly these seven additions.
Nothing else changed. In particular:

- `lbm_solver_cg3d.py` — **byte-identical** to base;
- `tests/**` — **byte-identical** to base;
- no physics, boundary, initial condition, convergence rule or gate changed.

## 3. Reviewer binding checks — expected results

| check | expected | how to verify |
|---|---|---|
| exact base ancestry | PASS | `git merge-base 6c30260… HEAD` == `6c30260…`; `git log --oneline 6c30260..HEAD` shows exactly the two commits above |
| exact candidate SHA | `c12e2fc4f0c756dec9c93fc71d508e95d283485b` | `git rev-parse HEAD`, and `git ls-remote origin agent-task/BI-DEEPSEEK-TRANSITION-001` |
| clean worktree | tracked content clean | see the disclosure in §6 |
| no solver modification | PASS | `git diff 6c30260 HEAD -- lbm_solver_cg3d.py` is empty |
| no V3 execution | PASS | no V3 driver, no V3 run directory, no V3 result exists in the diff |
| no graphite / separator / gap / PCS work | PASS | no such file in the diff |

## 4. Commands the executor ran (exact)

```bash
# Part A — independent recomputation
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/recompute_metrics.py
# exit 0

# §6.2 of the audit — read-only z-seam probe over committed field archives
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/periodic_seam_probe.py
# exit 0
```

Both scripts resolve the repository root from their own location and were also
verified to run from a different working directory. Neither starts a
simulation: no Taichi compilation, no CUDA context, no GPU work.

## 5. Recomputed metrics (Part A)

Source: `results/model_transition/recomputed_metrics.json`. All values below
were computed from committed raw CSV/JSON; committed headline values appear only
afterwards in a `cross_check` block.

### A1 — periodic C1, 240k steps (`ac_C1_T3C1X_A2_240k/mass_series.csv`, `M0 = 36864.000549316406`)

| quantity | value |
|---|---|
| full 240k colour slope | `+1.8046e-11 / step` |
| full 240k R² | `0.2797` |
| 60k window slopes | `+1.93e-10`, `-5.04e-12`, `+1.24e-11`, `-4.66e-13` |
| increment-sign fraction, full | `0.5492` (329 of 599 first differences positive) |
| increment-sign fraction per window | `0.523`, `0.487`, `0.687`, `0.500` |
| cross-check vs committed `drift_fits.Mc` | reproduces (`slope_rel_diff 3.9e-9`) |

### A2 — C3, 120k steps (`ac_C3_T3C1X_A2_120k/mass_series.csv`, `M0 = 28800.000429153442`)

| quantity | value |
|---|---|
| full 120k colour slope | `+2.6929e-12 / step` |
| full 120k R² | `0.4146` |
| 30k window slopes | `+2.23e-11`, `-4.11e-12`, `+3.70e-12`, `+3.85e-12` |
| increment-sign fraction, full | `0.5585` |
| increment-sign fraction per window | `0.676`, `0.467`, `0.560`, `0.533` |
| cross-check vs committed `drift_fits.Mc` | reproduces (`slope_rel_diff 7.3e-9`) |

### A3 — V2 bilateral (`levelc_v2_fix/v2_primary/`)

| quantity | value |
|---|---|
| max blue relative mass drift `eps_b` | `5.1584e-07` (at t = 60000; = the final sample) |
| max front mirror error `e_x` | `7.4005e-04 lu` from the committed column; `7.4500e-04 lu` independently derived from `x_left`/`x_right` |
| RMS `e_x` | `3.97e-04 lu` |
| trapped-cluster count history | `{1}` at every one of the 60 samples; t=0 topology: 1 cluster, largest 38400 |
| fragmentation | none (cluster count never exceeds 1) |
| interaction status | `NOT_REACHED`; `G_bulk` constant at 146 in all 60 samples; `G_bulk` min 146 > 0 |

### Independent cross-check of the whole Part A

`cross_check` blocks record: committed value, recomputed value, relative /
absolute difference, the declared tolerance (`slope_rel = 1e-7`,
`r2_abs = 1e-7`, `frac_pos_abs = 1e-12`) and its basis (13-significant-digit CSV
text quantisation, not a physical tolerance). Verdict: **all three reproduce**.

## 6. Disclosures the reviewer should weigh

1. **`.agent_runtime/` is not git-ignored in this repository**, although
   `.agent/README.md` says it is (`git check-ignore .agent_runtime` exits 1;
   the repo `.gitignore` has no such entry). The contract requires
   `REVIEW_REQUEST.md` at this path, so it is created here and appears as
   untracked scratch in `git status`. **Tracked content is clean**; the only
   untracked entry is this contract-mandated scratch directory. The same
   situation exists in the sibling worktree `cg3d-bilateral`.
2. **Two artifacts beyond the contract's required output list** were added:
   `periodic_seam_probe.py` and `periodic_seam_probe.json`. They perform
   read-only analysis of already-committed artifacts to answer the item-6
   question factually, and they keep the probe numbers out of prose (project
   practice: report numbers are script-generated, never hand-copied).
3. **Window convention.** "Four 60k" / "four 30k" window slopes are
   convention-sensitive in the last significant digit. The JSON declares the
   primary convention (zero-aligned windows, `lo <= step <= hi`) and also
   records a disjoint-boundary variant plus the difference. The primary
   convention is the one that reproduces the values published in
   `EXTERNAL_SCIENTIFIC_REVIEW_PASS.md`; the reviewer may use any convention
   and should compare the sign pattern, which is the material content.
4. **Mirror error is reported twice** (committed column and independent
   derivation) because the two differ by `1.0e-5 lu`, the text quantum of the
   8-significant-digit position columns. Disclosed, not silently resolved.
5. **The probe's `E_psi`** uses its own fluid mask, so the field-based value
   differs from the committed series by about 0.9%. The probe JSON records both
   and labels the committed series value as authoritative.
6. **Push transport incident (non-scientific).** The first push of the second
   commit died with `send-pack: unexpected disconnect while reading sideband
   packet` / `fatal: the remote end hung up unexpectedly`, and the remote was
   left at the first commit. `git ls-remote` was used to confirm the remote ref
   rather than trusting the local remote-tracking ref or the push summary, and
   the push was retried successfully (`235bb86..c12e2fc`). No history was
   rewritten and no force-push was used; the branch is append-only.
7. **Revision of the audit after the first commit.** The caveat added in
   `c12e2fc` was not in `235bb86`. It is a documentation addition motivated by
   the committed evidence itself (the pocket region expands while its density
   holds), and no previously reported number changed. The executor reviewed its
   own draft for this gap before handing the package over; this is a disclosure,
   not a claim that the draft was independently reviewed.

## 7. Scientific-state comprehension checklist

Confirm `results/model_transition/V3_READINESS_AND_PERIODIC_BC_AUDIT.md`
correctly states:

| required statement | where |
|---|---|
| `T3 + C1X + A2` is frozen | §1.1 |
| V1c / V2 / conservation are accepted | §1.2, §1.3 |
| the central gas is trapped from t = 0 | §2.2 |
| the old isolation-time / pre-isolation V3 framing is obsolete | §2.1–§2.4 |
| revised V3 is planning only | header, §3.1, §9 |
| periodic-BC tests are proposed, not executed | §6.3, §7, §9 |
| graphite / separator / gap / PCS remain unauthorized | §1.4, §9 |

## 8. V3 design-quality checklist

Confirm the document distinguishes, and does not blur:

| required distinction | where |
|---|---|
| hard invariants | §5.1 (frozen H1–H7), §5.2 (proposed N1–N4, flagged as requiring owner approval) |
| scientific diagnostics | §5.3 |
| buffer-size sensitivity | §3, §4 |
| periodic-BC sanity checks | §6, §7 (P0–P3) |
| stop conditions | §9 (what was not done, what remains unauthorized) |

Two design claims to test adversarially:

1. **The old 5% gate is unusable.** §3.3 claims the closed-system balance
   predicts a `1.333×` pocket-compression ratio between 1 B and 2 B, so an
   equal-value 5% gate would reject correct physics by 6.7×. Check the
   arithmetic: `d rho_gas = 3 Pc V_liquid/(V_gas+V_liquid)` with
   `Pc = 2.280325e-3` (V1c same-slit static, h=40), `G0 = 160`, `h = 40`,
   `nz = 6`, unit density, `c_s² = 1/3`.
2. **The balance matches the measurement.** §3.2 claims the same expression
   predicts `+3.421e-3` against the observed committed `rho_gas_mean` rise
   `+3.444e-3` at t = 1000 (0.7%). Independently check the observed value from
   `gas_series.csv` and judge whether a 0.7% agreement at a single geometry and
   a single time justifies the document's wording ("below one percent",
   labelled as leading-order consistency, not as a validated dynamics model).

Also judge whether §6.3's recommendation is correctly scoped: a periodic-BC
suite is recommended **not** to gate V3, with P1 shape checks and P3 deferred to
the first geometry that wraps solid or interface across the z seam. The
supporting facts are in §6.2 (z-spread saturating at `5.07e-04`, persistent at
`r = 0.996`) and `periodic_seam_probe.json`.

## 9. What the reviewer must not do

- Do not modify the product candidate.
- Do not read or request the executor transcript.
- Do not execute V3, the buffer sweep, or the P0–P3 periodic tests.

## 10. Reviewer outputs

```text
.agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW.md
.agent_runtime/BI-DEEPSEEK-TRANSITION-001/REVIEW_SESSION.json
```

Decision exactly one of: `PASS` / `CHANGES_REQUESTED` / `HUMAN_REQUIRED`.
`PASS` means DeepSeek is sufficiently calibrated for a staged revised-V3 task;
it does not start V3. Return the package to the external reviewer afterwards.
