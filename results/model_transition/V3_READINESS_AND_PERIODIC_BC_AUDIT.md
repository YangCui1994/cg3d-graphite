# Revised-V3 Readiness and Periodic-BC Audit

- **Task ID:** BI-DEEPSEEK-TRANSITION-001
- **Document class:** readiness design / planning record. **No experiment was
  executed to produce it.**
- **Accepted candidate this document is bound to:**
  `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`
- **Product branch:** `agent-task/BI-DEEPSEEK-TRANSITION-001`
- **Solver status:** unmodified. `lbm_solver_cg3d.py` and everything under
  the production numerical path are byte-identical to the accepted candidate.
- **What this document is not:** it is not a V3 contract, not a V3 result, and
  not an authorization. It proposes; the contract owner decides.

---

## 1. Accepted and frozen scientific state

### 1.1 Frozen production numerical path

| item | accepted value | source |
|---|---|---|
| total-distribution channel | `total_fix = T3` (f64 inverse matrix, f64 accumulator, final f32 cast) | §25, external review of BI-SOLVER-CONSERVATION-FIX-001 |
| colour closure | `colour_fix = C1X` (weighted closure + natural guard) | §26, external review of BI-COLOUR-CLOSURE-001 |
| colour transport/accumulation | `acc_fix = A2` (f64 post-equilibrium colour pipeline) | §26 |
| solver blob | `38bf419e…` unchanged across the four review rounds of BI-SOLVER-CONSERVATION-FIX-001; the later colour-closure task changed the colour path only | §25.0, §26.3 |

`T0` / `C0` / `A0` remain selectable through
`LBM_TOTAL_FIX` / `LBM_COLOUR_FIX` / `LBM_ACC_FIX` to reproduce pre-fix
arithmetic. That is a regression affordance, not a second production path.

### 1.2 Accepted validation chain

```text
V0   Level-A baseline             PASS   (Poiseuille eff 0.9933, Laplace 0.29%, contact 30.3 deg)
V1c  single-front closure         PASS   a26 = 1.0618, a40 = 1.0741  (|a-1| <= 0.10 gate)
V2   bilateral trapped pocket     PASS   symmetry / topology mechanism certified
     total-channel conservation   CLOSED C3 60k total  +1.19e-11 -> -2.48e-11 /step
     colour-channel conservation  CLOSED for project engineering use
```

Details that a revised V3 depends on:

- **V1c static slit calibration** (same-slit protocol, h = 26/40/60/80):
  reproducible plateau `C_static = 0.7819 +/- 0.0308`. For h = 40 this is
  `Pc_static = 2.280325e-3`. The plateau is method/protocol-conditional (an
  18% h26 shift exists between the V1b and V1c protocols); it is a calibrated
  measurement, not a continuum constant.
- **V1c differential hydraulics**: the increment of hydraulic resistance per
  unit added slit length agrees with plane Poiseuille to 4.4% (h = 26) and
  7.0% (h = 40). This is the accepted statement about bulk viscous transport.
- **V2 geometry** (the base for revised V3):
  `wall[0,3) | liquid[3,83) | gas[83,243) | liquid[243,323) | wall[323,326)`,
  h = 40, ny = 42, nz = 6, nx = 326, `psi_solid = -0.68` everywhere, no
  reservoir, no membrane, no body force. x and y are closed by solid while
  their BC flags stay periodic; z is genuinely periodic.

### 1.3 Conservation status, in the exact accepted wording

Accepted wording — use it verbatim, do not strengthen it:

> calibrated, horizon-decaying arithmetic residual with no persistent
> one-sided late trend over the tested horizons.

Explicitly **not** claimed: a mathematically proven bounded floor.
Independently recomputed in Part A of this task from the committed mass
series (see §1.5):

| series | full-window slope | R² | window slopes | increment signs |
|---|---:|---:|---|---|
| periodic C1, 240k | `+1.8046e-11 /step` | 0.2797 | `+1.93e-10`, `-5.04e-12`, `+1.24e-11`, `-4.66e-13` | mixed |
| C3, 120k | `+2.6929e-12 /step` | 0.4146 | `+2.23e-11`, `-4.11e-12`, `+3.70e-12`, `+3.85e-12` | mixed |

Long-window slopes of this size with R² well below 1 are the signature of a
decaying transient plus noise, not of a persistent drift. This is what the
frozen no-sign-bias clause required.

The frozen drift envelope from the V2 external review remains the operative
bound for qualitative certification: `r_M <= 2e-8 /step` and
`|dM|/M0 <= 1e-3` over 60k steps.

### 1.4 Authorization boundary

```text
conservation HOLD for revised V3        LIFTED
old V3 contract                         SUPERSEDED (must not be executed unchanged)
revised V3 buffer-sensitivity design    AUTHORIZED (design only; this document)
revised V3 execution                    NOT authorized
periodic-BC sanity suite execution      NOT authorized
graphite / separator / gap / PCS        NOT authorized
```

### 1.5 Independently recomputed evidence (Part A of this task)

Recomputed from committed raw CSV/JSON only, without reading any headline
value as an input (`results/model_transition/recompute_metrics.py` ->
`recomputed_metrics.json`). Cross-checked against the committed producer
reports at 13-significant-digit text-precision tolerance: **match**.

| quantity | recomputed | committed headline | verdict |
|---|---:|---:|---|
| periodic C1 240k colour slope | `+1.8046e-11 /step` | `+1.8046e-11` | reproduces |
| periodic C1 240k R² | 0.2797 | 0.2797 | reproduces |
| C3 120k colour slope | `+2.6929e-12 /step` | `+2.6929e-12` | reproduces |
| C3 120k R² | 0.4146 | 0.4146 | reproduces |
| V2 max blue relative drift `eps_b` | `5.1584e-7` | `5.1584e-7` | reproduces |
| V2 max front mirror error `e_x` | `7.45e-04 lu` derived / `7.4005e-04 lu` from the committed column | `7.4005e-04` | reproduces (text quantisation) |
| V2 trapped-cluster count | `{1}` at every sample; t=0 single cluster of 38400 nodes | 1 | reproduces |
| V2 interaction status | `NOT_REACHED`; `G_bulk` constant at 146 for all 60 samples | `NOT_REACHED` | reproduces |

---

## 2. Why the old V3 isolation-time / pre-isolation framing is obsolete

### 2.1 What the old contract required

`.agent/episodes/bilateral-imbibition-v0.1/STAGE_V3_BUFFER_SENSITIVITY.md`
lists, among its required observables and promotion gates:

1. "time to central-pocket isolation";
2. gate 2: the 1 B and 2 B cases must produce **pre-isolation front
   trajectories** that "differ by <= 5% in the selected normalized
   front-position metric over their common comparison interval";
3. gate 3: **time to central-pocket isolation** must agree within 5% between
   1 B and 2 B;
4. gate 4: "no case shows the active liquid/gas interface interacting with the
   outer closed wall before the central isolation event";
5. "the trapped-cluster volume at comparable post-isolation states".

Every one of these presupposes the same unstated model: the central gas
starts connected to a vent or bypass and only *later* becomes trapped.

### 2.2 What the accepted evidence says

That model is wrong for this geometry, and the record already says so in three
independent places:

1. **It is trapped from t = 0, by construction.** The layout is
   `liquid buffer | central gas | liquid buffer` with both outer ends closed by
   solid and no vent or bypass. V2 records exactly one 38400-node trapped gas
   cluster at t = 0 (§21.1, `topology_t0.json`).
2. **The V1c external review already deleted this assumption.** Of the two old
   contract assumptions it ordered corrected before V2, the second one removes
   the hard gate that the central gas later loses connectivity to the two
   liquid buffers: for `liquid buffer | central gas | liquid buffer` with both
   outer walls closed and no vent or bypass, the central gas is a trapped
   pocket from the initial instant. (Rendered from the Chinese original in
   §20.9 of the algorithm record; not a verbatim quotation.)
3. **The recomputation in this task shows the isolation event never happens.**
   `G_bulk` — the longest contiguous run of bulk-gas columns — is constant at
   146 in every one of the 60 committed samples from t = 1000 to t = 60000.
   No sample reaches `G_bulk = 0`, so `INTERACTION_ONSET` is `NOT_REACHED`,
   not merely "later".

### 2.3 Gate-by-gate disposition

| old requirement | disposition | reason |
|---|---|---|
| pre-isolation front trajectory (gate 2) | **vacuous** | there is no pre-isolation interval; the menisci form within ~10³ steps and the pocket is trapped at t = 0 |
| time to isolation ≤ 5% (gate 3) | **undefined** | the event it times never occurs |
| interface must not reach the outer wall before isolation (gate 4) | **ill-posed as a risk test** | the interface starts B lu from the wall and moves sub-lu; the real closed-wall coupling is a pressure reflection, not interface arrival |
| trapped volume at post-isolation states (observable 5) | **mis-specified** | see §3.5: a psi-threshold volume mixes interface-profile change with genuine volume change |
| 5% equal-value agreement between 1 B and 2 B | **actively wrong** | the leading-order closed-system balance predicts a 1.33× difference between B and 2 B — see §3.3 |

The last row matters most. A 5% equal-value gate is not merely unsatisfiable
by an immature solver; it contradicts the closed-system thermodynamics of a
correct one. Reusing it would reject correct physics.

### 2.4 What must not be reused

- the words "isolation", "pre-isolation", "post-isolation event" as
  *observable landmarks* (they may appear only in this historical section);
- any gate keyed on an isolation time;
- any gate requiring 1 B and 2 B to agree to a few percent in a quantity that
  closed-system compressibility makes buffer-dependent by construction.

---

## 3. The revised V3 question

### 3.1 Statement

> In the closed bilateral trapped-pocket system, how do the trapped-pocket
> state (mean density / pressure), the compartment mass distribution, the
> interface configuration and the symmetry respond to the finite liquid-buffer
> thickness B — and is the observed B-dependence quantitatively explained by
> closed-system compressibility, or does an additional finite-buffer or
> closed-wall reflection effect remain?

The question is a *sensitivity and attribution* question. It is not a
convergence study and not a search for agreement between buffer sizes.

### 3.2 Why the question is well posed — the governing balance

The system is closed and rigid. The fluid volume is fixed, so for the two
compartments

```text
dV_gas + dV_liquid = 0                                            (rigid, closed)
```

Both phases are weakly compressible with the same unit density, so
`d rho / rho = dp / c_s^2` with `c_s^2 = 1/3`. At a quasistatic meniscus the
capillary pressure is held at `Pc`, giving `dp_gas - dp_liquid = Pc`. Solving
the three together:

```text
dp_liquid = - Pc * V_gas / (V_gas + V_liquid)
dp_gas    = + Pc * V_liquid / (V_gas + V_liquid)
d rho_gas = + 3 * Pc * V_liquid / (V_gas + V_liquid)              (unit density)
```

with `V_gas = G0*h*nz` fixed by the contract geometry and
`V_liquid = 2*B*h*nz` the swept quantity. Two consequences:

1. the pocket is **compressed**, but only by the amount the capillary pressure
   can buy against a stiff two-compartment system;
2. the pocket density rise is an explicit, monotone, *saturating* function of
   B — it is a prediction, not a nuisance.

**Quantitative consistency with the accepted V2 run.** At the first
post-meniscus sample (t = 1000) the committed V2 pocket mean density is
`rho_gas_mean = 1.003444`. The balance above with `Pc = Pc_static(h=40) =
2.280325e-3` (the V1c same-slit calibration, §1.2) predicts
`+3.4205e-3` — **0.7% from the measurement**. Using instead the nominal
droplet-registry value `2 sigma cos(theta)/h = 2.6213e-3` predicts `+3.9319e-3`,
14.2% off. So:

- the closed-system compressibility balance reproduces the measured pocket
  compression to below one percent, and
- the V1c same-slit static calibration is the right capillary pressure for this
  geometry, which is an independent cross-check of that calibration.

**One caveat, stated explicitly.** The balance explains the *density* jump; it
does not explain the whole subsequent evolution. Between t = 1000 and
t = 60000 the committed V2 run shows the pocket's `psi > 0` region slowly
**expanding** — continuum pocket sum `38288 -> 38379` nodes, gas mass proxy
`38421 -> 38509` — while the mean density holds at `1.0034`. The system is
closed and total mass is conserved, so that growth is a *redistribution*
(liquid-region nodes becoming gas-region nodes as the diffuse profile drifts
outward), not new mass. Two things follow, and both are design inputs rather
than objections:

- the balance is a statement about the pocket *state* at meniscus formation,
  **not** a closed-form model of the slow mode that continues afterwards;
- this is precisely why §3.5 adds compartment masses and a fitted slow mode,
  and why the interface-position observable must not be leaned on: the V2
  review already flagged a `d(t)` identity defect that remains unfixed on the
  accepted candidate.

### 3.3 Predicted buffer dependence (the design target)

```text
Pc = 2.280325e-3 (V1c same-slit static, h = 40),  G0 = 160, h = 40, nz = 6
```

| B | `V_liquid/V_total` | predicted `d rho_gas` | vs B = 80 | predicted meniscus advance |
|---:|---:|---:|---:|---:|
| 40 (0.5 B) | 0.333 | `+2.280e-3` (+0.228%) | 0.667 | 0.18 lu / front |
| 80 (1 B, V2 base) | 0.500 | `+3.421e-3` (+0.342%) | 1.000 | 0.27 lu / front |
| 160 (2 B) | 0.667 | `+4.561e-3` (+0.456%) | 1.333 | 0.37 lu / front |
| 320 (4 B, conditional) | 0.800 | `+5.473e-3` (+0.547%) | 1.600 | 0.44 lu / front |

The meniscus column is the same balance expressed as geometry:
`delta = 3 Pc (V_gas V_liquid / V_total) / (2 h nz)`.

The 1 B / 2 B ratio is **1.333**. A 5% equal-value gate would therefore fail a
correct simulation by a factor of 6.7. The replacement criterion is stated in
§5.

### 3.4 What would falsify the "closed-system, no extra artifact" reading

The B-sweep falsifies it if any of the following holds:

- measured `d rho_gas(B)` departs from `3 Pc 2B/(G0+2B)` by more than the
  declared tolerance, in a way that is monotone in B;
- the compartment mass budget shows a redistribution between the two liquid
  buffers and the pocket that the balance does not predict;
- the outer-wall pressure history carries an oscillatory component whose
  amplitude does not scale away with B (the reflection signature);
- symmetry metrics (`e_x`, `E_psi`) grow with B rather than staying at their
  V2 level.

None of these is a failure of the solver; each is a finding about how far the
closed bilateral model can be pushed.

### 3.5 Observables: keep, add, retire

**Retire.** `trapped-cluster volume` computed as a count of `psi > 0` or
`|psi| > 0.9` nodes. It moves when the diffuse interface *profile* changes,
not only when the pocket volume changes: in V2 the binary count moves
38304 -> 38400 while the continuum sum moves 38288 -> 38379, and the 0.5-crossing
gap moves 160.23 -> 161.70 lu while the pocket density moves by 1e-4. These
three "volumes" disagree because they measure different things. Keep them as
diagnostics but never as the primary buffer-sensitivity observable.

**Keep (well defined, already committed for the base case).**

| observable | definition | V2 value (post-fix, recomputed) |
|---|---|---|
| pocket mean density / pressure | mean over pocket nodes; `p = c_s^2 rho` | `1.003444 -> 1.003343`; `p = 0.334481 -> 0.334448` |
| front positions and mirror error | `x_left`, `x_right`, `x_right* = (nx-1) - x_right`, `e_x` | max `e_x = 7.4005e-04 lu` |
| field mirror asymmetry | `E_psi = mean_fluid abs(psi(x) - psi(nx-1-x))` | series max `9.02e-05`; `8.65e-05` at the final sample |
| bulk-gas column count | `G_bulk` | constant 146 |
| cluster topology | 6-neighbour + z-wrap union find | 1 throughout, no fragmentation |
| conservation sentinels | `eps_r`, `eps_b`, total channel | `5.87e-06`, `5.16e-07` |

**Add (new, required by the revised question).**

1. **Compartment mass budget.** Split the fluid domain into
   `left buffer | pocket region | right buffer` and report the mass in each as
   a time series. Total mass is exactly conserved to the arithmetic floor, so
   any change in the split is a *redistribution*, which is the direct,
   profile-independent observable for buffer sensitivity. This replaces the
   psi-threshold volume.
2. **Outer-wall coupling history.** For each of the two closed x-walls, the
   density/pressure history of the adjacent fluid layer (and its amplitude in
   a late window). This is the direct observable for "does the closed wall feed
   back", replacing the old interface-arrival gate.
3. **Fitted slow mode.** The V2 evidence shows the system is still relaxing at
   t = 60000: the continuum pocket sum is `20.7` nodes below its nominal
   38400 (`5.4e-4` relative) and still closing; `e_x` wanders at the
   `1e-4 - 7e-4` level; only the pocket density is stable to `1e-4` relative.
   V3 must therefore fit each observable as
   `y(t) = y_inf + A exp(-t/tau)` (or an equivalent declared slow-mode form)
   and compare the **fitted asymptote**, not the value at an arbitrary step.
   The measured residual offset at the comparison horizon is the resolution
   floor of the buffer comparison and must be reported next to every
   difference.
4. **z-structure spread.** `max_k F(i,j,k) - min_k F(i,j,k)` for `psi` and
   `rho`. Cheap, and it is the natural coupling to §7. Measured on the
   committed V2 fields: exactly 0 in the initial condition, `5.0e-4` (psi) and
   `1.3e-5` (rho) at the final field, with a highly persistent spatial pattern
   (`r = 0.996` between the mid and final maps).
5. **V1c-style differential hydraulic slope.** Only if the sweep changes the
   *length* rather than the buffer thickness. Not applicable to the B-sweep
   itself, where the outer walls are closed; listed here so the distinction is
   not lost.

---

## 4. Proposed buffer-size test matrix

Hold fixed: `W = 3`, `G0 = 160`, `h = 40`, `ny = 42`, `nz = 6`,
`psi_solid = -0.68`, `niu_l = niu_g = 0.1`, `CapA = 0.06`, no force, no
reservoir, no membrane, all `bc_*` flags at the periodic default. Sweep only B.

| case tag | B | nx | nodes | vs V2 | predicted `d rho_gas` | role |
|---|---:|---:|---:|---:|---:|---|
| `v3_B40` | 40 | 246 | 61 992 | 0.75× | `+2.28e-3` | 0.5 B |
| `v3_B80` | 80 | 326 | 82 152 | 1.00× | `+3.42e-3` | 1 B, must reproduce V2 |
| `v3_B160` | 160 | 486 | 122 472 | 1.49× | `+4.56e-3` | 2 B |
| `v3_B320` | 320 | 806 | 203 112 | 2.47× | `+5.47e-3` | 4 B, conditional |

`nx = 2W + 2B + G0`.

- **Core sweep: `{40, 80, 160}`.** The 0.5 B case is *not* geometrically
  compromised: B = 40 lu holds the interface (width ~2.2 lu) and the ~0.3 lu
  meniscus advance far from the wall, so the old contract's escape to
  1 B/2 B/4 B is unnecessary. State the absolute B values, as the old contract
  required.
- **`v3_B80` is a reproduction control.** It must reproduce the committed V2
  observables within the declared tolerances; if it does not, the sweep is
  invalid before any buffer conclusion is drawn.
- **`v3_B320` is conditional and bounded.** Add it only if 2 B and 4 B are
  needed to separate the saturating prediction (`1.600×`) from a residual
  linear trend; a single bounded addition, not an open-ended ladder.
- **Horizon.** V2 is still relaxing at 60k, so the core sweep must run at least
  to the pre-registered horizon at which the fitted slow mode of the *pocket
  density* is below the smallest buffer difference to be resolved. On the V2
  slow mode a 150k horizon is the natural first choice; if the fit is still
  unresolved, extend once by a fixed factor and record it, rather than
  iterating.
- **Cost (no new information needed; scaled from the committed V2 timing of
  325.6 s for 60k steps at 326x42x6, same GPU):** core sweep at 60k
  ~1 060 s; at 150k ~2 650 s. Affordable as a single bounded batch; run as one
  instance-reuse batch per the project's Taichi JIT policy.
- **Alignment rule.** The old contract asked for event-aligned comparison.
  The only event in this system is meniscus formation, which completes inside
  the first ~10³ steps and is local. Align on the pre-registered first sample
  after `G_bulk` stabilizes, then compare *fitted asymptotes* over the common
  window. Do not compare snapshots at equal step counts alone.

**Owner decisions this matrix does not take** (flagged, not resolved —
AGENTS.md requires unresolved acceptance criteria to be reported, not chosen
implicitly): the acceptance tolerance for departure from the §3.2 balance; the
horizon length; whether the 4 B case is included.

---

## 5. Hard invariants versus scientific diagnostics

### 5.1 Frozen hard invariants, carried over unchanged

A case that violates any of these is **invalid**, not a scientific result.

| id | invariant | status |
|---|---|---|
| H1 | no NaN / Inf at any sample | frozen (g1) |
| H2 | `u_max <= 0.12` | frozen (g2); V2 measured 0.0256 |
| H3 | bulk-node `rho` inside `[0.89, 1.11]` | frozen (g3, ratified semantics: bulk `abs(psi) > 0.9`; all-fluid extrema reported but not a bulk-EOS criterion) |
| H4 | front mirror error `e_x <= max(2, 0.02 d)` lu | frozen (g5); V2 measured `7.4e-4` |
| H5 | exactly one trapped cluster at t = 0 | frozen (g7) |
| H6 | no fragmentation before onset | frozen (g8); V2: cluster count 1 throughout |
| H7 | drift envelope `r_M <= 2e-8 /step`, `abs(dM)/M0 <= 1e-3` over 60k | frozen (V2 external review R-V2-2) |

### 5.2 Proposed new hard invariants

These are **proposals**. They require contract-owner approval; they are not
self-authorizing, and nothing in this document should be read as adopting them.

| id | proposed invariant | rationale |
|---|---|---|
| N1 | the `B = 80` control reproduces the committed V2 observables inside the declared reproduction tolerance | the sweep is meaningless if its own base case cannot be reproduced |
| N2 | compartment mass budget closes: `sum of the three compartment masses` equals the domain mass to the same order as the conservation sentinel | without this the "redistribution" observable is not trustworthy |
| N3 | the total-channel and colour sentinels stay inside the *post-fix* measured level, not merely inside the old pre-fix envelope | the envelope was calibrated before the fix; a V3 case sitting at the old envelope would indicate a regression, not physics |
| N4 | the `z`-spread does not grow with B beyond the V2 level | guards against a geometry-dependent seam effect entering through the sweep |

Explicitly **not** proposed as hard invariants: agreement between buffer sizes.
That is the scientific question, and a hard gate on it would pre-decide it.

### 5.3 Scientific diagnostics (no pass/fail)

Reported for every case, never gated:

- `d rho_gas(B)` and its ratio to `B = 80`, against the §3.3 prediction;
- compartment masses and their redistribution history;
- fitted slow-mode amplitudes and time constants per observable;
- interface positions, `e_x`, `E_psi`, `G_bulk`;
- outer-wall adjacent-layer pressure amplitude and its late-window trend;
- cluster count history, `V_bin`, `V_cont`;
- `z`-spread of `psi` and `rho`;
- `rho_min_allfluid` (reported as an interface structure, as in V2, not as a
  bulk-EOS failure).

---

## 6. Should a periodic-BC sanity suite precede V3?

### 6.1 What the periodic question actually is in this geometry

In the V2/V3 geometry the three axes are not equivalent:

- **x**: closed by solid (`wall[0,3)` and `wall[323,326)`), BC flag periodic;
- **y**: closed by solid (two wall rows), BC flag periodic;
- **z**: genuinely periodic, no solid.

So the z seam is the only *live* seam, and in V2/V3 neither solid nor interface
crosses it. The seam is exercised only by the flow and by the diffuse
interface stencil when a node at `k = 0` reads `k = nz-1`.

### 6.2 Read-only probe on committed evidence

`results/model_transition/periodic_seam_probe.py` (analysis of committed
artifacts only — no simulation) measured on the three archived V2 fields:

| field | `z`-spread `psi` (max / mean) | `z`-spread `rho` (max) | `E_psi` mean |
|---|---:|---:|---:|
| initial | `0.0` / `0.0` | `0.0` | `0.0` |
| mid | `4.98e-04` / `1.71e-04` | `1.24e-05` | `8.00e-05` |
| final | `5.07e-04` / `1.91e-04` | `1.32e-05` | `8.57e-05` |

Two facts follow:

1. **The z direction is not inert.** The initial condition is exactly
   z-uniform, yet a `~5e-4` z-structure develops and then *saturates* (it does
   not grow between the mid and final snapshots). This is the same order as the
   front mirror error (`7.4e-4 lu`), so z-structure is not negligible relative
   to the V2 symmetry metrics.
2. **It is systematic, not noise.** The per-node z-spread maps at the mid and
   final snapshots correlate at `r = 0.996`. A random artifact would not
   reproduce its spatial pattern after tens of thousands of steps.

### 6.3 Recommendation

**A periodic-BC sanity suite is not a prerequisite for the revised V3 as
designed, and V3 should not be gated on it.** Reasons:

- V3's decisive comparison varies B in **x**; the z-geometry is identical in
  every case, so any z-structure is common-mode and cancels in the comparison
  to first order;
- neither solid nor interface crosses the z seam in any V3 case, so V3 does
  not exercise the untested path;
- the probe above already bounds the z-effect in the base geometry at
  `~5e-4` in `psi`, and §5.2/N4 turns that into a guard rather than an
  open investigation.

**But run the bounded pre-V3 readiness pass**, and do not expand it:

1. re-read `P0` and `P2` from the already-committed C0/C1/C3 isolation matrix
   plus the probe above — no new runs;
2. carry the z-spread observable into V3 as proposed invariant N4;
3. **defer `P1` shape observables and all of `P3`** to the first task whose
   geometry actually wraps solid or an interface across the z seam. That is
   where the untested code path lives, and where a seam test becomes mandatory
   rather than precautionary.

**Trigger condition (explicit):** `P3` must be executed and passed *before*
the first simulation whose solid geometry or interface is contiguous across
the z seam — which includes any z-periodic porous packing, and therefore the
graphite / PCS line, but not V3.

---

## 7. Proposed P0–P3 periodic-BC tests

All four are **proposals**. None has been executed. Each states what already
exists in committed evidence so that the suite does not re-run settled work.

### P0 — fully periodic single phase

- **Geometry:** solid-free box, uniform `psi`, all `bc_* = 0`. Sizes 16³ / 24³
  / 32³ and one anisotropic box (e.g. `64 x 24 x 6`) to include a thin periodic
  axis.
- **Check:** stationarity. Uniform single phase must remain *exactly*
  stationary under the frozen arithmetic: `max abs(u) = 0.0` and bit-exact
  fields after N steps.
- **Already covered?** Yes — `C0` in the isolation matrix and the 7-combination
  A2 stationarity isolation both report exact `0.0`, and the frozen A2 gate is
  phrased precisely as this. **Re-read; no new run needed.**

### P1 — fully periodic two-phase slab

- **Geometry:** solid-free box, `psi = -1` for `x < nx/2` and `+1` otherwise,
  fully periodic on all axes (the isolation-matrix `C1`, `64 x 24 x 24`); both
  interfaces are normal to x, so the periodic x-wrap is crossed by an
  interface.
- **Check (new observables, not present in the conservation-focused runs):**
  interface planarity (max deviation from the fitted interface plane in lu);
  no accumulation or depletion at the x seam (compare the seam-adjacent column
  against its mirror column); magnitude of the parasitic interface current
  against the walled `C3` case; symmetry of the two interfaces.
- **Already covered?** Conservation only — `C1` exists and is characterised for
  240k steps under `T3+C1X+A2`. The shape/continuity observables are new and
  need one short run (of order 20k steps, not a science run).

### P2 — z-periodic with x/y solid walls

- **Geometry:** the production-like case: solid in x and y, z periodic. Two
  variants: single phase (`C2`, `32 x 46 x 6`) and two phase (`C3`,
  `126 x 46 x 6`; or the V2 geometry itself, `326 x 42 x 6`).
- **Check:** z-invariance of the solution to round-off where the initial
  condition is z-invariant; `u_z` and its extrema; conservation across the
  seam; the z-spread of `psi` and `rho` as a declared, bounded quantity rather
  than an implicit assumption.
- **Already covered?** Conservation yes (`C2`/`C3`, and the 240k colour runs).
  The z-invariance observable is new; for the V2 geometry it is already
  reported in §6.2 from committed fields.

### P3 — solid geometry crossing the z-periodic seam

- **Geometry:** the one genuinely untested case. A solid pillar or rib occupying
  a subset of `(x, y)` for `z in {0, nz-1}` — i.e. contiguously across the
  seam — with fluid elsewhere. Plus a **paired control**: the identical pillar
  moved to the interior, e.g. `z in {3, 4}`.
- **Check:** the seam-crossing pillar must behave as one connected obstacle —
  no flux through it, no spurious interface pinning or leakage at the seam, and
  agreement with the interior-pillar control within the declared arithmetic
  floor for `G_bulk`, pocket density, symmetry and the compartment mass budget.
- **Already covered?** No. Nothing in the committed evidence has solid
  contiguous across a periodic seam.
- **Relevance:** not on the V3 critical path (§6.3). Mandatory before any
  z-periodic geometry containing solid that wraps the seam.

---

## 8. Expected evidence and artifact structure

### 8.1 Revised-V3 product evidence

```text
results/levelc_v3_buffer/
  MANIFEST.json                 SHA256 of every artifact
  PROVENANCE.md                 base/candidate SHAs, commands, env, incidents
  EXECUTION_REPORT.md           per .agent/templates/EXECUTION_REPORT.md
  summary.json                  per-case fitted parameters + gate verdicts
  gates.csv                     machine-readable gate table (generated)
  cases/<tag>/                  tag in {v3_B40, v3_B80, v3_B160[, v3_B320]}
    front_series.csv            t, x_left, x_right, x_right*, e_x, ...
    gas_series.csv              pocket density/pressure, G_bulk, clusters, ...
    mass_stability_series.csv   m_r, m_b, eps_r, eps_b
    compartment_mass_series.csv NEW: per-compartment mass, profile-independent
    wall_series.csv             NEW: outer-wall adjacent-layer density/pressure
    z_spread_series.csv         NEW: z-spread of psi and rho per sample
    fields_{initial,mid,final}.npz
    report.json                 gates, exit reason, prov block (incl. exit code)
    run.log, run.exit           stdout and machine-captured exit code
  figures/                      script-generated; candidate SHA in every caption
  analysis/                     generator scripts for the above artifacts
```

Rules carried forward from the accepted practice (§25.9 lesson): every number
that appears in a report table is generated by a committed script from the
committed JSON/CSV — no hand-copied values; every figure caption carries the
candidate SHA; every case reports a machine-captured exit code.

### 8.2 Periodic-BC suite evidence (when authorized)

```text
results/periodic_bc_sanity/
  P0_periodic_single_phase/  P1_periodic_two_phase_slab/
  P2_z_periodic_walled/      P3_solid_across_seam/   (with interior-pillar control)
  summary.json  gates.csv  MANIFEST.json  PROVENANCE.md  EXECUTION_REPORT.md
```

### 8.3 Review chain

Executor report -> fresh reviewer (`.agent_runtime/<TASK-ID>/REVIEW.md`) ->
external scientific review. The reviewer contract for this transition task is
`.agent/episodes/bilateral-imbibition-v0.1/DEEPSEEK_TRANSITION_REVIEWER_CONTRACT.md`.

---

## 9. Explicit stop boundary

This document performed, and this task performed:

- no solver modification (`lbm_solver_cg3d.py` and the production numerical
  path are byte-identical to `6c30260`);
- no V3 execution;
- no periodic-BC test execution (the probe in §6.2 is read-only analysis of
  already-committed fields, not a run);
- no graphite, separator, gap or PCS work;
- no change to any accepted physics, boundary condition, initial condition,
  convergence rule or acceptance gate;
- no revival of the superseded isolation-time / pre-isolation framing (§2
  describes it only to retire it).

What remains unauthorized:

```text
revised V3 execution            requires a written contract + external authorization
periodic-BC suite execution     requires a separate authorized task
P0-P3 as proposed here          proposals only
graphite / separator / gap / PCS  not authorized
```

---

## Appendix A — commands and provenance

```bash
# repository root = the BI-DEEPSEEK-TRANSITION-001 worktree, branch
# agent-task/BI-DEEPSEEK-TRANSITION-001, base 6c30260dfe0c8b61ea9609e6bffa5c487312cf06

# Part A — independent recomputation (writes recomputed_metrics.json)
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/recompute_metrics.py

# §6.2 — read-only z-seam probe (writes periodic_seam_probe.json)
C:/Users/yangc/anaconda3/envs/lbm/python.exe results/model_transition/periodic_seam_probe.py
```

Neither command runs a simulation; both read committed CSV/JSON/NPZ only.

## Appendix B — terms used

| term | meaning in this document |
|---|---|
| buffer thickness `B` | liquid-buffer extent on each side of the pocket, in lu; the swept quantity |
| `G0` | central gas extent at t = 0, in lu (160) |
| `G_bulk` | longest contiguous run of columns that are >= 95% bulk gas; the interaction-onset detector |
| `e_x` | front mirror error, `abs(x_left - ((nx-1) - x_right))`, in lu |
| `E_psi` | field mirror asymmetry, mean over fluid nodes of `abs(psi(x) - psi(nx-1-x))` |
| pocket | the central trapped gas cluster; trapped from t = 0 in this geometry |
| seam | a periodic boundary plane; here the live one is `z` |
| `Pc` | capillary pressure; `Pc_static(h=40) = 2.280325e-3` from the V1c same-slit calibration |
