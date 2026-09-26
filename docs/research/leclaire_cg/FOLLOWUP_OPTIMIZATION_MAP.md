# FOLLOWUP OPTIMIZATION MAP

Task: `BI-CG-LECLAIRE-IMPLEMENTATION-001`

Purpose: keep the baselines and their later optimisations **separately
identifiable** so that any change in numerical behaviour can be attributed by
ablation. The papers are explicitly *not* collapsed into one undocumented "best"
model (`LECLAIRE_IMPLEMENTATION_CONTRACT.md` §4).

Each entry states: baseline behaviour → follow-up source → exact change →
motivation → expected effect → implemented now? → switch/ablation plan.

Legend for "implemented now": **YES (core)** is part of `L17_CORE`;
**YES (switch)** is implemented but default-off; **NO (planned)** is specified
but not implemented in this task.

---

## F1 — Explicit `β` control of the numerical interface thickness

- **Baseline (R1).** `L17_CORE` already includes `β` as a first-class parameter:
  Eq. (19) carries `β (ρ_rρ_b/ρ²) cos ϑ_i N_i^(e)`.
- **Follow-up source.** None — this is *not* a later optimisation. It is listed
  here because the executor contract names "explicit-beta recoloring" as a
  candidate variant, and because the current production line has **no `β` at
  all** (`CURRENT_VS_LECLAIRE_MAP.md` row 19).
- **Exact change vs the current production line.** Replace the implicit
  `min(ρ_r, ρ_b)` amplitude with `β (ρ_r ρ_b/ρ)`, and apply the increment to the
  post-perturbation colour-blind `N_i` rather than to an equilibrium colour split.
- **Motivation.** R2 states that in the CGM the Cahn number is controlled by the
  recoloring parameter *alone* and is independent of the physical parameters —
  this is one of the CGM's stated advantages over the pseudopotential model.
  Without `β` the current line has no independent interface-width knob.
- **Expected effect.** Measurable, monotone dependence of the equilibrium
  interface width on `β` at fixed interface tension; no dependence of the
  physical parameters on the chosen width.
- **Implemented now?** **YES (core).** `β` is a `L17_CORE` parameter with the
  paper's semantics.
- **Switch/ablation.** `recolor_beta` (float, core). Ablation arm:
  `recolor_beta` swept over a small set in canonical test 5, plus a
  `recolor_form="min_variant"` arm that reproduces the current production
  amplitude law under an otherwise identical solver, so the two amplitude laws
  can be compared without any other variable changing.

### F1.1 — The `η` lattice-refinement law

- **Baseline.** Eq. (19): `β = β*(Δx/Δx*)^η`, with `Δx` **physical** spacing.
- **Motivation.** R2's claim that the numerical interface thickness remains
  constant across resolutions in *physical* space is exactly this law.
- **Expected effect.** At fixed resolution the law is inert; it needs two
  resolutions to calibrate `(β*, η)`.
- **Implemented now?** **NO (planned).** Parameter `eta` exists and is honoured,
  but the canonical lattice-unit matrix cannot calibrate it.
- **Switch/ablation.** `beta_ref=…` and `eta=…`; the report states plainly that
  `η` is **not determined** by this task's evidence, and that any later claim
  about it requires a two-resolution study. Not to be reported as validated.

---

## F2 — Later wetting boundary condition (Akai / Bijeljic / Blunt 2018)

- **Baseline (R1, Eqs. 30–33).** Rotate the colour-gradient **orientation** to
  form `θ_c` with `n_w`, preserving `|F|`; solve the degenerate condition with a
  two-step secant (`λ = 1/2`, stop at `n = 2`) restricted to the plane spanned by
  `n_c` and `n_w`; `n_w` from a 3-pass D3Q27-weighted smoothing of the binary
  solid mask.
- **Follow-up source.** DOI `10.1016/j.advwatres.2018.03.014` (R3).
- **Exact change.** R3 keeps the same philosophy (modify the gradient direction,
  preserve its norm) but replaces the degenerate secant with a **closed-form
  rotation**:
  - solid-site colour function extrapolated by a lattice-weighted average over
    the adjacent boundary-fluid nodes — R3 Eq. (2);
  - estimated interface normal `n* = −∇ρ_N*/|∇ρ_N*|` — R3 Eq. (3);
  - `n± = [(cos θ ∓ sin θ cos θ′)/sin θ′] n_s + [sin θ/sin θ′] n*`, with
    `θ′ = arccos(n_s·n*)`, and `n* ← n±` whichever has the shorter Euclidean
    distance — R3 Eq. (4).
- **Motivation (stated in R3).** R1's recurrence "would in principle require many
  iterations, which could increase computational costs"; R3 additionally reports
  that the fictitious-density BC (the one the current production line uses) is
  inaccurate in some cases and that its 3D extension is not obvious.
- **Expected effect.** A cheaper, non-iterative wall treatment with the same
  norm-preserving property; R3 reports improved agreement with analytic and
  experimental contact angles relative to the fictitious-density BC.
- **Implemented now?** **YES (switch), default off.** Selected by
  `wetting="akai"`; `L17_CORE` is `wetting="leclaire"`.
- **Switch/ablation.** Both arms run the same static-contact-angle and
  asymmetric-killer geometries. Attribute any difference to the wetting closure
  only, because nothing else differs between the arms.

---

## F3 — Later porous-media variant (Parmigiani et al. 2019)

- **Baseline (R1).** D3Q19; orientation-rotating wetting BC; recoloring that is
  exactly mass- and momentum-conserving by construction.
- **Follow-up source.** DOI `10.1155/2019/5176410` (R4).
- **Exact change (as documented in R4).** R4 works in a porous geometry with a
  D3Q15 lattice, drives the wetting phase with an external force, applies the
  wetting condition in its *simple per-node* form (dispersed phase treated as
  perfectly non-wetting, contact angle `180°`), and adds an **additional
  recoloring step** whose stated role is to preserve mass conservation
  ("the perturbation operator … is preserved by using an additional recoloring
  step"). It also notes that adopting the advanced wetting BC "would be
  necessary" if the dispersed phase were more wetting than the continuous one.
- **Motivation.** Application to transport-enhanced phase separation in porous
  media; the extra recoloring guards component mass under the perturbation.
- **Expected effect.** On the R4 use-case (one strongly non-wetting dispersed
  phase, forced wetting-phase flow) the simplified wetting treatment is adequate,
  and the extra recoloring reduces component-mass drift.
- **Implemented now?** **NO (planned).** Two reasons, both recorded rather than
  silent: (a) R4 is a D3Q15 application and its operator ordering is not stated
  at the equation level, so implementing it would mean reconstructing the
  ordering from a description rather than from equations; (b) the "additional
  recoloring step" is exactly the kind of un-sourced arithmetic addition that
  `LECLAIRE_IMPLEMENTATION_CONTRACT.md` §1 says must not be folded into a
  paper-faithful baseline.
- **Switch/ablation.** Reserved name `extra_mass_recolor`; if implemented later it
  must be a separate switch with its own evidence, and must never be enabled in
  an arm labelled `L17_CORE`.

---

## F4 — Regularized density / velocity open boundaries (R1 §II.D) — deferred core element

- **Baseline.** R1 Eqs. (21)–(29), with the variable-zero-weight generalisation
  `Υ⁽²⁾ = (c_s^k)²`, `Υ⁽⁴⁾ = λΥ⁽²⁾`, `λ = 1/3` for all four lattices.
- **Follow-up source.** None; this is part of the canonical paper and is listed
  here only because this task defers it.
- **Exact change vs current production.** The current line uses `feq`-overwrite
  density boundaries and velocity bounce-back boundaries with no
  stress-regularisation step.
- **Motivation.** R1 introduces these because the CGM's variable zero-velocity
  weight breaks the textbook assumption `Υ⁽⁴⁾ = c_s⁴`.
- **Expected effect.** At unit density ratio the generalisation is inert
  (`Υ⁽²⁾ = 1/3`, `Υ⁽⁴⁾ = 1/9`), so the *only* observable difference in this
  task's regime would come from the regularisation itself, not from the
  zero-weight correction.
- **Implemented now?** **NO (planned).** Rationale: a partially-correct
  open-boundary implementation would be a larger fidelity risk than an explicit
  omission, and none of the ten required canonical tests needs it.
- **Switch/ablation.** Reserved `open_bc="regularized"`. `L17_CORE` evidence is
  produced with periodic / no-slip / wall-bounded setups only, and the report
  states which tests would be invalidated if a regularized boundary were
  substituted later.

---

## F5 — Variable density ratio (`α_r ≠ α_b`)

- **Baseline.** R1 Eqs. (10)–(12) plus the `φ_i + ϕ_i α` term of Eq. (4).
- **Follow-up source.** None; canonical but out of the declared task scope.
- **Exact change.** `α` becomes a local density-weighted average instead of the
  constant `W0`, opening a genuine density ratio `γ = (1−α_b)/(1−α_r)`.
- **Motivation.** R1's stated purpose for the generalisation is to reach high
  density ratios; it is the reason the paper's equilibrium carries `φ_i/ϕ_i` and
  the reason `Υ⁽²⁾/Υ⁽⁴⁾` need generalising.
- **Expected effect.** Non-unit `γ` changes the interface equilibrium and makes
  the `ψ_i`/`ξ_i` density-gradient terms of Eq. (4) non-negligible.
- **Implemented now?** **NO (planned).** The contract's canonical set is
  unit-density-ratio; the constants `φ_i, ϕ_i, ζ` are already carried in the
  formulation so the extension is a switch, not a rewrite.
- **Switch/ablation.** Reserved `alpha_r`; `L17_CORE` fixes `alpha_r = W0` and the
  formulation proves the reduction (`PAPER_FORMULATION.md` §2.4).

---

## F6 — Project-specific conservation overlay

- **Baseline.** None — `L17_CORE` contains no project corrections by construction.
- **Follow-up source.** Not a paper. The project's own conservation line
  (`BI-SOLVER-CONSERVATION-FIX-001`, `BI-COLOUR-CLOSURE-001`).
- **Exact change.** The `T3` (f64 inverse-matrix / f64 accumulator),
  `C1X` (weighted colour closure) and `A2` (f64 colour pipeline) arithmetic
  overlay, in the shapes the production line uses.
- **Motivation.** The current line's interface-driven component-mass residual is
  a finite-precision effect of the equilibrium-based colour split
  (`CURRENT_VS_LECLAIRE_MAP.md` §A.9) and of the f32 matrix roundtrip.
- **Expected effect.** Reduces long-horizon component-mass drift to the
  f64-to-f32 store floor; does not change the physical model.
- **Implemented now?** **YES (switch), default off.** `conservation_overlay=None`
  is `L17_CORE`. `T3`-like f64 accumulation is available as an explicit overlay.
- **Switch/ablation.** `conservation_overlay ∈ {None, "f64_arithmetic"}`. The
  critical labelling rule from `LECLAIRE_IMPLEMENTATION_CONTRACT.md` §5: an arm
  that enables the overlay **must not** be reported as paper-faithful. The
  conservation audit therefore reports both arms side by side and labels the
  overlay arm accordingly.

**Note on independence.** The current line's defect was *diagnosed* before it was
corrected. The new line repeats that discipline: canonical test 10 measures the
raw `L17_CORE` component/total drift first, and only then is the overlay arm run
so that the overlay's contribution is attributable.

---

## Ablation matrix summary

| arm | F1 β | F2 wetting | F3 extra recolor | F4 open BC | F5 variable γ | F6 overlay |
|---|---|---|---|---|---|---|
| `L17_CORE` | paper (core) | `leclaire` | off | off | off | off |
| `L17_PLUS_AKAI` | paper | `akai` | off | off | off | off |
| `L17_PLUS_OVERLAY` | paper | `leclaire` | off | off | off | `f64_arithmetic` |
| `CURRENT_AMPLITUDE_ABLATION` | `min_variant` | `leclaire` | off | off | off | off |

`CURRENT_AMPLITUDE_ABLATION` is not a production candidate. It exists solely so
that F1's effect is attributable to the **amplitude law alone**, with every other
element held at `L17_CORE`.
