# EXECUTION REPORT — BI-CONSERVATION-AUDIT-001

> Executor report, not sole proof. Git identity, command logs, and CSV
> artifacts under `results/conservation_audit/` may be independently
> captured by the controller/reviewer.

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
the **collision kernel at diffuse colour interfaces**, in a form the
contract classifies as **B — colour/total-population bookkeeping
mismatch**. Both mass representations leak independently inside the same
kernel — the total distribution through the `M -> relax -> inv_M` moment
roundtrip (identity J1), the colour populations through the
`feq`-pair/recoloring/accumulate transport (identity J7) — at different
rates, so `sum(rho_r+rho_b)` and `sum_f sum_q f_q` diverge monotonically
(`d_fc` grows linearly). Walls/bounce-back are exactly innocent (C2:
bit-exact zero drift over 10k steps). Uniform single-phase states are a
bit-exact fixed point with zero drift at all tested domain sizes (C0). In
the production-relevant regime (evolving menisci, C3) the leak is
backend-independent (CPU 1.517e-8 vs GPU 1.556e-8 per step, both R^2 >
0.999, both J1 sign-positive in 100% of late-window steps).

Executor proposal (reviewer to judge): **PASS_DIAGNOSIS_READY_FOR_FIX**,
mechanism class **B**. No fix was implemented (contract section 11).

## Method

The audited timestep calls the public kernels in the exact `step()` order
with f64 host-reduction measurements at checkpoints S0..S6:

```
S0 -> collision -> S1 -> F.fill(0) -> S2 -> streaming1 -> S3
   -> Boundary_condition -> S4 -> streaming3 -> S5
   -> Boundary_condition_psi -> S6          (no reservoirs; all bc=0)
```

Non-traced steps use the production `step()` entry itself. Host reads do
not mutate state; this is verified by identity J9 (S6(n) == S0(n+1)
exactly across the measurement boundary, every traced step, all runs).
Mass views: `Mff`, `MFF`, `Mr`, `Mb`, `Mracc`, `Mbacc`, `Mrho`; identities
J0..J9 and cross-representation residuals `d_fc`, `d_frho`, `d_crho` as
defined in the driver docstring and contract section 3/4.

## Isolation matrix (contract section 5)

Fitted drift slopes (relative, per step; f64 host sums, fluid nodes):

| run | dims | steps | Mff (total) | Mc (colour) | Mrho | late-window J1 | late-window J7 |
|---|---|---|---|---|---|---|---|
| C0_16_gpu | 16^3 | 5000 | 0 (bit-exact) | 0 | 0 | 0 | 0 |
| C0_24_gpu | 24^3 | 5000 | 0 | 0 | 0 | 0 | 0 |
| C0_32_gpu | 32^3 | 5000 | 0 | 0 | 0 | 0 | 0 |
| C0_24_cpu | 24^3 | 5000 | 0 | 0 | 0 | 0 | 0 |
| C1_gpu | 64x24x24 | 10000 | +1.046e-8 (R2 .996) | +2.03e-9 (R2 .911) | +1.046e-8 | +1.42e-8, 95% pos | +7.0e-9, 80% pos |
| C1_cpu | 64x24x24 | 5000 | +6.65e-9 (R2 .80)* | +4.07e-9 (R2 .76)* | +6.65e-9* | -1.0e-11, 50% pos* | -5.4e-11, 55% pos* |
| C2_gpu | 32x46x6 | 10000 | 0 (bit-exact) | 0 | 0 | 0 | 0 |
| C2_cpu | 32x46x6 | 5000 | 0 | 0 | 0** | 0 | 0 |
| C3_gpu | 126x46x6 | 20000 | +1.556e-8 (R2 .9999) | +8.31e-9 (R2 .993) | +1.556e-8 | +1.59e-8, 100% pos | +7.5e-9, 100% pos |
| C3_cpu | 126x46x6 | 10000 | +1.517e-8 (R2 .9999) | +1.14e-8 (R2 .998) | +1.517e-8 | +1.58e-8, 100% pos | +9.9e-9, 100% pos |

\* C1_cpu rises during the IC-relaxation transient then **plateaus**
   frozen (+3.5221e-5 flat from t~3200 to 5000): on CPU the quiescent
   flat interface reaches a bit-frozen state whose per-step identities
   are unbiased (J1 frac_pos 0.50). GPU continues drifting at the same
   state. The divergence is a quiescent-state arithmetic-realization
   difference, not a different mechanism (see C3, where both backends
   drift identically under active meniscus dynamics).
\** C0/C2 CPU show a constant J6 = -1.49e-8 offset (frac_pos 0.00,
   non-accumulating): a static device-vs-host f32 representation
   difference of the frozen state, not drift (horizon slope 0).

Late-window J1/J7 detail: `late_window_identities.json`; full per-step
series: `<tag>/identities.csv`.

## Answers to the four audit questions (contract section 1)

1. **First sub-step with measurable imbalance:** S0->S1, the collision
   kernel (identity J1 for the total channel, J7 for colour). Every other
   sub-step is exactly conservative in every run: J3 (streaming1), J5
   (streaming3 copy), J8 (colour consume), J0/J2/J4/J9 are bit-exact zero
   across all 10 runs x 40 traced steps. The cumulative cross-represent-
   ation residual `d_fc`/`d_crho` first exceeds 1e-6 relative during IC
   relaxation: step 200 (C1_gpu), 400 (C3_gpu), 400 (C1_cpu), 600
   (C3_cpu). `d_frho` never becomes material (total f vs macro rho stay
   equal to <=1e-9).
2. **Mechanism family:** inconsistent bookkeeping between the total and
   colour populations inside `collision` (class B), rooted in f32
   arithmetic: (i) J1 — the moment roundtrip `m = M F` (integer, exact
   row 0) followed by `f = inv_M m` does not preserve the zeroth moment
   in f32 because `inv_M` is the f64 inverse cast to f32; the residues
   multiply the surface-tension/non-equilibrium moment components that
   exist only at diffuse interfaces (`meq[1,9,11,13,14,15] += CapA*cc`
   terms), producing a sign-biased per-node mass error; (ii) J7 — the
   colour transport's per-pair `feq(s,rho_r)+feq(s,rho_b)` sums, the
   recoloring pair arithmetic `(a+c)+(b-c) != a+b` in f32, and the 19-way
   f32 accumulation into `rhor/rhob`, at a smaller rate. Not atomics
   ordering (backend-independent in C3), not walls (C2 exactly clean),
   not macro reconstruction (J6 small; Mrho slope == Mff slope), not
   random accumulation (C0 bit-exact fixed point; J1 frac_pos 1.00 late).
3. **Solver correction before V3?** The measured production-relevant
   rates (total <=1.56e-8/step, colour <=1.14e-8/step) are inside the
   owner's calibrated V2 envelope (r_M <= 2e-8/step; total-normalised
   <=1e-3/60k). V3 may proceed under that envelope **without** a fix;
   the fix is a recommended separate task (below). This is a contract-
   owner decision, not the executor's.
4. **Bounded-floor scaling law (if class A were claimed):** not
   supported. GPU/C3 drift is linear in T (7.46e-5 / 1.52e-4 / 2.31e-4 /
   3.10e-4 at 5k/10k/15k/20k — increments 7.5-7.9e-5 per 5k) with R2 =
   0.9999 and per-step sign bias 100%, i.e. an unbounded linear leak, and
   the uniform-state floor is exactly zero (C0), which a bounded-precision
   explanation cannot produce.

## Spatial budget (C3_gpu, final vs ref1000 vs t0)

Regions mechanical from final psi (wall rows carved out first; |psi|<=0.9
interface; gas/liquid bulk beyond):

| region | nodes | dMc (ref1000) | dMf (ref1000) | dMrho (ref1000) |
|---|---|---|---|---|
| gas_bulk | 17880 | -33.79 | +3.70 | +3.70 |
| interface | 960 | +2.91 | +0.33 | +0.33 |
| liq_bulk | 8520 | +35.33 | +4.10 | +4.10 |
| wall_rows | 1440 | +0.16 | +0.35 | +0.35 |

Net: dMc = +4.6 (== fitted colour drift 1.7e-4 x 28800), dMf = +8.5
(== 3.1e-4 x 28800). The colour redistribution gas->liquid (-30 Mr out
of the pocket) is meniscus dynamics, not leak; the leaked total-channel
mass resides in both bulks (+3.7/+4.1) with wall rows and the interface
band contributing ~0 — consistent with creation at the interfaces during
collision followed by streaming into the bulks within the same step
(streaming itself is exactly conservative, J3 = 0). Full table with
rho_r/rho_b columns and both references: `C3_gpu/spatial_budget.csv`.

## Backend comparison (contract section 7)

`backend_comparison.csv`. C3: CPU 1.517e-8 vs GPU 1.556e-8 per step
(2.5% apart, same sign, same R2 > 0.999, same 100% J1 sign bias) ->
algorithmic f32 bookkeeping, not atomic ordering (contract section 7
interpretation rule). C1 quiescent-state CPU/GPU difference documented
above and in the CSVs.

## Scaling (contract section 8)

- Domain (C0: 16/24/32, GPU): zero drift at every size — no
  volume-related floor.
- Horizon (C3_gpu 5k/10k/15k/20k): linear in T for the total channel
  (slope 1.556e-8/step, R2 0.9999); colour sublinear (increments 5.4 /
  4.3 / 3.7 / 3.7e-5 per 5k) — the two channels' divergence `d_fc` is
  therefore superlinear in the colour-vs-total sense and reaches +1.39e-4
  at 20k in the small analogue.
- Interface-area normalization: leak per interface-band node per step
  (rate x N / 960-band): C1_gpu 3.4e-4, C3_gpu 4.7e-4 absolute mass per
  node per step — same order; the actively curving menisci (C3) leak
  ~1.4x the quiescent flat interfaces (C1).

## Consistency with V2 production evidence

V2 production (326x46x6, 60k steps, GPU) measured population-channel
+9.21e-4 (1.53e-8/step) and colour +5.47e-4 (9.1e-9/step). The C3
analogue reproduces 1.556e-8/step (total, +2% vs V2) and 8.31e-9/step
(colour, -9% vs V2) — the audit geometry captures the production
mechanism.

## Classification and proposal (contract sections 10-11)

**Class B** — colour/total-population bookkeeping mismatch, localized at
the collision kernel (S0->S1), repeatable, not a transitional storage
representation (S6(n)==S0(n+1) exact; accumulators consumed exactly).

No-fix rule honoured: no solver source touched; no diagnostic added to
production code.

Solver-fix proposal for a separate task (NOT implemented):

- kernel / path: `collision()` in `lbm_solver_cg3d.py` — (a) the
  `inv_M @ m_temp` reconstruction (total channel), (b) the `g_r/g_b`
  transport into `rhor/rhob` (colour channel);
- failed identity: per-step global `sum_fluid sum_s f` should equal the
  pre-collision `sum_fluid sum_s F` (J1), and `sum(rho_r+rho_b)` should
  equal its pre-transport value (J7); in exact arithmetic both hold
  (M row 0 exact; S[0]=0; recoloring pair-conserving);
- candidate minimal scopes: f64 intermediate accumulation for the moment
  roundtrip and/or an exact per-node zeroth-moment correction of the
  reconstructed f; colour side: transport the pair sum exactly and split
  by the recolored fraction;
- regressions that would need rerun if fixed: P-line unit validations
  (Laplace sigma=1.012*CapA, contact angle theta(-0.68), Poiseuille
  eff~0.99), V1c a26/a40 differential gates, V2 symmetry/topology
  sentinels, and re-issue of every mass-drift number in V1c/V2 evidence
  (all are expected to shift at the f32-floor level only).

## Validation commands

- Batch (exact reproduction): `bash results/conservation_audit/run_batch.sh`
  (per-run exact commands + exit codes in `logs/*.log` and `prov.json`).
- Aggregate: `python tests/conservation_audit.py analyze`.
- All 10 runs exit 0; no NaN/Inf; umax guardrail not applicable (no
  force; max 2.2e-2 meniscus currents in C3).

## Artifacts

`results/conservation_audit/`: `summary.json`, `backend_comparison.csv`,
`scaling_results.csv`, `late_window_identities.json`, per-run dirs
(`substep_mass_trace.csv`, `identities.csv`, `long_horizon_mass.csv`,
`case_report.json`, `prov.json`, `logs/`; C3 additionally
`spatial_budget.csv`, `symmetry_check.json`, `fields_t0.npz`,
`fields_ref.npz`), `run_batch.sh`, `logs/`. Manifest:
`MANIFEST.json`; provenance: `PROVENANCE.md`.
