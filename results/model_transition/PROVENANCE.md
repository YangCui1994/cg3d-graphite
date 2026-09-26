# PROVENANCE — BI-DEEPSEEK-TRANSITION-001

## Binding

- **Task:** BI-DEEPSEEK-TRANSITION-001 (one real, low-risk calibration task for
  DeepSeek as the next executor model, producing a revised-V3 readiness
  artifact)
- **Contract:** `.agent/episodes/bilateral-imbibition-v0.1/DEEPSEEK_TRANSITION_CONTRACT.md`
- **Entry point:** `.agent/episodes/bilateral-imbibition-v0.1/START_DEEPSEEK_TRANSITION.md`
- **Product base:** `6c30260dfe0c8b61ea9609e6bffa5c487312cf06` (accepted
  BI-COLOUR-CLOSURE-001 candidate; externally reviewed PASS)
- **Product branch:** `agent-task/BI-DEEPSEEK-TRANSITION-001`
- **Final candidate:** recorded in `REVIEW_REQUEST.md`
- **Solver state:** unmodified; byte-identical to the base commit

## What this task is

This is explicitly **not** a V3 execution task. It is Part A an independent
recomputation of already-committed evidence, and Part B a readiness/design
document. No simulation was started, no GPU work was performed, and no
production code was edited.

## Environment

- Hardware: Windows 11 host, RTX 5080 (not used by this task)
- Python for both scripts: `C:/Users/yangc/anaconda3/envs/lbm/python.exe`
  (Python 3.10.21, numpy 2.2.6) — the same interpreter recorded as the producer
  of the accepted evidence
- No Taichi compilation, no CUDA context created, no JIT cache touched
- Both scripts read only files committed on the base commit

## Commands run (exact)

```bash
# worktree creation (from the main repository checkout)
git worktree add -b agent-task/BI-DEEPSEEK-TRANSITION-001 \
  ../cg3d-episode-worktrees/BI-DEEPSEEK-TRANSITION-001 \
  6c30260dfe0c8b61ea9609e6bffa5c487312cf06

# Part A
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/recompute_metrics.py

# z-seam probe (read-only)
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/periodic_seam_probe.py
```

## Inputs (all committed on the base commit, read-only)

| input | used for |
|---|---|
| `results/colour_closure/ac_C1_T3C1X_A2_240k/mass_series.csv` + `accum_report.json` | A1 periodic C1 colour drift, `M0` |
| `results/colour_closure/ac_C3_T3C1X_A2_120k/mass_series.csv` + `accum_report.json` | A2 C3 colour drift, `M0` |
| `results/colour_closure/levelc_v2_fix/v2_primary/front_series.csv` | A3 mirror error, `E_psi` cross-check |
| `results/colour_closure/levelc_v2_fix/v2_primary/mass_stability_series.csv` | A3 blue relative mass drift |
| `results/colour_closure/levelc_v2_fix/v2_primary/gas_series.csv` | A3 cluster history, interaction status |
| `results/colour_closure/levelc_v2_fix/v2_primary/report.json`, `symmetry_check.json`, `topology_t0.json` | A3 constants (`m_b0`, `nx`, t=0 topology) |
| `results/colour_closure/levelc_v2_fix/v2_primary/fields_{initial,mid,final}.npz` | seam probe only |

Sources not used: `SUMMARY.md` files and any review prose. Per the contract,
no headline value was an input to a calculation. Committed producer values are
consulted only in the `cross_check` blocks, which record the committed value,
the recomputed value and an explicit match verdict.

## Definitions fixed by the producers (quoted in the script docstring)

- colour series `Mc_norm(t) = (Mr(t) + Mb(t)) / M0 - 1`, `M0` from the run's own
  `accum_report.json`;
- fit = OLS against the step index; `slope_per_step`, `r2 = 1 - SS_res/SS_tot`,
  `frac_pos` = fraction of positive first differences;
- window selection `lo <= step <= hi` (inclusive; the convention already used by
  `tests/colour_closure.py`), with window boundaries aligned on multiples of the
  window span from zero;
- mirror error `e_x = |x_left - ((nx-1) - x_right)|`, `nx` from
  `symmetry_check.json`;
- blue relative drift `eps_b = |m_b / m_b0 - 1|`;
- `E_psi = mean over fluid nodes of |psi(x) - psi(nx-1-x)|` (the V2 driver's own
  definition, taken from its docstring).

## Cross-check tolerances and why they are not tighter

`recompute_metrics.json -> A1/A2.cross_check.tolerance` declares
`slope_rel = 1e-7`, `r2_abs = 1e-7`, `frac_pos_abs = 1e-12`. The mass series is
written as 13-significant-digit text, which quantises each sample to about
`1e-13` relative; a slope fitted over 600 such samples inherits roughly `1e-8`
relative error. The observed residual differences are `3.9e-9` (A1) and
`7.3e-9` (A2), i.e. text round-off. A tighter tolerance would report a
mismatch that is not a numerical disagreement.

The front series is written at 8 significant digits, so the independently
derived mirror error and the committed `e_x` column differ by up to `1.0e-5` lu;
both values are reported and the difference is disclosed rather than resolved.

## Conventions disclosed rather than hidden

- The contract asks for "four 60k" and "four 30k" window slopes. These are
  convention-sensitive at the last significant digit. The JSON records both the
  inclusive-boundary windows used as primary and a disjoint-boundary variant,
  plus the difference between them. The primary convention is the one that
  reproduces the values published in the external scientific review
  (`+1.93e-10 / -5.04e-12 / +1.24e-11 / -4.66e-13` for periodic C1 and
  `+2.23e-11 / -4.11e-12 / +3.70e-12 / +3.85e-12` for C3).
- The material content of the window table is the sign pattern, not the last
  digit: a large first-window transient followed by sign-mixed, near-zero
  windows.

## Incidents and deviations

1. The first version of the window helper anchored window boundaries on the
   first recorded sample rather than on zero, producing boundaries such as
   400-60300 instead of 400-60000. It was corrected before the artifact was
   committed; the corrected version reproduces the published window slopes
   exactly. Recorded here because an earlier draft number set existed on disk
   during the session.
2. The first mirror-error cross-check used a 1e-9 relative tolerance, which
   flagged a mismatch caused by CSV text precision rather than by a numerical
   disagreement. The tolerance was replaced by the declared text-precision
   tolerance above, with its basis recorded in the JSON. No value changed.
3. Two files beyond the contract's required output list were added
   (`periodic_seam_probe.py`, `periodic_seam_probe.json`). They perform
   read-only analysis of committed artifacts to answer the item-6 question
   factually; no simulation and no production change.
4. The z-seam probe's fluid mask is its own construction and does not reproduce
   the V2 driver's `E_psi` denominator exactly; the field-based and
   series-based `E_psi` values therefore differ by about 0.9%. The probe JSON
   records both and labels the series value as the committed one. This is a
   mask-convention difference, not a numerical discrepancy.

## Evidence paths

```text
results/model_transition/
  EXECUTION_REPORT.md                       this task's executor report
  PROVENANCE.md                             this file
  recompute_metrics.py                      Part A generator
  recomputed_metrics.json                   Part A output
  periodic_seam_probe.py                    read-only z-seam probe
  periodic_seam_probe.json                  probe output
  V3_READINESS_AND_PERIODIC_BC_AUDIT.md     Part B design document
.agent_runtime/BI-DEEPSEEK-TRANSITION-001/
  REVIEW_REQUEST.md                         reviewer binding (git-ignored scratch)
```

## Synchronization note (repository constraints)

The repository contains copy-paired files with the separate
`LBM/source_code/taichi_LBM3D/2phase/` working tree. This task changed no
solver, boundary or driver file in either tree, so **no synchronization is
required** and none was performed.

## Reproduction

From the worktree root, on the branch at the candidate commit:

```bash
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/recompute_metrics.py
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/periodic_seam_probe.py
```

Both scripts resolve the repository root from their own location, so they can
be run from any working directory.
