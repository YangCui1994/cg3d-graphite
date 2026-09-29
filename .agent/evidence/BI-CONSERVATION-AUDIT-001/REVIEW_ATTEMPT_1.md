stage: conservation-audit
attempt: 1
candidate: 24b00dbe28d23c12049d05679542301ccc507eac
execution_report: results/conservation_audit/EXECUTION_REPORT.md

# REVIEW — BI-CONSERVATION-AUDIT-001

## Review Mode

`FRESH_SESSION` (independent reviewer session; executor transcript not read).

## Coverage

Inspected:

- task: `.agent_runtime/BI-CONSERVATION-AUDIT-001/REVIEW_REQUEST.md`,
  `CONSERVATION_AUDIT_CONTRACT.md`, `CONSERVATION_AUDIT_REVIEWER_CONTRACT.md`,
  control review `BI-V2-BILATERAL-001/V2_EXTERNAL_SCIENTIFIC_REVIEW_PASS.md` (R-V2-3);
- candidate worktree `cg3d-episode-worktrees/BI-CONSERVATION-AUDIT-001`
  (git identity, worktree state, full diff vs base, solver source);
- driver `tests/conservation_audit.py` (all 647 lines, read in full);
- solver `lbm_solver_cg3d.py` kernel order and arithmetic (docstring, tables,
  `init`, `Compute_C`, `Compute_S_local`, `multiply_M`, `collision`,
  `streaming1`, `Boundary_condition`, `Boundary_condition_psi`,
  `streaming3`, `step`);
- evidence: `MANIFEST.json`, `PROVENANCE.md`, `summary.json`,
  `backend_comparison.csv`, `scaling_results.csv`,
  `late_window_identities.json`, all 10 `<tag>/` CSV/JSON sets, `logs/`,
  `run_batch.sh`, `spatial_budget.csv`, `symmetry_check.json`;
- V2 comparison numbers in `.agent/evidence/BI-V2-BILATERAL-001/`
  (population 9.21e-4/60k, colour 5.47e-4);
- planned document `docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`
  (structure, §2/§16/§17/§18/§19/§21.7/§22/§23, figure convention).

Independent recomputation performed (host-side, numpy f32/f64 only, no
solver execution, no GPU):

- refit of all slopes/R² for Mff, Mc=Mr+Mb, Mrho in all 10 runs;
- late-window (20 rows) and all-traced J1/J7/J6 statistics in all 10 runs;
- exact-zero scan of J0/J2/J3/J4/J5/J8 and J9 closure over all 10 runs;
- S6(n)==S0(n+1) closure directly from `substep_mass_trace.csv`;
- spatial-budget region sums vs horizon deltas, per-node rates;
- first-material checkpoint scan (1e-6 relative);
- full MANIFEST SHA256 verification (84 artifacts) + driver hash;
- transcription-verified reproduction of the production collision
  arithmetic in f32 (M, `multiply_M` order, `meq_vec`, `S_local`, inverse
  transform, feq pair sum, recolouring, atomic-order accumulation).

Not inspected / not done:

- executor conversation transcript (prohibited);
- `.agent_runtime/.../reviewer_session_stdout.log` (session stdout, not used);
- V1/V1b/V1c product evidence beyond the V2 drift numbers quoted above;
- `fields_t0.npz` / `fields_ref.npz` element-wise (only via budget sums);
- no simulation was re-run (not needed; no authorization; no GPU used).

## Requirement Review

| Req (contract §9/§12) | Status | Evidence / reason |
|---|---|---|
| R1 all four C0–C3 cases run | PASS | 10 runs, per-run `case_report.json` complete; `C3_gpu` horizon reaches step 20000 (101 rows), wall 350.9 s == log 350.9 s |
| R2 per-kernel sub-step trace per case | PASS | 40 traced steps × S0–S6 per run in `substep_mass_trace.csv`; driver order == `step()` (`lbm_solver_cg3d.py:819-828`) |
| R3 M_f / M_c / M_ρ compared explicitly | PASS | `d_fc/d_frho/d_crho` in `identities.csv` + `long_horizon_mass.csv`; recomputed |
| R4 first nonzero cross-representation checkpoint | PASS | C1_gpu 200, C3_gpu 400, C1_cpu 400, C3_cpu 600 (d_fc, d_crho); `d_frho` never material (max 2.21e-9 rel) — all reproduced |
| R5 C3 spatial budget | PASS (numbers) | region sums == horizon deltas to ≤1.1e-9; nodes sum to 28800; region asserts in driver `:476-478` |
| R6 backend/precision comparison | PASS | C0/C1/C2/C3 on gpu+cpu; C3 1.5556e-8 (gpu) vs 1.5173e-8 (cpu), both R²>0.999, recomputed |
| R7 scaling probe | PASS | C0 16/24/32; C3 horizon 5k/10k/15k/20k; recomputed (Mff increments 7.76/7.90/7.84e-5 per 5k) |
| R8 no solver source change | PASS | `git diff 5e679d8 24b00db -- lbm_solver_cg3d.py cg3d/` = 0 lines; diff is 74 files = `tests/conservation_audit.py` + `results/conservation_audit/**` |
| R9 evidence set (§12) | PASS with gaps | all required files present; 84/84 MANIFEST hashes verify, driver hash matches committed file; gaps: batch shell exit codes not persisted, `late_window_identities.json` has no committed generator and omits the 3 C0 GPU runs |
| R10 candidate binding | PASS | HEAD 24b00dbe28d23c12049d05679542301ccc507eac on `agent-task/BI-CONSERVATION-AUDIT-001`; worktree clean; base 5e679d8 is ancestor; single commit; `git ls-remote` matches |
| R11 producer revision valid | PASS with caveat | `prov.json` records head = base `5e679d8` + dirty (untracked driver/evidence) — disclosed in PROVENANCE; closed by driver SHA256 equality, not by commit |

## Validation Review

| Validation | Status | Notes |
|---|---|---|
| 10 audit runs (logs, `prov.json`) | PASS | all `<tag>/case_report.json` internally consistent; no NaN; `solid_residue` = 0; C3 mirror checks True; wall times match logs |
| `analyze` aggregation | PASS | `summary.json`, `backend_comparison.csv`, `scaling_results.csv` reproduced by my own refit (max slope deviation 1.35e-17) |
| Exact identities J0/J2/J3/J4/J5/J8 | PASS | bitwise 0.0 in all 10 runs × 40 traced steps (independent scan) |
| J9 closure S6(n)==S0(n+1) | PASS | max = 0.0 over 38 consecutive pairs per run; `closure_fail_steps` = 0 in all runs → decomposed step ≡ production `step()` |
| Reviewer mechanism reproduction (new) | PASS | host f32 model reproduces the audit's own C0 jumps exactly (+2.682209e-07, +7.450581e-08, cum +3.427267e-07, then exactly 0) and predicts the C3 rates within 4% (see Findings) |
| Bounded-floor hypothesis | NOT_SUPPORTED | no bounded scaling exists: C3 drift linear in T with 100% per-step sign bias; C0/C2 "zero" applies to the *slope* only (see B1) |

## Findings

### Blocking

**B1 — Decisive claim in required answer Q4 is false and is contradicted by
the candidate's own artifact.** The report states "the uniform-state floor
is exactly zero (C0), which a bounded-precision explanation cannot
produce". `backend_comparison.csv` (and `case_report.json:drift_fits`) show
`final_rel_Mff = final_rel_Mc = final_rel_Mrho = +3.427267e-07` for
`C0_16_gpu`, `C0_24_gpu`, `C0_32_gpu` and `C2_gpu`, and
`+3.427267e-07` (colour) for `C0_24_cpu`, `C2_cpu`. My host-side
reproduction of the production arithmetic shows this mass is *created by
f32 precision* in the first two steps of the uniform run and then stops
because the state becomes a bit-exact fixed point (iteration deltas
+2.682209e-07, +7.450581e-08, cumulative +3.427267e-07, then exactly 0.0 —
identical to the audit's step-0/step-1 J1 and final offset). The
isolation-matrix cells "C0 … 0 (bit-exact)" are also only true under the
table's "fitted drift slope" heading, and `R²=1.00000` there is the driver's
zero-variance fallback (`tests/conservation_audit.py:419-421`), not a fit
quality. Consequence: the argument used to exclude a precision reading is
invalid as written. The *conclusion* (no bounded floor) survives on the
other evidence (unbounded linear accumulation, 100% sign bias), but the
report must say so on the correct grounds.

**B2 — The claimed colour-gradient/interface dependence of the collision
defect is falsified by independent recomputation.** The report attributes
J1 to "residues [that] multiply the surface-tension/non-equilibrium moment
components that exist only at diffuse interfaces (`meq[1,9,11,13,14,15] +=
CapA*cc` terms)". My transcription-verified f32 model of
`collision()`/`multiply_M`/`inv_M` (M@feq vs closed form 4.44e-16) gives a
per-node mass gain that is essentially *independent* of the colour-gradient
strength: mean +1.368e-08 at cc = 0 → +1.398e-08 at cc = 0.20. The dominant
systematic term is the stored f32 inverse matrix itself:
`Σ_s inv_M[s,0] = 1 + 1.490116e-08` (i.e. `inv_M` is not a zeroth-moment-
conserving inverse in f32; `lbm_solver_cg3d.py:115` is the only place it is
built). That single number predicts the measured per-step relative drift:
predicted +1.49e-08/step vs measured C3_gpu +1.5556e-08 and C3_cpu
+1.5173e-08 (+4.4% / +1.8%). The report's other sub-claim ("`inv_M` is the
f64 inverse cast to f32") is confirmed; the interface-moment story is not.
The interface's real role is indirect: it sustains persisting
non-equilibrium, which keeps the state off the kernel's bit-exact fixed
point (exactly why C0 freezes and C1/C3 do not).

**B3 — Fix scope (§11 required element) is partly ineffective as written.**
Candidate (a) "f64 intermediate accumulation for the moment roundtrip", read
as an f64 accumulator with the stored f32 matrix, does **not** remove the
bias: my decomposition gives mean defect +1.496e-08 with `frac_pos = 1.00`
(f32 matrix + f64 accumulator) versus 2.7e-17 with a fully f64 roundtrip.
The effective minimal scopes are (i) carry the moment roundtrip in f64
(matrix *and* accumulator) or (ii) apply an exact per-node zeroth-moment
correction to the reconstructed `f` (variant (b) as proposed). For the
colour channel the audit lists three co-equal causes; measured weights at
realistic splits are: `feq` pair sum +1.508e-08 (dominant, matches the
traced J7 mean +1.51e-08), recolouring pair arithmetic
`(a+c)+(b-c)-(a+b)` +8.3e-11 (~300× smaller), f32 accumulation order
zero-mean noise with a small bias (+1.4e-09 rel). A fix task scoped to the
recolouring or the atomics would miss the actual term.

**B4 — §6 caution violated: causality inferred from the spatial budget.**
The report writes the leaked mass is "consistent with creation at the
interfaces during collision followed by streaming into the bulks". Contract
§6 forbids inferring causality from the budget alone, and the budget does
not support locality: per fluid node over the ref1000 window the leak is
+2.07e-04 (gas bulk, 17880 nodes), +4.81e-04 (liquid bulk, 8520), +2.44e-04
(wall rows, 1440), +3.43e-04 (interface band, 960) — i.e. comparable
everywhere, with 92% of the leaked mass in the bulk regions and the
interface band and wall rows *not* "~0" on a per-node basis. These
per-node rates agree with a node-wise arithmetic residue (B2), not with
interface-localized creation. The budget numbers themselves are correct
(ΣdMf = +8.4827 == horizon delta to 1.1e-09; ΣdMc = +4.6094; ΣdMrho
consistent).

**B5 — Non-reproducible quantitative claim (§Scaling, interface-area
normalization).** "leak per interface-band node per step (rate x N /
960-band): C1_gpu 3.4e-4, C3_gpu 4.7e-4" cannot be reproduced from the
committed artifacts: that formula yields 4.0e-7 (C1) and 4.7e-7 (C3); the
quoted numbers are ~10^3 larger and only match `rate×N/band` if C1's band is
assumed ≈1152 nodes, a value that is not committed (only C3 has
`spatial_budget.csv`). The 1.4× C1→C3 ratio is therefore not independently
verifiable as written.

### Non-blocking

- N1 `PROVENANCE.md` says "numpy 1.26.x"; every `prov.json` records 2.2.6.
- N2 Per-run shell exit codes are asserted ("all exit code 0") but the
  `run_batch.sh` stdout lines carrying `exit=$ec` are not committed; the
  per-run logs hold only the python output.
- N3 `late_window_identities.json` has no committed generator (not written
  by the driver or `analyze`) and omits `C0_16_gpu/C0_24_gpu/C0_32_gpu`; its
  7 present entries match my recomputation exactly, and the report's C0/C2
  late-window zeros are verifiable from `identities.csv`.
- N4 "C1_cpu … bit-frozen" is slightly overstated: the plateau carries a
  ±1.4e-09 relative wobble and late-window J1 `frac_pos = 0.50` with mean
  −1.0e-11 (zero-mean jitter, non-accumulating). The plateau claim itself is
  verified (+3.5206e-05 flat from ≈3400 to 5000).
- N5 "colour sublinear (increments 5.4 / 4.3 / 3.7 / 3.7e-5 per 5k)": 5.4e-5
  is the value at 5k, not an increment; true increments are 4.30/3.74/3.61e-5.
- N6 C1_gpu is not strictly linear (increments vary ×1.6; R² 0.996); the
  "linear to 20k, R² 0.9999" statement should be scoped to C3.
- N7 Q1 lists J4 among "exactly conservative" sub-steps; with all `bc_*`
  flags at 0, `Boundary_condition`/`Boundary_condition_psi` are compiled out,
  so J4 = 0 and S6 == S5 are vacuous no-op checks. The C2/C3 wall physics is
  actually exercised in `streaming1` bounce-back and the colour bounce-back
  inside `collision` (there J3 = 0 has a mechanistic proof: bounce-back is a
  permutation of distribution values). The document must not present J4 as
  BC-path validation.
- N8 `MANIFEST.json:generator` is a free-text string, not a script hash or
  commit id.

## Modeling / Scientific Review

- No solver physics, BC/IC meaning, convergence rule, wettability
  interpretation or default parameter was changed; the audit is
  diagnostic-only and the no-fix rule was honoured (`git diff` shows only
  audit files; `lbm_solver_cg3d.py` byte-identical to base).
- Assumptions are explicit and appropriate: C0/C1/C2/C3 exactly match the
  isolation matrix requested by the contract and the four-level split that
  the living document's V3-hold text already demanded. C3 is a legitimate
  minimal V2 analogue (mirror-checked; two menisci, closed slit, ψ_solid =
  −0.68), and its rates reproduce the V2 production rates (population
  1.5556e-08 vs V2 1.53e-08 = +1.7%; colour 8.31e-09 vs 5.47e-4/60k =
  9.12e-09, −8.7%) — the V2 numbers are faithfully quoted from
  `.agent/evidence/BI-V2-BILATERAL-001/`.
- The audit's central methodological claim (host reads do not perturb; the
  decomposed step is production-identical) is verified bit-exactly by
  J9 = 0 over 38 consecutive step pairs per run.
- Mechanism classification: the evidence (mine included) supports
  "collision-kernel f32 roundoff with a *systematic positive bias*", with
  **no discrete imbalance** (f64 roundtrip residual 2.7e-17) — so it is
  neither an exactly-conservative formulation implemented wrongly nor
  random-walk noise. Because the bias persists wherever non-equilibrium
  persists, it is *unbounded in T* (C3: 0.031% at 20k, 0.093% at 60k at
  1.556e-08/step), which is precisely why class A / `PASS_BOUNDED_FLOOR`
  cannot be supported. The label "B — colour/total-population bookkeeping
  mismatch" is defensible for the observable (the two channels diverge) but
  should be stated as B/D-composite with the single f32 root cause, since
  both channels leak independently inside `collision` at different rates
  (J1 total 1.556e-08/step; J7 colour 8.31e-09/step).
- Convergence: process completion is not claimed as physical convergence;
  the cases are closed-system fixed-point/flux-stationary runs, and the
  audit reports rates and R², not "convergence". Acceptable.
- Claims bounded by evidence: the audit does not claim the drift affects V2
  symmetry/topology gates; the executor defers the gate/fix decision to the
  contract owner (correct per contract §11 and R-V2-3).
- Stale evidence: none of V1/V1b/V1c/V2 is re-issued by this task; the audit
  *explains* the V2 drift rather than changing any V2 number. The living
  document's §23 sentence "当前没有证据要求修改 core solver" and its
  "owner decision: gate re-scope vs solver conservation item" line become
  stale once the audit section is published and must be updated.

## Document Update Review (contract §13, planned section)

Placement recommendation (the document's actual convention is append-at-end;
§21.7 already sits after §23, so inserting mid-file would force renumbering of
§18–§23 and break existing "见 §x" references):

1. append the new chapter as `# 24. SOLVER Conservation Audit —
   BI-CONSERVATION-AUDIT-001` at the end of
   `docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md`,
   written as a *diagnostic* record (SOLVER row = "无"), not as an algorithm
   change; §22's change template does not apply to it;
2. add a one-line pointer from §21.7 (V2 review / V3 conservation hold) to
   the new chapter;
3. update §23's status block (collapse the "no evidence requires a core
   solver change" sentence into the audit outcome: leak localized to the
   collision kernel f32 moment roundtrip, no discrete imbalance, walls
   exactly innocent, backend-independent, ≤1.56e-08/step ⇒ ≤0.093%/60k, fix
   = separate task candidate, V3 hold pending owner decision);
4. add the new precision layer to §16 (`16.7 Intrinsic closed-system mass
   conservation`), since §16 is the document's designated home for
   separating accuracy layers;
5. add the episode's evidence paths to §19 (`results/conservation_audit/**`,
   review artifacts under `.agent_runtime/BI-CONSERVATION-AUDIT-001/`).

Pre-existing (untracked) document figures — inspected, one carries a false
label and must be regenerated before publication. The main repo already
contains `docs/research/bilateral_imbibition/figures/ca_make_figs.py` and
four `fig_ca_*.svg` for this audit (generated from the frozen candidate's
committed CSVs, candidate `24b00dbe…` annotated — convention respected).
`fig_ca_substep_localization.svg` (only the collision kernel leaks) and the
spatial-budget title ("… leaked M_f/M_ρ mass resides in the bulks", no
causality clause) are consistent with the evidence. But
`fig_ca_drift_horizon.svg` panel (b) plots `|Mff/M0 − 1|` for `C0_24_gpu`
and `C2_gpu` with legends "C0 GPU 24³ (uniform, |d|<10⁻¹²)" and "C2 GPU
(walls, single phase, exact 0)", while the plotted and actual value is
+3.427e-07 for both (the B1 offset): the legend is false by ~5 orders of
magnitude, the log-scale curve visibly sits at 3.4e-07 (self-contradicting
the panel title "(b) isolation: uniform / wall-only floors are zero"), and
the code divides by the node count 13824.0 instead of the recorded M0
(`M0 = 13824.00021`), which does not fix the falsehood. Relabel to the
verified statement (flat, no accumulating drift; constant +3.427e-07 offset
acquired in steps 0–2 and reproduced bit-exactly by collision arithmetic),
or plot the per-horizon increment (which is <1e-12 for C0/C2) and say so.

Content requirements: all 12 items of contract §13, with formulas matching
the driver's definitions (`tests/conservation_audit.py:27-43`, J0–J9 at
`:316-340`), code excerpts from the frozen solver (`lbm_solver_cg3d.py:115`,
`:481-486`, `:554-557`, `:537-542`, `:558-573`, `:578-588`, `:603-606`,
`:789-800`, `:819-828`), the C0–C3 matrix with the corrected C0/C2
annotation (B1), the corrected mechanism attribution (B2) and fix scope
(B3), a non-causal spatial-budget table (B4), the corrected/removed
interface-area normalization (B5), and evidence links. Figures must follow
the existing convention (`figures/`, generated by a newly committed script
from the frozen candidate's committed CSVs, candidate SHA annotated
in-figure). No solver claim may rest on J4 (N7).

## Missing Evidence

- No persisted batch-level log with shell exit codes (N2).
- No committed generator for `late_window_identities.json`, and it omits 3
  runs (N3).
- C1/C2 interface-band and wall-band node counts are not committed, so the
  interface-area normalization cannot be checked (B5).
- The audit does not localize the colour channel below the kernel
  (`feq` pair sum vs recolouring vs accumulation); the reviewer's probe
  supplies the attribution (B3) but this should be stated as
  reviewer-derived unless the executor reproduces it.

## Decision Rationale

The candidate binding is sound (SHA/branch/clean worktree/base ancestry/single
commit/audit-only 74-file diff/no solver change/84-of-84 artifact hashes), and
the audit's numbers are not merely plausible but reproducible: I refit every
slope and R² (max deviation 1.35e-17), reproduced every late-window J1/J7
statistic, confirmed all exact identities and the S6≡S0 closure bitwise,
reconciled the spatial budget with the horizon deltas, and confirmed the V2
cross-claim. The diagnosis itself — collision kernel, S0→S1, sign-biased,
not a storage-representation artifact, walls exactly innocent, not random
accumulation, unbounded in T — is *upheld and strengthened* by an
independent host-side reproduction of the production arithmetic that matches
the audit's own C0 signature bit-for-bit and predicts the C3 rates to within
4%. For a fix task, only the fix scope needs sharpening (B3).

However, the report as delivered contains four finite defects that fail this
contract's own cautions (§11 required elements, §6 no-causality, "do not
accept an explanation merely because it is plausible"), all of them
correctable by text and derived-artifact revision with **no new
simulations**: a false decisive argument about C0 that is refuted by the
candidate's own `backend_comparison.csv` (B1), a mechanism sub-attribution
that independent recomputation falsifies (B2), a causality statement the
contract forbids and the budget does not support (B4), and a numeric claim
that cannot be reproduced from the committed artifacts (B5), plus a fix
scope whose first variant would not work (B3). Awarding `PASS` here would
certify the audit as accepted while these claims enter the living document,
which is the durable record. Per contract §14 (`CHANGES_REQUESTED`: finite
audit/evidence defects) and the episode's own precedent (V1c attempt 1),
the correct verdict is a bounded revision.

## Next Action

Executor, on `agent-task/BI-CONSERVATION-AUDIT-001`, produces a revision
commit containing exactly these text/derived-artifact changes, **without
re-running any simulation and without regenerating any raw evidence file**:

1. rewrite the Q4 answer and the C0/C2 cells: slope ≈ 0 because the state
   reaches a bit-exact fixed point after 2 steps, *and* the fixed point sits
   +2.875 ULP/node (+3.427e-07 relative) above the initial condition — i.e.
   precision does create mass in C0, once and bounded; the anti-bounded-floor
   argument must rest on the linear-in-T, 100%-sign-biased accumulation
   (and note R² = 1.0 in C0/C2 is the zero-variance fallback);
2. rewrite the Q2 mechanism attribution: f32 `inv_M` column-sum defect
   `Σ_s inv_M[s,0] = 1 + 1.49e-08` as the dominant total-channel term
   (predicted 1.49e-08/step vs measured 1.556e-08/1.517e-08), bias
   independent of the colour gradient (cc = 0 ⇒ no interface needed), the
   interface's role being to sustain non-equilibrium; colour channel
   dominated by the `feq` pair sum (+1.5e-08), recolouring pair arithmetic
   ≈300× smaller; a reviewer-supplied host reproduction may be cited as
   such;
3. rewrite the fix scope: effective minimal fixes are an f64 moment
   roundtrip (matrix *and* accumulator; residual 2.7e-17) or an exact
   per-node zeroth-moment correction; state explicitly that "f64
   accumulator with the f32 matrix" is insufficient (bias unchanged,
   frac_pos 1.00);
4. delete the spatial-budget causality sentence and replace it with the
   per-node rate table and the statement that the budget cannot localize
   creation;
5. delete or re-derive the interface-area normalization numbers using only
   committed quantities (and commit the C1/C2 band counts if the
   normalization is kept);
6. fix N1–N8 (numpy version, exit-code log or drop the assertion,
   regenerate `late_window_identities.json` through a committed generator
   covering all 10 runs, C1_cpu wording, the 5.4e-5 label, scope "linear"
   to C3, restate J4 as a vacuous no-op check, record a real generator id);
7. regenerate `fig_ca_drift_horizon.svg` panel (b) and its legend/title from
   the corrected C0/C2 statement (see the figure finding above), and commit
   `figures/ca_make_figs.py` together with the four SVGs.

Then re-submit for fresh review (attempt 2). After that review accepts the
revision, publish the document update per the placement review above. No
solver fix and no V3 work is authorized by this review; the fix remains a
separate owner-authorized task, and the V3 hold stays in force.

Decision: CHANGES_REQUESTED
