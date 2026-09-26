# External Review — BI-DEEPSEEK-TRANSITION-001

## Binding

- Base: `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`
- Candidate: `c12e2fc4f0c756dec9c93fc71d508e95d283485b`
- Product branch: `agent-task/BI-DEEPSEEK-TRANSITION-001`
- Fresh reviewer: DeepSeek, independent session
- Fresh-review decision: PASS

## External decision

**PASS — DeepSeek transition/calibration accepted.**

The task demonstrates sufficient capability for DeepSeek to act as the next
staged executor and fresh reviewer under the artifact-driven harness.

This decision does **not** promote the readiness document itself into a frozen
V3 contract. Several scientific proposals in that document require owner-level
normalization before execution.

## 1. Why the model transition passes

### Repository / scope discipline

The candidate descends from the exact accepted base and changes only seven
files under `results/model_transition/`.

No solver, test, boundary-condition, physical-parameter or accepted gate file
is modified.

No V3 simulation, periodic-BC simulation, graphite, separator, gap or PCS work
was performed.

### Independent numerical recomputation

The executor recomputed accepted metrics from raw committed evidence rather
than copying summaries. The fresh reviewer then independently recomputed the
same quantities again.

The external review agrees with the reported values, including:

- periodic C1 240k colour slope ~ +1.8046e-11 / step, R2 ~ 0.2797;
- four 60k C1 slopes ~ +1.93e-10, -5.04e-12, +1.24e-11, -4.66e-13;
- C3 120k colour slope ~ +2.6929e-12 / step, R2 ~ 0.4146;
- four 30k C3 slopes ~ +2.23e-11, -4.11e-12, +3.70e-12, +3.85e-12;
- V2 max blue relative drift ~ 5.1584e-7;
- V2 mirror error ~ 7.4e-4 lu;
- one trapped gas cluster throughout;
- INTERACTION_ONSET = NOT_REACHED.

This is sufficient evidence that DeepSeek can read the repository state,
recover definitions from artifacts, reproduce calculations, and preserve stop
boundaries.

### Reviewer quality

The fresh reviewer did not merely rubber-stamp the executor. It independently
identified four non-blocking issues, including:

- a hand-transcribed E_psi digit;
- ambiguous V1c-generation provenance;
- the t=1000 pocket-density comparison lying inside the producer-declared
  initial transient;
- an asymmetric fluid mask in the read-only seam probe.

That is a positive calibration result for the reviewer role.

## 2. V3 readiness document — accepted as design input, not as contract

The document correctly retires the obsolete isolation-time / pre-isolation
framing.

The revised scientific question is appropriate:

> how finite liquid-buffer thickness B changes the trapped-pocket state,
> compartment redistribution, interface configuration and closed-wall coupling
> in a system where the gas is trapped from t=0.

The proposed core sweep B = 40 / 80 / 160, with B=320 conditional, is a
reasonable starting design.

The B=80 case should remain a reproduction control.

## 3. Closed-system balance — useful, but its derivation must be tightened

The proposed leading-order result

[
Delta ho_g
=
rac{P_c}{c_s^2}
rac{V_l}{V_g+V_l}
=
3P_crac{V_l}{V_g+V_l}
]

is correct for the intended linearized two-compartment model **provided that
the red/liquid and blue/gas component masses are separately conserved**.

The readiness document currently states rigid-volume closure and the EOS but
does not explicitly write the component-mass constraints that close the
derivation.

The revised V3 contract should state, to first order,

[
V_l,Deltaho_l+ho_l,Delta V_l=0,
qquad
V_g,Deltaho_g+ho_g,Delta V_g=0,
qquad
Delta V_l+Delta V_g=0,
]

together with

[
Delta p = c_s^2Deltaho,
qquad
Delta p_g-Delta p_l=P_c.
]

This makes the assumptions explicit and prevents the algebra from appearing
underdetermined.

The model should be labelled a **leading-order sharp-compartment
compressibility balance**, not an exact model of the diffuse-interface slow
mode.

## 4. The t=1000 0.7% agreement is not a validation gate

The readiness document notes that the balance predicts the t=1000 pocket
density within ~0.7%.

The fresh reviewer correctly found that t=1000 lies inside the V2 producer's
declared initial-condition relaxation interval.

Therefore:

- keep the 0.7% result as a consistency observation;
- do not use it as evidence that the balance is quantitatively validated;
- do not derive the V3 acceptance tolerance from this one sample;
- V3 should compare the full B-dependence and fitted late-state/asymptotic
  response.

The fact that the t=60000 difference is larger (~2.3%) reinforces this
requirement.

## 5. Periodic BC decision

The readiness document finds a persistent z-dependent numerical structure of
order ~5e-4 in psi from an initially z-uniform state.

This is scientifically useful and should not be dismissed as random noise.

However a full P0-P3 periodic suite does not need to block V3, because:

- V3 changes B only in x;
- the live periodic topology remains z-only and identical across cases;
- no solid or intended interface crosses the z seam in V3;
- B=80 reproduces the accepted V2 geometry.

Therefore the external decision is:

**the full periodic-BC suite is not a prerequisite for V3.**

But the readiness proposal N4 should **not** become a hard invariant in its
current form ("z-spread must not exceed the V2 level").

Changing nx changes the execution problem and can change numerical
round-off/statistical extrema even when the topology is unchanged.

Instead V3 should:

1. record z-spread of psi and rho for every B;
2. normalize/report mean/RMS or percentile measures as well as maxima;
3. compare their scale with the B-dependent scientific signal;
4. trigger a focused periodic/z-resolution investigation only if z-structure
   changes materially with B or becomes comparable to the signal being
   interpreted.

P3 remains mandatory before the first z-periodic porous geometry whose solid
structure actually wraps the seam.

## 6. Proposed hard invariant N3 should be relaxed/reformulated

The readiness document proposes requiring conservation sentinels to stay
inside the exact post-fix measured level rather than the older engineering
envelope.

That is too implementation-specific for a B sweep with different nx/domain
sizes.

The formal V3 contract should instead retain:

- the established engineering conservation gate;
- the accepted no-persistent-one-sided-drift semantics;
- a B=80 reproduction check against the accepted V2 case;
- explicit reporting of how the residual scales with domain size.

A larger B case should not fail merely because a machine-level residual is
larger than the exact B=80 measured value while remaining far inside the
validated numerical floor.

## 7. Slow-mode fitting

The readiness document's recommendation to compare fitted asymptotes rather
than arbitrary equal-time snapshots is directionally correct.

But the formal contract should not mandate a single exponential

[
y(t)=y_infty+A e^{-t/	au}
]

before the data demonstrate that form.

Use a hierarchy:

1. test whether a single exponential is adequate over a predeclared late
   window;
2. if not, report a nonparametric late-window slope/plateau measure or another
   declared form;
3. do not add fit complexity solely to obtain convergence.

This prevents the fitting model from becoming the new source of arbitrary
degrees of freedom.

## 8. V1c / front-position caution

The readiness document correctly carries forward that the V2 d(t) /
interface-position identity has an unresolved non-blocking defect.

Therefore front position should remain a diagnostic in revised V3, not the
primary quantitative buffer-sensitivity observable.

Primary observables should be:

- pocket mean density / pressure;
- component/compartment mass redistribution;
- symmetry and topology;
- outer-wall adjacent pressure/density response;
- conservation sentinels.

## 9. Harness findings from the transition

Two process issues should be carried forward:

1. `.agent_runtime/` is described in repository documentation as ignored
   scratch, but the reviewer found it is not actually ignored. Fix the
   repository ignore/configuration before relying on "clean worktree" checks.
2. Final-batch exit-code capture remains weaker than the intended durable
   provenance model. Revised V3 should store machine-readable per-case
   `run.exit` or equivalent.

These are harness hygiene issues, not scientific blockers.

## 10. Calibration verdict

DeepSeek demonstrated:

- correct project-state reconstruction;
- exact raw-evidence recomputation;
- independent fresh review;
- useful adversarial checking of executor claims;
- scope discipline;
- explicit uncertainty / owner-decision handling.

**DeepSeek is accepted for the next staged V3 executor/reviewer workflow.**

Recommended operating pattern remains:

```text
DeepSeek executor
-> immutable candidate/evidence
-> fresh DeepSeek reviewer
-> ChatGPT external scientific review
```

## 11. Next authorization boundary

Allowed next step:

- write the revised V3 buffer-sensitivity contract incorporating the external
  corrections above.

Not yet authorized by this review:

- execute V3;
- execute the full periodic-BC suite;
- graphite / separator / gap / PCS work.

