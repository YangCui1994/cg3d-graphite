stage: colour-closure / candidate: 6c30260
attempt: 1
candidate_full_sha: 6c30260dfe0c8b61ea9609e6bffa5c487312cf06
base: e256b4857a6e51510b75358994d7c5bcc742781e
branch: agent-task/BI-COLOUR-CLOSURE-001
execution_report: results/colour_closure/EXECUTION_REPORT.md

# REVIEW — BI-COLOUR-CLOSURE-001 (attempt 1)

## Review mode and coverage

`FRESH_SESSION`, independent reviewer. The executor transcript was not read.
No GPU work, no Taichi run, no simulation re-run; every check below is
host-side on the committed machine-readable evidence (git object comparison,
raw per-node `.npz` snapshots, committed CSV/JSON, log tails, independent
OLS re-fits and my own re-implementation of the node-class masks and of the
colour scatter gather). Nothing was modified except this file and
`REVIEW_SESSION.json`.

Inspected: `AGENTS.md`; the external review
`.agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/EXTERNAL_SCIENTIFIC_REVIEW_CHANGES_REQUESTED.md`;
the contracts `COLOUR_CLOSURE_CONTRACT.md` and
`COLOUR_CLOSURE_REVIEWER_CONTRACT.md`; `REVIEW_REQUEST.md`; the product
worktree `cg3d-episode-worktrees/BI-COLOUR-CLOSURE-001` (clean at `6c30260`);
the full diff `e256b485..6c30260` including the extracted T3/T2/recolour
solver blocks; `results/colour_closure/**` (253 manifest entries, all
re-hashed); the frozen `results/conservation_fix/**`; the frozen regression
baselines `results/conservation_fix/levelc_v1c_fix/`,
`levelc_v2_fix/`; the unchanged test drivers
`tests/levelc_v1c.py`, `tests/levelc_v2_bilateral.py`,
`tests/run_level_a.py`, `tests/levelb_laplace.py`,
`tests/levelb_contact_angle.py`, `tests/test_poiseuille_cg3d.py`,
`tests/test_postprocessing.py`, `tests/test_compute_c_bulk.py`; and the
control-worktree documents `docs/research/bilateral_imbibition/`.

Not inspected: the executor transcript (excluded by the review request); any
re-run of the GPU runs (not authorized for this review); the executor session
log that holds the batch `exit=$?` lines (not committed — see Finding N2).

## 1. Binding, candidate integrity and scope — verified

| Check | Result | Evidence |
|---|---|---|
| Worktree clean at the named candidate | PASS | `git status --porcelain` empty; `HEAD` = `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`; branch `agent-task/BI-COLOUR-CLOSURE-001` |
| Descends from `e256b485…` | PASS | `git merge-base --is-ancestor e256b485 HEAD` true; chain `388892e -> 71d2a4b -> 1854a58 -> 246a463 -> 6c30260` (5 commits) |
| Diff is colour-only + evidence | PASS | changed files vs base: `lbm_solver_cg3d.py`, `tests/colour_closure.py` (new), `tests/conservation_fix.py` (4 lines: `acc` passthrough, default `'A0'`), `.gitignore` (+3 npz un-ignore), `results/colour_closure/**`. No `docs/`, no BC, no physical-parameter, no threshold/gate file touched |
| T3 total path frozen | PASS | extracted blocks byte-compared base vs candidate: T3/T4 inverse transform identical, T2 correction identical, Latva-Kokko recolouring identical; total fields `rho`, `f`, `F` untouched; `rhor`/`rhob` (the `acc_fix` dtype switch) are colour-only accumulators |
| Frozen prior evidence intact | PASS | `git diff e256b485..HEAD -- results/conservation_fix/` is empty (byte-identical) |
| No BC / IC / physical-parameter change | PASS | only the four files above; constructor BC/parameter arguments unchanged; `streaming3`'s `psi = (rho_r-rho_b)/(rho_r+rho_b)` expression unchanged |
| Gates not weakened | PASS | regression drivers unmodified from base; V1c gate `|a-1|<=0.10`, V2 `MASS_TOL=5e-4` / `g5: e_x<=max(2.0, 0.02d)`, A2 gate `max|v|<1e-6` all read from the unchanged files |
| Final-commit delta | PASS | `6c30260` vs `246a463` changes the solver by comments plus the two default values only (`colour_fix 'C1'->'C1X'`, `acc_fix 'A0'->'A2'`, 37+/52− lines, no arithmetic line); the F3/F4 batch sets `LBM_COLOUR_FIX=C1X LBM_ACC_FIX=A2` explicitly, so the regression runs exercise the final arithmetic |

## 2. Contract A — blocker reproduced independently (PASS)

Recomputed by me from the frozen `results/conservation_fix` series (not from
the executor's `reproduce_report.json`):

| Quantity | External review / contract | My recomputation |
|---|---|---|
| C1 `R_r` mean / frac_pos | +3.88e-9 / 0.758 | +3.8836e-9 / 0.7578 |
| C1 `R_b` mean / frac_pos | +3.10e-9 / 0.761 | +3.0965e-9 / 0.7609 |
| C3 `R_r` / `R_b` mean | ~1e-10 / ~2e-10 | +9.7602e-11 / +1.9554e-10 |
| C3 60k colour slope / R2 | −6.43e-10 / 0.9827 | −6.42529e-10 / 0.9827, 1 pos / 299 neg |
| C3 60k segments (1–20/20–40/40–60k) | −9.56 / −5.77 / −5.22e-10 | −9.5625 / −5.7711 / −5.2211e-10 (R2 0.9940/0.9992/0.9995, all frac_pos ≤0.01) |
| C3 60k total slope | +1.1944e-11 (R2 0.625) | +1.1944e-11 (R2 0.6246) |
| Pre-fix T0+C0 60k colour (≥10x basis) | — | +6.7617e-9 (R2 0.9960, 300/300 positive) |

All 13 checks confirmed → `A_reproduce` PASS.

## 3. Residual localization (contract B) — verified, one prose imprecision

I recomputed `R_r`, `R_b`, `Req_r`, `Rc1_r`, `dacc_r`, `net_r` per node class
from the committed per-node snapshots with my own mask code
(`wall_adj` = any solid among the 19 periodic streaming targets;
`chi = min(rho_r,rho_b)/(rho_r+rho_b)`) and my own replication of the
production colour scatter (stream + bounce-to-source, `mem_r` asserted zero).
The global budget identity closes at 1.7e-15 (f64) and the committed
`class_stats.csv` aggregates are reproduced.

**Which class causes the base one-sided residual — the contract's explicit
question.** For the periodic-C1 geometry under `T3 + C1(scoped)/A0`:

- `cc == 0` node-steps (82.4 %): `R_r` mean **+4.6603e-9**, frac_pos **0.785**,
  and *identical to `Req_r`* because `Rc1_r == 0.0` exactly there (the
  `cc>0` scope never fires). This is the B2 residual.
- `cc > 0` (17.6 %): `R_r` −7.86e-12, frac_pos 0.542 — closed and unbiased by
  scoped-C1.
- The biased `cc == 0` set is entirely `cczero/pure/nonwall` at every chi
  threshold (1e-7/1e-6/1e-5); for C1 the `mixed` class is a strict subset of
  `cc>0`, so a chi-threshold scope extension cannot reach the biased nodes.
  The operative discriminator really is non-frozenness, not mixture.
- Committed x-profile: the positive-mean `cc==0` band carries ongoing net mass
  motion (`|net_r|` up to 9e-7 per step, `Req_r = R_r ~ +1e-8` per node) over
  x≈34–61 on the red side and x≈0–1 across the periodic seam, whereas the deep
  bulk (x=2–29) sits at `Req_r ~ 1e-19`, `net_r ~ 1e-14` (effectively frozen).
- C3 analogue: the biased class is `cczero/pure/wall`
  (+5.0526e-9 r / +1.1649e-8 b, frac_pos 0.364/0.617); `cc>0` unbiased.

**Candidate `T3 + C1X + A2`:** every class closes to f64 epsilon with
non-one-sided sign fractions — C1 `ALL` −5.90e-17 (frac_pos 0.334), `cc==0`
−5.48e-17 (0.356), `cc>0` −7.84e-17 (0.234), per-node `|ΔR_r|` max 1.33e-15
(base: 4.66e-8); C3 `cczero/pure/wall` −6.71e-17 / −1.49e-16 (0.512/0.384).
`Req_r` is unchanged (+4.9e-9 C1, +5.6e-9 C3) and is now closed exactly
(`Rc1_r = −Req_r` to ~1e-16). The previously biased classes are gone, not
merely reduced.

## 4. Periodic-C1 accumulation (contract C) — verifies the base accumulates

My independent fits of the committed `mass_series.csv` (they reproduce every
committed `accum_report.json` value exactly):

| run | Mc slope/step | R2 | frac_pos(inc>0) |
|---|---:|---:|---:|
| base `C1/A0` 20k | +8.84463e-10 | 0.9269 | 0.778 |
| base `C1/A0` 240k | +1.04800e-9 | 0.9986 | 0.861 |
| base 240k quarters (4×60k) | +9.64e-10 / +1.10e-9 / +1.19e-9 / +1.10e-9 | 0.987–0.995 | 0.83–0.89 |
| candidate `C1X/A2` 20k | −1.07785e-10 | 0.9834 | 0.030 |
| candidate 60k | −6.40049e-11 | 0.9539 | 0.027 |
| candidate 240k | +1.80456e-11 | 0.2797 | 0.549 |
| candidate 240k quarters | +1.93e-10 / −4.94e-12 / +1.25e-11 / −5.14e-13 | 0.66/0.20/0.96/0.07 | — |

The base is a **linear, one-sided accumulation** (its fitted slope is
horizon-invariant and `|slope|×window` grows 2.1e-5 → 2.5e-4 from 20k to
240k). The candidate improves it **13.8x at 60k and 58.1x at 240k**, with
`|1.80e-11| <= 2e-9/step`, the last 60k quarter statistically flat
(mean increment −2.95e-11 ± 1.15e-9, t = −0.03, frac_pos 0.500), and
`|slope|×window` shrinking with horizon (1.09e-5 at 20k → 4.3e-6 at 240k) —
i.e. a decaying/wandering residual, not a linear leak. The required C1 gate
is met. It is **not** called a bounded floor (see §6).

## 5. Long-horizon fits (contract E) — C3 required windows

| series | slope/step | R2 | frac_pos |
|---|---:|---:|---:|
| base rerun `C1/A0` 60k colour | −6.55307e-10 | 0.9872 | 0.000 |
| — segments 1–20/20–40/40–60k | −9.563e-10 / −5.594e-10 / −6.054e-10 | 0.994/1.000/1.000 | 0.00 |
| candidate 60k colour | **+8.08797e-12** | 0.5826 | 0.538 |
| — segments | +3.132e-11 / −4.722e-12 / +1.320e-12 | 0.908/0.827/0.201 | 0.69/0.39/0.54 |
| candidate 120k colour | +2.69288e-12 | 0.4146 | 0.559 |
| candidate 60k total | −2.47635e-11 | 0.8136 | 0.492 |
| candidate 120k total | +1.01410e-11 | 0.3219 | 0.482 |

The base blocker is reproduced by the same-code rerun to 2 % (run-to-run GPU
atomic-ordering band). Against it the candidate is 79x/81x better and 836x
better than pre-fix `T0+C0`; `|8.09e-12| <= 2e-9` (247x margin);
`|r_total| <= 2e-9`; the late 20k window is flat (slope +1.32e-12, R2 0.201,
frac_pos 0.54) and the segments alternate sign while decaying. The literal
"no persistent one-sided late trend" gate is satisfied.

Residual honesty: over the full 60k window the candidate increments still
carry a small positive mean (t = +4.4 over 299 checkpoint increments) that
decays with horizon; the C1 series is *itself* still one-sided at the 60k
horizon (9 pos / 291 neg) and only reaches its flat regime at 240k. I
therefore do **not** describe any residual as bounded (see §7).

## 6. Candidate mechanism (contract D/E) — verified

- **Momentum:** with the solver's actual f32 weight table,
  `sum_s w_s e_s = 0.0` exactly in f64 **and** f32, and
  `sum_s w_s e_a e_b = (1/3) delta_ab`. The weighted closure therefore injects
  no momentum by construction (both arms), and its second-moment effect is a
  `(1/3)·dr` per-component term — at the f64 floor for A2 (`dr ~ 1e-17`) and
  `~3e-9` for the f32 arms.
- **Representability / where the residual lives:** under A2 the closure is
  evaluated in f64 against the exact sum, so each node's outgoing sum equals
  the stored f32 `rho_r`; the only surviving rounding is the single
  `rho_r = f32(rhor)` store. The committed budget confirms the mechanism
  end-to-end (`bg_C3_T3C1X_A2` at t=20k: `sumR_r = −2.27e-12`,
  `sumdacc_r = −4.41e-15`, versus base `+6.99e-6 / −1.98e-5` with the
  identity closing at 7.7e-12). The rho-store rounding sum is a wandering
  term (per-step sd ~1e-6 raw ≈ 3.5e-11 relative) whose long-horizon mean is
  the ~1e-11/step residual measured in §5 — not a class bias.
- **f32-storage survival (rejected arm):** the rest-population `C1R` arm's
  computed correction (−3.79e-9) does **not** survive storage — the stored
  `R_r` stays at leak level (+1.58e-9). The rejection is evidence-based and
  correct; the selected arm is not a rest-population correction.
- **Frozen-state preservation while correcting (contract D):** `a2_candidates.json`
  and its log give `max|v| = 0.0` and `psi_dev = 0.0` **exactly** for all 7
  combos including `T3+C1X/A2`; production Level A (N=32) confirms
  `max|v| = 0.00e+00`, `psi_dev = 0.0e+00`, and colour-mass conservation
  relative drift 0.00e+00 versus 3.58e-7 for `T0`. Caveat (non-blocking): the
  `max|v|` leg is structurally insensitive to colour-channel changes (`v`
  derives from the untouched total `f` field); the load-bearing legs are
  `psi_dev = 0` and the f64 closure/budget evidence.
- **No material pressure/second-moment change:** V2 statistics are
  essentially identical to the accepted run (`rho_min` 0.885077 vs 0.885064,
  `E_psi` max 9.02e-5 vs 8.95e-5, `umax` 2.5568e-2 vs 2.5543e-2), and the
  unchanged-gate regression chain passes (§7).

## 7. Regression chain (contract F) — unchanged gates, all green

| Suite | Result | Values (candidate / accepted) |
|---|---|---|
| F2 Level A (A1–A5) | PASS | ALL PASS; A2 `max|v| = 0.00e+00`, `psi_dev = 0.0e+00` |
| F2 Laplace | PASS | sigma 0.0610 (0.42 %) vs T0 0.0609 (0.31 %) |
| F2 contact angle | PASS | 31.2° vs T0 32.1° (gate 30 ± 6) |
| F2 Poiseuille | PASS | eff 1.0010 vs T0 0.9933 |
| F2 Compute_C / postproc | PASS | PASS / ALL PASS |
| F3 V1c | PASS | a26 = 1.0618, a40 = 1.0741 (gate ≤0.10); dynamic `all_hard` x4; static plateau 0.7904/0.7516/0.8068/0.7715 (accepted 0.7902/0.7511/0.8067/0.7795) |
| F4 V2 primary 60k | PASS | g1/g2/g3/g5–g9 True (g4/g10 null by design); `max_eps_r = 5.8705e-6`, `max_eps_b = 5.1584e-7` (accepted 7.4868e-5 / 1.9758e-4 → 12.8x / 383x better; gate 5e-4); mirror 7.40e-4 (gate `max(2.0, 0.02d)`); 1 cluster; no fragmentation; symmetry `all_pass`; INTERACTION NOT_REACHED |
| T3 total channel | PASS | C3 60k −2.48e-11, 120k +1.01e-11; C1 240k −1.5981e-10 — all ≤ 2e-9 |
| Performance | PASS | C3 2833→2853, C1 2838→2809 steps/s (net-zero) |

Non-gated disclosures (accepted, not fix-attributable): Laplace/contact deltas
inside the documented run-to-run spread; the V1c estimator-sensitivity pattern
(some mean-estimator variants fail) is identical to the accepted baseline; the
non-gated `L0/h(h26)` diagnostic shifts 3.02→2.64; the C1 240k *total* slope
(−1.60e-10, R2 0.82) has the same component in the base (−1.580e-10, R2 0.62)
and is inside the gate.

## 8. Evidence, manifest, provenance

- `MANIFEST.json`: 253 entries; I recomputed every SHA256 — **253/253 match**,
  0 missing, 0 mismatch. Only `MANIFEST.json` and `summary.json` are outside
  the manifest (by `make_manifest.py` design). Every log ends with its
  driver's terminal marker.
- The two pre-gather-fix artifacts (`dx_C3_T3C1s`, `bg_C3_T3C1s` with
  `identity_err 1.77e+2`, `sumdacc +1.4e+2`) were superseded; the committed
  artifacts carry the corrected numbers (`bg_C3_T3C1s` identity 7.7e-12),
  consistent with the disclosed deviation record.

### Findings — blocking

None.

### Findings — non-blocking

1. **N1 (provenance flag, disclosed).** The F3/F4 evidence was produced at
   `run_head 246a463` with `worktree_dirty: true` (untracked evidence);
   `6c30260` touches the solver by comments + the two default values only, and
   `run_regression_batch.sh` passes `C1X/A2` explicitly, so the arithmetic
   attribution to the final candidate holds. Future packages should record the
   dirty file list.
2. **N2 (exit codes).** `prov` blocks carry `exit_code: null` /
   `finished_at: null` — the same pattern as the previously accepted package
   (pre-existing driver writer behaviour), and the batch `exit=$?` lines live
   in the uncommitted executor stdout. Exit codes are therefore *not*
   independently verifiable; the terminal log markers and artifacts are
   consistent with clean completion.
3. **N3.** `summary.json` (the headline gate summary) is excluded from the
   hash manifest by design, so it is the one load-bearing document without
   hash coverage.
4. **N4.** Diagnosis prose "x ~ 34-40" is narrower than the committed
   `x_profile.csv`, where the positive-mean `cc==0` band spans x≈34–61 (plus
   the periodic seam); the class identification and all machine-readable
   numbers are correct and the narrower phrasing does not affect any
   conclusion.
5. **N5.** "far bulk bit-frozen" is qualitative: those nodes sit at
   `Req_r ~ 1e-19` but `net_r ~ 1e-14` per step (not literally zero). The
   committed tables carry the real numbers; the accumulating class is
   unaffected.
6. **N6.** The `max|v|` leg of the A2 isolation test cannot detect a
   colour-channel momentum defect (`v` comes from the total `f` field). The
   claim is carried by the exact `sum_s w_s e_s = 0` algebra, `psi_dev = 0`,
   and the budget evidence instead.

## 9. Modeling / scientific review

- No physical model, BC, IC, convergence rule, contact-angle or parameter
  change; the total channel is byte-frozen. The only physics-visible change is
  the colour bookkeeping precision (psi/rho_r at the f32-ulp scale).
- The colour channel is a bookkeeping/transport channel here; momentum lives
  in the untouched total populations, so the correction cannot inject momentum
  (verified exactly), and the second-moment effect is at the f64 floor for A2.
- The claimed improvement direction is consistent with an independent
  mechanism (removing the f32 equilibrium-construction leak and the f32
  scatter-accumulate bias that previously cancelled), and the residual is
  attributed, not asserted.
- No previous accepted result becomes stale: the accepted T3 total channel,
  V0/V1c/V2 conclusions and the frozen prior evidence all remain valid; the
  earlier colour drifts remain reproducible via `LBM_COLOUR_FIX=C1 LBM_ACC_FIX=A0`.
- `docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`
  is unmodified, which is correct per contract G ("update after fresh
  review"); the external review's §7 citation errata already stand in the
  control worktree (commit `1687574`, docs tree clean).

## 10. Missing evidence

- Batch `exit=$?` lines are not committed (N2).
- A hash-covered copy of `summary.json` (N3).
- Nothing else that the frozen contract requires. The colour residual is
  disclosed with the horizon/scaling evidence the contract asked for, but it
  is **not** a demonstrated bounded floor, so the "no-sign-bias attributable
  to the correction" clause of the external review's B1 is not literally
  satisfied by this package; the executor explicitly declines to call it
  bounded and hands the wording decision to the owner. This review does not
  close that clause either.

## Decision rationale

All frozen hard gates are met with large margins and are independently
reproduced here: C3 60k colour +8.09e-12/step (247x inside the 2e-9 gate;
79x better than the accepted colour baseline, 836x better than pre-fix T0);
C3 total −2.48e-11/step; periodic C1 13.8x (60k) / 58.1x (240k) better and
inside 2e-9, with the last quarter flat; C3 local closure improved by 6–7
orders at every node class including the previously biased `cc==0`
(interface-side) and `cczero/pure/wall` classes; momentum preserved exactly
by construction; no material pressure/second-moment change; the whole
unchanged-gate V0/V1c/V2 chain green; manifest 253/253 hashes verified.

The remaining colour residual is small, sign-symmetric in the late windows
and horizon-decaying (its fitted slope falls as the window grows, while the
base's stays constant), and its source is localized to the single f32
`rho_r` store rather than to any node class. I do not call it a bounded floor,
and the frozen no-sign-bias clause requires an explicit owner decision
(re-scope wording or acceptance of a calibrated residual) before any V3
consideration. That decision is handed forward; this PASS authorizes neither
V3 nor promotion, and the residual is recorded here rather than silently
closed.

Next action: forward to external scientific review with the explicit
statement that the colour residual is calibrated but not proven bounded, so
the frozen no-sign-bias clause needs the owner's explicit acceptance or
amendment (and the deferred `ALGORITHM_IMPLEMENTATION_EVOLUTION.md` update)
before V3 can be reconsidered.

Decision: PASS
