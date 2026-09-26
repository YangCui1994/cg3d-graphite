stage: V1B
attempt: 1
candidate: a9c6db87da2eeb3572607152391fe6863394ebee
execution_report: D:/2026_agent_work/01_GLM_LBM3D_porous_media/cg3d-episode-worktrees/BI-V1B-DIAGNOSTIC-001/results/levelc_v1b/EXECUTION_REPORT.md

# REVIEW — BI-V1B-DIAGNOSTIC-001 (V1b diagnostic)

## Review Mode

`FRESH_SESSION` (no prior context on this task). Review performed read-only on
the frozen candidate. No product file, commit, branch, or executor artifact was
modified; only this file was written. The executor conversation transcript was
neither read nor requested. No GPU rerun was performed (optional per contract;
all gate-relevant numbers were recomputed from committed CSV/JSON and were
internally consistent).

## Binding

| Check | Result | Evidence |
|---|---|---|
| HEAD equals candidate SHA | PASS | `git -C <worktree> rev-parse HEAD` = `a9c6db87da2eeb3572607152391fe6863394ebee` |
| Product worktree clean | PASS | `git status --porcelain` empty (0 lines) |
| Descends from `e9540bcadb86257c70b805afc98f2eec9626c64e` | PASS | `git merge-base --is-ancestor e9540bca HEAD` → true; log `e9540bc → cd5986b → da9a13d → a9c6db8` |
| No solver source changed | PASS | diff vs base touches only `tests/levelc_v1b.py` + `results/levelc_v1b/**`; `lbm_solver_cg3d.py`, `cg3d/**`, V0 tests, V1 driver/results untouched |
| Only V1b-authorized files changed | PASS | 54 files, exactly the set claimed in `REVIEW_REQUEST.md` |
| Producer binding is real (not asserted) | PASS | sha256 of committed `tests/levelc_v1b.py` = `f66aabb236281b00996b7894f7e8e06f27425ef67e3b2a624b2c676be5706f46`, identical to every recorded `producer_sha256`; all 40 artifact sha256 in `MANIFEST.json` re-verified against the bytes on disk (0 mismatches) |

Candidate is bound. All further statements below were produced from the frozen
candidate's committed artifacts.

## Changed-file scope

- `tests/levelc_v1b.py` (774 lines, new V1b driver, committed before the runs
  at `cd5986b` and refined at `da9a13d`, byte-identical in the candidate).
- `results/levelc_v1b/**` (53 files: per-run `report.json`, `front.csv`,
  `probes.csv`, `axial_*.csv`, `static_series.csv`, `.prov.json` sidecars,
  `logs/*.log|*.exit`, `summary.json`, `pressure_budget.csv`, `gates.csv`,
  `MANIFEST.json`, `EXECUTION_REPORT.md`, `PROVENANCE.md`).
- No figures committed (so the V1 figure/producer-drift gap is closed by
  omission, as contract §10 permits).
- `*.npz` final-field dumps exist on disk but are **not** committed
  (`.gitignore:9` = `*.npz`). Nothing in this review depends on them.

Contract §4 (allowed changes) and the AGENTS.md scientific-change guardrails
are respected: no solver file, no existing V1/V0 artifact, no
`.agent/episodes/**/runner/episode_runner.py` was modified.

## Gate table (independent verification)

Verdicts below are mine, from recomputation, not from `gates.csv`.

| Gate (contract) | h=26 | h=40 | h=26 2L | My verdict | Basis |
|---|---|---|---|---|---|
| g1 no NaN/Inf | TRUE | TRUE | TRUE | PASS | `nan_at=None`; logs clean; probe series finite |
| g2 u_max ≤ 0.12 | TRUE (0.0235) | TRUE (0.0236) | TRUE (0.0240) | PASS (not discriminating) | reproduced; spurious-current floor is 0.021–0.024, i.e. 3–5× the physical front speed |
| g3 zero imposed ΔP | TRUE (dev 0.0) | TRUE (0.0) | TRUE (0.0) | PASS | reservoir ρ deviation exactly 0.0 |
| g4 monotonic post-transient | TRUE | TRUE | TRUE | PASS | recomputed on declared window |
| g5 window valid (no silent `argmax`) | TRUE | TRUE | TRUE | PASS | `levelc_v1b.py:508-520` fails explicitly (`len(win)<20`); windows [44,159] / [62,144] / [71,239] |
| g6 R²[x,t] ≥ 0.995 | TRUE | TRUE | TRUE | PASS | I re-fitted `front.csv`: 0.99999796 / 0.99999958 / 0.99999716 — exact match |
| g7 \|V/V_hyd−1\| ≤ 0.10 | **FALSE** (0.738) | **FALSE** (0.562) | **FALSE** (0.836) | **FAIL (robust)** | 0.68–0.73 / 0.51–0.56 / 0.83–0.85 across all band choices; 0.68 / 0.44 / 0.81 even if driven by `Pc_static` |
| g8 plane-Poiseuille ≤ 10% | **FALSE** (gas 0.783) | **FALSE** (gas 0.735) | **FALSE** (gas 0.721) | **FAIL as measured; attribution unresolved** | liquid leg 1.05/0.97/1.02 passes; gas leg is zone-dependent (see below) |
| g9 colour-mass closure | not tabulated | not tabulated | not tabulated | effectively PASS, label defect | closure/transferred mass 2.8e-4 / 3.3e-4 / 7.0e-4 — no order-one leakage |
| static scaling ≤ 10% rel | **FALSE** (11.53%) | — | — | **FAIL (robust)** | 11.53% committed band; 12.4% with a tail-free gas band |

## Independent recalculations from committed artifacts

| Quantity | Executor | My recomputation | Agreement |
|---|---|---|---|
| `V_meas` h26 / h40 / 2L | 4.974326e-3 / 5.587780e-3 / 3.000209e-3 | identical (linear fit on `front.csv` over the declared window rows) | exact |
| `R²[x,t]` | 0.99999796 / 0.99999958 / 0.99999716 | identical | exact |
| `V_meas_secondary` vs primary | 0.04% apart | reproduced | consistent |
| `Pc_dynamic` at mid-window state (h26) | 2.949994e-3 (probe row) | 2.949994e-3 from `axial_mid.csv` with the declared band rule | exact |
| `Pc_dynamic` band sensitivity | not reported | h26 2.94–3.11e-3 (±3%), h40 1.81–1.97e-3 (±4%), 2L 2.97–3.05e-3 (±1.5%) | stable |
| Pressure-budget closure | implied by construction | verified as an exact identity at the h26 mid state: jumps (1.927e-4+4.571e-4) + ∫|dp/dx| over both slit spans = 2.9500e-3 = `Pc_dynamic` (0.00% residual) | closes |
| `Pc_static` / `C_static` | 3.131648e-3 / 0.6705 (h26); 2.284527e-3 / 0.7525 (h40) | reproduced from `axial_static.csv`; 0.6724 / 0.7616 with a gas band that excludes the interface tail (`x ≥ 130`) | reproduced |
| Poiseuille `G = 12μV/h²` | liq 1.05/0.97/1.02, gas 0.78/0.74/0.72 | reproduced; **but** the gas leg measured 40–73 lu behind the meniscus reads |g| ≈ 1.04·G at the h26 mid state | zone-dependent |
| `V_hyd` | 6.742e-3 / 9.942e-3 / 3.589e-3 | reproduced with `L_hyd` = 241/241/477; sensitivity to the alternative `L_hyd` definition (243 = between pinned reservoir edges) is +0.8%, immaterial | exact |
| Mass closure | 2.8e-4 (h26) | 2.8e-4 / 3.3e-4 / 7.0e-4 | exact |
| `L_eq` | 117.7 (L_eq/L1 = 0.488) | contract formula reproduced exactly; **Pc-aware per-run estimate**: `L_eff = Pc h²/(12μV)` = 326.6 (L=241) and 570.6 (L=477) → `L_eq` = 85.7 and 93.6 lu (0.36–0.39·L1, consistent within 9%); h=40: `L_eff` = 428.8 → `L_eq` = 187.8 lu (0.78·L1) | see assessment |
| Boundary masks / indices | layout JSON | verified in `levelc_v1b.py:96-99,155-168,312-326`: wall [0,3) · liq res [3,11) · mem_in x=11 · buffer [12,14) · slit [14,14+L) · buffer [14+L,16+L) · mem_out x=16+L · gas res [17+L,25+L) · wall [25+L,28+L); no reservoir/membrane overlap; h26/h40 layouts identical except `ny` | PASS |

Note on the L_eq discrepancy: the contract formula assumes both lengths share the
same `Pc`. The measured `Pc_dynamic` differs by 5.4% between the two h=26 runs
(2.884e-3 vs 3.039e-3), so the Pc-blind formula mixes a capillary change into the
resistance inference. The Pc-aware estimate is the better diagnostic; both are
reported, and both say the same thing qualitatively (see below).

## Boundary-resistance assessment

Layout quality (V1b-A) is genuinely improved and meets contract §5: uniform
cross-section corridor, membranes separated from the active slit by 2-lu open
buffers, membranes disjoint from both pinned masks, both reservoirs pinned at
ρ = 1 (imposed ΔP exactly zero), identical x-index layout for both heights.

What the data say:

1. The front is now materially faster than in V1 (h=26: `V_meas` 3.86e-3 → 4.97e-3,
   +29%) and the residual fixed extra length roughly halved (~190 lu → ~86–94 lu
   by the Pc-aware estimate, ~118 lu by the contract formula). This is a real,
   measurable improvement.
2. The residual has **not** been removed and is still order-one:
   `L_eq/L1` = 0.49 (contract formula) / 0.36–0.39 (Pc-aware) at h=26.
3. A localized pressure discontinuity still exists at both open-boundary
   transitions. At the h=26 mid-window state: the pinned liquid plenum sits at
   exactly p = 1/3 while the first buffer column (x=12) reads 0.3329086 — a
   4.25e-4 drop within ~2 lu, equivalent to ~48 lu of Poiseuille length; at the
   outlet x=249 reads 0.3337248, i.e. 3.9e-4 **above** the pinned gas plenum,
   with the drop occurring across ~4 lu (buffer + membrane). Window medians of
   the two jumps are 0.33·Pc (h26), 0.51·Pc (h40), 0.32·Pc (2L).
   These are measured, not extrapolated, values.
4. The jumps cannot be split into "membrane resistance" vs "pinning-edge
   entrance effect" in this layout, because the contract itself places the
   membrane immediately adjacent to the pinned mask (x=10 pinned, x=11
   membrane). That is a diagnostic limitation to carry forward, not an executor
   error.
5. **Decisive scaling problem**: with the identical x-geometry at h=40 the
   Pc-aware residual is ~188 lu — i.e. 0.78·L1, exactly the magnitude of the old
   V1 signature — while at h=26 it is ~90 lu. A fixed geometric boundary feature
   cannot double when only the slit height changes. So at least part of the
   residual resistance is proportional to `h` (meniscus/interface-localized),
   not to the boundary layout.

**Answer to reviewer-contract question 1:** the old ~190-lu signature has been
materially reduced at h=26 (roughly halved), not reduced at h=40, and remains
order-one at both heights. It is not yet separable from an h-proportional
(meniscus-localized) contribution.

## Static / dynamic wetting assessment

Static calibration (V1b-B) is the cleanest measurement in this bundle and I
consider it trustworthy:

- liquid bulk flat to 1.7e-6 (h26) / 1.4e-6 (h40), gas bulk plateau flat to
  ~1e-8 once the interface tail is excluded;
- `Pc` is time-stationary (std 8.0e-8 / 1.1e-7 over the last 20 blocks; relative
  drift 6.3e-5 / 4.3e-5 over the last 10 blocks — 20× inside the driver's own
  1e-3 tolerance). The run reports `steps_cap` only because the *kinetic*
  criterion (`umax < 5e-6`) is unattainable: `umax` sits on the colour-gradient
  spurious-current floor (0.0219–0.0220 h26, 0.0195–0.0252 h40) and does not
  decay. Process completion is honestly *not* equated with convergence; the
  pressure measurement is nevertheless stationary and I verified it
  independently.

Results:

- `C_static` = `Pc_static·h/(2σ)`: **0.672** (h26, θ_slit = 47.8°) and **0.762**
  (h40, θ_slit = 40.4°) with a tail-free gas band; 0.670/0.752 (θ = 47.9°/41.2°)
  with the committed band.
- **Static scaling gate: FAIL, and robustly so** — 11.53% as committed, 12.4%
  with a tail-free band (I initially suspected a band artifact, because the
  committed gas band starts only ~11–12 lu from the meniscus crossing and thus
  catches the interface tail, whose depth is resolution-dependent: −4.3e-5 (h26)
  vs −1.19e-4 (h40) at +13 lu. Correcting that does **not** fix the gate; the
  difference lives in the bulk plateau values themselves.)
- **The droplet registry does not transfer to the slit.** cos 30° = 0.866
  versus the measured slit values 0.672 / 0.762 — i.e. the slit angle is 18°/10°
  larger than the registry at h=26/h=40.
- The measured interface is **not thin relative to the slit**: core-to-core the
  diffuse interface spans ~11–17 lu in both static and dynamic states, which is
  42–65% of h=26 and 28–43% of h=40. A naive fit `C(h) = cosθ∞ − a/h` to the two
  points returns cosθ∞ ≈ 0.42 (θ∞ ≈ 65°), which is physically implausible — i.e.
  the two-point data do not support any clean resolution extrapolation.

Dynamic capillary pressure:

- `Pc_dynamic` (far-field extrapolation) = 2.884e-3 (h26, C_dyn = 0.617,
  θ_app = 51.9°) and 1.797e-3 (h40, C_dyn = 0.592, θ_app = 53.7°); Ca = 8.2e-3 /
  9.2e-3. With a tail-free band: 3.109e-3 (C_dyn = 0.666) and 1.969e-3
  (C_dyn = 0.648).
- `Pc_dynamic/Pc_static` = 0.92 (h26) / 0.79 (h40) as committed, or 0.99 / 0.85
  with tail-free bands. The committed value is biased low because the gas
  measurement band (12–45 lu behind the meniscus) overlaps the interface
  distortion zone. Note the consequence: the **dynamic** coefficient is nearly
  height-independent (C_dyn 0.617 vs 0.592, 3–4% apart, under either band
  choice), while the **static** one is not (12% apart). So the headline
  "dynamic deficit" is dominated by the static resolution dependence, not by a
  demonstrated moving-meniscus effect.

**Answers to reviewer-contract questions 2–5:**

2. Same-slit static transfer h26 → h40: **NO** — 12% relative difference,
   outside the 10% engineering gate, and both values far from the registry.
3. Can the observed front speed be explained by independently measured
   `Pc_dynamic` plus slit hydraulic resistance? **NO, robustly** — `V_meas/V_hyd`
   = 0.738/0.562/0.836 as committed, 0.68–0.73/0.51–0.56/0.83–0.85 across every
   band choice I tried, and 0.68/0.44/0.81 even when the driving pressure is
   taken as the *static* same-slit value. The front is 16–56% too slow in all
   consistent readings.
4. Static vs dynamic capillary pressure: `Pc_dynamic` is 8–9% lower than the
   tail-free `Pc_dynamic` estimate should be (measurement-zone bias), and
   `Pc_dyn/Pc_static` is 0.92/0.79 as committed vs 0.99/0.85 tail-free; the
   residual difference is confounded by the static resolution dependence listed
   above.
5. Blocking numerical inconsistency or declared moving-contact-line
   characteristic? **Neither is established, and this is the core unresolved
   finding.** The gas-leg gradient deficit (g8) looks largely like a
   measurement-zone artifact — 40–73 lu behind the meniscus the gas gradient
   reads ≈1.04·G, i.e. plane-Poiseuille within ~4%. The velocity deficit (g7)
   survives every measurement and definition choice I tested, cannot be absorbed
   into the boundary accounting (the budget closes exactly), and its equivalent
   length scales with `h`. V1b has *localized* the deficit but has not explained
   it, and the candidate explanations (residual boundary forcing at membrane +
   pinning edge, moving-contact-line/dynamic-wetting extra dissipation,
   dissipation of the spurious currents whose amplitude is 0.59–1.34·`V_meas`,
   or an effective viscosity different from μ = νρ₀ = 0.1) cannot be separated
   from the current evidence without new scientific assumptions or solver work —
   both outside V1b's frozen scope.

## Provenance assessment

Sound, with stated defects that do not affect the numbers:

- Producer binding is real and independently verified: committed
  `tests/levelc_v1b.py` sha256 equals every recorded
  `producer_sha256`; all 40 artifact hashes in `MANIFEST.json` match the bytes.
- Console logs and shell exit codes exist for all five primary runs
  (`logs/*.log`, `logs/*.exit` = 0, mirrored in `MANIFEST.json`).
- No figures committed → no figure-from-wrong-revision exposure.
- Remaining defects are listed under non-blocking findings N1–N4 below.

## Blocking findings

- **B1 — g7 fails and no finite measurement/implementation correction closes it.**
  `V_meas/V_hyd` = 0.738 / 0.562 / 0.836 (committed) and 0.68–0.73 / 0.51–0.56 /
  0.83–0.85 (all band choices; 0.68 / 0.44 / 0.81 with `Pc_static`). Contract
  §12's "dynamic hydraulic consistency fails without a finite
  measurement/implementation correction" is met.
- **B2 — the static scaling gate fails and the registry does not transfer.**
  11.53% (committed) / 12.4% (tail-free) vs a 10% gate; θ_slit = 40–48° vs 30°
  registry. Contract §12's "static slit scaling is inconsistent" is met.
- **B3 — order-one residual extra resistance that scales with slit height.**
  `L_eq/L1` = 0.49 (contract formula) or 0.36–0.39 (Pc-aware) at h=26, but
  **0.78** at h=40 with an identical x-layout, i.e. ≈ the old V1 magnitude. Per
  contract §8 and the V1 external review's stop rule, this blocks any
  recommendation toward V2 on its own.
- **B4 — the hydraulic deficit is not attributed to any physical or numerical
  mechanism.** Candidates (boundary forcing, moving contact line,
  spurious-current dissipation — measured at 0.59–1.34·`V_meas` transverse RMS
  in the interface band, or effective-viscosity deviation) require a
  modeling/numerical decision to separate. Until then, "g7 fails" cannot be
  turned into a scientific statement about the wetting model.
- **B5 — `Pc_dynamic`, and hence `Pc_dynamic/Pc_static` (a contract §9
  deliverable), are biased by 8–9% because the measurement band overlaps the
  interface distortion zone.** This is a finite methodology defect (fix: require
  a minimum clearance in interface widths and report band sensitivity), but it
  must be corrected before any of those numbers are quoted externally. It does
  not rescue g7.

## Non-blocking findings

- **N1 — `PROVENANCE.md` states `worktree_dirty=false`, but every embedded
  `prov` block (five runs and `collect`) records `worktree_dirty=true`.** The
  statement is wrong as written. Mitigating fact: the producer file hash proves
  the driver was byte-identical at every run start, so this is a document error,
  not content drift.
- **N2 — `exit_code` and `finished_at` are `null` in every `report.json` prov
  block and every `.prov.json` sidecar** (they are written before `prov_finish`);
  the real exit codes live only in `logs/*.exit` and
  `MANIFEST.json::shell_exit_code`. Contract §10 asks each primary output to
  carry the exit code; it is accompanied, not embedded.
- **N3 — the candidate SHA is not embedded in any artifact** (only the producer
  revision `da9a13d`). Binding is nevertheless auditable by ancestry +
  byte-identical producer + MANIFEST hashes, all of which I verified.
- **N4 — g9 (colour-mass closure) has no tabulated verdict** in `gates.csv`
  although contract §7 lists it as a hard gate. The numbers are committed and are
  benign (2.8e-4 / 3.3e-4 / 7.0e-4 relative).
- **N5 — the static convergence criterion as coded is unattainable**
  (`umax < 5e-6` against a spurious-current floor of ~0.022), so both static runs
  report `steps_cap` and read as NOT_CONVERGED. The static `Pc` is in fact
  stationary; recommend re-defining the criterion as pressure-stationarity with
  the kinetic floor reported as a diagnostic.
- **N6 — g2's velocity cap (0.12) is not discriminating**: the spurious-current
  floor is 0.021–0.024 in *all* runs, including the static ones. A more useful
  declared metric is the ratio of interface-band transverse RMS velocity to the
  front speed, which is 0.82 (h26), 0.59 (h40), 1.34 (2L) — reported in
  `probes.csv` but not interpreted.
- **N7 — the 2L run has no `axial_mid.csv`** (the front never reached the
  mid-window threshold before the step cap), so its profile evidence exists only
  at the final state; the length scan is therefore slightly asymmetric in
  diagnostic depth. `L_eq` is unaffected.
- **N8 — `EXECUTION_REPORT.md` prints `R2[x,t]` (h26) = 0.99999806**, while
  `report.json` and my recomputation give 0.99999796. Transcription slip; no
  gate impact.
- **N9 — contract §5's "exact x-index layout must be printed and written to
  JSON"**: the JSON layout is complete, but the console print is partial
  (`nx/ny/L_hyd/T_TRANS/x_ic_exit/x_stop` only). Cosmetic.

## Modeling / scientific review

- Fixed assumptions (CapA = 0.06, ν_l = ν_g = 0.1, unit density ratio,
  ψ_solid = −0.68, ψ = ∓1 conventions, z-periodic slit, no imposed ΔP) were
  respected; no parameter was tuned to move a gate — the executor reported the
  failures instead, which I confirmed against the raw data.
- Convergence is established as *stationarity* (static `Pc`), not as process
  completion. Good.
- The scientific claims in `EXECUTION_REPORT.md` are bounded appropriately: the
  gate failures are labelled as measured facts, the residual resistance as
  "preliminary model interpretation", and four unresolved questions are listed.
  I found no overstated claim. One framing nuance: the report's "the fixed extra
  hydraulic resistance halved but did not vanish" is true at h=26 but not at
  h=40, where the residual equals the old V1 magnitude; and "the semi-permeable
  membrane planes appear to carry a finite signature" cannot be separated from
  the pinning-edge entrance effect in this layout.
- New evidence has made part of the V1 external review's framing stale: the
  V1b-A layout change did reduce the boundary signature, and the static slit
  calibration (V1b-B) shows the droplet-derived 30° registry does not describe
  the slit at these resolutions — so the earlier "Pc_dynamic/Pc_nominal = 0.763
  is a possible moving-contact-line effect" reading must now be re-based on the
  *slit* static value, not the registry.
- No previous committed result is invalidated, but no V2/V3 claim may be built
  on the current absolute front speed or on the 30° registry.

## Decision

CHANGES_REQUESTED is unavailable: it covers only finite implementation/evidence
defects that leave scientific assumptions intact, and the dominant findings here
(B1–B4) are not finite. PASS is unavailable: three hard gates fail, two of them
robustly.

HUMAN_REQUIRED

Decision: HUMAN_REQUIRED

## Rationale

1. Three of the contract's own HUMAN_REQUIRED triggers (contract §12) are met on
   independently reproduced evidence: the dynamic hydraulic consistency fails
   (g7: 0.74/0.56/0.84, robust to every Pc, band, L_hyd and window choice I
   tested), the static slit scaling is inconsistent beyond the declared 10%
   gate (11.5% committed / 12.4% tail-free), and the residual boundary
   resistance is order-one (0.49 by the contract formula, 0.36–0.39 Pc-aware at
   h=26, 0.78 at h=40 — the last being the old V1 magnitude).
2. The remaining questions are modeling questions, not measurement questions:
   why the equivalent extra resistance scales with slit height; whether an
   interface whose width is 0.4–0.65 of the slit height can support a
   well-defined static contact angle at all; whether the 30° droplet registry
   should be replaced by the measured slit value (0.67–0.76 → 40–48°) as the
   reference for the next episode; and how to treat the spurious currents
   (0.59–1.34·`V_meas`) that coexist with the moving meniscus. Resolving any of
   these requires a decision the executor is not authorized to make (contract §3
   and §11 forbid changing the physics, geometry height, or thresholds).
3. The V1 external review's stop rule for V1b is therefore engaged: order-one
   boundary/resistance signature remains, and `V_meas` cannot be reconciled with
   the independently measured `Pc_dynamic` plus slit hydraulic resistance. V2
   and V3 must remain unstarted, and this package must go back to external
   scientific review rather than to another executor attempt under the frozen
   V1b contract.
4. Credit where due: the execution is honest and auditable — no tuning, failures
   reported, logs and exit codes preserved, artifacts hash-bound to a
   byte-identical producer, and the L_eq order-one result flagged by the
   executor itself as blocking. The HUMAN_REQUIRED verdict is a statement about
   the science, not about execution quality.

## Exact next action

1. **Stop.** Do not start V2, V3, graphite, interface-gap, separator, or PCS work
   (contract §13). Do not open another executor attempt under the frozen V1b
   contract; the blockers are scientific, not implementation.
2. **Escalate to human/external scientific review** with exactly these decisions
   to make:
   - (a) **Thin-interface validity**: at h=26/40 the diffuse interface spans
     11–17 lu (0.4–0.65·h) and `C_static` is resolution-dependent with no
     sensible two-point extrapolation. Decide whether the next configuration
     must make the interface thin relative to `h` (larger `h`, or a narrower
     interface formulation) or whether the height-dependent coefficients are
     accepted and all conclusions are bounded accordingly.
   - (b) **Wetting reference**: decide whether the next episode measures the
     slit static angle in situ (0.67–0.76, i.e. 40–48°) and retires the
     30° droplet registry as the capillary-pressure reference.
   - (c) **Attribution of the residual resistance**: decide between
     characterizing the h-scaling excess as a moving-contact-line/model
     characteristic (Ca scan at fixed h, no solver change) and a numerical
     study of the spurious-current contribution (which would require
     authorizing solver/algorithm work that V1b explicitly forbade).
3. **If** the human determines the failures are measurement-only, the rework
   scope should be limited to a V1c measurement protocol: interface-width-aware
   far-field bands outside the distortion zone, a declared `L_hyd` sensitivity
   check, the g9 closure and spurious-current ratio as explicit gates, plus the
   N1–N4 provenance corrections. Be aware that this rework alone is unlikely to
   close g7 given the robustness test above.
4. **Provenance corrections to include in whichever package comes next**: make
   `PROVENANCE.md` agree with the recorded `worktree_dirty` flag, populate
   `exit_code`/`finished_at` before writing artifacts (or drop the fields),
   embed the candidate SHA in each artifact, and tabulate g9.
