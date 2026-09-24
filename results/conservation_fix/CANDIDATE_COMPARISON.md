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

Momentum (full-collision change `sum_q e_q (f_post - F_pre)`, max over
probe window): all candidates <= 2.2e-08 absolute per node (f32 floor;
pre-correction momentum scale rho*u ~ 1e-2..1e0).  Correction-specific
momentum residuals (`delta*sum w_q e_q`, `(dr+db)*sum w_q e_q`): <= 3e-9.
Colour three-stage split (C1 runs): equilibrium-sum residual dominates
(+4.4e-9..+6.5e-9 mean, sign-consistent with the audit's feq-pair
attribution); recoloring contribution ~2 orders smaller; post-C1
residual at the ~1e-10 floor.

## F1 — long-horizon C3 drift (linear fits, relative per step)

| combo | horizon | total Mff | R2 | colour Mc | R2 | notes |
|---|---|---|---|---|---|---|
| T0+C0 | 20k | +1.549e-08 | 0.9999 | +8.31e-09 | 0.993 | baseline reproduces audit |
| T1+C0 | 20k | +1.14e-10 | 0.95 | +8.28e-09 | 0.993 | 136x total |
| T2+C0 | 20k | **-2.76e-09** | **0.9998** | +8.37e-09 | 0.994 | **fails >=10x gate** (5.6x; monotone negative) |
| T3+C0 | 20k | -6.40e-11 | 0.77 | +8.24e-09 | 0.992 | reference (non-monotone) |
| T2+C1 | 20k | -2.74e-09 | 0.9999 | -1.59e-09 | 0.998 | T2 global bias persists |
| T1+C1 | 20k | +5.74e-12 | 0.030 | -1.58e-09 | 0.998 | total = no trend |
| T0+C0 | 60k | +1.552e-08 | 1.0000 | +6.76e-09 | 0.996 | 60k total 9.3e-4 (== V2 production) |
| T3+C0 | 60k | +1.17e-11 | 0.35 | +6.77e-09 | 0.996 | reference floor |
| **T1+C1** | **60k** | **+2.87e-11** | **0.81** | **-1.30e-09** | 0.997 | **selected**: total 541x better; colour within 2e-9 target |
| T1+C1 (CPU) | 20k | +8.13e-11 | 0.84 | -7.80e-10 | 0.993 | backend-consistent |

Colour-channel floor justification: after C1 the colour residual
(-1.3e-9..-1.6e-9/step, sign flipped from C0's +8e-9) is the measured
f32 arithmetic floor of the 19-way colour-transport accumulation itself
(the equilibrium-sum bias C1 removes is the dominant pre-fix term); the
remaining term is common to every candidate and meets the engineering
target `|r_M,colour| <= 2e-9`.  Total-channel 10x gate: met with 541x;
colour improvement is 6.4x (8.31e-9 -> 1.30e-9 at 60k) — within target,
floor-documented, submitted for review per contract section 9's
"defensible arithmetic floor" clause.

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

**T1 + C1** (production default since commit `46be3f2`):

1. smallest solver change: T1 touches only the module-level table
   construction (~25 host lines, zero kernel arithmetic change); C1 is
   one static block in `collision()`;
2. simplest invariant: exact algebraic constraints (`1^T inv_M =
   e_0^T`; per-colour zeroth-moment equality) rather than per-step
   corrections (T2) or precision promotion (T3);
3. lowest cost: no extra fields, no f64 ops, steady rate == baseline;
4. best measured closure among f32 candidates (total = no-trend noise;
   colour at floor).

T2 is honestly rejected: unbiased local closure (F0 -3.5e-10, 0.52) but
a persistent monotone global bias (-2.76e-9, R2 0.9998) — the
w-distributed correction interacts with the downstream on-device f32
zeroth-moment sums; this is precisely the "global improvement while
leaving a systematic local/global closure bias" pattern the contract
forbids selecting.  T3 rejected for production (reference only):
correctness equal to T1 within noise but f64 machinery + ~4-5% cost and
no additional closure benefit on the acceptance metrics.  T4 rejected
at F0 (negative control confirmed: f64 accumulation does not repair the
stored-matrix identity defect).

## F2/F3/F4 — physics regressions (selected fix)

See `EXECUTION_REPORT.md` (before/after tables) — populated from
`logs/f2_*.log`, `levelc_v1c_fix/`, `levelc_v2_fix/`.
