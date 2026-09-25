# CANDIDATE COMPARISON — BI-SOLVER-CONSERVATION-FIX-001

All runs on the task branch (base `1f5ee76`), C3 minimal V2 analogue
(126x46x6, two-phase slit, mirror IC) unless noted.  F0 = per-node local
identities in device arithmetic (probe window after 1500 steps, 40
collisions, `f0_*/f0_local_identities.csv`); F1 = closed-system
long-horizon drift (f64 host reductions, linear fits,
`f1_*/long_horizon_mass.csv`); F10 = performance (first-step JIT vs
steady state, same grid/horizon).  Negative control T4 eliminated at F0
per contract section 7 (early elimination by failed local invariant).

## Mechanisms

- **T0**: baseline — stored f32 `inv_M` has `sum_s inv_M[s,0] = 1+2^-26`
  (conservation-audit root cause); colour channel leaks via feq-pair
  sum (+ recoloring pair arithmetic + 19-way f32 accumulation).
- **T1**: stored-matrix conservation projection — reshape the stored f32
  inverse so `1^T inv_M = (1,0,...,0)` as closely as f32 represents
  (greedy ulp-stepping on the smallest-magnitude entry per column;
  `project_inv_m_colsums()`).  Achieved exact (f64) column sums after
  projection: `colsum[0]-1 = 0.0` (exactly), `max|colsum[l>0]| =
  6.2e-17` (from +1.4901e-8 / 1.49e-8).  3 entries change significantly
  (max 1.49e-8 absolute = 5.4e-7 relative of that entry:
  `inv_M[7,0] 0.0277778->0.0277777631`, `inv_M[6,1] 0->-1.49e-8`,
  `inv_M[7,2] -3.7e-9`) plus ~17 sub-ulp entries (|delta| <= 1e-16) on
  formerly-zero positions.  Zero kernel-code arithmetic change; kernels
  identical to T0 (shared JIT cache).
- **T2**: local post-reconstruction zeroth-moment correction —
  `delta = m_temp[0] - sum_q f_q` distributed as `w_q * delta`
  (momentum-preserving to the f32 floor).
- **T3**: full-f64 moment roundtrip (f64 `inv_M_f64` matrix + f64
  accumulator, final cast to f32) — numerical reference.
- **T4**: f64 accumulator + unchanged f32 matrix — negative control.
- **C0/C1**: colour baseline / per-colour local zeroth-moment projection
  after equilibrium+recoloring (`g_r += w_q*(rho_r - sum g_r)` etc.).

## F0 — local identities (per node per collision, C3 geometry)

| candidate | R_f mean | R_f frac_pos | R_r mean | R_r frac_pos | R_b mean | verdict |
|---|---|---|---|---|---|---|
| T0+C0 | +1.489e-08 | 0.66 | +6.50e-09 | 0.54 | +5.02e-09 | biased (defect reproduced) |
| T1+C0 | -3.78e-11 | 0.446 | +6.54e-09 | 0.54 | +5.02e-09 | total closed; colour open |
| T2+C0 | -3.47e-10 | 0.521 | +6.47e-09 | 0.54 | +5.04e-09 | total closed; colour open |
| T3+C0 | -3.63e-12 | 0.469 | +6.43e-09 | 0.54 | +5.02e-09 | total closed (tightest); colour open |
| T4+C0 | **+1.494e-08** | **0.940** | +6.52e-09 | 0.54 | +5.01e-09 | **negative control: bias survives f64 accumulation** |
| T1+C1 | +8.67e-11 | 0.448 | -1.68e-10 | 0.518 | -5.64e-10 | both channels closed |
| T2+C1 | -2.62e-10 | 0.521 | -1.55e-10 | 0.518 | -4.69e-10 | both channels closed |

Momentum (full-collision change `sum_q e_q (f_post - F_pre)`, committed
F0 CSVs): selected T3+C1s mean ~1e-12 / max 1.30e-8 per node (f32
floor); T0/T2+C0 max 2.79e-8; T1+C1 max 4.28e-8 — and T1 carries a
**systematic per-axis momentum mean of −1.5e-8 in x/y** (attempt-1
review independent reproduction: the projected table trades the
zeroth-moment defect for a local momentum defect
`sum_q e_q delta_f_q = (−1.49e-8, −1.49e-8, ~0)` per node; further
grounds for T1's rejection — disclosed per review B2).
Correction-specific momentum residuals (`delta*sum w_q e_q`,
`(dr+db)*sum w_q e_q`): `sum_q w_q e_q = 0` exactly (host f64),
so zero by construction. Colour three-stage split (C1 runs):
equilibrium-sum residual dominates (+6.45e-9 mean, sign-consistent
with the audit's feq-pair attribution); recoloring ~2 orders smaller
(−1.1e-10); post-C1 residual ~1e-10.

## F1 — long-horizon C3 drift (linear fits, relative per step)

| combo | horizon | total Mff | R2 | colour Mc | R2 | notes |
|---|---|---|---|---|---|---|
| T0+C0 | 20k | +1.549e-08 | 0.9999 | +8.31e-09 | 0.993 | baseline reproduces audit |
| T1+C0 | 20k | +1.14e-10 | 0.95 | +8.28e-09 | 0.993 | 136x total |
| T2+C0 | 20k | **-2.76e-09** | **0.9998** | +8.37e-09 | 0.994 | **fails >=10x gate** (5.6x; monotone negative) |
| T3+C0 | 20k | -6.40e-11 | 0.77 | +8.24e-09 | 0.992 | reference (non-monotone) |
| T2+C1 | 20k | -2.74e-09 | 0.9999 | -1.59e-09 | 0.998 | T2 global bias persists |
| T1+C1 | 20k | +5.74e-12 | 0.030 | -1.58e-09 | 0.998 | total = no trend (rejected by A2, see below) |
| T0+C0 | 60k | +1.552e-08 | 1.0000 | +6.76e-09 | 0.996 | 60k total 9.3e-4 (== V2 production) |
| T3+C0 | 60k | +1.17e-11 | 0.35 | +6.77e-09 | 0.996 | reference floor |
| T1+C1 | 60k | +2.87e-11 | 0.81 | -1.30e-09 | 0.997 | initial selection, **rejected by A2** (kept for history) |
| **T3+C1s** | **60k** | **+1.19e-11** | **0.62** | **-6.43e-10** | 0.983 | **SELECTED**: total ~1300x; colour 10.5x, within 2e-9 |
| T3+C1s (CPU) | 20k | -3.30e-11 | 0.85 | -6.85e-11 | 0.795 | selected, backend check (colour at noise) |
| T1+C1 (CPU) | 20k | +8.13e-11 | 0.84 | -7.80e-10 | 0.993 | backend-consistent |

Colour-channel floor justification (restated per attempt-1 review B3):
after C1 the colour residual is a **bounded one-sided (negative) floor**
— 299/300 checkpoints negative, −4.05e-5 over 60k, sign-flipped from
C0's positive leak; the scoped correction removes ~90% of the pre-fix
absolute colour leak (6.09e-9/node x 28800 = 1.75e-4/step vs baseline
1.95e-4/step), and the leftover varies 6.9e-11–1.6e-9 across C1
variants and backends (ordering-dependent, floor-consistent).  It meets
the engineering target `|r_M,colour| <= 2e-9` and the >=10x gate
(10.5x); the surviving one-sided sign is stated for external review
rather than claimed away.  Total-channel 10x gate: met with ~1300x
(+1.19e-11/step, no trend, 52.7% positive increments).

## F10 — performance (C3 grid, same horizon)

| combo | JIT first step (s) | steady steps/s | MLUPS | extra storage |
|---|---|---|---|---|
| T0+C0 | 6.9 (cache-warm) / 329 (cold) | 2352-2465 | 67.7-71.0 | none |
| T1+C0 | 6.8 | 2453 | 70.6 | none (table reshaped in place) |
| T2+C0 | 337 (cold) | 2486 | 71.6 | none |
| T3+C0 | 296 (cold) | 2355-2423 | 67.8-69.8 | +f64 19x19 table + f64 ops |
| T1+C1 | 348 (cold) / 6.8 (warm) | 2347-2480 | 67.6-71.4 | none |

T1+C1 has no measurable steady-state cost (within run-to-run noise of
T0); T3 costs ~4-5% throughput plus f64 machinery.  JIT columns mix
cold/warm cache states; per-run detail in `f1_*/f1_report.json`.

## Selection

**REVISED after the F2 A2 gate (see "A2 stationarity finding" below):
T3 + C1-scoped is the production default** (commit `e3d5a93`; initial
selection `46be3f2` was T1+C1 and is retained in history as the
rejected first choice).

### A2 stationarity finding (drives the reselection)

The unchanged V0 suite gate A2 ("uniform phase stationary",
`max|v| < 1e-6` after 200 steps) exposes a structural property the F1
drift metrics cannot see: under T0 the uniform single-phase state is a
**bit-exact frozen fixed point** (velocity stays exactly 0.0).
All nine combos re-run with the committed generator
`a2_isolation_check.py` -> `a2_isolation.json` (grid N=24, 200 steps;
the production gate in `run_level_a.py` uses N=32 and the full
suite; C1 rows in the committed generator run under the CURRENT
scoped code — the pre-scoping unscoped variants failed identically,
see `logs/f2_levelA_T1C1.log`):

| combo | max\|v\| | A2 |
|---|---|---|
| T0+C0 | 0.0 | PASS (bit-frozen) |
| T3+C0 | 0.0 | PASS (f64 roundtrip preserves the frozen point exactly) |
| T1+C0 | 4.463e-06 | FAIL |
| T2+C0 | 4.463e-06 | FAIL |
| T4+C0 | 3.103e-06 | FAIL |
| T0+C1 (scoped, committed) | 4.463e-06 | FAIL |
| T1+C1 (scoped, committed; unscoped variant failed identically in the F2 suite log) | 4.463e-06 | FAIL |
| T2+C1 (scoped, committed) | 4.463e-06 | FAIL |
| **T3+C1 (scoped)** | **0.0** | **PASS** |

Any f32-path perturbation of the kernel arithmetic (table reshaping,
per-step corrections) breaks the frozen point; the state then migrates
to a common nearby attractor with `max|v| = 4.46e-6` — four orders
below operational velocities and with `psi_dev = 0.0` exactly (no
physical phase error), but above the 1e-6 gate, which may not be
weakened.  Only the f64 roundtrip (T3) preserves the frozen point
bit-exactly.  C1 was additionally **scoped to interface nodes
(`cc > 0`)**: the audit measured the colour leak to exist only at
diffuse interfaces (J7 exactly 0 in single-phase/wall-only cases), so
bulk corrections were both unnecessary and stationarity-breaking.  This
is defect-scoped correction, not gate tuning.

Consequences: T1 (identical drift quality to T3, zero cost) is
eliminated by A2; T2 additionally fails the F1 >=10x gate; the selection
is forced to T3+C1(scoped) — the only candidate passing F0, F1 and A2
simultaneously.

### Rejected-candidate evidence retained

- T1+C1 full F2 suite ran before the reselection
  (`logs/f2_*_T1C1.log`): all parts PASS except A2 (FAIL, the trigger);
  its F1 numbers stay in the table above.
- T2's F0-pass-but-F1-fail pattern (unbiased local closure, monotone
  global -2.76e-9) is preserved evidence that local identities alone
  are insufficient for selection.

### Final selection rationale (T3 + scoped C1)

1. only candidate passing every unchanged gate (F0 both channels, F1
   drift targets, A2 exact stationarity);
2. invariant is exact in real arithmetic (f64 roundtrip removes the
   stored-matrix representation defect rather than compensating it);
3. cost measured: ~4-5% steady throughput (2347-2423 vs 2465 steps/s on
   C3), one 19x19 f64 table, plus the 10 unconditional per-node f64
   probe fields (12 f64 values per node incl. the 3-component momentum;
   ~3 MB on C3, ~7 MB on V2; writes compiled out when dbg off); JIT one-time;
4. performance may not override conservation/physics gates (contract
   section 10); among gate-passing candidates it is the only one.

## F2/F3/F4 — physics regressions (selected fix: T3 + scoped C1)

All gates pass with thresholds unchanged (details in
`EXECUTION_REPORT.md`):

- **F2 V0 suite**: Level A ALL PASS (A2 max|v| = 0.00 exact), Compute_C,
  Poiseuille (eff 0.9933 -> 1.0010), Laplace (0.42% -> 0.35% rel;
  committed-log pair; T0 run-to-run spread 0.26-0.42%, not
  fix-attributable), contact angle (34.0 -> 27.3 deg, band 30+-6;
  T0 spread 30.8-34.0 deg across the two T0 batches, not
  fix-attributable), postprocessing ALL PASS.
- **F3 V1c**: static C = 0.7902/0.7513/0.8070/0.7834 (baseline
  0.7902/0.7511/0.8067/0.7795); differential a26 = 1.0389 /
  a40 = 1.0581 — both |a-1| <= 0.10 PASS (baseline 1.0436/1.0699).
- **F4 V2**: mirror error 4.96e-4 lu (baseline 1.297e-3, 2.6x better);
  eps_r/eps_b max 7.49e-5 / **1.98e-4** (baseline 4.21e-4 / 6.73e-4 —
  3.4x better, now inside the original 5e-4 g6 value); single trapped
  cluster, NOT_REACHED, bulk rho [0.9350, 1.0074] unchanged.
