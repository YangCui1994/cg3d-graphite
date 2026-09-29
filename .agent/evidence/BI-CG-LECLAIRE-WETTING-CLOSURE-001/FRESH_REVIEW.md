# FRESH REVIEW — BI-CG-LECLAIRE-WETTING-CLOSURE-001 (Pass-5)

## Binding

- **Task ID:** `BI-CG-LECLAIRE-WETTING-CLOSURE-001`
- **Product branch:** `agent-task/BI-CG-LECLAIRE-IMPLEMENTATION-001`
- **Base:** `6c30260dfe0c8b61ea9609e6bffa5c487312cf06` (23 commits to the evidence tip)
- **Frozen Pass-5 source candidate:** `b65bdce3758dd967df1a3f5559c7014f97fd960b`
- **Pass-5 evidence / package tip:** `ad07b18c548a06babf385f0b33f13e52433234a4`
- **Control branch read (fast-forward):** `agent-dev/bilateral-episode-v0.1` @ `d606ad07a434e5316823a928ffed8f9d5ec61169`
- **Reviewer contract:** `.agent/episodes/bilateral-imbibition-v0.1/LECLAIRE_WETTING_CLOSURE_REVIEWER_CONTRACT.md`
- **Predecessors:** `.agent/evidence/BI-CG-LECLAIRE-PASS4-001/FRESH_REVIEW.md`, `.agent/evidence/BI-CG-LECLAIRE-PASS4-001/EXTERNAL_SCIENTIFIC_REVIEW_R3_CHANGES_REQUESTED.md`
- **Staging:** `D:/2026_agent_work/01_GLM_LBM3D_porous_media/.review_runtime/BI-CG-LECLAIRE-WETTING-CLOSURE-001/` (outside every git worktree)
- **Review mode:** `FRESH_SESSION` — executor transcript not read and not requested; the candidate and the evidence tree were not modified.

## Decision

**CHANGES_REQUESTED**

The scientific core of Pass-5 is real and I verified it independently: the wall-normal
convention now matches R1, the contact-angle instrument returns the liquid-side angle,
and the slit capillary-pressure test now has the correct sign and magnitude. The whole
matrix is reproducible from the frozen source with one command — my rerun reproduces
**311/311 metric fields bit-for-bit, 39/39 raw snapshots byte-for-byte, 11/11 verdicts**,
and the unit checks at 88/88.

The stage nevertheless cannot be closed as published, for two reasons that are
record-integrity rather than physics:

1. **Every generated artifact states the rejected wall-normal convention** while the
   frozen solver implements the canonical one. `SUMMARY.json`, `VALIDATION_REPORT.md`,
   three case READMEs and `case-04/metrics.json` all say
   `n_w = -grad(g) solid->fluid` — the very convention the external review R3-1 removed.
   Only the hand-written report prose is correct. The contract's section J requires one
   consistent current statement; the machine-readable record is currently false.
2. **case-08 is a misclassified invalid test, not a solver failure.** Its initial
   condition is not the "connected column" its own metadata and README claim, and the
   configuration cannot exhibit a Jurin rise at all: the tube mouth sits above the
   reservoir surface and the trapped gas of the closed box blocks the rise. I verified
   both statements from the committed raw fields and with a new two-arm experiment.

## Coverage

Inspected: the eight required documents; the complete `b65bdce..ad07b18` diff and the
commit chain `245d6e6 … ad07b18`; `experimental/leclaire_cg/{solver,geometry}.py`
diffs against the Pass-4 tip; `tests/leclaire_cg/{pass05,artifact,test_lattice_tables,verify_manifest_paths}.py`;
all eleven case `metrics.json` / `metadata.json` / `README.md` / `render_manifest.json`;
`SUMMARY.json`, `run_manifest.json`, `VALIDATION_REPORT.md`, `EXECUTION_REPORT.md`,
`VALIDATION_ATLAS.md`, `WETTING_PHASE_CONVENTION.md`, `SCIENCE_MASTERLINE.md`.

Recomputed (not read):

- the unit checks and the **entire Pass-5 matrix** from a byte-exact staged copy of
  `b65bdce` using the committed harness, into a staging results tree;
- the contact-angle contour, the circle fit and the liquid-side angle from the committed
  raw fields with my own extraction and my own least-squares fit (two independent
  estimators);
- the invariant `angle(F, n_w)` on the committed fields for both wall-normal signs,
  building `F`, the smoothed image `g` and `n_w` by hand;
- the slit meniscus shape, `Pc = p_gas - p_liquid`, its theory value and the
  z-invariance;
- the Jurin initial/final fields, the reservoir and capillary levels, and a **new
  two-arm experiment** on the same geometry with an immersed-tube initial condition;
- the mechanical-sigma observable from the retained `Ndist` snapshot, plus window and
  bulk-reference sensitivity;
- figure regeneration for six `fig1_field` figures and the three contact-angle wedge
  figures, compared pixel-by-pixel;
- the committed `reproduce.py` scripts by execution.

Not inspected: the executor transcript (forbidden); the production Taichi solver (out of
scope); the R1/R2 PDF internals beyond the `n_w` definition already established in the
previous round.

---

## A. Freeze binding — PASS

| check | result | evidence |
|---|---|---|
| frozen source is the harness that produced the run | PASS | `ad07b18^ == b65bdce`; the only commits between are the evidence commit itself |
| no source/harness/gate change between freeze and evidence | PASS | `git diff --name-status b65bdce ad07b18` = 2 modified docs (`VALIDATION_ATLAS.md`, `EXECUTION_REPORT.md`), the Pass-4 raw backfill (39 `A` `.npz`), the whole `pass-05/` tree, and run logs. No `experimental/**`, no `tests/leclaire_cg/pass05.py`, no gate, no geometry, no artifact-writer source change |
| one command reproduces the complete matrix | PASS | `python tests/leclaire_cg/pass05.py` from a byte-exact staged copy of `b65bdce` → `{'PASS': 8, 'FAIL_SOLVER': 3}`, **311/311 metrics.json fields bit-identical**, **39/39 raw npz byte-identical**, verdicts identical |
| no case-specific post-freeze patch or selective rerun | PASS | there is one evidence commit, it is a pure child of the freeze, and the harness file is unchanged across it; my single-command rerun (no per-case invocation) reproduces every case |
| raw-schema and environment recorded | PASS | `raw_schema_version l17c_core_raw_v1`, `candidate_sha b65bdce…`, `command python tests/leclaire_cg/pass05.py` |
| isolation invariants | PASS | `lbm_solver_cg3d.py` blob `1b7db4ac…` identical at base, freeze and tip; the only non-added file `base..tip` is `.gitignore` (+6 lines) |

Note for the record: the declared freeze is the *third* Pass-5 source commit
(`9ed10aa` → `fd5ab42` → `b65bdce`). That is compatible with R3-6, which asked for a new
frozen candidate *after* the harness fixes; what matters is that no source change occurs
after `b65bdce`, and that is verified.

## B. Canonical wetting convention — PASS in code, FAIL in the artifact metadata

Verified against the source tree:

| element | required | as implemented | verdict |
|---|---|---|---|
| `red = liquid`, `blue = gas` | yes | `psi = (rho_r - rho_b)/rho`, `+1` is red | AGREE |
| `F = grad(psi)` gas → liquid | yes | `op.gradient(psi, …)`, unit-checked | AGREE |
| `g = 1` solid, `0` fluid | yes | `smooth_solid()` on the binary mask | AGREE |
| `n_w = +grad(g)/|grad(g)|` fluid → solid | yes (R1 §II.E / Eqs. 34-38) | `solver.py` default `nw_sign = +1.0`; `nw_sign_override` only as a labelled debug switch | AGREE |
| `theta = theta_liquid` | yes | `cos(theta_liquid) = -(z_c - z_w)/R` in `geometry.py`, with a tangent-based derivation | AGREE |

The Pass-4→Pass-5 source diff is exactly the fix and nothing else:
`experimental/leclaire_cg/solver.py` (one default: `-1.0` → `+1.0`, comment rewritten),
`experimental/leclaire_cg/geometry.py` (circle-fit sign + derivation),
`tests/leclaire_cg/artifact.py` (`script` string, new `fig_contact_angle`). `operators.py`
and `lattice.py` are untouched.

**Independent confirmation from the committed raw fields.** I rebuilt `F`, the smoothed
`g` and both candidate normals by hand and evaluated `angle(F, n_w)` at the wall sites of
the case-04 final states:

| prescribed | `n_w = +grad(g)` (canonical) | `n_w = -grad(g)` (Pass-4) |
|---|---|---|
| 60° | mean 62.4° / median 67.9° | mean 117.6° / median 112.1° |
| 90° | mean 88.1° / median 88.4° | mean 91.9° / median 91.6° |
| 120° | mean 109.2° / median 108.2° | mean 70.8° / median 71.9° |

The canonical branch is the one that reproduces the prescribed liquid-side angle; the
negated branch returns its complement.

**The analytic lock is no longer circular** (contract B, "reject circular tests",
external R3-2). `test_lattice_tables.py` now builds the reference cap from the interface
tangent (`C = (0, z_wall + R·N_z)` with `N = (-sin t, -cos t)`), verifies the
*construction itself* with a chord-angle check independent of both the fit and the
centre relation (residuals 0.06–0.13° against a 0.6° bound), asserts that the reversed
sign returns the complement, asserts that `-grad(g)` is rejected, and drives the R1
secant from three starting branches (including the complement) to `angle(F, n_w) = θ`.
All five angles 30/60/90/120/150 pass; my rerun log is structurally identical to the
committed one; 88/88.

**But the published metadata contradicts this.** See blocking finding **W-1**.

## C. Contact angle (case-04) — PASS, independently reproduced

| prescribed | driver | my own contour + own fit | independent `2·atan(h/a)` |
|---|---|---|---|
| 60° | 65.19 | 64.85 | 63.29 |
| 90° | 95.70 | 96.29 | 91.19 |
| 120° | 129.40 | 128.99 | 112.48 |

Errors ≤ 9.4° against the 15° gate; fit quality `fit_rms_geom` 0.035 / 0.050 / 0.072 lu
against a 0.30 bound. The physical configuration flipped as it must: for prescribed 60°
the fitted centre is now **below** the wall plane (`z_c = -3.83`, cap `h/a = 0.62`), a
spreading liquid film, where Pass-4 produced a bead (`h/a = 1.79`, angle through the
liquid ≈ 126°). The three committed wedge figures (`fig_cap_theta{60,90,120}`) regenerate
from the tracked raw fields: 90° and 120° pixel-identical, 60° with `max|d| = 1`.

## D. Slit capillary pressure (case-07) — PASS, independently reproduced

Geometry re-verified from the raw mask and field: plates transverse to the meniscus
(normals ±y), interface intersecting both plates, `x` sealed at both ends, and
`max|psi(z=kz) - psi(z in {3,5,7,9})| = 0.000e+00` — exactly z-invariant, so there is no
hidden periodic second interface.

| prescribed | my `Pc = p_gas - p_liquid` | `2 σ cos θ / h` | ratio | meniscus near-wall vs centre |
|---|---|---|---|---|
| 60° | **+2.032e-03** | +2.000e-03 | +1.016 | 13.765 vs 13.096 (advances at the wall) |
| 90° | -1.99e-08 | ~0 | — | 13.500 vs 13.500 (flat) |
| 120° | **-2.141e-03** | -2.000e-03 | +1.071 | 13.223 vs 13.932 (recedes at the wall) |

Signs, magnitudes and the meniscus deformation direction are now all correct — the
mirror image of the Pass-4 result. Per the contract's section D, a sign failure would
have been a solver/convention failure; there is none.

## E. Jurin (case-08) — the verdict is misclassified and the documentation is wrong

The case reports `FAIL_SOLVER` with `capillary_interface_exists = false`,
`rise = NaN`, and the classification note "contract E3: precheck passed but the tube
emptied -> physical/numerical failure reported directly". The raw fields do not support
that attribution.

**(a) The initial condition is not the one the artifacts describe.** From the committed
`raw/t0000.npz`, the capillary centre column `z = 16…20` reads
`[-1, -1, +1, +1, -1]`: liquid exists only in the 2-lu blob at `z = 18,19`; `z = 14…17`
is gas between it and the reservoir surface at `z ≈ 13.5`. The metadata and README state
"liquid column continuous from reservoir into capillary" and "a connected column inside
the capillary". Both are false for the committed initial state.

**(b) No liquid ever enters the tube.** At `t_mid` and `t_final`, the fraction of
`psi > 0` cells is **0.000 at every layer `z ≥ 16`** across the full cross-section, not
merely on the probe column; the free surface settles at `z ≈ 15`, three lu *below* the
tube mouth at `z = 18`.

**(c) The reachability precheck cannot detect this.** It verifies only that the
volume-conservation levels `M = 13.22`, `L = 21.56` lie inside the measurement windows.
It never checks that the liquid can physically reach the mouth (`M < neck = 18`) or that
a closed box can support the column.

**(d) A new two-arm experiment (geometry and physics identical, initial condition only
changed) shows the configuration cannot work at all.** With the tube immersed
(`psi = +1` for `z < 24`) arm A holds `tube_liquid_frac = 0.1042` from `t = 0` to
`t = 3000`; with the tube additionally pre-seeded to `z = 26`, arm B holds `0.1375`
unchanged. **The meniscus does not move.** The reason is the closed box: pushing liquid
into the tube compresses the trapped, essentially incompressible gas
(`p0 = 1/3`, `A_cap = 160`, `V_gas ≈ 7360`), giving a back-pressure slope of
`≈7.3e-3` per lu against a capillary drive of only `2.5e-3`, i.e. a rise limited to
`≲ 0.33 lu` where the theory asks for `8.33 lu`. The sub-lattice rise is exactly what the
immobile probes show.

So the observed outcome is a property of the test configuration (disconnected initial
state; tube mouth above the free surface; trapped gas), not of the wetting closure —
which cases 04 and 07 independently demonstrate to be working. The correct label is
`INVALID_TEST` / `INVALID_CONFIGURATION`.

## F. Raw artifacts — PASS

- 39 raw `.npz` are committed at the evidence tip and tracked; `verify_manifest_paths.py`
  reports 36 referenced paths, 0 missing, 0 ignored.
- All 16 distinct `source_raw` paths referenced by the Pass-5 manifests resolve to
  committed files.
- Figures regenerate from the tracked raw: **6/6 `fig1_field` PNGs pixel-identical**
  (cases 03, 04, 05, 07, 08, 09) once the manifest's own plane/index and the driver's
  title are used, plus `fig_cap_theta{90,120}` pixel-identical and `fig_cap_theta60` at
  `max|d| = 1`.
- The Pass-4 raw backfill (39 files added at the evidence commit) is the genuine set:
  the Pass-5 raw files regenerate the Pass-5 figures, and the on-disk Pass-4 raw set is
  the same 39-file set that the Pass-4 manifests reference.
- One manifest field is stale: `script_version: "pass-04"` in all 36 entries, while
  `script` correctly says `pass05.py`.

## G. Full regression — PASS

- Unit checks: **88/88** from the frozen source, log structurally identical to the
  committed `pass-05/UNIT_CHECKS.log`.
- Full matrix: one command, 11 cases, `{'PASS': 8, 'FAIL_SOLVER': 3}`.
- **311/311 metric fields bit-identical** (not "close" — `==`), across all eleven cases.
- **39/39 raw snapshots byte-identical** (SHA256) between my rerun and the committed tree.
- Representative figures regenerated as in section F.
- The previously broken binding (`0b3da4e` could not run its own harness) is genuinely
  fixed: the named candidate runs the whole matrix.

## H. Preserved science — PASS

The `ca10d65 → b65bdce` diff touches only the three files listed in section B. Therefore
`operators.py` (Eq. (4) with the `u·grad(rho)` term, the `X_W` 1-D Cartesian wall
gradient, the unrelaxed post-collision perturbation, `A = (9/4) ω_eff σ`, the explicit-β
recolouring) and `lattice.py` (D3Q19 tables, MRT basis) are byte-identical to the Pass-4
candidate that was already accepted on those points. The unit checks that lock each of
them (A1–A4 at non-zero `u` and `grad rho`, `perturbation.A_equals_9over4_omega_sigma`,
`grad_l17.*`, the recolouring conservation identities) pass at 88/88, and the f64
conservation cases (case-10) are unchanged in my rerun.

## I. Mechanical sigma (case-11) — premises now closed; PASS is defensible, the atlas text is not

R3-7's four required items are all implemented: the full `N_i` distribution is retained
(`Ndist`, shape `(6,6,64,19)`), exactly one interface is isolated by a window located from
the phase field, the bulk reference window sits between the two interfaces, and the
discrete total-variation consistency is reported.

My independent recomputation from the retained `Ndist` gives
`sigma_mech = 0.019999960` (ratio 0.999998) against the committed 0.999995 — the small
difference is the f32 storage of the snapshot. The result is insensitive to the
integration window and to the bulk window within the bulk region (ratios within 0.03 %),
and degenerate when the bulk window straddles the interface (ratio −2.71), which is the
expected behaviour of the estimator. The verdict rule in the harness is explicit:
`PASS` only when the premises close and the ratio is inside the predeclared band,
otherwise `EXPLORATORY_UNGATED`.

Caveat, recorded rather than counted as a defect: this observable is close to an
algebraic identity (Σ(P_N − P_T) = (2/9)A·Σ|F| and Σ|F| ≈ TV = 2), so it verifies the
implemented moment prefactor on a relaxed monotone profile rather than measuring an
independent surface tension. The comparison that matters for the open Laplace question
now reads: mechanical ≈ 1.00 σ_input versus Laplace ≈ 1.127 σ_input — still no uniform
prefactor, but a 13 % gap rather than the 47 % Pass-4 reported.

## J. Durable science documents — PARTIAL

Correct and current:

- `EXECUTION_REPORT.md` §0 gives the right convention (`n_w = +grad(g) fluid->solid`),
  the frozen SHA, the 88/88 and the `{'PASS': 8, 'FAIL_SOLVER': 3}` counts, and banners
  everything below it as superseded.
- `VALIDATION_ATLAS.md`'s Pass-5 section repeats the same and states the Pass-4
  convention error correctly as history.
- The stale closing paragraph of `REFERENCE_MANIFEST.md` (R3-9's first item) is gone.
- `SCIENCE_MASTERLINE.md` and `WETTING_PHASE_CONVENTION.md` state the canonical
  convention and supersede the Pass-4 choice.

Still wrong:

- **W-1** (blocking): the generated artifact metadata states the *rejected* convention.
- **W-4** (non-blocking): `PROVENANCE.md` still contains R3-9's second stale sentence,
  and `PROVENANCE.md` / `summary.json` / `UNIT_CHECKS.log` still carry Pass-3 numbers with
  no in-file superseded banner; `pass-05/VALIDATION_REPORT.md` declares
  `stage: BI-CG-LECLAIRE-PASS4-001` while `SUMMARY.json` says
  `BI-CG-LECLAIRE-WETTING-CLOSURE-001` — two "current headline" files disagree.

---

## Findings

### Blocking

**W-1 — every generated Pass-5 artifact states the wall-normal convention that the frozen
solver does not use.**

The frozen source runs `nw_sign = +1.0`, i.e. `n_w = +grad(g)/|grad(g)|` (fluid → solid),
which is R1 and which the report prose states correctly. The following artifacts state
the negation (solid → fluid), i.e. the convention external review R3-1 rejected:

| artifact | location | text |
|---|---|---|
| `pass-05/SUMMARY.json` | `convention` | `n_w=-grad(g)/|grad(g)| solid->fluid; theta through liquid/red` |
| `pass-05/VALIDATION_REPORT.md` | line 7 and line 86 | same / `n_w = -grad(g)/|grad(g)| (solid->fluid)` |
| `pass-05/case-04-contact-angle/README.md` | `wetting convention` | `n_w = -grad(g)/|grad(g)| solid->fluid` |
| `pass-05/case-07-…/README.md`, `case-08-…/README.md` | `wetting convention` | same |
| `pass-05/case-04-…/metrics.json` | `wall_normal` | `n_w = -grad(g)/|grad(g)|  (solid->fluid)` |
| `pass-05/case-04-…/metadata.json` | `wall_normal_sign` | `-1` |
| `tests/leclaire_cg/pass05.py` | lines 391, 403, 674, 806, 1209 | the hardcoded strings that generate all of the above |

Consequences: the machine-readable record of the current pass contradicts the code and
the prose; an automated reader (or the promotion gate of `VALIDATION_ARTIFACT_SPEC.md`
§12) consumes the false version; and the one confusion this entire task line exists to
eliminate — which sign of `grad(g)` is canonical — is reintroduced in the evidence.
Section J of the reviewer contract requires one consistent current statement, so this
cannot be waived as cosmetic. The fix is five strings in the harness plus a regeneration
of the Pass-5 artifact tree.

**W-2 — case-08 is not a solver failure; it is an invalid test with a documented
misdescription of its own initial condition.**

Established in section E: the initial state is two disconnected liquid bodies (gas
between `z ≈ 14` and `z ≈ 18`), contrary to the "connected column" claim in
`metadata.json` and the README; no liquid ever enters the tube; and a new two-arm
experiment shows the meniscus cannot move in this closed box because the trapped gas
back-pressure (`≈7.3e-3` per lu) dwarfs the capillary drive (`2.5e-3`), capping the rise
at `≲0.33 lu` against a theoretical `8.33 lu`. Reporting this as `FAIL_SOLVER` with the
classification note "precheck passed but the tube emptied -> physical/numerical failure"
attributes a test-design defect to the solver and would permanently mislead the closure
record. It should be `INVALID_TEST` / `INVALID_CONFIGURATION`, with the reachability
precheck extended to require that the liquid can actually reach the mouth (equivalently
that the free surface stays above `neck`), or the geometry re-scoped (see the owner
question below).

### Non-blocking

**W-3 — all eleven per-case `reproduce.py` scripts are broken.** Each contains
`import pass04` / `pass04.run_one(idx, …)`, and `tests/leclaire_cg/pass04.py` does not
exist at the evidence tip. Executing the committed `case-04-contact-angle/reproduce.py`
raises `ModuleNotFoundError: No module named 'pass04'`. Root cause:
`artifact.Case.write_reproduce` hardcodes the module name. This violates
`VALIDATION_ARTIFACT_SPEC.md` §5.1 ("exact figure-generation script"), §8 and §11.

**W-4 — the R3-9 durable-record cleanup is half done, and two headline files disagree.**
`REFERENCE_MANIFEST.md`'s stale sentence is removed, but
`results/leclaire_cg/PROVENANCE.md` ("Known weaknesses" item 4) still says R5 was obtained
"by local search rather than download", contradicting the corrected 科研通 statement 65
lines above it in the same file; the same file, `summary.json` and `UNIT_CHECKS.log`
carry Pass-3 numbers with no in-file superseded banner; and
`pass-05/VALIDATION_REPORT.md` names the wrong stage (`BI-CG-LECLAIRE-PASS4-001`).

**W-5 — the atlas contradicts the mechanical-sigma verdict.** The Pass-5 atlas section
says case 11 "does not contribute a validating verdict", while the case's own verdict is
`PASS` and it is counted in the headline's `PASS 8`. Both statements cannot be current.
Related: `script_version: "pass-04"` in all 36 manifest entries, and the harness docstring
still says it writes into `results/leclaire_cg/pass-04/`.

**W-6 — case-09's `FAIL_SOLVER` remains unattributed.** Its wall-band gate fails at
−6.83 % with an explicit "NOT attributed to wall mass transfer; no stationary reference
case was run" note, while global excursions are at f64 roundoff. The number is
bit-identical to Pass-4, so it is not convention-driven. The label is defensible under the
harness rule but sits uneasily with the withheld attribution; the report should state
that limit rather than list it as a bare solver failure.

**W-7 — `verify_manifest_paths.py` does not verify what it claims.** Its docstring says
each `source_raw` "exists, is tracked and is reachable from the evidence commit"; it
actually runs `git check-ignore`, which passes for any file that is neither ignored nor
tracked. The Pass-5 raw set is in fact tracked (I verified with `git ls-files`), so no
false negative occurred — but the check is weaker than advertised.

**W-8 — `sigma_extrapolated_large_R` is still mislabelled** (carried from Pass-4 P4-8).
It is the slope of `sigma_local` against `R_measured` (units σ/length), not a `1/R → 0`
limit, yet the README prints it in a row labelled `sigma_extrapolated(1/R->0)` with an
"error" column. No stable infinite-radius extrapolation exists.

---

## Answers to the questions the contract asks

**Is the frozen source the harness that produced the evidence, and does one command
reproduce the matrix?** Yes. `ad07b18^ == b65bdce`, no source or gate changes across the
evidence commit, and my single-command rerun reproduces 11/11 verdicts, 311/311 metric
fields and 39/39 raw snapshots exactly. The Pass-4 binding defect is genuinely closed.

**Is the canonical wetting convention implemented?** Yes — `+grad(g)` fluid → solid,
`theta = theta_liquid`, non-circular analytic locks at 30/60/90/120/150 — but the
generated artifact metadata states the opposite (W-1).

**Do the contact-angle results validate the Leclaire wetting condition?** Yes, at the
level this stage claims: 65.2 / 95.7 / 129.4° for 60 / 90 / 120° prescribed, reproduced by
two independent estimators, with the liquid film (not a bead) now the realised
configuration. The residual 5–9° bias is systematic and worth recording but inside the
predeclared gate.

**Is the slit Pc test valid and does it pass?** Both yes. Transverse plates, real contact
lines, sealed ends, exact z-invariance, correct `Pc` sign and 1.6–7 % magnitude, and the
meniscus deforms the right way at 60° and 120°.

**Is the Jurin test valid and does it pass?** No to both, and the failure is the
configuration's, not the solver's (section E, finding W-2).

**Is the mechanical-sigma observable now recomputable and its premises closed?** Yes: I
recomputed it from the retained `Ndist` and reproduced the ratio to 3e-6; the window and
bulk choices are robust; the TV consistency closes. It remains, scientifically, a
consistency check of the implementation's moment prefactor rather than an independent σ
measurement, and the atlas should describe it that way (W-5).

**Are the raw artifacts durable?** Yes — committed, tracked, referenced and
figure-regenerating — with the one stale `script_version` field and the broken
`reproduce.py` scripts (W-3).

**Are the durable documents consistent?** Not yet: correct in the report and atlas,
wrong in every generated metadata artifact (W-1), with the R3-9 leftovers (W-4).

**Is the NumPy/f64 wetting-reference stage closed?** **No.** The formulation, the
convention, the instrument and two of the three wetting validations are closed and
independently verified — that is a large, real advance over Pass-4. What remains is
record integrity (W-1), one misclassified invalid test with a false initial-condition
claim (W-2), and the small artisan defects W-3…W-8.

---

## Owner question to resolve before the next round

The Jurin item cannot be closed inside the current closed box. Two options, both
compatible with the rest of the stage:

1. **Keep the closed-box design and re-scope the claim.** State that this stage validates
   static wetting (contact angle, slit `Pc`) and does not validate Jurin: mark case-08
   `INVALID_TEST` with the gas-compression reasoning, drop the rise from the closure
   claim, and record the trapped-gas limit as the reason. Cheapest, and honest.
2. **Give the gas somewhere to go.** Implement a constant-pressure gas boundary (a
   partial step towards R1 Eqs. (21)–(29), which remain out of scope) or enlarge the gas
   reservoir until `p0·ΔV/V_gas ≪ 2σcosθ/h`, then rerun the same geometry with an immersed
   initial condition. This is the only route that produces a quantitative Jurin result in
   this line.

I am not able to choose between them on the evidence; both are legitimate, but the second
is a scope extension that the current contract excludes.

## What should be preserved

1. the freeze discipline itself — one source SHA, one command, no post-freeze patches;
2. the convention fix and the non-circular analytic lock suite at 30/60/90/120/150;
3. the corrected circle-fit relation together with its tangent-based derivation;
4. the slit-Pc geometry and its now-correct sign/magnitude result;
5. the contact-angle wedge figures and the raw→figure binding;
6. `A = (9/4) ω_eff σ` untuned, and the Laplace FAIL preserved as an open calibration;
7. the retained `N_i` distribution and the premise-gated mechanical-sigma rule;
8. the f64 conservation result and its explicit backend scope limitation;
9. the Pass-5 report/atlas headline structure, once W-1's strings are corrected.

## Declaration

- Fresh, independent reviewer session; the executor transcript was not read or requested.
- Neither the frozen candidate nor the evidence tree was modified. Every run wrote into
  `.review_runtime/BI-CG-LECLAIRE-WETTING-CLOSURE-001/`, outside every git worktree.
- No GPU work, no Taichi execution, no production run.
- Files written by this review: this file and `FRESH_REVIEW_SESSION.json`, published to
  `.agent/evidence/BI-CG-LECLAIRE-WETTING-CLOSURE-001/` on
  `agent-dev/bilateral-episode-v0.1`.
- `PASS` was not available: the machine-readable convention record is false (W-1) and one
  wetting case is misclassified with a false initial-condition claim (W-2). `HUMAN_REQUIRED`
  was considered and is not triggered — the corrections are determined, and the one genuine
  scope decision (the Jurin re-scope) is stated above for the owner rather than blocking the
  review.
