# SUMMARY — BI-CONSERVATION-AUDIT-001

## Outcome

**PASS_DIAGNOSIS_READY_FOR_FIX** (fresh reviewer attempt 2, no
self-review). The pre-V3 conservation audit mandated by the V2 external
review (R-V2-3) is complete: the monotone mass drift of V1c/V2 is
localized, classified, and quantified; **no solver change was made**
(no-fix rule honoured) and **no V3 work was started**.

## Binding

- base `5e679d8` (V2 candidate) -> attempt-1 candidate `24b00db`
  (CHANGES_REQUESTED) -> attempt-2 candidate `1f5ee76`
  (PASS_DIAGNOSIS_READY_FOR_FIX), branch
  `agent-task/BI-CONSERVATION-AUDIT-001`, all pushed.
- Reviewer sessions: attempt 1 `sess_c85bbfb2-c98e-4b47-b109-6ea47fd77dab`,
  attempt 2 `sess_c5a55809-c412-43b3-8290-1385b3e547b2`
  (`REVIEW_SESSION.json`).

## Diagnosis (one paragraph)

The drift is a single f32 root cause inside `collision()` with a class-B
observable (the total-distribution and colour bookkeeping channels
diverge monotonically at that kernel): the stored f32 inverse moment
matrix does not conserve the zeroth moment —
`sum_s inv_M[s,0] = 1 + 1.4901e-8` (= 2^-26) — so each collision inflates
the reconstructed total mass by that factor wherever non-equilibrium
persists; the colour channel leaks independently in the same kernel
(`feq`-pair sum dominant, +1.508e-8 at realistic splits; recoloring ~300x
smaller; accumulation noise). Measured C3 (minimal V2 analogue):
total +1.556e-8/step (GPU) / +1.517e-8 (CPU), linear in T, R^2 0.9999,
J1 sign-positive in 100% of late steps on both backends; colour +8.31e-9
(GPU). Walls/bounce-back exactly innocent (C2 bit-zero); uniform states
freeze at a bit-exact fixed point after a one-time bounded +3.427e-7
offset (C0, all sizes). The C3 total-channel rate reproduces the V2
production population rate (1.53e-8/step) within +1.7%. Root cause first
derived by the attempt-1 reviewer's independent host-side f32 model and
executor-reproduced via the committed `inv_m_colsum_check.py`.

## Consequences

- `PASS_BOUNDED_FLOOR` refuted: unbounded linear-in-T deterministic bias.
- Operational magnitude inside the owner's calibrated V2 envelope
  (r_M <= 2e-8/step; extrapolated ~9.3e-4/60k <= 1e-3): V3 **may**
  proceed before a fix under that envelope — owner decision.
- Fix = separate owner-authorized task; effective minimal scopes
  (reviewer-verified): (i) f64 moment roundtrip (matrix AND accumulator,
  residual 2.7e-17) or (ii) exact per-node zeroth-moment correction;
  f32-matrix + f64-accumulator is explicitly insufficient (bias
  unchanged). Colour fix must target the feq pair sum, not
  recoloring/atomics. Regression list in the execution report.
- V3 contract still requires rewrite + external authorization (V2
  external review section 9); the hold stands until the owner decides.

## Evidence

- product: `results/conservation_audit/**` on branch
  `agent-task/BI-CONSERVATION-AUDIT-001` at `1f5ee76` (93-artifact
  MANIFEST, SHA256-bound generators; 10 runs C0-C3 x GPU/CPU + C0 domain
  scaling + C3 horizon scaling; EXECUTION_REPORT / PROVENANCE /
  summary.json / per-run CSVs / logs / figures);
- reviews: `REVIEW_ATTEMPT_1.md` (CHANGES_REQUESTED, B1-B5/N1-N8),
  `REVIEW.md` (attempt 2, PASS_DIAGNOSIS_READY_FOR_FIX, observations
  O1-O6 to be applied in the living document — done in the published
  section 24);
- living document: `docs/research/bilateral_imbibition/`
  `ALGORITHM_IMPLEMENTATION_EVOLUTION.md` section 24 (+ 16.7, 19, 21.7
  pointer, 23 status update).

## History of this task line

V1c PASS -> V2 scientific PASS with mandatory conservation audit
(R-V2-3) -> this audit PASS_DIAGNOSIS_READY_FOR_FIX -> (next) owner
decision on solver-fix task vs envelope-based V3 contract rewrite;
external scientific review still required for both.
