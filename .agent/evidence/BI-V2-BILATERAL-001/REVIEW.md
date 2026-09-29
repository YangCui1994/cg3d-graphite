stage: V2
attempt: 1
candidate: 5e679d8d99d338f9ab28565c636f021a0f9211b2
execution_report: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-V2-BILATERAL-001/results/levelc_v2/v2_primary/EXECUTION_REPORT.md

# V2 Fresh Reviewer Report — BI-V2-BILATERAL-001

Reviewer: independent fresh reviewer (no prior episode context).
Scope: frozen candidate only. No product file, commit, branch or executor
artifact was modified; no executor transcript was read. The only file written
is this REVIEW.md.

Method note. Everything below was recomputed from the committed evidence with
the `lbm` interpreter (CPU only, no GPU simulation): `front_series.csv`,
`gas_series.csv`, `mass_stability_series.csv`, `report.json`,
`symmetry_check.json`, `topology_t0.json`, the driver source, and the three
field snapshots `fields_{initial,mid,final}.npz`. The `.npz` files are not in
the git tree (`.gitignore:9` covers `*.npz`), but their SHA256 values match the
committed `MANIFEST.json` exactly, so they are hash-bound to the candidate; the
durable committed reduced data are the slice CSVs. Two external baselines were
also recomputed: the accepted V1c fields in
`../BI-V1C-CLOSURE-001/results/levelc_v1c/*/fields_final.npz` and
`results/levelc_v1c/summary.json` (both on the candidate's ancestor tree).

---

## 1. Candidate binding

| Item | Required | Verified |
|---|---|---|
| Candidate SHA | `5e679d8d99d338f9ab28565c636f021a0f9211b2` | HEAD = `5e679d8d99d338f9ab28565c636f021a0f9211b2` ✓ |
| Product branch | `agent-task/BI-V2-BILATERAL-001` | matches ✓ |
| Base | `2b82f9a5f448e756b5d5903b0df37f9a3b11d804` | `git merge-base --is-ancestor` → true; 5 V2 commits sit on top ✓ |
| Product worktree | clean | `git status --porcelain` empty ✓ (also empty after my re-run of the unit checks) |
| Changed files base..cand | V2-authorized only | `tests/levelc_v2_bilateral.py`, `tests/v2_unit_check.py`, `results/levelc_v2/**` — 22 files, +2 474 lines ✓ |
| Solver / cg3d / V1* / runner | unchanged | `git diff --stat base..cand -- lbm_solver_cg3d.py cg3d/` is empty; no V1/V1b/V1c source or results touched ✓ |
| MANIFEST hashes | 19/19 artifacts | all 19 SHA256 values reproduce byte-exactly ✓ |
| Producer hash | `producer_sha256` | `3b618e2a6fc1b6fca8423d0204df9c037a89ccad21d0aa684728ba9516f5ccd3` = SHA256 of the committed driver ✓ |
| Producer revision | recorded | `MANIFEST`/`report.json`/`PROVENANCE.md` say `052ab97` (an ancestor of the candidate) ✓ — but `EXECUTION_REPORT.md` names `7a16bd7`, which does not exist (see N6) |
| Shell exit | 0 | `results/levelc_v2/logs/v2_primary.exit` = `0`; `report.json.exit_reason = steps_cap` ✓ |

Binding is accepted: the candidate is identified, frozen, clean, descends from
the declared base, and touches only V2-authorized paths.

## 2. Requirement / gate table

All gate numbers below are my own recomputation, not the executor's.

| # | Contract gate | Executor claim | Reviewer recomputation | Verdict |
|---|---|---|---|---|
| g1 | no NaN/Inf | none | no non-finite value in any series; `exit_reason = steps_cap`; all field snapshots finite | **PASS** |
| g2 | `u_max ≤ 0.12` | 0.0254 post-equil | max 0.025473 (all samples), 0.025435 post-equil → 4.7× margin | **PASS** |
| g3 | fluid ρ inside `[0.89, 1.11]` "approximately" | bulk-node `[0.935, 1.008]` | bulk (`|ψ|>0.9`, t>5000): `[0.935295, 1.008070]` ✓. All-fluid (t>5000): min **0.888446** (16 samples < 0.89) — a *letter* miss; all-fluid max 1.008070; recovers to 0.890860 at t=60 000 | **PASS under the declared bulk-node semantics; the semantics is a gate-scope change requiring ratification (B2)** |
| g4 | exact IC/geometry/wettability symmetry | `all_pass` | independently: `psi_solid` is a constant field (mirror-exact by construction); re-derived fluid mask `x∈[3,323), y∈[1,41)`; committed t=0 fields mirror exactly (`max|Δψ| = max|Δρ| = 0` over 76 800 fluid nodes); buffers 80/80, gas 160 centred on x = 162.5 | **PASS** |
| g5 | `e_x ≤ max(2 lu, 0.02 d)` | max 0.0013 lu | max 0.001297 lu, RMS 0.000996 lu; bound = 2 lu under both the reported and the offset-corrected `d` (see N1) → 1 542× margin | **PASS** |
| g6 | `max(ε_r, ε_b) ≤ 5e-4` | ε_r 4.2e-4 PASS, ε_b 6.7e-4 **letter-FAIL** | ε_r max 4.207e-4 ✓; ε_b max **6.730e-4** ✗; both strictly monotone (0 of 59 increments negative); ε_b above the gate from t=35 000 to 60 000; independent population-channel check `Σ_fluid ρ`: 76 800.000 → 76 870.715 = **+9.21e-4** (monotone, near-constant rate 1.53e-8/step) | **FAIL (letter), exceedance monotone ⇒ blocking per §10 (B1)** |
| g7 | t=0 = one trapped non-wetting cluster | 1 cluster / 38 400 | my own 6-neighbour + z-wrap union-find: **1 cluster, 38 400 nodes** (=160×40×6), mean ρ 1.000000, `G_bulk` = 160 | **PASS** |
| g8 | no fragmentation/disappearance before onset | 1 cluster throughout | 1 cluster in all 60 committed samples; my labelling at t=0/30 000/60 000: 1 cluster (38 400 / 38 376 / 38 400); `largest == V_bin` at every sample | **PASS** |
| g9 | if `INTERACTION_ONSET` occurs, verified by the declared rule | `NOT_REACHED` | `G_bulk` = 146 at every sample; my independent column-class recomputation at t=30 000 and 60 000 gives `G_bulk` = 146 (run [90,236), envelopes 79/246) → never 0 | **PASS (vacuous; explicitly permitted by §8.4/§9)** |
| g10 | reviewer can reproduce the metrics | — | front-series internal relations reproduce exactly (see §3); gas/mass series endpoints reproduce from hash-bound fields; product unit checks re-run PASS | **PASS** |
| cond. | `2|V_L−V_R|/(|V_L|+|V_R|) ≤ 0.05` if both fronts move ≥ 2 lu | `NOT_DISCRIMINATING` (0.09 lu) | confirmed: window [12 000, 60 000] displacements −0.0920 / −0.0922 lu; the *maximum achievable* displacement in **any** window is 0.72 lu = 36% of the 2-lu trigger, so the status is robust to window choice. Supplementary displacement-symmetry ratio: 0.11% (full run) / 0.26% (post-transient window) | **NOT_DISCRIMINATING — contract-permitted; the underlying symmetry is inside 5% by 20×** |

No `x²(t)` relation was used anywhere in this review. No collision or
interface-contact event was required. Pocket pressure was not read as real-air
compression.

## 3. Independent symmetry recomputation

Geometry (contract §5), re-derived from source and confirmed from fields:

- `nx = 3+80+160+80+3 = 326`, `ny = 42` (40-lu slit + 2 wall rows), `nz = 6`;
  layout `wall[0,3) | liquid[3,83) | gas[83,243) | liquid[243,323) | wall[323,326)`;
  h=40, B=80, G0=160; mirror map `x → nx−1−x`, node-index mirror plane 162.5
  (the reported `mirror_plane = 163.0` is the centre of the half-open gas
  interval; the gas node set is mirror-exact: 83 ↔ 242).
- No reservoirs, no membranes, no force: the driver only calls
  `set_psi_solid_field`, `init`, `step`, `color_masses`, `macro_snapshot`,
  `psi_snapshot`; all solver `bc_psi_*`/boundary switches keep their defaults.
- z is periodic by solver default (`periodic_index` wraps `k<0 → nz−1`,
  `k>nz−1 → 0` while `bc_psi_z_* = 0`), i.e. the declared "z periodic only"
  convention for the fluid topology is correct.
- t=0 IC: exactly −1 in both buffers, +1 in the gas, all fluid ρ = 1, constant
  `psi_solid = −0.68`, no noise, no velocity — all confirmed from the committed
  initial field (ρ ≡ 1.000000 on 76 800 fluid nodes).

Mirror symmetry during the run:

| Metric | Value |
|---|---|
| initial field mirror error (ψ and ρ) | exactly 0 |
| `max e_x` (primary, interpolated 0.5 crossing) | **0.001297 lu** at t=25 500 |
| `rms e_x` | 0.000996 lu |
| gate margin | 1 542× (2-lu floor) |
| volumetric mirror error `e_x_vol` | 0.9989–1.0000; the ±1-lu spread is a *constant definitional offset* of that secondary estimator (left counts columns from x=3 while the right uses `(NX−W) − Σφ`), so the fluctuation is 0.0011 lu |
| local field asymmetry (my own check, not the executor's mean) | `max|ψ(x)−ψ(325−x)|` = 5.9e-3 (0.6% of the ±1 range); 370 of 76 800 fluid nodes above 1e-3, **none** above 1e-2 |
| reported `E_ψ` (mean) | ≤ 8.34e-5 — reproduced analytically (my float64 mean × 80640/76800 = 7.58e-5 at t=60 000, matching the CSV) |
| mixed-envelope pairing | `env_R = 325 − env_L` at all 240 samples (difference identically 0) |
| buffer gas occupancy | equal per side in 59 of 60 samples; **one** exception at t=32 000 (288 vs 276) — see N3 |
| front displacement symmetry | retreat ratio `2|ΔL−ΔR|/(|ΔL|+|ΔR|)` = 0.11% (full run), 0.26% (post-transient window) |

Front-series internal relations were verified row by row
(`x_R* = 325 − x_R`, `e_x = |x_L − x_R*|`, `e_x_vol = |x_Lvol − (325 − x_Rvol)|`,
and the `d` identity that exposed N1): all residuals ≤ 1e-5 lu, i.e. the
committed series is internally consistent. Front motion is *not* strictly
monotone (8 small re-advances of order 0.05 lu during the interface-formation
transient) and then stalls; the contract imposes no monotonicity requirement
for V2.

## 4. Topology review

- Connectivity convention implemented as declared: `scipy.ndimage.label` with
  `generate_binary_structure(3,1)` (6-neighbour) plus a union-find merge of
  `(i,j,0) ↔ (i,j,nz−1)` pairs only (z wrap; x and y non-periodic). I re-read
  the merge code and the merged-size aggregation; the aggregation fix in
  `2fcb552` is correct (node counts per root, not root tallies), and my
  independent labelling reproduces the committed numbers at t=0, 30 000 and
  60 000.
- t=0 (contract §9): **exactly one** non-wetting cluster, 38 400 nodes =
  160×40×6, mean ρ = 1.000000, `G_bulk` = 160 → the central pocket is trapped
  by construction with the intended topology. No vent/reservoir exists, so
  there is no vent-loss event to look for (V1c external review §7.2).
- Evolution: `n_clusters ≡ 1` in all 60 samples; `largest == V_bin` at every
  sample (no secondary clusters at all); binary gas volume
  38 400 → 38 304 (minimum, t=1 000) → 38 400; continuous volume
  38 400 → 38 374.72 (−0.066%); pocket mean ρ 1.000000 → 1.004246 (+0.42%);
  min ψ inside the largest cluster stays positive (0.0206 at t=60 000).
- No fragmentation, no disappearance, no merging event. Gate g7/g8 satisfied by
  independent recomputation, not by executor assertion.
- The only topology-adjacent numerical artefact is a −96-node (−0.25%) dip in
  the binary gas count at t=1 000 (sharp-IC interface relaxation), which fully
  recovers by t=33 000. It is confined to the interface columns, is exactly
  mirror-symmetric, and is *not* a fragmentation event (cluster count never
  changes).

## 5. Interaction-event review

- Rule as declared (contract §8.4): column is bulk-gas if ≥95% of its fluid
  nodes have ψ > +0.9; bulk-liquid if ≥95% have ψ < −0.9; otherwise mixed.
  `G_bulk` = longest contiguous bulk-gas run; `INTERACTION_ONSET` = first
  sample with `G_bulk == 0`. The implementation matches the contract text.
  One benign difference: the driver takes the longest contiguous bulk-gas run
  *anywhere* rather than strictly "between the two mixed envelopes"; in this
  geometry (a single central gas band, no other gas regions) the two readings
  coincide.
- Recomputing the column classes from the hash-bound fields at t=30 000 and
  60 000: `G_bulk` = 146, gas run [90,236), envelopes 79 and 246 — identical to
  the committed `gas_series.csv` at those times. `G_bulk` = 146 in **all** 60
  committed samples; it is never 0 between the envelopes.
- `INTERACTION_ONSET = NOT_REACHED` is therefore confirmed, and §8.4/§9 state
  explicitly that this is an acceptable, non-failing outcome. The two fronts
  move *outward* (retreat into their own buffers) by ~0.117 lu in the first
  250 steps and by 0.838 lu over the whole run and then stall, so no
  overlap/coalescence event exists in this run and there is nothing to resolve
  reproducibly.
- The executor's "G_bulk 150 → 146" is not reproducible: the committed t=0
  field gives 160 (see N2).

## 6. Conservation / stability review (including the g6 blocking judgment)

### 6.1 Stability

- No NaN/Inf in ψ, ρ, v or any reduced series; `exit_reason = steps_cap` after
  the full 60 000 steps (contract §12 satisfied).
- `u_max`: 0.025473 (all samples) / 0.025435 (post-equil) vs the 0.12 cap.
- `u_rms` ~1.5e-3; `E_ψ` ≤ 8.34e-5.
- Bulk-phase density `[0.935295, 1.008070]` post-equil; all-fluid maximum
  1.008070 (never near the 1.11 ceiling).
- Residual drift at the end (t=40 000→60 000): fronts −5.0e-4 lu/1000 steps,
  pocket mean ρ +1.6e-5/1000 steps, `u_max` +2.2e-6/1000 steps. The system is
  quasi-stationary but **not** converged; the executor makes no convergence
  claim (correct — `exit_code = 0` would not be convergence evidence anyway).
  The residual pocket-density creep is the same phenomenon as the mass drift
  below.

### 6.2 The two declared guardrail-interpretation decisions — audit

**(i) Equilibration window 5 000.** Declared in the driver (`--equil 5000`),
with the excluded transient's worst values still recorded
(`report.json::equil`: ρ_min 0.885094 at t=2 000, `u_max` 0.025473).
Audit result: the window does **not** decide g3 — under *any* literal all-fluid
reading the excursion survives past 5 000 (16 samples below 0.89 for t>5 000,
min 0.888446 at t=6 000) and even past the repo's own equilibration default
(`docs/BC_IC_OUTPUT.md` line 38 uses `equil_steps = 20000`: still 9 samples
below 0.89, min 0.889895). So choosing 5 000 instead of 20 000 is *stricter*,
not self-serving. The citation in the driver docstring ("repo equilibration
convention, BC_IC_OUTPUT.md section 2") is imprecise: that document's number is
20 000 and it concerns the geometry ladder, not guardrail gating. Verdict:
acceptable as declared, with the citation corrected; it is not what makes g3
pass.

**(ii) Bulk-node (|ψ| > 0.9) density semantics.** This is what makes g3 pass,
so I audited it hard against the contract's "approximately" wording and against
the V1c baseline evidence cited by the executor:

| Claim (executor) | My recomputation from the V1c run fields | Match |
|---|---|---|
| dyn_h40_s = 0.8877 | 0.887740 (at x=237, ψ = 0.0557, i.e. an interface node) | ✓ |
| static_h26 = 0.8930 | 0.893018 (x=91, ψ = −0.1075) | ✓ |
| static_h40 = 0.8907 | **0.888573** (x=147, ψ = −0.0070) | ✗ — transcription error (N4) |
| (not claimed) | dyn_h26_s = 0.880460, dyn_h40_2L = 0.891801 — both from *accepted* dynamic runs | — |

So the accepted V1c baseline genuinely exhibits the same class of sub-0.89
per-node density minima, some **deeper** than anything in V2 (0.880460 vs
0.885094). The V2 dips are interface-localized: at t=60 000 the all-fluid
minimum sits at x=245 with ψ = 0.0208; at t=30 000 at x=80 with ψ = −0.0030;
i.e. at ψ≈0 nodes, not in the pocket and not at a boundary artefact. The
contract's concern in §11 is worded as a *pocket/phase* condition ("If the
trapped pocket requires density outside this range to continue evolving, stop
with HUMAN_REQUIRED"), and that trigger is **not** met: the pocket bulk stays in
[0.935, 1.008], and the excursion decays (0.885094 → 0.890860 at t=60 000,
i.e. back above 0.89). Verdict: substantively well founded and consistent with
the "operational … approximately … not a validated real-gas EOS range" wording;
but it *is* a narrowing of a hard gate's scope, declared by the executor rather
than authorized by the contract, so it needs contract-owner ratification
(B2). It is not, on its own, a reason to block.

### 6.3 The g6 blocking judgment (explicit)

Gate quantity per §10: `max_t(ε_r, ε_b) ≤ 5×10⁻⁴`, computed from the solver's
colour-mass sentinel (`Σ_over all nodes of ρ_r, ρ_b`, f64 accumulation — which
I confirmed is effectively a fluid-only sum, because every collision/streaming
kernel is guarded by `solid == 0` and the colour fields at solid nodes stay 0
forever; at t=0 the sentinel equals 76 800 exactly).

Facts I verified:

1. **Letter status.** ε_r, max = 4.207e-4 (pass). ε_b, max = 6.730e-4 (fail),
   first above the gate at t=35 000, still rising at 60 000.
2. **Monotonicity.** ε_b is *strictly* increasing: all 59 sampled increments are
   positive (5.4e-6 … 1.8e-5 per 1 000 steps). ε_r likewise. Both colours drift
   **positive** (m_r +16.16, m_b +25.84, total **+42.00 = +5.47e-4**), i.e. this
   is mass creation, not colour exchange at the interfaces.
3. **Rate.** ε_b's rate is 1.57e-8/step early and 5.5e-9/step in the last
   20 000 steps — decelerating by ~3×, but never zero.
4. **Independent population-channel check (new information, not in the report).**
   Σ_fluid ρ from the hash-bound snapshots: 76 800.000000 (t=0) → 76 835.214173
   (t=30 000) → 76 870.714718 (t=60 000) = **+9.21e-4**, monotone, with a
   near-constant rate of 1.174 / 1.183 absolute units per 1 000 steps
   (1.53e-8/step relative). This is ~1.7× the sentinel's total and **1.84× the
   5e-4 gate**, and unlike the sentinel its rate does not decay.
5. **The two channels disagree.** At t=60 000, Σ_fluid ρ = 76 870.71 but
   Σ(ρ_r+ρ_b) = 76 842.00 — a 28.7-unit (3.7e-4 relative) divergence that
   develops over the run (both agree exactly at t=0). So the frozen evidence
   cannot certify how much mass was actually created: between +5.5e-4 and
   +9.2e-4, both monotone, both above the gate in the total-mass reading.
6. **Where it comes from** (my spatial decomposition of the t=0 → t=60 000 mass
   difference): the gas region gains ~+177 (dominated by a *uniform* pocket
   density rise 1.0000 → 1.0042 = +161), the two interface bands lose ~−74.5
   (−0.8% locally, the expected capillary-pressure drop across the menisci), the
   liquid buffers lose ~−21.8, and the near-wall rows lose a little
   (−1.06 in rows y=1,40 vs +71.8 in the interior rows). The redistribution is
   physically sensible and exactly mirror-symmetric; the *net* +70.7 is not
   compensated anywhere, so ~44% of the pocket's compression has no
   corresponding loss elsewhere. This is a numerical non-conservation of the
   frozen solver, not a V2 setup error.
7. **Baseline context.** The same solver, unchanged, in the externally accepted
   V1c episode, produced `closure_rel` (committed
   `results/levelc_v1c/summary.json`, reported-not-gated there):
   4.905e-4 (dyn_h40_s, 36 500 steps), 5.299e-4 (dyn_h26_s, 40 250),
   5.952e-4 (dyn_h26_2L, 60 000), 6.821e-4 (dyn_h40_2L, 60 000) — per-step
   relative rates 1.14e-8 … 1.34e-8. V2's rates: 9.11e-9/step (sentinel total),
   1.12e-8/step (sentinel blue), 1.53e-8/step (population). Two consequences
   matter: (a) the drift is *not* V2-specific — it is a per-step property of the
   solver at the same order in every run; and (b) the V2 gate of 5e-4 is
   **below the accepted baseline's own band**, since two accepted V1c runs
   (5.95e-4, 6.82e-4) exceed it.

Judgment. The contract sentence I was instructed to apply is: *"If this
threshold is exceeded monotonically or by an order-one amount, the reviewer must
treat it as blocking."* The condition is met on the evidence, under every
reading I can construct: the gate quantity is exceeded, the exceedance is
strictly monotone through and beyond the crossing, it does not saturate (the
population channel's rate is constant), and the independent channel check makes
the non-conservation *larger*, not smaller, than the gated quantity. The
"order-one amount" limb is not met (0.67× the gate, not ~10×), but the
"monotonically" limb is, so I must treat it as blocking. I therefore **cannot
return PASS**.

Which blocking verdict? I judge **HUMAN_REQUIRED**, not CHANGES_REQUESTED:

- `CHANGES_REQUESTED` is reserved for "finite implementation/evidence defects
  that do not change the scientific problem". The g6 blocker is not such a
  defect. The driver measures and reports the drift faithfully; the drift is
  produced by `lbm_solver_cg3d.py`, which contract §3 forbids changing and which
  is byte-identical to the V1c-accepted solver. A re-run reproduces it by
  construction (systematic, not stochastic), and no edit to any V2 product file
  can bring ε_b below 5e-4 at 60 000 steps.
- Contract §20 lists as `HUMAN_REQUIRED` triggers: "solver modification would
  be required" and, in effect, deciding to change the problem/gate. Both apply:
  reaching the gate as written needs the per-step non-conservation to drop by
  ≥1.4× (sentinel) or ≥1.8× (population) — a solver-level conservation work
  item; or the §10 gate itself must be re-scoped, which is a contract-owner
  decision precisely because the accepted V1c baseline also exceeds it. The
  reviewer cannot make either call, and a rerun cannot dissolve it.

I want to be explicit about what is *not* in question: every gate that bears on
the V2 scientific question (g1–g5, g7–g10 and the conditional rate diagnostic,
plus the interaction event handling) passes, several of them by 3–4 orders of
margin, and I reproduced them independently rather than accepting assertions.
The blocker is a single, small, systematic solver-level conservation floor that
the project's own gate is calibrated below.

## 7. Interpretation boundary (the five required answers)

1. **Is bilateral symmetry preserved?** Yes. The t=0 fields are exactly
   mirror-symmetric (zero error on 76 800 fluid nodes) and stay so to
   ≤0.0013 lu in front position (RMS 0.0010 lu), ≤5.9e-3 locally in ψ
   (370 of 76 800 nodes above 1e-3, none above 1e-2 — I checked this directly,
   so the reported mean `E_ψ` is not hiding local asymmetry), with exactly
   mirror-paired mixed envelopes at every sample and front retreats agreeing to
   0.11–0.26% relative. The single blemish is a 12-node gas-count flicker in
   the buffer regions at t=32 000 (288 vs 276), which is a thresholded integer
   count, not a field asymmetry, and has no counterpart in `e_x`, `E_ψ` or
   `env`. No evidence of symmetry breaking.
2. **Does the central trapped gas remain numerically coherent?** Yes. One
   cluster at every one of the 60 committed samples and at the three
   independently re-labelled snapshots; `largest == V_bin` always; no
   fragmentation, no disappearance; minimum ψ inside the largest cluster stays
   positive; the pocket's mean density and the bulk-gas column count vary
   smoothly and by <0.5%.
3. **Is any gas-volume reduction explainable inside the weakly compressible
   model without leaving the operational density range?** There is no *net*
   reduction. Relative to the programmed IC the binary gas volume returns to
   exactly 38 400; the only reduction is a −96-node (−0.25%) dip at t=1 000
   during the sharp-IC interface relaxation, which fully recovers by t=33 000;
   the continuous volume ends 0.066% below its initial value. The pocket
   *compresses* instead: mean ρ 1.000000 → 1.004246 (+0.42% relative to the
   true t=0 state — note the report's "+0.06%" uses the t=1 000 sample as
   baseline, N2), i.e. under p = ρ/3 a numerical pressure rise of ≈1.4e-3,
   the same order as the capillary pressure the two menisci can supply
   (3·P_c ≈ 7.2e-3 in ρ units). No density outside the operational range is
   required, and I explicitly do **not** read this as validated real-air
   compression — it is a weak-compressibility diagnostic only.
4. **Did interface overlap occur? If yes, was it resolved reproducibly?** No.
   The two fronts retreated ~0.117 lu in the first 250 steps and ~0.838 lu in
   total, then stalled; `G_bulk` stayed at 146 bulk-gas columns (envelope span
   79→246) for all 60 samples, never reaching 0, so `INTERACTION_ONSET` is
   genuinely `NOT_REACHED` — an outcome the contract explicitly permits and
   which I do not treat as a failure. There is therefore no overlap/coalescence
   event to resolve; gate 9 is vacuously satisfied.
5. **Is there any evidence requiring a solver change before V3?** Yes, exactly
   one: the closed-system mass non-conservation described in §6.3 — ~1.0–1.5e-8
   relative per step, monotone, which (i) fails the project's 5e-4 colour-mass
   gate at 60 000 steps, (ii) is larger in the population channel (+9.2e-4),
   (iii) leaves the solver's two bookkeeping channels disagreeing by 3.7e-4
   relative about the size of the effect, and (iv) is shared with the accepted
   V1c baseline. V3 (porous media) will have far more solid/interface area and
   likely much longer runs, so this floor must be settled deliberately — by
   re-scoping the gate and/or by a solver-level conservation work item —
   before it becomes the dominant uncertainty of a porous-media result. No
   other solver change is justified: no NaN, no velocity-cap or density-range
   excursion, no symmetry or topology failure, no spurious discontinuity.

## 8. Provenance assessment

Accepted (verified by re-hashing and by reading the producer):

- exact candidate SHA, clean worktree, correct branch, correct base ancestry;
- 19/19 MANIFEST artifact hashes match the files on disk, including the three
  `fields_*.npz` I used for the strongest checks, so my recomputations are bound
  to the candidate's own products;
- `producer_sha256` matches the committed driver byte-for-byte;
- `run_head 052ab97` is an ancestor of the candidate and the driver in the
  candidate is byte-identical to it;
- command, interpreter, console log and `exit 0` are recorded; `report.json`
  carries layout, `prov`, `equil` and per-gate blocks; every CSV has a
  `.prov.json` sidecar with its own SHA256;
- `report.json::prov.worktree_dirty = true` is expected and benign: the results
  tree was being regenerated during the run; the *source* is pinned by
  `producer_sha256`.

Weaknesses (non-blocking, listed in §10):

- `EXECUTION_REPORT.md` names a producer revision (`7a16bd7`) that does not
  exist in the repository (N6);
- the `.prov.json` sidecars and `report.json::prov` carry
  `finished_at = null, exit_code = null` because they are written before the run
  ends; the exit-code binding lives only in `MANIFEST.json` +
  `logs/v2_primary.exit` (N7);
- the field snapshots are git-ignored, so a fresh clone cannot re-run the 3-D
  topology/symmetry checks even though `MANIFEST.json` binds them (N8);
- the two aborted attempts' logs were overwritten; their causes and values
  survive only as prose in `EXECUTION_REPORT.md`/`MANIFEST.json` (declared
  honestly, but not independently auditable);
- the one value in the V1c-based justification that does not reproduce
  (`static_h40 0.8907` vs actual `0.888573`) (N4).

No evidence of fabricated, copied or mismatched results was found: every
headline number I could recompute either matched exactly or its discrepancy is
fully explained by a named defect below.

## 9. Blocking findings

**B1 (the decision driver) — g6 colour-mass gate exceeded monotonically.**
`max_t(ε_b) = 6.730e-4 > 5e-4`, strictly increasing, above the gate from
t=35 000 to the end of the run; the independent population-channel measurement
shows a *larger* monotone drift (Σ_fluid ρ: +9.21e-4, constant 1.53e-8/step),
and the two channels disagree by 3.7e-4 relative about the size of the
non-conservation. Per contract §10 this must be treated as blocking, and per
§20 the resolution requires either a solver modification or a contract-level
change of the conservation gate — neither of which is within the reviewer's
authority or reachable by editing V2 product files. Note for the human: the same
gate as written is exceeded by the externally accepted V1c baseline (5.95e-4,
6.82e-4 over 60 000 steps), so this is at least as much a gate-calibration
question as a solver-quality question.

**B2 (requires ratification, not a standalone block) — declared scope change of
hard gate g3.** g3 passes only under the executor-declared bulk-node
(`|ψ| > 0.9`) semantics; under any literal all-fluid reading it fails
(t>5 000: min 0.888446 in 16 samples; even with the repo's 20 000-step
equilibration default, 9 samples at min 0.889895). My substantive audit supports
the narrowing — the dips are interface-localized (ψ≈0 nodes), deeper dips exist
in accepted V1c runs (0.880460 dyn_h26_s, 0.887740 dyn_h40_s, 0.888573
static_h40, 0.893018 static_h26), the pocket stays inside [0.935, 1.008], the
contract's own stop condition in §11 is keyed to the *pocket*, and the
excursion decays back above 0.89 by t=60 000 — but a hard gate's scope is the
contract owner's to change, so this must be ratified explicitly (or the gate
must be restated) before it can be cited as a V2 PASS. I would not have blocked
on B2 alone.

## 10. Non-blocking findings

- **N1 — `d(t)` coordinate defect in the driver (product code bug).**
  `d = 0.5·((x_left − x_left0) + (x_right_star − x_right0))` mixes the mirrored
  right coordinate with the unmirrored initial right front, so the committed
  `d` column and `report.json::max_d/final_d` are offset by exactly −80
  (max_d = −80.117, final_d = −80.838) while the report text quotes the correct
  −0.84 lu. Gate g5 is unaffected *here* only because d < 0 makes
  `max(2, 0.02 d)` collapse to the 2-lu floor either way; for a future run in
  which the fronts advance, the 0.02·d term would be silently disabled. Fix the
  identity (use the mirrored initial coordinate) and regenerate
  `front_series.csv`/`report.json` whenever the candidate is next touched.
- **N2 — t=1 000 used as "initial" in three headline diagnostics**, although the
  run itself computed and stored the t=0 state: binary gas volume
  ("38 304 → 38 400, +0.25%" — true: 38 400 → 38 304 → 38 400, i.e. a transient
  dip that fully recovers), pocket mean ρ ("+0.06% compression" — true
  +0.42% from the programmed IC), and `G_bulk` ("150 → 146" — true: 160 at t=0
  post-init, 146 from t=1 000 onwards; the value 150 appears nowhere in the
  committed evidence and is not reproducible from the committed fields or
  series).
- **N3 — "buffer gas occupancy 288 nodes on EACH side, exactly equal"** is true
  in 59 of 60 samples; at t=32 000 the counts are 288 vs 276, and earlier
  samples carry 240/264/276. The claim should be restated as "equal except one
  12-node thresholded count flicker (0.06% of the buffer region)".
- **N4 — V1c baseline value `static_h40 = 0.8907` does not reproduce**; the V1c
  run field gives 0.888573. The other two cited values reproduce exactly
  (dyn_h40_s 0.887740, static_h26 0.893018), and the correction makes the
  argument stronger, but the number in the report and in the review request
  should be fixed.
- **N5 — "≈7e-9 per-step relative"** in the g6 decomposition does not reproduce
  under any obvious normalisation (measured ε_b: 1.12e-8/step; sentinel total:
  9.11e-9/step; population channel: 1.53e-8/step).
- **N6 — `EXECUTION_REPORT.md` names producer revision `7a16bd7`**, which does
  not exist in the repository; the actual producer is `052ab97` (as
  `MANIFEST.json`, `report.json::prov` and `PROVENANCE.md` correctly state).
- **N7 — provenance sidecars carry null `finished_at`/`exit_code`** (written
  before completion); exit code is bound only through `MANIFEST.json` and
  `logs/v2_primary.exit`.
- **N8 — the `fields_*.npz` snapshots are git-ignored**, so only their hashes
  (in the committed `MANIFEST.json`) are durable; the committed slice CSVs
  satisfy contract §17, but a future 3-D topology re-check would need the npz
  restored or regenerated.
- **N9 — no recorded outcome for `tests/v2_unit_check.py`.** I re-ran it myself
  (`PYTHONDONTWRITEBYTECODE=1 python tests/v2_unit_check.py`, exit 0,
  "ALL UNIT CHECKS PASS"; worktree still clean afterwards). The checks exercise
  the production functions (`build`, `verify_symmetry`, `front_positions`,
  `gap_metrics`, `label_gas`) on synthetic masks, which satisfies the project's
  "validation must use the production path" rule as a thin wrapper; the
  outcome should be committed with the next evidence update.
- **N10 — no local-max field-symmetry diagnostic in the committed evidence.**
  Contract §8.2 warns against field averaging hiding local asymmetry. I supplied
  the missing check myself (max |Δψ| = 5.9e-3, all above 1e-3 confined to 370
  interface-adjacent nodes, none above 1e-2); it would be worth committing with
  the V2 update.
- **N11 — optional items not taken** (both legitimate under the contract): the
  near-contact stress probe (§16, NOT RUN — acceptable, an explicit "NOT_RUN"
  statement would be clearer than silence), and no formal quasi-steady window
  (§12, "may"): supported by my numbers (G_bulk constant, front and velocity
  residuals ≤ 5e-4 lu/1 000 steps) but not declared, so no convergence claim is
  made — correct, and no convergence is claimed anywhere.

## 11. Living technical document

Contract §19 / my reviewer contract require the V2 update to
`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`.
Status on the control checkout (`cg3d-graphite`, branch
`agent-dev/bilateral-episode-v0.1`, commit `4f44441`): the document exists
(1 444 lines) and contains §20.9 "V1c external scientific review — PASS" and the
pre-V2 authorization text (§ "V2 前必须修正的两个旧 contract 假设", §22 status),
but **there is no V2 section**: no candidate SHA, no V2 result figures
(`docs/research/bilateral_imbibition/figures/` holds V1c figures plus an
unversioned `v2_make_figs.py` added after the candidate commit, with no V2 SVG
output yet), no front/mirror-error figure, no pocket/gas-gap figure, no
topology/event or mass/stability table, no V1c-comparison section. This matches
§19's sequencing (the document is updated *after* the fresh reviewer finishes),
so it is not a candidate defect — but it is an **outstanding mandatory
deliverable**: V2 is incomplete until it is produced, and it must carry the
corrected numbers from this review (t=0 baselines, the g6 classification, the
gate-ratification outcome) and the candidate SHA `5e679d8…` in every figure
caption.

## 12. Decision

Decision: HUMAN_REQUIRED

## 13. Rationale

Every gate that bears on the V2 scientific question passes, and I reproduced
them independently rather than accepting the executor's numbers: the initial
condition is exactly mirror-symmetric and stays so to ≤0.0013 lu in front
position and ≤5.9e-3 locally in ψ; the central gas is trapped at t=0 as exactly
one 38 400-node 6-neighbour cluster (z-periodic merge only) and never fragments,
disappears or splits (one cluster in all 60 samples, `largest == V_bin`); no
NaN/Inf, `u_max` 0.0255 vs a 0.12 cap; bulk densities in range; the interaction
event is genuinely `NOT_REACHED` (bulk-gas columns never vanish) which the
contract explicitly permits, and the conditional rate diagnostic is
`NOT_DISCRIMINATING` robustly (no window could have reached the 2-lu trigger),
with the available displacement symmetry at 0.11–0.26% versus a 5% tolerance.
The measured physics is also self-consistent: the two fronts stall after
forming static menisci, the pocket compresses by 0.4% (the order of magnitude
the capillary pressure can supply), and the interfaces, envelope positions and
buffer occupancies stay mirror-paired.

Nevertheless I cannot return PASS. Contract §10 states that a monotone
exceedance of the 5e-4 colour-mass gate must be treated as blocking, and the
exceedance is monotone on the evidence: ε_b reaches 6.730e-4, strictly
increasing, from t=35 000 onward. I also found, independently of the executor,
that the drift is *at least* as large as the gate suggests: the total fluid mass
grows monotonically by +9.21e-4 (Σ_fluid ρ, hash-bound snapshots, constant rate
1.53e-8/step), and the solver's two bookkeeping channels disagree by 3.7e-4
relative about how much mass was created — so the conservation status cannot be
certified from the frozen evidence, and the "small bounded floor" reading is not
established. The physics conclusions stand; the missing certification does not.

HUMAN_REQUIRED rather than CHANGES_REQUESTED because the blocker is not a finite
implementation or evidence defect that a V2-side edit could fix: the drift is
produced by the frozen, V1c-accepted solver (`lbm_solver_cg3d.py` may not be
changed under §3), it reproduces deterministically, and the gate as written is
already exceeded by the externally accepted V1c runs themselves (5.95e-4 and
6.82e-4 over 60 000 steps). Reaching the gate requires either reducing the
solver's per-step non-conservation by ≥1.4–1.8× (a solver-level conservation
work item — an explicit §20 `HUMAN_REQUIRED` trigger) or re-scoping §10 (a
contract-owner decision the reviewer has no authority to make). A second,
smaller human item accompanies it: the bulk-node reinterpretation of hard gate
g3 is *necessary* for g3 to pass and is substantively well founded on the V1c
evidence I re-verified, but a hard gate's scope is the contract owner's to
change, not the executor's to declare.

## 14. Exact next action

1. **Contract owner / controller decision on §10 (blocking).** Choose one:
   - **(a) Re-scope the conservation gate** to a form the established solver
     satisfies, keeping the 5e-4 per-colour absolute value as the V3 target.
     Any of these is calibrated by the existing evidence: a per-step relative
     rate bound of 2e-8/step (all five frozen-solver runs meet this: V1c
     9.9e-9–1.34e-8; V2 sentinel total 9.11e-9, blue 1.12e-8, population
     1.53e-8), and/or a total-mass-normalised bound (V2 total +5.47e-4 ≤ 1e-3
     over 60 000 steps). If chosen, record the amendment in the episode
     contract, then re-issue the V2 decision as PASS against the amended gate.
   - **(b) Authorise a solver-level conservation work item before V3** and
     re-certify g6 afterwards. The diagnosis should start from the one
     measurement that does not yet exist in the evidence: per-step
     `Σ_fluid ρ` versus `Σ_fluid (ρ_r + ρ_b)` (they agree at t=0 and differ by
     28.7 by t=60 000), plus the mass budget of the wall-adjacent rows and the
     two interface bands (interior rows gain +71.8, rows y=1/40 lose −1.06,
     interface bands lose −74.5, pocket gains +161). Likely candidates are the
     wall bounce-back/Guo-forcing bookkeeping and the recoloring step's effect
     on `ρ_r + ρ_b`.
2. **Ratify or restate gate g3's scope** (bulk `|ψ| > 0.9` versus all-fluid
   nodes), and either way keep the all-fluid extremes reported per sample. My
   audit supports the bulk-node target; the record needs the contract owner's
   signature, not the executor's declaration.
3. **Correct the finite evidence/claim defects (N1–N7, N9) whenever the
   candidate is next touched**: fix the `d` identity (mirrored initial
   coordinate) and regenerate `front_series.csv`/`report.json`; restate the
   t=0 baselines for binary volume, pocket ρ and `G_bulk` (160 → 146, not
   150 → 146); correct the "exactly equal" buffer-occupancy claim; replace the
   V1c `static_h40 = 0.8907` with the reproduced 0.888573; replace producer
   revision `7a16bd7` with `052ab97`; recompute or drop the "7e-9/step" figure;
   commit the unit-check outcome; and add the local-max field-symmetry
   diagnostic. None of these change the scientific problem or the V2
   conclusions, and none of them can be used to make g6 pass.
4. **Preserve the V2 physics conclusions**: symmetry, topology, trapping,
   interaction `NOT_REACHED`, and the stability metrics are independently
   confirmed above and should be quoted with the t=0 baselines and the
   gate-scope caveats attached.
5. **Produce the §19 technical-document update** on the control branch after the
   decision, with the candidate SHA `5e679d8d99d338f9ab28565c636f021a0f9211b2`
   in every figure caption, the corrected numbers from this review, the
   SOLVER/BC/VAL/DIAG/HARNESS classification (expected: no SOLVER/BC change; V2
   adds VAL + DIAG + HARNESS paths), and the explicit statement of the §10/g3
   ratification outcome. V2 remains incomplete without it.
6. **Stop there.** Do not start V3, graphite, separator, gap or PCS work
   (contract §21); this review does not authorise them, and a PASS would not
   have either.
