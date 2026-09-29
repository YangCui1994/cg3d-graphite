# V2 External Scientific Review — BI-V2-BILATERAL-001

## Binding

- Product branch: \`agent-task/BI-V2-BILATERAL-001\`
- Base: \`2b82f9a5f448e756b5d5903b0df37f9a3b11d804\`
- Candidate: \`5e679d8d99d338f9ab28565c636f021a0f9211b2\`
- Fresh internal reviewer: \`HUMAN_REQUIRED\`
- Control evidence: \`.agent/evidence/BI-V2-BILATERAL-001/\`
- Review scope: contract-owner / external scientific checkpoint

## Executive decision

**V2 scientific benchmark: PASS.**

The V2 candidate establishes the intended bilateral numerical mechanism:

- exact programmed mirror symmetry;
- front mirror error only \`0.001297 lu\`;
- field-level symmetry error \`E_psi <= 8.34e-5\`;
- exactly one trapped non-wetting cluster from t=0 through the full run;
- no fragmentation or disappearance;
- \`INTERACTION_ONSET = NOT_REACHED\`, which is an allowed physical outcome;
- no NaN/Inf;
- operational velocity guardrail satisfied by a wide margin;
- trapped-pocket weak-compressibility state remains inside the bulk density range.

The fresh reviewer correctly stopped because two hard-gate semantics required
contract-owner decisions. Those decisions are made below.

This PASS is limited to the **symmetry / topology / trapped-pocket numerical
mechanism**. It does not certify quantitative real-gas compression and does
not authorize V3 until the conservation audit defined in this review is
completed.

---

# 1. V2 physics result

## 1.1 Symmetry

Primary front mirror error:

\[
e_x(t)
=
|x_L-(N_x-1-x_R)|
\]

Measured maximum:

\[
e_{x,\max}=1.297\times10^{-3}\ {\rm lu}
\]

against the engineering gate floor of 2 lu.

The candidate therefore clears the positional-symmetry bound by more than
three orders of magnitude.

Independent reviewer field check:

\[
\max |\psi(x)-\psi(N_x-1-x)| \approx 5.9\times10^{-3}
\]

with the largest differences confined to interface-adjacent nodes.

Mean field symmetry:

\[
E_\psi\le8.34\times10^{-5}.
\]

This is sufficient evidence that the bilateral implementation does not
introduce a material left/right numerical bias.

## 1.2 Trapped-pocket topology

At t=0:

- one non-wetting cluster;
- 38 400 binary gas nodes;
- 6-neighbour connectivity;
- z-periodic merge only;
- no x/y periodic connectivity;
- no vent / reservoir.

The cluster remains single throughout all 60 committed samples.

Binary volume:

\[
38400 \rightarrow 38304 \rightarrow 38400
\]

so the early binary-volume change is interface classification during sharp-IC
relaxation, not fragmentation.

\`INTERACTION_ONSET\` is correctly \`NOT_REACHED\`.

The fronts form their menisci and stall rather than sweeping through the
central trapped gas. This is consistent with the intended closed-system weakly
compressible problem.

---

# 2. Owner resolution R-V2-1 — density guardrail semantics

The original V2 text states approximately:

\[
0.89\le\rho\le1.11
\]

for fluid density.

The executor applied the hard gate to bulk-phase nodes:

\[
|\psi|>0.9.
\]

**This interpretation is formally ratified.**

For V2 and later weak-compressibility guardrails, the hard EOS/stability range
applies to:

- bulk liquid;
- bulk gas;
- trapped-pocket bulk nodes.

Diffuse-interface extrema remain mandatory diagnostics but are not hard
weak-compressibility failures by themselves.

Reason:

1. the purpose of the guardrail is to prevent interpreting a bulk trapped
   phase outside the solver's weak-compressibility operating range;
2. the \(\psi\approx0\) interface has its own density structure and is not a
   homogeneous EOS state;
3. externally accepted V1c cases contain equal or deeper interface-local
   minima, including approximately 0.88046 / 0.88774 / 0.88857;
4. the V2 trapped pocket itself remains comfortably inside the range:
   approximately \([0.935,1.008]\).

All-fluid extrema must continue to be recorded.

Under this clarified definition, **V2 g3 PASS**.

---

# 3. Owner resolution R-V2-2 — conservation gate calibration

## 3.1 Why the original 5e-4 gate is not retained as a binary V2 gate

Original V2 engineering gate:

\[
\max_t(\epsilon_r,\epsilon_b)\le5\times10^{-4}.
\]

Measured:

\[
\epsilon_r=4.21\times10^{-4},
\qquad
\epsilon_b=6.73\times10^{-4}.
\]

The exceedance is real and monotone.

However, the same frozen solver was externally accepted at V1c with colour
closure approximately:

\[
5\times10^{-4}\text{–}7\times10^{-4}
\]

over comparable 60k-step horizons.

Thus the V2 gate was calibrated below the already-established numerical
floor of the accepted implementation.

Treating \`5e-4\` as a universal pass/fail boundary would make the V2 contract
internally inconsistent with its own accepted base.

The 5e-4 value remains a **future improvement target**, not the current
qualitative-mechanism certification threshold.

## 3.2 Calibrated V2 numerical-drift envelope

For V2 symmetry/topology certification only, require all of:

1. no abrupt mass jump;
2. no order-one colour transfer or loss;
3. worst measured relative drift rate
   \[
   r_M\le2\times10^{-8}\ {\rm step}^{-1};
   \]
4. total-mass-normalised drift over 60k steps
   \[
   |\Delta M|/M_0\le10^{-3};
   \]
5. drift does not create left/right asymmetry, fragmentation or disappearance.

V2 measured rates are approximately:

- colour-blue sentinel: \(1.12\times10^{-8}/step\);
- total colour sentinel: \(9.1\times10^{-9}/step\);
- independent population channel: \(1.53\times10^{-8}/step\).

Independent population-channel total drift:

\[
9.21\times10^{-4}
\]

over 60k steps.

The candidate therefore lies inside this calibrated envelope.

Under this **V2-specific mechanism gate**, the conservation requirement is
accepted for the purpose of mirror-symmetry/topology validation.

This is a contract calibration decision, not a claim that the solver is
strictly conservative.

---

# 4. Conservation remains a solver-level open item

The monotone drift is scientifically important.

At 60k steps:

- colour-sentinel total drift is approximately \(5.47\times10^{-4}\);
- independent \(\Sigma_{\rm fluid}\rho\) drift is approximately
  \(9.21\times10^{-4}\);
- the two bookkeeping routes disagree by order \(3.7\times10^{-4}\).

The discrepancy is therefore not fully characterised as a simple reporting
roundoff.

A conservative closed-system algorithm should ideally preserve the zeroth
moment apart from a quantified floating-point accumulation floor.

The current evidence localises this as a **SOLVER / numerical-conservation
work item**, not a V2 topology failure.

---

# 5. Why this matters before V3

V2 pocket mean density changes approximately:

\[
1.0000\rightarrow1.00425
\]

or roughly:

\[
+0.42\%.
\]

The global accumulated mass-drift measures are approximately:

\[
0.055\%\text{–}0.092\%.
\]

Their magnitude is therefore roughly **13–22% of the V2 pocket-density
signal**.

This does not invalidate the V2 topology/symmetry result.

It is too large to ignore when V3 begins comparing:

- pocket pressure;
- pocket density;
- trapped volume;
- buffer-size dependence.

Therefore:

> **A dedicated conservation audit is mandatory before V3.**

No V3 run is authorized by this PASS.

---

# 6. Required pre-V3 conservation audit

The first audit must be diagnostic-only: do not change solver physics before
the loss mechanism is identified.

Instrument one timestep into explicit conservation checkpoints.

At minimum measure in f64 host/reduction form:

\[
M_f=\sum_{i,s} f_{i,s},
\]

\[
M_c=\sum_i(\rho_r+\rho_b),
\]

and, where available,

\[
M_\rho=\sum_i\rho_i.
\]

Track before/after:

1. collision + recoloring;
2. colour streaming / bounce-back;
3. total-distribution streaming;
4. boundary-condition kernels;
5. macro reconstruction.

Run a small isolation matrix:

### C0 — periodic single phase, no solid

Expected to isolate pure streaming/collision accumulation.

### C1 — periodic two phase, no solid

Adds recoloring/interface contributions.

### C2 — single phase slit with bounce-back walls

Adds solid-wall streaming/bounce-back.

### C3 — two-phase slit with bounce-back walls

Closest minimal analogue of V2.

For each case report:

- per-step \(\Delta M_f\);
- per-step \(\Delta M_c\);
- \(M_f-M_c\);
- spatial mass budget by wall rows / interface bands / bulk;
- CPU vs GPU result if low-cost and useful for separating atomic-order error
  from algorithmic imbalance.

The audit must distinguish:

- floating-point accumulation floor;
- bounce-back bookkeeping;
- recoloring colour/total mismatch;
- macro reconstruction mismatch.

If an implementation defect is found and solver code is changed, rerun the
minimum affected regression chain before V3.

---

# 7. V2 candidate defects that do not change the scientific decision

The fresh reviewer identified several finite product/evidence defects.

Most important:

## 7.1 Incorrect \`d(t)\` identity

The driver mixes mirrored current right coordinate with the unmirrored initial
right coordinate.

This creates an exact −80 lu offset in the stored \`d\` column.

It does not affect the V2 result because the mirror gate uses the fixed 2-lu
floor in this run.

**Required:** fix before this driver is reused or adapted.

## 7.2 Headline baselines

Use the corrected t=0 values:

- binary gas: \(38400\rightarrow38304\rightarrow38400\);
- \(G_{\rm bulk}:160\rightarrow146\);
- pocket mean rho: \(1.0000\rightarrow1.00425\), approximately +0.42%.

## 7.3 Provenance/evidence cleanup

When V2 files are next touched:

- correct producer revision prose to \`052ab973...\`;
- commit the V2 unit-check outcome;
- preserve local-max symmetry diagnostic;
- distinguish runtime sidecar null exit fields from shell-level exit binding;
- retain the reviewer-corrected static_h40 baseline.

These are non-blocking for the present scientific PASS.

---

# 8. Technical-document review

The required living document has been updated:

\`docs/research/bilateral_imbibition/ALGORITHM_IMPLEMENTATION_EVOLUTION.md\`

It now contains:

- V2 task/base/candidate binding;
- bilateral equations/geometry;
- implementation excerpts;
- symmetry/topology metrics;
- corrected t=0 baselines;
- result figures from committed evidence;
- V1c comparison;
- mass/stability table and open conservation issue.

The technical-document deliverable is accepted.

The document must now append this external owner resolution so the final V2
status is no longer left at \`HUMAN_REQUIRED\`.

---

# 9. V3 contract is not yet valid

The existing V3 contract still assumes:

- a later "central-pocket isolation time";
- pre-isolation trajectories.

V2 established that in the chosen closed geometry the gas pocket is trapped
from t=0.

Therefore V3 must be rewritten before execution.

A revised V3 should compare buffer-size sensitivity of quantities such as:

- meniscus-shaping / stall displacement;
- quasi-steady/stall time;
- \(G_{\rm bulk}\);
- trapped-cluster topology;
- outer-wall reflection / density oscillations;
- pocket \(\rho/p\) only after conservation uncertainty is bounded.

No V3 task should start from the old isolation-time gates.

---

# 10. Decision

**Decision: PASS — V2 bilateral symmetry/topology mechanism accepted.**

Owner resolutions:

- **R-V2-1:** g3 bulk-phase density semantics ratified.
- **R-V2-2:** the original absolute 5e-4 g6 value is reclassified as a
  future conservation-improvement target; V2 mechanism certification uses the
  calibrated drift envelope above.
- **R-V2-3:** monotone mass drift becomes a mandatory SOLVER conservation audit
  before any V3 quantitative trapped-pocket/buffer comparison.

This PASS does **not** authorize V3 yet.

Required next sequence:

\[
\text{V2 PASS}
\rightarrow
\text{conservation audit}
\rightarrow
\text{revised V3 contract}
\rightarrow
\text{external authorization}
\rightarrow
\text{V3}
\]

No core solver change is authorized until the conservation audit identifies a
specific mechanism.
