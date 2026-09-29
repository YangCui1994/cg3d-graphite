# Colour Closure External Scientific Review — BI-COLOUR-CLOSURE-001

## Binding

- Product branch: `agent-task/BI-COLOUR-CLOSURE-001`
- Base: `e256b4857a6e51510b75358994d7c5bcc742781e`
- Candidate: `6c30260dfe0c8b61ea9609e6bffa5c487312cf06`
- Fresh reviewer: PASS
- Control evidence: `.agent/evidence/BI-COLOUR-CLOSURE-001/`

## Executive decision

**Decision: PASS.**

The remaining colour-channel closure problem is sufficiently resolved for the
project to reconsider V3.

This PASS is based on four independent facts:

1. the previously biased local node classes now close at numerical epsilon;
2. the periodic-C1 accumulating colour leak is converted from a persistent
   linear trend into a decaying transient;
3. the C3 colour drift becomes trendless at the tested long horizons;
4. the unchanged V0/V1c/V2 regression chain remains inside all frozen gates.

The accepted total-channel T3 path remains frozen.

This PASS does not revive the old V3 contract. V3 must still be rewritten
before execution.

---

# 1. Residual mechanism

The diagnosis separates two pre-fix mechanisms that partially cancelled:

1. positive local equilibrium-construction leakage at non-frozen
   `cc==0` pure-like nodes near the diffuse interface;
2. negative f32 scatter-accumulate rounding in the colour transport.

The committed C3 budget for the base implementation is consistent with this
decomposition.

A single-intervention fix exposes the opposite-sign mechanism, which explains
why the closure-only and accumulation-only candidates do not satisfy the
frozen gates.

The selected combination:

`T3 + C1X + A2`

addresses both mechanisms:

- C1X extends the local weighted closure to the actual non-frozen residual
  class;
- A2 carries the post-equilibrium colour closure/transport arithmetic and
  accumulation in f64;
- the accepted T3 total-distribution path is unchanged.

The remaining component-mass noise is dominated by the eventual f64-to-f32
component-density store, not by a persistent node-class closure defect.

---

# 2. Local closure

For periodic C1, the base residual was approximately:

`R_r ~ +4.66e-9`

in the `cc==0` class, with a strongly one-sided sign distribution.

For the selected candidate, every reported node class closes at approximately
`1e-16` scale.

Representative committed values:

```text
ALL      R_r mean ~ -5.9e-17
cc==0    R_r mean ~ -5.5e-17
cc>0     R_r mean ~ -7.8e-17
```

The C3 classes show the same f64-epsilon structure.

The previous geometry-dependent local colour blocker is therefore closed.

---

# 3. Owner resolution of the no-sign-bias clause

The previous external review rejected the wording "bounded floor" because the
interim C3 series remained a persistent one-sided linear drift.

The selected candidate no longer has that behaviour.

## C3

Independent refit of the committed C3 candidate series:

```text
60k full:    +8.09e-12 / step, R2 ~ 0.583
120k full:   +2.69e-12 / step, R2 ~ 0.415
```

The 120k quarter slopes are approximately:

```text
+2.23e-11
-4.11e-12
+3.70e-12
+3.85e-12
```

with mixed increment signs.

There is no persistent one-sided late trend.

## Periodic C1

The base remains linearly accumulating at 240k:

```text
+1.05e-9 / step
R2 ~ 0.9986
```

with all four 60k quarters near `1e-9/step`.

The selected candidate at 240k gives:

```text
+1.80e-11 / step
R2 ~ 0.280
```

and quarter slopes:

```text
+1.93e-10
-5.04e-12
+1.24e-11
-4.66e-13
```

The final quarter is effectively flat with approximately balanced increment
signs.

## Owner decision R-CC-1

The frozen requirement was:

> no persistent one-sided bias attributable to the correction itself.

**R-CC-1: this requirement is satisfied.**

No gate re-scope is required.

Reason: the evidence now demonstrates loss of the persistent one-sided regime
at longer horizon. The project does **not** claim a mathematical proof that the
remaining floating-point residual is bounded for arbitrary time. Such a proof
was not the acceptance requirement.

The durable wording should therefore be:

> calibrated, horizon-decaying arithmetic residual with no persistent
> one-sided late trend over the tested horizons.

Do not use "bounded floor" as a stronger claim.

---

# 4. Candidate selection

The candidate comparison is accepted.

Notable rejected alternatives:

- rest-population closure: the intended correction can be below the f32 storage
  ULP and does not reliably close the stored populations;
- closure-only C1X/A0: exposes the negative f32 accumulation drift;
- accumulation-only C1/A1: exposes the positive local construction leak;
- intermediate f64-accumulation / f32-closure variants leave systematic
  residuals.

The combined C1X+A2 path is therefore mechanistically justified rather than
selected only by aggregate gate scores.

---

# 5. Regression chain

## A2 / V0

The unchanged production Level-A gate passes.

Uniform single phase remains exactly stationary in the tested A2 cases:

`max|v| = 0`.

The colour-specific load-bearing evidence is the exact phase stationarity and
the local closure/budget evidence; velocity alone is not a sensitive
colour-channel diagnostic.

Laplace, contact angle and Poiseuille remain inside their unchanged gates.

## V1c

The recomputed differential hydraulic slopes are:

[
a_{26}=1.0618,qquad a_{40}=1.0741.
]

Both satisfy:

[
|a_h-1|le0.10.
]

The static slit calibration remains in the accepted resolution band.

The non-gated diagnostic `L0/h` at h26 changes from approximately 3.02 to
2.64.

This does not block acceptance:

- the short-case dynamic Pc changes only at the ~1 percent scale;
- `L0` is an intercept obtained by subtracting two larger quantities and is
  correspondingly sensitive;
- the primary differential slope remains stable and inside the unchanged gate;
- V3 uses a closed finite-buffer geometry and does not depend on the open-system
  boundary-resistance intercept as a quantitative acceptance observable.

Carry the `L0/h` change as a diagnostic, not as an improvement.

## V2

The bilateral regression remains stable:

- one trapped gas cluster;
- no unexplained fragmentation;
- interaction remains NOT_REACHED;
- symmetry remains well inside the engineering gate;
- component-mass drift is substantially reduced.

Reported maximum blue relative drift:

[
epsilon_bapprox5.16	imes10^{-7},
]

well below the original:

[
5	imes10^{-4}
]

V2 engineering value.

---

# 6. Total-channel non-regression

The T3 total-distribution arithmetic is accepted as frozen.

C3 total drift remains far inside the accepted target:

```text
60k  ~ -2.48e-11 / step
120k ~ +1.01e-11 / step
```

No evidence requires reopening T0-T4.

---

# 7. Technical caveats

The following are non-blocking but should remain explicit.

1. "f64 colour pipeline end to end" is slightly broader than the implementation.
   The equilibrium helper itself still returns f32 populations; the relevant
   closure/recolor/transport path after that construction is carried in f64 and
   the exact component closure removes the equilibrium-sum mass residual.
   Prefer the phrase **f64 post-equilibrium colour closure/transport path**.
2. The A2 budget's old two-term identity no longer closes by itself because the
   remaining f64-to-f32 component-density store is a third arithmetic term.
   Future budget diagnostics should include that store-rounding term explicitly
   rather than reporting it only as an unexplained residual.
3. The product evidence records some regression runs from a dirty worktree,
   although the final candidate arithmetic was subsequently shown to be
   unchanged except for defaults/comments. Future runs should bind the exact
   clean candidate before execution.
4. Exit-code provenance remains weaker than ideal in this task package; future
   controller publication should machine-capture shell exit codes.

None changes the scientific decision.

---

# 8. Decision

**PASS — BI-COLOUR-CLOSURE-001 accepted.**

Accepted production numerical path:

```text
total_fix  = T3
colour_fix = C1X
acc_fix    = A2
```

Scientific status:

```text
single-front validation       CLOSED
bilateral trapped-pocket V2   CLOSED
total conservation defect     CLOSED
colour conservation defect    CLOSED for project engineering use
```

The remaining store-rounding residual is calibrated and non-persistent over
the tested long horizons; it is not claimed to be mathematically bounded.

## V3 authorization boundary

The conservation hold is lifted.

**A revised V3 buffer-sensitivity task may now be designed and authorized.**

The superseded old V3 contract must not be executed unchanged because it still
contains the obsolete "isolation-time / pre-isolation" framing. The central gas
is trapped from t=0 in the current closed bilateral geometry.

No graphite / separator / gap / PCS work is authorized yet.
