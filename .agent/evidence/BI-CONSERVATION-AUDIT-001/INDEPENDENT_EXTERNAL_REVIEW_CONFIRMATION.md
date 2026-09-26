# Independent External Review Confirmation — V2 + Conservation Audit

## Scope

Independent review of the completed V2 bilateral verification and the
follow-on conservation audit.

This review does not rely on the prior "external review" verdicts as authority;
it re-checks the central numerical claims against the committed source/evidence.

## V2 status

Product candidate:

`5e679d8d99d338f9ab28565c636f021a0f9211b2`

V2 qualitative numerical mechanism is accepted:

- exact programmed mirror symmetry;
- max front mirror error ~1.3e-3 lu;
- mean field mirror error ~8e-5;
- one trapped gas cluster from t=0 throughout the run;
- no fragmentation/disappearance;
- `INTERACTION_ONSET = NOT_REACHED`, which is allowed;
- no NaN/Inf;
- velocity and bulk-density operational bounds satisfied.

The original absolute per-colour 5e-4 conservation gate is exceeded by the
blue channel (~6.7e-4 over 60k steps), so the V2 fresh review correctly
escalated the conservation issue rather than treating it as a V2 topology
failure.

V2 symmetry/topology result: **PASS**.

## Conservation audit status

Audit candidate:

`1f5ee76fa183b42dd0ffcb291f389c3f1974a147`

The diagnosis is technically credible and sufficiently localized for a
dedicated solver-fix task.

### Independent matrix check

Using the D3Q19 MRT matrix committed in `lbm_solver_cg3d.py`:

```text
inv_M = float32(inv(M_float64))
```

I independently recomputed the column sums of the stored f32 inverse.

For exact zeroth-moment conservation:

```text
sum_s inv_M[s,0] = 1
sum_s inv_M[s,l] = 0, l>0
```

Actual stored-f32 result:

```text
sum_s inv_M[s,0] - 1
= +1.4901161193847656e-08
```

and the maximum residual among non-density columns is also of order

```text
1.4901161193847656e-08.
```

This independently reproduces the audit's key matrix identity defect.

### Quantitative correspondence

Measured accumulating total-channel rates reported by the audit:

- C3 GPU: ~1.56e-8 / step
- C3 CPU: ~1.52e-8 / step
- V2 production population channel: ~1.53e-8 / step

These are quantitatively consistent with the stored-matrix zeroth-moment
residual above.

This correspondence is strong evidence that the total-distribution drift is
not merely an arbitrary empirical offset.

### Localization

The audit localizes the first accumulating imbalance to the collision step.

The tested closed-system downstream stages do not show a comparable
accumulating contribution:

- wall bounce-back alone does not generate the linear drift;
- downstream streaming/copy steps close in the tested identities;
- CPU and GPU share the same sign and nearly the same total-channel rate.

Thus the evidence does not support blaming GPU atomic ordering as the primary
cause.

### Two closure defects, not one

The total-distribution channel and colour channel must remain conceptually
separate.

Total channel:

```text
F -> M F -> m* -> inv_M m*
```

has a demonstrated f32 inverse-transform zeroth-moment defect.

Colour channel:

```text
rho_r/rho_b -> feq pairs -> recoloring -> rhor/rhob
```

also has a systematic zeroth-moment closure bias; current audit evidence
attributes the dominant colour contribution to equilibrium-distribution
pair/sum rounding, with recoloring arithmetic much smaller.

Therefore fixing only `inv_M` is not sufficient to declare the conservation
problem closed.

## Decision

`PASS_DIAGNOSIS_READY_FOR_FIX` is confirmed.

The audit has done enough diagnosis to authorize a dedicated solver-level
conservation fix task.

## Required next task

Do **not** run V3 yet.

The solver-fix task should compare candidate fixes rather than committing to
one implementation immediately.

At minimum:

### Total-distribution candidates

1. stored-matrix zeroth-moment projection;
2. local post-reconstruction zeroth-moment correction that preserves momentum;
3. full-f64 moment roundtrip as the numerical reference.

A f64 accumulator with the current f32 inverse matrix is not a sufficient
candidate because it leaves the matrix identity defect intact.

### Colour candidates

Test an independent per-colour zeroth-moment closure correction after
equilibrium/recoloring, with momentum/stress effects checked explicitly.

Do not assume recoloring is the dominant colour defect without measurement.

## Fix acceptance hierarchy

The fix should be accepted only if it passes all of:

1. local total and per-colour zeroth-moment identities;
2. C3 long-horizon conservation, with at least 10x reduction from the current
   ~1.56e-8/step total-channel rate;
3. existing V0 regression suite;
4. V1c static/hydraulic regressions;
5. V2 symmetry/topology regression.

Engineering target:

```text
drift rate <= ~2e-9 / step
```

unless the corrected implementation reveals a defensible lower numerical
floor.

Existing physics gates must not be weakened to accept the conservation fix.

## Final state

```text
V2 symmetry/topology: PASS
Conservation audit: PASS_DIAGNOSIS_READY_FOR_FIX
Solver fix: AUTHORIZED, not yet implemented
V3: HOLD
```
