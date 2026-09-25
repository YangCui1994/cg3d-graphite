# Solver Conservation Fix — External Scientific Review

## Binding

- Task: `BI-SOLVER-CONSERVATION-FIX-001`
- Product branch: `agent-task/BI-SOLVER-CONSERVATION-FIX-001`
- Base: `1f5ee76fa183b42dd0ffcb291f389c3f1974a147`
- Candidate: `e256b4857a6e51510b75358994d7c5bcc742781e`
- Fresh reviewer attempt 4: `PASS`
- External scope: scientific acceptance of the solver fix and whether V3 can be reconsidered

## Executive decision

**Decision: CHANGES_REQUESTED.**

The **total-distribution conservation fix is accepted**.

The selected T3 inverse-transform path is strongly supported by the evidence:

- the f32 stored-inverse defect is reproduced;
- T4 shows that f64 accumulation with the unchanged f32 inverse does not remove it;
- T1 removes the mass defect but creates a systematic local momentum defect and fails A2;
- T2 fails the required long-horizon improvement;
- T3 preserves the V0 A2 exact frozen state and reduces the total-channel drift by roughly three orders of magnitude;
- V0, V1c and V2 scientific regressions remain inside their unchanged gates.

However the **colour channel is not yet closed under the frozen task contract**.
It meets the numerical drift-magnitude target, but two independent contract
conditions remain unresolved:

1. the 60k colour series is still a persistent one-sided drift, not a
   demonstrated bounded floor;
2. the selected scoped-C1 correction does not remove the local one-sided
   colour residual in every representative F0 geometry.

V3 remains **HOLD**.

No new total-channel solver design is requested.

---

# 1. Total-channel fix — accepted

The selected total path uses the un-cast f64 inverse matrix and f64 inverse
accumulation before storing the reconstructed populations back to f32.

The relevant root-cause identity before the fix is:

[
sum_s (mathrm{inv_M}_{f32})_{s0}-1
=
1.4901161193847656	imes10^{-8}.
]

The audited production drift was of the same order:

[
r_{M,f}approx1.5	imes10^{-8}/step.
]

The selected T3+C1s C3 60k run gives:

[
r_{M,f}
=
1.1944	imes10^{-11}/step.
]

The increment signs are approximately symmetric and the fitted trend is weak
((R^2approx0.625)).

The T4 negative control is particularly persuasive:

[
R_f(T4)
approx+1.494	imes10^{-8},
]

showing that a f64 accumulator with the unchanged f32 inverse matrix retains
the original bias.

Therefore the total-channel root-cause/fix chain is accepted.

---

# 2. T1/T2 rejection — accepted

## T1

The host-projected f32 inverse can satisfy the zeroth-column sum, and its
long-horizon total drift is small.

But the committed comparison shows that T1 introduces a systematic local
momentum residual of approximately:

[
(-1.49,-1.49,0)	imes10^{-8}
]

per node in the relevant x/y components, and the unmodified V0 A2 test moves
from a bit-exact frozen state to:

[
u_{max}approx4.46	imes10^{-6}>10^{-6}.
]

T1 is therefore correctly rejected even though its mass drift is attractive.

## T2

T2 closes the local zeroth moment more directly but leaves a persistent total
drift:

[
r_{M,f}approx-2.76	imes10^{-9}/step,
]

which does not meet the required >=10x improvement from the audited baseline.

T2 is correctly rejected.

---

# 3. V0 / V1c / V2 regressions — accepted

The selected T3 + scoped-C1 candidate preserves the previously validated
scientific behaviour.

## V0

- Level A: PASS
- A2: (u_{max}=0) exactly
- Poiseuille: 1.0010, inside the unchanged gate
- Laplace: inside the unchanged gate
- contact angle: inside 30 +/- 6 deg
- Compute_C / postprocessing: PASS

The observed Laplace/contact before-after differences are smaller than or
comparable to the run-to-run spread of the baseline and should not be
attributed as a physical improvement caused by the conservation fix.

## V1c

[
a_{26}=1.0389,qquad a_{40}=1.0581.
]

Both remain inside:

[
|a_h-1|le0.10.
]

The static slit sequence remains consistent with the accepted V1c calibration.

## V2

- max front mirror error: (4.96	imes10^{-4}) lu;
- one trapped gas cluster remains;
- no unexplained fragmentation;
- interaction remains NOT_REACHED;
- bulk-density range remains consistent;
- (epsilon_bapprox1.98	imes10^{-4}), now below the original
  (5	imes10^{-4}) V2 conservation value.

The fix does not materially alter V2 qualitative topology.

---

# 4. Blocking finding B1 — the colour residual is not a bounded floor

The selected C3 60k colour result is:

[
r_{M,c}
=
-6.4253	imes10^{-10}/step
]

with:

[
R^2=0.9827.
]

It meets both numerical magnitude requirements:

- >10x improvement over the baseline;
- (|r_{M,c}|<2	imes10^{-9}/step).

But the frozen contract also requires:

> no monotone sign bias attributable to the correction itself.

The committed series has 299/300 negative checkpoint increments.

I independently refit three 20k segments of the same committed 60k series:

| interval | colour slope / step | R2 | positive-increment fraction |
|---|---:|---:|---:|
| 1–20k | -9.56e-10 | 0.9940 | 0.01 |
| 20–40k | -5.77e-10 | 0.9992 | 0.00 |
| 40–60k | -5.22e-10 | 0.9995 | 0.00 |

The rate decreases in magnitude, but the final 20k interval is still an
extremely linear negative trend.

Therefore the current evidence does **not** establish a bounded floor or
plateau.

The correct description is:

> a small, systematic one-sided residual colour drift that is more than one
> order of magnitude smaller than the pre-fix drift and already inside the
> engineering magnitude target.

That may ultimately be acceptable for V3, but accepting it requires an
explicit owner re-scope of the frozen no-sign-bias gate. It cannot be silently
called closed.

---

# 5. Blocking finding B2 — F0 colour closure is geometry-dependent

The frozen F0 contract requires representative C0-C3 states and states:

> if a fix improves global drift while leaving a systematic local closure
> bias, it cannot be selected.

For the selected T3+C1s candidate, the production-relevant C3 geometry is
well behaved:

[
R_rapprox9.8	imes10^{-11},
quad
R_bapprox2.0	imes10^{-10}
]

with positive fractions approximately 0.51 / 0.49.

However the same committed `f0_T3C1s/f0_report.json` also contains the C1
periodic two-phase geometry:

[
R_rapprox+3.88	imes10^{-9},
quad
R_bapprox+3.10	imes10^{-9},
]

with:

[
frac_{+}(R_r)approx0.758,
quad
frac_{+}(R_b)approx0.761.
]

That is a materially one-sided local residual.

The current scoped correction is intentionally applied only when `cc>0` in
order to preserve the exact A2 frozen state. This is a reasonable design
choice, but the evidence package does not yet determine whether the C1
residual comes from:

- pure/frozen nodes where a local arithmetic residual is non-accumulating;
- mixed nodes with `cc==0`;
- another region not covered by the current correction scope.

The final fresh reviewer largely evaluates F0 using the C3 result and does not
close this cross-geometry issue.

Thus the literal F0 hard gate is not yet satisfied.

---

# 6. Required narrow colour-closure rework

Do not revisit T0-T4 total-channel candidate selection.

Freeze the accepted T3 total path and perform a small colour-only closure task.

## 6.1 Local residual partition

For selected T3 + current scoped C1, measure (R_r,R_b) separately for:

1. `cc > 0`;
2. `cc == 0`;
3. pure-phase nodes;
4. mixed two-colour nodes;
5. wall-adjacent vs non-wall nodes.

Do this at least for the C1 periodic two-phase and C3 slit cases.

The objective is to determine which nodes produce the remaining one-sided F0
residual.

## 6.2 C1 periodic long-horizon check

Run the selected fix on the periodic two-phase C1 isolation case at sufficient
horizon to determine whether the local C1 bias produces accumulating component
mass drift.

If the biased local residual belongs only to a bit-exact/non-accumulating
fixed-point population, document that explicitly.

If it accumulates, it must be corrected.

## 6.3 C3 colour-tail check

Do not call the current C3 colour result bounded.

Either:

- remove the remaining systematic colour drift with a defect-scoped
  correction that preserves A2; or
- provide enough additional horizon/scaling evidence for the owner to
  explicitly accept a calibrated systematic residual and amend the
  no-sign-bias clause.

A useful candidate to test is an exact/local rest-population component
closure on the active mixed/interface population, because (e_0=0) preserves
momentum by construction. This is a candidate, not a mandated fix; compare it
against the current weighted C1 projection.

Any new colour correction must rerun at minimum:

- A2;
- C3 long-horizon colour drift;
- V1c hydraulic gates;
- V2 conservation/topology.

A full repeat of the T0-T4 total candidate matrix is not required.

---

# 7. Literature metadata corrections

The search conclusion itself is sound:

- no direct published precedent was found for this repository's specific
  f32 inverse-column-sum defect;
- FP32 is not inherently unsuitable for LBM;
- colour-gradient formulations treat conservation as a structural constraint.

Two product-report citations are factually incorrect and must be repaired.

## 7.1 Dubois & Philippi

The published 2025 paper is:

François Dubois and Paulo Cesar Philippi,
"Multiple relaxation times lattice Boltzmann schemes with projection",
Physics of Fluids 37, 037179 (2025).

Correct DOI:

`10.1063/5.0254041`

not the `10.1063/5.0255650-family` string currently in the product report.

This projection method is still mechanistically unrelated to the repository's
floating-point conservation defect.

## 7.2 3D D3Q19 colour-gradient paper

The paper associated with PMID 22680576 is:

Haihu Liu, Albert J. Valocchi, Qinjun Kang,
"Three-dimensional lattice Boltzmann model for immiscible two-phase flow
simulations",
Physical Review E **85**, 046309 (2012).

DOI:

`10.1103/PhysRevE.85.046309`.

It is not "Leclaire et al., PRE 86".

The control literature memo must be corrected in the same documentation pass.

---

# 8. Non-blocking observations

1. The phrase "full-f64 moment roundtrip" is broader than the implemented T3
   path. The production change is specifically the **inverse moment transform**
   using the f64 inverse and f64 accumulation while the solver state and
   forward path remain primarily f32. Future documentation should use the
   narrower description.
2. The reported 2D D2Q9 same-family defect (+7.45e-9) is plausible but is not
   independently verifiable from the remotely visible candidate because the
   referenced canonical file is not present at the cited repository path.
   If the claim is retained in the durable technical record, commit a minimal
   reproduction artifact or identify the durable source path.
3. The unconditional debug-field allocation is not a scientific blocker; it is
   a later implementation-cleanup item.

---

# 9. Decision

**Decision: CHANGES_REQUESTED.**

Accepted now:

- total-channel root cause;
- T3 total-channel fix;
- rejection of T1/T2/T4;
- unchanged V0 gates;
- V1c hydraulic/wetting regressions;
- V2 symmetry/topology regression;
- candidate comparison methodology.

Not yet accepted:

- statement that the colour channel is closed/bounded;
- literal F0 colour closure across representative C0-C3 states;
- V3 authorization.

Required sequence:

```text
T3 total fix ACCEPTED
        ↓
narrow colour residual localization / closure
        ↓
fresh reviewer
        ↓
external scientific review
        ↓
only then reconsider revised V3
```

No V3 work is authorized by this review.
