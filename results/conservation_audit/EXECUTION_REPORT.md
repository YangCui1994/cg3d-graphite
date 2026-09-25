# EXECUTION REPORT — BI-CONSERVATION-AUDIT-001

> Executor report, not sole proof. Git identity, command logs, and CSV
> artifacts under `results/conservation_audit/` may be independently
> captured by the controller/reviewer.
>
> Revision 2 (attempt-2 candidate): incorporates the attempt-1 fresh
> review (CHANGES_REQUESTED, findings B1–B5, N1–N8). Text and derived
> artifacts only — no simulation was re-run and no raw evidence file
> (`*_mass_trace/identities/long_horizon/spatial_budget` CSVs, npz,
> prov.json, logs) was regenerated.

## Task

- **Task ID:** BI-CONSERVATION-AUDIT-001
- **Status:** COMPLETED (diagnostic audit; no solver change made)
- **Contract:** `.agent/episodes/bilateral-imbibition-v0.1/CONSERVATION_AUDIT_CONTRACT.md`
- **Base:** `5e679d8d99d338f9ab28565c636f021a0f9211b2` (V2 candidate)
- **Branch:** `agent-task/BI-CONSERVATION-AUDIT-001`
- **Driver:** `tests/conservation_audit.py` (audit-only; calls the
  production kernels directly in `step()` order; zero solver edits)

## Summary

The monotone closed-system mass drift observed in V1c/V2 is localized to
the **collision kernel**, with a **single f32 root cause** whose
observable is class B (the total-distribution and colour bookkeeping
channels diverge monotonically): the stored f32 inverse moment matrix
does not conserve the zeroth moment —

```
sum_s inv_M[s,0] = 1 + 1.4901161193847656e-08   (= 2^-26)
```

(executor-reproduced from the solver's own table by
`results/conservation_audit/inv_m_colsum_check.py`; first derived by the
attempt-1 reviewer's independent host-side f32 model). That number
predicts the measured per-step relative drift of the total channel
(predicted +1.49e-8 vs measured C3_gpu +1.556e-8 / C3_cpu +1.517e-8,
+4.4%/+1.8%) and is independent of the colour-gradient strength; the
interface's role is only to sustain non-equilibrium so the state never
reaches the kernel's bit-exact fixed point. The colour channel leaks
inside the same kernel at roughly half the rate, dominated by the
`feq`-pair sum (reviewer-attributed: +1.508e-8 at realistic splits;
recoloring pair arithmetic ~300x smaller, +8.3e-11; accumulation order
zero-mean with small bias +1.4e-9). Walls/bounce-back are exactly
innocent (C2). The drift is unbounded-linear in T with 100% per-step
sign bias where non-equilibrium persists, so the bounded-floor reading
(class A) is refuted. Executor proposal (reviewer to judge):
**PASS_DIAGNOSIS_READY_FOR_FIX**, mechanism observable class **B**
(B/D-composite single f32 root cause). No fix was implemented
(contract section 11).

## Method

The audited timestep calls the public kernels in the exact `step()` order
with f64 host-reduction measurements at checkpoints S0..S6:

```
S0 -> collision -> S1 -> F.fill(0) -> S2 -> streaming1 -> S3
   -> Boundary_condition -> S4 -> streaming3 -> S5
   -> Boundary_condition_psi -> S6          (no reservoirs; all bc=0)
```

Non-traced steps use the production `step()` entry itself. Host reads do
not mutate state; verified by identity J9 (S6(n) == S0(n+1) exactly
across the measurement boundary, every traced step, all runs).
Mass views: `Mff`, `MFF`, `Mr`, `Mb`, `Mracc`, `Mbacc`, `Mrho`; identities
J0..J9 and cross-representation residuals `d_fc`, `d_frho`, `d_crho` as
defined in the driver docstring and contract section 3/4.

Note on vacuous checks (attempt-1 review N7): with all `bc_*` flags at 0,
`Boundary_condition` and `Boundary_condition_psi` are compiled out, so
J4 (and S6 == S5) are vacuous no-op checks. The wall physics of C2/C3 is
actually exercised in `streaming1`'s half-way bounce-back and the colour
bounce-back inside `collision`, where J3 = 0 carries a mechanistic proof:
bounce-back is a permutation of distribution values, conserving their
sums exactly. No solver-claim below rests on J4.

## Isolation matrix (contract section 5)

Fitted drift slopes (relative, per step; f64 host sums, fluid nodes).
C0/C2 annotation per attempt-1 review B1: the **slope** is bit-zero
because the state reaches a bit-exact fixed point after ~2 steps, but
those two steps create a **one-time bounded offset** of +3.427267e-07
relative (+2.875 ULP per node) that then persists unchanged — precision
does create mass in C0/C2, once and bounded, and stops. `R2 = 1.000`
for C0/C2 is the driver's zero-variance fallback, not a fit quality.

| run | dims | steps | Mff (total) | Mc (colour) | late-window J1 | late-window J7 |
|---|---|---|---|---|---|---|
| C0_16_gpu | 16^3 | 5000 | slope 0* | slope 0* | 0 | 0 |
| C0_24_gpu | 24^3 | 5000 | slope 0* | slope 0* | 0 | 0 |
| C0_32_gpu | 32^3 | 5000 | slope 0* | slope 0* | 0 | 0 |
| C0_24_cpu | 24^3 | 5000 | slope 0* | slope 0* | 0 | 0 |
| C1_gpu | 64x24x24 | 10000 | +1.046e-8 (R2 .996)** | +2.03e-9 (R2 .911) | +1.42e-8, 95% pos | +7.0e-9, 80% pos |
| C1_cpu | 64x24x24 | 5000 | transient-only*** | transient-only*** | -1.0e-11, 50% pos*** | -5.4e-11, 55% pos*** |
| C2_gpu | 32x46x6 | 10000 | slope 0* | slope 0* | 0 | 0 |
| C2_cpu | 32x46x6 | 5000 | slope 0* | slope 0* | 0 | 0 |
| C3_gpu | 126x46x6 | 20000 | +1.556e-8 (R2 .9999) | +8.31e-9 (R2 .993) | +1.59e-8, 100% pos | +7.5e-9, 100% pos |
| C3_cpu | 126x46x6 | 10000 | +1.517e-8 (R2 .9999) | +1.14e-8 (R2 .998) | +1.58e-8, 100% pos | +9.9e-9, 100% pos |

\*  slope bit-zero after the 2-step transient; final state sits at
   +3.427267e-07 relative above the initial condition (bounded, frozen).
\** C1_gpu is not strictly linear (per-5k increments vary by ~x1.6;
   R2 0.996). Linearity statements in this report are scoped to C3.
\*** C1_cpu rises during IC relaxation, then plateaus with zero-mean
   jitter (relative wobble ~±1.4e-9, non-accumulating; +3.5206e-05 flat
   from ~3400 to 5000; late-window J1 frac_pos 0.50, mean -1.0e-11). On
   CPU the quiescent flat interface reaches a state whose per-step
   identities are unbiased; GPU continues to leak at the same state. A
   quiescent-state arithmetic-realization difference, not a different
   mechanism (see C3, where both backends leak identically under active
   meniscus dynamics).

Late-window J1/J7 detail: `late_window_identities.json` (all 10 runs;
committed generator `make_late_window.py`); full per-step series:
`<tag>/identities.csv`. C0/C2 CPU additionally carry a constant J6 =
-1.49e-8 device-vs-host representation offset of the frozen state
(non-accumulating; horizon slope 0).

## Answers to the four audit questions (contract section 1)

1. **First sub-step with measurable imbalance:** S0->S1, the collision
   kernel (identity J1 for the total channel, J7 for colour). J3
   (streaming1, incl. bounce-back permutation) and J5/J8 (streaming3
   copy / colour consume) are bit-exact zero in every run; J0/J2/J9
   exact; J4 is a vacuous no-op check (all `bc_*` flags 0 — see Method).
   The cumulative cross-representation residual `d_fc`/`d_crho` first
   exceeds 1e-6 relative during IC relaxation: step 200 (C1_gpu), 400
   (C3_gpu), 400 (C1_cpu), 600 (C3_cpu). `d_frho` never becomes material
   (max 2.21e-9 relative).
2. **Mechanism family:** a single f32 root cause with a class-B
   observable. Dominant total-channel term: the stored f32 `inv_M`
   zeroth column does not sum to 1 (`sum_s inv_M[s,0] = 1 + 1.4901e-8`;
   `inv_m_colsum_check.py`), so every collision inflates the
   reconstructed zeroth moment by that factor wherever the state keeps
   evolving; the attempt-1 reviewer's host-side f32 model shows the bias
   is essentially independent of the colour-gradient strength (+1.368e-8
   at cc = 0 -> +1.398e-8 at cc = 0.20) — the interface's role is to
   sustain non-equilibrium and keep the state off the kernel's bit-exact
   fixed point (why C0/C2 freeze and stop leaking, C1/C3 do not). Colour
   channel, same kernel: `feq`-pair sum dominant (+1.508e-8 at realistic
   splits), recoloring pair arithmetic `(a+c)+(b-c)-(a+b)` ~300x smaller
   (+8.3e-11), f32 accumulation order zero-mean with small bias
   (+1.4e-9 rel) — reviewer-attributed decomposition, cited as such.
   Not walls (C2 exactly clean), not macro reconstruction (J6 small;
   Mrho slope == Mff slope), not random accumulation (linear-in-T with
   100% sign bias in C3 on both backends).
3. **Solver correction before V3?** The measured production-relevant
   rates (total <=1.56e-8/step, colour <=1.14e-8/step; extrapolating
   C3_gpu to 60k: ~9.3e-4) are inside the owner's calibrated V2 envelope
   (r_M <= 2e-8/step; total-normalised <=1e-3/60k). V3 may proceed under
   that envelope **without** a fix; the fix is a recommended separate
   task (below). Contract-owner decision, not the executor's.
4. **Bounded-floor scaling law (class A):** refuted — but not by the C0
   floor: in C0 precision does create mass, once (+3.427267e-07,
   +2.875 ULP/node in the first two steps), bounded and frozen
   thereafter. The refutation rests on C1/C3: where non-equilibrium
   persists, the drift is linear and unbounded in T (C3_gpu:
   7.46e-5 / 1.52e-4 / 2.31e-4 / 3.10e-4 at 5k/10k/15k/20k, increments
   7.76 / 7.90 / 7.84e-5 per 5k, R2 = 0.9999) with a 100% per-step
   positive sign bias on **both** backends (C3_cpu 1.517e-8/step) — a
   deterministic per-collision inflation factor, not a bounded
   accumulation.

## Spatial budget (C3_gpu, final vs ref1000 vs t0)

Regions mechanical from final psi (wall rows carved out first; |psi|<=0.9
interface; gas/liquid bulk beyond):

| region | nodes | dMc (ref1000) | dMf (ref1000) | dMrho (ref1000) | dMf per node |
|---|---|---|---|---|---|
| gas_bulk | 17880 | -33.79 | +3.70 | +3.70 | +2.07e-4 |
| interface | 960 | +2.91 | +0.33 | +0.33 | +3.43e-4 |
| liq_bulk | 8520 | +35.33 | +4.10 | +4.10 | +4.81e-4 |
| wall_rows | 1440 | +0.16 | +0.35 | +0.35 | +2.44e-4 |

Net: dMc = +4.61 (== fitted colour drift 1.705e-4 x 28800), dMf = +8.48
(== 3.096e-4 x 28800; region sums reconcile with the horizon deltas to
<=1.1e-9). The budget **cannot localize creation** (end-of-step
residence only; contract section 6): 92% of the leaked total-channel
mass resides in the bulk regions, and the per-node rates are comparable
across all four regions — consistent with the node-wise arithmetic
residue of the mechanism above, and inconsistent with interface-localized
creation. The large colour exchange gas->liquid (-30 Mr out of the
pocket) is meniscus dynamics, not leak. Full table with rho_r/rho_b
columns and both references: `C3_gpu/spatial_budget.csv`.

## Backend comparison (contract section 7)

`backend_comparison.csv`. C3: CPU 1.517e-8 vs GPU 1.556e-8 per step
(2.5% apart, same sign, same R2 > 0.999, same 100% J1 sign bias) ->
algorithmic f32 bookkeeping, not atomic ordering (contract section 7
interpretation rule). C1 quiescent-state CPU/GPU difference documented
above and in the CSVs.

## Scaling (contract section 8)

- Domain (C0: 16/24/32, GPU): no accumulating drift at any size; the
  one-time +3.427267e-07 offset is size-independent (per-node constant).
- Horizon (C3_gpu 5k/10k/15k/20k): linear in T for the total channel
  (slope 1.556e-8/step, R2 0.9999; increments 7.76/7.90/7.84e-5 per
  5k). Colour channel value 5.40e-5 at 5k with increments 4.30 / 3.74 /
  3.61e-5 per 5k (decelerating), so the channel divergence `d_fc` grows
  super-linearly relative to the colour channel alone (+1.39e-4 at 20k).
- Interface-area normalization: not claimed — C1/C2 interface-band and
  wall-band node counts are not committed artifacts (only C3 has a
  spatial budget), so any per-band-node normalization for C1/C2 would
  not be reproducible from the evidence (attempt-1 review B5).

## Consistency with V2 production evidence

V2 production (326x46x6, 60k steps, GPU) measured population-channel
+9.21e-4 (1.53e-8/step) and colour +5.47e-4 (9.12e-9/step). The C3
analogue reproduces 1.556e-8/step (total, +1.7% vs V2) and 8.31e-9/step
(colour, -8.7% vs V2) — the audit geometry captures the production
mechanism.

## Classification and proposal (contract sections 10-11)

Observable class **B — colour/total-population bookkeeping mismatch**
(the two representations diverge at a specific sub-step, repeatably, not
a transient storage artifact), best stated as a **B/D-composite with a
single f32 root cause** (both channels leak independently inside
`collision` at different rates: J1 total 1.556e-8/step, J7 colour
8.31e-9/step in C3_gpu; no discrete imbalance — the attempt-1 reviewer's
fully-f64 roundtrip residual is 2.7e-17).

No-fix rule honoured: no solver source touched; no diagnostic added to
production code.

Solver-fix proposal for a separate task (NOT implemented; scope per
attempt-1 review B3):

- kernel / path: `collision()` in `lbm_solver_cg3d.py` — (a) the
  `inv_M @ m_temp` reconstruction (total channel), (b) the `g_r/g_b`
  transport into `rhor/rhob` (colour channel);
- failed identity: per-node zeroth moment of the reconstructed `f`
  should equal the pre-collision `sum_s F[s]` (J1); in exact arithmetic
  it holds (M row 0 integer ones; S[0]=0) — it fails only through the
  stored f32 `inv_M` (zeroth column sums to 1 + 2^-26);
- effective minimal scopes (reviewer-verified): (i) carry the moment
  roundtrip in **f64 — matrix and accumulator both** (residual 2.7e-17),
  or (ii) an **exact per-node zeroth-moment correction** of the
  reconstructed `f`. Explicitly insufficient: an f64 accumulator with
  the f32 matrix (bias +1.496e-8 unchanged, frac_pos 1.00). Colour fix
  must target the **feq pair sum** (dominant +1.508e-8) — a fix scoped
  to recoloring or atomics would miss the actual term;
- regressions that would need rerun if fixed: P-line unit validations
  (Laplace sigma=1.012*CapA, contact angle theta(-0.68), Poiseuille
  eff~0.99), V1c a26/a40 differential gates, V2 symmetry/topology
  sentinels, and re-issue of every mass-drift number in V1c/V2 evidence
  (all expected to shift at the f32-floor level only).

## Validation commands

- Batch (exact reproduction): `bash results/conservation_audit/run_batch.sh`
  — per-run python console logs in `logs/<tag>.log`; shell-level exit
  codes persisted in `logs/batch_exit_codes.log` (all exit=0);
  per-run argv/env in `<tag>/prov.json`.
- Aggregate: `python tests/conservation_audit.py analyze`.
- Derived artifacts (revision): `python results/conservation_audit/make_late_window.py`,
  `LBM_ARCH=cpu python results/conservation_audit/inv_m_colsum_check.py`,
  `python results/conservation_audit/figures/ca_make_figs.py`.
- All 10 runs exit 0; no NaN/Inf; umax guardrail not applicable (no
  force; max 2.2e-2 meniscus currents in C3).

## Artifacts

`results/conservation_audit/`: `summary.json`, `backend_comparison.csv`,
`scaling_results.csv`, `late_window_identities.json` (+ committed
generator `make_late_window.py`), `inv_m_colsum_check.py/.json`,
`figures/ca_make_figs.py` + 4 SVGs, per-run dirs
(`substep_mass_trace.csv`, `identities.csv`, `long_horizon_mass.csv`,
`case_report.json`, `prov.json`, `logs/`; C3 additionally
`spatial_budget.csv`, `symmetry_check.json`, `fields_t0.npz`,
`fields_ref.npz`), `run_batch.sh`, `logs/` (incl.
`batch_exit_codes.log`). Manifest: `MANIFEST.json`; provenance:
`PROVENANCE.md`.
