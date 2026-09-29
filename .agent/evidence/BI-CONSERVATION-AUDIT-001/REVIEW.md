stage: conservation-audit
attempt: 2
candidate: 1f5ee76fa183b42dd0ffcb291f389c3f1974a147
execution_report: results/conservation_audit/EXECUTION_REPORT.md

# REVIEW — BI-CONSERVATION-AUDIT-001 (attempt 2)

## Review Mode

`FRESH_SESSION` (independent reviewer session; executor transcript not read).

## Coverage

Inspected:

- task/contracts: this request, `CONSERVATION_AUDIT_CONTRACT.md`,
  `CONSERVATION_AUDIT_REVIEWER_CONTRACT.md`, attempt-1 review
  (`REVIEW_ATTEMPT_1.md`), control review
  `.agent/evidence/BI-V2-BILATERAL-001/V2_EXTERNAL_SCIENTIFIC_REVIEW_PASS.md`
  (§3.2 envelope, R-V2-3);
- worktree `cg3d-episode-worktrees/BI-CONSERVATION-AUDIT-001` (git identity,
  cleanliness, full attempt-1..attempt-2 diff, solver/driver immutability);
- revision artifacts: `EXECUTION_REPORT.md` (revision 2, full diff vs
  attempt 1), `PROVENANCE.md`, `MANIFEST.json`, `make_late_window.py`,
  `inv_m_colsum_check.py/.json`, `logs/batch_exit_codes.log`,
  `figures/ca_make_figs.py` + all four SVGs (label text extracted);
- raw evidence (unchanged): all 10 per-run dirs
  (`identities.csv`, `long_horizon_mass.csv`, `substep_mass_trace.csv`,
  `case_report.json`, `prov.json`, `spatial_budget.csv`, `symmetry_check.json`),
  `summary.json`, `backend_comparison.csv`, `scaling_results.csv`, `logs/`;
- solver table construction `lbm_solver_cg3d.py:95-115` (`M_np` f64 →
  `M`/`inv_M` f32 cast) and its single use at `:557` (`inv_M[s,l]*m_temp[l]`).

Independent recomputation performed (host-side, read-only; solver tables
imported in a CPU subprocess with bytecode writing disabled; no GPU; no file
written):

- full MANIFEST verification (93/93 SHA256) + driver hash + generator
  bindings;
- attempt-1 vs attempt-2 MANIFEST hash comparison (raw-evidence invariance);
- independent reproduction of `sum_s inv_M[s,0]-1` from the solver's own
  f32 table;
- late-window (last 20 traced steps) J1/J6/J7 mean_rel and frac_pos for all
  10 runs, recomputed from `identities.csv` + `case_report.json` M0;
- exact-zero scan of J0/J2/J3/J4/J5/J8 and J9 closure over all 10 runs;
- first-material `d_fc`/`d_crho` checkpoints from `case_report.json`;
- C3_gpu horizon values/increments, C1_gpu increments, C1_cpu plateau;
- C3_gpu spatial-budget region sums vs horizon deltas and per-node rates;
- C0/C2 offset signatures (GPU and CPU) from `backend_comparison.csv`,
  `identities.csv`, `long_horizon_mass.csv`;
- figure SVG: label strings and geometry of panel (b) curves.

Not inspected / not done:

- executor conversation transcript (prohibited);
- no simulation was re-run; no GPU used; no file modified except this review.

## Binding Verification

| Check | Status | Evidence |
|---|---|---|
| Candidate SHA / branch | PASS | HEAD `1f5ee76fa183b42dd0ffcb291f389c3f1974a147` on `agent-task/BI-CONSERVATION-AUDIT-001`; `git ls-remote origin` matches |
| Clean worktree | PASS | `git status --porcelain` empty |
| Descends from V2 candidate | PASS | `5e679d8` and `24b00db` are ancestors; revision is a single commit, parent `24b00db` |
| Only audit files changed | PASS | `git diff 24b00db 1f5ee76 --name-status` = 13 files, all under `results/conservation_audit/` |
| No solver/driver change | PASS | `git diff 24b00db 1f5ee76 -- lbm_solver_cg3d.py cg3d/ tests/` = empty; `git diff 5e679d8 1f5ee76 -- lbm_solver_cg3d.py cg3d/` = empty |
| Raw evidence byte-identical | PASS | 84/84 common MANIFEST entries unchanged except the three derived entries (`EXECUTION_REPORT.md`, `PROVENANCE.md`, `late_window_identities.json`); no raw-evidence path in the diff; raw mtimes 18:05–18:50 precede revision work 19:17–19:20 |
| No simulation re-run | PASS | unchanged raw hashes + unchanged mtimes + unchanged per-run logs; `logs/batch_exit_codes.log` timestamps match per-run dir mtimes and `wall_s` values, so it is a transcription of the attempt-1 batch, not a new run |
| Artifact hashes / producer revision | PASS | MANIFEST 93/93 verify on disk; `driver` hash equals committed `tests/conservation_audit.py`; generator bindings are SHA256-bound to the committed scripts (`ca_make_figs.py 6a085e1f…`, `inv_m_colsum_check.py 4b6306b6…`, `make_late_window.py 19342190…`, `run_batch.sh 12cc8a33…`) — attempt-1 N8 closed |

Note on the request's file count: the revision diff contains exactly the 13
files enumerated in the request body (report, PROVENANCE, MANIFEST, figures
script + 4 SVGs, `inv_m_colsum_check.py`/`.json`, `late_window_identities.json`,
`make_late_window.py`, `logs/batch_exit_codes.log`); the phrase "twelve files"
is a miscount of that same list, and no unauthorized path is present.

## Verification of Attempt-1 Next Action Items 1–7

1. **Q4 / C0/C2 rewrite — implemented, verified.** `backend_comparison.csv`:
   `final_rel_Mff = +3.427267023515e-07` for `C0_16/24/32_gpu`, `C2_gpu`;
   `C0_24_cpu`/`C2_cpu` carry `final_rel_Mc = +3.427267023515e-07`
   (`Mff = 0.0`, `Mrho = −1.490116097e-08`). `C0_24_gpu/identities.csv`:
   J1 step 0 `+3.707886e-03` (= +2.682209e-07 rel), step 1 `+1.029968e-03`
   (= +7.450581e-08 rel), cumulative +3.427267e-07, exactly 0 from step 2;
   horizon `Mff` constant at +3.427269e-07. The report's claims — slope 0
   after a 2-step transient, one-time bounded +3.427267e-07 offset, anti-A
   argument resting on linear-in-T and 100 % sign bias, and `R² = 1.000` for
   C0/C2 being the driver's zero-variance fallback
   (`tests/conservation_audit.py:419-420`) — all reproduce.
2. **Q2 rewrite — implemented, verified.** Independent import of the solver's
   own f32 tables gives `sum_s inv_M[s,0] − 1 = +1.49011611938477e-08`, equal
   to `inv_m_colsum_check.json` (`colsum0_minus_1`,
   `predicted_total_channel_rate_per_step`); `max|colsum[l>0]| = 1.4901e-08`
   matches; `M` row 0 is bit-equal to ones; `inv_M == f32(inv(M_f64))`. The
   colour decomposition and cc-independence are explicitly attributed to the
   attempt-1 reviewer's host-side model, and the interface role is stated as
   sustaining non-equilibrium — as required.
3. **Fix scope — implemented, verified.** Report §"Solver-fix proposal":
   effective minimal scopes are (i) f64 moment roundtrip (matrix *and*
   accumulator, residual 2.7e-17) or (ii) an exact per-node zeroth-moment
   correction; "f64 accumulator with the f32 matrix" is explicitly stated
   insufficient (bias +1.496e-8 unchanged, frac_pos 1.00); the colour fix is
   directed at the `feq` pair sum.
4. **Spatial budget — causality deleted, table verified.** The causality
   sentence is gone; the budget is stated as unable to localize creation.
   Per-node rates recomputed from `C3_gpu/spatial_budget.csv` (ref1000 rows):
   gas +3.7023/17880 = 2.071e-4, interface +0.3292/960 = 3.429e-4, liq
   +4.1007/8520 = 4.813e-4, wall +0.3506/1440 = 2.435e-4 (report
   2.07/3.43/4.81/2.44e-4 ✓). "92 % in the bulks" = 7.803/8.4827 ✓. "Region
   sums reconcile with the horizon deltas to ≤1.1e-9" verified exactly
   (ΣdMf − (Mff(20000) − Mff(1000)) = 1.106e-09).
5. **Interface-area normalization — deleted.** Replaced by an explicit
   "not claimed — not reproducible from committed artifacts" statement; no
   residual per-band normalization appears anywhere in the report.
6. **N1–N8 — all closed.** N1 `PROVENANCE.md` now says numpy 2.2.6 (matches
   every `prov.json`). N2 `logs/batch_exit_codes.log` committed (all exit=0;
   timestamps consistent, see binding table). N3 `late_window_identities.json`
   regenerated for all 10 runs by the committed `make_late_window.py`; my
   independent recomputation of M0, window bounds, mean_rel and frac_pos for
   J1/J6/J7 matches the JSON exactly in all 10 runs. N4 C1_cpu wording fixed
   (late J1 −1.0e-11, frac_pos 0.50; plateau 3.5200–3.5207e-05 from ≈3400 to
   5000, non-accumulating). N5 colour increments verified (5.397e-05 at 5k;
   increments 4.302/3.739/3.613e-05). N6 linearity scoped to C3; C1_gpu
   R² = 0.9957 flagged non-linear. N7 J4 restated as a vacuous no-op check
   (J4 = 0.0 in all runs; wall physics located in `streaming1` bounce-back /
   collision colour bounce-back); no claim rests on J4. N8 generator field is
   now SHA256-bound (verified above).
7. **Figure regenerated — implemented, verified.** `figures/ca_make_figs.py`
   reads `M0` from each `case_report.json` (no more 13824.0 divisor); panel
   (b) legend/title now read "slope 0, constant +3.43×10⁻⁷ offset", "walls,
   single phase: slope 0, same bounded offset", "(b) isolation: no
   accumulating drift (one-time offset from the 2-step transient)"; the
   committed SVG contains exactly these strings, and its axes_2 contains
   exactly two 50-point flat curves, consistent with the flat +3.427e-07
   series (C0 level above C2, as in the data).

Cross-checks retained from attempt 1 (raw evidence unchanged, re-verified):
J0/J2/J3/J4/J5/J8 = 0.0 and J9 closure = 0.0 over all 10 runs × traced
steps; first-material `d_fc`/`d_crho` checkpoints 200/400/400/600
(`case_report.first_material_residual_horizon`); C3_gpu slopes 1.5556e-8
(total) / 8.309e-9 (colour), C3_cpu 1.5173e-8; C3_gpu horizon
7.458e-5/1.522e-4/2.312e-4/3.096e-4 with increments 7.76/7.90/7.84e-5;
C1_gpu late J1 +1.42e-8 (95 % pos), J7 +7.0e-9 (80 % pos); C3 late J1/J7
100 % positive on both backends. The V2 envelope cited in Q3 exists in the
control review (§3.2: r_M ≤ 2e-8/step, |ΔM|/M0 ≤ 1e-3/60k).

## Observations (non-blocking; to be corrected in the document, not in a new audit revision)

- **O1 — spatial-budget "Net:" parenthetical mixes two windows.**
  `EXECUTION_REPORT.md` states `dMf = +8.48 (== 3.096e-4 × 28800)` and
  `dMc = +4.61 (== 1.705e-4 × 28800)`. The budget table is the ref1000
  window: ΣdMf = +8.4827, ΣdMc = +4.6094. The quoted rates are the
  t0→final totals (3.095983e-4, 1.705164e-4), i.e. 3.096e-4 × 28800 =
  8.9164 and 1.705e-4 × 28800 = 4.9113 — the t0-column sums, not the
  table's. The correct ref1000-window rates are 2.9454e-4 (Mf) and
  1.6005e-4 (Mc). The adjacent claim "region sums reconcile with the
  horizon deltas to ≤1.1e-9" is exact; only the normalization parenthetical
  is mislabelled. (Structure pre-dates the revision, where it read
  "1.7e-4/3.1e-4"; the revision sharpened the digits.)
- **O2 — `d_frho` parenthetical is the C3 maximum, not the global one.**
  "(max 2.21e-9 relative)" equals `C3_gpu`'s horizon maximum (2.209e-09).
  The global horizon maxima are `C1_gpu` 2.687e-8 (step 200) and
  `C0_24_cpu`/`C2_cpu` 1.490e-8 (constant CPU representation offset); the
  largest traced-step value is 7.451e-8 (`C0_24_gpu` step 1, transient,
  back to 0 at step 2). The substantive claim (never material, ≪1e-6) holds;
  the number is the one the attempt-1 review derived for C3.
- **O3 — C0/C2 one-time offset is channel-specific on CPU.** The footnote
  "final state sits at +3.427267e-07 … above the initial condition" and Q4's
  "in the first two steps" describe the GPU signature. For
  `C0_24_cpu`/`C2_cpu` the total channel is exactly 0.0 and the
  +3.427267e-07 sits in the colour channel (J7; `Mrho = −1.49e-8`,
  disclosed separately in the CPU J6 note). No conclusion changes; the
  document should state it channel-wise.
- **O4 — C1_gpu "×1.6" spread not exactly reproduced.** My per-5k block
  ratio is 1.24 and per-1k increments span ×2.3; R² = 0.9957. The
  qualitative claim (not strictly linear) is correct; the factor is quoted
  from the attempt-1 review.
- **O5 — panel (b) axis degeneracy (rendering, not labelling).** Because
  the C0/C2 series are flat at nearly identical values, the auto log axis
  spans ~ULP-level differences, all eight major tick labels read
  `3.42727×10⁻⁷`, and the two flat curves appear vertically separated
  although they differ by ~6e-7 relative. Labels/title are correct; the
  caption in the document should note the axis span, or the figure should
  use a fixed/linear zoom.
- **O6 — generator portability.** `figures/ca_make_figs.py` is
  environment-bound (`EV` absolute worktree path, `OUT = HERE`, docstring
  referencing the `docs/…/figures` location). Acceptable for the audit
  artifact; the document-publication step must place a properly relocated
  generator next to the committed evidence (the regenerated
  `docs/research/bilateral_imbibition/figures/` copies already carry the
  same corrected labels).

## Missing Evidence

None material. Remaining caveats: `logs/batch_exit_codes.log` is a
transcription of batch stdout rather than machine-captured output (its
timestamps are consistent with per-run dir mtimes, logs and `wall_s`);
figure generation depends on the candidate worktree path (O6).

## Decision Rationale

The revision implements Next Action items 1–7 faithfully and introduces no
new defect: the diff is text plus the authorized derived artifacts (13 files,
no raw evidence, no solver, no driver), all 93 MANIFEST hashes verify,
raw-evidence hashes are untouched between attempts, and no simulation was
re-run. Every corrected claim I was asked to spot-check reproduces from the
committed artifacts: the C0/C2 +3.427267e-07 offset and its 2-step transient,
the `inv_M` zeroth-column defect (independently reproduced from the solver's
own table), the spatial-budget per-node rates, the colour increments, the
regenerated 10-run `late_window_identities.json`, the SHA256-bound generator
identities, and the regenerated figure labels. The four `PASS_DIAGNOSIS_READY_FOR_FIX`
elements all hold on the frozen candidate: the imbalance is localized to
`collision()` S0→S1 (J1 total, J7 colour; every other sub-step bit-exact
zero); the failed identity is reproducible (per-node zeroth moment vs
`sum_s F`; `sum_s inv_M[s,0] = 1 + 2⁻²⁶`, 2.7e-17 with a fully-f64
roundtrip); the minimal fix scope is credible and the ineffective variant is
excluded; the regression list is given. `PASS_BOUNDED_FLOOR` remains
refuted: the drift is linear in T with a 100 % per-step sign bias on both
backends, so despite its small operational magnitude (≤1.56e-8/step,
~9.3e-4 over 60k, inside the owner's calibrated envelope) it is a
deterministic f32 bias, not a bounded floor. The residual issues O1–O4 are
text/normalization imprecisions (three of them pre-existing and two being
numbers derived by the attempt-1 review itself); they change no conclusion,
their correct values are in the committed CSVs, and they are to be fixed in
the living document, which is the durable record. This review therefore
accepts the audit and does not block on them.

## Exact Next Action

1. Publish the technical-document update per the attempt-1 placement review
   (append `# 24. SOLVER Conservation Audit — BI-CONSERVATION-AUDIT-001`,
   §21.7 pointer, §23 status update, §16.7, §19 evidence links), with the
   corrected statements from O1–O3 and O5 applied there: ref1000-window
   budget rates 2.9454e-4 (Mf) / 1.6005e-4 (Mc) — or label 3.096e-4/1.705e-4
   explicitly as t0→final totals; `d_frho` maximum 2.69e-8 (C1_gpu) with the
   CPU 1.49e-8 offset noted; the C0/C2 offset stated channel-wise for CPU
   runs; and a panel-(b) caption noting the log-axis span (or a re-scaled
   figure).
2. No solver fix is authorized by this review; the fix remains a separate
   owner-authorized task with the regression list in the report. No V3 work
   is authorized; the V3 hold stays in force until the owner decides.
3. STOP after document publication (contract §15). Optionally, the
   controller may issue a small erratum commit to `EXECUTION_REPORT.md`
   carrying O1–O4, but the binding corrections are the document ones.

Decision: PASS_DIAGNOSIS_READY_FOR_FIX
