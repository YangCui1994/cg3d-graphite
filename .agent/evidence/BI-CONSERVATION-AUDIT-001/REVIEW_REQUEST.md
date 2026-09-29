# REVIEW REQUEST — BI-CONSERVATION-AUDIT-001 (attempt 2)

## Binding

- **Task:** BI-CONSERVATION-AUDIT-001 (diagnostic solver conservation
  audit; diagnostic-only, no solver change)
- **Product base:** `5e679d8d99d338f9ab28565c636f021a0f9211b2` (V2
  candidate)
- **Product branch:** `agent-task/BI-CONSERVATION-AUDIT-001`
- **Attempt-1 candidate:** `24b00dbe28d23c12049d05679542301ccc507eac`
  (reviewed: CHANGES_REQUESTED)
- **Attempt-2 candidate (this review):**
  `1f5ee76fa183b42dd0ffcb291f389c3f1974a147`
- **Reviewer contract:**
  `.agent/episodes/bilateral-imbibition-v0.1/CONSERVATION_AUDIT_REVIEWER_CONTRACT.md`
- **Audit contract:**
  `.agent/episodes/bilateral-imbibition-v0.1/CONSERVATION_AUDIT_CONTRACT.md`
- **Attempt-1 review:** `.agent_runtime/BI-CONSERVATION-AUDIT-001/REVIEW_ATTEMPT_1.md`

## Revision scope (attempt 1 -> attempt 2)

Exactly the attempt-1 review's Next Action items 1-7, as a single
revision commit (`git diff 24b00db 1f5ee76` — text and derived artifacts
only; **no simulation re-run; no raw evidence file modified**; the
per-run CSVs/npz/prov.json/logs are byte-identical to attempt 1):

1. Q4 / C0/C2 cells rewritten: slope-0-after-bit-exact-fixed-point **and**
   the one-time bounded +3.427267e-07 (+2.875 ULP/node) offset; anti-A
   argument now rests on linear-in-T + 100% sign bias; R2=1.0 flagged as
   zero-variance fallback;
2. Q2 rewritten to the inv_M zeroth-column defect
   (`sum_s inv_M[s,0] = 1 + 1.4901e-8`), cc-independence, interface role
   = sustaining non-equilibrium; colour channel decomposition
   (feq-pair dominant / recoloring ~300x smaller / accumulation noise)
   attributed to the attempt-1 reviewer's host-side model, with the
   colsum number now executor-reproduced via the committed
   `inv_m_colsum_check.py` (+ json output);
3. fix scope rewritten: f64 roundtrip (matrix AND accumulator) or exact
   per-node zeroth-moment correction; f32-matrix+f64-accumulator
   explicitly stated insufficient;
4. spatial-budget causality sentence deleted; per-node rate table added
   (gas 2.07e-4 / liq 4.81e-4 / wall 2.44e-4 / interface 3.43e-4); the
   budget's non-localizability stated;
5. interface-area normalization deleted (C1/C2 band counts not
   committed; claim removed as non-reproducible);
6. N1-N8: numpy 2.2.6; `logs/batch_exit_codes.log` committed;
   `late_window_identities.json` regenerated for all 10 runs by the
   committed `make_late_window.py`; C1_cpu wording (zero-mean jitter,
   non-accumulating); increments corrected (4.30/3.74/3.61e-5); linearity
   scoped to C3; J4/S6==S5 restated as vacuous no-op checks (wall physics
   lives in streaming1 bounce-back / collision colour bounce-back, J3=0
   by permutation); MANIFEST generator field now SHA256-bound script
   identities;
7. `fig_ca_drift_horizon.svg` panel (b) regenerated with the corrected
   labels (slope 0, constant +3.43e-7 offset; M0 read from
   case_report.json); `figures/ca_make_figs.py` + all four SVGs committed
   under `results/conservation_audit/figures/`.

## Where the evidence lives

Candidate worktree:
`D:\2026_agent_work\01_GLM_LBM3D_porous_media\cg3d-episode-worktrees\BI-CONSERVATION-AUDIT-001`

- `results/conservation_audit/EXECUTION_REPORT.md` (revision 2),
  `PROVENANCE.md` (revision note + generator list), `MANIFEST.json`
  (93 artifacts, SHA256, generator bindings);
- new derived artifacts: `make_late_window.py` /
  `late_window_identities.json` (10 runs), `inv_m_colsum_check.py/.json`,
  `logs/batch_exit_codes.log`, `figures/` (script + 4 SVGs);
- all raw evidence unchanged from attempt 1 (per-run dirs, `summary.json`,
  `backend_comparison.csv`, `scaling_results.csv`, `logs/`).

## Reviewer instructions

Follow the reviewer contract, taking the attempt-1 review
(`REVIEW_ATTEMPT_1.md`) as the prior finding set. Verify the revision
implements items 1-7 faithfully and introduces no new defects; re-check
candidate binding (candidate 1f5ee76 descends from 24b00db -> 5e679d8,
clean worktree, solver byte-identical, audit-only diff) and that the raw
evidence is untouched (`git diff 24b00db 1f5ee76 --stat` must show only
the twelve files listed in the revision commit). Write only
`.agent_runtime/BI-CONSERVATION-AUDIT-001/REVIEW.md` (attempt: 2,
candidate: 1f5ee76...) with a single final
`Decision: <PASS_DIAGNOSIS_READY_FOR_FIX|PASS_BOUNDED_FLOOR|CHANGES_REQUESTED|HUMAN_REQUIRED>`
line. Stop after writing REVIEW.md.
