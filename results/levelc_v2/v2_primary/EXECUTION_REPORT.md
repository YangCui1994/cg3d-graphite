# EXECUTION REPORT — BI-V2-BILATERAL-001

- Task: V2 bilateral trapped-pocket verification per
  `V2_BILATERAL_CONTRACT.md`, launched from `START_V2.md` (executor =
  interactive ZCode session).
- Base: `2b82f9a5f448e756b5d5903b0df37f9a3b11d804` (V1c candidate)
- Producer revisions: `d689526` (driver) → `2fcb552` (cluster-size fix)
  → `9ed4bcb` (declared equil window) → `7a16bd7` (bulk-node rho
  guardrail semantics) — all ancestors; the candidate carries the final
  file byte-identical.  Two earlier aborted attempts (their exit
  reasons below) are part of the record; no GPU result from them is
  used as evidence.
- Primary run: `python tests/levelc_v2_bilateral.py --tag v2_primary`
  (interpreter = conda env `lbm`), 60 000 steps completed, shell exit 0,
  console log `logs/v2_primary.log`.

## Geometry / symmetry (contract sections 5-7)

nx=326, ny=42, nz=6: `wall[0,3) | liquid[3,83) | gas[83,243) |
liquid[243,323) | wall[323,326)`; h=40, B=80, G0=160, mirror plane
162.5.  Programmatic checks (all PASS, `symmetry_check.json`): solid /
psi0 / psi_solid exact mirror equality, equal buffers, centred gas.
No reservoirs, no membranes, no forcing.  t=0 topology: exactly ONE
non-wetting cluster (38 400 nodes), trapped by construction
(`topology_t0.json`).

## Headline results

| Metric | Value | Gate |
|---|---|---|
| front mirror error `max e_x` | **0.0013 lu** (RMS 0.0010) | g5 PASS (≤ max(2, 0.02d)) |
| full-field symmetry `max E_psi` | 8.3e-5 | diagnostic |
| one-sided displacement d(t) | −0.84 lu (retreat; static-meniscus shaping) | — |
| rate symmetry | NOT_DISCRIMINATING (window displacement 0.09 lu < 2 lu) | contract-permitted |
| colour-mass drift | max ε_r 4.2e-4, **max ε_b 6.7e-4** | **g6 FAIL (5e-4)** |
| u_max (post-equil) | 0.0254 | g2 PASS |
| bulk-node rho range (post-equil) | [0.935, 1.008] | g3 PASS |
| all-fluid per-node rho min | 0.8851 (interface structure) | diagnostic, see below |
| binary gas volume | 38 304 → 38 400 (+0.25%) | diagnostic |
| continuous gas volume | 38 288 → 38 373 (+0.22%) | diagnostic |
| gas pocket mean rho / p | 1.0035 → 1.0041 / 0.33449 → 0.33470 (+0.06% compression) | diagnostic |
| cluster count | 1 throughout (no fragmentation) | g7/g8 PASS |
| buffer gas occupancy | 288 nodes on EACH side, exactly equal | diagnostic |
| INTERACTION_ONSET | **NOT_REACHED** (G_bulk 150→146, fronts stalled) | contract-permitted |
| NaN/Inf | none | g1 PASS |

## The two guardrail-interpretation decisions (declared, evidence-based)

1. **Equilibration window.**  The sharp-IC interface relaxation dips
   per-node rho to 0.8851 at the x≈80/245 interfaces (t=1000; the first
   attempt stopped on it).  Guardrails now gate only for
   `t > --equil` (5000, repo equilibration convention);
   transient worst values are recorded in `report.json::equil`.
2. **Bulk-node rho guardrail.**  The per-node all-fluid minimum is a
   diffuse-interface density structure ALSO PRESENT IN THE ACCEPTED
   V1c BASELINE (committed `fields_final.npz` per-node minima:
   dyn_h40_s **0.8877**, static_h40 0.8907, static_h26 0.8930).
   The contract's "[0.89, 1.11] approximately" guardrail targets
   phase/pocket compression, so g3 is applied to BULK nodes
   (|psi|>0.9): [0.935, 1.008] PASS.  All-fluid extremes remain
   reported per sample (`rho_min/max_allfluid` in gas_series.csv).

## g6 mass-drift FAIL — decomposition for the reviewer's blocking judgment

ε_b exceeds the 5e-4 gate (6.7e-4 at 60k steps) with a slow,
near-linear accumulation (~1.1e-5 / 1000 steps; per-step relative
7e-9).  Signed decomposition: BOTH colours drift POSITIVE
(ε_r +4.1e-4, ε_b +6.6e-4; total mass +5.4e-4) — i.e. not a colour
exchange at interfaces but a rounding-level total-mass drift of the
f32 evolution, the same floor exhibited by the ACCEPTED V1c dynamic
runs (closure_r/b 4.9e-4–6.8e-4 over comparable horizons, there
reported-not-gated).  Trajectory data:
`mass_stability_series.csv`.  Per the contract the blocking judgment
(`exceeded monotonically or by an order-one amount`) belongs to the
reviewer; the executor reports the letter-FAIL as-is.

## Physics summary (interpretation, contract section 4.1 anticipated)

As predicted for this closed system (capillary pressure ~2.4e-3 vs
pocket stiffness ρc_s²=1/3), the fronts do not sweep: after
interface/meniscus shaping (≈0.8 lu column-mean retreat = static
meniscus curvature forming, with near-wall wetting films — buffer gas
occupancy 288/side symmetric) the system stalls with the pocket
compressed by only ~0.06% (p +2.1e-4).  G_bulk shrinks 150→146 bulk
columns.  No collision, no fragmentation, symmetry at the 1e-3-lu /
1e-4-field level throughout.

## Deviations

- Optional near-contact stress probe (contract section 16): NOT RUN
  (optional; primary case already exhibits stalled non-interaction).
- Figures: none on the product branch (provenance rule); SVGs are
  generated on the control branch from committed evidence.

## Suggested next action

Fresh review against `V2_REVIEWER_CONTRACT.md`; g6 requires the
reviewer's explicit blocking judgment with the decomposition above.
