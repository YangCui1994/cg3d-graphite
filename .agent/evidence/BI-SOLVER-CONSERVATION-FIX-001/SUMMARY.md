# SUMMARY — BI-SOLVER-CONSERVATION-FIX-001

## Outcome

**PASS** (fresh reviewer attempt 4; attempts 1–3 CHANGES_REQUESTED for
documentation-package defects only — the scientific conclusions were
independently reproduced at every attempt and never disputed). The
authorized solver conservation fix is implemented, selected through an
honest candidate comparison, and passes every unchanged physics gate.
**V3 remains HOLD**: only external scientific review can lift it.

## Binding

- base `1f5ee76` (conservation-audit candidate) → final candidate
  `e256b48` on branch `agent-task/BI-SOLVER-CONSERVATION-FIX-001`
  (pushed; solver blob `38bf419e` stable across all four review
  attempts; 198-file SHA256 MANIFEST).
- Reviewer sessions: see `REVIEW_SESSION.json` (4 fresh sessions, no
  self-review).

## Selected fix (one paragraph)

**T3 + C1(scoped)**: the collision kernel's moment inverse transform is
carried out in f64 (exact f64 inverse matrix `inv_M_f64` + f64
accumulator, final f32 cast), removing the audit's root cause
(`sum_s inv_M[s,0] = 1 + 2^-26` stored-f32 defect) rather than
compensating it; the colour channel gains a per-colour zeroth-moment
projection after equilibrium/recoloring, scoped to interface nodes
(`cc > 0`) where the audit measured the leak. Selection was forced by
the unchanged V0 **A2 stationarity gate**: under T0 the uniform
single-phase state is a bit-exact frozen fixed point; every f32-path
table/correction candidate (T1, T2, unscoped C1) breaks it
(max|v| → 4.46e-6 > 1e-6); only the T3 f64 roundtrip preserves it
exactly (0.0). T1 additionally carries a −1.5e-8 x/y systematic local
momentum defect (attempt-1 review reproduction); T2 fails the ≥10×
total gate (−2.76e-9/step monotone); T4 confirmed the negative control.

## Headline numbers

- C3 60k GPU: total-channel drift +1.55e-8/step (R²=1.0000) →
  **+1.19e-11/step** (R²=0.62, no trend) ≈ 1300×; colour +6.76e-9 →
  **−6.43e-10** (10.5×, within the ≤2e-9 target; bounded one-sided
  floor, sign disclosed); CPU consistent (−3.3e-11 / −6.9e-11).
- Performance: net zero (2479 vs 2465 steps/s steady on C3); one 19×19
  f64 table + 10 per-node f64 probe fields (writes compiled out when
  dbg off).
- F2 V0 suite (thresholds unchanged): all PASS; A2 exact 0.0;
  Poiseuille eff 0.9933→1.0010; Laplace/contact within their T0
  run-to-run spreads (documented, not fix-attributable).
- F3 V1c: static C = 0.7902/0.7513/0.8070/0.7834 (baseline
  0.7902/0.7511/0.8067/0.7795); **a26 = 1.0389, a40 = 1.0581** (both
  gates PASS).
- F4 V2: mirror error 4.96e-4 lu (2.6× better); max ε_r/ε_b
  7.49e-5/**1.98e-4** — 3.4× better and **inside the original 5e-4 g6
  value**; single trapped cluster; NOT_REACHED; bulk ρ guardrail
  unchanged.

## Search

Two mandatory passes executed before code changes
(`results/conservation_fix/LITERATURE_AND_IMPLEMENTATION_SEARCH.md`):
no direct literature precedent for the defect (none claimed); new
finding: the 2D canonical D2Q9 solver carries the same defect class
(+7.45e-9 = 2^-27); Dubois/Philippi projection papers name-similar but
mechanistically unrelated; C2 = none (justified). Sources downloaded
(arXiv 2412.17426, **2112.08926** — the initial 2202.05643 download was
a wrong-source error caught by the attempt-1 review and replaced).

## Review history (documentation iterations)

Attempt 1 (B1–B5): wrong literature source asserted as verified;
momentum/"no monotone bias" claims vs CSV; F2 before-values not from
committed logs; §17 missing. Attempt 2: seven leftovers. Attempt 3: one
hand-typed R². Attempt 4: **PASS** — with the reviewer's process note
that derived tables should be generated from committed JSON (adopted
for the final fix). All revisions were documentation-only; solver,
tests, and raw evidence byte-identical from attempt 1 onward.

## Consequences

- The conservation preconditions for V3 are substantively met (total
  channel closed; colour within contract target, sign disclosed).
- V3 contract still requires rewrite + external authorization; V3 HOLD
  stands until the owner-run external scientific review accepts this
  package.
- Out-of-scope observations for future work: 2D solver carries the same
  defect class (2D line frozen, no action); probe fields could use lazy
  allocation; the original V2 g6 value 5e-4 is now met by the fixed
  solver, closing the loop opened by the V2 review.

## Evidence

- product: `results/conservation_fix/**` @ `e256b48` (EXECUTION_REPORT,
  CANDIDATE_COMPARISON, LITERATURE search, summary.json, f0_/f1_ runs,
  levelc_v1c_fix/, levelc_v2_fix/, logs, figures + generator).
- reviews: `.agent/evidence/BI-SOLVER-CONSERVATION-FIX-001/`
  (REVIEW.md PASS + three CHANGES_REQUESTED attempts + REQUEST +
  SESSION + this SUMMARY).
- living document: ALGORITHM_IMPLEMENTATION_EVOLUTION.md **§25**
  (+ figures) on this control branch.
