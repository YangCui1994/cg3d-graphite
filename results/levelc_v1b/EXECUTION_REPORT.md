# EXECUTION REPORT — BI-V1B-DIAGNOSTIC-001

- Task: V1b diagnostic — boundary / static-Pc / dynamic-Pc separation
  (`V1B_DIAGNOSTIC_CONTRACT.md`), executor = the interactive ZCode session
  per `START_V1B.md` section 3.
- Base SHA: `e9540bcadb86257c70b805afc98f2eec9626c64e`
- Producer revision (driver committed before any run):
  `da9a13d…` (`tests/levelc_v1b.py`, blob sha256 `f66aabb236281b00…`,
  unchanged in the final candidate).  All runs recorded
  `run_head = da9a13d…` in their `prov` blocks and in `MANIFEST.json`.
- Candidate: this commit (results + reports only; no solver change).
- Changed files: `tests/levelc_v1b.py`, `results/levelc_v1b/**` only.
- Primary runs (all exit 0, console logs + shell exit codes under
  `logs/`):
  1. `static --hy 26 --tag static_h26` (60 000 steps, steps_cap)
  2. `static --hy 40 --tag static_h40` (60 000 steps, steps_cap)
  3. `dynamic --hy 26 --tag dyn_h26` (front reached x_stop, step 40 250)
  4. `dynamic --hy 40 --tag dyn_h40` (front reached x_stop, step 36 500)
  5. `dynamic --hy 26 --L 472 --tag dyn_h26_2L` (60 000 steps, steps_cap)
  6. `collect` (summary.json / pressure_budget.csv / gates.csv /
     MANIFEST.json)
- No solver modification.  No tuning of `psi_solid`, `CapA`, viscosity,
  geometry height, or thresholds.  Figures intentionally omitted
  (contract section 10: only commit figures regenerable from the exact
  committed producer — numerical data + committed producer satisfy the
  binding rule instead).

## Measured facts

| Quantity | h=26 | h=40 | Source |
|---|---|---|---|
| `Pc_static` | 3.1316e-3 | 2.2845e-3 | `static_*/report.json` |
| `C_static = Pc·h/(2σ)` | 0.6705 | 0.7525 | idem |
| `theta_static_slit` | 47.90° | 41.19° | idem |
| `V_meas` (front, primary) | 4.9743e-3 | 5.5878e-3 | `dyn_*/report.json` |
| `R2[x,t]` on window | 0.99999806 | 0.99999999 | idem |
| `Pc_dynamic` (far-field extrap.) | 2.8844e-3 | 1.7970e-3 | idem |
| `V_hyd` | 6.7422e-3 | 9.9415e-3 | idem |
| `V_meas/V_hyd` | 0.738 | 0.562 | idem |
| dp/dx liquid / analytic | 1.051 | 0.974 | idem |
| dp/dx gas / analytic | 0.783 | 0.735 | idem |
| (jump_in+jump_out)/Pc_dyn | 0.328 | 0.514 | idem |
| `Ca = μV/σ` | 8.19e-3 | 9.20e-3 | idem |
| 2× length scan | L1=241, V1=4.9743e-3; L2=477, V2=3.0002e-3 → `L_eq`=117.7, `L_eq/L1`=0.488 | — | `summary.json` |
| `Pc_dynamic/Pc_static` | 0.921 | 0.787 | `summary.json` |

Static relaxation: `umax` plateaus at 2.2e-2 (h26) / 2.5e-2 (h40) — the
familiar colour-gradient spurious-current floor near static interfaces;
`Pc` drift over the last 10 blocks is 7.6e-5 (h26) — the pressure jump
is stationary although the kinetic criterion (umax<5e-6) is not met.
Both facts recorded in `static_*/report.json::convergence` (process
completion ≠ convergence is stated there explicitly).

Colour-mass closure (f64 bookkeeping, `closure_r/b_last` in reports):
h26 −8.9 / −11.1 mass units against an injected liquid volume of
≈ 40 000 → relative ≈ 2.8e-4; same order for all runs — no order-one
leakage.  Reported, not gated (g9).

## Gates (declared mechanical rules; no post-hoc adjustment)

| Gate | h26 | h40 | 2L |
|---|---|---|---|
| g1 no NaN/Inf | PASS | PASS | PASS |
| g2 u_max ≤ 0.12 | PASS (0.0235) | PASS | PASS |
| g3 zero imposed ΔP (reservoir ρ=1) | PASS (dev 0.0) | PASS | PASS |
| g4 monotonic window | PASS | PASS | PASS |
| g5 window valid (explicit threshold) | PASS | PASS | PASS |
| g6 R2[x,t] ≥ 0.995 | PASS | PASS | PASS |
| g7 \|V/V_hyd−1\| ≤ 0.10 | **FAIL** (0.738) | **FAIL** (0.562) | **FAIL** (0.836) |
| g8 Poiseuille gradients ≤ 10% | **FAIL** (gas 0.783) | **FAIL** (gas 0.735) | **FAIL** (gas 0.721) |
| static scaling ≤ 10% | **FAIL** (11.53%) | — | — |

`all_hard = false` for every dynamic case; `gate_static_scaling=false`.

## Interpretation (separated per contract section 11)

- **Measured fact**: with the separated open-boundary layout the front
  is stable, monotonic and essentially perfectly linear (R2 ≈ 1−2e-6),
  and faster than the old V1 layout (4.97e-3 vs 3.86e-3 at h26).
- **Measured fact**: the fixed extra hydraulic resistance halved but
  did not vanish: `L_eq/L1` 0.78 (old V1 estimate) → 0.49 (V1b
  two-length scan); residual boundary jumps are 33–51% of `Pc_dynamic`.
- **Measured fact**: the same-slit static angle is 41–48°, not the
  30° droplet-registry value; h26/h40 static coefficients differ by
  11.5%.
- **Analytic relation**: `V_hyd = Pc_dynamic·h²/(12μL_hyd)` and the
  plane-Poiseuille gradient `12μV/h²` — used as declared, not fitted.
- **Project engineering gate**: the 10% internal-consistency gates fail
  (g7 by 26–44%, g8 gas leg by 22–28%, static scaling by 1.5 points).
- **Model interpretation (preliminary, not a conclusion)**: the
  semi-permeable membrane planes themselves appear to carry a finite
  hydraulic/capillary signature even in the separated layout, and the
  gas-column gradient deficit is systematic across all three dynamic
  cases; both need physical explanation before V2.
- **Unresolved scientific questions**:
  1. why the gas-column pressure gradient is consistently ~0.72–0.78 of
     plane-Poiseuille while the liquid column matches (~1.0);
  2. whether the residual `L_eq ≈ 118 lu` is dominated by the two
     membrane planes (0.33–0.51 Pc jumps) or by entrance effects;
  3. why `C_static` transfers from h26 to h40 only within 11.5%, not
     10% (interface-width/resolution coupling?);
  4. `Pc_dynamic/Pc_static` = 0.92 (h26) vs 0.79 (h40) — resolution
     dependence of the moving-meniscus deficit.

## Deviations

- Static runs stopped at the 60 000-step cap with umax at the
  spurious-current floor (2.2e-2) rather than the declared 5e-6 kinetic
  criterion; Pc stationarity (drift < 1e-3) was met.  The convergence
  block records both facts; no rerun was attempted (no-tuning rule).
- `dyn_h26_2L` ended at the step cap with the front at x_vol ≈ 220
  (window rule satisfied from x≥94; R2 = 1.0).

## Suggested next action

Independent fresh review of this candidate against
`V1B_DIAGNOSTIC_CONTRACT.md`; several contract section 12
HUMAN_REQUIRED criteria are plausibly met (order-one residual boundary
resistance; static scaling inconsistency; g7 failures) and must be
weighed by the reviewer, not by the executor.
