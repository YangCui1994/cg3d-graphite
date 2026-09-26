# IMPLEMENTATION PLAN — `L17_CORE` and its variants

Task: `BI-CG-LECLAIRE-IMPLEMENTATION-001`
Product branch: `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`, base `6c30260`

This plan is the gate between the committed formulation
(`PAPER_FORMULATION.md`, `CURRENT_VS_LECLAIRE_MAP.md`,
`FOLLOWUP_OPTIMIZATION_MAP.md`, `REFERENCE_MANIFEST.md`) and any implementation
code. It separates three things that must stay separately identifiable:

```text
L17_CORE            paper-faithful Leclaire-2017 D3Q19 implementation
   +
FOLLOW-UP VARIANTS  individually switchable, default OFF
   +
CONSERVATION OVERLAY  distinct optional layer, default OFF,
                      never described as paper-faithful when enabled
```

---

## 1. Paths and isolation

```
experimental/leclaire_cg/
    __init__.py
    lattice.py        D3Q19 connectivity, weights, M, K, index tables
    solver.py         LeclaireCG3D: the isolated solver
    operators.py      gradient, wetting, perturbation, recoloring, bounce-back
    geometry.py       algorithm-independent test-geometry generators
tests/leclaire_cg/
    __init__.py
    test_lattice_tables.py   table-level unit checks (no simulation)
    run_canonical.py         the ten-test canonical validation matrix driver
docs/research/leclaire_cg/   formulation artifacts (this directory)
results/leclaire_cg/         evidence (created by the validation phase)
```

Hard constraints, checked before the implementation commit:

- `lbm_solver_cg3d.py` is **not modified** — enforced by comparing its blob hash
  against the base commit and by `git diff --name-only` on the product branch.
- no production default, gate or threshold is changed;
- no file outside `experimental/leclaire_cg/**`, `tests/leclaire_cg/**`,
  `results/leclaire_cg/**`, `docs/research/leclaire_cg/**`, and the
  `.gitignore` line for `_refs/` is touched;
- no Palabos-derived code;
- D3Q19 only.

Shared-with-production assets are limited to algorithm-independent infrastructure.
This task reuses **nothing** by import from the production solver: the new line is
self-contained, so a change in the production file cannot silently alter it. The
test-geometry generators are written here rather than imported, because the
production ones encode `psi_solid`-specific wall semantics
(`CURRENT_VS_LECLAIRE_MAP.md` rows 15, 20) and are therefore **not** algorithm
independent.

---

## 2. `L17_CORE` — element list and provenance

Every element carries a source reference in a code comment per
`LECLAIRE_IMPLEMENTATION_CONTRACT.md` §6.

| element | implementation | provenance |
|---|---|---|
| connectivity + ordering | `lattice.py` table | R1 Table IV, order fixed |
| `W_i, φ_i, ϕ_i, ψ_i, ξ_i, B_i` | `lattice.py` | R1 Table IV |
| `ζ = 1/2`, `α = W0 = 1/3` | `lattice.py` | R1 Table VI + §0.3 derivation |
| `M` (19×19) | `lattice.py`, transcribed | R1 Table XI |
| viscosity indexes `{9,11,13,14,15}` | `lattice.py` | R1 Table VIII |
| `K` | `operators.py` | R1: `ω_eff` on `υ`, else `χω_eff` |
| `ω_eff = 2/(6ν+1)` | `operators.py` | R1 Eq. (14) |
| `ν` interpolation | `operators.py` | R1 Eq. (13), harmonic |
| equilibrium `N^(e)` | `operators.py` | R1 Eq. (4) **including** `ψ_i`, `ξ_i` |
| forcing `|ΔN⟩` | `operators.py` | R1 Eqs. (6)–(9); **default off** |
| gradient `F` | `operators.py` | R1 Eq. (17) + §4.3 derived stencil |
| perturbation | `operators.py` | R1 Eqs. (15)–(18), applied **post-collision, unrelaxed** |
| recoloring | `operators.py` | R1 Eqs. (19)–(20), pairwise form §6.2 |
| wetting (orientation rotate) | `operators.py` | R1 Eqs. (30)–(33) |
| `n_w` smoothing + gradient | `geometry.py` | R1 Eqs. (34)–(38), 3 passes |
| full-way bounce-back | `solver.py` | R1 step (6) |
| streaming | `solver.py` | R1 step (7) |
| operator ordering | `solver.py` | R1 steps (1)–(7), as a single documented sequence |

**Design choice that protects fidelity.** The equilibrium is evaluated from Eq.
(4) **directly in distribution space**, and the moment equilibrium is obtained as
`m^(e) = M · N^(e)`. The closed-form 19-moment equilibrium is *not* hand-derived.
This removes the single largest transcription risk (the current production
header documents that its own closed form needed a separate 4.4e-16 verification
exercise), and it keeps the `ψ_i`/`ξ_i` terms structurally impossible to drop.

**Also implemented, default off, because they are switches in the plan:**
`recolor_beta` (core parameter), `recolor_form ∈ {paper, min_variant}`,
`wetting ∈ {leclaire, akai}`, `chi`, `conservation_overlay ∈ {None, f64_arithmetic}`.

**Explicitly not implemented in this task:** R1 Eqs. (21)–(29) regularized open
boundaries (`F4`), variable density ratio (`F5`), R4's extra recoloring step
(`F3`). Each is named in `FOLLOWUP_OPTIMIZATION_MAP.md` with its switch name and
the reason it is deferred. No silent stub will be shipped: an unimplemented
`open_bc` value raises rather than falling back.

---

## 3. Backend and performance strategy

The production line's hard-won constraint applies unchanged: on this machine a
Taichi solver instance costs ~5.5 min of JIT compile, the cache key includes an
instance counter, and a second instance in the same process always misses.

Plan:

1. **Write the core as NumPy-vectorised reference first**, and use it as the
   executable definition of the algorithm.
2. Provide the Taichi kernel path only if the NumPy path cannot reach the
   required grid sizes and step counts inside the budget — the canonical tests
   are deliberately small (see §4), so a vectorised NumPy solver is sufficient
   and avoids a compile tax that would dominate the run.
3. **One process per arm, one solver instance per process**, so that no two
   instances are ever created in one interpreter.

This is a deliberate deviation from "use Taichi like production" and is recorded
as such: the deliverable is an *algorithmic* candidate and its evidence, not a
production-performance port. The report states that the candidate is not
performance-comparable to the production line.

---

## 4. Canonical validation matrix

Ten required tests, each with a machine-readable JSON output, an exit code, and a
committed generator script. Geometries are sized to the smallest dimensions that
still make the measurement meaningful, and each test declares its own
acceptance statement **before** the run (recorded in the driver, not
post-hoc).

| # | test | setup | headline metric | acceptance statement |
|---|---|---|---|---|
| 1 | uniform single-phase stationarity | periodic box, `ψ ≡ 1`, `u = 0` | `max|v|`, `max|Δρ|`, drift per step | machine-precision stationarity |
| 2 | planar interface stationarity | periodic slab, `ψ = ±1` | interface position drift, `max|v|` | no spurious flow across the interface |
| 3 | Laplace droplet | droplet in a periodic box | measured `σ` from `Δp` vs `r` | `σ` matched to input within a stated band |
| 4 | static contact angle | droplet on a flat wall, `θ_c` swept | measured `θ` vs prescribed `θ_c` | monotone, accurate over the tested band |
| 5 | interface width vs `β` | planar interface, `β` swept | fitted `tanh` width | monotone response to `β`; floor set by lattice |
| 6 | dynamic isotropy | moving droplet / capillary wave | anisotropy of the front speed vs lattice direction | no resolvable lattice-direction bias |
| 7 | static slit capillary pressure | slit of width `h`, no driving | `P_c` vs `2σcosθ/h` | matches the analytic relation |
| 8 | simple capillary imbibition | single capillary, spontaneous filling | front position vs Washburn | `x ∝ √t` with the expected prefactor |
| 9 | **asymmetric killer test** | one-sided complex wall, no imposed `Δp` | wall-directed mass flux, contact-line drift, spurious velocity, topology | no artificial wall-directed mass transfer |
| 10 | conservation audit | reuses 1/2/7 geometries | total and component mass drift per step | drift characterised; overlay arm reported separately |

### 4.1 The killer test (test 9), designed against R2's warning

R2 records that periodic boundaries can **conceal** wetting-BC defects, because
artificial wall-directed mass transfers can cancel under periodic closure
(R2, extracted p.9–10, and `PALABOS_LECLAIRE_CODE_TRACE.md` §10.2). The killer
test is therefore built so that cancellation is impossible:

- the wall is a **single-sided step/ledge** spanning part of the domain, not a
  symmetric channel;
- the two ends are closed (no through-flow) and there is **no imposed pressure
  difference**;
- the solid mask is deliberately **not** symmetric under any lattice
  translation that the periodic wrap identifies;
- the tracked quantities are, per R1's and the contract's lists: component mass
  **near the wall** (a thin band), total component mass, contact-line position
  with zero driving pressure, spurious velocity, and the number/size of
  disconnected regions (topology).

An arm that shows a monotone wall-band component-mass transfer with zero imposed
drive, or a contact line that creeps without a capillary driver, is reported as
a **failure of that arm** — including the `L17_CORE` arm. The test is not tuned
to make the new line win; the contract's §8 is explicit that the goal is
attribution.

### 4.2 A/B structure

Where the geometry is shared, each measurement is reported as

`CURRENT_PRODUCTION`  vs  `L17_CORE`  vs  `L17_PLUS_AKAI`  vs  `L17_PLUS_OVERLAY`

and, for test 5 only, `CURRENT_AMPLITUDE_ABLATION`. Production numbers are
obtained by **running the production solver on the shared geometry inside this
task's own driver** — no prior production PASS is reused as evidence
(`LECLAIRE_IMPLEMENTATION_CONTRACT.md` §7). Production gates and thresholds are
read, never written.

### 4.3 What the matrix will and will not support

Stated in advance so the report cannot overreach:

- **supports**: fidelity of the elements listed in §2; whether the paper's
  recoloring amplitude and wetting closure change the observables; the sign and
  size of the conservation residual; whether an asymmetric wall is handled.
- **does not support**: any claim about `η` (F1.1); any porous-media or
  multi-pore claim (no porous geometry is run — the contract's stop boundary
  forbids full porous-media production runs); any performance claim; any claim
  about variable density ratio or regularized open boundaries (not implemented).

---

## 5. Commit discipline

Exactly the three logical commits the contract requires, in this order:

1. `formulation:` — `PAPER_FORMULATION.md`, `CURRENT_VS_LECLAIRE_MAP.md`,
   `FOLLOWUP_OPTIMIZATION_MAP.md`, `IMPLEMENTATION_PLAN.md`,
   `REFERENCE_MANIFEST.md`, plus the `.gitignore` entry for `_refs/`. **No code.**
2. `implementation:` — `experimental/leclaire_cg/**`, `tests/leclaire_cg/**`.
3. `validation:` — `results/leclaire_cg/**` evidence, report, `summary.json`,
   `PROVENANCE.md`.

Commit 1 is not amended after simulation results are known. If the formulation
turns out to be wrong, a separate corrective commit is added — the provenance of
"what we believed before running" is part of the deliverable.

---

## 6. Stop boundary

This task does not authorize: promotion into the production solver, revised-V3
execution, graphite / separator / PCS work, or full porous-media production runs.
After the validation commit and the review request, the executor stops.

## 7. Risk register

| risk | mitigation | fallback |
|---|---|---|
| exact R5 gradient coefficients unavailable | isotropy derivation in the formulation; `UNRESOLVED` label | report as a bounded fidelity gap, not as a pass |
| contact-angle sign convention ambiguous in R1 | report measured `θ` with the phase it was measured on | flag as `HUMAN_REQUIRED` if it flips a test verdict |
| Taichi compile tax dominates the budget | NumPy reference implementation | state the deviation explicitly |
| an arm fails the killer test | report the failure | do **not** retune the test or the arm; the contract forbids it |
| conserved-moment relaxation reading ambiguous | literal reading + recorded as immaterial | note in the report |
